# Codebase Concerns

**Analysis Date:** 2026-02-25

## Tech Debt

**Experimental skill completeness mismatch:**
- Issue: Three experimental skill directories currently lack required `SKILL.md` files.
- Files: `skills/.experimental/agent-team-protocol/`, `skills/.experimental/auto-memory/`, `skills/.experimental/ralph-wiggum-loop/`.
- Impact: Discovery/trigger behavior can become inconsistent because these directories do not expose primary skill metadata.
- Fix approach: Add minimal `SKILL.md` frontmatter + usage guidance for each experimental directory or move non-skill artifacts outside `skills/.experimental/`.

**No centralized quality gate:**
- Issue: Repository has many executable scripts but no repo-level automated test/lint pipeline.
- Files: script-heavy paths such as `skills/.curated/**/scripts/` and `skills/.system/**/scripts/`.
- Impact: Regressions in CLI behavior are likely to be detected late and manually.
- Fix approach: Add lightweight CI checks for syntax (`python -m py_compile`), frontmatter validation, and smoke runs for selected scripts.

## Known Bugs

**Auto-memory listener startup invocation is easy to misuse:**
- Symptoms: Running shell script via Python interpreter causes syntax errors.
- Files: `/Users/maleick/.codex/skills/auto-memory/scripts/start_auto_memory_listener.sh`.
- Trigger: Invoking with `python3 ...start_auto_memory_listener.sh` instead of `bash ...start_auto_memory_listener.sh`.
- Workaround: Execute with shell (`bash`) explicitly.

**Experimental content may be mistaken for fully installable skills:**
- Symptoms: Directory appears skill-like but lacks trigger metadata.
- Files: `skills/.experimental/agent-team-protocol/`, `skills/.experimental/auto-memory/`, `skills/.experimental/ralph-wiggum-loop/`.
- Trigger: Tools or users assume every top-level experimental directory is a complete skill package.
- Workaround: Document status in directory README/metadata or add placeholder `SKILL.md` with clear incomplete state.

## Security Considerations

**Token-based integrations across scripts:**
- Risk: Inadvertent logging or accidental commit of secret values when extending scripts.
- Files: `skills/.system/skill-installer/scripts/github_utils.py`, `skills/.curated/imagegen/scripts/image_gen.py`, `skills/.curated/sentry/scripts/sentry_api.py`.
- Current mitigation: Scripts primarily read tokens from environment variables and avoid hardcoded secrets.
- Recommendations: Add a shared secret-redaction helper and CI pattern scan for accidental secret literals in `skills/**`.

**Remote shell/install instructions in references:**
- Risk: Copy/paste of remote install commands can introduce supply chain risk if provenance is not verified.
- Files: `skills/.curated/render-deploy/SKILL.md`, `skills/.curated/netlify-deploy/SKILL.md`.
- Current mitigation: Documentation context exists, but no automated integrity checks.
- Recommendations: Add explicit checksum/signature verification guidance where remote scripts are suggested.

## Performance Bottlenecks

**Large reference corpus increases maintenance/read overhead:**
- Problem: Long reference files are expensive to review and can be stale over time.
- Files: `skills/.curated/security-best-practices/references/*.md` (several >700 lines, with top files >1100 lines).
- Cause: Centralized all-in-one reference documents per framework.
- Improvement path: Split oversized references by subtopic and add generated TOCs/indexes.

**High number of markdown docs with manual synchronization:**
- Problem: Many interlinked docs can drift and create inconsistent guidance.
- Files: Broadly `skills/.curated/**/SKILL.md` + `references/*.md` + `agents/openai.yaml`.
- Cause: Manual edits across multiple artifacts per skill.
- Improvement path: Add consistency lints (SKILL frontmatter, agents metadata parity, dead-link checks).

## Fragile Areas

**Platform-specific screenshot tooling:**
- Files: `skills/.curated/screenshot/scripts/take_screenshot.py`, `skills/.curated/screenshot/scripts/ensure_macos_permissions.sh`, `skills/.curated/screenshot/scripts/*.swift`.
- Why fragile: Behavior depends on OS-specific utilities and permission state.
- Safe modification: Preserve explicit platform guards and keep fallback branches tested per platform.
- Test coverage: No automated cross-platform test harness detected.

**Vercel deploy shell parser logic:**
- Files: `skills/.curated/vercel-deploy/scripts/deploy.sh`.
- Why fragile: Framework detection and response parsing rely on shell text processing and command availability.
- Safe modification: Keep changes small, add JSON-safe parsing tools where possible, and preserve strict mode.
- Test coverage: Not detected in repository.

## Scaling Limits

**Catalog growth without index validation:**
- Current capacity: 30 curated skills + 4 experimental + 2 system skill directories.
- Limit: Manual discoverability and consistency checks degrade as count grows.
- Scaling path: Generate machine-readable registry and enforce per-skill validation in CI.

## Dependencies at Risk

**Unpinned optional Python dependencies:**
- Risk: Scripts rely on optional third-party packages (`yaml`, `openai`, `openpyxl`, `pdf2image`, `Pillow`) with no repository-level lock.
- Impact: Environment drift can break scripts unpredictably.
- Migration plan: Add per-skill requirement manifests or a consolidated `requirements-dev.txt` for validation environments.

## Missing Critical Features

**Repository-wide validation command:**
- Problem: No single command validates all skill packaging conventions.
- Blocks: Fast confidence checks before large refactors or mass updates.

## Test Coverage Gaps

**Script behavior and metadata validation remain mostly manual:**
- What's not tested: CLI argument handling, error paths, and metadata consistency across many scripts.
- Files: `skills/.system/skill-installer/scripts/*.py`, `skills/.system/skill-creator/scripts/*.py`, `skills/.curated/**/scripts/*`, `skills/**/agents/openai.yaml`.
- Risk: Silent breakage in automation paths and degraded skill UX.
- Priority: High.

---

*Concerns audit: 2026-02-25*
