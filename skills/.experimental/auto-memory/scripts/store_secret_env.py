#!/usr/bin/env python3
"""Store secret values in project-scoped .env files (never markdown)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import MemoryValidationError, ensure_project_name, env_dir_for_project

ENV_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Store a secret in $CODEX_HOME/env/<project>/.env."
    )
    parser.add_argument("--project", required=True, help="Project scope for env storage.")
    parser.add_argument("--var", required=True, help="Environment variable name (UPPERCASE).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", help="Secret value.")
    group.add_argument("--value-file", help="File containing the secret value.")
    return parser.parse_args()


def read_value(args: argparse.Namespace) -> str:
    if args.value is not None:
        return args.value
    return Path(args.value_file).read_text(encoding="utf-8").rstrip("\n")


def quote_env_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f"\"{escaped}\""


def upsert_env_line(lines: list[str], key: str, value: str) -> tuple[list[str], str]:
    assignment = f"{key}={quote_env_value(value)}"
    updated = False
    for index, line in enumerate(lines):
        match = ASSIGNMENT_RE.match(line)
        if not match:
            continue
        if match.group(1) == key:
            lines[index] = assignment
            updated = True
            break
    if not updated:
        lines.append(assignment)
    action = "updated" if updated else "created"
    return lines, action


def main() -> int:
    args = parse_args()
    try:
        project = ensure_project_name(args.project)
    except MemoryValidationError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2

    key = args.var.strip()
    if not ENV_KEY_RE.match(key):
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": "var must match ^[A-Z_][A-Z0-9_]*$ (example: SERVICE_API_TOKEN).",
                },
                indent=2,
            )
        )
        return 2

    value = read_value(args)
    if not value:
        print(json.dumps({"status": "error", "error": "secret value must not be empty"}, indent=2))
        return 2

    env_dir = env_dir_for_project(project)
    env_dir.mkdir(parents=True, exist_ok=True)
    env_path = env_dir / ".env"

    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    new_lines, action = upsert_env_line(existing_lines, key, value)
    env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")

    try:
        env_path.chmod(0o600)
    except OSError:
        # Keep operation non-fatal on filesystems that do not support chmod.
        pass

    print(
        json.dumps(
            {
                "status": "ok",
                "action": action,
                "project": project,
                "variable": key,
                "location": str(env_path),
                "hint": "[REDACTED]",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
