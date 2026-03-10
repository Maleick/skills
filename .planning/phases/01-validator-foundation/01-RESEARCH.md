# Phase 1: Validator Foundation - Research

**Researched:** 2026-02-25
**Domain:** Repository-wide skill validation CLI and structural metadata checks
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- One primary validation command scans all three tiers (`.system`, `.curated`, `.experimental`) in a single run.
- Findings include severity (`valid|warning|invalid`), stable rule ID, path, and short remediation guidance.
- Include `SKILL.md` existence/frontmatter validation in this phase.
- Keep Phase 1 read-only (no autofix or file mutation).
- Keep baseline severity behavior simple; tier-specific exception tuning is deferred.

### Claude's Discretion
- Internal module breakdown for scanner/rule/formatter components.
- Exact CLI flag naming for baseline command.
- Parser/library selection details.

### Deferred Ideas (OUT OF SCOPE)
- Tier-aware severity overrides and policy exceptions.
- Cross-file parity checks (`SKILL.md` ↔ `agents/openai.yaml`).
- JSON index and markdown discovery reporting.
- CI threshold policy modes.
- Incremental scan and autofix suggestions.

</user_constraints>

<research_summary>
## Summary

Phase 1 should establish a stable validation foundation with a deterministic scanner, a typed findings model, and a focused `SKILL.md` frontmatter validator. The implementation should be Python-first to match existing repository script conventions and to minimize integration friction.

The core sequence that keeps risk low is: (1) deterministic skill inventory across all tiers, (2) normalized findings envelope (`id`, `severity`, `path`, `message`, `suggested_fix`), and (3) one frontmatter rule pack for `SKILL.md` presence and shape. This directly satisfies SCAN-01, SCAN-02, and META-01 without pulling Phase 2/3 scope into Phase 1.

Primary risks are false positives from treating non-skill directories as skills and unstable output ordering that makes diffs noisy. Both are prevented by explicit tier scanning rules and sorted output.

**Primary recommendation:** Implement a read-only Python CLI at `tools/skill_audit/` with scanner + findings model + `SKILL.md` rule set and fixture-driven tests.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`pathlib`, `argparse`, `json`) | 3.11+ | CLI + filesystem traversal + serialization | Already used across existing skill tooling and sufficient for Phase 1 requirements. |
| `PyYAML` | 6.x | Parse YAML frontmatter safely | Existing repo tooling already depends on YAML parsing patterns for skill metadata. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `typing` / `dataclasses` (stdlib) | 3.11+ | Strong finding/result contracts | Use for predictable internal model and testability. |
| `pytest` | 8.x | Fast deterministic validation tests | Use for fixture-based scan and rule checks. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python CLI | Shell-only validator (`find` + `grep`) | Faster to start but brittle and hard to extend with structured findings. |
| `PyYAML` parsing | Regex-only frontmatter parsing | Less dependency footprint but error-prone for multiline/frontmatter edge cases. |

**Installation:**
```bash
python3 -m pip install pyyaml pytest
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
tools/
└── skill_audit/
    ├── cli.py                # command entrypoint
    ├── scanner.py            # tier directory and skill inventory
    ├── findings.py           # finding/result models
    ├── rules/
    │   └── skill_md.py       # SKILL.md presence + frontmatter checks
    └── tests/
        ├── fixtures/
        ├── test_scanner.py
        └── test_skill_md_rules.py
```

### Pattern 1: Deterministic Scan Pipeline
**What:** Discover candidate skill folders by tier, normalize, then sort by path.
**When to use:** Any repo-wide structural validation with diff-sensitive outputs.
**Example:**
```python
skills = sorted(discover_skills(repo_root))
for skill in skills:
    findings.extend(run_rules(skill))
```

### Pattern 2: Typed Findings Envelope
**What:** Every rule returns the same finding shape.
**When to use:** Multiple rule types and future output adapters.
**Example:**
```python
Finding(id="META-001", severity="invalid", path="skills/.experimental/auto-memory", message="Missing SKILL.md")
```

### Anti-Patterns to Avoid
- **Implicit path discovery without tier filtering:** causes noise by scanning unrelated directories.
- **Rule logic mixed with output rendering:** makes testing and extension harder.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML frontmatter parsing | Custom line-splitting parser | `PyYAML` + bounded frontmatter extraction | Avoids edge-case bugs and malformed parsing. |
| Path sorting/grouping | Ad-hoc comparator chains in multiple places | Single normalized path utility | Prevents inconsistent ordering across commands/tests. |
| Test harness | Manual one-off shell checks only | Fixture-based `pytest` suite | Keeps behavior stable as rules expand. |

**Key insight:** Phase 1 should hand-roll rule logic, not low-level parsing infrastructure.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Treating every folder as a skill package
**What goes wrong:** Validator reports false invalids on non-skill utility directories.
**Why it happens:** No explicit tier/skill candidate filtering.
**How to avoid:** Limit phase scan scope to immediate skill directories under `.system`, `.curated`, `.experimental`.
**Warning signs:** High invalid count with paths that are clearly not intended as skills.

### Pitfall 2: Unstable finding order
**What goes wrong:** Output changes run-to-run, creating noisy diffs.
**Why it happens:** Reliance on filesystem iteration order.
**How to avoid:** Stable sort by tier + directory + rule ID.
**Warning signs:** No-code-change runs produce different output ordering.

### Pitfall 3: Over-validating before baseline confidence
**What goes wrong:** Phase 1 absorbs Phase 2/3 scope and slips.
**Why it happens:** Adding parity/index/reporting too early.
**How to avoid:** Hard boundary: only scan/finding model/`SKILL.md` validation in this phase.
**Warning signs:** Tasks mention `openai.yaml` parity or CI thresholds in Phase 1 plans.
</common_pitfalls>

<code_examples>
## Code Examples

### Skill directory inventory
```python
from pathlib import Path

TIERS = ["skills/.system", "skills/.curated", "skills/.experimental"]

def discover_skill_dirs(repo_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for tier in TIERS:
        tier_path = repo_root / tier
        if not tier_path.exists():
            continue
        dirs.extend([p for p in tier_path.iterdir() if p.is_dir()])
    return sorted(dirs)
```

### Frontmatter presence and parse check
```python
import yaml

def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise ValueError("Missing YAML frontmatter")
    _, body = text.split("---\n", 1)
    yaml_block, _rest = body.split("\n---", 1)
    data = yaml.safe_load(yaml_block) or {}
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a mapping")
    return data
```

### Finding normalization
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    path: str
    message: str
    suggested_fix: str
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex-only metadata checks | Typed validation + schema-aligned findings | Ongoing best-practice shift | Better CI compatibility and lower false positives. |
| Ad-hoc one-off lint scripts | Layered scanner/rule/output pipeline | Ongoing | Easier extension to future phases without rewrites. |

**New tools/patterns to consider:**
- Structured findings models from day one.
- Deterministic output ordering as a first-class requirement.

**Deprecated/outdated:**
- Non-deterministic directory traversal for policy outputs.
</sota_updates>

<open_questions>
## Open Questions

1. **Should experimental directories without `SKILL.md` be `warning` or `invalid` in Phase 1 baseline?**
   - What we know: Context asks for simple baseline behavior; strict tuning deferred.
   - What's unclear: Exact default severity expectation for these known gaps.
   - Recommendation: Start with `invalid` for missing `SKILL.md` in all tiers in Phase 1, then introduce tier overrides in Phase 2.

2. **CLI naming convention (`skill-audit` vs `validate-skills`)**
   - What we know: User wants one primary command.
   - What's unclear: Preferred naming style for maintainers.
   - Recommendation: Use `python3 -m tools.skill_audit.cli` internally now; add stable alias in later phase if needed.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Local repository conventions: `/opt/skills/skills/**` and `.planning` artifacts.
- Existing Python tooling patterns in `skills/.system/skill-creator/scripts/*.py` and `skills/.system/skill-installer/scripts/*.py`.

### Secondary (MEDIUM confidence)
- [Python argparse docs](https://docs.python.org/3/library/argparse.html)
- [PyYAML docs](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [pytest docs](https://docs.pytest.org/)

### Tertiary (LOW confidence - needs validation)
- None.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python CLI validation tool
- Ecosystem: YAML parsing + test harness
- Patterns: deterministic scan, typed findings, scoped rules
- Pitfalls: scope creep, false positives, unstable outputs

**Confidence breakdown:**
- Standard stack: HIGH — aligned with local conventions and stable ecosystem
- Architecture: HIGH — straightforward layered policy tool pattern
- Pitfalls: HIGH — directly reflected in current repository signals
- Code examples: MEDIUM — local adaptation expected during implementation

**Research date:** 2026-02-25
**Valid until:** 2026-03-27
</metadata>

---

*Phase: 01-validator-foundation*
*Research completed: 2026-02-25*
*Ready for planning: yes*
