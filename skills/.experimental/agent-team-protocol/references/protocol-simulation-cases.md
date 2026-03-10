# Protocol Simulation Cases

1. Parallel claim collision
- Two workers try to claim one `assigned` task. Expected: exactly one lease holder.

2. Stale lease recovery
- An `in_progress` task has expired `claimed_until`. Expected: deterministic orchestrator re-claim path.

3. Reviewer conflict
- Reviewer A passes while Reviewer B fails. Expected: escalation state and explicit tie-break rule.

4. Non-self approval
- Builder attempts to approve own task in `review`. Expected: rejection.

5. Memory isolation
- Query project A memory tags while task belongs to project B. Expected: no cross-project recall.

6. Runtime-coupled guard
- Task references direct OpenClaw command in adapter mode. Expected: blocked unless explicitly allowed.

7. Ralph bounded-loop compliance
- One task attempts multi-change iteration. Expected: reject due to one-change policy.

8. Self-improve gate compliance
- Smoke passes and regression fails. Expected: final decision `reject`.
