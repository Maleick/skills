---
name: agent-team-protocol
description: Canonical multi-agent task protocol for role ownership, lifecycle transitions, handoff packages, and parallel safety. Use when coordinating multiple agents or when integrating team workflows into existing codex skills.
---

# Agent Team Protocol

Use this skill as the canonical contract layer for multi-agent planning and execution.
This skill defines machine-readable schemas and deterministic process rules, but does not assume any specific external runtime provider.

## Scope
- Role model and ownership rules.
- Canonical task card schema.
- Lifecycle transition authority.
- Handoff package contract.
- Parallel safety and escalation constraints.

## Canonical References
- Task card schema: `references/task-card-schema.json`
- Lifecycle and transition guards: `references/lifecycle-rules.md`
- Handoff template: `references/handoff-template.md`
- Simulation scenarios: `references/protocol-simulation-cases.md`
- Validator usage: `references/validator-usage.md`
- Validation fixtures: `references/fixtures/`

## Role Model
- `Orchestrator`: owns task assignment, transition approvals, and escalation decisions.
- `Builder`: executes bounded change sets and provides evidence-backed handoffs.
- `Reviewer`: validates acceptance criteria and cannot self-approve authored work.
- `Ops`: maintains workflow health and state integrity without mutating task intent.

## Lifecycle Contract
- Allowed states: `inbox`, `assigned`, `in_progress`, `review`, `done`, `failed`.
- Only allowed transition path:
  - `inbox -> assigned`
  - `assigned -> in_progress`
  - `in_progress -> review`
  - `review -> done|failed`
- Any other transition is invalid.

## Parallel Safety Contract
- Every in-progress task must carry a lease in `claimed_until`.
- Claim operation must be deterministic and single-owner.
- Expired lease allows deterministic re-claim by orchestrator policy.
- Task IDs and handoff IDs must be globally unique within a project scope.

## Integration Contract With Existing Skills
- `ralph-wiggum-loop`: use bounded one-change iteration and emit protocol-compliant handoff fields.
- `self-improve`: enforce reviewer separation and dual-gate decision policy.
- `auto-memory`: store durable evidence with protocol tags for retrieval isolation.

## Validator Tooling
- Validate task cards:
  - `python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_task_card.py" --input /path/to/task-card.json`
- Validate lifecycle transitions:
  - `python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/validate_lifecycle.py" --from-state assigned --to-state in_progress --actor-role Builder --claimed-until "2099-01-01T00:00:00Z"`
- Run protocol simulations:
  - `python3 "$CODEX_HOME/skills/agent-team-protocol/scripts/run_protocol_simulations.py" --markdown-out /tmp/protocol-sim.md --json-out /tmp/protocol-sim.json`
