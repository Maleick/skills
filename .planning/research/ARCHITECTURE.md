# Architecture Research

**Domain:** Repository quality and discovery tooling for Codex skill catalogs
**Researched:** 2026-02-25
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Layer                          │
├─────────────────────────────────────────────────────────────┤
│  CLI args parser   Config loader   Mode selector (CI/local) │
└──────────────┬───────────────┬──────────────────────────────┘
               │               │
┌──────────────┴──────────────────────────────────────────────┐
│                    Analysis Layer                           │
├─────────────────────────────────────────────────────────────┤
│ Scanner → Rule Engine → Findings Aggregator → Severity Map │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────┴──────────────────────────────────────────────┐
│                     Output Layer                             │
├─────────────────────────────────────────────────────────────┤
│ JSON writer   Markdown summary   Exit-code policy evaluator │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Scanner | Enumerate candidate skill directories/files | Filesystem traversal with include/exclude filters. |
| Rule Engine | Evaluate structural and metadata contracts | Rule registry with pure validation functions. |
| Findings Aggregator | Normalize issues into one schema | Typed finding objects with severity + remediation. |
| Output Adapters | Emit machine and human formats | JSON serializer + markdown/template renderer. |
| Policy Evaluator | Determine process exit status | Configurable threshold mapping severity to exit code. |

## Recommended Project Structure

```
tools/skill-audit/
├── cli.py                  # Entry point and argument parsing
├── config.py               # Rule/profile configuration loading
├── scanner.py              # Repository traversal logic
├── rules/
│   ├── structural.py       # Required file/folder checks
│   ├── metadata.py         # SKILL/frontmatter/openai.yaml checks
│   └── references.py       # Path/reference validity checks
├── model/
│   ├── finding.py          # Findings schema
│   └── report.py           # Report aggregate schema
├── output/
│   ├── json_writer.py      # Machine output
│   └── markdown_writer.py  # Human output
└── tests/
    ├── fixtures/           # Sample skill directories
    └── test_*.py           # Rule + CLI tests
```

### Structure Rationale

- **`rules/` separation:** keeps rule ownership explicit and reduces coupling.
- **`model/` contracts:** stabilizes outputs for CI and downstream consumers.
- **`output/` adapters:** allows format expansion without changing rule logic.

## Architectural Patterns

### Pattern 1: Rule-Pipeline Validation

**What:** scanner emits artifacts, rule engine evaluates them, aggregator composes findings.
**When to use:** any multi-rule repository audit.
**Trade-offs:** easy extension, but requires disciplined finding schema.

**Example:**
```typescript
// pseudo-flow
scan() -> applyRules() -> normalizeFindings() -> writeReports()
```

### Pattern 2: Typed Finding Envelope

**What:** every rule returns the same shape (`id`, `severity`, `path`, `message`, `fix`).
**When to use:** whenever multiple outputs (JSON + markdown + exit code) depend on shared data.
**Trade-offs:** strong consistency, slightly higher upfront modeling cost.

**Example:**
```typescript
{ id: "META-001", severity: "warning", path: "skills/.experimental/auto-memory", message: "Missing SKILL.md" }
```

### Pattern 3: Policy-Driven Exit Behavior

**What:** map findings to exit codes via config profile.
**When to use:** CI integration where warnings may or may not be blocking.
**Trade-offs:** flexible, but requires clear default policy.

## Data Flow

### Request Flow

```
User/CI command
    ↓
CLI parser → config profile → scanner
    ↓
rule engine → finding aggregator
    ↓
JSON + Markdown reports
    ↓
exit-code policy
```

### State Management

```
In-memory report model
    ↓
Rendered outputs + optional artifacts on disk
```

### Key Data Flows

1. **Skill directory evaluation:** directory -> structural rules -> metadata rules -> findings.
2. **Report synthesis:** findings list -> grouped summary -> JSON/markdown outputs.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-200 skills | Single-process scan is sufficient. |
| 200-1k skills | Add file hash caching and changed-path mode. |
| 1k+ skills | Consider parallel scanning workers and batched IO. |

### Scaling Priorities

1. **First bottleneck:** repeated full scans in CI; solve with changed-path optimization.
2. **Second bottleneck:** report noise and triage fatigue; solve with rule profiles/severity tuning.

## Anti-Patterns

### Anti-Pattern 1: Monolithic Validator Script

**What people do:** place scan, rules, formatting, and CI logic in one file.
**Why it's wrong:** difficult to test and extend safely.
**Do this instead:** separate scanner/rules/model/output modules.

### Anti-Pattern 2: Unstructured String-Based Findings

**What people do:** emit ad-hoc text messages only.
**Why it's wrong:** impossible to consume reliably in CI and downstream tools.
**Do this instead:** enforce typed findings schema and render text from that schema.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Git (`git diff`) | Optional changed-files source | Enables incremental scans for PR workflows. |
| CI runners (GitHub Actions, etc.) | Command + artifact upload | JSON output should be deterministic and schema-validated. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| scanner ↔ rules | In-memory artifact descriptors | Keep descriptors minimal and immutable. |
| rules ↔ output | Findings model objects | No output formatting inside rule functions. |

## Sources

- Local repository structure and script conventions in `/opt/skills/skills/**`.
- [JSON Schema](https://json-schema.org/) patterns for report contracts.
- CLI design practices from Python argparse-based tooling.

---
*Architecture research for: repository quality and discovery tooling for Codex skills*
*Researched: 2026-02-25*
