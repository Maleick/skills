# Compaction Handoff

Use this flow to preserve context through compaction.
This flow works standalone and can also be consumed by `self-improve` or `ralph-wiggum-loop`.

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
- `reinjection_prompt_chars`
- `reinjection_prompt_estimated_tokens`

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
- `reinjection_prompt_chars`
- `reinjection_prompt_estimated_tokens`

Use `reinjection_prompt` immediately as the first context payload in the resumed conversation.

## Listener Integration

- Compaction mode only:
  - `AUTO_MEMORY_MODE=compaction "$AUTO_MEMORY_DIR/scripts/start_auto_memory_listener.sh"`
- Combined compaction + auto-save mode:
  - `AUTO_MEMORY_MODE=both "$AUTO_MEMORY_DIR/scripts/start_auto_memory_listener.sh"`

Compaction handoff behavior is unchanged by auto-save mode.
