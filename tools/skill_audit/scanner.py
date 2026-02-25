"""Tier-aware scanner for skill directory discovery and incremental scope filtering."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

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


def _to_repo_relative(path: Path, repo_root: Path) -> str:
    root = repo_root.resolve()
    return path.resolve().relative_to(root).as_posix()


def _skill_key_from_repo_path(repo_path: str) -> str | None:
    normalized = repo_path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    if len(parts) < 3:
        return None
    if parts[0] != "skills":
        return None
    if parts[1] not in {".system", ".curated", ".experimental"}:
        return None
    return "/".join(parts[:3])


def impacted_skill_keys(changed_files: Iterable[str]) -> set[str]:
    """Return canonical skill keys impacted by the provided changed file paths."""
    impacted: set[str] = set()
    for changed in changed_files:
        key = _skill_key_from_repo_path(changed)
        if key is not None:
            impacted.add(key)
    return impacted


def filter_impacted_skill_dirs(
    skill_dirs: list[Path], repo_root: Path, changed_files: Iterable[str]
) -> list[Path]:
    """Filter discovered skill dirs to impacted skills while preserving deterministic order."""
    impacted = impacted_skill_keys(changed_files)
    if not impacted:
        return []
    return [
        skill_dir
        for skill_dir in skill_dirs
        if _to_repo_relative(skill_dir, repo_root) in impacted
    ]


def _run_git_name_only(repo_root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            args,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"Failed to run git command: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git error"
        raise RuntimeError(f"{' '.join(args)} failed: {stderr}")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def discover_changed_files(repo_root: Path, compare_range: str | None) -> list[str]:
    """Return deterministic changed file paths relative to the repo root."""
    commands: list[list[str]]
    if compare_range:
        commands = [["git", "diff", "--name-only", compare_range]]
    else:
        commands = [
            ["git", "diff", "--name-only"],
            ["git", "diff", "--name-only", "--cached"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ]

    changed: set[str] = set()
    for command in commands:
        changed.update(_run_git_name_only(repo_root, command))
    return sorted(changed)
