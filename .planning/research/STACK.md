# Stack Research

**Domain:** Skills repository audit, policy governance, and remediation automation CLI
**Researched:** 2026-02-26
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Core CLI/runtime | Already the project runtime; keeps v1.2 additive and low-risk. |
| pytest | 8.x | Contract/regression tests | Existing workflow already depends on deterministic subprocess tests. |
| PyYAML | 6.x | Policy/profile config parsing | Already used for override parsing and strict config validation. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 (stdlib) | bundled | Persistent cache + historical snapshots | Use for fast local metadata cache and trend indexing without extra infra. |
| hashlib/json/pathlib (stdlib) | bundled | Cache keys and deterministic serialization | Use for stable fingerprints and repeatable snapshot payloads. |
| difflib (stdlib) | bundled | Dry-run autofix suggestion rendering | Use for suggested patch previews without mutating files. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| py_compile | Syntax gate | Keep as pre-test check for changed modules. |
| pytest subprocess tests | CLI contract locks | Continue verifying exit codes and text output determinism. |

## Installation

```bash
# Existing dependencies (already in project)
pip install pyyaml pytest

# No additional external dependency required for v1.2 baseline
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| sqlite3 (stdlib) | DuckDB | If snapshot analytics/query volume grows significantly. |
| stdlib diffs | external patch engines | If future milestone adds auto-apply write mode with conflict resolution. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| In-memory-only cache | Lost between runs, no trend support | Persistent sqlite/json cache with deterministic keys |
| Non-deterministic timestamps in core output contracts | Breaks regression stability | Stable fields + optional timestamp isolation |

## Stack Patterns by Variant

**If running local dev scans repeatedly:**
- Use persistent cache with content hash invalidation.
- Keep report payload deterministic independent of cache hit path.

**If running CI strict mode:**
- Treat cache as optional optimization, never source-of-truth.
- Recompute when cache invalid/missing.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.11+ | pytest 8.x | Matches current suite usage and syntax. |
| PyYAML 6.x | existing override parser | No migration needed for v1.2 profile extension. |

## Sources

- Existing repository implementation (`tools/skill_audit/*`) and tests.
- Milestone v1.1 audit and verification artifacts.
- Existing CLI contract and deterministic-output test patterns.

---
*Stack research for: skills audit governance and automation*
*Researched: 2026-02-26*
