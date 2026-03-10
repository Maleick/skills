# Phase 6: Override Policy Profiles - Research

**Researched:** 2026-02-25
**Domain:** Repository-level override policy parsing, validation, and deterministic severity resolution for `tools/skill_audit`
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Override config is repo-root YAML file: `.skill-audit-overrides.yaml`.
- Phase 6 uses a single active profile model.
- Override capability is severity remap only, scoped by tier and/or rule ID.
- Precedence is deterministic: `rule+tier > rule > tier > base default`.
- Unknown keys, unknown rule IDs, malformed YAML, and schema violations must fail fast with runtime/config error (`exit 2`).
- Missing override file is non-error and falls back to defaults.
- Overrides apply consistently in default, CI, and changed-files modes.
- Unknown rule IDs are validated against the current built-in rule registry.

### Claude's Discretion
- Internal module split between config parser and policy resolver helpers.
- Exact wording of validation errors and help text.
- Minor schema ergonomics that do not change locked behavior.

### Deferred Ideas (OUT OF SCOPE)
- Named profiles and profile selector flags (`RULE-03`, later phase).
- Output/profile metadata surfacing in reports (Phase 7).
</user_constraints>

<research_summary>
## Summary

The current policy implementation is static and hard-coded in `policy.py`. Phase 6 should introduce an explicit override config parser that loads once per CLI invocation and returns a validated severity remap profile. The safest path is a strict schema with deterministic merge semantics and explicit error classes consumed by CLI as runtime/config failures.

A small parser module (`override_config.py`) should own file loading, YAML parsing, schema validation, and conversion to typed override structures. Policy resolution stays in `policy.py`, where current base behavior remains the baseline and config-driven remaps are layered deterministically by precedence.

Built-in rule ID validation should use a canonical exported registry from the rules package rather than ad-hoc regex acceptance. This avoids silent drift and ensures unknown rule IDs in config are rejected before scanning.

**Primary recommendation:** introduce a strict typed override config loader + rule ID registry, wire overrides into `apply_tier_policy` in CLI once per run, and lock behavior with parser/policy/CLI matrix tests.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Parse Once, Resolve Everywhere
- Parse `.skill-audit-overrides.yaml` once in CLI.
- Pass resolved override profile into policy translation used by all modes.
- Avoid per-finding config lookups.

### Pattern 2: Strict Schema + Typed Intermediate Model
- Validate YAML shape and allowed keys immediately.
- Convert to typed internal profile structure.
- Reject unknown keys/rules/severities before scanning.

### Pattern 3: Deterministic Multi-scope Precedence
- Evaluate each finding with precedence order:
  1. `rule+tier`
  2. `rule`
  3. `tier`
  4. base default behavior
- Keep this logic centralized and unit tested.
</architecture_patterns>

<schema_contract>
## Proposed Config Contract

```yaml
version: 1
severity_overrides:
  tier:
    experimental: warning
  rule:
    META-001: invalid
  rule_tier:
    experimental:
      META-110: warning
```

Validation rules:
- Required top-level keys: `version`, `severity_overrides`.
- `version` must be integer `1` in Phase 6.
- `severity_overrides` allowed child keys: `tier`, `rule`, `rule_tier` only.
- Tier keys allowed: `system`, `curated`, `experimental`.
- Rule IDs must exist in built-in rule registry.
- Remap target severity must be one of `valid|warning|invalid`.
- Any unknown key or wrong type is a hard config error.
</schema_contract>

<integration_notes>
## Integration Notes

- `cli.py`:
  - load override profile from repo root before scanning,
  - return `2` on config parsing/validation failure,
  - pass resolved profile to policy translation regardless of mode.
- `policy.py`:
  - keep current default behavior as base default,
  - add override-aware resolver with deterministic precedence.
- `rules/__init__.py`:
  - export canonical built-in rule ID set used by parser validation.

</integration_notes>

<test_strategy>
## Test Strategy

1. Parser unit tests (`test_override_config.py`):
- missing file => no profile,
- malformed YAML => config error,
- unknown keys => config error,
- unknown rule IDs => config error,
- valid schema => typed profile output.

2. Policy precedence tests (`test_policy.py`):
- rule+tier beats rule,
- rule beats tier,
- tier beats base default,
- base default used when no override matches.

3. CLI integration tests:
- invalid override file returns exit `2` in default and CI mode,
- valid override influences severity outcomes across default/CI/changed-files runs,
- missing file keeps existing behavior unchanged.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/06-override-policy-profiles/06-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/policy.py`
- `/opt/skills/tools/skill_audit/rules/*.py`
- `/opt/skills/tools/skill_audit/tests/test_policy.py`
- `/opt/skills/tools/skill_audit/tests/test_ci_gating.py`
- `/opt/skills/tools/skill_audit/tests/test_output_options.py`

</sources>

---

*Phase: 06-override-policy-profiles*
