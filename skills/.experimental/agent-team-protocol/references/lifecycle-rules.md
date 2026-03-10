# Lifecycle Rules

## Allowed transitions
- `inbox -> assigned`
- `assigned -> in_progress`
- `in_progress -> review`
- `review -> done`
- `review -> failed`

## Transition authority
- `Orchestrator` can move `inbox -> assigned` and handle reassignment.
- `Builder` can request `assigned -> in_progress` and `in_progress -> review` with evidence.
- `Reviewer` can decide `review -> done|failed`.
- Self-approval is not allowed.

## Parallel safety
- A task in `in_progress` must include a non-expired `claimed_until` lease.
- If lease expires, only orchestrator policy can reassign ownership.
- Task cards must be updated atomically per transition to avoid split-brain state.
