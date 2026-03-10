# Testing Patterns

**Analysis Date:** 2026-02-25

## Test Framework

**Runner:**
- Not detected as a centralized automated test runner.
- No `jest.config.*`, `vitest.config.*`, `pytest.ini`, or `tox.ini` detected at repository root.

**Assertion Library:**
- Not detected (no dedicated unit/integration test suite present).

**Run Commands:**
```bash
rg --files . | wc -l                                    # Inventory file count
find . -type f \( -name '*.test.*' -o -name '*.spec.*' \)   # Discover tests (expected empty)
python3 skills/.system/skill-creator/scripts/quick_validate.py skills/.curated/openai-docs
```

## Test File Organization

**Location:**
- Not detected. No `tests/` directory and no co-located `*.test.*`/`*.spec.*` files found.

**Naming:**
- Not applicable for automated tests in current repo state.

**Structure:**
```
No repository-wide automated test tree detected.
Validation is script- and workflow-driven (for example quick validators and manual checks).
```

## Test Structure

**Suite Organization:**
```typescript
// Not detected in repository; no TypeScript/Jest/Vitest suites present.
```

**Patterns:**
- Validation is mostly command-based smoke checking for scripts and metadata.
- Examples include frontmatter/interface checks in `skills/.system/skill-creator/scripts/quick_validate.py`.

## Mocking

**Framework:**
- Not detected.

**Patterns:**
```typescript
// Not detected in repository test code.
```

**What to Mock:**
- For future tests, external APIs should be mocked (GitHub/OpenAI/Sentry) used in scripts such as `skills/.system/skill-installer/scripts/github_utils.py` and `skills/.curated/sentry/scripts/sentry_api.py`.

**What NOT to Mock:**
- Pure file-path and frontmatter parsing logic in local validators should be tested against fixture files directly.

## Fixtures and Factories

**Test Data:**
```typescript
// Not detected as a formal fixture system.
// Existing examples under `skills/.curated/**/evaluations/*.json` can be repurposed as fixtures.
```

**Location:**
- Closest existing structured examples are evaluation JSON files in `skills/.curated/notion-*/evaluations/`.

## Coverage

**Requirements:**
- None enforced in current repository state.

**View Coverage:**
```bash
# Not available - no centralized coverage pipeline detected.
```

## Test Types

**Unit Tests:**
- Not detected.

**Integration Tests:**
- Not detected.

**E2E Tests:**
- Not detected.

## Common Patterns

**Async Testing:**
```typescript
// Not detected.
```

**Error Testing:**
```typescript
// Not detected.
```

---

*Testing analysis: 2026-02-25*
