# Requirements: Skills Catalog Quality Layer

**Defined:** 2026-02-25
**Core Value:** Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Scanning

- [ ] **SCAN-01**: Maintainer can run one command to scan `skills/.system`, `skills/.curated`, and `skills/.experimental` in a single pass.
- [ ] **SCAN-02**: Scan output classifies each finding as `valid`, `warning`, or `invalid` with file path and rule ID.
- [ ] **SCAN-03**: Validator applies tier-aware rule behavior so experimental folders can use warning-biased handling.

### Metadata Integrity

- [ ] **META-01**: Validator detects missing or malformed `SKILL.md` frontmatter in skill directories.
- [ ] **META-02**: Validator checks `agents/openai.yaml` metadata consistency with `SKILL.md` metadata where both exist.
- [ ] **META-03**: Validator flags broken local references (scripts/references/assets paths) declared by skill docs/metadata.

### Discovery Index

- [ ] **INDEX-01**: Maintainer can generate a machine-readable JSON skill index including name, tier, and validation status.
- [ ] **INDEX-02**: JSON index includes per-tier and per-severity summary counts for automation consumption.

### Reporting

- [ ] **REPT-01**: Maintainer can generate a markdown summary grouped by severity and skill directory.
- [ ] **REPT-02**: Each reported issue includes actionable remediation guidance.

### CI Gating

- [ ] **CI-01**: Validator supports configurable exit thresholds (default: fail on invalid findings).
- [ ] **CI-02**: CI mode supports warning-tolerant operation for selected contexts (for example experimental-only checks).

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Performance and Extensibility

- **PERF-01**: Support changed-files-only scan mode for faster incremental checks.
- **RULE-01**: Support repository override config for custom rule profiles.

### Advanced Automation

- **FIX-01**: Provide opt-in dry-run auto-fix suggestions for selected findings.
- **HIST-01**: Produce historical trend snapshots to track quality over time.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Rewriting skill prose/style | Not required to achieve structural quality goals |
| Hosted dashboard UI | CLI + file artifacts are sufficient for v1 |
| Automatic file mutation during validate mode | Risks trust and introduces noisy diffs |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAN-01 | Phase 1 | Pending |
| SCAN-02 | Phase 1 | Pending |
| META-01 | Phase 1 | Pending |
| SCAN-03 | Phase 2 | Pending |
| META-02 | Phase 2 | Pending |
| META-03 | Phase 2 | Pending |
| INDEX-01 | Phase 3 | Pending |
| INDEX-02 | Phase 3 | Pending |
| REPT-01 | Phase 3 | Pending |
| REPT-02 | Phase 3 | Pending |
| CI-01 | Phase 4 | Pending |
| CI-02 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 after roadmap creation*
