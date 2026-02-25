# Skills Catalog Quality Layer

## What This Is

This project builds a quality and discovery layer for the Codex skills catalog in `/opt/skills`. The focus is to keep skill packages structurally consistent, easier to discover, and safer to evolve as the number of curated and experimental skills grows. It targets maintainers and operators who need fast confidence checks before merging skill changes.

## Core Value

Maintainers can run one reliable validation workflow that catches structural and metadata drift across all skills before changes are merged.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Add a repository-wide validator command that classifies skill directories as valid/warning/invalid.
- [ ] Generate a machine-readable skill index that improves discovery and status visibility.
- [ ] Detect and report high-risk metadata inconsistencies (missing `SKILL.md`, stale `agents/openai.yaml`, broken references).

### Out of Scope

- Rewriting existing skill content for tone/style — not required for the quality layer.
- Building a hosted web interface — command-line and file outputs are sufficient for v1.
- Enforcing opinionated writing style rules beyond required packaging/contract checks.

## Context

The repository contains a large skill catalog split across `skills/.system`, `skills/.curated`, and `skills/.experimental`, with helper scripts and metadata contracts distributed across directories. Existing quality checks are mostly manual or script-specific, which increases the chance of structural drift as the catalog grows. Initial codebase mapping already highlighted gaps such as experimental directories without `SKILL.md` and limited centralized validation gates.

## Constraints

- **Scope**: Focus on repository quality/discovery workflows, not product feature rewrites — keeps effort bounded.
- **Usability**: Output must be both human-readable and machine-readable — supports maintainers and automation.
- **Performance**: Validation pass should remain quick (target under 30 seconds) — avoids skipped checks.
- **Compatibility**: Work with current skill directory conventions and avoid breaking existing skill execution paths.
- **Adoption**: Integrate with git-friendly workflows so checks can be run pre-merge and in CI.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize a validator + index as v1 | Highest leverage against current drift and discovery pain | — Pending |
| Keep v1 CLI/file-based (no web UI) | Lower complexity and faster rollout | — Pending |
| Treat metadata contract checks as first-class | Missing/stale metadata breaks downstream skill reliability | — Pending |

---
*Last updated: 2026-02-25 after initialization*
