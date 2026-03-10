# Phase 4: CI Gate Hardening - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning
**Mode:** Auto (`$gsd-discuss-phase 4 --auto`)

<domain>
## Phase Boundary

Add CI-safe gating controls to the existing validator CLI without changing non-CI behavior: dedicated CI mode, threshold-based fail policy, tier-scoped tolerant mode, deterministic exit codes, and CI-focused output ergonomics.

</domain>

<decisions>
## Implementation Decisions

### CI mode and gate threshold model
- Add dedicated `--ci` mode for CI-oriented gating and output behavior.
- Add severity threshold control with `--max-severity {valid,warning,invalid}`.
- Severity ordering is `valid < warning < invalid`.
- Gate fails when any in-scope finding has rank greater than `--max-severity`.

### Defaults and warning-tolerant scope rules
- In CI mode, default threshold is `warning` (therefore fail on `invalid` only).
- `--max-severity valid` is strict mode (fails on warning and invalid).
- `--max-severity invalid` is report-only mode (never fails by severity policy).
- Warning-tolerant behavior is tier-scoped and requires explicit scope.
- `--tiers` is the scope selector and applies to gate decision logic, not just report filtering.

### Tier selector and validation contract
- Add `--tiers` as a comma-separated tier selector with allowed values: `system`, `curated`, `experimental`.
- Unknown tier names, empty tier lists, or malformed values are configuration errors.
- Requesting warning-tolerant mode without explicit `--tiers` is a configuration error.

### Exit codes and CI output shape
- Exit code `0`: success / gate pass.
- Exit code `1`: policy failure (threshold exceeded in-scope).
- Exit code `2`: runtime/configuration error (IO, parsing, invalid combinations).
- CI stdout is compact by default (gate status + threshold/scope + in-scope totals).
- Add `--verbose-ci` to emit full in-scope issue details in CI mode.
- `--verbose-ci` without `--ci` is a configuration error.

### Backward compatibility
- Non-CI invocation behavior remains unchanged.
- Existing output flags (`--json`, `--json-out`, `--markdown-out`, `--output-dir`, `--force-overwrite`) remain supported.

### Documentation targets
- Update both `README.md` and `contributing.md` with CI policy examples.

### Claude's Discretion
- Exact compact-output wording/format in CI mode (as long as it is concise and deterministic).
- Internal helper-module split for parsing/scope evaluation if it improves readability.
- Optional minor normalization details in CLI parsing as long as public behavior matches locked decisions.

</decisions>

<specifics>
## Specific Ideas

- Prioritize maintainers and CI operators being able to understand pass/fail outcomes in one short summary line set.
- Keep policy semantics explicit in output (`mode`, `threshold`, `scope`) to reduce false assumptions in pipelines.
- Ensure tests cover return code matrix and tier-scoped policy behavior to prevent regressions.

</specifics>

<deferred>
## Deferred Ideas

- Phase 5+: workflow provisioning (`.github/workflows`) and org-specific pipeline templates.
- Phase 5+: policy profiles/presets, baseline files, and historical trend gates.
- Phase 5+: incremental changed-files gating and optional auto-fix policy modes.

</deferred>

---

*Phase: 04-ci-gate-hardening*
*Context gathered: 2026-02-25*
