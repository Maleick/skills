# Phase 2: Metadata Integrity Rules - Research

**Researched:** 2026-02-25
**Domain:** Tier-aware policy rules, metadata parity checks, and local reference validation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep `.system` and `.curated` strict for required contract violations.
- Apply warning-biased behavior for `.experimental` without hiding true invalid states.
- Enforce `SKILL.md` ↔ `agents/openai.yaml` parity using explicit field mapping with actionable output.
- Validate local references (`scripts/`, `references/`, `assets/`, explicit local paths) and ignore web URLs.
- Preserve one primary validator command and keep this phase read-only.

### Claude's Discretion
- Exact parity field mapping and normalization details.
- Parser strategy for markdown/yaml reference extraction.
- Module boundaries for policy and parity rule helpers.

### Deferred Ideas (OUT OF SCOPE)
- JSON index generation and markdown report grouping (Phase 3).
- CI threshold modes and warning-tolerant gates (Phase 4).
- Autofix behavior and incremental scan modes (future work).

</user_constraints>

<research_summary>
## Summary

Phase 2 should extend the current validator with a policy layer rather than changing scanner behavior. The most stable design is:
1. Keep each rule emitting baseline severities.
2. Apply tier policy translation in one centralized place before reporting.
3. Add two new rule packs: metadata parity and local reference checks.

This keeps rule authorship simple and allows policy changes later without rewriting every validator rule.

**Primary recommendation:** introduce `policy.py` and additional rules under `rules/` while preserving the existing findings envelope and CLI entrypoint.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Baseline Rule Output + Policy Translation
- Rules emit semantic severities (`invalid`, `warning`, `valid`) based on objective contract checks.
- Policy resolver applies tier overrides for `.experimental` cases where warning bias is approved.
- CLI output remains deterministic because translation happens before sort/render.

### Pattern 2: Explicit Parity Mapping
- Build a static mapping table for cross-file checks.
- Compare normalized string values.
- Emit one finding per mismatched field to keep remediation granular.

### Pattern 3: Local Path Extraction + Existence Check
- Extract relative paths from predictable skill document conventions.
- Resolve against skill directory.
- Ignore `http://` and `https://` references.
- Emit localized findings with the unresolved path and containing file.
</architecture_patterns>

<implementation_notes>
## Implementation Notes

- Add `skill_tier_for_path()` helper so policies and reporting use the same tier derivation logic.
- Keep existing `Finding` unchanged for compatibility; policy can transform severity while preserving rule IDs.
- For parity checks, parse:
  - `SKILL.md` frontmatter keys (`name`, `description`)
  - `agents/openai.yaml` top-level `name`, `description`
- For local references:
  - Parse markdown links and backticked paths from `SKILL.md`.
  - Validate expected directories `scripts/`, `references/`, and `assets/` when referenced.
  - Return one finding per missing path.
</implementation_notes>

<test_strategy>
## Test Strategy

- `test_policy.py`
  - verifies tier detection and severity translation rules.
- `test_parity_rules.py`
  - verifies field mismatch and missing counterpart behavior.
- `test_reference_rules.py`
  - verifies local path extraction, URL ignore behavior, and missing path findings.
- CLI integration tests should assert severity totals include translated policy results.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/02-metadata-integrity-rules/02-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/*` current Phase 1 implementation
- `/opt/skills/skills/**` existing skill layout and metadata examples

### Secondary
- `PyYAML` parsing behavior for small YAML documents
- Existing repository conventions for skill package structure
</sources>

---

*Phase: 02-metadata-integrity-rules*
