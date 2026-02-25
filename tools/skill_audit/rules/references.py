"""Local reference-path validation for skill packages."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..findings import Finding

LOCAL_REFERENCE_PREFIXES: tuple[str, ...] = ("scripts/", "references/", "assets/", "agents/")


def _to_repo_path(path: Path, repo_root: Path) -> str:
    root = repo_root.resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _normalize_candidate(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    if value.startswith("./"):
        value = value[2:]
    value = value.split("#", 1)[0].split("?", 1)[0]
    return value


def _is_local_candidate(value: str) -> bool:
    if not value or _is_url(value):
        return False
    if value.startswith("/"):
        return False
    return "/" in value and value.startswith(LOCAL_REFERENCE_PREFIXES)


def _extract_markdown_local_references(content: str) -> set[str]:
    candidates: set[str] = set()

    # Markdown links.
    for match in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        candidate = _normalize_candidate(match)
        if _is_local_candidate(candidate):
            candidates.add(candidate)

    # Backtick references.
    for match in re.findall(r"`([^`]+)`", content):
        candidate = _normalize_candidate(match)
        if _is_local_candidate(candidate):
            candidates.add(candidate)

    return candidates


def _extract_yaml_local_references(value: object) -> set[str]:
    refs: set[str] = set()

    if isinstance(value, dict):
        for nested in value.values():
            refs.update(_extract_yaml_local_references(nested))
        return refs
    if isinstance(value, list):
        for nested in value:
            refs.update(_extract_yaml_local_references(nested))
        return refs
    if not isinstance(value, str):
        return refs

    candidate = _normalize_candidate(value)
    if _is_local_candidate(candidate):
        refs.add(candidate)
    return refs


def validate_local_references(skill_dir: Path, repo_root: Path) -> list[Finding]:
    """Validate local references declared in SKILL.md and agents/openai.yaml."""
    refs: set[str] = set()
    findings: list[Finding] = []

    skill_md_path = skill_dir / "SKILL.md"
    if skill_md_path.exists():
        refs.update(_extract_markdown_local_references(skill_md_path.read_text(encoding="utf-8")))

    openai_yaml_path = skill_dir / "agents" / "openai.yaml"
    if openai_yaml_path.exists():
        try:
            openai_data = yaml.safe_load(openai_yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            openai_data = None
        refs.update(_extract_yaml_local_references(openai_data))

    for ref in sorted(refs):
        target_path = skill_dir / ref
        if target_path.exists():
            continue
        findings.append(
            Finding(
                id="META-201",
                severity="invalid",
                path=_to_repo_path(target_path, repo_root),
                message=f"Broken local reference '{ref}' in skill metadata or docs.",
                suggested_fix=f"Create '{ref}' relative to this skill, or update the reference to an existing local path.",
            )
        )

    if findings:
        return findings

    if refs:
        return [
            Finding(
                id="META-200",
                severity="valid",
                path=_to_repo_path(skill_dir, repo_root),
                message="All declared local references resolve successfully.",
                suggested_fix="No action required.",
            )
        ]

    return []
