---
name: self-improve
description: Run a minimal self-improvement loop with one bounded change per iteration, smoke+regression acceptance gates, and durable decision logging through auto-memory. Use when users ask for iterative improvement of prompts, workflows, or code quality over time.
---

# Self Improve

Use this skill to run deterministic, test-gated improvement iterations with durable memory.

## Setup

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export AUTO_MEMORY_DIR="$CODEX_HOME/skills/auto-memory"
```

## Workflow

1. Load prior memory before proposing changes:
   `python3 "$AUTO_MEMORY_DIR/scripts/load_memory.py" --project "<project>" --query "<objective> decisions regressions known-good commands" --limit 8`

2. Plan exactly one bounded change for this iteration using `references/prompt-contract.md`.

3. Execute only that one planned change-set.

4. Run evaluation from `references/eval-criteria.md`:
   - smoke command (required)
   - targeted regression command (required)

5. Decision rule:
   - Accept only if smoke and regression both pass.
   - Reject if either fails.

6. Persist durable outcome via auto-memory:
   `python3 "$AUTO_MEMORY_DIR/scripts/save_memory.py" --project "<project>" --title "<repo>: self-improve iteration <id>" --body "<memory note body>" --tags "self-improve,decision,eval"`

7. Compaction handoff (mandatory when compaction is likely or occurring):
   - pre: `python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" --project "<project>" --mode pre --objective "<objective>" --summary "<state and blockers>"`
   - post: `python3 "$AUTO_MEMORY_DIR/scripts/compaction_handoff.py" --project "<project>" --mode post --objective "<objective>"`
   - Use returned `reinjection_prompt` as first payload after compaction.

8. Never store secrets in markdown memory notes. Use:
   `python3 "$AUTO_MEMORY_DIR/scripts/store_secret_env.py" --project "<project>" --var "<ENV_NAME>" --value "<secret>"`

## Iteration Contract

- One planned change-set per iteration.
- One verification pass (smoke + regression) per iteration.
- No accept decision without both gates passing.
- Record decision evidence for every iteration.

## References

- `references/prompt-contract.md`
- `references/eval-criteria.md`
- `references/auto-memory-integration.md`
