# Pitfalls Research

**Domain:** Repository quality and discovery tooling for Codex skill catalogs
**Researched:** 2026-02-25
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Over-Strict Rules That Block Adoption

**What goes wrong:**
Validator flags too many warnings/errors, causing maintainers to bypass or disable it.

**Why it happens:**
Rule sets are designed for ideal states without considering experimental directories or legacy patterns.

**How to avoid:**
Start with tier-aware severity defaults (`.curated` stricter, `.experimental` warning-biased), and ship with transparent policy config.

**Warning signs:**
High warning count on first run, repeated `--no-verify` usage, or frequent CI bypass conversations.

**Phase to address:**
Phase 1 and Phase 4.

---

### Pitfall 2: False Positives from Cross-File Drift Assumptions

**What goes wrong:**
Tool reports metadata mismatches that are valid exceptions, reducing trust.

**Why it happens:**
Rules assume every folder follows complete curated-skill contracts.

**How to avoid:**
Explicitly encode per-tier contracts and allow documented exceptions.

**Warning signs:**
Findings that maintainers repeatedly mark as "expected" with no remediation.

**Phase to address:**
Phase 2.

---

### Pitfall 3: Unstable Output Schema

**What goes wrong:**
CI consumers break when JSON structure changes across tool updates.

**Why it happens:**
No versioned report schema and no contract tests for output format.

**How to avoid:**
Version the output schema and validate report payloads before release.

**Warning signs:**
Downstream automation failures after minor changes.

**Phase to address:**
Phase 3 and Phase 4.

---

### Pitfall 4: Hidden Writes by Default

**What goes wrong:**
Validation unexpectedly edits files, creating noisy diffs and distrust.

**Why it happens:**
Auto-fix and validation logic are coupled.

**How to avoid:**
Make read-only validation default; require explicit `--fix` for writes.

**Warning signs:**
Unexpected modified files after "check only" execution.

**Phase to address:**
Phase 1.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hard-coded path assumptions | Fast initial implementation | Breaks as repo structure evolves | Only in prototype branches |
| One giant rule function | Fewer files now | Hard debugging and fragile changes | Never in v1 release |
| Non-versioned JSON output | Faster shipping | CI integration breaks on refactors | Never once CI depends on output |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Git diff integration | Assuming clean working tree only | Support staged/unstaged diff modes explicitly. |
| CI gate | Treating warnings as hard failures always | Provide configurable threshold for fail-on-invalid only. |
| Markdown reporting | Embedding terminal colors in files | Keep file outputs plain markdown; colorize terminal only. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full deep scan every run | Slow feedback in PRs | Add changed-files mode and cache fingerprints | Frequent CI runs on medium+ repos |
| Duplicate parsing per rule | CPU-heavy scans | Parse once, share normalized artifact model | 500+ skill files |
| Re-rendering report formats from scratch per rule | High overhead and inconsistency | Aggregate findings once, render after all rules | Mid-size repos with many rules |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging environment variable values in findings | Secret leakage in CI logs | Log variable names only, never values. |
| Treating external reference URLs as trusted content | Supply-chain and trust issues | Validate syntax only; do not execute remote content. |
| Auto-fixing YAML without parser guarantees | Corrupted metadata files | Use safe parser and dry-run diffs before write mode. |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Vague finding messages | Slow remediation | Include path, rule ID, why it matters, and suggested fix. |
| Massive ungrouped output | Triage fatigue | Group by severity and skill folder. |
| No summary counts | Hard to assess progress | Always show valid/warning/invalid totals. |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Validation command:** Often missing tier-aware exceptions — verify `.experimental` policy handling.
- [ ] **JSON report:** Often missing schema version — verify `schema_version` field exists.
- [ ] **Metadata parity checks:** Often missing cross-file link validation — verify `SKILL.md` ↔ `openai.yaml` checks.
- [ ] **CI integration:** Often missing fail-threshold configurability — verify warning-only mode exists.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Over-strict rules | MEDIUM | Reclassify severities by tier, add profile tests, release policy update. |
| Output schema drift | HIGH | Introduce schema versioning, ship compatibility shim, update CI consumers. |
| Hidden writes | MEDIUM | Split validate/fix commands, add dry-run and explicit opt-in flags. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Over-strict rules | Phase 1 and 4 | Baseline run shows manageable findings and clear thresholds. |
| Cross-file false positives | Phase 2 | Known exception cases pass with expected severity. |
| Output schema instability | Phase 3 and 4 | JSON schema tests pass and CI parsers remain compatible. |

## Sources

- Existing repo structure and observed gaps in `/opt/skills/skills/.experimental/*`.
- Existing helper script practices in `/opt/skills/skills/.system/*/scripts`.
- Operational patterns from CLI-based repository policy tools.

---
*Pitfalls research for: repository quality and discovery tooling for Codex skills*
*Researched: 2026-02-25*
