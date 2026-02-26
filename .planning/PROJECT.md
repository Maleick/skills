# Skills Catalog Quality Layer

## What This Is

A repository quality and discovery layer for `/opt/skills` that validates skill packaging contracts, reports metadata drift, and provides deterministic machine/human outputs for maintainers and CI.

## Core Value

Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## Current Milestone Status

- **v1.0 MVP:** shipped 2026-02-25
- **v1.1 Performance & Policy:** shipped 2026-02-26
- **v1.2:** not yet defined

## Current State

- **Delivered scope:** validator foundation, metadata integrity rules, deterministic JSON/markdown reporting, CI gate hardening, incremental changed-files scanning, override policy profiles, and override-aware reporting/CI behavior.
- **Runtime surface:** `python3 -m tools.skill_audit.cli` with full, changed-files, compare-range, JSON/markdown output, and CI gate modes.
- **Verification status:** all Phase 5-7 verifications passed and milestone audit passed.
- **Quality signal:** `71` passing tests in `tools/skill_audit/tests`.

## Requirements

### Validated

- ✓ One-command scan across `.system`, `.curated`, `.experimental` (SCAN-01)
- ✓ Severity-classified findings with rule ID and path (SCAN-02)
- ✓ Tier-aware policy behavior for experimental handling (SCAN-03)
- ✓ `SKILL.md` presence/frontmatter contract validation (META-01)
- ✓ `SKILL.md` ↔ `agents/openai.yaml` parity checks (META-02)
- ✓ Broken local reference detection for skill metadata/docs (META-03)
- ✓ JSON skill index generation with status and metadata fields (INDEX-01)
- ✓ Per-tier and per-severity summary totals in JSON output (INDEX-02)
- ✓ Markdown remediation report grouped by severity and skill (REPT-01)
- ✓ Actionable remediation guidance for each reported issue (REPT-02)
- ✓ Configurable CI threshold gating semantics (CI-01)
- ✓ Tier-scoped warning-tolerant CI mode (CI-02)
- ✓ Incremental changed-files scan mode and compare-range scope controls (PERF-01, PERF-02)
- ✓ Deterministic incremental scope/count reporting across output surfaces (PERF-03)
- ✓ Repository override policy config with strict schema validation (RULE-01, RULE-02)
- ✓ Override-aware output visibility and CI deterministic scope/threshold evaluation (VIS-01, CI-03)

### Active

- [ ] Define v1.2 milestone scope and requirements.
- [ ] Decide whether to prioritize cache/performance expansion (`PERF-04`) or policy profile expansion (`RULE-03`) first.

### Out of Scope

- Hosted dashboard UI (CLI and file artifacts remain sufficient).
- Automatic file mutation in validate mode (read-only trust model retained).
- Style-only prose rewrites unrelated to packaging/contract integrity.

## Next Milestone Goals

1. Define v1.2 requirements and roadmap via `$gsd-new-milestone --auto`.
2. Prioritize one major axis for v1.2: performance cache/governance (`PERF-04`, `RULE-03`) or historical/autofix automation (`HIST-01`, `FIX-01`).
3. Preserve deterministic contracts across JSON, markdown, and CI outputs while extending capabilities.

## Context

v1.1 completed performance and policy objectives: incremental scan performance, strict override policy configuration, and explicit override-aware reporting/CI semantics. The next milestone should focus on the next highest-leverage capability while keeping deterministic behavior and testability intact.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize validator + index as v1 | Highest leverage against drift/discovery pain | ✓ Delivered in v1.0 |
| Keep v1 CLI/file-based | Fastest route to maintainable adoption | ✓ Delivered in v1.0 |
| Treat metadata contract checks as first-class | Metadata drift breaks downstream skill reliability | ✓ Delivered in v1.0 |
| Add dedicated CI mode with explicit policy controls | CI requires predictable pass/fail semantics | ✓ Delivered in v1.0 |
| Prioritize incremental scan + override config in v1.1 | Highest leverage for larger repos and varied team policies | ✓ Delivered in v1.1 |
| Preserve deterministic outputs under override translation | CI trust requires stable, auditable gate behavior | ✓ Delivered in v1.1 |

---
*Last updated: 2026-02-26 after v1.1 milestone completion*
