# Project Research Summary

**Project:** Skills Catalog Quality Layer
**Domain:** Validator performance and policy extensibility
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

v1.1 should prioritize two high-leverage capabilities: incremental changed-files scanning and repository-level policy override configuration. These directly improve validator adoption in larger repositories and multi-team environments while preserving the deterministic behavior established in v1.0.

The recommended approach is evolutionary: keep the existing canonical findings pipeline and add explicit scope/config resolution layers around it. This avoids contract churn in outputs and keeps CI gate semantics stable.

## Key Findings

### Recommended Stack

- Keep Python stdlib-first implementation.
- Add optional `pathspec` for robust path filtering if needed.
- Use existing pytest subprocess pattern for regression safety.

### Expected Features

**Must have (table stakes):**
- Changed-files scan mode.
- Repo override policy file support.
- Output visibility for effective scope/profile.

**Should have (competitive):**
- Fail-fast override diagnostics.
- Scope-aware incremental summaries.

**Defer (v2+):**
- Auto-fix and historical trend reporting.

### Architecture Approach

Retain `cli.py` as orchestrator and add focused helpers for changed-scope and override resolution. Reuse the existing aggregate/reporting stack rather than introducing alternate schemas.

### Critical Pitfalls

1. Non-deterministic incremental filtering.
2. Silent fallback when override config is invalid.
3. CI output ambiguity about scope/profile.

## Implications for Roadmap

### Phase 5: Incremental Scan Performance
- Deliver changed-files scope resolution and deterministic incremental behavior.

### Phase 6: Override Policy Profiles
- Deliver repo-level override config parsing, validation, and effective-policy resolution.

### Phase 7: Override-Aware CI and Reporting
- Deliver explicit scope/profile visibility across default, JSON, markdown, and CI outputs.

### Phase Ordering Rationale

Incremental scope must land before override-aware CI/reporting so later phases can validate behavior on both full and filtered scans with stable policy semantics.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | builds directly on existing v1.0 architecture |
| Features | HIGH | aligns with current deferred items and adoption pressure |
| Architecture | HIGH | incremental extension over proven modules |
| Pitfalls | HIGH | derived from current deterministic CI constraints |

**Overall confidence:** HIGH

## Sources

### Primary
- `.planning/PROJECT.md`
- `.planning/milestones/v1.0-REQUIREMENTS.md`
- `.planning/milestones/v1.0-ROADMAP.md`
- Existing `tools/skill_audit/*` implementation and tests

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
