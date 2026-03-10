# Phase 2: Metadata Integrity Rules - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning
**Mode:** Auto (`$gsd-discuss-phase 2 --auto`)

<domain>
## Phase Boundary

Add metadata-integrity validation on top of the Phase 1 scanner foundation: tier-aware severity policy behavior, `SKILL.md` to `agents/openai.yaml` parity checks, and local reference-path validation for skill packages.

</domain>

<decisions>
## Implementation Decisions

### Tier policy behavior (SCAN-03)
- Keep a strict baseline for `.system` and `.curated`; required-contract failures in these tiers remain `invalid`.
- Apply warning-biased behavior to `.experimental` for non-critical metadata drift, but do not suppress true contract failures.
- Preserve stable rule IDs regardless of tier; only severity can be policy-adjusted.
- Report the final severity deterministically so maintainers can compare runs without ambiguity.

### SKILL.md ↔ openai.yaml parity (META-02)
- Validate parity only when both files are present in a skill directory.
- Compare explicitly mapped fields (`name`, `description`, and other directly mapped metadata keys) using normalized string comparison.
- Emit one finding per mismatched field with both source paths and a concrete remediation hint.
- Missing counterpart files should surface through dedicated findings, not be silently skipped.

### Local reference-path validation (META-03)
- Validate only local repository paths declared by skill docs/metadata (`scripts/`, `references/`, `assets/`, and explicit local file references).
- Ignore web URLs and non-local references.
- Resolve relative paths from the owning skill directory and flag unresolved targets with localized path context.
- Path checks remain read-only; no auto-fix or file creation in this phase.

### Output and operator ergonomics
- Continue using one primary validator command path; metadata-integrity rules are part of the same scan pass.
- Keep finding messages remediation-first so maintainers can fix issues in one pass.
- Runtime/tool failures must remain clearly distinguishable from rule findings.

### Claude's Discretion
- Exact field-mapping table for `SKILL.md` and `openai.yaml` parity checks.
- Parser choice and extraction strategy for local references in markdown/yaml.
- Internal module layout and helper boundaries for policy resolution and rule execution.

</decisions>

<specifics>
## Specific Ideas

- Experimental tier should remain visible in reports (not ignored), but policy should reduce noisy blocking results for intentional experimentation.
- Parity findings should identify both the mismatched key and canonical source of truth expected by the rule.
- Reference-path findings should include the unresolved path exactly as written plus the resolved lookup base.

</specifics>

<deferred>
## Deferred Ideas

- JSON index generation and markdown remediation report formatting (Phase 3).
- CI fail-threshold and warning-tolerant gate modes (Phase 4).
- Incremental scan mode and autofix suggestions (future work).

</deferred>

---

*Phase: 02-metadata-integrity-rules*
*Context gathered: 2026-02-25*
