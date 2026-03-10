# Phase 6: Override Policy Profiles - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 delivers repository-level policy override configuration and deterministic resolution for the skill validator. Scope is limited to defining, loading, validating, and applying override policy behavior within existing scan and gate workflows. It does not add new reporting surfaces or profile-selection UX beyond a single active profile contract.

</domain>

<decisions>
## Implementation Decisions

### Override config contract
- Override config is a repo-root YAML file.
- Canonical file name is `.skill-audit-overrides.yaml`.
- Phase 6 supports a single active profile model only.

### Override capability scope
- Override behavior in Phase 6 is limited to severity remap policy.
- Remapping may be scoped by tier and/or rule ID.
- Arbitrary rule settings and non-severity behavior switches are out of scope.

### Policy resolution semantics
- Deterministic precedence is required: `rule+tier > rule > tier > base default`.
- Unknown rule IDs in override config are invalid unless they exist in the current built-in rule registry.
- Resolution behavior must be deterministic across repeated runs.

### Validation and error handling
- Unknown keys and unknown rule IDs are runtime/configuration errors.
- Malformed YAML and schema violations are runtime/configuration errors.
- Invalid override configuration must fail fast with actionable diagnostics and exit code `2`.
- Missing override file is non-error and falls back to default policy behavior.

### Runtime application scope
- Overrides apply consistently across all modes: default, CI (`--ci`), and changed-files mode.
- No silent fallback is allowed when override config is present but invalid.

### Claude's Discretion
- Exact internal module split for override parser/resolver helpers.
- Exact error message wording as long as diagnostics are actionable and deterministic.
- Optional minor schema ergonomics that do not alter locked behavior or expand scope.

</decisions>

<specifics>
## Specific Ideas

- Prioritize maintainer and CI ergonomics: policy decisions should be obvious from failures and reproducible across environments.
- Keep the config contract strict enough to prevent drift, but simple enough for repository maintainers to edit safely.

</specifics>

<deferred>
## Deferred Ideas

- Multiple named profiles and profile selector flags (`RULE-03` / later phase).
- Output/report surfacing of effective override profile metadata (Phase 7 scope).

</deferred>

---

*Phase: 06-override-policy-profiles*
*Context gathered: 2026-02-25*
