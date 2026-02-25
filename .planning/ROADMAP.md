# Roadmap: Skills Catalog Quality Layer

## Overview

This roadmap delivers a practical quality and discovery system for the skills repository: first establish reliable scan and findings foundations, then enforce metadata integrity, then ship machine/human reporting, and finally harden CI gating behavior for safe adoption.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Validator Foundation** - Build full-catalog scan and baseline finding model.
- [ ] **Phase 2: Metadata Integrity Rules** - Add tier-aware policy and cross-file parity checks.
- [ ] **Phase 3: Discovery and Reporting Outputs** - Generate JSON index and markdown remediation summary.
- [ ] **Phase 4: CI Gate Hardening** - Add policy thresholds and operational reliability checks.

## Phase Details

### Phase 1: Validator Foundation
**Goal**: Maintainers can run one baseline validator command across all skill tiers and receive structured severity findings.
**Depends on**: Nothing (first phase)
**Requirements**: SCAN-01, SCAN-02, META-01
**Success Criteria** (what must be TRUE):
  1. Maintainer can run a single command that scans `.system`, `.curated`, and `.experimental` tiers.
  2. Findings include severity, rule ID, and path for every issue.
  3. Missing or malformed `SKILL.md` frontmatter is detected and reported.
**Plans**: 3 plans

Plans:
- [ ] 01-01: Implement repository scanner and normalized artifact inventory.
- [ ] 01-02: Implement findings schema, severity model, and base rule engine.
- [ ] 01-03: Add `SKILL.md` frontmatter validation and CLI wiring.

### Phase 2: Metadata Integrity Rules
**Goal**: Metadata contracts are checked consistently with tier-aware policies and cross-file validation.
**Depends on**: Phase 1
**Requirements**: SCAN-03, META-02, META-03
**Success Criteria** (what must be TRUE):
  1. Experimental tier issues can be reported with warning-biased policy without masking true invalid states.
  2. `SKILL.md` and `agents/openai.yaml` mismatches are detected with actionable remediation.
  3. Broken local references to scripts/references/assets are detected and localized.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Implement tier policy profile resolution and severity override behavior.
- [ ] 02-02: Implement `SKILL.md` ↔ `openai.yaml` parity checks.
- [ ] 02-03: Implement local reference-path validation rules and tests.

### Phase 3: Discovery and Reporting Outputs
**Goal**: Maintainers and CI systems receive stable machine and human outputs from one canonical findings model.
**Depends on**: Phase 2
**Requirements**: INDEX-01, INDEX-02, REPT-01, REPT-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can generate a JSON skill index that includes tier and validation status for each skill.
  2. Output contains reliable per-tier and per-severity counts for automation.
  3. Maintainer can generate a markdown summary grouped by severity and skill with remediation guidance.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Implement JSON index/report models and schema validation checks.
- [ ] 03-02: Implement markdown report renderer with grouping and fix guidance.
- [ ] 03-03: Add regression tests for output stability and deterministic ordering.

### Phase 4: CI Gate Hardening
**Goal**: Quality checks integrate safely into CI with configurable blocking thresholds and predictable exit behavior.
**Depends on**: Phase 3
**Requirements**: CI-01, CI-02
**Success Criteria** (what must be TRUE):
  1. CI mode fails on invalid findings by default using stable exit behavior.
  2. Maintainers can run warning-tolerant mode for selected contexts (for example experimental-focused checks).
  3. Gate behavior is documented and validated with command-level tests.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Implement threshold-based exit policy and CI-focused flags.
- [ ] 04-02: Add CI usage examples and policy-mode verification tests.

## Progress

**Execution Order:**
Phases execute in numeric order: 2 → 2.1 → 2.2 → 3 → 3.1 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Validator Foundation | 0/3 | Not started | - |
| 2. Metadata Integrity Rules | 0/3 | Not started | - |
| 3. Discovery and Reporting Outputs | 0/3 | Not started | - |
| 4. CI Gate Hardening | 0/2 | Not started | - |
