"""Cross-file metadata parity checks for skill packages."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..findings import Finding

FIELD_MAPPING: dict[str, str] = {
    "name": "name",
    "description": "description",
}


def _to_repo_path(path: Path, repo_root: Path) -> str:
    root = repo_root.resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _extract_skill_frontmatter(content: str) -> dict[str, object] | None:
    if not content.startswith("---\n"):
        return None
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if not match:
        return None
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_metadata_parity(skill_dir: Path, repo_root: Path) -> list[Finding]:
    """Validate parity between SKILL.md frontmatter and agents/openai.yaml."""
    skill_md_path = skill_dir / "SKILL.md"
    openai_yaml_path = skill_dir / "agents" / "openai.yaml"

    skill_rel = _to_repo_path(skill_md_path, repo_root)
    openai_rel = _to_repo_path(openai_yaml_path, repo_root)

    skill_exists = skill_md_path.exists()
    openai_exists = openai_yaml_path.exists()

    if skill_exists and not openai_exists:
        return [
            Finding(
                id="META-101",
                severity="invalid",
                path=openai_rel,
                message="Missing agents/openai.yaml counterpart for SKILL.md.",
                suggested_fix="Create agents/openai.yaml with metadata fields that match SKILL.md.",
            )
        ]
    if openai_exists and not skill_exists:
        return [
            Finding(
                id="META-102",
                severity="invalid",
                path=skill_rel,
                message="Missing SKILL.md counterpart for agents/openai.yaml.",
                suggested_fix="Create SKILL.md with required frontmatter and matching metadata.",
            )
        ]
    if not skill_exists and not openai_exists:
        return []

    skill_content = skill_md_path.read_text(encoding="utf-8")
    skill_frontmatter = _extract_skill_frontmatter(skill_content)
    if skill_frontmatter is None:
        return []

    try:
        openai_raw = yaml.safe_load(openai_yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [
            Finding(
                id="META-103",
                severity="invalid",
                path=openai_rel,
                message=f"Invalid YAML in agents/openai.yaml: {exc.__class__.__name__}.",
                suggested_fix="Fix YAML syntax in agents/openai.yaml so metadata can be compared.",
            )
        ]

    if not isinstance(openai_raw, dict):
        return [
            Finding(
                id="META-104",
                severity="invalid",
                path=openai_rel,
                message="agents/openai.yaml root must be a YAML mapping.",
                suggested_fix="Use top-level key/value metadata fields (for example: name, description).",
            )
        ]

    findings: list[Finding] = []
    for skill_key, openai_key in FIELD_MAPPING.items():
        skill_value = _normalize(skill_frontmatter.get(skill_key))
        openai_value = _normalize(openai_raw.get(openai_key))
        if skill_value != openai_value:
            findings.append(
                Finding(
                    id="META-110",
                    severity="invalid",
                    path=skill_rel,
                    message=(
                        f"Metadata mismatch for '{skill_key}': "
                        f"SKILL.md='{skill_value or '<missing>'}' vs "
                        f"agents/openai.yaml='{openai_value or '<missing>'}'."
                    ),
                    suggested_fix=f"Align '{skill_key}' values between SKILL.md and agents/openai.yaml.",
                )
            )

    if findings:
        return findings

    return [
        Finding(
            id="META-100",
            severity="valid",
            path=skill_rel,
            message="SKILL.md and agents/openai.yaml metadata parity checks passed.",
            suggested_fix="No action required.",
        )
    ]
