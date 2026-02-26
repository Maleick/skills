from pathlib import Path
import subprocess

import pytest

from tools.skill_audit.scanner import (
    discover_changed_files,
    discover_skill_dirs,
    filter_impacted_skill_dirs,
    impacted_skill_keys,
)


def _relative_paths(paths: list[Path], repo_root: Path) -> list[str]:
    return [path.relative_to(repo_root).as_posix() for path in paths]


def test_discover_skill_dirs_scans_all_tiers(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "skills/.system/alpha").mkdir(parents=True)
    (repo_root / "skills/.curated/bravo").mkdir(parents=True)
    (repo_root / "skills/.experimental/charlie").mkdir(parents=True)
    (repo_root / "skills/.curated/README.md").write_text("not a directory", encoding="utf-8")

    discovered = discover_skill_dirs(repo_root)
    assert _relative_paths(discovered, repo_root) == [
        "skills/.curated/bravo",
        "skills/.experimental/charlie",
        "skills/.system/alpha",
    ]


def test_discover_skill_dirs_returns_only_immediate_children(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "skills/.system/top").mkdir(parents=True)
    (repo_root / "skills/.system/top/nested-child").mkdir(parents=True)

    discovered = discover_skill_dirs(repo_root)
    assert _relative_paths(discovered, repo_root) == ["skills/.system/top"]


def test_discover_skill_dirs_is_deterministic(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    for path in (
        "skills/.experimental/zeta",
        "skills/.curated/alpha",
        "skills/.system/mike",
        "skills/.experimental/beta",
    ):
        (repo_root / path).mkdir(parents=True)

    first = _relative_paths(discover_skill_dirs(repo_root), repo_root)
    second = _relative_paths(discover_skill_dirs(repo_root), repo_root)
    assert first == second


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "skill-audit@example.com")
    _git(repo_root, "config", "user.name", "Skill Audit")


def test_impacted_skill_keys_maps_only_skill_paths() -> None:
    changed_files = [
        "skills/.curated/alpha/SKILL.md",
        "skills/.curated/alpha/references/guide.md",
        "skills/.experimental/bravo/agents/openai.yaml",
        "README.md",
        "tools/skill_audit/cli.py",
    ]

    assert impacted_skill_keys(changed_files) == {
        "skills/.curated/alpha",
        "skills/.experimental/bravo",
    }


def test_filter_impacted_skill_dirs_preserves_discovery_order(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    for rel in (
        "skills/.system/base",
        "skills/.curated/alpha",
        "skills/.curated/bravo",
        "skills/.experimental/zeta",
    ):
        (repo_root / rel).mkdir(parents=True)

    discovered = discover_skill_dirs(repo_root)
    filtered = filter_impacted_skill_dirs(
        discovered,
        repo_root,
        [
            "skills/.curated/bravo/SKILL.md",
            "skills/.experimental/zeta/agents/openai.yaml",
            "docs/notes.md",
        ],
    )

    assert _relative_paths(filtered, repo_root) == [
        "skills/.curated/bravo",
        "skills/.experimental/zeta",
    ]


def test_discover_changed_files_uses_working_tree_when_no_range(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    (repo_root / "skills/.curated/alpha").mkdir(parents=True)
    (repo_root / "skills/.experimental/bravo").mkdir(parents=True)
    (repo_root / "skills/.curated/alpha/SKILL.md").write_text("initial\n", encoding="utf-8")
    (repo_root / "skills/.experimental/bravo/SKILL.md").write_text(
        "experimental\n",
        encoding="utf-8",
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "baseline")

    (repo_root / "skills/.curated/alpha/SKILL.md").write_text("changed\n", encoding="utf-8")
    (repo_root / "skills/.experimental/bravo/new.md").write_text("new\n", encoding="utf-8")
    _git(repo_root, "add", "skills/.experimental/bravo/new.md")
    (repo_root / "skills/.experimental/bravo/untracked.md").write_text("u\n", encoding="utf-8")

    changed = discover_changed_files(repo_root, compare_range=None)
    assert changed == [
        "skills/.curated/alpha/SKILL.md",
        "skills/.experimental/bravo/new.md",
        "skills/.experimental/bravo/untracked.md",
    ]


def test_discover_changed_files_with_compare_range(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    (repo_root / "skills/.curated/alpha").mkdir(parents=True)
    skill_path = repo_root / "skills/.curated/alpha/SKILL.md"
    skill_path.write_text("v1\n", encoding="utf-8")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "v1")

    skill_path.write_text("v2\n", encoding="utf-8")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "v2")

    changed = discover_changed_files(repo_root, compare_range="HEAD~1..HEAD")
    assert changed == ["skills/.curated/alpha/SKILL.md"]


def test_discover_changed_files_invalid_range_raises(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    (repo_root / "skills/.curated/alpha").mkdir(parents=True)
    (repo_root / "skills/.curated/alpha/SKILL.md").write_text("v1\n", encoding="utf-8")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "v1")

    with pytest.raises(RuntimeError):
        discover_changed_files(repo_root, compare_range="HEAD~99..HEAD")


def test_discover_changed_files_ignores_cache_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    (repo_root / "skills/.curated/alpha").mkdir(parents=True)
    (repo_root / "skills/.curated/alpha/SKILL.md").write_text("v1\n", encoding="utf-8")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "v1")

    (repo_root / "skills/.curated/alpha/SKILL.md").write_text("v2\n", encoding="utf-8")
    cache_path = repo_root / ".planning/cache/skill-audit-cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("{}", encoding="utf-8")

    changed = discover_changed_files(repo_root, compare_range=None)
    assert changed == ["skills/.curated/alpha/SKILL.md"]
