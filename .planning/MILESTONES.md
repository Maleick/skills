# Milestones

## v1.1 Performance & Policy (Shipped: 2026-02-26)

**Delivered:** Incremental scan performance, strict repository override policy controls, and override-aware deterministic reporting/CI semantics.

**Phases completed:** 3 phases, 8 plans, 24 tasks

**Key accomplishments:**
- Implemented changed-files incremental scanning with compare-range support and deterministic impacted-skill filtering.
- Added explicit scope metadata across JSON, console, markdown, and CI outputs.
- Implemented strict `.skill-audit-overrides.yaml` parsing with unknown-key/rule fail-fast behavior.
- Integrated deterministic override precedence (`rule+tier > rule > tier > base default`) across all runtime modes.
- Surfaced effective policy profile metadata (`source`, `active`, `mode`, override counts) across output channels.
- Extended CI regression coverage for override-aware deterministic gating and profile echo behavior (`71` tests passing overall).

**Stats:**
- 38 files changed, 3,137 insertions, 69 deletions
- 3 phases, 8 plans, 24 tasks
- Timeline: ~3.25 hours of implementation+verification flow (2026-02-25 16:16 -0600 → 2026-02-25 19:11 -0600)
- Git range: `feat(05-01)` → `docs(v1.1): audit milestone completion`

**What's next:** Define v1.2 scope and requirements with `$gsd-new-milestone --auto`.

---

## v1.0 MVP (Shipped: 2026-02-25)

**Phases completed:** 4 phases, 11 plans, 33 tasks

**Key accomplishments:**
- Implemented a deterministic scanner and normalized findings model across system, curated, and experimental tiers.
- Added tier-aware metadata integrity rules including SKILL/openai parity and local reference validation.
- Shipped deterministic JSON index and markdown remediation outputs with explicit output-path controls.
- Added CI gate hardening with threshold policy flags, scoped tolerance, and split 0/1/2 exit semantics.
- Completed command-level regression coverage with 41 passing tests for validator, reporting, and CI flows.
- Published CI usage guidance in README and contributing documentation.

---
