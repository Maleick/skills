import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _create_valid_repo(repo_root: Path) -> None:
    skill_dir = repo_root / "skills/.curated/demo-skill"
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references/guide.md").write_text("# Guide\n", encoding="utf-8")

    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: demo-skill\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo Skill\n\n"
            "Use `references/guide.md`.\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        "name: demo-skill\ndescription: Demo skill fixture.\n",
        encoding="utf-8",
    )


def _run_cli(repo_root: Path, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "tools.skill_audit.cli",
        "--repo-root",
        str(repo_root),
        *extra_args,
    ]
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_console_only_default(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)

    result = _run_cli(repo_root, [])
    assert result.returncode == 0
    assert "Skill Audit Report" in result.stdout
    assert "Wrote JSON index" not in result.stdout
    assert "Wrote markdown report" not in result.stdout


def test_explicit_output_paths_write_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    json_out = tmp_path / "index.json"
    markdown_out = tmp_path / "report.md"

    result = _run_cli(
        repo_root,
        ["--json-out", str(json_out), "--markdown-out", str(markdown_out)],
    )
    assert result.returncode == 0
    assert json_out.exists()
    assert markdown_out.exists()
    assert "\"skills\"" in json_out.read_text(encoding="utf-8")
    assert "# Skill Audit Remediation Report" in markdown_out.read_text(encoding="utf-8")


def test_existing_output_fails_without_force(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    json_out = tmp_path / "index.json"

    first = _run_cli(repo_root, ["--json-out", str(json_out)])
    assert first.returncode == 0

    second = _run_cli(repo_root, ["--json-out", str(json_out)])
    assert second.returncode == 2
    assert "Output file already exists" in second.stderr


def test_existing_output_overwrites_with_force(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    json_out = tmp_path / "index.json"

    first = _run_cli(repo_root, ["--json-out", str(json_out)])
    assert first.returncode == 0
    before = json_out.read_text(encoding="utf-8")

    second = _run_cli(repo_root, ["--json-out", str(json_out), "--force-overwrite"])
    assert second.returncode == 0
    after = json_out.read_text(encoding="utf-8")
    assert before == after


def test_repeated_runs_are_deterministic(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    markdown_out = tmp_path / "report.md"

    json_first = _run_cli(repo_root, ["--json"])
    json_second = _run_cli(repo_root, ["--json"])
    assert json_first.returncode == 0
    assert json_second.returncode == 0
    assert json_first.stdout == json_second.stdout

    md_first = _run_cli(repo_root, ["--markdown-out", str(markdown_out)])
    assert md_first.returncode == 0
    md_before = markdown_out.read_text(encoding="utf-8")

    md_second = _run_cli(
        repo_root,
        ["--markdown-out", str(markdown_out), "--force-overwrite"],
    )
    assert md_second.returncode == 0
    md_after = markdown_out.read_text(encoding="utf-8")
    assert md_before == md_after


def test_output_dir_uses_stable_names(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    output_dir = tmp_path / "out"

    result = _run_cli(repo_root, ["--output-dir", str(output_dir)])
    assert result.returncode == 0
    assert (output_dir / "skill-index.json").exists()
    assert (output_dir / "skill-remediation.md").exists()


def test_ci_mode_coexists_with_output_flags(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    output_dir = tmp_path / "ci-out"

    result = _run_cli(repo_root, ["--ci", "--output-dir", str(output_dir)])
    assert result.returncode == 0
    assert "Skill Audit CI Gate" in result.stdout
    assert "Result: PASS" in result.stdout
    assert (output_dir / "skill-index.json").exists()
    assert (output_dir / "skill-remediation.md").exists()
