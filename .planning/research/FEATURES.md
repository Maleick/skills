# Feature Research

**Domain:** Repository quality and discovery tooling for Codex skill catalogs
**Researched:** 2026-02-25
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Full-catalog scan command | Maintainers need one entrypoint, not per-skill checks | LOW | Must include `.system`, `.curated`, `.experimental` traversal. |
| Contract presence checks (`SKILL.md`, expected dirs) | Structural drift is the primary pain point | LOW | Tier-aware rule exceptions needed for experiments. |
| Severity-based findings (`valid/warning/invalid`) | Users need triage, not raw lint noise | MEDIUM | Include clear reason + file path per finding. |
| Machine-readable output (`json`) | CI and automation require stable formats | MEDIUM | Must include summary counts and deterministic schema. |
| Human-readable summary (`markdown`/terminal) | Reviewers need quick scanable remediation notes | MEDIUM | Keep concise but with actionable fixes. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Incremental mode (`--changed-only`) | Faster feedback in large repos and PRs | MEDIUM | Integrates with `git diff` context. |
| Rule profiles by maturity tier | Reduces false positives for experimental folders | MEDIUM | Critical for trust and adoption. |
| Suggested auto-fix patches (dry-run) | Speeds remediation without hidden writes | HIGH | Prefer planned v2 scope. |
| Trend snapshots over time | Helps quantify quality improvement | HIGH | Requires historical storage model. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-rewrite all malformed files by default | Appears convenient | High risk of unintended repo churn | Default read-only mode with opt-in fix command. |
| Style-policing every markdown sentence | Feels like “complete quality” | Creates noisy, low-value failures | Restrict v1 to structural/contract checks. |
| Always-block CI on warnings | Signals strict quality | Encourages bypassing tool due false positives | Support fail-on-invalid and warn-on-warning modes. |

## Feature Dependencies

```
Full-catalog scan
    └──requires──> Rule engine
                       └──requires──> Severity model

Machine-readable output
    └──requires──> Stable schema definition

Human-readable report
    └──enhances──> Severity model

Auto-fix suggestions ──requires──> Rule engine + precise parsers
```

### Dependency Notes

- **Scan requires rule engine:** traversal alone does not provide actionable status.
- **JSON output requires schema:** CI contracts fail if format drifts.
- **Human summary enhances severity model:** without severity, reports are hard to prioritize.
- **Auto-fix depends on precise parsers:** unsafe without high-confidence rule mapping.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] One validator command scans all skill tiers and returns severity-classified findings.
- [ ] Contract checks detect missing/inconsistent skill metadata (`SKILL.md`, `agents/openai.yaml`, referenced assets/scripts).
- [ ] JSON and markdown outputs are generated from the same findings model.
- [ ] CI-friendly exit behavior supports strict and warning-tolerant modes.

### Add After Validation (v1.x)

- [ ] Incremental changed-files mode once baseline validator adoption is stable.
- [ ] Richer rule profile controls per skill tier and optional local overrides.

### Future Consideration (v2+)

- [ ] Opt-in auto-fix generator with dry-run preview.
- [ ] Historical trend dashboard/reporting snapshots.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Unified scan command | HIGH | LOW | P1 |
| Severity-classified findings | HIGH | MEDIUM | P1 |
| Metadata parity checks | HIGH | MEDIUM | P1 |
| JSON schema-backed output | HIGH | MEDIUM | P1 |
| Markdown summary output | MEDIUM | MEDIUM | P1 |
| Incremental mode | MEDIUM | MEDIUM | P2 |
| Tier-specific rule profiles | MEDIUM | MEDIUM | P2 |
| Auto-fix suggestions | MEDIUM | HIGH | P3 |
| Trend analytics | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Repo policy validation | Generic markdown linters | Generic schema tools | Combine skill-specific contracts with repo-aware outputs. |
| CI enforcement | Binary pass/fail only | Rich output but noisy | Severity model with configurable gate behavior. |
| Metadata consistency checks | Limited cross-file checks | Requires custom scripting | First-class cross-artifact parity checks for `SKILL.md` and `openai.yaml`. |

## Sources

- Local project signals: [idea.md](/opt/skills/idea.md) and existing script patterns under `skills/.system/*/scripts`.
- Existing skill contract examples in `skills/.curated/**/SKILL.md` and `skills/.curated/**/agents/openai.yaml`.
- GitHub Actions/CI conventions for JSON artifacts and exit-code gating.

---
*Feature research for: repository quality and discovery tooling for Codex skills*
*Researched: 2026-02-25*
