# Architecture Research

**Domain:** Incremental scan and override policy integration for `tools/skill_audit`
**Researched:** 2026-02-25
**Confidence:** HIGH

## Standard Architecture

### System Overview

- CLI orchestration (`cli.py`) remains single entrypoint.
- Scanner layer resolves candidate skill directories.
- Rule/policy layer evaluates findings with tier + override policy.
- Reporting layer emits console/json/markdown/ci outputs.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `scanner.py` | skill directory discovery and changed-set filtering | deterministic path collection + sort |
| `policy.py` / override helper | effective policy resolution | merge defaults with validated config |
| `cli.py` | argument routing + gate semantics | explicit mode branches (default vs ci vs incremental) |
| reporting/index modules | deterministic output serialization | canonical aggregate + renderer-specific formatting |

## Recommended Project Structure Changes

```
tools/skill_audit/
├── cli.py
├── scanner.py
├── policy.py
├── override_config.py      # new: parse/validate repo override config
├── tests/
│   ├── test_incremental_scan.py
│   ├── test_override_config.py
│   └── test_ci_gating.py
```

## Architectural Patterns

### Pattern 1: Explicit Effective-Config Resolution

Resolve runtime policy once from defaults + optional repo config and pass it through scan/evaluation paths.

### Pattern 2: Canonical Aggregation Then Filtering

Keep canonical finding schema; incremental mode filters input scope before output rendering, not by introducing alternate finding schema.

### Pattern 3: Deterministic Scope Metadata

All incremental and override outputs should echo scope/profile metadata to avoid ambiguity in CI logs.

## Data Flow

1. Parse args and optional override config.
2. Build effective scan scope (full or changed).
3. Run existing rules and tier policy translation.
4. Evaluate CI policy against in-scope findings.
5. Render outputs with explicit scope/profile summary.

## Integration Points

| Integration | Pattern | Notes |
|-------------|---------|-------|
| Git changed-files collection | shell/git helper wrapper | avoid fragile parsing and normalize paths |
| Override config file | YAML read + schema checks | invalid schema returns runtime/config error |
| Existing output modules | reuse aggregate/index model | preserve determinism guarantees |

## Anti-Patterns

- Embedding override parsing logic across multiple modules.
- Mixing incremental/full-scan semantics in report contracts without explicit markers.
- Allowing silent config fallback in CI mode.

## Sources

- Existing `tools/skill_audit` architecture and v1.0 phase summaries.

---
*Architecture research for: v1.1 performance + policy milestone*
*Researched: 2026-02-25*
