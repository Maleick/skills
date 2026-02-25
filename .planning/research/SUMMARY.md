# Project Research Summary

**Project:** Skills Catalog Quality Layer
**Domain:** Repository quality and discovery tooling for Codex skills
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

The project should be built as a Python-first repository validator with a stable findings model and dual outputs (JSON + markdown). This matches current repository conventions, where Python scripts already power core skill utilities and maintainers need deterministic local and CI behavior.

Research indicates v1 should focus on structural and metadata integrity checks, not style policing or auto-rewrites. The fastest path to value is a read-only validator that classifies issues by severity and supports fail-threshold configuration for different skill tiers.

Primary risks are adoption failure from over-strict rules, output schema drift that breaks CI consumers, and false positives in experimental folders. These are mitigated with tier-aware policies, schema versioning, and profile-based exit behavior.

## Key Findings

### Recommended Stack

A Python 3.11+/3.12 CLI with `PyYAML` + `jsonschema` is the most compatible approach for this repository. It aligns with existing script ecosystems while allowing robust parsing and machine-verified output contracts.

**Core technologies:**
- Python: execution/runtime foundation — consistent with existing repository scripts.
- PyYAML: metadata parsing — required for `agents/openai.yaml` integrity checks.
- JSON Schema: output contract — ensures CI-safe stable report structures.

### Expected Features

**Must have (table stakes):**
- Single command scans all skill tiers and classifies findings.
- Structural and metadata contract checks with actionable remediation.
- JSON output for CI plus markdown/terminal summary for humans.

**Should have (competitive):**
- Tier-aware rule profiles.
- Optional incremental changed-files mode.

**Defer (v2+):**
- Auto-fix patch generation.
- Historical trend analytics.

### Architecture Approach

Use a layered CLI architecture: scanner -> rule engine -> findings aggregator -> output adapters -> policy evaluator. Keep rule logic pure and output rendering separate so both human and machine formats stay consistent and testable.

**Major components:**
1. Scanner and artifact model — discovers and normalizes skill folders/files.
2. Rule engine and findings schema — enforces contracts and emits typed issues.
3. Output/policy layer — renders reports and maps severities to exit codes.

### Critical Pitfalls

1. **Over-strict gating** — prevent with tier-aware defaults and warning-tolerant profiles.
2. **False positives on experimental skills** — prevent with explicit contract variants.
3. **Schema drift** — prevent with versioned JSON schema and contract tests.
4. **Hidden writes in validation mode** — prevent with read-only default and opt-in fix mode.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Validator Foundation
**Rationale:** Establishing scan + findings core is prerequisite for every downstream capability.
**Delivers:** CLI command, scanner, baseline structural checks, severity model.
**Addresses:** table-stake validation functionality.
**Avoids:** hidden-write and over-strict adoption pitfalls.

### Phase 2: Metadata Integrity Rules
**Rationale:** Cross-file consistency checks depend on stable foundational findings model.
**Delivers:** `SKILL.md` and `openai.yaml` parity checks plus reference path validation.
**Uses:** typed findings model and structural inventory from Phase 1.
**Implements:** high-value contract enforcement.

### Phase 3: Discovery Index and Reporting
**Rationale:** Once findings are reliable, reporting/index outputs create maintainability leverage.
**Delivers:** JSON index and markdown report from one canonical findings source.
**Uses:** schema-backed output contracts.
**Implements:** discovery and remediation visibility.

### Phase 4: CI Policy and Hardening
**Rationale:** Gate behavior should come after findings quality stabilizes.
**Delivers:** configurable fail thresholds, warning modes, and verification tests.
**Uses:** all prior components.
**Implements:** reliable pre-merge quality gate.

### Phase Ordering Rationale

- Rule and scanner foundation must exist before parity checks and reporting.
- Reporting should follow accurate findings to avoid cementing noisy output.
- CI hardening is last to avoid locking in unstable rules.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** precise parity rules for mixed-maturity skill tiers.
- **Phase 4:** CI policy defaults that balance strictness with adoption.

Phases with standard patterns (skip research-phase):
- **Phase 1:** established CLI/rule-engine patterns.
- **Phase 3:** established report and schema output patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strong alignment with existing repository tooling conventions. |
| Features | HIGH | Directly grounded in idea doc and observed maintenance pain points. |
| Architecture | HIGH | Standard policy-tool architecture with low uncertainty. |
| Pitfalls | HIGH | Common failure modes seen in repository quality tools and current repo signals. |

**Overall confidence:** HIGH

### Gaps to Address

- Define strictness profile for experimental skills with explicit documented exceptions.
- Decide whether incremental mode is v1.0 or v1.x based on early runtime measurements.

## Sources

### Primary (HIGH confidence)
- Local repository structure and scripts in `/opt/skills/skills/**`.
- [idea.md](/opt/skills/idea.md) project framing.

### Secondary (MEDIUM confidence)
- Python/JSON schema ecosystem best practices from official docs.

### Tertiary (LOW confidence)
- Competitor-style assumptions from generic lint/policy tooling patterns.

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
