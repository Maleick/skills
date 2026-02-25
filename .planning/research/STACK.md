# Stack Research

**Domain:** Skill catalog validator performance and policy extensibility
**Researched:** 2026-02-25
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | CLI/runtime foundation | Existing validator is Python-first and already tested. |
| argparse + pathlib | stdlib | CLI interface and filesystem traversal | Zero-dependency fit with current architecture. |
| pytest | current repo baseline | Regression verification | Existing suite already provides subprocess-level safety. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathspec | 0.12+ | Gitignore-aware path filtering | Useful for changed-file filtering with explicit include/exclude behavior. |
| pyyaml | existing | Config parsing | Keep for repo override profile file support. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| git CLI | changed-file inputs | Use for `--changed` and compare-range semantics. |
| py_compile | syntax validation | Fast pre-test gate for touched modules. |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| explicit override config file | env-var-only policy overrides | Only for ad-hoc local debugging, not team-shared policy. |
| deterministic filesystem scan + filter | direct shell pipeline filtering | Avoid when deterministic ordering and cross-platform behavior matter. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| implicit mutable global policy state | hard to reason/test in CI | explicit policy resolution per invocation |
| non-deterministic traversal/filtering | noisy diffs and flaky tests | stable sorted path resolution |

## Sources

- Existing repository implementation in `tools/skill_audit/`.
- Existing v1.0 tests and milestone verification artifacts.

---
*Stack research for: v1.1 performance + policy milestone*
*Researched: 2026-02-25*
