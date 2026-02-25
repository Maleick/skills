"""Tier-aware scanner for skill directory discovery."""

from __future__ import annotations

from pathlib import Path

SKILL_TIERS: tuple[str, ...] = (
    "skills/.system",
    "skills/.curated",
    "skills/.experimental",
)


def discover_skill_dirs(repo_root: Path) -> list[Path]:
    """Return deterministic skill directories across all configured tiers."""
    root = repo_root.resolve()
    found: list[Path] = []

    for tier in SKILL_TIERS:
        tier_path = root / tier
        if not tier_path.is_dir():
            continue
        for entry in tier_path.iterdir():
            if entry.is_dir():
                found.append(entry.resolve())

    return sorted(found, key=lambda item: item.as_posix())
