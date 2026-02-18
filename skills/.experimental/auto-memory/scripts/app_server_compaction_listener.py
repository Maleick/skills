#!/usr/bin/env python3
"""Listen for app-server compaction events and trigger memory handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, BinaryIO, Iterator

from common import MemoryValidationError, ensure_project_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Watch app-server event stream for compaction and run auto memory handoff."
    )
    parser.add_argument("--project", required=True, help="Project scope for memory operations.")
    parser.add_argument("--objective", default="", help="Objective carried into reinjection prompts.")
    parser.add_argument("--query", default="", help="Optional memory query override.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum memory results per handoff.")
    parser.add_argument(
        "--input-file",
        default="",
        help="Read app-server messages from a file instead of stdin.",
    )
    parser.add_argument(
        "--prompt-out",
        default="",
        help="Write latest reinjection prompt to this file.",
    )
    parser.add_argument(
        "--jsonl-log",
        default="",
        help="Append listener actions as JSONL records.",
    )
    parser.add_argument(
        "--inject-turn-start",
        action="store_true",
        help="Emit a turn/start JSON-RPC request to stdout after post-compaction handoff.",
    )
    parser.add_argument(
        "--output-framing",
        choices=("jsonl", "lsp"),
        default="jsonl",
        help="Framing for emitted turn/start request payloads.",
    )
    parser.add_argument(
        "--request-id-prefix",
        default="auto-memory",
        help="Prefix for emitted turn/start request IDs.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error stderr logs.",
    )
    return parser.parse_args()


def _log(message: str, quiet: bool = False) -> None:
    if quiet:
        return
    print(message, file=sys.stderr, flush=True)


def _write_jsonl(path: str, payload: dict[str, Any]) -> None:
    if not path:
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _iter_payload_text(stream: BinaryIO) -> Iterator[str]:
    """Yield JSON payload text from either LSP framing or raw JSONL."""
    while True:
        first = stream.readline()
        if not first:
            return
        if not first.strip():
            continue

        lowered = first.lower()
        if lowered.startswith(b"content-length:"):
            try:
                length = int(first.split(b":", 1)[1].strip())
            except ValueError:
                continue
            while True:
                header = stream.readline()
                if not header:
                    return
                if header in (b"\r\n", b"\n"):
                    break
            body = stream.read(length)
            if not body:
                return
            yield body.decode("utf-8", errors="replace")
            continue

        yield first.decode("utf-8", errors="replace").strip()


def _extract_thread_id(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("threadId", "thread_id"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        for value in payload.values():
            found = _extract_thread_id(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _extract_thread_id(value)
            if found:
                return found
    return None


def _contains_context_compacted(payload: Any) -> bool:
    if isinstance(payload, dict):
        if payload.get("type") == "context_compacted":
            return True
        return any(_contains_context_compacted(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_context_compacted(value) for value in payload)
    return False


def _run_handoff(
    mode: str,
    project: str,
    objective: str,
    query: str,
    limit: int,
) -> dict[str, Any]:
    script_path = Path(__file__).with_name("compaction_handoff.py")
    cmd = [
        sys.executable,
        str(script_path),
        "--project",
        project,
        "--mode",
        mode,
        "--limit",
        str(max(1, limit)),
    ]
    if objective:
        cmd.extend(["--objective", objective])
    if query:
        cmd.extend(["--query", query])
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "handoff execution failed")
    return json.loads(completed.stdout)


def _emit_turn_start(
    output_framing: str,
    request_id_prefix: str,
    thread_id: str,
    prompt: str,
    counter: int,
) -> None:
    request = {
        "id": f"{request_id_prefix}-{counter}",
        "method": "turn/start",
        "params": {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt}],
        },
    }
    serialized = json.dumps(request, ensure_ascii=False)
    if output_framing == "lsp":
        payload = serialized.encode("utf-8")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        sys.stdout.buffer.write(header + payload)
        sys.stdout.buffer.flush()
        return

    print(serialized, flush=True)


def _record_event(
    log_path: str,
    event: str,
    mode: str,
    thread_id: str | None,
    result: dict[str, Any] | None,
    error: str | None,
) -> None:
    _write_jsonl(
        log_path,
        {
            "ts": int(time.time()),
            "event": event,
            "mode": mode,
            "thread_id": thread_id,
            "status": "ok" if error is None else "error",
            "checkpoint_file": None if not result else result.get("checkpoint_file"),
            "error": error,
        },
    )


def main() -> int:
    args = parse_args()
    try:
        project = ensure_project_name(args.project)
    except MemoryValidationError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    source: BinaryIO
    source_file = None
    if args.input_file:
        source_file = open(args.input_file, "rb")
        source = source_file
    else:
        source = sys.stdin.buffer

    last_thread_id: str | None = None
    seen_keys: set[str] = set()
    inject_counter = 0

    _log("auto-memory listener started", quiet=args.quiet)
    if args.prompt_out:
        Path(args.prompt_out).parent.mkdir(parents=True, exist_ok=True)

    try:
        for payload_text in _iter_payload_text(source):
            try:
                message = json.loads(payload_text)
            except json.JSONDecodeError:
                continue

            method = message.get("method") if isinstance(message, dict) else None
            params = message.get("params") if isinstance(message, dict) else None
            thread_id = _extract_thread_id(message) or last_thread_id
            if thread_id:
                last_thread_id = thread_id

            event_kind = None
            mode = None
            if method == "thread/compact/start":
                event_kind = "thread/compact/start"
                mode = "pre"
            elif method == "thread/compacted":
                event_kind = "thread/compacted"
                mode = "post"
            elif _contains_context_compacted(message):
                event_kind = "context_compacted"
                mode = "post"

            if not mode:
                continue

            dedupe_key = f"{event_kind}:{thread_id}:{json.dumps(params, sort_keys=True, default=str)}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            _log(f"detected {event_kind}, running {mode} handoff", quiet=args.quiet)
            result: dict[str, Any] | None = None
            err: str | None = None
            try:
                result = _run_handoff(
                    mode=mode,
                    project=project,
                    objective=args.objective.strip(),
                    query=args.query.strip(),
                    limit=max(1, args.limit),
                )
                prompt = (result.get("reinjection_prompt") or "").strip()
                if prompt and args.prompt_out:
                    Path(args.prompt_out).write_text(prompt + "\n", encoding="utf-8")
                if mode == "post" and prompt and args.inject_turn_start and thread_id:
                    inject_counter += 1
                    _emit_turn_start(
                        output_framing=args.output_framing,
                        request_id_prefix=args.request_id_prefix,
                        thread_id=thread_id,
                        prompt=prompt,
                        counter=inject_counter,
                    )
            except Exception as exc:
                err = str(exc)
                _log(f"handoff error: {err}", quiet=False)

            _record_event(
                log_path=args.jsonl_log,
                event=event_kind,
                mode=mode,
                thread_id=thread_id,
                result=result,
                error=err,
            )
    finally:
        if source_file:
            source_file.close()

    _log("auto-memory listener stopped", quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
