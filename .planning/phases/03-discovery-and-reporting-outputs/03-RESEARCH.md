# Phase 3: Discovery and Reporting Outputs - Research

**Researched:** 2026-02-25
**Domain:** Stable JSON index and markdown remediation rendering on canonical findings
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- JSON output includes all discovered skills and computes per-skill status by worst severity.
- Required JSON fields include path, tier, status, finding counts, severity counts, and key metadata fields.
- JSON requires top-level global, per-tier, and per-severity summary blocks.
- Markdown output groups by severity first, then skill, with full actionable issue details.
- Valid findings appear in markdown totals only, not per-item listings.
- Default run remains console-only; file outputs require explicit paths and fail on existing targets unless force is set.
- Deterministic ordering is required for stable repeated-run diffs.

### Claude's Discretion
- Exact optional metadata keys in index records beyond required core set.
- Internal module boundaries for serialization and CLI output routing.
- Markdown heading/section wording as long as required grouping/detail semantics are preserved.

### Deferred Ideas (OUT OF SCOPE)
- CI threshold modes and warning-tolerant gating (Phase 4).
- Incremental scan mode, autofix, historical trend artifacts (future work).
- Additional backward-compat contracts outside current CLI behavior.

</user_constraints>

<research_summary>
## Summary

Phase 3 should layer structured output generation on top of the existing findings pipeline without changing rule semantics. The lowest-risk sequence is:
1. Normalize findings into per-skill aggregates.
2. Emit deterministic JSON index and summaries.
3. Emit markdown grouped views from the same aggregate model.
4. Lock deterministic behavior with regression tests.

This ensures JSON and markdown totals always reconcile and keeps implementation compact.

**Primary recommendation:** add dedicated output modules (`indexing.py`, `markdown_report.py`) and keep CLI orchestration thin.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: One Aggregate Model, Multiple Renderers
- Build one `SkillIndexEntry` + aggregate summary structure.
- JSON and markdown both consume this structure.
- Prevents drift between machine and human outputs.

### Pattern 2: Deterministic Ordering at Aggregate Layer
- Sort tiers, skills, and findings before rendering.
- Avoid renderer-specific sorting differences.
- Use stable severity rank (`invalid`, `warning`, `valid`) for report grouping.

### Pattern 3: Explicit Output Routing
- Console remains default.
- `--json-out` and `--markdown-out` are explicit path controls.
- Fail if target exists unless `--force-overwrite` is set.
</architecture_patterns>

<implementation_notes>
## Implementation Notes

- Reuse existing `Finding` records and translated severities after policy application.
- Derive tier from path using existing policy helper.
- Build per-skill aggregate with:
  - `path`, `tier`, `status`, `finding_count`, `severity_counts`, `metadata` subset.
- Produce top-level JSON summary:
  - `skill_count`, `severity_totals`, `tier_totals`.
- Markdown format should include:
  - summary header and totals,
  - severity sections (`invalid`, `warning`),
  - skill subheadings with issue bullets containing rule/path/message/fix.
</implementation_notes>

<test_strategy>
## Test Strategy

- `test_indexing.py`
  - verifies per-skill aggregation, worst-severity status, and summary reconciliation.
- `test_markdown_report.py`
  - verifies grouping/order rules and omission of valid per-item details.
- `test_output_options.py`
  - verifies console-only default and overwrite protections with explicit file outputs.
- Determinism checks:
  - repeated-run equality for JSON/markdown outputs in fixtures.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/03-discovery-and-reporting-outputs/03-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- Existing output/finding pipeline in:
  - `/opt/skills/tools/skill_audit/cli.py`
  - `/opt/skills/tools/skill_audit/findings.py`
  - `/opt/skills/tools/skill_audit/reporting.py`
  - `/opt/skills/tools/skill_audit/policy.py`

</sources>

---

*Phase: 03-discovery-and-reporting-outputs*
