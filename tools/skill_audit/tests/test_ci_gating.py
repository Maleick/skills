import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _write_skill(
    repo_root: Path,
    *,
    tier: str,
    name: str,
    skill_name: str,
    openai_name: str,
) -> None:
    skill_dir = repo_root / f"skills/.{tier}/{name}"
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            f"name: {skill_name}\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            f"# {skill_name}\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        f"name: {openai_name}\ndescription: Demo skill fixture.\n",
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


def _write_override(repo_root: Path, content: str) -> None:
    (repo_root / ".skill-audit-overrides.yaml").write_text(content, encoding="utf-8")


def test_ci_default_fails_when_invalid_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-broken",
        skill_name="curated-broken",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, ["--ci"])
    assert result.returncode == 1
    assert "Skill Audit CI Gate" in result.stdout
    assert "Threshold: warning" in result.stdout
    assert "Result: FAIL" in result.stdout


def test_ci_default_passes_when_only_warning_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="experimental",
        name="experimental-warning",
        skill_name="experimental-warning",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, ["--ci"])
    assert result.returncode == 0
    assert "Result: PASS" in result.stdout
    assert "invalid=0" in result.stdout


def test_ci_strict_mode_fails_on_warning(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="experimental",
        name="experimental-warning",
        skill_name="experimental-warning",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, ["--ci", "--max-severity", "valid"])
    assert result.returncode == 1
    assert "Threshold: valid" in result.stdout
    assert "Result: FAIL" in result.stdout


def test_ci_scoped_tolerant_mode_ignores_out_of_scope_invalid(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-invalid",
        skill_name="curated-invalid",
        openai_name="different-name",
    )
    _write_skill(
        repo_root,
        tier="experimental",
        name="experimental-warning",
        skill_name="experimental-warning",
        openai_name="different-name",
    )

    result = _run_cli(
        repo_root,
        ["--ci", "--tiers", "experimental", "--max-severity", "warning"],
    )
    assert result.returncode == 0
    assert "Scope tiers: experimental" in result.stdout
    assert "Result: PASS" in result.stdout


def test_warning_tolerant_requires_explicit_scope(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="experimental",
        name="experimental-warning",
        skill_name="experimental-warning",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, ["--ci", "--max-severity", "warning"])
    assert result.returncode == 2
    assert "requires explicit --tiers scope" in result.stderr


def test_tier_parser_rejects_unknown_and_empty_values(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="valid-curated",
        skill_name="valid-curated",
        openai_name="valid-curated",
    )

    unknown = _run_cli(repo_root, ["--ci", "--tiers", "curated,unknown"])
    assert unknown.returncode == 2
    assert "Unknown tier value(s)" in unknown.stderr

    empty = _run_cli(repo_root, ["--ci", "--tiers", ","])
    assert empty.returncode == 2
    assert "Invalid --tiers value" in empty.stderr


def test_verbose_ci_requires_ci_mode(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-invalid",
        skill_name="curated-invalid",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, ["--verbose-ci"])
    assert result.returncode == 2
    assert "--verbose-ci requires --ci" in result.stderr


def test_ci_verbose_mode_prints_detailed_findings(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-invalid",
        skill_name="curated-invalid",
        openai_name="different-name",
    )

    compact = _run_cli(repo_root, ["--ci"])
    assert compact.returncode == 1
    assert "In-scope details:" not in compact.stdout
    assert "Fix:" not in compact.stdout

    verbose = _run_cli(repo_root, ["--ci", "--verbose-ci"])
    assert verbose.returncode == 1
    assert "In-scope details:" in verbose.stdout
    assert "Fix:" in verbose.stdout
    assert "[invalid]" in verbose.stdout


def test_non_ci_behavior_remains_unchanged(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-invalid",
        skill_name="curated-invalid",
        openai_name="different-name",
    )

    result = _run_cli(repo_root, [])
    assert result.returncode == 1
    assert "Skill Audit Report" in result.stdout


def test_ci_override_can_escalate_warning_to_invalid(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="experimental",
        name="experimental-warning",
        skill_name="experimental-warning",
        openai_name="different-name",
    )
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  rule_tier:\n"
            "    experimental:\n"
            "      META-110: invalid\n"
        ),
    )

    result = _run_cli(repo_root, ["--ci"])
    assert result.returncode == 1
    assert "Result: FAIL" in result.stdout
    assert "invalid=1" in result.stdout


def test_ci_invalid_override_file_returns_config_error(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_skill(
        repo_root,
        tier="curated",
        name="curated-valid",
        skill_name="curated-valid",
        openai_name="curated-valid",
    )
    _write_override(repo_root, "version: 1\nseverity_overrides: [\n")

    result = _run_cli(repo_root, ["--ci"])
    assert result.returncode == 2
    assert "runtime-error:" in result.stderr
