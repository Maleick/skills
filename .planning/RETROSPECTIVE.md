# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

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

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 41 passing | Contract-level CLI coverage for core flows | 4 modules (`scanner`, `policy`, `indexing`, `markdown_report`) |

### Top Lessons (Verified Across Milestones)

1. Deterministic ordering and explicit contracts are foundational for CI trust.
2. Phase summaries plus verification reports create high-fidelity milestone auditability.
