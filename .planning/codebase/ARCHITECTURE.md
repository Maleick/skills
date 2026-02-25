# Architecture

**Analysis Date:** 2026-02-25

## Pattern Overview

**Overall:** Documentation-centric modular skill catalog.

**Key Characteristics:**
- Each skill is self-contained in a directory with `SKILL.md` as primary entrypoint (for example `skills/.curated/openai-docs/SKILL.md`).
- Optional helper resources follow predictable subdirectories (`scripts/`, `references/`, `assets/`, `agents/`) such as `skills/.system/skill-installer/`.
- Runtime behavior is mostly delegated to on-demand script execution (for example `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`).

## Layers

**Catalog Layer:**
- Purpose: Organize skill packages by maturity/stability.
- Location: `skills/.system/`, `skills/.curated/`, `skills/.experimental/`.
- Contains: Skill directories and metadata resources.
- Depends on: Repository conventions documented in `README.md`.
- Used by: Codex skill discovery and contributors adding/updating skills.

**Skill Definition Layer:**
- Purpose: Encode trigger criteria and operating instructions.
- Location: `skills/**/SKILL.md`.
- Contains: Frontmatter metadata + markdown workflow guidance.
- Depends on: Referenced resources inside each skill directory.
- Used by: Codex runtime when a skill is triggered.

**Execution Helper Layer:**
- Purpose: Provide deterministic operations for tasks that need code execution.
- Location: `skills/**/scripts/*`.
- Contains: Python, shell, Swift, and JavaScript helper scripts.
- Depends on: Host tools and external APIs (for example `gh`, `curl`, OpenAI APIs).
- Used by: Skills that need reproducible behavior beyond natural-language instructions.

**Reference/Asset Layer:**
- Purpose: Store deep references and reusable output artifacts.
- Location: `skills/**/references/*` and `skills/**/assets/*`.
- Contains: Long-form docs, examples, icons, templates, notebooks.
- Depends on: Skill-level workflows that selectively load or reuse these files.
- Used by: Codex at execution time when additional context or output assets are required.

## Data Flow

**Skill Invocation Flow:**

1. User request maps to skill metadata (name/description) declared in `skills/**/SKILL.md`.
2. Codex loads selected `SKILL.md` instructions and decides whether to read referenced files (for example `skills/.curated/playwright/references/cli.md`).
3. If deterministic work is needed, Codex executes helper scripts from paths like `skills/.system/skill-installer/scripts/list-skills.py`.
4. Results are returned to user; repository state changes only when explicitly writing files.

**State Management:**
- Repository is static content-first; no always-on service state.
- Any runtime state is ephemeral (process env vars, temp files) and scoped to script execution.

## Key Abstractions

**Skill Package:**
- Purpose: Unit of capability distribution.
- Examples: `skills/.curated/openai-docs/`, `skills/.curated/screenshot/`, `skills/.system/skill-installer/`.
- Pattern: Directory-level modular composition with required `SKILL.md`.

**Agent Metadata Contract:**
- Purpose: Define UI presentation hints for skills.
- Examples: `skills/.curated/openai-docs/agents/openai.yaml`, `skills/.system/skill-creator/agents/openai.yaml`.
- Pattern: `interface` YAML object with display text and optional icons/prompts.

**Helper Script Contract:**
- Purpose: Encapsulate repeatable workflows with CLI interfaces.
- Examples: `skills/.curated/vercel-deploy/scripts/deploy.sh`, `skills/.curated/security-ownership-map/scripts/run_ownership_map.py`.
- Pattern: Command-line entrypoint + argument parsing + explicit error exits.

## Entry Points

**Repository Entry:**
- Location: `README.md`.
- Triggers: Human contributor onboarding and high-level usage lookup.
- Responsibilities: Explain skill purpose, install pathways, and licensing.

**Skill Entry:**
- Location: `skills/**/SKILL.md`.
- Triggers: Skill selection by user prompt intent.
- Responsibilities: Define when to trigger, what workflow to run, and what resources to use.

**Script Entry:**
- Location: shebang-based scripts in `skills/**/scripts/`.
- Triggers: Explicit command execution by Codex or user.
- Responsibilities: Perform deterministic operations and emit machine-usable output.

## Error Handling

**Strategy:** Fail fast with explicit command-line errors.

**Patterns:**
- Python scripts use `raise SystemExit(...)` and argument validation (`skills/.curated/imagegen/scripts/image_gen.py`, `skills/.system/skill-installer/scripts/list-skills.py`).
- Shell scripts use strict mode (`set -euo pipefail`) in files like `skills/.curated/playwright/scripts/playwright_cli.sh`.

## Cross-Cutting Concerns

**Logging:** CLI stdout/stderr messaging for operational clarity (for example `skills/.curated/vercel-deploy/scripts/deploy.sh`).
**Validation:** Frontmatter and interface validation in `skills/.system/skill-creator/scripts/quick_validate.py` and `skills/.system/skill-creator/scripts/generate_openai_yaml.py`.
**Authentication:** Environment variable based tokens for external APIs in helper scripts and skill docs.

---

*Architecture analysis: 2026-02-25*
