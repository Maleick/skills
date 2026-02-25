# Stack Research

**Domain:** Repository quality and discovery tooling for Codex skill catalogs
**Researched:** 2026-02-25
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ (target 3.12) | Primary implementation language for validator/index CLI | Existing repository helper scripts already standardize on Python (`skills/**/scripts/*.py`) and this minimizes adoption friction. |
| JSON Schema | 2020-12 | Contract validation for generated index and finding payloads | Provides durable, machine-checkable structure for CI and downstream tooling. |
| YAML parsing (`PyYAML`) | 6.0+ | Parse `agents/openai.yaml` contracts safely | Already used in system skill tooling (`skills/.system/skill-creator/scripts/*.py`). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `jsonschema` | 4.x | Validate output index/findings shape | Required for CI-safe machine-readable guarantees. |
| `rich` | 13.x | Terminal tables and severity-colored output | Use for human summary mode; keep JSON mode plain. |
| `pathspec` | 0.12+ | Robust include/exclude pattern handling | Use when implementing tier-specific or pattern-based scanning rules. |
| `ruamel.yaml` (optional) | 0.18+ | Round-trip YAML checks without reformat drift | Use only if auto-fix mode is added in v2. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pytest` | Unit/integration test runner | Use fixture-driven repository samples and golden report outputs. |
| `ruff` | Lint + format | Fast, single-tool Python quality gate for CI. |
| `pre-commit` | Local pre-merge checks | Optional developer workflow acceleration; CI remains source of truth. |

## Installation

```bash
# Core
python3 -m pip install pyyaml jsonschema rich pathspec

# Dev dependencies
python3 -m pip install -U pytest ruff pre-commit
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Python CLI | Node.js CLI (`tsx`/TypeScript + zod) | Choose Node if the team already has strong TS-only enforcement and Python is undesired. |
| JSON output + markdown report | SQLite/stateful backend | Use a DB only if historical trend analytics are mandatory in v1 (not required now). |
| Local file traversal with `pathlib` | Shell-only pipelines (`find` + `grep`) | Shell-only is acceptable for one-off audits but is brittle for maintainable rule logic. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Regex-only frontmatter parsing | High false-positive risk with multiline YAML and edge formatting | YAML parser with explicit schema checks. |
| Implicit auto-fix by default | Surprising writes can reduce trust and cause noisy diffs | Read-only validate/report default; explicit `--fix` later. |
| Heavy service architecture for v1 | Adds operational overhead without user value | Single-process CLI with deterministic outputs. |

## Stack Patterns by Variant

**If running locally for maintainers:**
- Use fast scan + markdown summary + JSON artifact.
- Because maintainers need immediate actionable feedback.

**If running in CI gate:**
- Use JSON output + strict exit code mode.
- Because automation needs stable machine-consumable status.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.11+ | `pyyaml>=6`, `jsonschema>=4` | Covers modern typing and stable dependency support windows. |
| `rich` 13.x | Python 3.8+ | Safe with 3.11/3.12 target; keep output optional for JSON mode. |
| `ruff` latest stable | Python project roots | Use same version in CI and local dev for deterministic linting. |

## Sources

- Repository evidence: `skills/.system/skill-creator/scripts/generate_openai_yaml.py` and `skills/.system/skill-installer/scripts/list-skills.py` — confirms Python-first script ecosystem.
- [Python docs](https://docs.python.org/3/) — runtime and stdlib baseline.
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) — schema contract baseline.
- [PyYAML docs](https://pyyaml.org/wiki/PyYAMLDocumentation) — YAML parsing behavior.
- [pytest docs](https://docs.pytest.org/) and [Ruff docs](https://docs.astral.sh/ruff/) — test/lint quality workflow.

---
*Stack research for: repository quality and discovery tooling for Codex skills*
*Researched: 2026-02-25*
