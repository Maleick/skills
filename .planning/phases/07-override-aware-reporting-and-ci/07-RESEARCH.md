# Phase 7: Override-Aware Reporting and CI - Research

**Researched:** 2026-02-25
**Domain:** Output metadata surfacing and CI gate determinism under active override profiles
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Console/JSON/markdown outputs must expose effective policy profile metadata.
- Metadata must show whether overrides are active and source (`default` vs `.skill-audit-overrides.yaml`).
- CI gate evaluation remains on translated findings after override resolution.
- Tier scope filtering is applied after override translation and before threshold comparison.
- CI output must echo scope + policy metadata for auditability.
- Existing flags/exit codes remain unchanged; behavior changes are additive and deterministic.

### Claude's Discretion
- Exact field names and output line phrasing.
- Internal helper placement and minor renderer refactors.
- Supplemental regression coverage details beyond required contracts.

### Deferred Ideas (OUT OF SCOPE)
- Multi-profile selection/reporting UX.
- Historical override-profile trends.
</user_constraints>

<research_summary>
## Summary

Phase 6 added strict override parsing and deterministic precedence; Phase 7 should make this behavior explicit in output surfaces and CI diagnostics. The safest approach is to extend the existing scan metadata contract with a normalized policy profile block generated once in CLI and reused across JSON, console, markdown, and CI rendering.

Current CI semantics already evaluate translated findings. Phase 7 should lock this contract with targeted tests that prove threshold decisions are made after overrides and within the active scope filters.

Backward compatibility risk is low if reporting changes are additive and deterministic. Existing automation should continue to parse outputs with minimal adaptation because key sections remain intact and only new lines/fields are appended.

**Primary recommendation:** add a deterministic `policy_profile` metadata block into scan metadata, render concise policy lines across outputs, and add CI regression tests specifically asserting post-override, in-scope threshold behavior.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Single Metadata Source of Truth
- Build one policy-profile metadata object in CLI per invocation.
- Inject it into index payload `scan` block.
- Reuse across renderers to avoid divergent representations.

### Pattern 2: Additive Rendering Strategy
- Preserve existing output lines and sections.
- Append profile metadata lines in console/markdown/CI.
- Keep JSON schema deterministic and explicit.

### Pattern 3: CI Semantics Lock via Subprocess Tests
- Validate gate results under active override + tier scope combinations.
- Assert deterministic behavior across repeated runs and equivalent inputs.
</architecture_patterns>

<metadata_contract>
## Policy Profile Metadata Contract

Proposed normalized block under `scan`:

```json
"policy_profile": {
  "source": "default" | ".skill-audit-overrides.yaml",
  "active": true | false,
  "mode": "single",
  "counts": {
    "tier": 0,
    "rule": 0,
    "rule_tier": 0
  }
}
```

Contract notes:
- `active=false` when override file is absent.
- `source` explicitly identifies policy source.
- `counts` are deterministic summary counts, not raw mapping dumps.
</metadata_contract>

<test_strategy>
## Test Strategy

1. Output metadata tests
- JSON payload contains `scan.policy_profile` for default and override runs.
- Console/markdown include policy-profile lines.
- Existing scope metadata lines remain stable.

2. CI semantics tests
- Override escalation/demotion affects gate result deterministically.
- Tier-scoped gate uses translated findings in selected scope.
- Invalid override config returns exit `2` in CI mode.

3. Compatibility tests
- No-override runs preserve prior pass/fail expectations.
- Repeated same-input runs remain deterministic.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/07-override-aware-reporting-and-ci/07-CONTEXT.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/indexing.py`
- `/opt/skills/tools/skill_audit/reporting.py`
- `/opt/skills/tools/skill_audit/markdown_report.py`
- `/opt/skills/tools/skill_audit/override_config.py`
- `/opt/skills/tools/skill_audit/tests/test_output_options.py`
- `/opt/skills/tools/skill_audit/tests/test_ci_gating.py`

</sources>

---

*Phase: 07-override-aware-reporting-and-ci*
