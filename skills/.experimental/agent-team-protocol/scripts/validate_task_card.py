#!/usr/bin/env python3
"""Validate protocol task cards against schema and semantic rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_rules import parse_iso8601, validate_task_card_semantics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to task card JSON file.")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).resolve().parent.parent / "references" / "task-card-schema.json"),
        help="Path to JSON schema file.",
    )
    parser.add_argument(
        "--now",
        default="",
        help="Optional ISO-8601 timestamp used for lease/time checks (defaults to current UTC).",
    )
    parser.add_argument("--output", choices=("json", "text"), default="text")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validate_with_jsonschema(task_card: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    from jsonschema import Draft7Validator

    validator = Draft7Validator(schema)
    errors: list[str] = []
    for row in sorted(validator.iter_errors(task_card), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in row.path)
        location = f"/{path}" if path else "/"
        errors.append(f"schema error at {location}: {row.message}")
    return errors


def schema_validate_fallback(task_card: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required") or []
    properties = schema.get("properties") or {}

    for key in required:
        if key not in task_card:
            errors.append(f"schema fallback: missing required field '{key}'")

    if schema.get("additionalProperties") is False:
        for key in task_card.keys():
            if key not in properties:
                errors.append(f"schema fallback: unexpected field '{key}'")

    for key, value in task_card.items():
        if key not in properties:
            continue
        prop = properties[key] if isinstance(properties[key], dict) else {}
        enum_values = prop.get("enum")
        if enum_values is not None and value not in enum_values:
            errors.append(f"schema fallback: field '{key}' must be one of {enum_values}")

        if prop.get("format") == "date-time" and value is not None:
            try:
                parse_iso8601(str(value))
            except Exception as exc:
                errors.append(f"schema fallback: field '{key}' is not valid date-time ({exc})")

    return errors


def emit_text(result: dict[str, Any]) -> None:
    status = "PASS" if result["valid"] else "FAIL"
    print(f"task-card validation: {status}")
    print(f"schema backend: {result['schema_backend']}")
    print(f"input: {result['input']}")
    if result["errors"]:
        print("errors:")
        for row in result["errors"]:
            print(f"- {row}")
    if result["warnings"]:
        print("warnings:")
        for row in result["warnings"]:
            print(f"- {row}")


def main() -> int:
    args = parse_args()

    try:
        input_path = Path(args.input).expanduser().resolve()
        schema_path = Path(args.schema).expanduser().resolve()
        task_card = load_json(input_path)
        schema = load_json(schema_path)

        if not isinstance(task_card, dict):
            raise ValueError("task card root must be a JSON object")
        if not isinstance(schema, dict):
            raise ValueError("schema root must be a JSON object")

        schema_backend = "jsonschema"
        try:
            schema_errors = schema_validate_with_jsonschema(task_card, schema)
        except Exception:
            schema_backend = "fallback"
            schema_errors = schema_validate_fallback(task_card, schema)

        ts_now = parse_iso8601(args.now) if args.now else None
        semantic_errors, semantic_warnings = validate_task_card_semantics(task_card, now=ts_now)

        result = {
            "valid": len(schema_errors) == 0 and len(semantic_errors) == 0,
            "input": str(input_path),
            "schema": str(schema_path),
            "schema_backend": schema_backend,
            "errors": schema_errors + semantic_errors,
            "warnings": semantic_warnings,
        }

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            emit_text(result)

        return 0 if result["valid"] else 1
    except Exception as exc:
        payload = {"status": "error", "error": str(exc)}
        if args.output == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"task-card validation error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
