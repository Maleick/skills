# Coding Conventions

**Analysis Date:** 2026-02-25

## Naming Patterns

**Files:**
- Skill definitions are consistently named `SKILL.md` at the skill root (for example `skills/.curated/openai-docs/SKILL.md`).
- Skill directories are kebab-case (`skills/.curated/security-threat-model/`, `skills/.system/skill-installer/`).
- Python helper scripts use snake_case (for example `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).

**Functions:**
- Python functions predominantly use snake_case (`run_gh_command`, `resolve_pr`, `fetch_checks` in `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).
- Shell helper functions use lowercase snake/camel-like names (`screen_capture_status` in `skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`).

**Variables:**
- Constants are upper snake case (`DEFAULT_MAX_LINES`, `FAILURE_MARKERS` in `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).
- Local variables are snake_case in Python and uppercase for shell env/config constants (`DEPLOY_ENDPOINT` in `skills/.curated/vercel-deploy/scripts/deploy.sh`).

**Types:**
- Type hints are used in many Python scripts (`GhResult`, `Sequence[str]`, `Path | None` in `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).
- Dataclass usage appears in installer tooling (`skills/.system/skill-installer/scripts/install-skill-from-github.py`).

## Code Style

**Formatting:**
- Shebang-first executable scripts (`#!/usr/bin/env python3`, `#!/usr/bin/env bash`) across `skills/**/scripts/`.
- Python style is standard-library-first imports with explicit typing in modern scripts.
- Shell scripts prefer strict execution flags (`set -euo pipefail`) as seen in `skills/.curated/playwright/scripts/playwright_cli.sh`.

**Linting:**
- Centralized lint config not detected (`.eslintrc*`, `.prettierrc*`, `eslint.config.*`, `biome.json` absent at repo root).
- Convention enforcement appears procedural through skill guidance and validator scripts such as `skills/.system/skill-creator/scripts/quick_validate.py`.

## Import Organization

**Order:**
1. Python future import where used (`from __future__ import annotations`).
2. Python standard library modules (`argparse`, `json`, `subprocess`, `pathlib`).
3. Third-party modules when needed (`yaml`, `openpyxl`, `pdf2image`, `openai`).
4. Local module imports (`from github_utils import ...` in `skills/.system/skill-installer/scripts/list-skills.py`).

**Path Aliases:**
- Not detected. Relative/local Python imports are used instead.

## Error Handling

**Patterns:**
- CLI tools fail fast with explicit exit status and context message (`raise SystemExit(...)` patterns in many scripts).
- External command failures are surfaced with stderr messages and non-zero exits (`skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).
- Shell scripts short-circuit on failure via strict mode and explicit checks (`skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`).

## Logging

**Framework:**
- Plain stdout/stderr logging (`print(..., file=sys.stderr)` in Python scripts and `echo ... >&2` in shell scripts).

**Patterns:**
- Human-readable error context for failed preconditions (missing tool, auth, path).
- Minimal progress output, then structured output where needed (JSON options in scripts like `skills/.system/skill-installer/scripts/list-skills.py`).

## Comments

**When to Comment:**
- Comments are used for non-obvious logic and ordering constraints, especially in shell scripts (for example framework detection order comments in `skills/.curated/vercel-deploy/scripts/deploy.sh`).

**JSDoc/TSDoc:**
- Not detected (no TypeScript source in this checkout).

## Function Design

**Size:**
- Utility scripts often split workflow into focused helper functions (for example `run_gh_command`, `resolve_pr`, `fetch_checks`).

**Parameters:**
- Argument parsing is explicit and documented with `argparse` options in Python scripts.

**Return Values:**
- Functions return typed primitives or lightweight objects; command-line exit status controls success/failure path.

## Module Design

**Exports:**
- Script modules are primarily CLI entrypoints with `main()` and `if __name__ == "__main__":`.

**Barrel Files:**
- Not applicable/not detected for this repository shape.

---

*Convention analysis: 2026-02-25*
