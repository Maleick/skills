# External Integrations

**Analysis Date:** 2026-02-25

## APIs & External Services

**GitHub Platform:**
- GitHub Contents API and repo download paths are used for skill listing/install workflows.
  - SDK/Client: Python urllib in `skills/.system/skill-installer/scripts/github_utils.py` and `skills/.system/skill-installer/scripts/install-skill-from-github.py`.
  - Auth: Optional `GITHUB_TOKEN` or `GH_TOKEN` env vars (`skills/.system/skill-installer/scripts/github_utils.py`).

**OpenAI APIs:**
- OpenAI model APIs are used by media-focused helper scripts.
  - Integration scripts: `skills/.curated/imagegen/scripts/image_gen.py`, `skills/.curated/sora/scripts/sora.py`, `skills/.curated/speech/scripts/text_to_speech.py`, `skills/.curated/transcribe/scripts/transcribe_diarize.py`.
  - Auth: `OPENAI_API_KEY` env var checked directly in these scripts.

**Issue Tracking / Observability APIs:**
- Sentry REST API utility script in `skills/.curated/sentry/scripts/sentry_api.py`.
  - Integration method: HTTP requests via `urllib.request`.
  - Auth: token-based auth handled through script inputs/env conventions in that file.

**Deployment Helper Endpoint:**
- Vercel claimable deploy endpoint in `skills/.curated/vercel-deploy/scripts/deploy.sh`.
  - Endpoint: `https://codex-deploy-skills.vercel.sh/api/deploy`.
  - Integration method: `curl` POST with tarball upload.

## Data Storage

**Databases:**
- Not detected. No repository-owned database layer or migration directory is present.

**File Storage:**
- Local filesystem repository content only (`skills/`, `README.md`, `.gitignore`, `.planning/`).
- Generated artifacts for planning are stored in `.planning/codebase/*.md`.

**Caching:**
- No centralized cache service detected.
- Local transient cache paths are used by specific scripts only (for example module cache in `skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`).

## Authentication & Identity

**Auth Provider:**
- No single repo-wide auth provider.
- Per-integration token patterns exist in scripts and skill docs:
  - GitHub token env vars in `skills/.system/skill-installer/scripts/github_utils.py`.
  - OpenAI API keys referenced in `skills/.curated/openai-docs/SKILL.md` and media scripts.

**OAuth Integrations:**
- Not detected as repository runtime code.

## Monitoring & Observability

**Error Tracking:**
- Sentry-specific API support is encapsulated in `skills/.curated/sentry/scripts/sentry_api.py`.

**Logs:**
- CLI-centric stderr/stdout reporting across Python and shell helper scripts (for example `skills/.curated/gh-fix-ci/scripts/inspect_pr_checks.py` and `skills/.curated/vercel-deploy/scripts/deploy.sh`).

## CI/CD & Deployment

**Hosting:**
- Repository itself is documentation/content; no primary service host defined.
- Several skills contain deployment guidance for external platforms such as Netlify (`skills/.curated/netlify-deploy/SKILL.md`) and Render (`skills/.curated/render-deploy/SKILL.md`).

**CI Pipeline:**
- Not detected (`.github/workflows` not present in this checkout).

## Environment Configuration

**Required env vars:**
- `CODEX_HOME` for install destination resolution (`skills/.system/skill-installer/scripts/list-skills.py`).
- `GITHUB_TOKEN`/`GH_TOKEN` for authenticated GitHub API access (`skills/.system/skill-installer/scripts/github_utils.py`).
- `OPENAI_API_KEY` for OpenAI media scripts (`skills/.curated/imagegen/scripts/image_gen.py` and peers).
- `CODEX_SANDBOX` branch logic in screenshot permission checks (`skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`).

**Secrets location:**
- Environment variables only; no committed secrets directory detected.

## Webhooks & Callbacks

**Incoming:**
- Not detected as repository-managed webhook handlers.

**Outgoing:**
- Outgoing HTTP calls in helper scripts to third-party APIs and endpoints, notably GitHub and Vercel deployment endpoint paths cited above.

---

*Integration audit: 2026-02-25*
