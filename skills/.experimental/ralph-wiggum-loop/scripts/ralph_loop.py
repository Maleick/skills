#!/usr/bin/env python3
"""Ralph Wiggum Loop: single-process, one-change-per-iteration orchestrator."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import signal
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except Exception:  # pragma: no cover - handled at runtime
    yaml = None


STATE_VERSION = "1"
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_SLEEP_SECONDS = 0
DEFAULT_MODE = "auto"
DEFAULT_MEMORY_WINDOW = 5
DEFAULT_OUTPUT_TAIL_LINES = 120
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_CONTEXT_MAX_FILES = 8
DEFAULT_CONTEXT_MAX_CHARS_PER_FILE = 1800
DEFAULT_CONTEXT_MAX_TOTAL_CHARS = 12000
DEFAULT_FUZZY_MIN_SIMILARITY = 0.94
DEFAULT_FUZZY_MIN_GAP = 0.03
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def tail_lines(text: str, max_lines: int) -> str:
    if max_lines <= 0:
        return ""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def parse_float(value: Any, default: float, field_name: str) -> float:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return parsed


def parse_int(value: Any, default: int, field_name: str, minimum: int = 1) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    return parsed


def parse_llm_json_payload(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("LLM response content was empty.")

    candidates: list[str] = [text]
    candidates.extend(match.group(1).strip() for match in JSON_FENCE_RE.finditer(text))

    left = text.find("{")
    right = text.rfind("}")
    if left != -1 and right != -1 and right > left:
        candidates.append(text[left : right + 1].strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("LLM response did not contain a valid JSON object.")


def normalize_allowed_paths(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, list):
        raw = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise ValueError("allowed_paths must be a list or comma-separated string")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw:
        item = item.replace("\\", "/")
        if item.startswith("./"):
            item = item[2:]
        item = item.strip("/")
        if item and item not in seen:
            normalized.append(item)
            seen.add(item)
    return normalized


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off", ""}:
            return False
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def load_config_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    suffix = config_path.suffix.lower()

    if suffix == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required for YAML config files. Install dependencies from requirements.txt"
            )
        data = yaml.safe_load(text) or {}

    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping/object")
    return data


def merge_config(file_config: dict[str, Any], cli_overrides: dict[str, Any]) -> dict[str, Any]:
    config = dict(file_config)
    for key, value in cli_overrides.items():
        if value is not None:
            config[key] = value
    return config


def redact_config_for_state(config: dict[str, Any]) -> dict[str, Any]:
    snapshot = dict(config)
    return snapshot


class RalphLoop:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.goal = str(config["goal"])
        self.repo_path = Path(str(config["repo_path"])).expanduser().resolve()
        if not self.repo_path.exists():
            raise FileNotFoundError(f"repo_path does not exist: {self.repo_path}")

        work_dir_value = str(config.get("work_dir") or "").strip()
        self.work_dir = (
            Path(work_dir_value).expanduser().resolve() if work_dir_value else self.repo_path
        )
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.state_dir = self.work_dir / ".ralph"
        self.iterations_dir = self.state_dir / "iterations"
        self.state_path = self.state_dir / "state.json"
        self.last_patch_path = self.state_dir / "last_patch.diff"
        self.failures_path = self.state_dir / "failures.md"

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.iterations_dir.mkdir(parents=True, exist_ok=True)

        self.allowed_paths = normalize_allowed_paths(config.get("allowed_paths"))
        self.mode = str(config.get("mode", DEFAULT_MODE)).strip().lower() or DEFAULT_MODE
        self.max_iterations = int(config.get("max_iterations", DEFAULT_MAX_ITERATIONS))
        self.sleep_seconds = float(config.get("sleep_seconds", DEFAULT_SLEEP_SECONDS))
        self.dry_run = coerce_bool(config.get("dry_run", False))
        self.readonly = coerce_bool(config.get("readonly", False))
        self.acceptance_criteria = list(config.get("acceptance_criteria") or [])
        self.loop_memory_window = int(config.get("loop_memory_window", DEFAULT_MEMORY_WINDOW))
        self.output_tail_lines = int(config.get("output_tail_lines", DEFAULT_OUTPUT_TAIL_LINES))
        self.llm_config = dict(config.get("llm") or {})
        self.llm_adapter = str(self.llm_config.get("adapter", "stub")).strip().lower() or "stub"
        self.llm_model = str(self.llm_config.get("model", DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
        self.llm_base_url = (
            str(self.llm_config.get("base_url", DEFAULT_OPENAI_BASE_URL)).strip()
            or DEFAULT_OPENAI_BASE_URL
        )
        self.llm_api_key_env = (
            str(self.llm_config.get("api_key_env", "OPENAI_API_KEY")).strip()
            or "OPENAI_API_KEY"
        )
        self.llm_timeout_seconds = parse_float(
            self.llm_config.get("timeout_seconds", DEFAULT_OPENAI_TIMEOUT_SECONDS),
            DEFAULT_OPENAI_TIMEOUT_SECONDS,
            "llm.timeout_seconds",
        )
        self.context_max_files = parse_int(
            self.llm_config.get("context_max_files", DEFAULT_CONTEXT_MAX_FILES),
            DEFAULT_CONTEXT_MAX_FILES,
            "llm.context_max_files",
            minimum=1,
        )
        self.context_max_chars_per_file = parse_int(
            self.llm_config.get("context_max_chars_per_file", DEFAULT_CONTEXT_MAX_CHARS_PER_FILE),
            DEFAULT_CONTEXT_MAX_CHARS_PER_FILE,
            "llm.context_max_chars_per_file",
            minimum=200,
        )
        self.context_max_total_chars = parse_int(
            self.llm_config.get("context_max_total_chars", DEFAULT_CONTEXT_MAX_TOTAL_CHARS),
            DEFAULT_CONTEXT_MAX_TOTAL_CHARS,
            "llm.context_max_total_chars",
            minimum=1000,
        )
        patch_apply_config = dict(config.get("patch_apply") or {})
        self.fuzzy_min_similarity = parse_float(
            patch_apply_config.get("fuzzy_min_similarity", DEFAULT_FUZZY_MIN_SIMILARITY),
            DEFAULT_FUZZY_MIN_SIMILARITY,
            "patch_apply.fuzzy_min_similarity",
        )
        self.fuzzy_min_gap = parse_float(
            patch_apply_config.get("fuzzy_min_gap", DEFAULT_FUZZY_MIN_GAP),
            DEFAULT_FUZZY_MIN_GAP,
            "patch_apply.fuzzy_min_gap",
        )
        if self.fuzzy_min_similarity > 1.0:
            raise ValueError("patch_apply.fuzzy_min_similarity must be <= 1.0")
        if self.fuzzy_min_gap > 1.0:
            raise ValueError("patch_apply.fuzzy_min_gap must be <= 1.0")

        self.prompt_template_path = (
            Path(__file__).resolve().parent.parent / "references" / "prompt_template.md"
        )

        self.verifier_registry: dict[str, Callable[[], dict[str, Any]]] = {}
        self.deploy_registry: dict[str, Callable[..., Any]] = {}
        self.deploy_enabled = False
        self._register_default_verifiers()

        self.stop_requested = False
        self.state = self._load_or_init_state()
        self._install_signal_handlers()

    def _register_default_verifiers(self) -> None:
        self.verifier_registry["tests"] = self._verify_tests
        if str(self.config.get("lint_command") or "").strip():
            self.verifier_registry["lint"] = self._verify_lint

    def register_verifier(self, name: str, verifier: Callable[[], dict[str, Any]]) -> None:
        self.verifier_registry[name] = verifier

    def register_deploy(self, name: str, deployer: Callable[..., Any]) -> None:
        self.deploy_registry[name] = deployer

    def _install_signal_handlers(self) -> None:
        def _handler(signum: int, frame: Any) -> None:  # pragma: no cover - signal-driven
            _ = signum
            _ = frame
            self.stop_requested = True
            self.state["status"] = "interrupted"
            self.state["updated_at"] = utc_now()
            self._save_state()
            print(
                "\n[ralph] SIGINT received. State persisted; exiting at next boundary.",
                file=sys.stderr,
            )
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, _handler)

    def _default_state(self) -> dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "goal": self.goal,
            "repo_path": str(self.repo_path),
            "status": "initialized",
            "current_iteration": 0,
            "max_iterations": self.max_iterations,
            "started_at": utc_now(),
            "updated_at": utc_now(),
            "last_outcome": "none",
            "last_failure_domain": "none",
            "baseline_verification": None,
            "config_snapshot": redact_config_for_state(self.config),
        }

    def _load_or_init_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                raise ValueError(f"Invalid state format in {self.state_path}")
        else:
            state = self._default_state()

        defaults = self._default_state()
        for key, default_value in defaults.items():
            state.setdefault(key, default_value)

        state["goal"] = self.goal
        state["repo_path"] = str(self.repo_path)
        state["max_iterations"] = self.max_iterations
        state["config_snapshot"] = redact_config_for_state(self.config)
        state["updated_at"] = utc_now()

        self._save_state(state)
        return state

    def _save_state(self, state: dict[str, Any] | None = None) -> None:
        data = state if state is not None else self.state
        self.state_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _iteration_file(self, iteration: int) -> Path:
        return self.iterations_dir / f"iter_{iteration:04d}.json"

    def _read_json_file(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _recent_iteration_records(self, n: int) -> list[dict[str, Any]]:
        files = sorted(self.iterations_dir.glob("iter_*.json"))
        records: list[dict[str, Any]] = []
        for path in files[-max(0, n):]:
            try:
                records.append(self._read_json_file(path))
            except Exception:
                continue
        return records

    def _read_recent_failures(self, max_lines: int = 40) -> str:
        if not self.failures_path.exists():
            return "No failure history yet."
        return tail_lines(self.failures_path.read_text(encoding="utf-8"), max_lines)

    def _extract_recent_failing_output(self) -> str:
        for record in reversed(self._recent_iteration_records(self.loop_memory_window * 2)):
            verification = record.get("verification") or {}
            tests = verification.get("tests") or {}
            lint = verification.get("lint") or {}
            if tests and not tests.get("ok", True):
                return str(tests.get("output_tail") or "")
            if lint and not lint.get("ok", True):
                return str(lint.get("output_tail") or "")

        baseline = self.state.get("baseline_verification") or {}
        tests = baseline.get("tests") or {}
        if tests and not tests.get("ok", True):
            return str(tests.get("output_tail") or "")
        return "No failing output captured yet."

    def _build_repo_summary(self, max_files: int = 80) -> str:
        ignored_dirs = {
            ".git",
            ".ralph",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
        }
        files: list[str] = []
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for filename in filenames:
                full_path = Path(root) / filename
                try:
                    rel = full_path.relative_to(self.repo_path).as_posix()
                except Exception:
                    continue
                files.append(rel)
                if len(files) >= max_files:
                    break
            if len(files) >= max_files:
                break

        if not files:
            return "Repository appears empty."
        preview = "\n".join(f"- {path}" for path in sorted(files)[:max_files])
        return f"Showing up to {max_files} files:\n{preview}"

    def _loop_memory_summary(self) -> str:
        records = self._recent_iteration_records(self.loop_memory_window)
        if not records:
            return "No prior iterations."

        lines: list[str] = []
        for record in records:
            iteration = record.get("iteration", "?")
            step = (record.get("planned_step") or "").strip()
            domain = record.get("failure_domain", "none")
            acceptance = record.get("acceptance") or {}
            met = acceptance.get("met", False)
            signature = record.get("error_signature", "none")
            lines.append(
                f"iter={iteration} met={met} domain={domain} step={step[:120]} signature={signature[:160]}"
            )
        return "\n".join(lines)

    def _constraints_summary(self) -> str:
        allowed = ", ".join(self.allowed_paths) if self.allowed_paths else "<all paths under repo_path>"
        criteria = ", ".join(self.acceptance_criteria)
        return (
            f"allowed_paths={allowed}\n"
            f"readonly={self.readonly}\n"
            f"dry_run={self.dry_run}\n"
            f"acceptance_criteria={criteria}\n"
            f"mode={self.mode} max_iterations={self.max_iterations}\n"
            f"context_max_files={self.context_max_files} context_max_chars_per_file={self.context_max_chars_per_file} "
            f"context_max_total_chars={self.context_max_total_chars}\n"
            f"fuzzy_min_similarity={self.fuzzy_min_similarity:.3f} fuzzy_min_gap={self.fuzzy_min_gap:.3f}"
        )

    def _build_prompt(self, context: dict[str, Any], plan: dict[str, Any]) -> str:
        if self.prompt_template_path.exists():
            template = self.prompt_template_path.read_text(encoding="utf-8")
        else:
            template = "Goal:\n{{goal}}\n\nInstruction:\n{{single_step_instruction}}\n"

        mapping = {
            "goal": self.goal,
            "constraints": context.get("constraints", ""),
            "repo_summary": context.get("repo_summary", ""),
            "file_context": context.get("file_context", ""),
            "last_outcome": context.get("last_outcome", ""),
            "recent_failures": context.get("recent_failures", ""),
            "failing_output": context.get("failing_output", ""),
            "loop_memory": context.get("loop_memory", ""),
            "single_step_instruction": plan.get("single_step_instruction", ""),
        }

        prompt = template
        for key, value in mapping.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
        return prompt

    def _run_shell_command(self, command: str) -> dict[str, Any]:
        started = utc_now()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.repo_path),
                text=True,
                capture_output=True,
                check=False,
            )
            combined = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "command": command,
                "started_at": started,
                "ended_at": utc_now(),
                "output_tail": tail_lines(combined, self.output_tail_lines),
            }
        except Exception as exc:
            return {
                "ok": False,
                "returncode": -1,
                "command": command,
                "started_at": started,
                "ended_at": utc_now(),
                "output_tail": tail_lines(traceback.format_exc(), self.output_tail_lines),
                "error": str(exc),
                "error_type": "runtime_error",
            }

    def _verify_tests(self) -> dict[str, Any]:
        return self._run_shell_command(str(self.config["test_command"]))

    def _verify_lint(self) -> dict[str, Any]:
        lint_command = str(self.config.get("lint_command") or "").strip()
        if not lint_command:
            return {
                "ok": True,
                "returncode": 0,
                "command": "",
                "started_at": utc_now(),
                "ended_at": utc_now(),
                "output_tail": "Lint skipped: no lint_command configured.",
                "skipped": True,
            }
        return self._run_shell_command(lint_command)

    def _is_allowed_rel_path(self, rel_posix: str) -> bool:
        if not self.allowed_paths:
            return True
        return any(
            rel_posix == prefix or rel_posix.startswith(prefix + "/")
            for prefix in self.allowed_paths
        )

    def _build_file_context(self) -> str:
        ignored_dirs = {
            ".git",
            ".ralph",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
        }
        candidates: list[Path] = []
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for filename in sorted(filenames):
                full_path = Path(root) / filename
                try:
                    rel_posix = full_path.relative_to(self.repo_path).as_posix()
                except Exception:
                    continue
                if not self._is_allowed_rel_path(rel_posix):
                    continue
                candidates.append(full_path)
                if len(candidates) >= self.context_max_files:
                    break
            if len(candidates) >= self.context_max_files:
                break

        if not candidates:
            return "No file context available."

        blocks: list[str] = []
        total_chars = 0
        for path in candidates:
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if "\x00" in content:
                continue

            rel_posix = path.relative_to(self.repo_path).as_posix()
            remaining = self.context_max_total_chars - total_chars
            if remaining <= 0:
                break

            snippet = content[: min(self.context_max_chars_per_file, remaining)]
            if not snippet.strip():
                continue

            truncated = len(content) > len(snippet)
            header = f"### File: {rel_posix}"
            if truncated:
                header += " (truncated)"
            block = f"{header}\n```\n{snippet}\n```"

            blocks.append(block)
            total_chars += len(snippet)

        return "\n\n".join(blocks) if blocks else "No file context available."

    def _resolve_repo_path(self, relative_path: str) -> Path:
        rel = relative_path.replace("\\", "/").lstrip("/")
        candidate = (self.repo_path / rel).resolve()
        repo_root = self.repo_path.resolve()
        if candidate != repo_root and repo_root not in candidate.parents:
            raise ValueError(f"Path escapes repository: {relative_path}")

        rel_posix = candidate.relative_to(repo_root).as_posix()
        if not self._is_allowed_rel_path(rel_posix):
            raise ValueError(
                f"Path blocked by allowed_paths: {rel_posix} (allowed: {', '.join(self.allowed_paths)})"
            )

        return candidate

    def _stub_llm(self, prompt: str, context: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        _ = prompt
        _ = context
        _ = plan

        # Deterministic marker-based repair for offline demo repos.
        for path in self.repo_path.rglob("*.py"):
            if ".ralph" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            marker = "return a - b  # RALPH_FIXME:addition_bug"
            if marker in text:
                rel = path.relative_to(self.repo_path).as_posix()
                return {
                    "kind": "single_change_set",
                    "summary": "Fix marker-tagged addition bug",
                    "changes": [
                        {
                            "path": rel,
                            "op": "replace_text",
                            "target": marker,
                            "replacement": "return a + b",
                            "count": 1,
                        }
                    ],
                }

        # Heuristic fallback when marker is absent.
        for path in self.repo_path.rglob("*.py"):
            if ".ralph" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "def add(" in text and "return a - b" in text:
                rel = path.relative_to(self.repo_path).as_posix()
                return {
                    "kind": "single_change_set",
                    "summary": "Fix likely subtraction typo in add()",
                    "changes": [
                        {
                            "path": rel,
                            "op": "replace_text",
                            "target": "return a - b",
                            "replacement": "return a + b",
                            "count": 1,
                        }
                    ],
                }

        return {
            "kind": "single_change_set",
            "summary": "No deterministic patch identified by stub adapter",
            "changes": [],
        }

    def _extract_openai_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI response missing choices.")

        first = choices[0]
        if not isinstance(first, dict):
            raise RuntimeError("OpenAI response has invalid choice shape.")

        message = first.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("OpenAI response missing message.")

        content = message.get("content")
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                    continue
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
            if parts:
                return "\n".join(parts)

        raise RuntimeError("OpenAI response content was missing or unsupported.")

    def _openai_llm(self, prompt: str) -> dict[str, Any]:
        api_key = os.environ.get(self.llm_api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{self.llm_api_key_env} is not set (required for llm.adapter=openai)."
            )

        url = f"{self.llm_base_url.rstrip('/')}/chat/completions"
        system_prompt = (
            "You are a deterministic patch planner. "
            "Return exactly one JSON object matching the requested single_change_set contract."
        )
        request_payload = {
            "model": self.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        data = json.dumps(request_payload).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.llm_timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error HTTP {exc.code}: {tail_lines(body, 8)}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI API request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI API returned invalid JSON.") from exc

        text = self._extract_openai_text(parsed)
        try:
            return parse_llm_json_payload(text)
        except ValueError as exc:
            preview = tail_lines(text, 12)
            raise RuntimeError(f"{exc} Raw response tail:\n{preview}") from exc

    def _normalize_patch_instruction(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RuntimeError("Patch instruction must be a JSON object.")

        kind = str(payload.get("kind", "")).strip()
        if kind != "single_change_set":
            raise RuntimeError("Patch instruction kind must be 'single_change_set'.")

        raw_changes = payload.get("changes")
        if not isinstance(raw_changes, list):
            raise RuntimeError("Patch instruction 'changes' must be a list.")

        normalized_changes: list[dict[str, Any]] = []
        for index, raw_change in enumerate(raw_changes):
            if not isinstance(raw_change, dict):
                raise RuntimeError(f"Change #{index + 1} must be an object.")

            path = str(raw_change.get("path", "")).strip()
            if not path:
                raise RuntimeError(f"Change #{index + 1} is missing required 'path'.")

            op = str(raw_change.get("op", "replace_text")).strip()
            if op not in {"replace_text", "write_file"}:
                raise RuntimeError(f"Change #{index + 1} has unsupported op '{op}'.")

            change: dict[str, Any] = {"path": path, "op": op}
            if op == "replace_text":
                target = raw_change.get("target")
                replacement = raw_change.get("replacement")
                if not isinstance(target, str) or not isinstance(replacement, str):
                    raise RuntimeError(
                        f"Change #{index + 1} replace_text requires string target and replacement."
                    )
                count = raw_change.get("count", 1)
                try:
                    count_int = int(count)
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(f"Change #{index + 1} count must be an integer.") from exc
                if count_int <= 0:
                    raise RuntimeError(f"Change #{index + 1} count must be >= 1.")
                change["target"] = target
                change["replacement"] = replacement
                change["count"] = count_int
            else:
                content = raw_change.get("content", "")
                if not isinstance(content, str):
                    raise RuntimeError(f"Change #{index + 1} write_file content must be a string.")
                change["content"] = content

            normalized_changes.append(change)

        return {
            "kind": "single_change_set",
            "summary": str(payload.get("summary", "")).strip() or "LLM-proposed change-set",
            "changes": normalized_changes,
        }

    def load_context(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "constraints": self._constraints_summary(),
            "repo_summary": self._build_repo_summary(),
            "file_context": self._build_file_context(),
            "last_outcome": f"last_outcome={self.state.get('last_outcome')} last_failure_domain={self.state.get('last_failure_domain')}",
            "recent_failures": self._read_recent_failures(),
            "failing_output": self._extract_recent_failing_output(),
            "loop_memory": self._loop_memory_summary(),
        }

    def plan_step(self, context: dict[str, Any]) -> dict[str, Any]:
        failing_output = str(context.get("failing_output") or "")
        last_domain = str(self.state.get("last_failure_domain") or "none")

        if last_domain in {"patch_apply_error", "tool_error"}:
            instruction = (
                "Produce one minimal glue-safe edit that resolves the previous patch/tool failure and improves test progress."
            )
        elif failing_output and failing_output != "No failing output captured yet.":
            instruction = "Fix the highest-signal failing test with exactly one minimal change-set."
        else:
            instruction = "Apply one minimal change-set that advances acceptance criteria."

        return {
            "single_step_instruction": instruction,
            "strategy": "minimal_single_change",
        }

    def call_llm(self, context: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_prompt(context, plan)
        adapter = self.llm_adapter
        if adapter == "stub":
            payload = self._stub_llm(prompt, context, plan)
        elif adapter == "openai":
            payload = self._openai_llm(prompt)
        else:
            raise RuntimeError(f"Unsupported llm.adapter '{adapter}'.")

        payload = self._normalize_patch_instruction(payload)
        payload["adapter"] = adapter
        payload["prompt_excerpt"] = prompt[:3000]
        return payload

    def call_tool(self, context: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        return self.call_llm(context, plan)

    def _fuzzy_replace(self, old_text: str, target: str, replacement: str) -> tuple[str, dict[str, Any]]:
        if target in old_text:
            return old_text.replace(target, replacement, 1), {
                "mode": "exact",
                "similarity": 1.0,
            }

        target_lines = target.splitlines(keepends=True)
        if not target_lines:
            raise ValueError("target text not found")

        lines = old_text.splitlines(keepends=True)
        if not lines:
            raise ValueError("target text not found")

        window_size = max(1, len(target_lines))
        candidates: list[tuple[float, int, int]] = []
        for start in range(0, len(lines) - window_size + 1):
            chunk = "".join(lines[start : start + window_size])
            ratio_raw = difflib.SequenceMatcher(None, target, chunk).ratio()
            ratio_stripped = difflib.SequenceMatcher(None, target.strip(), chunk.strip()).ratio()
            ratio = max(ratio_raw, ratio_stripped)
            candidates.append((ratio, start, start + window_size))

        if not candidates:
            raise ValueError("target text not found")

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_ratio, best_start, best_end = candidates[0]
        second_ratio = candidates[1][0] if len(candidates) > 1 else 0.0

        if best_ratio < self.fuzzy_min_similarity:
            raise ValueError(
                f"target text not found; fuzzy best similarity {best_ratio:.3f} < {self.fuzzy_min_similarity:.3f}"
            )
        if (best_ratio - second_ratio) < self.fuzzy_min_gap:
            raise ValueError(
                f"target text ambiguous; best/second gap {best_ratio - second_ratio:.3f} < {self.fuzzy_min_gap:.3f}"
            )

        offsets: list[int] = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))

        start_idx = offsets[best_start]
        end_idx = offsets[best_end]
        matched_chunk = old_text[start_idx:end_idx]
        adjusted_replacement = replacement
        if "\n" not in replacement:
            leading_ws = matched_chunk[: len(matched_chunk) - len(matched_chunk.lstrip())]
            if leading_ws and replacement == replacement.lstrip():
                adjusted_replacement = leading_ws + replacement
            if matched_chunk.endswith("\n") and not adjusted_replacement.endswith("\n"):
                adjusted_replacement += "\n"

        new_text = old_text[:start_idx] + adjusted_replacement + old_text[end_idx:]
        return new_text, {
            "mode": "fuzzy",
            "similarity": round(best_ratio, 6),
            "second_similarity": round(second_ratio, 6),
            "matched_lines": [best_start + 1, best_end],
        }

    def apply_changes(self, patch_instruction: dict[str, Any]) -> dict[str, Any]:
        changes = patch_instruction.get("changes") or []
        if not isinstance(changes, list):
            return {
                "ok": False,
                "error": "Patch instruction missing list field: changes",
                "changed_files": [],
                "dry_run": self.dry_run,
                "readonly": self.readonly,
            }

        if not changes:
            self.last_patch_path.write_text("# No-op: patch instruction contained no changes.\n", encoding="utf-8")
            return {
                "ok": True,
                "mode": "no_op",
                "changed_files": [],
                "dry_run": self.dry_run,
                "readonly": self.readonly,
            }

        changed_files: list[str] = []
        diffs: list[str] = []
        fuzzy_matches: list[dict[str, Any]] = []
        staged_writes: list[tuple[Path, str, str, bool]] = []

        try:
            for change in changes:
                path = str(change["path"])
                op = str(change.get("op", "replace_text"))
                file_path = self._resolve_repo_path(path)
                rel_path = file_path.relative_to(self.repo_path).as_posix()

                old_text = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
                new_text = old_text

                if op == "replace_text":
                    target = str(change.get("target", ""))
                    replacement = str(change.get("replacement", ""))
                    count = int(change.get("count", 1))

                    if count <= 0:
                        raise ValueError("replace_text count must be >= 1")
                    if target in old_text:
                        new_text = old_text.replace(target, replacement, count)
                    else:
                        if count != 1:
                            raise ValueError(
                                f"target text not found in {rel_path}; fuzzy fallback requires count=1"
                            )
                        new_text, fuzzy_meta = self._fuzzy_replace(old_text, target, replacement)
                        fuzzy_meta["path"] = rel_path
                        fuzzy_matches.append(fuzzy_meta)
                elif op == "write_file":
                    new_text = str(change.get("content", ""))
                else:
                    raise ValueError(f"Unsupported change op: {op}")

                diff = "".join(
                    difflib.unified_diff(
                        old_text.splitlines(keepends=True),
                        new_text.splitlines(keepends=True),
                        fromfile=f"a/{rel_path}",
                        tofile=f"b/{rel_path}",
                    )
                )
                if diff:
                    diffs.append(diff)

                staged_writes.append((file_path, old_text, new_text, file_path.exists()))

                changed_files.append(rel_path)

            if not self.readonly and not self.dry_run:
                applied_writes: list[tuple[Path, str, bool]] = []
                try:
                    for file_path, old_text, new_text, existed_before in staged_writes:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(new_text, encoding="utf-8")
                        applied_writes.append((file_path, old_text, existed_before))
                except Exception:
                    for applied_path, old_text, existed_before in reversed(applied_writes):
                        if existed_before:
                            applied_path.write_text(old_text, encoding="utf-8")
                        elif applied_path.exists():
                            applied_path.unlink()
                    raise

            diff_text = "\n".join(diffs).strip()
            if not diff_text:
                diff_text = "# Patch produced no textual diff.\n"
            self.last_patch_path.write_text(diff_text + ("\n" if not diff_text.endswith("\n") else ""), encoding="utf-8")

            mode_note = "applied"
            if self.readonly:
                mode_note = "readonly_preview"
            elif self.dry_run:
                mode_note = "dry_run_preview"

            return {
                "ok": True,
                "mode": mode_note,
                "changed_files": changed_files,
                "diff_path": str(self.last_patch_path),
                "dry_run": self.dry_run,
                "readonly": self.readonly,
                "fuzzy_matches": fuzzy_matches,
            }
        except Exception as exc:
            self.last_patch_path.write_text(
                f"# apply_changes failed\n# error: {exc}\n", encoding="utf-8"
            )
            return {
                "ok": False,
                "error": str(exc),
                "changed_files": changed_files,
                "diff_path": str(self.last_patch_path),
                "dry_run": self.dry_run,
                "readonly": self.readonly,
            }

    def run_verification(self) -> dict[str, Any]:
        tests = self.verifier_registry["tests"]()
        lint: dict[str, Any] | None = None
        if "lint" in self.verifier_registry:
            lint = self.verifier_registry["lint"]()

        overall_ok = bool(tests.get("ok", False)) and (lint is None or bool(lint.get("ok", False)))
        payload: dict[str, Any] = {
            "timestamp": utc_now(),
            "tests": tests,
            "overall_ok": overall_ok,
        }
        if lint is not None:
            payload["lint"] = lint
        return payload

    def _evaluate_acceptance(self, verification: dict[str, Any]) -> dict[str, Any]:
        criteria_results: dict[str, bool] = {}
        unmet: list[str] = []

        for criterion in self.acceptance_criteria:
            value = False
            if criterion == "tests_pass":
                value = bool((verification.get("tests") or {}).get("ok", False))
            elif criterion == "lint_pass":
                value = bool((verification.get("lint") or {}).get("ok", False))
            else:
                value = False

            criteria_results[criterion] = value
            if not value:
                unmet.append(criterion)

        met = len(unmet) == 0
        return {
            "met": met,
            "criteria": criteria_results,
            "unmet": unmet,
        }

    def _classify_failure(
        self,
        orchestration_error: str | None,
        tool_error: str | None,
        apply_result: dict[str, Any],
        verification: dict[str, Any],
        acceptance: dict[str, Any],
    ) -> tuple[str, str, str, str]:
        tests = verification.get("tests") or {}
        lint = verification.get("lint") or {}

        if orchestration_error:
            return (
                "runtime_error",
                orchestration_error[:200],
                "Loop orchestration stage raised an exception.",
                "glue patch",
            )

        if tool_error:
            return (
                "tool_error",
                tool_error[:200],
                "Planner/adapter raised an exception or returned invalid structure.",
                "glue patch",
            )

        if not apply_result.get("ok", False):
            signature = str(apply_result.get("error") or "patch apply failed")
            return (
                "patch_apply_error",
                signature[:200],
                "Patch instruction could not be applied under current constraints.",
                "constraints change",
            )

        if tests.get("error_type") == "runtime_error" or lint.get("error_type") == "runtime_error":
            signature = str(tests.get("error") or lint.get("error") or "runtime error")
            return (
                "runtime_error",
                signature[:200],
                "Verification command failed to execute cleanly.",
                "glue patch",
            )

        runtime_like_return_codes = {126, 127}
        tests_output = str(tests.get("output_tail") or "")
        lint_output = str(lint.get("output_tail") or "")
        if (
            tests.get("returncode") in runtime_like_return_codes
            or lint.get("returncode") in runtime_like_return_codes
            or "command not found" in tests_output.lower()
            or "command not found" in lint_output.lower()
        ):
            signature = tests_output or lint_output or "verification command not found"
            return (
                "runtime_error",
                tail_lines(signature, 6)[:200],
                "Verifier command appears missing or not executable in this environment.",
                "constraints change",
            )

        if apply_result.get("mode") == "no_op" and acceptance.get("met", False):
            return (
                "none",
                "no_error",
                "No-op accepted because acceptance criteria were met.",
                "none",
            )

        if lint and not lint.get("ok", True):
            signature = str(lint.get("output_tail") or "lint failed")
            return (
                "lint_failure",
                tail_lines(signature, 6)[:200],
                "Lint verifier returned a non-zero result.",
                "prompt tweak",
            )

        if not tests.get("ok", True):
            signature = str(tests.get("output_tail") or "tests failed")
            return (
                "test_failure",
                tail_lines(signature, 6)[:200],
                "Tests still failing after the change-set.",
                "prompt tweak",
            )

        if not acceptance.get("met", False):
            unmet = ", ".join(acceptance.get("unmet") or [])
            return (
                "acceptance_unmet",
                f"Unmet: {unmet}"[:200],
                "Verification passed partially but acceptance criteria are broader.",
                "constraints change",
            )

        return (
            "none",
            "no_error",
            "No failure detected.",
            "none",
        )

    def _append_failure_log(
        self,
        iteration: int,
        failure_domain: str,
        error_signature: str,
        suspected_cause: str,
        operator_lever_hint: str,
    ) -> None:
        section = (
            f"## Iteration {iteration:04d} - {utc_now()}\n"
            f"- failure_domain: {failure_domain}\n"
            f"- error_signature: {error_signature}\n"
            f"- suspected_cause: {suspected_cause}\n"
            f"- suggested_operator_lever: {operator_lever_hint}\n\n"
        )
        with self.failures_path.open("a", encoding="utf-8") as f:
            f.write(section)

    def record_iteration(self, record: dict[str, Any]) -> None:
        iteration = int(record["iteration"])
        iter_path = self._iteration_file(iteration)
        iter_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        self._append_failure_log(
            iteration=iteration,
            failure_domain=str(record.get("failure_domain", "none")),
            error_signature=str(record.get("error_signature", "")),
            suspected_cause=str(record.get("suspected_cause", "")),
            operator_lever_hint=str(record.get("operator_lever_hint", "")),
        )

        acceptance = record.get("acceptance") or {}
        self.state["current_iteration"] = iteration
        self.state["last_outcome"] = "success" if acceptance.get("met") else "failed"
        self.state["last_failure_domain"] = str(record.get("failure_domain", "none"))
        self.state["updated_at"] = utc_now()
        self.state["status"] = "success" if acceptance.get("met") else "running"
        self._save_state()

    def run_iteration(self, iteration: int) -> bool:
        started_at = utc_now()
        context: dict[str, Any] = {}
        plan: dict[str, Any] = {}
        patch_instruction: dict[str, Any] = {}
        apply_result: dict[str, Any] = {}
        verification: dict[str, Any] = {}
        tool_error: str | None = None
        orchestration_error: str | None = None

        try:
            context = self.load_context()
        except Exception as exc:
            orchestration_error = f"load_context failed: {type(exc).__name__}: {exc}"
            context = {
                "goal": self.goal,
                "constraints": self._constraints_summary(),
                "repo_summary": "Context load failed.",
                "file_context": "Context unavailable due to load error.",
                "last_outcome": f"last_outcome={self.state.get('last_outcome')}",
                "recent_failures": self._read_recent_failures(),
                "failing_output": "",
                "loop_memory": "Context unavailable due to load error.",
            }

        try:
            plan = self.plan_step(context)
        except Exception as exc:
            if orchestration_error is None:
                orchestration_error = f"plan_step failed: {type(exc).__name__}: {exc}"
            plan = {
                "single_step_instruction": (
                    "Apply one minimal change-set while preserving safety constraints."
                ),
                "strategy": "fallback_after_plan_error",
            }

        try:
            patch_instruction = self.call_llm(context, plan)
        except Exception as exc:
            tool_error = f"{type(exc).__name__}: {exc}"
            patch_instruction = {
                "kind": "single_change_set",
                "summary": "call_llm failed",
                "changes": [],
                "prompt_excerpt": self._build_prompt(context, plan)[:3000],
            }

        apply_result = self.apply_changes(patch_instruction)
        verification = self.run_verification()
        acceptance = self._evaluate_acceptance(verification)
        failure_domain, error_signature, suspected_cause, operator_lever_hint = self._classify_failure(
            orchestration_error,
            tool_error, apply_result, verification, acceptance
        )

        context_summary = {
            "goal": self.goal,
            "last_outcome": self.state.get("last_outcome"),
            "last_failure_domain": self.state.get("last_failure_domain"),
            "repo_summary": tail_lines(str(context.get("repo_summary", "")), 40),
        }

        record = {
            "iteration": iteration,
            "started_at": started_at,
            "ended_at": utc_now(),
            "context_summary": context_summary,
            "planned_step": str(plan.get("single_step_instruction", "")),
            "prompt_excerpt": str(patch_instruction.get("prompt_excerpt", "")),
            "patch_instruction": patch_instruction,
            "apply_result": apply_result,
            "verification": verification,
            "acceptance": acceptance,
            "failure_domain": failure_domain,
            "error_signature": error_signature,
            "suspected_cause": suspected_cause,
            "operator_lever_hint": operator_lever_hint,
        }
        self.record_iteration(record)
        return bool(acceptance.get("met", False))

    def _ensure_baseline_verification(self) -> None:
        if self.state.get("baseline_verification") is not None:
            return

        baseline = self.run_verification()
        self.state["baseline_verification"] = baseline
        self.state["updated_at"] = utc_now()
        self._save_state()

    def _show_last_patch(self) -> None:
        if not self.last_patch_path.exists():
            print("[ralph] No last patch available.")
            return
        print(self.last_patch_path.read_text(encoding="utf-8"))

    def _step_controls(self) -> bool:
        while True:
            choice = input("[step] Enter=continue, r=verify-only, s=show-patch, q=quit > ").strip().lower()
            if choice == "":
                return True
            if choice == "q":
                self.state["status"] = "stopped"
                self.state["updated_at"] = utc_now()
                self._save_state()
                return False
            if choice == "s":
                self._show_last_patch()
                continue
            if choice == "r":
                verification = self.run_verification()
                tests_ok = (verification.get("tests") or {}).get("ok", False)
                lint = verification.get("lint") or {}
                lint_ok = lint.get("ok", True) if lint else True
                print(f"[step] verify-only tests_ok={tests_ok} lint_ok={lint_ok}")
                continue
            print("[step] Unknown option. Use Enter, r, s, or q.")

    def run(self) -> int:
        self.state["status"] = "running"
        self.state["updated_at"] = utc_now()
        self._save_state()

        self._ensure_baseline_verification()

        try:
            while self.state["current_iteration"] < self.max_iterations:
                if self.stop_requested:
                    self.state["status"] = "interrupted"
                    self.state["updated_at"] = utc_now()
                    self._save_state()
                    return 130

                iteration = int(self.state["current_iteration"]) + 1
                print(f"[ralph] Iteration {iteration}/{self.max_iterations}")
                success = self.run_iteration(iteration)

                if success:
                    self.state["status"] = "success"
                    self.state["updated_at"] = utc_now()
                    self._save_state()
                    print("[ralph] Acceptance criteria met. Stopping.")
                    return 0

                if self.mode == "step" and not self._step_controls():
                    print("[ralph] Step mode requested stop.")
                    return 0

                if self.sleep_seconds > 0:
                    time.sleep(self.sleep_seconds)

            self.state["status"] = "max_iterations_reached"
            self.state["updated_at"] = utc_now()
            self._save_state()
            print("[ralph] Max iterations reached without meeting acceptance criteria.")
            return 1
        except KeyboardInterrupt:
            self.state["status"] = "interrupted"
            self.state["updated_at"] = utc_now()
            self._save_state()
            print("[ralph] Interrupted; state persisted.")
            return 130
        except Exception:
            self.state["status"] = "runtime_error"
            self.state["updated_at"] = utc_now()
            self._save_state()
            traceback.print_exc()
            return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to YAML/JSON config file")

    parser.add_argument("--goal")
    parser.add_argument("--repo_path")
    parser.add_argument("--test_command")
    parser.add_argument("--lint_command")
    parser.add_argument("--mode", choices=["auto", "step"])
    parser.add_argument("--max_iterations", type=int)
    parser.add_argument("--sleep_seconds", type=float)
    parser.add_argument(
        "--allowed_paths",
        help="Comma-separated relative paths/prefixes permitted for edits",
    )
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--readonly", action="store_true")
    parser.add_argument("--work_dir")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if "acceptance_criteria" not in config or config["acceptance_criteria"] in (None, ""):
        config["acceptance_criteria"] = ["tests_pass"]

    required = ["goal", "repo_path", "test_command", "acceptance_criteria"]
    missing = [key for key in required if key not in config or config[key] in (None, "")]
    if missing:
        raise ValueError(f"Missing required config key(s): {', '.join(missing)}")

    if not isinstance(config["acceptance_criteria"], list):
        raise ValueError("acceptance_criteria must be a list")
    normalized_criteria = [str(item).strip() for item in config["acceptance_criteria"]]
    config["acceptance_criteria"] = normalized_criteria
    if "tests_pass" not in config["acceptance_criteria"]:
        raise ValueError("acceptance_criteria must include 'tests_pass'")
    allowed_criteria = {"tests_pass", "lint_pass"}
    unsupported_criteria = [item for item in config["acceptance_criteria"] if item not in allowed_criteria]
    if unsupported_criteria:
        raise ValueError(
            "Unsupported acceptance_criteria value(s): "
            + ", ".join(unsupported_criteria)
            + ". Allowed values: tests_pass, lint_pass"
        )

    config["mode"] = str(config.get("mode", DEFAULT_MODE)).strip().lower() or DEFAULT_MODE
    if config["mode"] not in {"auto", "step"}:
        raise ValueError("mode must be 'auto' or 'step'")

    config["max_iterations"] = int(config.get("max_iterations", DEFAULT_MAX_ITERATIONS))
    if config["max_iterations"] <= 0:
        raise ValueError("max_iterations must be > 0")

    config["sleep_seconds"] = float(config.get("sleep_seconds", DEFAULT_SLEEP_SECONDS))
    if config["sleep_seconds"] < 0:
        raise ValueError("sleep_seconds must be >= 0")

    config["allowed_paths"] = normalize_allowed_paths(config.get("allowed_paths"))
    config["dry_run"] = coerce_bool(config.get("dry_run", False))
    config["readonly"] = coerce_bool(config.get("readonly", False))
    config.setdefault("lint_command", "")
    config.setdefault("work_dir", "")
    llm = config.get("llm")
    if llm is None:
        llm = {}
    if not isinstance(llm, dict):
        raise ValueError("llm must be a mapping/object")

    adapter = str(llm.get("adapter", "stub")).strip().lower() or "stub"
    if adapter not in {"stub", "openai"}:
        raise ValueError("llm.adapter must be 'stub' or 'openai'")

    model = str(llm.get("model", DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    base_url = str(llm.get("base_url", DEFAULT_OPENAI_BASE_URL)).strip() or DEFAULT_OPENAI_BASE_URL
    api_key_env = str(llm.get("api_key_env", "OPENAI_API_KEY")).strip() or "OPENAI_API_KEY"
    timeout_seconds = parse_float(
        llm.get("timeout_seconds", DEFAULT_OPENAI_TIMEOUT_SECONDS),
        DEFAULT_OPENAI_TIMEOUT_SECONDS,
        "llm.timeout_seconds",
    )
    context_max_files = parse_int(
        llm.get("context_max_files", DEFAULT_CONTEXT_MAX_FILES),
        DEFAULT_CONTEXT_MAX_FILES,
        "llm.context_max_files",
        minimum=1,
    )
    context_max_chars_per_file = parse_int(
        llm.get("context_max_chars_per_file", DEFAULT_CONTEXT_MAX_CHARS_PER_FILE),
        DEFAULT_CONTEXT_MAX_CHARS_PER_FILE,
        "llm.context_max_chars_per_file",
        minimum=200,
    )
    context_max_total_chars = parse_int(
        llm.get("context_max_total_chars", DEFAULT_CONTEXT_MAX_TOTAL_CHARS),
        DEFAULT_CONTEXT_MAX_TOTAL_CHARS,
        "llm.context_max_total_chars",
        minimum=1000,
    )

    config["llm"] = {
        "adapter": adapter,
        "model": model,
        "base_url": base_url,
        "api_key_env": api_key_env,
        "timeout_seconds": timeout_seconds,
        "context_max_files": context_max_files,
        "context_max_chars_per_file": context_max_chars_per_file,
        "context_max_total_chars": context_max_total_chars,
    }
    patch_apply = config.get("patch_apply") or {}
    if not isinstance(patch_apply, dict):
        raise ValueError("patch_apply must be a mapping/object")
    fuzzy_min_similarity = parse_float(
        patch_apply.get("fuzzy_min_similarity", DEFAULT_FUZZY_MIN_SIMILARITY),
        DEFAULT_FUZZY_MIN_SIMILARITY,
        "patch_apply.fuzzy_min_similarity",
    )
    fuzzy_min_gap = parse_float(
        patch_apply.get("fuzzy_min_gap", DEFAULT_FUZZY_MIN_GAP),
        DEFAULT_FUZZY_MIN_GAP,
        "patch_apply.fuzzy_min_gap",
    )
    if fuzzy_min_similarity > 1.0:
        raise ValueError("patch_apply.fuzzy_min_similarity must be <= 1.0")
    if fuzzy_min_gap > 1.0:
        raise ValueError("patch_apply.fuzzy_min_gap must be <= 1.0")
    config["patch_apply"] = {
        "fuzzy_min_similarity": fuzzy_min_similarity,
        "fuzzy_min_gap": fuzzy_min_gap,
    }
    config.setdefault("loop_memory_window", DEFAULT_MEMORY_WINDOW)
    config.setdefault("output_tail_lines", DEFAULT_OUTPUT_TAIL_LINES)
    return config


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    file_config = load_config_file(args.config)

    cli_overrides = {
        "goal": args.goal,
        "repo_path": args.repo_path,
        "test_command": args.test_command,
        "lint_command": args.lint_command,
        "mode": args.mode,
        "max_iterations": args.max_iterations,
        "sleep_seconds": args.sleep_seconds,
        "allowed_paths": args.allowed_paths,
        "dry_run": args.dry_run if args.dry_run else None,
        "readonly": args.readonly if args.readonly else None,
        "work_dir": args.work_dir,
    }

    config = merge_config(file_config, cli_overrides)
    return validate_config(config)


def main() -> int:
    args = parse_args()
    config = build_config(args)
    loop = RalphLoop(config)
    return loop.run()


if __name__ == "__main__":
    raise SystemExit(main())
