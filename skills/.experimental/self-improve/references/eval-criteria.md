# Eval Criteria

## Required Gates

1. Smoke gate:
- Run `smoke_command`.
- Pass condition: exit code `0`.

2. Regression gate:
- Run `regression_command`.
- Pass condition: exit code `0`.

## Acceptance Rule

- Accept iteration only if both gates pass.
- Reject iteration if either gate fails.
- On reject, capture failing command + short error evidence in memory note.
- Run each gate exactly once per iteration (no in-iteration retries).
- Keep one-change-per-iteration semantics strict:
  - if a change is rejected, queue a new single change for the next iteration.

## Minimum Evidence

- Record command string.
- Record exit code.
- Record first relevant failure line or summary.
- Record decision reason tied to gate result.

## Clean Pass Definition

Count a clean pass when all are true:
- smoke gate passes
- regression gate passes
- no meaningful code/doc diff is produced by the iteration
- portability checks still pass
