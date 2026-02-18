#!/usr/bin/env python3
"""Pre/post-compaction memory handoff helper for auto-memory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    MemoryValidationError,
    ensure_project_name,
    memory_dir_for_project,
    merge_tags,
    next_note_path,
    normalize_sections,
    normalize_tags,
    render_sections,
    write_note,
)

DEFAULT_POST_QUERY = "latest compaction checkpoint decisions blockers next step"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and restore pre/post compaction memory context.")
    parser.add_argument("--project", required=True, help="Project scope for memory operations.")
    parser.add_argument("--mode", choices=("pre", "post"), required=True, help="Run pre- or post-compaction phase.")
    parser.add_argument("--query", default="", help="Memory query used to gather context.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum memory results to include.")
    parser.add_argument("--objective", default="", help="Current objective to preserve through compaction.")
    parser.add_argument("--session-label", default="", help="Optional human-friendly session label.")
    parser.add_argument("--title", default="", help="Optional explicit checkpoint title.")
    parser.add_argument("--tags", default="compaction,checkpoint", help="Checkpoint tags.")
    summary_group = parser.add_mutually_exclusive_group()
    summary_group.add_argument("--summary", default="", help="Checkpoint summary text.")
    summary_group.add_argument("--summary-file", default="", help="File containing checkpoint summary text.")
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_summary(args: argparse.Namespace) -> str:
    if args.summary:
        return args.summary.strip()
    if args.summary_file:
        return Path(args.summary_file).read_text(encoding="utf-8").strip()
    return ""


def run_load_memory(project: str, query: str, limit: int) -> dict[str, Any]:
    script = Path(__file__).with_name("load_memory.py")
    command = [
        sys.executable,
        str(script),
        "--project",
        project,
        "--query",
        query,
        "--limit",
        str(limit),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"load_memory failed: {completed.stderr.strip() or completed.stdout.strip()}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("load_memory returned invalid JSON output.") from exc


def build_checkpoint_note(summary: str, objective: str) -> str:
    effective_summary = summary or "Compaction checkpoint captured before context compression."
    body = (
        "## Summary\n"
        f"- {effective_summary}\n\n"
        "## Context\n"
        "- Automatic checkpoint before conversation compaction.\n\n"
        "## Decision\n"
        "- Preserve current objective, constraints, and in-flight plan through compaction.\n\n"
        "## Rationale\n"
        "- Prevent loss of critical context after conversation compression.\n\n"
        "## Implementation\n"
        "- Save checkpoint note and load relevant historical memory.\n\n"
        "## Verification\n"
        "- Confirm post-compaction reinjection prompt includes objective and recent highlights.\n\n"
        "## Follow-ups\n"
        f"- Objective carry-forward: {objective or 'unspecified'}\n"
    )
    required, extras = normalize_sections(body)
    return render_sections(required, extras=extras)


def build_reinjection_prompt(
    project: str,
    objective: str,
    query: str,
    checkpoint_file: str | None,
    memory_payload: dict[str, Any],
) -> str:
    results = memory_payload.get("results", []) or []
    lines: list[str] = []
    lines.append(f'Resume the compacted session for project "{project}".')
    if objective:
        lines.append(f"Primary objective: {objective}")
    if checkpoint_file:
        lines.append(f"Checkpoint note: {checkpoint_file}")
    lines.append(f"Memory query used: {query}")
    lines.append("Recovered memory snippets:")

    if not results:
        lines.append("- No relevant memory found. Ask for missing context before proceeding.")
    else:
        for index, result in enumerate(results[:8], start=1):
            title = result.get("title", "(untitled)")
            date = result.get("date", "")
            tags = ", ".join(result.get("tags", []) or [])
            lines.append(f"{index}. {title} | {date} | tags: {tags}")
            highlights = result.get("highlights", []) or []
            for highlight in highlights[:2]:
                cleaned = " ".join(str(highlight).split())
                lines.append(f"- {cleaned}")

    lines.append("Next step: continue execution from the latest checkpoint unless the user changes direction.")
    return "\n".join(lines)


def pre_mode(args: argparse.Namespace, project: str) -> dict[str, Any]:
    memory_dir = memory_dir_for_project(project)
    memory_dir.mkdir(parents=True, exist_ok=True)

    timestamp = utc_now_iso()
    label = args.session_label.strip() or "session"
    title = args.title.strip() or f"compaction-checkpoint: {label} {timestamp}"
    summary = load_summary(args)
    tags = merge_tags(normalize_tags(args.tags.split(",")), ["compaction", "checkpoint"])

    checkpoint_path = next_note_path(memory_dir, title)
    frontmatter = {
        "title": title,
        "date": timestamp,
        "project": project,
        "tags": tags,
    }
    checkpoint_body = build_checkpoint_note(summary=summary, objective=args.objective.strip())
    write_note(checkpoint_path, frontmatter, checkpoint_body)

    query = args.query.strip() or DEFAULT_POST_QUERY
    memory_payload = run_load_memory(project=project, query=query, limit=max(1, args.limit))
    reinjection_prompt = build_reinjection_prompt(
        project=project,
        objective=args.objective.strip(),
        query=query,
        checkpoint_file=str(checkpoint_path),
        memory_payload=memory_payload,
    )

    return {
        "status": "ok",
        "mode": "pre",
        "project": project,
        "checkpoint_file": str(checkpoint_path),
        "memory_payload": memory_payload,
        "reinjection_prompt": reinjection_prompt,
    }


def post_mode(args: argparse.Namespace, project: str) -> dict[str, Any]:
    query = args.query.strip() or DEFAULT_POST_QUERY
    memory_payload = run_load_memory(project=project, query=query, limit=max(1, args.limit))
    results = memory_payload.get("results", []) or []
    checkpoint_file = None
    if results:
        first = results[0]
        filename = first.get("filename")
        if filename:
            checkpoint_file = str(memory_dir_for_project(project) / filename)

    reinjection_prompt = build_reinjection_prompt(
        project=project,
        objective=args.objective.strip(),
        query=query,
        checkpoint_file=checkpoint_file,
        memory_payload=memory_payload,
    )
    return {
        "status": "ok",
        "mode": "post",
        "project": project,
        "checkpoint_file": checkpoint_file,
        "memory_payload": memory_payload,
        "reinjection_prompt": reinjection_prompt,
    }


def main() -> int:
    args = parse_args()
    try:
        project = ensure_project_name(args.project)
    except MemoryValidationError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2

    try:
        if args.mode == "pre":
            result = pre_mode(args, project)
        else:
            result = post_mode(args, project)
    except Exception as exc:
        print(json.dumps({"status": "error", "mode": args.mode, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
