# Prompt Contract

## Required Input Object

```json
{
  "project": "string",
  "objective": "string",
  "repo_path": "absolute path",
  "smoke_command": "string",
  "regression_command": "string",
  "constraints": ["string"],
  "memory_query": "string (optional)",
  "iteration_cap": "number (optional, default 1 for this invocation)"
}
```

Rules:
- `project`, `objective`, `repo_path`, `smoke_command`, `regression_command` are mandatory.
- If any mandatory field is missing, ask and stop before planning changes.
- Plan exactly one bounded change-set per iteration.
- If objective appears already satisfied, return explicit no-op while keeping the required output schema unchanged.
- Never plan more than one verification pass per gate in a single iteration.

## Required Iteration Output Object

```json
{
  "iteration_id": "YYYYMMDD-HHMMSS",
  "hypothesis": "string",
  "planned_change": "string",
  "expected_impact": "string",
  "eval_plan": {
    "smoke_command": "string",
    "regression_command": "string"
  },
  "eval_results": {
    "smoke": {"status": "pass|fail", "evidence": "string"},
    "regression": {"status": "pass|fail", "evidence": "string"}
  },
  "decision": "accept|reject",
  "memory_note": {
    "title": "string",
    "body_markdown": "string with required auto-memory sections"
  },
  "fallback_local_note": {
    "path": ".self-improve/memory/<timestamp>-iteration.md",
    "enabled_when_auto_memory_missing": true
  },
  "next_step": "string"
}
```

Rules:
- `decision=accept` only when both gate statuses are `pass`.
- `memory_note.body_markdown` must include sections:
  `Summary`, `Context`, `Decision`, `Rationale`, `Implementation`, `Verification`, `Follow-ups`, `Changelog`.
- `planned_change` must describe one change-set only.
- `eval_plan` must contain one smoke and one regression command execution only (no retries inside the same iteration).
