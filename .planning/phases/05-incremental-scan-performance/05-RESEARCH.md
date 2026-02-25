# Phase 5: Incremental Scan Performance - Research

**Researched:** 2026-02-25
**Domain:** Incremental repository scanning and deterministic output contracts for Python CLI tools
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

No phase context file exists for Phase 5. Planning is based on roadmap, requirements, and current implementation.

### Locked Decisions
- Phase target is 5 (`Incremental Scan Performance`) with requirement coverage for `PERF-01`, `PERF-02`, `PERF-03`.
- Planning flow continues without `05-CONTEXT.md`.
- Auto chain keeps execute handoff enabled after plan verification.

### Claude's Discretion
- Exact CLI flag naming for changed-scope discovery and compare-range controls.
- Internal helper boundaries between scanner and CLI modules.
- Exact output metadata shape as long as scope and scanned counts are explicit and deterministic.

### Deferred Ideas (OUT OF SCOPE)
- Persistent cache layer for unchanged-skill metadata (`PERF-04`).
- Autofix or historical trend models.
- Policy override behavior (Phase 6 onward).
</user_constraints>

<research_summary>
## Summary

Current validator behavior always scans all discovered skill directories. This is deterministic but slow for frequent local checks because every run traverses all tiers, even when only one skill changed. The most direct Phase 5 path is to add an optional changed-files scope selector that computes impacted skill directories from git paths, then runs the existing rule stack only on that filtered set.

`PERF-02` is best served by an explicit compare-range argument so maintainers can choose exact scope in CI or local pre-merge checks. The default changed-files mode should still support working-tree deltas for local iteration. A hard runtime/config error model is appropriate when changed-files cannot be computed (invalid range, non-git repository, etc.).

`PERF-03` requires output clarity, not just behavior change. JSON, markdown, and console output should expose stable scan metadata (mode, compare range, changed-file count, impacted-skill count, scanned-skill count, total-skill count) so operators can trust what was actually evaluated.

**Primary recommendation:** add changed-files and compare-range controls in CLI, implement deterministic skill-impact filtering in scanner helpers, and thread a stable scan-metadata object through all output renderers and tests.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Compute Full Catalog, Then Filter Scope
- Keep `discover_skill_dirs()` as the canonical full-scan discovery path.
- Add a deterministic filter layer for impacted skills derived from changed paths.
- Preserve full-scan ordering guarantees by filtering from the already-sorted catalog.

### Pattern 2: Separate Scope Discovery from Validation Execution
- Scanner helpers should only resolve changed files and impacted skill directories.
- CLI decides mode (`full` or `changed-files`) and handles configuration errors.
- Existing validation rules remain unchanged and continue to consume selected skill directories.

### Pattern 3: Stable Metadata Contract for Every Output Channel
- Build a single scan-metadata payload in CLI.
- Attach metadata to JSON index payload.
- Render the same metadata in markdown and console/CI output.
- Avoid volatile fields (timestamps, hashes) to keep output deterministic.
</architecture_patterns>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Non-deterministic changed-file ordering
**What goes wrong:** output diffs fluctuate run-to-run.
**How to avoid:** de-duplicate and sort changed-file lists before scope mapping.

### Pitfall 2: Scope leakage from string prefix checks
**What goes wrong:** non-skill paths incorrectly map into skill scope.
**How to avoid:** normalize to repo-relative paths and map only `skills/.{tier}/{skill}` prefixes.

### Pitfall 3: Silent fallback when compare range is invalid
**What goes wrong:** operators think scoped run succeeded while it silently scanned everything.
**How to avoid:** treat invalid range or git command failures as runtime/config errors (exit `2`).
</common_pitfalls>

<test_strategy>
## Test Strategy

- Scanner unit tests:
  - impacted-skill mapping from changed files,
  - deterministic filtering,
  - compare-range command behavior in a temp git repo.
- CLI subprocess tests:
  - changed-files mode scans only impacted skills,
  - compare-range works and invalid ranges fail fast,
  - outputs include scope/scanned metadata.
- Determinism regression:
  - repeated same-input runs produce byte-stable JSON and markdown outputs.

</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/scanner.py`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/indexing.py`
- `/opt/skills/tools/skill_audit/markdown_report.py`
- `/opt/skills/tools/skill_audit/reporting.py`
- `/opt/skills/tools/skill_audit/tests/test_scanner.py`
- `/opt/skills/tools/skill_audit/tests/test_output_options.py`

</sources>

---

*Phase: 05-incremental-scan-performance*
