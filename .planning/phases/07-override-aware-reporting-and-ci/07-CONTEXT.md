# Phase 7: Override-Aware Reporting and CI - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 surfaces effective override/scope metadata across validator outputs and ensures CI gate behavior remains deterministic under active override policies. Scope is limited to reporting and CI semantics over existing scan, override parsing, and policy resolution behavior. It does not introduce new override profile selection features.

</domain>

<decisions>
## Implementation Decisions

### Output metadata contract
- Console, JSON, and markdown outputs must include effective policy profile metadata in addition to existing scan scope metadata.
- Metadata should clearly identify whether repository overrides are active and where policy came from (`default` vs `.skill-audit-overrides.yaml`).
- Metadata should summarize effective override profile shape using deterministic counts (tier overrides, rule overrides, rule+tier overrides).

### CI semantics under overrides
- CI threshold evaluation must continue to run on translated findings after override policy resolution.
- Tier scope filters (`--tiers`) apply after override translation and before threshold comparison.
- CI output must echo active policy profile metadata and current scope metadata so gate decisions are auditable.

### Backward compatibility constraints
- Existing CLI flags and exit code contracts remain unchanged.
- Non-override runs must preserve prior behavior except for additive metadata visibility.
- Deterministic ordering and stable payload shape must be preserved for repeated identical runs.

### Metadata shape defaults
- JSON payload should include policy profile metadata in the existing scan metadata block.
- Console/markdown/CI should include concise policy profile lines, not full verbose override maps.
- Reporting format remains additive; no removal of existing scope/count lines.

### Claude's Discretion
- Exact field names and output line wording, as long as semantics stay explicit and deterministic.
- Internal helper placement for rendering profile metadata.
- Minimal additional compatibility test coverage beyond locked requirement set.

</decisions>

<specifics>
## Specific Ideas

- Keep metadata human-scannable in console and CI while maintaining machine-readable detail in JSON.
- Prioritize deterministic regression tests that prove CI evaluates translated severities under active overrides.

</specifics>

<deferred>
## Deferred Ideas

- Multi-profile selection surfacing and profile switching UX.
- Historical profile/override trend reporting.

</deferred>

---

*Phase: 07-override-aware-reporting-and-ci*
*Context gathered: 2026-02-25*
