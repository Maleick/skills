# Idea: Skills Catalog Quality and Discovery

**Date:** 2026-02-25  
**Status:** Draft

## One-liner

Build a lightweight quality and discovery layer for the `/opt/skills` repository so skill packs stay consistent, searchable, and easy to evolve.

## Problem

- The repository has many skill directories with mixed maturity.
- Validation is mostly manual and distributed across scripts.
- Missing or inconsistent metadata can silently degrade skill discovery and execution quality.

## Target Users

- Skill maintainers updating or adding skills.
- Engineers/operators using skills in daily Codex workflows.
- Reviewers who need fast confidence checks before merge.

## Goals

- Add one command that validates skill package shape and metadata consistency.
- Improve discoverability with a generated skill index/registry.
- Surface high-risk issues early (missing `SKILL.md`, stale `agents/openai.yaml`, broken references).

## Non-goals

- Rewriting existing skill content.
- Building a hosted web app.
- Enforcing opinionated writing style beyond required structure checks.

## MVP Scope

- Scanner for all `skills/.system`, `skills/.curated`, and `skills/.experimental` directories.
- Checks for required files and folder contracts per skill type.
- Metadata parity checks between `SKILL.md` and `agents/openai.yaml` where present.
- Machine-readable report output (`json`) plus human summary (`markdown`).

## Success Criteria

- Every skill folder is classifiable as valid, warning, or invalid.
- Validation report can run locally in under 30 seconds.
- At least one CI-ready command exists for repository-wide checks.
- Maintainers can identify and fix top structural issues in one pass.

## Risks

- False positives from intentionally incomplete experimental skills.
- Drift between rule set and evolving skill conventions.
- Tooling complexity growing faster than repository needs.

## Open Questions

- Should experimental directories be allowed to omit `SKILL.md`, or should they use a minimal placeholder contract?
- What severity levels should block merges vs. warn only?
- Should reports be committed under `.planning/` or generated on demand only?

## Why Now

This repo is large enough that manual consistency checks are expensive, and low-friction automation will improve reliability for future `gsd-new-project` and planning workflows.
