# Eval Criteria

## Required Gates

1. Smoke gate:
- Run `smoke_command`.
- Pass condition: exit code `0`.

2. Regression gate:
- Run `regression_command`.
- Pass condition: exit code `0`.
- Execute smoke and regression once per iteration (no repeated retries in the same iteration).

## Acceptance Rule

- Accept iteration only if both gates pass.
- Reject iteration if either gate fails.
- On reject, capture failing command + short error evidence in memory note.

## Minimum Evidence

- Record command string.
- Record exit code.
- Record first relevant failure line or summary.
- Record decision reason tied to gate result.
