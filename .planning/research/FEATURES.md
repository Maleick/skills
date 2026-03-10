# Feature Research

**Domain:** Repository quality governance and operator automation
**Researched:** 2026-02-26
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Persistent cache for unchanged scans | Large repos need repeated fast runs | MEDIUM | Must preserve deterministic outputs across cache hit/miss paths. |
| Profile-based policy selection | Teams need different policy strictness contexts | MEDIUM | Extends current single-profile override model. |
| Historical run snapshots | Maintainers need trend visibility over time | MEDIUM | Can start as file/sqlite snapshots; UI not required. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dry-run autofix suggestions | Helps teams remediate quickly without unsafe writes | MEDIUM-HIGH | Keep read-only by default, suggest-only in v1.2. |
| Deterministic trend + profile-aware reports | Builds trust for CI and audit workflows | MEDIUM | Reuse existing deterministic ordering rules. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automatic file mutation by default | “Fix everything in one command” | Risky and hard to trust in CI; large blast radius | Dry-run suggestions first; opt-in apply later |
| Highly dynamic per-run random metadata | “More context in reports” | Breaks regression stability and contract tests | Stable summaries + optional explicit debug payload |

## Feature Dependencies

```
[Persistent cache]
    └──enables──> [faster incremental/trend pipelines]

[Named policy profiles]
    └──feeds──> [profile-aware snapshots and reporting]

[Historical snapshots]
    └──informs──> [autofix prioritization suggestions]
```

### Dependency Notes

- **Historical snapshots depend on stable identity keys:** without deterministic skill/rule identifiers, trends are noisy.
- **Autofix suggestions depend on clear finding taxonomy:** rule metadata and suggested fixes must remain structured.

## MVP Definition

### Launch With (v1.2)

- [ ] `PERF-04` persistent cache for unchanged-skill metadata.
- [ ] `RULE-03` named override profiles with explicit selector.
- [ ] `HIST-01` historical trend snapshot artifact generation.
- [ ] `FIX-01` dry-run autofix suggestion output (no write mutation).

### Add After Validation (v1.3)

- [ ] Optional autofix apply mode with explicit confirmation and backup paths.
- [ ] Snapshot diff/compare UX improvements.

### Future Consideration (v2+)

- [ ] Hosted dashboard and interactive visualization.
- [ ] Multi-repo federated trends.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| PERF-04 cache | HIGH | MEDIUM | P1 |
| RULE-03 profiles | HIGH | MEDIUM | P1 |
| HIST-01 snapshots | MEDIUM-HIGH | MEDIUM | P1 |
| FIX-01 dry-run suggestions | MEDIUM-HIGH | MEDIUM-HIGH | P1 |

## Sources

- v1.1 deferred requirements and milestone audit outcomes.
- Existing CLI/operator workflow constraints in project docs.
- Current regression suite and deterministic contract requirements.

---
*Feature research for: governance and automation expansion*
*Researched: 2026-02-26*
