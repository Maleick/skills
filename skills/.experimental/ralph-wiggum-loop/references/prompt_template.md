# Ralph Loop Iteration Prompt

## Goal
{{goal}}

## Constraints
{{constraints}}

## Repository Summary (bounded)
{{repo_summary}}

## Last Outcome
{{last_outcome}}

## Recent Failure Log Snippets
{{recent_failures}}

## Recent Failing Test Output (bounded)
{{failing_output}}

## Loop Memory (last N iterations)
{{loop_memory}}

## Single-Step Instruction
{{single_step_instruction}}

## Response Contract
Return exactly one change-set as JSON with this shape:

```json
{
  "kind": "single_change_set",
  "summary": "short summary",
  "changes": [
    {
      "path": "relative/path.py",
      "op": "replace_text",
      "target": "old",
      "replacement": "new",
      "count": 1
    }
  ]
}
```
