# Skills Catalog Quality Layer

## What This Is

A repository quality and discovery layer for `/opt/skills` that validates skill packaging contracts, reports metadata drift, and provides deterministic machine/human outputs for maintainers and CI.

## Core Value

Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## Current Milestone: v1.1 Performance & Policy

**Goal:** Make the validator faster on real repositories and safely configurable across teams without forking rule code.

**Target features:**
- Incremental changed-files scan mode for faster local and CI feedback loops.
- Repository override configuration for rule/profile customization.
- Clear CLI/reporting visibility into active override and policy behavior.

## Current State

- **Shipped milestone:** v1.0 MVP (2026-02-25)
- **Delivered scope:** validator foundation, metadata integrity rules, reporting/index outputs, CI gate hardening.
- **Runtime surface:** `python3 -m tools.skill_audit.cli` with scan, reporting, and CI gate modes.
- **Verification status:** all phase verifications passed; milestone audit passed.
- **Quality signal:** `41` passing tests in `tools/skill_audit/tests`.

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

### Active

- [ ] Deliver incremental changed-files scanning with deterministic behavior and stable output contracts.
- [ ] Add repository override profiles for rule policy customization without code edits.
- [ ] Keep CI and reporting surfaces explicit about active scope/profile decisions.

### Out of Scope

- Hosted dashboard UI (CLI and file artifacts are sufficient).
- Automatic file mutation in validate mode (read-only trust model retained).
- Style-only prose rewrites unrelated to packaging/contract integrity.

## Next Milestone Goals

1. Implement changed-files scan mode (`PERF-*`) and verify runtime reductions on typical workflows.
2. Implement repository override config (`RULE-*`) with strict validation and predictable fallback behavior.
3. Preserve compatibility across JSON/markdown outputs and CI gate semantics under override scenarios.

## Context

v1.0 established a stable validation platform with deterministic outputs and CI policy controls. v1.1 focuses on operational scalability (faster scans) and governance flexibility (repo-level policy overrides) while keeping deterministic, testable behavior intact.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize validator + index as v1 | Highest leverage against drift/discovery pain | ✓ Delivered in v1.0 |
| Keep v1 CLI/file-based | Fastest route to maintainable adoption | ✓ Delivered in v1.0 |
| Treat metadata contract checks as first-class | Metadata drift breaks downstream skill reliability | ✓ Delivered in v1.0 |
| Add dedicated CI mode with explicit policy controls | CI requires predictable pass/fail semantics | ✓ Delivered in v1.0 |
| Prioritize incremental scan + override config in v1.1 | Highest leverage for adoption in larger repos and varied team policies | — Pending |

---
*Last updated: 2026-02-25 after v1.1 milestone initialization*
