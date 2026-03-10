# Technology Stack

**Analysis Date:** 2026-02-25

## Languages

**Primary:**
- Markdown (documentation-first content) - dominant format across skill definitions and references in `skills/.curated/**/SKILL.md`, `skills/.curated/**/references/*.md`, and `skills/.system/**/SKILL.md`.

**Secondary:**
- Python 3 (automation and helper CLIs) in `skills/.system/skill-installer/scripts/*.py`, `skills/.system/skill-creator/scripts/*.py`, and curated helper scripts such as `skills/.curated/imagegen/scripts/image_gen.py`.
- YAML (agent metadata and config examples) in `skills/.curated/**/agents/openai.yaml` and `skills/.curated/render-deploy/assets/*.yaml`.
- Shell (platform wrappers and deploy automation) in `skills/.curated/playwright/scripts/playwright_cli.sh`, `skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`, and `skills/.curated/vercel-deploy/scripts/deploy.sh`.
- JSON (evaluation scenarios and payload examples) in `skills/.curated/notion-*/evaluations/*.json` and `skills/.curated/develop-web-game/references/action_payloads.json`.
- Swift and JavaScript for platform-specific helpers in `skills/.curated/screenshot/scripts/*.swift` and `skills/.curated/develop-web-game/scripts/web_game_playwright_client.js`.

## Runtime

**Environment:**
- No single application runtime; repository is consumed by Codex as static skill packages rooted at `README.md` and `skills/`.
- Python runtime is required for helper scripts (`#!/usr/bin/env python3`) in paths like `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py`.
- Shell tooling is required for `.sh` wrappers in `skills/.curated/playwright/scripts/playwright_cli.sh` and `skills/.curated/vercel-deploy/scripts/deploy.sh`.
- macOS + Swift runtime is required for macOS screenshot helpers in `skills/.curated/screenshot/scripts/macos_permissions.swift`.

**Package Manager:**
- No repository-wide package manager detected (no `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, or `Cargo.toml` at repo root).
- Lockfile: Not detected at repository root.

## Frameworks

**Core:**
- Codex skill packaging conventions: `SKILL.md` + optional `agents/`, `scripts/`, `references/`, `assets/` under each skill directory (for example `skills/.system/skill-installer/`).

**Testing:**
- Not detected as a centralized framework; no `*.test.*`, `*.spec.*`, or `tests/` tree found.

**Build/Dev:**
- Git + filesystem tooling for maintenance (`.gitignore`, `README.md`, and helper scripts under `skills/.system/*/scripts/`).
- `npx` bridge used by Playwright wrapper in `skills/.curated/playwright/scripts/playwright_cli.sh`.

## Key Dependencies

**Critical:**
- OpenAI SDK usage appears in `skills/.curated/imagegen/scripts/image_gen.py`, `skills/.curated/sora/scripts/sora.py`, `skills/.curated/speech/scripts/text_to_speech.py`, and `skills/.curated/transcribe/scripts/transcribe_diarize.py`.
- PyYAML is used for metadata generation/validation in `skills/.system/skill-creator/scripts/generate_openai_yaml.py` and `skills/.system/skill-creator/scripts/quick_validate.py`.
- `gh` CLI integration is core to GitHub-related skills in `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py` and `skills/.curated/gh-address-comments/scripts/fetch_comments.py`.

**Infrastructure:**
- GitHub API access via urllib helpers in `skills/.system/skill-installer/scripts/github_utils.py`.
- `curl` + tar-based packaging/deploy in `skills/.curated/vercel-deploy/scripts/deploy.sh`.

## Configuration

**Environment:**
- User-level skill installation path is controlled by `CODEX_HOME` in `skills/.system/skill-installer/scripts/list-skills.py` and `skills/.system/skill-installer/scripts/install-skill-from-github.py`.
- Token-based integrations rely on env vars such as `GITHUB_TOKEN`/`GH_TOKEN` (`skills/.system/skill-installer/scripts/github_utils.py`) and `OPENAI_API_KEY` (`skills/.curated/imagegen/scripts/image_gen.py`).
- Sandbox-awareness checks are present via `CODEX_SANDBOX` in `skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`.

**Build:**
- No dedicated build system config detected; repository behavior is file- and script-driven via `SKILL.md` guidance and helper scripts.

## Platform Requirements

**Development:**
- Works primarily as a cross-platform content repo, but some skills require platform-specific tooling:
  - macOS/Swift for screenshot internals in `skills/.curated/screenshot/scripts/*.swift`.
  - Node tooling (`npx`) for Playwright wrapper in `skills/.curated/playwright/scripts/playwright_cli.sh`.
  - Python 3 for most helper scripts in `skills/.system/*/scripts/*.py` and `skills/.curated/*/scripts/*.py`.

**Production:**
- Not a deployable service; primary "deployment" target is Git repository consumption by Codex skill loading from `skills/` and documentation in `README.md`.

---

*Stack analysis: 2026-02-25*
