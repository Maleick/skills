# Phase 10: History and Autofix Suggestions - Research

**Researched:** 2026-02-26
**Domain:** Deterministic historical snapshots, trend summaries, and dry-run autofix guidance
**Confidence:** HIGH

## User Constraints

### Locked Decisions
- Snapshot/history output is opt-in and must not change default console behavior.
- Snapshot payloads must be deterministic for identical inputs.
- Snapshot data must contain run/tier/severity/skill aggregates needed for trend analysis.
- Snapshot data must avoid sensitive content and store normalized metadata only.
- Existing file-overwrite safety behavior remains: fail by default, overwrite only when forced.
- Trend summaries compare against deterministic baseline and remain additive to existing report contracts.
- Dry-run autofix suggestions are non-mutating and deterministic.
- Unsupported findings are reported as unsupported for suggestions, not fabricated.
- History/autofix functionality must work with full scan, changed-files mode, and CI flows without changing gate semantics.
- Invalid configuration and invalid artifact arguments are runtime/config errors (`exit 2`).

### Claude's Discretion
- Exact flag names for history/trend/autofix controls.
- Exact artifact file naming for output-dir defaults.
- Exact text format for trend/suggestion summaries.
- Initial supported rule set for autofix suggestions.

### Deferred Ideas (Out of Scope)
- Apply-mode autofix that edits files (`FIX-02`).
- First-class two-snapshot delta artifact beyond baseline trend summary (`HIST-02`).
- Cross-repo/federated history and hosted dashboards.

## Summary

Phase 10 should be delivered as additive CLI capabilities that preserve current scan, report, and CI behavior by default. The safest implementation pattern is:

1. Build a deterministic snapshot model derived from existing index payload structures.
2. Add trend comparison helpers over snapshot summaries (current vs baseline).
3. Add dry-run autofix suggestion generation as an explicit opt-in output path.

**Primary recommendation:** Introduce focused modules (`history.py`, `autofix.py`) and wire them through `cli.py` via explicit flags, reusing existing sorting/summary logic so output determinism remains consistent with prior phases.

## Proposed Runtime Architecture

### Snapshot layer (`history.py`)
- Build snapshot payload from:
  - `index_payload["summary"]`
  - `index_payload["skills"]` (reduced trend-safe skill metadata)
  - `scan_metadata` (`mode`, `compare_range`, scope counts, policy/cache metadata)
- Include schema version and deterministic ordering.
- Provide helpers:
  - `build_history_snapshot(index_payload, findings, scan_metadata, repo_root)`
  - `write_history_snapshot(path, payload, force_overwrite)`
  - `load_history_snapshot(path)`

### Trend layer (`history.py`)
- Compare current snapshot to baseline snapshot.
- Emit deterministic deltas for:
  - global finding totals
  - per-severity totals
  - per-tier totals
  - per-skill status transitions where changed
- Missing baseline should be non-fatal with explicit status text.

### Autofix layer (`autofix.py`)
- Add deterministic suggestion model:
  - `rule_id`
  - `path`
  - `severity`
  - `reason`
  - `suggested_change`
  - optional `preview`
- Implement explicit supported-rule mapping (initially limited, deterministic, read-only).
- Provide helpers:
  - `build_autofix_suggestions(findings)`
  - `render_autofix_console(...)`
  - `render_autofix_markdown(...)`

## CLI Integration Strategy

### New opt-in controls (naming finalized in implementation)
- History snapshot output path flag.
- Trend summary enable flag and optional baseline path flag.
- Autofix suggestion output enable/path flag.

### Compatibility guarantees
- No new flags used => current behavior unchanged.
- Existing `--json`, `--json-out`, `--markdown-out`, `--output-dir`, `--force-overwrite`, `--ci` semantics stay intact.
- CI gating decision remains based only on in-scope severities, not suggestion counts.

## Determinism and Safety Risks

1. **Timestamp-driven nondeterminism in snapshots**
- Mitigation: keep deterministic payload section isolated; if timestamp included, keep under metadata and exclude from parity asserts.

2. **Suggestion order instability**
- Mitigation: sort suggestions by `(severity rank, path, rule_id, message)`.

3. **Scope drift between changed-files and full mode**
- Mitigation: reuse existing scoped `skill_dirs` + `ordered findings` pipeline; never rescan with separate logic for history/autofix.

4. **Output bloat in CI mode**
- Mitigation: compact by default, detailed history/autofix output only with explicit opt-in flags.

## Verification Strategy

1. Snapshot tests
- deterministic snapshot payload for repeated identical runs.
- explicit overwrite behavior for snapshot outputs.
- changed-files metadata presence in snapshots.

2. Trend tests
- baseline compare deltas are deterministic and correctly signed (+/-/0).
- missing baseline emits non-fatal message.
- trend summary additive to existing outputs.

3. Autofix tests
- supported finding classes return deterministic suggestions.
- unsupported findings reported as unsupported.
- no file mutation occurs during suggestion generation.

4. End-to-end CLI tests
- output-flag coexistence with existing flags.
- CI mode still returns the same gate exit-code behavior.
- full test suite remains green.

## Sources

### Primary
- `/opt/skills/.planning/phases/10-history-and-autofix-suggestions/10-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/indexing.py`
- `/opt/skills/tools/skill_audit/reporting.py`
- `/opt/skills/tools/skill_audit/markdown_report.py`
- `/opt/skills/tools/skill_audit/findings.py`
- `/opt/skills/tools/skill_audit/tests/test_output_options.py`
- `/opt/skills/tools/skill_audit/tests/test_cache.py`

---
*Phase: 10-history-and-autofix-suggestions*
*Research completed: 2026-02-26*
