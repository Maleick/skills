import subprocess
import sys
from pathlib import Path
import json


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


def _create_valid_skill(repo_root: Path, rel_skill_dir: str, skill_name: str) -> None:
    skill_dir = repo_root / rel_skill_dir
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references/guide.md").write_text("# Guide\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            f"name: {skill_name}\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo Skill\n\n"
            "Use `references/guide.md`.\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        f"name: {skill_name}\ndescription: Demo skill fixture.\n",
        encoding="utf-8",
    )


def _create_mismatch_skill(repo_root: Path, rel_skill_dir: str, skill_name: str) -> None:
    skill_dir = repo_root / rel_skill_dir
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
        "name: different-name\ndescription: Demo skill fixture.\n",
        encoding="utf-8",
    )


def _write_override(repo_root: Path, content: str) -> None:
    (repo_root / ".skill-audit-overrides.yaml").write_text(content, encoding="utf-8")


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )


def _init_git_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "skill-audit@example.com")
    _git(repo_root, "config", "user.name", "Skill Audit")


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
    assert "Policy profile active: no" in result.stdout
    assert "Policy source: default" in result.stdout
    assert (output_dir / "skill-index.json").exists()
    assert (output_dir / "skill-remediation.md").exists()


def test_compare_range_requires_changed_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)

    result = _run_cli(repo_root, ["--compare-range", "HEAD~1..HEAD"])
    assert result.returncode == 2
    assert "--compare-range requires --changed-files" in result.stderr


def test_changed_files_mode_json_reports_scope_and_counts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    _create_valid_skill(repo_root, "skills/.curated/alpha", "alpha")
    _create_valid_skill(repo_root, "skills/.experimental/bravo", "bravo")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "baseline")

    (repo_root / "skills/.curated/alpha/SKILL.md").write_text(
        (
            "---\n"
            "name: alpha\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo Skill\n\n"
            "Use `references/guide.md`.\n"
            "Changed.\n"
        ),
        encoding="utf-8",
    )

    result = _run_cli(repo_root, ["--changed-files", "--json"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["scan"]["mode"] == "changed-files"
    assert payload["scan"]["compare_range"] is None
    assert payload["scan"]["changed_file_count"] == 1
    assert payload["scan"]["impacted_skill_count"] == 1
    assert payload["scan"]["scanned_skill_count"] == 1
    assert payload["scan"]["total_skill_count"] == 2
    assert payload["scan"]["changed_files"] == ["skills/.curated/alpha/SKILL.md"]
    assert payload["scan"]["policy_profile"] == {
        "source": "default",
        "active": False,
        "mode": "base-default",
        "override_counts": {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0},
    }
    assert [skill["path"] for skill in payload["skills"]] == ["skills/.curated/alpha"]


def test_compare_range_scopes_incremental_scan(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    _create_valid_skill(repo_root, "skills/.curated/alpha", "alpha")
    _create_valid_skill(repo_root, "skills/.curated/bravo", "bravo")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "baseline")

    (repo_root / "skills/.curated/alpha/SKILL.md").write_text(
        (
            "---\n"
            "name: alpha\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Alpha\n"
        ),
        encoding="utf-8",
    )
    _git(repo_root, "add", "skills/.curated/alpha/SKILL.md")
    _git(repo_root, "commit", "-m", "alpha change")

    (repo_root / "skills/.curated/bravo/SKILL.md").write_text(
        (
            "---\n"
            "name: bravo\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Bravo\n"
        ),
        encoding="utf-8",
    )
    _git(repo_root, "add", "skills/.curated/bravo/SKILL.md")
    _git(repo_root, "commit", "-m", "bravo change")

    result = _run_cli(
        repo_root,
        ["--changed-files", "--compare-range", "HEAD~1..HEAD", "--json"],
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["scan"]["compare_range"] == "HEAD~1..HEAD"
    assert payload["scan"]["changed_files"] == ["skills/.curated/bravo/SKILL.md"]
    assert [skill["path"] for skill in payload["skills"]] == ["skills/.curated/bravo"]


def test_invalid_compare_range_returns_runtime_error(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    _create_valid_skill(repo_root, "skills/.curated/alpha", "alpha")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "baseline")

    result = _run_cli(
        repo_root,
        ["--changed-files", "--compare-range", "HEAD~99..HEAD"],
    )
    assert result.returncode == 2
    assert "runtime-error:" in result.stderr


def test_invalid_override_file_returns_config_error(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_valid_repo(repo_root)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: [\n",
    )

    result = _run_cli(repo_root, [])
    assert result.returncode == 2
    assert "runtime-error:" in result.stderr
    assert "malformed YAML" in result.stderr


def test_override_applies_in_default_mode(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_mismatch_skill(repo_root, "skills/.experimental/demo", "demo")

    baseline = _run_cli(repo_root, [])
    assert baseline.returncode == 0
    assert "- warning: 1" in baseline.stdout
    assert "- invalid: 0" in baseline.stdout
    assert "Policy profile active: no" in baseline.stdout
    assert "Policy source: default" in baseline.stdout

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
    overridden = _run_cli(repo_root, [])
    assert overridden.returncode == 1
    assert "- warning: 0" in overridden.stdout
    assert "- invalid: 1" in overridden.stdout
    assert "Policy profile active: yes" in overridden.stdout
    assert "Policy source: .skill-audit-overrides.yaml" in overridden.stdout
    assert "Policy mode: severity-overrides" in overridden.stdout
    assert "Policy overrides: tier=0, rule=0, rule+tier=1, total=1" in overridden.stdout


def test_override_applies_in_changed_files_mode(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_git_repo(repo_root)
    _create_mismatch_skill(repo_root, "skills/.experimental/demo", "demo")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "baseline")

    (repo_root / "skills/.experimental/demo/SKILL.md").write_text(
        (
            "---\n"
            "name: demo\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo\n"
            "changed\n"
        ),
        encoding="utf-8",
    )

    baseline = _run_cli(repo_root, ["--changed-files"])
    assert baseline.returncode == 0

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

    overridden = _run_cli(repo_root, ["--changed-files"])
    assert overridden.returncode == 1


def test_json_output_includes_active_policy_profile_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_mismatch_skill(repo_root, "skills/.experimental/demo", "demo")
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  tier:\n"
            "    experimental: warning\n"
            "  rule:\n"
            "    META-001: invalid\n"
            "  rule_tier:\n"
            "    experimental:\n"
            "      META-110: invalid\n"
        ),
    )

    result = _run_cli(repo_root, ["--json"])
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["scan"]["policy_profile"] == {
        "source": ".skill-audit-overrides.yaml",
        "active": True,
        "mode": "severity-overrides",
        "override_counts": {"tier": 1, "rule": 1, "rule_tier": 1, "total": 3},
    }
