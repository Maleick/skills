# Phase 9: Named Policy Profiles - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 adds named override policy profiles so maintainers can switch policy contexts deterministically without editing repository policy files per run. Scope is limited to profile schema, profile selection, strict validation, and consistent cross-mode application. It does not add profile inheritance, profile composition, or policy history dashboards.

</domain>

<decisions>
## Implementation Decisions

### Profile config contract
- Canonical policy file remains `.skill-audit-overrides.yaml` at repo root.
- Config must support a named profile collection under an explicit profile map key (for example `profiles`).
- Each named profile uses the existing severity-override model from Phase 6 (`tier`, `rule`, `rule_tier`) rather than introducing new rule-behavior controls.
- Legacy single-profile shape remains accepted for backward compatibility and is treated as an implicit default profile.

### Active profile selection behavior
- Exactly one profile is active per run.
- CLI provides explicit profile selector flag(s) to choose profile by name.
- When no selector is provided, selection resolves deterministically: explicit default profile in config first, then legacy implicit default behavior.
- If multiple named profiles exist and no deterministic default can be resolved, fail with actionable runtime/config error (`exit 2`) instead of guessing.

### Validation and error semantics
- Unknown top-level/profile keys, unknown profile names, unknown rule IDs, malformed YAML, and schema violations are runtime/config errors (`exit 2`).
- Selecting a profile that is not defined is a runtime/config error (`exit 2`) with a clear profile-name diagnostic.
- Missing override file remains non-error and falls back to base default policy behavior.
- Validation stays strict and deterministic; no silent ignore of malformed or unknown profile data.

### Runtime application and determinism
- Selected profile applies consistently in default mode, CI mode, and changed-files mode.
- Profile selection is resolved once per invocation and used uniformly for finding translation, gate decisions, and output rendering.
- Deterministic precedence inside active profile remains unchanged from Phase 6: `rule+tier > rule > tier > base default`.
- Cache identity must incorporate active profile identity/signature so profile switching cannot reuse stale policy translations.

### Output and observability requirements
- Scan metadata must report active profile identity deterministically in JSON, console, markdown, and CI outputs.
- Reporting surfaces should make it obvious which profile was active and where policy came from.
- Existing contracts remain additive: no removal of existing policy metadata fields or CI summary lines.

### Claude's Discretion
- Exact selector flag name(s) and aliases (single canonical selector remains required).
- Exact config key names for profile map/default marker as long as schema is strict and deterministic.
- Exact wording of profile-related diagnostics and output lines.
- Optional compatibility warnings when loading legacy single-profile format.

</decisions>

<specifics>
## Specific Ideas

- Keep common profile naming ergonomic for operators (for example `strict`, `balanced`, `experimental`).
- Ensure CI logs show profile context up front so gate failures are directly traceable to profile choice.
- Preserve compatibility for repositories already using single-profile overrides while encouraging migration to named profiles.

</specifics>

<deferred>
## Deferred Ideas

- Profile inheritance/composition (base profile + overrides).
- Environment-based auto-selection and profile fallback chains.
- Multi-profile comparison output in a single run.
- Historical profile efficacy reporting and drift analytics.

</deferred>

---

*Phase: 09-named-policy-profiles*
*Context gathered: 2026-02-26*
