# Phase 1: Validator Foundation - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a baseline validator command that scans all skill tiers (`.system`, `.curated`, `.experimental`) and reports structured severity findings, including missing/malformed `SKILL.md` detection. This phase does not include advanced parity rules, discovery index generation, or CI gating policies.

</domain>

<decisions>
## Implementation Decisions

### Command behavior
- Provide one primary validation command that scans all three tiers by default in a single run.
- Use deterministic path ordering in findings so repeated runs are stable and comparable.
- Keep the phase output focused on scan/finding fundamentals rather than advanced report formats.

### Findings model
- Findings must include: severity (`valid|warning|invalid`), stable rule ID, path, and short remediation guidance.
- Emit a clear summary with totals by severity at end of run.
- Use human-readable messages optimized for maintainers fixing repository structure issues.

### Validation scope
- Include `SKILL.md` existence/frontmatter validation for skill directories in this phase.
- Keep validation read-only in this phase (no file mutation or autofix behavior).
- Keep baseline severity behavior simple in Phase 1; maturity-tier exception tuning is deferred.

### Execution expectations
- Target a fast local run suitable for pre-merge checks (goal aligned to idea doc: practical and quick feedback).
- Runtime failures should be clearly distinguishable from validation findings.
- Treat this phase as foundation only; downstream phases layer stricter policy and richer outputs.

### Claude's Discretion
- Internal module breakdown for scanner/rule/formatter components.
- Exact CLI flag naming for baseline command.
- Parser/library selection details, as long as outputs honor the decisions above.

</decisions>

<specifics>
## Specific Ideas

- Prioritize one-command maintainability: "scan everything relevant in one pass".
- Keep output actionable first, elegant second; every finding should help a maintainer decide what to fix next.
- Preserve v1 trust with explicit read-only validation behavior.

</specifics>

<deferred>
## Deferred Ideas

- Tier-aware policy exceptions and severity overrides (Phase 2).
- Cross-file metadata parity checks between `SKILL.md` and `agents/openai.yaml` (Phase 2).
- JSON index and markdown discovery/reporting artifacts (Phase 3).
- CI fail-threshold policy modes (Phase 4).
- Incremental changed-files mode and autofix suggestions (future phases).

</deferred>

---

*Phase: 01-validator-foundation*
*Context gathered: 2026-02-25*
