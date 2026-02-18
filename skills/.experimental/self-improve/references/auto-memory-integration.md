# Auto-memory Integration

## Setup

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export AUTO_MEMORY_DIR="$CODEX_HOME/skills/auto-memory"
```

## Project Selection

- Prefer active session project.
- Else infer from repository folder name.
- Else ask once for project name.

## Load Before Iteration

`python3 "$AUTO_MEMORY_DIR/scripts/load_memory.py" --project "<project>" --query "<objective> previous decisions regressions blockers" --limit 8`

## Save After Decision

`python3 "$AUTO_MEMORY_DIR/scripts/save_memory.py" --project "<project>" --title "<repo>: self-improve iteration <id>" --body "<note>" --tags "self-improve,decision,eval"`

## Compaction Handoff

- Pre: `python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" --project "<project>" --mode pre --objective "<objective>" --summary "<state and blockers>"`
- Post: `python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" --project "<project>" --mode post --objective "<objective>"`

Use `reinjection_prompt` immediately after compaction before continuing.

## Secret Safety

- Never save secret values in memory markdown.
- Persist secrets only with `store_secret_env.py`.
