from pathlib import Path

from tools.skill_audit.scanner import discover_skill_dirs


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
