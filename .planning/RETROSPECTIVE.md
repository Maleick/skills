# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — Performance & Policy

**Shipped:** 2026-02-26
**Phases:** 3 | **Plans:** 8 | **Sessions:** 1

### What Was Built
- Incremental changed-files scanning with compare-range controls and deterministic scope metadata.
- Repository override policy configuration with strict validation and deterministic precedence.
- Override-aware JSON/console/markdown/CI output metadata and deterministic CI scoped gating behavior.

### What Worked
- Phase summaries and verification artifacts provided high-confidence requirement traceability.
- Regression-first CLI subprocess tests kept cross-mode contracts explicit and stable.

### What Was Inefficient
- `summary-extract` one-liner parsing returned null for milestone rollups, requiring manual accomplishment curation.
- `init milestone-op` defaulted to `v1.0`, so milestone scope had to be anchored manually to roadmap state.

### Patterns Established
- Keep policy/scope metadata as a first-class shared scan contract reused across all renderers and CI output.
- Treat deterministic output checks as non-negotiable for milestone closure.

### Key Lessons
1. Milestone tooling should infer current milestone from active roadmap heading when state pointers drift.
2. Summary parsers should support body one-liner fallback to avoid empty milestone accomplishment entries.

### Cost Observations
- Model mix: primarily sonnet orchestration and verification work.
- Sessions: 1 focused closeout session for Phase 7 completion through milestone archive.
- Notable: deterministic tests reduced audit and completion risk even with tooling metadata mismatches.

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-02-25
**Phases:** 4 | **Plans:** 11 | **Sessions:** 1

### What Was Built
- Repository-wide skill validator with deterministic scanning and structured findings.
- Metadata integrity rules (tier policy, parity checks, reference-path checks).
- Discovery/reporting outputs (JSON index + markdown remediation) with output controls.
- CI gate hardening with threshold/scope policy semantics and deterministic exit codes.

### What Worked
- Phase-based execution with summary and verification artifacts kept implementation auditable.
- Deterministic output/testing strategy reduced ambiguity and made regression checks reliable.

### What Was Inefficient
- Manual post-processing was needed to enrich milestone roll-up accomplishments and task counts.
- Workflow/tooling mismatch required extra normalization for state and milestone docs.

### Patterns Established
- Keep one canonical findings model and layer renderers/gates on top.
- Lock CLI behavior with subprocess tests for end-to-end policy contracts.

### Key Lessons
1. Milestone archival tooling should extract accomplishment one-liners from summary body as fallback when frontmatter omits them.
2. Milestone completion should preserve and update state in one schema to avoid manual cleanup.

### Cost Observations
- Model mix: dominated by sonnet workflow operations.
- Sessions: 1 focused execution session for completion/archival.
- Notable: deterministic docs + tests made milestone audit and closeout low-risk.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 4 | Established deterministic phase workflow with auditable verification artifacts |
| v1.1 | 1 | 3 | Added milestone-level 3-source requirement cross-check with override-aware CI determinism gating |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 41 passing | Contract-level CLI coverage for core flows | 4 modules (`scanner`, `policy`, `indexing`, `markdown_report`) |
| v1.1 | 71 passing | Incremental + override + CI deterministic contract coverage | additive metadata contract surfaces across CLI/reporting |

### Top Lessons (Verified Across Milestones)

1. Deterministic ordering and explicit contracts are foundational for CI trust.
2. Phase summaries plus verification reports create high-fidelity milestone auditability.
3. Milestone-closeout automation needs stronger state/version inference to avoid manual normalization.
