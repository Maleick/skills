# Skills Catalog Quality Layer

## What This Is

A repository quality and discovery layer for `/opt/skills` that validates skill packaging contracts, reports metadata drift, and provides deterministic machine/human outputs for maintainers and CI.

## Core Value

Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## Current Milestone: v1.2 Governance & Automation

**Goal:** Expand governance controls and operator productivity without sacrificing deterministic scan/report/gate behavior.

**Target features:**
- Persistent incremental scan cache for unchanged skills (`PERF-04`).
- Multiple named override profiles with explicit selector flags (`RULE-03`).
- Historical quality snapshot generation for trend tracking (`HIST-01`).
- Opt-in dry-run autofix suggestions for selected finding classes (`FIX-01`).

## Current State

- **Shipped milestones:** v1.0 MVP and v1.1 Performance & Policy.
- **Delivered runtime surface:** `python3 -m tools.skill_audit.cli` with full/changed-files scan modes, CI gating, deterministic JSON/markdown outputs, and override-aware policy reporting.
- **Verification status:** all phase verifications passed through Phase 7; v1.1 milestone audit passed.
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

- [ ] Implement persistent scan cache for unchanged skills (`PERF-04`).
- [ ] Implement named override profile selection model (`RULE-03`).
- [ ] Add historical quality snapshot artifact generation (`HIST-01`).
- [ ] Add dry-run autofix suggestion workflows (`FIX-01`).

### Out of Scope

- Hosted dashboard UI (CLI and file artifacts remain sufficient).
- Automatic file mutation in validate mode by default (read-only trust model retained).
- Non-deterministic or timestamp-noisy reporting contracts.

## Next Milestone Goals

1. Cut scan latency for unchanged repositories via deterministic caching.
2. Add explicit profile-based policy governance for different team/risk contexts.
3. Introduce longitudinal and remediation-assist artifacts while preserving CI trust.

## Context

v1.2 builds on the stable v1.1 baseline: fast incremental scans, strict overrides, and explicit policy visibility. The milestone focus is to improve scale/governance and operator workflows while keeping outputs deterministic and auditable.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize validator + index as v1 | Highest leverage against drift/discovery pain | ✓ Delivered in v1.0 |
| Keep v1 CLI/file-based | Fastest route to maintainable adoption | ✓ Delivered in v1.0 |
| Treat metadata contract checks as first-class | Metadata drift breaks downstream skill reliability | ✓ Delivered in v1.0 |
| Add dedicated CI mode with explicit policy controls | CI requires predictable pass/fail semantics | ✓ Delivered in v1.0 |
| Prioritize incremental scan + override config in v1.1 | Highest leverage for larger repos and varied team policies | ✓ Delivered in v1.1 |
| Preserve deterministic outputs under override translation | CI trust requires stable, auditable gate behavior | ✓ Delivered in v1.1 |
| Prioritize cache/profile/history/autofix for v1.2 | Next highest impact on scale, governance, and maintainer efficiency | — Active |

---
*Last updated: 2026-02-26 after v1.2 milestone initialization*
