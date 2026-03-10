#!/usr/bin/env python3
"""Build protocol-validation overlay payloads for dashboard/kanban consumers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from protocol_rules import (
    ALLOWED_ROLES,
    ALLOWED_STATES,
    is_runtime_coupled,
    parse_iso8601,
    validate_task_card_semantics,
    validate_transition,
)
from validate_task_card import schema_validate_fallback, schema_validate_with_jsonschema

HANDOFF_FIELDS = (
    "summary",
    "changed_paths",
    "verification_commands",
    "risk_notes",
    "next_owner",
    "next_action",
)

CRITICAL_ERROR_PATTERNS = (
    re.compile(r"runtime-coupled", re.IGNORECASE),
    re.compile(r"self-approval", re.IGNORECASE),
    re.compile(r"state must be one of", re.IGNORECASE),
    re.compile(r"owner_role", re.IGNORECASE),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    default_schema = Path(__file__).resolve().parent.parent / "references" / "task-card-schema.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="Path to source task JSON (Notion projection/snapshot).")
    parser.add_argument("--schema", default=str(default_schema), help="Path to task-card JSON schema.")
    parser.add_argument(
        "--task-array-key",
        default="",
        help="Optional key path to task array, e.g. 'tasks' or 'payload.items'.",
    )
    parser.add_argument("--source-label", default="notion-kanban")
    parser.add_argument("--now", default="", help="Optional deterministic timestamp for lease checks.")
    parser.add_argument("--adapter-mode", action="store_true", help="Enable runtime-coupled guard checks.")
    parser.add_argument("--allow-runtime-coupled", action="store_true")
    parser.add_argument("--output-json", default="", help="Optional output path for full overlay JSON payload.")
    parser.add_argument("--output-markdown", default="", help="Optional output path for dashboard-friendly markdown summary.")
    parser.add_argument("--fail-on-gate-fail", action="store_true", help="Exit non-zero if any task gate status is fail.")
    return parser.parse_args()


def _pick_first(mapping: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_tasks(payload: Any, task_array_key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []

    if task_array_key:
        current: Any = payload
        for segment in [part for part in task_array_key.split(".") if part]:
            if not isinstance(current, dict) or segment not in current:
                return []
            current = current[segment]
        if isinstance(current, list):
            return [row for row in current if isinstance(row, dict)]
        return []

    for candidate in ("tasks", "items", "results", "records", "data", "pages"):
        if isinstance(payload.get(candidate), list):
            return [row for row in payload[candidate] if isinstance(row, dict)]

    if all(isinstance(value, dict) for value in payload.values()):
        return [value for value in payload.values() if isinstance(value, dict)]

    return []


def _normalize_priority(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value in {"critical", "p0", "p1"}:
        return "high"
    if value in {"p2"}:
        return "medium"
    if value in {"p3", "p4"}:
        return "low"
    if value in {"high", "medium", "low"}:
        return value
    return "medium"


def _normalize_state(raw: str) -> str:
    value = str(raw or "").strip().lower()
    aliases = {
        "backlog": "inbox",
        "todo": "inbox",
        "to_do": "inbox",
        "queued": "inbox",
        "validated": "review",
        "ready_to_submit": "review",
        "submitted": "review",
        "ready": "assigned",
        "assigned": "assigned",
        "inprogress": "in_progress",
        "in-progress": "in_progress",
        "in_progress": "in_progress",
        "review": "review",
        "done": "done",
        "closed": "done",
        "failed": "failed",
        "blocked": "failed",
    }
    return aliases.get(value, value or "inbox")


def _normalize_role(raw: str) -> str:
    value = str(raw or "").strip()
    aliases = {
        "orchestrator": "Orchestrator",
        "builder": "Builder",
        "reviewer": "Reviewer",
        "ops": "Ops",
    }
    return aliases.get(value.lower(), value or "Builder")


def _normalize_verification(raw: Any) -> list[dict[str, Any]]:
    items = _coerce_list(raw)
    normalized: list[dict[str, Any]] = []
    for row in items:
        if isinstance(row, dict):
            command = str(_pick_first(row, ("command", "cmd", "name"), "")).strip()
            status = str(_pick_first(row, ("status", "result"), "not_run")).strip().lower()
            if status not in {"pass", "fail", "not_run"}:
                status = "not_run"
            if command:
                normalized.append(
                    {
                        "command": command,
                        "status": status,
                        "evidence": str(row.get("evidence", "")).strip(),
                    }
                )
        elif isinstance(row, str) and row.strip():
            normalized.append({"command": row.strip(), "status": "not_run", "evidence": ""})
    return normalized


def _normalize_blockers(raw: Any) -> list[dict[str, Any]]:
    items = _coerce_list(raw)
    normalized: list[dict[str, Any]] = []
    for row in items:
        if isinstance(row, dict):
            description = str(_pick_first(row, ("description", "message", "reason"), "")).strip()
            if description:
                severity = str(_pick_first(row, ("severity",), "medium")).strip().lower()
                if severity not in {"high", "medium", "low"}:
                    severity = "medium"
                next_action = str(_pick_first(row, ("next_action", "nextAction"), "triage")).strip() or "triage"
                normalized.append(
                    {
                        "description": description,
                        "severity": severity,
                        "next_action": next_action,
                    }
                )
        elif isinstance(row, str) and row.strip():
            normalized.append({"description": row.strip(), "severity": "medium", "next_action": "triage"})
    return normalized


def _extract_handoff(row: dict[str, Any]) -> dict[str, Any]:
    handoff = row.get("handoff") if isinstance(row.get("handoff"), dict) else {}
    source = handoff if handoff else row
    return {field: source.get(field) for field in HANDOFF_FIELDS}


def _handoff_complete(handoff: dict[str, Any], state: str) -> tuple[bool, list[str]]:
    if state not in {"review", "done", "failed"}:
        return True, []

    missing: list[str] = []
    for field in HANDOFF_FIELDS:
        value = handoff.get(field)
        if value in (None, "", []):
            missing.append(field)
    return len(missing) == 0, missing


def _lease_health(state: str, claimed_until: Any, now_dt: datetime) -> str:
    if state != "in_progress":
        return "n/a"
    if claimed_until in (None, "", "null"):
        return "missing"
    try:
        lease = parse_iso8601(str(claimed_until))
    except Exception:
        return "invalid"
    if lease is None:
        return "missing"
    return "stale" if lease <= now_dt else "fresh"


def _has_critical_error(messages: list[str]) -> bool:
    return any(pattern.search(message) for message in messages for pattern in CRITICAL_ERROR_PATTERNS)


def _schema_errors(task_card: dict[str, Any], schema: dict[str, Any]) -> tuple[list[str], str]:
    backend = "jsonschema"
    try:
        errors = schema_validate_with_jsonschema(task_card, schema)
    except Exception:
        backend = "fallback"
        errors = schema_validate_fallback(task_card, schema)
    return errors, backend


def _build_task_card(row: dict[str, Any], index: int, now_stamp: str) -> dict[str, Any]:
    task_id = str(_pick_first(row, ("task_id", "taskId", "id", "ID"), f"TASK_UNKNOWN_{index:03d}")).strip()
    title = str(_pick_first(row, ("title", "name", "task_name"), f"Task {task_id}"))
    state = _normalize_state(str(_pick_first(row, ("state", "status", "stage", "lifecycle_state"), "inbox")))
    role = _normalize_role(str(_pick_first(row, ("owner_role", "ownerRole", "role"), "Builder")))
    owner_id = str(_pick_first(row, ("owner_id", "ownerId", "owner", "assignee"), "unknown-owner")).strip()

    verification = _normalize_verification(
        _pick_first(row, ("verification", "verification_commands", "checks"), [])
    )
    blockers = _normalize_blockers(_pick_first(row, ("blockers", "issues", "risks"), []))

    task_card = {
        "id": task_id,
        "title": title.strip() or f"Task {task_id}",
        "state": state,
        "priority": _normalize_priority(str(_pick_first(row, ("priority", "severity"), "medium"))),
        "owner_role": role,
        "owner_id": owner_id or "unknown-owner",
        "claimed_until": _pick_first(row, ("claimed_until", "claimedUntil", "lease_until", "leaseUntil"), None),
        "artifacts": [str(item).strip() for item in _coerce_list(_pick_first(row, ("artifacts", "changed_paths"), [])) if str(item).strip()],
        "verification": verification,
        "blockers": blockers,
        "next_action": str(_pick_first(row, ("next_action", "nextAction"), "triage")).strip() or "triage",
        "created_at": str(_pick_first(row, ("created_at", "createdAt", "created_time"), now_stamp)).strip(),
        "updated_at": str(_pick_first(row, ("updated_at", "updatedAt", "last_edited_time"), now_stamp)).strip(),
    }
    return task_card


def build_overlay(
    rows: list[dict[str, Any]],
    schema: dict[str, Any],
    now_dt: datetime,
    adapter_mode: bool,
    allow_runtime_coupled: bool,
) -> dict[str, Any]:
    checked_at = now_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    overlays: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        task_card = _build_task_card(row, index, checked_at)
        schema_errors, schema_backend = _schema_errors(task_card, schema)
        semantic_errors, semantic_warnings = validate_task_card_semantics(task_card, now=now_dt)

        previous_state = str(_pick_first(row, ("from_state", "previous_state", "prior_state"), "")).strip()
        lifecycle_errors: list[str] = []
        if previous_state:
            runtime_text = "\n".join(
                [
                    task_card.get("next_action", ""),
                    "\n".join(str(item.get("command", "")) for item in task_card.get("verification", [])),
                ]
            )
            lifecycle_result = validate_transition(
                from_state=previous_state,
                to_state=str(task_card.get("state", "")),
                actor_role=str(task_card.get("owner_role", "")),
                actor_id=str(task_card.get("owner_id", "")),
                author_id=str(_pick_first(row, ("author_id", "authorId"), "")),
                claimed_until=str(task_card.get("claimed_until") or ""),
                now=now_dt,
                adapter_mode=adapter_mode,
                allow_runtime_coupled=allow_runtime_coupled,
                runtime_text=runtime_text,
            )
            lifecycle_errors.extend(lifecycle_result.get("errors", []))

        handoff = _extract_handoff(row)
        handoff_complete, missing_handoff = _handoff_complete(handoff, str(task_card.get("state", "")))
        handoff_messages = [f"missing handoff field: {field}" for field in missing_handoff]

        runtime_blocked = False
        if adapter_mode and not allow_runtime_coupled:
            runtime_text = task_card.get("next_action", "") + "\n" + "\n".join(
                str(item.get("command", "")) for item in task_card.get("verification", [])
            )
            runtime_blocked = is_runtime_coupled(runtime_text)

        messages: list[str] = []
        messages.extend(schema_errors)
        messages.extend(semantic_errors)
        messages.extend(lifecycle_errors)
        messages.extend(handoff_messages)
        messages.extend(semantic_warnings)

        protocol_state_valid = str(task_card.get("state", "")) in ALLOWED_STATES
        protocol_owner_valid = str(task_card.get("owner_role", "")) in ALLOWED_ROLES

        gate_status = "pass"
        if messages:
            gate_status = "fail" if _has_critical_error(messages) or runtime_blocked else "warn"

        lease_health = _lease_health(str(task_card.get("state", "")), task_card.get("claimed_until"), now_dt)

        overlays.append(
            {
                "task_id": str(task_card.get("id", "")),
                "title": str(task_card.get("title", "")),
                "protocol_state_valid": protocol_state_valid,
                "protocol_owner_valid": protocol_owner_valid,
                "protocol_handoff_complete": handoff_complete,
                "protocol_runtime_coupled_blocked": runtime_blocked,
                "protocol_blockers_count": len(messages),
                "protocol_gate_status": gate_status,
                "protocol_last_checked_at": checked_at,
                "protocol_messages": messages,
                "lease_health": lease_health,
                "schema_backend": schema_backend,
                "state": str(task_card.get("state", "")),
                "owner_role": str(task_card.get("owner_role", "")),
            }
        )

    totals = {
        "tasks": len(overlays),
        "pass": sum(1 for row in overlays if row["protocol_gate_status"] == "pass"),
        "warn": sum(1 for row in overlays if row["protocol_gate_status"] == "warn"),
        "fail": sum(1 for row in overlays if row["protocol_gate_status"] == "fail"),
        "stale_lease": sum(1 for row in overlays if row["lease_health"] == "stale"),
        "missing_handoff": sum(1 for row in overlays if not row["protocol_handoff_complete"]),
    }

    return {
        "status": "ok",
        "generated_at": checked_at,
        "totals": totals,
        "overlays": overlays,
    }


def render_markdown(payload: dict[str, Any], source_label: str) -> str:
    lines: list[str] = []
    lines.append("# Protocol Dashboard Overlay")
    lines.append("")
    lines.append(f"- source: {source_label}")
    lines.append(f"- generated_at: {payload.get('generated_at', '')}")

    totals = payload.get("totals") or {}
    for key in ("tasks", "pass", "warn", "fail", "stale_lease", "missing_handoff"):
        lines.append(f"- {key}: {totals.get(key, 0)}")

    lines.append("")
    lines.append("| Task ID | Gate | Lease | Handoff | Blockers | Why |")
    lines.append("|---|---|---|---|---:|---|")
    for row in payload.get("overlays") or []:
        messages = row.get("protocol_messages") or []
        why = "<br>".join(messages[:2]) if messages else ""
        lines.append(
            "| "
            + f"{row.get('task_id', '')} | {row.get('protocol_gate_status', '')} | {row.get('lease_health', '')} | "
            + f"{'yes' if row.get('protocol_handoff_complete') else 'no'} | {row.get('protocol_blockers_count', 0)} | {why} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _write(path: str, content: str) -> None:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()

    now_dt = parse_iso8601(args.now) if args.now else datetime.now(timezone.utc)
    if now_dt is None:
        now_dt = datetime.now(timezone.utc)

    input_path = Path(args.input_json).expanduser().resolve()
    schema_path = Path(args.schema).expanduser().resolve()

    if not schema_path.exists():
        print(json.dumps({"status": "error", "error": f"schema file not found: {schema_path}"}, indent=2))
        return 2

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    if not input_path.exists():
        degraded = {
            "status": "degraded",
            "generated_at": now_iso(),
            "source": args.source_label,
            "message": f"task source unavailable: {input_path}",
            "totals": {"tasks": 0, "pass": 0, "warn": 0, "fail": 0, "stale_lease": 0, "missing_handoff": 0},
            "overlays": [],
        }
        output = json.dumps(degraded, indent=2)
        print(output)
        if args.output_json:
            _write(args.output_json, output + "\n")
        if args.output_markdown:
            _write(args.output_markdown, render_markdown(degraded, args.source_label))
        return 0

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    rows = _extract_tasks(payload, args.task_array_key)

    overlay = build_overlay(
        rows=rows,
        schema=schema,
        now_dt=now_dt,
        adapter_mode=args.adapter_mode,
        allow_runtime_coupled=args.allow_runtime_coupled,
    )
    overlay["source"] = args.source_label
    overlay["input"] = str(input_path)

    output = json.dumps(overlay, indent=2)
    print(output)

    if args.output_json:
        _write(args.output_json, output + "\n")
    if args.output_markdown:
        _write(args.output_markdown, render_markdown(overlay, args.source_label))

    if args.fail_on_gate_fail and (overlay.get("totals") or {}).get("fail", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
