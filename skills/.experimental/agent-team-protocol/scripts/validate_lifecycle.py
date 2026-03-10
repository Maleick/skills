#!/usr/bin/env python3
"""Validate lifecycle transitions and authority rules for protocol tasks."""

from __future__ import annotations

import argparse
import json

from protocol_rules import parse_iso8601, validate_transition


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-state", required=True)
    parser.add_argument("--to-state", required=True)
    parser.add_argument("--actor-role", required=True)
    parser.add_argument("--actor-id", default="")
    parser.add_argument("--author-id", default="")
    parser.add_argument("--claimed-until", default="")
    parser.add_argument("--now", default="")
    parser.add_argument("--adapter-mode", action="store_true")
    parser.add_argument("--allow-runtime-coupled", action="store_true")
    parser.add_argument(
        "--runtime-text",
        default="",
        help="Optional text payload checked for runtime-coupled references when adapter mode is enabled.",
    )
    parser.add_argument("--output", choices=("json", "text"), default="text")
    return parser.parse_args()


def emit_text(result: dict[str, object]) -> None:
    status = "ALLOW" if result.get("allowed") else "DENY"
    print(f"lifecycle transition: {status}")
    print(
        "transition: "
        + f"{result.get('from_state')} -> {result.get('to_state')} "
        + f"(actor_role={result.get('actor_role')})"
    )
    if result.get("errors"):
        print("errors:")
        for row in result.get("errors", []):
            print(f"- {row}")
    if result.get("warnings"):
        print("warnings:")
        for row in result.get("warnings", []):
            print(f"- {row}")


def main() -> int:
    args = parse_args()
    try:
        ts_now = parse_iso8601(args.now) if args.now else None
        claimed_until = args.claimed_until if args.claimed_until else None

        result = validate_transition(
            from_state=args.from_state,
            to_state=args.to_state,
            actor_role=args.actor_role,
            actor_id=args.actor_id,
            author_id=args.author_id,
            claimed_until=claimed_until,
            now=ts_now,
            adapter_mode=args.adapter_mode,
            allow_runtime_coupled=args.allow_runtime_coupled,
            runtime_text=args.runtime_text,
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            emit_text(result)

        return 0 if result.get("allowed") else 1
    except Exception as exc:
        payload = {"status": "error", "error": str(exc)}
        if args.output == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"lifecycle validation error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
