# Roadmap: Skills Catalog Quality Layer

## Milestones

- ✅ **v1.0 MVP** — shipped 2026-02-25 (Phases 1-4, 11 plans). Archive: `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 Performance & Policy** — shipped 2026-02-26 (Phases 5-7, 8 plans). Archive: `.planning/milestones/v1.1-ROADMAP.md`
- 🚧 **v1.2 Governance & Automation** — planned (Phases 8-10)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-02-25</summary>

- [x] **Phase 1: Validator Foundation** — 3/3 plans complete
- [x] **Phase 2: Metadata Integrity Rules** — 3/3 plans complete
- [x] **Phase 3: Discovery and Reporting Outputs** — 3/3 plans complete
- [x] **Phase 4: CI Gate Hardening** — 2/2 plans complete

</details>

<details>
<summary>✅ v1.1 Performance & Policy (Phases 5-7) — SHIPPED 2026-02-26</summary>

- [x] **Phase 5: Incremental Scan Performance** — 3/3 plans complete
- [x] **Phase 6: Override Policy Profiles** — 3/3 plans complete
- [x] **Phase 7: Override-Aware Reporting and CI** — 2/2 plans complete

</details>

### 🚧 v1.2 Governance & Automation (In Progress)

- [x] **Phase 8: Persistent Cache Engine** - Add deterministic unchanged-skill cache pathways and cache correctness gates. (completed 2026-02-26)
- [ ] **Phase 9: Named Policy Profiles** - Add multi-profile override governance with explicit profile selection controls.
- [ ] **Phase 10: History and Autofix Suggestions** - Add trend snapshot artifacts and dry-run remediation suggestions.

## Phase Details

### Phase 8: Persistent Cache Engine
**Goal**: Maintainers can rerun scans faster by reusing unchanged-skill validation state without changing correctness.
**Depends on**: Phase 7
**Requirements**: PERF-04
**Success Criteria** (what must be TRUE):
  1. Maintainer can enable persistent cache usage for unchanged skills.
  2. Cache hit and cache miss paths produce equivalent findings and summary contracts.
  3. Cache invalidation is deterministic for file/content/rule-profile changes.
**Plans**: 3 plans

Plans:
- [x] 08-01: Implement cache key model and storage module.
- [x] 08-02: Integrate cache into scan pipeline with correctness guards.
- [x] 08-03: Add cache parity/invalidations regression tests and docs.

### Phase 9: Named Policy Profiles
**Goal**: Maintainers can define and select named override profiles for different policy contexts.
**Depends on**: Phase 8
**Requirements**: RULE-03
**Success Criteria** (what must be TRUE):
  1. Override config supports multiple named profiles with strict schema validation.
  2. CLI can select profile explicitly and report active profile deterministically.
  3. Default, CI, and changed-files modes apply selected profile consistently.
**Plans**: 3 plans

Plans:
- [ ] 09-01: Extend override schema/parser for named profile collections.
- [ ] 09-02: Add CLI profile selector and runtime profile resolution integration.
- [ ] 09-03: Add cross-mode profile selection regression matrix.

### Phase 10: History and Autofix Suggestions
**Goal**: Maintainers can track quality trends and receive safe dry-run remediation suggestions.
**Depends on**: Phase 9
**Requirements**: HIST-01, FIX-01
**Success Criteria** (what must be TRUE):
  1. CLI can emit deterministic historical snapshot artifacts across runs.
  2. Maintainers can inspect trend summaries without breaking existing report contracts.
  3. Supported findings include dry-run autofix suggestions with explicit non-mutating output.
**Plans**: 3 plans

Plans:
- [ ] 10-01: Implement snapshot schema and deterministic persistence pipeline.
- [ ] 10-02: Add trend summary rendering and compatibility checks.
- [ ] 10-03: Implement dry-run autofix suggestion engine and safety-focused tests.

## Progress

**Execution Order:**
Phases execute in numeric order: 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Validator Foundation | v1.0 | 3/3 | Complete | 2026-02-25 |
| 2. Metadata Integrity Rules | v1.0 | 3/3 | Complete | 2026-02-25 |
| 3. Discovery and Reporting Outputs | v1.0 | 3/3 | Complete | 2026-02-25 |
| 4. CI Gate Hardening | v1.0 | 2/2 | Complete | 2026-02-25 |
| 5. Incremental Scan Performance | v1.1 | 3/3 | Complete | 2026-02-25 |
| 6. Override Policy Profiles | v1.1 | 3/3 | Complete | 2026-02-25 |
| 7. Override-Aware Reporting and CI | v1.1 | 2/2 | Complete | 2026-02-26 |
| 8. Persistent Cache Engine | v1.2 | 3/3 | Complete | 2026-02-26 |
| 9. Named Policy Profiles | v1.2 | 0/3 | Not started | - |
| 10. History and Autofix Suggestions | v1.2 | 0/3 | Not started | - |
