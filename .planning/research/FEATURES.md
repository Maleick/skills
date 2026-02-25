# Feature Research

**Domain:** CLI validator operational scalability and governance
**Researched:** 2026-02-25
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Changed-files scan mode | Maintainers need fast feedback in large repos | MEDIUM | Must preserve deterministic output semantics. |
| Repo-level override policy file | Teams need local policy customization without forking | MEDIUM | Requires clear precedence and validation. |
| Override visibility in output | CI users need to know which policy was applied | LOW | Include source/profile echo in output. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Profile validation + fail-fast diagnostics | Safer adoption in CI and pre-commit | MEDIUM | Invalid config should hard-fail clearly. |
| Scope-aware incremental stats | Better confidence in partial scans | MEDIUM | Distinguish scanned subset vs full repository context. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Silent fallback on invalid override config | “Don’t break builds” instinct | hides policy drift and creates false trust | explicit runtime/config error with clear guidance |
| Auto-fix during validation | quick remediation | risky mutations in CI/read-only workflows | keep validate-only and surface actionable fixes |

## Feature Dependencies

- Override-aware reporting depends on stable override resolution contract.
- Incremental scan depends on robust changed-path collection and tier derivation.
- CI policy trust depends on both deterministic ordering and explicit scope/profile echo.

## MVP Definition (v1.1)

### Launch With (v1.1)

- [ ] Changed-files scan mode and compare-range options.
- [ ] Repository override policy profile file support.
- [ ] Clear output indicators for active profile/scope.

### Add After Validation (v1.x)

- [ ] Baseline snapshots for quality trend checks.
- [ ] Additional override profile presets and docs examples.

### Future Consideration (v2+)

- [ ] Auto-fix suggestions with dry-run mode.
- [ ] Historical reporting dashboards.

## Sources

- Existing v1.0 artifacts and requirements archive.
- Existing CLI/test behavior in `tools/skill_audit`.

---
*Feature research for: v1.1 performance + policy milestone*
*Researched: 2026-02-25*
