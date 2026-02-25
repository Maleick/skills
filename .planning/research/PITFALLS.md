# Pitfalls Research

**Domain:** Adding incremental scan and policy override features to an existing validator
**Researched:** 2026-02-25
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Non-deterministic incremental scope

**What goes wrong:** Changed-files mode emits unstable output ordering and mismatched counts.

**How to avoid:** Normalize and sort filtered scope before rule execution and rendering.

**Warning signs:** Repeated runs on same diff produce different output ordering.

**Phase to address:** Phase 5.

---

### Pitfall 2: Silent override fallback

**What goes wrong:** Invalid override config is ignored and default policy is applied silently.

**How to avoid:** Treat override parse/validation failures as runtime/config error with explicit message.

**Warning signs:** CI output does not disclose active profile source.

**Phase to address:** Phase 6.

---

### Pitfall 3: Scope confusion in CI gate

**What goes wrong:** Gate result reflects partial scope but appears as full-repo verdict.

**How to avoid:** Echo scope source (`full` vs `changed` vs `tier-filtered`) in CI output and artifacts.

**Warning signs:** Failing builds without clear indication of filtered scope.

**Phase to address:** Phase 7.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| ad-hoc regex parsing of git output | quick implementation | path edge-case bugs | never for shipped CLI behavior |
| copying policy logic into cli branches | fast prototyping | behavior drift and brittle tests | never |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| filtering findings after full scan every time | little speed gain | prune scope before heavy rule execution where possible | medium-large repos |
| repeated YAML parse for every file | avoidable overhead | parse override once per command | frequent CI runs |

## "Looks Done But Isn't" Checklist

- [ ] Incremental mode tested for renamed/deleted paths.
- [ ] Override config validation tested for malformed YAML and invalid keys.
- [ ] CI output explicitly shows effective scope and profile source.
- [ ] JSON/markdown determinism preserved under incremental and override modes.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Non-deterministic incremental scope | Phase 5 | deterministic subprocess tests over same changed-set input |
| Silent override fallback | Phase 6 | invalid config returns exit 2 with explicit error |
| Scope confusion in CI gate | Phase 7 | CI output assertions include scope/profile echo |

## Sources

- Existing v1.0 regression patterns and verification artifacts.
- Existing CLI CI-gating behavior in `tools/skill_audit/cli.py`.

---
*Pitfalls research for: v1.1 performance + policy milestone*
*Researched: 2026-02-25*
