# Phase 3: Discovery and Reporting Outputs - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning
**Mode:** Auto (`$gsd-discuss-phase 3 --auto`)

<domain>
## Phase Boundary

Generate stable machine-readable and human-readable reporting artifacts from one canonical findings model: JSON skill index output plus markdown remediation summaries.

</domain>

<decisions>
## Implementation Decisions

### JSON contract priority and defaults
- Include all discovered skills across `.system`, `.curated`, and `.experimental`.
- Per-skill status is derived by worst severity (`invalid > warning > valid`).
- Require per-skill core fields: `path`, `tier`, `status`, `finding_count`, `severity_counts`, and key metadata fields.
- Require top-level summary blocks: global totals, per-tier counts, and per-severity counts.

### Markdown report behavior
- Group report entries by severity first, then by skill.
- Each issue entry must include rule ID, path, message, and suggested fix.
- Show valid findings in summary counts only (do not list each valid finding entry).
- Keep deterministic ordering: severity rank, then path, then rule ID.

### Generation behavior and CLI ergonomics
- Default run remains console output only.
- File output is enabled only by explicit path flags.
- Use stable names when auto-generating filenames from explicit output directories.
- Existing output files fail by default unless an explicit force-overwrite flag is provided.

### Claude's Discretion
- Optional metadata fields beyond the required core per-skill JSON fields.
- Exact markdown section cosmetics and heading wording as long as grouping and detail constraints are preserved.
- Internal module structure for serialization/rendering and argument parsing helpers.

</decisions>

<specifics>
## Specific Ideas

- Output should be immediately useful for maintainers during triage and for CI jobs consuming structured summaries.
- JSON and markdown views should reconcile to the same underlying counts so operators can trust both representations.
- Deterministic ordering is mandatory to keep repeated-run diffs low-noise.

</specifics>

<deferred>
## Deferred Ideas

- CI threshold policy controls and warning-tolerant gate modes (Phase 4).
- Incremental changed-files scan mode, autofix suggestions, and historical trend artifacts (future work).
- Additional backward-compat contract guarantees beyond current CLI behavior (future work).

</deferred>

---

*Phase: 03-discovery-and-reporting-outputs*
*Context gathered: 2026-02-25*
