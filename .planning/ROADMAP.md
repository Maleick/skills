# Roadmap: Skills Catalog Quality Layer

## Milestones

- ✅ **v1.0 MVP** — shipped 2026-02-25 (Phases 1-4, 11 plans). Archive: `.planning/milestones/v1.0-ROADMAP.md`
- 🚧 **v1.1 Performance & Policy** — planned (Phases 5-7)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-02-25</summary>

- [x] **Phase 1: Validator Foundation** — 3/3 plans complete
- [x] **Phase 2: Metadata Integrity Rules** — 3/3 plans complete
- [x] **Phase 3: Discovery and Reporting Outputs** — 3/3 plans complete
- [x] **Phase 4: CI Gate Hardening** — 2/2 plans complete

</details>

### 🚧 v1.1 Performance & Policy (In Progress)

- [x] **Phase 5: Incremental Scan Performance** - Add changed-scope scan pathways and deterministic incremental outputs. (completed 2026-02-25)
- [x] **Phase 6: Override Policy Profiles** - Add repository-level override config parsing and policy resolution. (completed 2026-02-25)
- [x] **Phase 7: Override-Aware Reporting and CI** - Surface effective scope/profile in outputs and preserve deterministic CI gate behavior. (completed 2026-02-26)

## Phase Details

### Phase 5: Incremental Scan Performance
**Goal**: Maintainers can run fast changed-files validation without sacrificing deterministic output contracts.
**Depends on**: Phase 4
**Requirements**: PERF-01, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. Maintainer can run changed-files mode and scan only impacted skill directories.
  2. Maintainer can specify compare range for changed-file discovery.
  3. Incremental outputs explicitly report scope and scanned counts for operator clarity.
**Plans**: 3/3 plans complete

Plans:
- [x] 05-01: Implement changed-files scope collection and normalized impacted-skill filtering.
- [x] 05-02: Add compare-range CLI controls and deterministic incremental report metadata.
- [x] 05-03: Add regression tests for incremental determinism and scope correctness.

### Phase 6: Override Policy Profiles
**Goal**: Teams can customize validator policy behavior through repo configuration with strict validation and fail-fast safety.
**Depends on**: Phase 5
**Requirements**: RULE-01, RULE-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can define override policy in repository config with documented schema.
  2. Invalid or malformed override configuration fails with actionable runtime/config errors.
  3. Effective policy resolution is deterministic and test-covered across tiers/rules.
**Plans**: 3/3 plans complete

Plans:
- [x] 06-01: Implement override config schema and parser module.
- [x] 06-02: Integrate override policy resolution into scan/gate pipeline.
- [x] 06-03: Add validation and error-matrix tests for override config failure paths.

### Phase 7: Override-Aware Reporting and CI
**Goal**: Outputs and CI behavior remain explicit and trustworthy under incremental scope plus overrides.
**Depends on**: Phase 6
**Requirements**: VIS-01, CI-03
**Success Criteria** (what must be TRUE):
  1. Console/JSON/markdown output surfaces effective scope and policy profile metadata.
  2. CI gate evaluation remains deterministic and scoped to active findings after override translation.
  3. Existing non-incremental and non-override workflows remain backward compatible.
**Plans**: 2/2 plans complete

Plans:
- [x] 07-01: Add override/scope metadata surfacing across output renderers.
- [x] 07-02: Extend CI regression suite for override-aware threshold behavior and compatibility.

### Phase 1: Validator Foundation (Archived)
**Goal**: Establish baseline repository scan and finding model.
**Depends on**: None
**Requirements**: Archived in milestone v1.0 roadmap
**Plans**: 3/3 complete (see `.planning/milestones/v1.0-ROADMAP.md`)

### Phase 2: Metadata Integrity Rules (Archived)
**Goal**: Add tier-aware metadata parity and reference validation.
**Depends on**: Phase 1
**Requirements**: Archived in milestone v1.0 roadmap
**Plans**: 3/3 complete (see `.planning/milestones/v1.0-ROADMAP.md`)

### Phase 3: Discovery and Reporting Outputs (Archived)
**Goal**: Provide deterministic JSON and markdown reporting outputs.
**Depends on**: Phase 2
**Requirements**: Archived in milestone v1.0 roadmap
**Plans**: 3/3 complete (see `.planning/milestones/v1.0-ROADMAP.md`)

### Phase 4: CI Gate Hardening (Archived)
**Goal**: Add configurable CI threshold gate behavior.
**Depends on**: Phase 3
**Requirements**: Archived in milestone v1.0 roadmap
**Plans**: 2/2 complete (see `.planning/milestones/v1.0-ROADMAP.md`)

## Progress

**Execution Order:**
Phases execute in numeric order: 5 → 6 → 7

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 5. Incremental Scan Performance | v1.1 | 3/3 | Complete | 2026-02-25 |
| 6. Override Policy Profiles | v1.1 | 3/3 | Complete | 2026-02-25 |
| 7. Override-Aware Reporting and CI | v1.1 | 2/2 | Complete | 2026-02-26 |
