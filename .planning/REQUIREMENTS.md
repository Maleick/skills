# Requirements: Skills Catalog Quality Layer

**Defined:** 2026-02-26
**Core Value:** Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## v1.2 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Performance and Caching

- [x] **PERF-04**: Maintainer can reuse unchanged-skill validation state via persistent cache without changing scan/report correctness.

### Policy Governance

- [ ] **RULE-03**: Maintainer can define and select named override policy profiles with explicit selector flags and deterministic precedence behavior.

### Historical Visibility

- [ ] **HIST-01**: Maintainer can generate deterministic historical quality snapshots for trend tracking across runs.

### Remediation Assistance

- [ ] **FIX-01**: Maintainer can generate dry-run autofix suggestions for supported finding classes with explicit non-mutating output.

## Future Requirements (Deferred)

Deferred until after v1.2 scope is validated.

- **HIST-02**: Compare two snapshots and emit normalized trend deltas as first-class artifact.
- **FIX-02**: Opt-in apply mode for autofix suggestions with rollback safeguards.
- **OPS-01**: Cache lifecycle management commands (inspect, prune, invalidate by scope/profile).

## Out of Scope

Explicit exclusions for v1.2.

| Feature | Reason |
|---------|--------|
| Automatic mutation of skill files during default validate/CI runs | v1.2 keeps read-only trust model by default |
| Hosted dashboard UI | CLI and generated artifacts remain sufficient for milestone scope |
| Cross-repo/federated history aggregation | postpone until single-repo trend model is stable |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERF-04 | Phase 8 | Complete |
| RULE-03 | Phase 9 | Pending |
| HIST-01 | Phase 10 | Pending |
| FIX-01 | Phase 10 | Pending |

**Coverage:**
- v1.2 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 phase 8 execution complete*
