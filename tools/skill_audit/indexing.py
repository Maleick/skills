"""Skill index aggregation and JSON payload generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .findings import ALLOWED_SEVERITIES, Finding

SEVERITY_RANK: dict[str, int] = {"invalid": 0, "warning": 1, "valid": 2}
TIER_ORDER: tuple[str, ...] = ("system", "curated", "experimental", "unknown")


def _to_repo_path(path: Path, repo_root: Path) -> str:
    root = repo_root.resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _skill_key_from_path(path: str) -> str | None:
    parts = path.replace("\\", "/").split("/")
    if len(parts) < 3:
        return None
    if parts[0] != "skills":
        return None
    if parts[1] not in {".system", ".curated", ".experimental"}:
        return None
    return "/".join(parts[:3])


def _tier_from_skill_key(skill_key: str) -> str:
    parts = skill_key.split("/")
    if len(parts) < 2:
        return "unknown"
    mapping = {
        ".system": "system",
        ".curated": "curated",
        ".experimental": "experimental",
    }
    return mapping.get(parts[1], "unknown")


def _severity_counts_template() -> dict[str, int]:
    return {severity: 0 for severity in ALLOWED_SEVERITIES}


def _extract_skill_frontmatter(skill_md_path: Path) -> dict[str, Any] | None:
    if not skill_md_path.exists():
        return None

    content = skill_md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if not match:
        return None
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_openai_metadata(openai_path: Path) -> dict[str, Any] | None:
    if not openai_path.exists():
        return None
    try:
        parsed = yaml.safe_load(openai_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_key_metadata(skill_dir: Path) -> dict[str, Any]:
    skill_md_path = skill_dir / "SKILL.md"
    openai_path = skill_dir / "agents" / "openai.yaml"

    skill_md = _extract_skill_frontmatter(skill_md_path) or {}
    openai = _extract_openai_metadata(openai_path) or {}

    resolved_name = skill_md.get("name") or openai.get("name")
    resolved_description = skill_md.get("description") or openai.get("description")

    return {
        "name": str(resolved_name) if resolved_name is not None else None,
        "description": str(resolved_description) if resolved_description is not None else None,
        "has_skill_md": skill_md_path.exists(),
        "has_openai_yaml": openai_path.exists(),
        "skill_md_name": str(skill_md.get("name")) if skill_md.get("name") is not None else None,
        "skill_md_description": (
            str(skill_md.get("description")) if skill_md.get("description") is not None else None
        ),
        "openai_name": str(openai.get("name")) if openai.get("name") is not None else None,
        "openai_description": (
            str(openai.get("description")) if openai.get("description") is not None else None
        ),
    }


def _status_from_counts(severity_counts: dict[str, int]) -> str:
    if severity_counts["invalid"] > 0:
        return "invalid"
    if severity_counts["warning"] > 0:
        return "warning"
    return "valid"


def _default_scan_metadata(skill_count: int) -> dict[str, Any]:
    return {
        "mode": "full",
        "compare_range": None,
        "changed_file_count": 0,
        "changed_files": [],
        "impacted_skill_count": skill_count,
        "scanned_skill_count": skill_count,
        "total_skill_count": skill_count,
        "scanned_skills": [],
    }


def build_skill_index(
    skill_dirs: list[Path],
    findings: list[Finding],
    repo_root: Path,
    scan_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic JSON index payload from findings and scanned skill dirs."""
    entries_by_key: dict[str, dict[str, Any]] = {}

    for skill_dir in sorted(skill_dirs, key=lambda item: _to_repo_path(item, repo_root)):
        skill_key = _to_repo_path(skill_dir, repo_root)
        entries_by_key[skill_key] = {
            "path": skill_key,
            "tier": _tier_from_skill_key(skill_key),
            "status": "valid",
            "finding_count": 0,
            "severity_counts": _severity_counts_template(),
            "metadata": _extract_key_metadata(skill_dir),
            "findings": [],
        }

    for finding in findings:
        skill_key = _skill_key_from_path(finding.path)
        if not skill_key:
            continue
        if skill_key not in entries_by_key:
            continue
        entry = entries_by_key[skill_key]
        entry["finding_count"] += 1
        entry["severity_counts"][finding.severity] += 1
        entry["findings"].append(finding.to_dict())

    for entry in entries_by_key.values():
        entry["status"] = _status_from_counts(entry["severity_counts"])
        entry["findings"].sort(
            key=lambda item: (
                SEVERITY_RANK[item["severity"]],
                item["path"],
                item["id"],
                item["message"],
            )
        )

    ordered_entries = sorted(entries_by_key.values(), key=lambda item: item["path"])

    severity_totals = _severity_counts_template()
    for finding in findings:
        severity_totals[finding.severity] += 1

    tier_totals: dict[str, dict[str, Any]] = {
        tier: {
            "skill_count": 0,
            "finding_count": 0,
            "status_counts": _severity_counts_template(),
            "severity_totals": _severity_counts_template(),
        }
        for tier in TIER_ORDER
    }

    for entry in ordered_entries:
        tier = entry["tier"]
        tier_total = tier_totals[tier]
        tier_total["skill_count"] += 1
        tier_total["finding_count"] += entry["finding_count"]
        tier_total["status_counts"][entry["status"]] += 1
        for severity in ALLOWED_SEVERITIES:
            tier_total["severity_totals"][severity] += entry["severity_counts"][severity]

    summary = {
        "global": {
            "skill_count": len(ordered_entries),
            "finding_count": len(findings),
            "total_skill_count": (
                scan_metadata.get("total_skill_count")
                if scan_metadata is not None
                else len(ordered_entries)
            ),
        },
        "severity_totals": severity_totals,
        "tier_totals": tier_totals,
    }

    resolved_scan = _default_scan_metadata(len(ordered_entries))
    if scan_metadata is not None:
        resolved_scan.update(scan_metadata)

    return {
        "skill_count": len(ordered_entries),
        "scan": resolved_scan,
        "summary": summary,
        "skills": ordered_entries,
    }
