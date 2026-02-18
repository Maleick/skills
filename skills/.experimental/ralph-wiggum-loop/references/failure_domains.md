# Failure Domains and Operator Levers

Use this taxonomy for per-iteration classification and operations tuning.

## `patch_apply_error`
Signals:
- Target file missing, replace target not found, path blocked by guardrails.
Likely causes:
- Over-constrained `allowed_paths`, stale target text, or unsafe path.
Operator levers:
- Constraints change (`allowed_paths`, readonly/dry_run), glue patch for patch parser/apply logic.

## `test_failure`
Signals:
- Test verifier returns non-zero and lint/runtime are not primary blockers.
Likely causes:
- Applied patch did not satisfy test behavior.
Operator levers:
- Prompt tweak (stronger single-step guidance), glue patch for stub heuristics.

## `lint_failure`
Signals:
- Lint verifier returns non-zero while tests may pass.
Likely causes:
- Formatting/static-check issues introduced or pre-existing.
Operator levers:
- Constraints change (run lint only after tests), prompt tweak for style-safe edits.

## `runtime_error`
Signals:
- Command execution exception, interpreter failures, orchestration exception.
Likely causes:
- Environment or command issues, unexpected script crash.
Operator levers:
- Glue patch in runner, constraints change for safer commands.

## `acceptance_unmet`
Signals:
- Verifiers run but configured acceptance criteria remain unmet.
Likely causes:
- Criteria broader than current patch objective.
Operator levers:
- Prompt tweak toward unmet criteria, constraints change for criterion scope.

## `tool_error`
Signals:
- Planner/LLM adapter fails or returns invalid payload.
Likely causes:
- Adapter misconfiguration, malformed response.
Operator levers:
- Glue patch in adapter handling, prompt tweak to tighten response format.
