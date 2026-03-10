# Phase 9: Named Policy Profiles - Research

**Researched:** 2026-02-26
**Domain:** Override policy profile governance for deterministic CLI validation
**Confidence:** HIGH

## User Constraints

### Locked Decisions
- Canonical policy file remains `.skill-audit-overrides.yaml` at repo root.
- Config supports named profile collection with strict schema validation.
- Each named profile uses existing severity override model (`tier`, `rule`, `rule_tier`) only.
- Exactly one active profile per run; CLI selects explicitly by name.
- Deterministic selection: explicit default profile first, then legacy implicit default fallback.
- If multiple profiles exist and no deterministic default resolves, fail with runtime/config error (`exit 2`).
- Unknown keys/profile names/rule IDs and malformed config fail fast with actionable runtime/config errors (`exit 2`).
- Missing override file remains non-error for default behavior.
- Selected profile applies consistently in default, CI, and changed-files modes.
- Output surfaces must include active profile identity deterministically.
- Cache identity must include active profile identity/signature.

### Claude's Discretion
- Selector flag naming (`--profile` vs other aliasing).
- Exact top-level key names for profile map/default marker.
- Exact output wording for profile metadata and diagnostics.
- Optional compatibility warning language for legacy single-profile format.

### Deferred Ideas (Out of Scope)
- Profile inheritance/composition.
- Environment-based auto-selection fallback chains.
- Multi-profile comparison in one run.
- Historical profile analytics.

## Summary

Phase 9 should evolve override loading from a single implicit profile into a deterministic profile-selection system while keeping strict validation behavior from Phase 6 intact. The safest path is additive schema support with explicit named profiles, explicit default profile routing, and legacy compatibility as an implicit `default` profile.

The CLI should resolve profile selection exactly once, then pass the resolved profile object (and profile identity metadata) through all existing scan/gate/report flows. This preserves deterministic behavior and avoids mode-specific divergence.

**Primary recommendation:** Introduce a new loader API that returns both profile data and profile identity metadata, wire a single `--profile` selector in CLI, and lock behavior with cross-mode subprocess regression tests.

## Configuration Contract Strategy

### Proposed additive schema

Support both modes in `.skill-audit-overrides.yaml`:

1. Legacy mode (existing, still valid):

```yaml
version: 1
severity_overrides:
  tier: {}
  rule: {}
  rule_tier: {}
```

2. Named profile mode (new):

```yaml
version: 1
default_profile: strict
profiles:
  strict:
    tier: {}
    rule: {}
    rule_tier: {}
  balanced:
    tier: {}
    rule: {}
    rule_tier: {}
```

### Deterministic resolution rules

1. If `--profile <name>` is passed: select `<name>` or fail (`exit 2`) if unknown.
2. Else if named profiles mode with `default_profile`: select that profile.
3. Else if named profiles mode has exactly one profile: select it.
4. Else if named profiles mode has multiple profiles and no default: fail (`exit 2`).
5. Else if legacy mode: treat as implicit profile `default`.
6. Missing file with no requested profile: return no override profile (base defaults).
7. Missing file with requested profile: fail (`exit 2`) because selected profile is undefined.

## Integration Points

### Override loader and metadata

- `override_config.py` should expose a structured selection result containing:
  - parsed `OverrideProfile`
  - selected `profile_name`
  - selection source (`explicit`, `config-default`, `single-profile`, `legacy-default`)
- `build_policy_profile_metadata` should include additive identity fields while keeping current fields stable:
  - `profile_name`
  - `selection`
  - optional `available_profiles` count/list

### CLI runtime

- Add explicit selector flag: `--profile <name>`.
- Resolve profile once at startup and reuse for:
  - finding translation (`apply_tier_policy`)
  - cache signature generation
  - JSON scan metadata
  - console/markdown/CI output rendering

### Cache coupling

- `build_policy_profile_signature` should include both profile content and selected profile name to guarantee deterministic invalidation on profile switches.

## Determinism and Compatibility Risks

### High-risk edge cases

1. Config containing both legacy `severity_overrides` and new `profiles` keys.
   - Recommendation: fail fast as ambiguous schema.

2. Multiple profiles with no `default_profile` and no `--profile`.
   - Recommendation: fail with actionable message requiring explicit selection.

3. Existing tests asserting exact metadata shape.
   - Recommendation: keep existing fields unchanged and add new fields additively.

4. Cache parity tests comparing full payloads.
   - Recommendation: keep deterministic metadata and update expected profile identity fields.

## Test and Verification Strategy

1. Override config unit tests
- Parse valid named-profile config.
- Parse valid legacy config unchanged.
- Unknown profile selection returns `OverrideConfigError`.
- Missing requested profile file returns config error.
- Ambiguous schema (legacy + profiles) returns config error.
- Multi-profile without default/selector returns config error.

2. CLI subprocess tests
- `--profile` applies selected profile deterministically.
- Default profile resolution in named mode without selector.
- CI/default/changed-files parity under selected profile.
- Output metadata includes active profile identity fields.

3. Cache parity tests
- Profile switch invalidates cache path deterministically.
- Same profile repeated run yields cache hit without contract drift.

## Sources

### Primary
- `/opt/skills/.planning/phases/09-named-policy-profiles/09-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/override_config.py`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/cache.py`
- `/opt/skills/tools/skill_audit/tests/test_override_config.py`
- `/opt/skills/tools/skill_audit/tests/test_output_options.py`
- `/opt/skills/tools/skill_audit/tests/test_ci_gating.py`

---
*Phase: 09-named-policy-profiles*
*Research completed: 2026-02-26*
