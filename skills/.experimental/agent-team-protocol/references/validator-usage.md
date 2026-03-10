# Protocol Validator Usage

## Task card validator

Validate a task card with schema + semantic checks:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_task_card.py" \
  --input "$CODEX_HOME/skills/agent-team-protocol/references/fixtures/task-card-valid.json"
```

Machine-readable output:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_task_card.py" \
  --input "$CODEX_HOME/skills/agent-team-protocol/references/fixtures/task-card-valid.json" \
  --output json
```

Custom schema and deterministic time anchor:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_task_card.py" \
  --input /path/to/task-card.json \
  --schema "$CODEX_HOME/skills/agent-team-protocol/references/task-card-schema.json" \
  --now "2026-02-19T00:00:00Z"
```

## Lifecycle validator

Validate a state transition with role, authority, lease, and non-self-approval checks:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_lifecycle.py" \
  --from-state assigned \
  --to-state in_progress \
  --actor-role Builder \
  --actor-id builder-01 \
  --author-id orchestrator-01 \
  --claimed-until "2099-01-01T00:00:00Z"
```

Adapter-mode runtime-coupled guard:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_lifecycle.py" \
  --from-state assigned \
  --to-state in_progress \
  --actor-role Builder \
  --adapter-mode \
  --runtime-text "openclaw cron add --session isolated" \
  --output json
```

## Simulation runner

Run all eight simulation cases and emit JSON + Markdown evidence:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/run_protocol_simulations.py" \
  --json-out "/Users/maleick/Downloads/clawhub_skill_audit_2026-02-19/session-reports/protocol-simulation-results.json" \
  --markdown-out "/Users/maleick/Downloads/clawhub_skill_audit_2026-02-19/session-reports/protocol-simulation-results.md"
```

Run selected cases only:

```bash
python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/run_protocol_simulations.py" \
  --case 4 \
  --case 6
```

## Exit codes

- `0`: validation/simulation passed
- `1`: validation denied or one/more simulation cases failed
- `2`: runtime/usage error
