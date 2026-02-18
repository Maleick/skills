# App-Server Compaction Listener

Use `scripts/app_server_compaction_listener.py` to watch compaction signals and trigger memory handoff automatically.

## Setup

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export AUTO_MEMORY_DIR="$CODEX_HOME/skills/auto-memory"
```

## One-command launcher

Start listener with defaults:

```bash
"$AUTO_MEMORY_DIR/scripts/start_auto_memory_listener.sh"
```

Defaults:
- project: sanitized current directory name (fallback `workspace`)
- objective: carry-forward compaction recovery objective
- reinjection output: `$CODEX_HOME/tmp/auto-memory-reinjection.txt`
- action log: `$CODEX_HOME/tmp/auto-memory-listener.log`
- reinjection mode: emits `turn/start` JSON-RPC request payloads

Common overrides:

```bash
AUTO_MEMORY_PROJECT="workspace" \
AUTO_MEMORY_OBJECTIVE="Continue task execution after compaction." \
AUTO_MEMORY_QUERY="blockers next step" \
AUTO_MEMORY_OUTPUT_FRAMING="jsonl" \
"$AUTO_MEMORY_DIR/scripts/start_auto_memory_listener.sh"
```

## What It Watches

- Request method: `thread/compact/start`
- Notification method: `thread/compacted`
- Event payloads containing `type: "context_compacted"`

## What It Does

1. Run `compaction_handoff.py --mode pre` when `thread/compact/start` appears.
2. Run `compaction_handoff.py --mode post` when compaction completes.
3. Optionally emit a `turn/start` JSON-RPC request with `reinjection_prompt`.

## Basic Usage

Read a protocol stream from stdin and emit a `turn/start` request in JSONL framing:

```bash
python3 "$AUTO_MEMORY_DIR/scripts/app_server_compaction_listener.py" \
  --project "<project>" \
  --objective "<objective>" \
  --inject-turn-start \
  --output-framing jsonl \
  --prompt-out "/tmp/auto-memory-reinjection.txt" \
  --jsonl-log "/tmp/auto-memory-listener.log"
```

Replay an existing event capture:

```bash
python3 "$AUTO_MEMORY_DIR/scripts/app_server_compaction_listener.py" \
  --project "<project>" \
  --input-file "/path/to/events.jsonl" \
  --inject-turn-start
```

## Output Notes

- With `--inject-turn-start`, emitted payloads are valid JSON-RPC requests for method `turn/start`.
- Choose `--output-framing lsp` to emit `Content-Length` framed requests for LSP-style transports.
- `--prompt-out` stores the latest reinjection prompt so an external process can reuse it.
- `start_auto_memory_listener.sh` accepts passthrough listener flags after env defaults.
