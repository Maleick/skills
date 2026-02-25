from pathlib import Path

import pytest

from tools.skill_audit.override_config import (
    OVERRIDE_CONFIG_FILENAME,
    OverrideConfigError,
    load_override_profile,
)


def _write_override(repo_root: Path, content: str) -> None:
    (repo_root / OVERRIDE_CONFIG_FILENAME).write_text(content, encoding="utf-8")


def test_missing_override_file_returns_none(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    assert load_override_profile(repo_root) is None


def test_valid_override_config_is_parsed(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
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
            "    curated:\n"
            "      META-110: valid\n"
        ),
    )

    profile = load_override_profile(repo_root)
    assert profile is not None
    assert profile.tier == {"experimental": "warning"}
    assert profile.rule == {"META-001": "invalid"}
    assert profile.rule_tier == {("curated", "META-110"): "valid"}


def test_malformed_yaml_raises_config_error(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: [\n",
    )

    with pytest.raises(OverrideConfigError, match="malformed YAML"):
        load_override_profile(repo_root)


def test_unknown_top_level_key_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides: {}\n"
            "extra: true\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="unknown top-level key"):
        load_override_profile(repo_root)


def test_missing_required_root_keys_fail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(repo_root, "version: 1\n")

    with pytest.raises(OverrideConfigError, match="missing required 'severity_overrides'"):
        load_override_profile(repo_root)


def test_unknown_override_section_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  nope: {}\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="unknown severity_overrides key"):
        load_override_profile(repo_root)


def test_unknown_tier_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  tier:\n"
            "    unknown: warning\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="unknown tier"):
        load_override_profile(repo_root)


def test_unknown_rule_id_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  rule:\n"
            "    META-999: warning\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="unknown rule ID"):
        load_override_profile(repo_root)


def test_invalid_severity_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides:\n"
            "  tier:\n"
            "    curated: critical\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="unsupported severity"):
        load_override_profile(repo_root)
