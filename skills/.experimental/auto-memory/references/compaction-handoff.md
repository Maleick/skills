# Compaction Handoff

Use this flow to preserve context through compaction.

## Setup

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export AUTO_MEMORY_DIR="$CODEX_HOME/skills/auto-memory"
```

## Pre-Compaction

Run:

```bash
python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" \
  --project "<project>" \
  --mode pre \
  --objective "<objective>" \
  --summary "<current state and blockers>"
```

Expected output fields:
- `checkpoint_file`
- `memory_payload`
- `reinjection_prompt`

## Post-Compaction

Run:

```bash
python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" \
  --project "<project>" \
  --mode post \
  --objective "<objective>"
```

Expected output fields:
- `memory_payload`
- `reinjection_prompt`

Use `reinjection_prompt` immediately as the first context payload in the resumed conversation.
