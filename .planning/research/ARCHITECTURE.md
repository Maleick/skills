# Architecture Research

**Domain:** CLI-based skill audit governance and automation extensions
**Researched:** 2026-02-26
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ CLI Layer (`tools/skill_audit/cli.py`)                      │
├─────────────────────────────────────────────────────────────┤
│  Scan Scope  │ Policy Resolution │ Reporting │ CI Gate      │
├─────────────────────────────────────────────────────────────┤
│ Core Engine (`scanner`, `rules`, `policy`, `indexing`)      │
├─────────────────────────────────────────────────────────────┤
│ Data Layer (cache + snapshots + deterministic artifacts)     │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Cache subsystem | Persist unchanged-skill metadata and fingerprints | New module using sqlite/json + content hash keys |
| Profile selector | Resolve named override profile for current invocation | Extend override config loader + CLI flags |
| Snapshot writer | Emit run summaries for trend analysis | Deterministic JSON records in dedicated history location |
| Autofix suggester | Produce safe dry-run patch suggestions | Rule-linked suggestion registry and diff formatter |

## Recommended Project Structure

```
tools/skill_audit/
├── cli.py                    # command entrypoint + orchestration
├── scanner.py                # changed-file and skill discovery
├── policy.py                 # severity translation + profile behavior
├── override_config.py        # override schema/profile parsing
├── cache.py                  # new: cache keying/read/write/invalidation
├── history.py                # new: snapshot persistence and trend summaries
├── autofix.py                # new: dry-run suggestion generation
└── tests/
```

## Architectural Patterns

### Pattern 1: Deterministic Contract Boundary

**What:** Keep cache/history/autofix internals behind stable scan/report outputs.
**When to use:** Any time performance or helper features are added.
**Trade-offs:** Slightly more adapter code; much safer compatibility.

### Pattern 2: Read-Only Default with Explicit Opt-In Modes

**What:** New automation features suggest and report by default, no mutation.
**When to use:** Autofix capabilities and policy profile selection UX.
**Trade-offs:** Less immediate automation, far lower safety risk.

### Pattern 3: Layered Fallbacks

**What:** Cache/profile/history features fail gracefully to existing baseline behavior.
**When to use:** CI and local runs where optional data may be missing.
**Trade-offs:** More branches to test; improved operational robustness.

## Data Flow

### Request Flow

```
CLI args
  -> scope discovery
  -> profile resolution
  -> cache lookup / recompute
  -> findings translation
  -> index/report generation
  -> optional snapshot + autofix suggestion output
```

### Key Data Flows

1. **Cache flow:** skill fingerprint -> cached metadata -> validation short-circuit when safe.
2. **Profile flow:** selected profile -> override policy translation -> CI/report outputs.
3. **History/autofix flow:** findings summary -> trend artifact -> dry-run suggestions.

## Integration Points

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `cli.py` ↔ `override_config.py` | function API + typed profile metadata | Extend from single active profile to named profile selection. |
| `cli.py` ↔ `cache.py` | function API + deterministic key contract | Cache is optional optimization; never authoritative over invalidation. |
| `indexing/reporting` ↔ `history.py` | structured payload handoff | Snapshot schema should reuse index summary shape when possible. |
| `rules` ↔ `autofix.py` | rule ID to suggestion mapping | Suggestions stay explicit and auditable. |

## Anti-Patterns

- Coupling cache hits directly to user-visible ordering or counts.
- Embedding profile-selection logic separately in CI and non-CI paths.
- Emitting snapshot fields that change nondeterministically run-to-run.

## Sources

- Existing skill_audit architecture and verification artifacts.
- v1.1 milestone audit integration findings.
- Current deterministic output and CI contract assumptions.

---
*Architecture research for: v1.2 governance and automation*
*Researched: 2026-02-26*
