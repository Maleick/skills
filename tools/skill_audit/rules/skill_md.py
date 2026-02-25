"""Rules for SKILL.md presence and frontmatter validation."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..findings import Finding

REQUIRED_FRONTMATTER_KEYS: tuple[str, ...] = ("name", "description")


def _to_repo_path(path: Path, repo_root: Path) -> str:
    root = repo_root.resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _extract_frontmatter_block(content: str) -> str | None:
    if not content.startswith("---\n"):
        return None

    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if not match:
        return None
    return match.group(1)


def validate_skill_md(skill_dir: Path, repo_root: Path) -> list[Finding]:
    """Validate SKILL.md for one skill directory."""
    skill_md_path = skill_dir / "SKILL.md"
    result_path = _to_repo_path(skill_md_path, repo_root)

    if not skill_md_path.exists():
        return [
            Finding(
                id="META-001",
                severity="invalid",
                path=result_path,
                message="Missing SKILL.md file.",
                suggested_fix="Create SKILL.md with required YAML frontmatter keys: name and description.",
            )
        ]

    content = skill_md_path.read_text(encoding="utf-8")
    frontmatter_block = _extract_frontmatter_block(content)
    if frontmatter_block is None:
        return [
            Finding(
                id="META-002",
                severity="invalid",
                path=result_path,
                message="Missing or malformed YAML frontmatter block.",
                suggested_fix="Start SKILL.md with --- frontmatter and close it with --- before body content.",
            )
        ]

    try:
        frontmatter = yaml.safe_load(frontmatter_block)
    except yaml.YAMLError as exc:
        return [
            Finding(
                id="META-003",
                severity="invalid",
                path=result_path,
                message=f"Invalid YAML frontmatter: {exc.__class__.__name__}",
                suggested_fix="Fix YAML syntax in frontmatter and ensure it parses to a key/value map.",
            )
        ]

    if not isinstance(frontmatter, dict):
        return [
            Finding(
                id="META-004",
                severity="invalid",
                path=result_path,
                message="Frontmatter must be a YAML mapping.",
                suggested_fix="Use key/value pairs for frontmatter metadata (for example: name, description).",
            )
        ]

    missing = [key for key in REQUIRED_FRONTMATTER_KEYS if not frontmatter.get(key)]
    if missing:
        return [
            Finding(
                id="META-005",
                severity="invalid",
                path=result_path,
                message=f"Frontmatter is missing required keys: {', '.join(missing)}.",
                suggested_fix="Add missing required frontmatter keys with non-empty values.",
            )
        ]

    return [
        Finding(
            id="META-000",
            severity="valid",
            path=result_path,
            message="SKILL.md exists and required frontmatter is valid.",
            suggested_fix="No action required.",
        )
    ]
