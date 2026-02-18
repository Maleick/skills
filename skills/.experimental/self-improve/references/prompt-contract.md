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
  "memory_query": "string (optional)"
}
```

Rules:
- `project`, `objective`, `repo_path`, `smoke_command`, `regression_command` are mandatory.
- If any mandatory field is missing, ask and stop before planning changes.
- Plan exactly one bounded change per iteration.
- Execute exactly one change-set for that plan in the iteration.
- Run exactly one verification pass (smoke + regression) after applying the change-set.

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
  "next_step": "string"
}
```

Rules:
- `decision=accept` only when both gate statuses are `pass`.
- `memory_note.body_markdown` must include sections:
  `Summary`, `Context`, `Decision`, `Rationale`, `Implementation`, `Verification`, `Follow-ups`, `Changelog`.
- Do not report `accept` when no verification evidence is present for both gates.
