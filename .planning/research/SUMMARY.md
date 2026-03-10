# Project Research Summary

**Project:** Skills Catalog Quality Layer
**Domain:** Repository quality governance and operator automation
**Researched:** 2026-02-26
**Confidence:** MEDIUM

## Executive Summary

v1.2 should focus on governance and productivity features that scale the current deterministic CLI platform: persistent cache, named policy profiles, historical trend artifacts, and dry-run autofix suggestions. The best path is incremental and compatibility-first: keep existing contracts stable while layering optional capabilities behind explicit flags.

The core recommendation is to phase work by dependency order: cache foundation first, profile model next, then history/autofix features that depend on the first two. This preserves CI trust while reducing implementation risk.

Key risk areas are cache invalidation drift, profile-selection ambiguity across modes, and non-deterministic snapshot payloads. Each risk should be mitigated with dedicated parity and deterministic regression tests.

## Key Findings

### Recommended Stack

Build v1.2 primarily with current Python/pytest/PyYAML stack plus standard library modules (`sqlite3`, `hashlib`, `json`, `difflib`) for cache/history/suggestion support. No new external runtime dependency is required for baseline delivery.

### Expected Features

**Must have (table stakes):**
- `PERF-04` persistent unchanged-skill caching.
- `RULE-03` named profile selection for policy governance.
- `HIST-01` historical run snapshots.

**Should have (competitive):**
- `FIX-01` dry-run autofix suggestions tied to existing finding metadata.

**Defer (future):**
- Autofix apply mode and hosted trend/dashboard UX.

### Architecture Approach

Use a layered extension model: keep `cli.py` as single orchestration boundary, add focused modules (`cache.py`, `history.py`, `autofix.py`), and preserve deterministic output semantics by treating all new features as additive optional layers.

### Critical Pitfalls

1. **Cache correctness drift** — avoid with schema/version-aware fingerprints and parity tests.
2. **Profile selection ambiguity** — avoid with single canonical resolver used by all modes.
3. **Snapshot non-determinism** — avoid by isolating stable payload core from volatile metadata.
4. **Unsafe autofix expectations** — avoid by keeping v1.2 dry-run only with explicit caveats.

## Implications for Roadmap

### Phase 8: Cache Foundation and Deterministic Reuse
**Rationale:** Cache is prerequisite for trend and autofix efficiency while carrying the highest correctness risk.
**Delivers:** `PERF-04` with invalidation and parity test matrix.
**Avoids:** stale cache drift.

### Phase 9: Named Profile Governance
**Rationale:** Profile model affects all finding translation and report/gate semantics.
**Delivers:** `RULE-03` with explicit selector flags and cross-mode consistency checks.
**Uses:** Existing override config and policy translation pathways.

### Phase 10: Historical Trends and Dry-Run Autofix
**Rationale:** Depends on stable cache/profile behaviors and deterministic contracts.
**Delivers:** `HIST-01` + `FIX-01` with deterministic snapshot schema and suggestion output.

### Phase Ordering Rationale

- Cache and profile contracts are foundational dependencies for history/autofix.
- Governance decisions must be resolved before longitudinal artifacts are emitted.
- Determinism gates should remain mandatory across every phase.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 8:** cache invalidation strategy and safe key design.
- **Phase 10:** dry-run suggestion quality thresholds and false-positive controls.

Phases with standard patterns (research optional during planning):
- **Phase 9:** selector/validation flows can build on existing override parser patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Extends existing Python CLI/runtime patterns without new infra. |
| Features | MEDIUM | Backlog is clear, but user-priority ordering may shift. |
| Architecture | MEDIUM | Integration points are known; cache/history details need careful design. |
| Pitfalls | MEDIUM | Risks are clear but mitigation details require phase-specific test design. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Cache storage backend choice (sqlite vs file index only) should be finalized in Phase 8 planning.
- Autofix suggestion boundaries per rule class should be explicitly defined in Phase 10 context/plans.

## Sources

### Primary
- Existing project artifacts: PROJECT, ROADMAP, MILESTONES, phase summaries/verifications.
- Existing code contracts in `tools/skill_audit` and `tools/skill_audit/tests`.

### Secondary
- Deferred requirement backlog captured in v1.1 requirements archive.

---
*Research completed: 2026-02-26*
*Ready for roadmap: yes*
