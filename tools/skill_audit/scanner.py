"""Tier-aware scanner for skill directory discovery and incremental scope filtering."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Iterable

SKILL_TIERS: tuple[str, ...] = (
    "skills/.system",
    "skills/.curated",
    "skills/.experimental",
)
IGNORED_CHANGED_PREFIXES: tuple[str, ...] = (".planning/cache/",)


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


def skill_key_for_dir(skill_dir: Path, repo_root: Path) -> str:
    """Return canonical repo-relative skill key for a discovered skill directory."""
    return _to_repo_relative(skill_dir, repo_root)


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


def skill_content_fingerprint(skill_dir: Path, repo_root: Path) -> str:
    """Build a deterministic content fingerprint for one skill directory."""
    if not skill_dir.is_dir():
        raise RuntimeError(f"Skill directory does not exist: {skill_dir}")

    root = repo_root.resolve()
    skill_key = _to_repo_relative(skill_dir, root)
    hasher = hashlib.sha256()
    hasher.update(skill_key.encode("utf-8"))
    hasher.update(b"\0")

    files = sorted(
        (path for path in skill_dir.rglob("*") if path.is_file()),
        key=lambda path: _to_repo_relative(path, root),
    )
    if not files:
        hasher.update(b"<empty-skill>")
        return hasher.hexdigest()

    for file_path in files:
        rel_path = _to_repo_relative(file_path, root)
        try:
            content_hash = hashlib.sha256(file_path.read_bytes()).digest()
        except OSError as exc:
            raise RuntimeError(
                f"Failed to fingerprint '{rel_path}': {exc}"
            ) from exc

        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content_hash)
        hasher.update(b"\0")

    return hasher.hexdigest()


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
    filtered = {
        path
        for path in changed
        if not any(path.startswith(prefix) for prefix in IGNORED_CHANGED_PREFIXES)
    }
    return sorted(filtered)
