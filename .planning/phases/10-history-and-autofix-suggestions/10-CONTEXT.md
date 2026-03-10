# Phase 10: History and Autofix Suggestions - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 adds deterministic history artifacts and dry-run remediation suggestions so maintainers can track quality trends and act faster on known findings. Scope is limited to snapshot generation, trend summary visibility, and non-mutating autofix guidance. It does not introduce automatic file mutation, hosted dashboards, or cross-repo analytics.

</domain>

<decisions>
## Implementation Decisions

### Historical snapshot contract
- Snapshot output is opt-in and must not change default console behavior when no history flag/path is provided.
- Snapshot artifacts must be deterministic for identical inputs (stable key ordering, stable section ordering, stable finding ordering).
- Snapshot payload includes run summary totals, per-tier/per-severity counts, and per-skill status aggregates required for trend tracking.
- Snapshot payload stores normalized relative paths and metadata only; no source file contents or secret material are captured.
- File write behavior follows existing output safety rules: fail on existing file by default, allow overwrite only with explicit force behavior.

### Trend summary behavior
- Trend view compares the current snapshot against a deterministic baseline snapshot (explicit baseline path when provided, otherwise most recent compatible snapshot in the same history stream).
- Trend output must include delta summaries for global totals plus per-severity and per-tier movements.
- Trend entries are deterministic and ordered by severity rank, then skill path, then rule ID where relevant.
- If no baseline is available, emit a clear non-error message and still produce the current snapshot artifact.
- Trend features remain additive and must not break existing JSON/markdown remediation report contracts.

### Dry-run autofix suggestion behavior
- Autofix remains suggestion-only in this phase; no mutation of skill files is allowed.
- Suggestions are generated only for explicitly supported finding classes and must remain deterministic for identical findings.
- Each suggestion includes actionable details: rule ID, target path, issue summary, and proposed change guidance (with preview text where safe).
- Unsupported findings are reported as unsupported for autofix (no fabricated remediation output).
- Suggestion output is opt-in and can be emitted to console and/or explicit artifact path without affecting gate semantics.

### Mode integration and error semantics
- Snapshot/trend/autofix behavior must work consistently in full scan, changed-files, and CI runs without changing existing gate decisions.
- Active policy profile and scan scope metadata must be carried into history artifacts and suggestion context for auditability.
- Invalid configuration, malformed snapshot input, or invalid output argument combinations are runtime/config errors (`exit 2`).
- CI mode stays compact by default; additional history/autofix detail in CI requires explicit opt-in controls.

### Claude's Discretion
- Exact CLI flag names for snapshot, trend summary, and autofix suggestion controls.
- Exact artifact filenames when an output directory is used without explicit output filenames.
- Exact wording/format of suggestion preview blocks and trend summary lines.
- Initial supported finding-class subset for autofix suggestions, as long as behavior is deterministic and non-mutating.

</decisions>

<specifics>
## Specific Ideas

- Keep artifacts easy to consume in CI by using stable machine-readable files plus concise console/trend summaries.
- Ensure trend summaries make regression/improvement direction obvious in one glance (`improved`, `regressed`, `unchanged` framing).
- Keep autofix suggestions copy/paste friendly for maintainers preparing manual patches.

</specifics>

<deferred>
## Deferred Ideas

- Apply-mode autofix with write + rollback safeguards (`FIX-02`).
- First-class two-snapshot diff artifact and normalized delta contract (`HIST-02`).
- Cross-repo/federated trend aggregation and hosted visualization.
- Automatic patch/PR generation from autofix suggestions.

</deferred>

---

*Phase: 10-history-and-autofix-suggestions*
*Context gathered: 2026-02-26*
