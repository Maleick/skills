# Phase 4: CI Gate Hardening - Research

**Researched:** 2026-02-25
**Domain:** CI threshold gating semantics and deterministic CLI exit behavior
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Add dedicated `--ci` mode for CI-oriented gate behavior.
- Use `--max-severity {valid,warning,invalid}` as the gating threshold model.
- Default CI threshold is `warning`, so CI fails on `invalid` findings by default.
- Warning-tolerant behavior must be tier-scoped and requires explicit `--tiers` scope.
- `--tiers` controls gate scope (not just output filtering).
- Exit codes are split by outcome: policy fail `1`, runtime/config fail `2`, pass `0`.
- CI output is compact by default; full issue detail requires explicit `--verbose-ci`.
- Non-CI behavior must remain unchanged.
- Documentation must cover CI usage in `README.md` and `contributing.md`.

### Claude's Discretion
- Exact compact-output line formatting in CI mode.
- Internal helper split for parsing tiers and evaluating policy exceedance.
- Minor parser normalization details that do not alter locked public behavior.

### Deferred Ideas (OUT OF SCOPE)
- CI workflow provisioning (`.github/workflows`) in this phase.
- Advanced policy presets/baselines/trend gates.
- Incremental changed-files CI gate variants and autofix policy integrations.

</user_constraints>

<research_summary>
## Summary

Phase 4 can be implemented with minimal risk by layering a CI-only policy path on top of the existing findings pipeline:
1. Reuse existing scanner/rules/tier policy translation.
2. Add CI argument contract parsing and config validation.
3. Compute in-scope findings (all findings by default, tier-filtered when `--tiers` is provided).
4. Evaluate threshold exceedance and emit policy return code (`1`) only in CI mode.
5. Preserve existing non-CI render/exit behavior as a compatibility guard.

This path isolates new semantics to explicit CI invocation and keeps current developer workflows stable.

**Primary recommendation:** keep policy evaluation logic explicit and deterministic in CLI (or a small helper module), and lock behavior with subprocess-level tests.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Scope First, Then Threshold
- Parse/validate `--tiers` into normalized set.
- Build an in-scope finding slice based on resolved tiers.
- Evaluate threshold only against in-scope findings.

### Pattern 2: CI Mode as Explicit Behavior Switch
- `--ci` gates compact output and policy-based return code path.
- `--verbose-ci` is legal only when `--ci` is enabled.
- Default report mode remains unchanged when `--ci` is absent.

### Pattern 3: Deterministic Rank-Based Gate Check
- Define stable severity rank map: `valid=0`, `warning=1`, `invalid=2`.
- Gate failure when any in-scope finding rank exceeds configured max rank.
- Keep this comparison centralized and covered by matrix tests.
</architecture_patterns>

<implementation_notes>
## Implementation Notes

- Add parser flags in `tools/skill_audit/cli.py`:
  - `--ci`
  - `--max-severity`
  - `--tiers`
  - `--verbose-ci`
- Add tier parser/validator for `system,curated,experimental` values.
- Enforce config errors (`return 2`) for:
  - invalid/empty `--tiers`,
  - `--verbose-ci` without `--ci`,
  - warning-tolerant mode request without explicit scope.
- In CI mode, print compact summary by default and detailed findings only with `--verbose-ci`.
- Preserve existing JSON/markdown output artifact behavior.
</implementation_notes>

<test_strategy>
## Test Strategy

- New subprocess regression suite: `test_ci_gating.py`
  - default CI behavior,
  - strict/tolerant/report-only thresholds,
  - scope filtering,
  - return-code matrix,
  - config error cases.
- Extend `test_output_options.py`
  - assert CI mode coexists with output flags.
- Full suite run for `tools/skill_audit/tests` to verify backward compatibility.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/04-ci-gate-hardening/04-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- Current implementation:
  - `/opt/skills/tools/skill_audit/cli.py`
  - `/opt/skills/tools/skill_audit/policy.py`
  - `/opt/skills/tools/skill_audit/reporting.py`
  - `/opt/skills/tools/skill_audit/tests/test_output_options.py`

</sources>

---

*Phase: 04-ci-gate-hardening*
