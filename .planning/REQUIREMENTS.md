# Requirements: Skills Catalog Quality Layer

**Defined:** 2026-02-25
**Core Value:** Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## v1.1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Incremental Performance

- [x] **PERF-01**: Maintainer can run validator in changed-files mode that scans only impacted skill directories.
- [x] **PERF-02**: Maintainer can select changed-file scope via explicit git compare range.
- [x] **PERF-03**: Incremental runs report exact scan scope and scanned-skill counts.

### Policy Overrides

- [ ] **RULE-01**: Maintainer can define repository override policy configuration without modifying validator source code.
- [ ] **RULE-02**: Validator validates override config schema and fails with actionable runtime/config errors when invalid.

### Reporting and CI Clarity

- [ ] **VIS-01**: Console/JSON/markdown outputs include effective policy profile and scope metadata.
- [ ] **CI-03**: CI gate semantics remain deterministic and evaluate threshold on active scope after policy overrides.

## v2 Requirements

Deferred to future releases; not in this milestone roadmap.

### Performance and Governance Expansion

- **PERF-04**: Support persistent scan cache for unchanged-skill metadata.
- **RULE-03**: Support multiple named override profiles with selection flags.

### Advanced Automation

- **HIST-01**: Produce historical trend snapshots for longitudinal quality tracking.
- **FIX-01**: Provide opt-in dry-run auto-fix suggestions for selected finding classes.

## Out of Scope

Explicit exclusions for v1.1.

| Feature | Reason |
|---------|--------|
| Automatic file mutation during validate/CI runs | v1.1 keeps read-only trust model intact |
| Hosted dashboard UI | CLI and generated artifacts remain sufficient |
| Historical quality dashboards | deferred until trend snapshot model exists |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERF-01 | Phase 5 | Complete |
| PERF-02 | Phase 5 | Complete |
| PERF-03 | Phase 5 | Complete |
| RULE-01 | Phase 6 | Pending |
| RULE-02 | Phase 6 | Pending |
| VIS-01 | Phase 7 | Pending |
| CI-03 | Phase 7 | Pending |

**Coverage:**
- v1.1 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 after Phase 5 completion*
