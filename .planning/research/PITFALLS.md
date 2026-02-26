# Pitfalls Research

**Domain:** Skills audit performance/governance automation expansion
**Researched:** 2026-02-26
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Cache Correctness Drift

**What goes wrong:**
Cached results diverge from real file state, hiding new issues.

**Why it happens:**
Weak invalidation keys or not hashing all relevant inputs.

**How to avoid:**
Use deterministic fingerprints that include file content + selected profile context + rule schema version.

**Warning signs:**
Identical files produce different results between cached and uncached runs, or stale findings persist after edits.

**Phase to address:**
Phase 8 (cache foundation + invalidation tests).

---

### Pitfall 2: Profile Selection Ambiguity

**What goes wrong:**
Different modes (default/CI/changed-files) resolve different policy profiles unintentionally.

**Why it happens:**
Profile selection logic duplicated in multiple code paths.

**How to avoid:**
One canonical profile resolver in CLI pipeline used by all modes.

**Warning signs:**
Same invocation scope yields different severities between modes.

**Phase to address:**
Phase 9 (named profile model + selector contract).

---

### Pitfall 3: Snapshot Noise and Non-Determinism

**What goes wrong:**
Historical outputs become noisy and not comparable due to unstable fields.

**Why it happens:**
Unbounded metadata/timestamps included in core comparison payloads.

**How to avoid:**
Separate stable snapshot core from optional runtime metadata.

**Warning signs:**
Trend diffs report high churn without real repository changes.

**Phase to address:**
Phase 10 (history schema and deterministic serialization tests).

---

### Pitfall 4: Unsafe Autofix Expectations

**What goes wrong:**
Users assume suggested fixes are always safe to apply blindly.

**Why it happens:**
Suggestion output appears authoritative without confidence/scope context.

**How to avoid:**
Keep v1.2 strictly dry-run, include rule-level caveats and confidence labels.

**Warning signs:**
Suggestions conflict with project conventions or reference missing context.

**Phase to address:**
Phase 10 (dry-run suggestion engine + safety wording tests).

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Cache without schema versioning | Quick implementation | Hard invalidation bugs after rule changes | Never |
| Implicit default profile switching | Fewer flags | Debugging ambiguity in CI | Never |
| Autofix suggestions without rule-level constraints | Faster rollout | Unsafe recommendations | Never |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Overly granular cache writes | IO-heavy runs | Batch writes and bounded indexes | medium-large repos |
| Snapshot payload bloat | Slow trend queries | Store compact summaries + optional detail files | repeated CI/history usage |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing sensitive path contents in snapshots | Information disclosure | Store relative paths and normalized metadata only |
| Accepting arbitrary profile names without validation | Policy bypass/confusion | Strict selector validation and clear errors |

## "Looks Done But Isn't" Checklist

- [ ] Cache validates schema/version drift, not just file mtime.
- [ ] Profile selection is identical across default, CI, and changed-files modes.
- [ ] Snapshot output remains deterministic under repeated identical inputs.
- [ ] Autofix suggestions are dry-run only and clearly non-mutating.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cache correctness drift | Phase 8 | cache hit/miss parity tests |
| Profile selection ambiguity | Phase 9 | cross-mode profile resolution tests |
| Snapshot non-determinism | Phase 10 | repeated-run snapshot stability tests |
| Unsafe autofix expectations | Phase 10 | suggestion safety/wording contract tests |

## Sources

- Existing v1.1 verification and milestone audit findings.
- Current CI determinism and reporting contract tests.
- Existing deferred requirement set for v2 capabilities.

---
*Pitfalls research for: v1.2 governance and automation*
*Researched: 2026-02-26*
