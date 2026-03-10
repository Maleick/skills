from pathlib import Path

import pytest

from tools.skill_audit.override_config import (
    OVERRIDE_CONFIG_FILENAME,
    OverrideConfigError,
    build_policy_profile_metadata,
    load_override_profile,
    load_override_profile_selection,
)


def _write_override(repo_root: Path, content: str) -> None:
    (repo_root / OVERRIDE_CONFIG_FILENAME).write_text(content, encoding="utf-8")


def test_missing_override_file_returns_none(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    assert load_override_profile(repo_root) is None
    assert load_override_profile_selection(repo_root) is None


def test_missing_override_file_with_requested_profile_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    with pytest.raises(OverrideConfigError, match="requested profile"):
        load_override_profile_selection(repo_root, profile_name="strict")


def test_valid_legacy_override_config_is_parsed(tmp_path: Path) -> None:
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

    resolved = load_override_profile_selection(repo_root)
    assert resolved is not None
    assert resolved.profile_name == "default"
    assert resolved.selection == "legacy-default"
    assert resolved.available_profiles == ("default",)
    assert resolved.profile.tier == {"experimental": "warning"}
    assert resolved.profile.rule == {"META-001": "invalid"}
    assert resolved.profile.rule_tier == {("curated", "META-110"): "valid"}


def test_legacy_default_profile_can_be_explicitly_selected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: {}\n",
    )

    resolved = load_override_profile_selection(repo_root, profile_name="default")
    assert resolved is not None
    assert resolved.profile_name == "default"
    assert resolved.selection == "explicit"


def test_legacy_unknown_profile_selection_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: {}\n",
    )

    with pytest.raises(OverrideConfigError, match="requested profile"):
        load_override_profile_selection(repo_root, profile_name="strict")


def test_valid_named_profiles_with_default_resolution(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "default_profile: balanced\n"
            "profiles:\n"
            "  strict:\n"
            "    rule:\n"
            "      META-110: invalid\n"
            "  balanced:\n"
            "    rule:\n"
            "      META-110: warning\n"
        ),
    )

    resolved = load_override_profile_selection(repo_root)
    assert resolved is not None
    assert resolved.profile_name == "balanced"
    assert resolved.selection == "config-default"
    assert resolved.available_profiles == ("balanced", "strict")
    assert resolved.profile.rule == {"META-110": "warning"}


def test_named_profiles_explicit_selection(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "default_profile: balanced\n"
            "profiles:\n"
            "  strict:\n"
            "    rule:\n"
            "      META-110: invalid\n"
            "  balanced:\n"
            "    rule:\n"
            "      META-110: warning\n"
        ),
    )

    resolved = load_override_profile_selection(repo_root, profile_name="strict")
    assert resolved is not None
    assert resolved.profile_name == "strict"
    assert resolved.selection == "explicit"
    assert resolved.profile.rule == {"META-110": "invalid"}


def test_named_profiles_single_profile_without_default_is_allowed(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "profiles:\n"
            "  strict:\n"
            "    tier:\n"
            "      experimental: invalid\n"
        ),
    )

    resolved = load_override_profile_selection(repo_root)
    assert resolved is not None
    assert resolved.profile_name == "strict"
    assert resolved.selection == "single-profile"


def test_named_profiles_multiple_without_default_or_selector_fail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "profiles:\n"
            "  strict: {}\n"
            "  balanced: {}\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="multiple profiles"):
        load_override_profile_selection(repo_root)


def test_default_profile_must_exist_in_profiles(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "default_profile: strict\n"
            "profiles:\n"
            "  balanced: {}\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="default_profile"):
        load_override_profile_selection(repo_root)


def test_named_profile_request_must_exist(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "profiles:\n"
            "  strict: {}\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="requested profile"):
        load_override_profile_selection(repo_root, profile_name="balanced")


def test_mixed_legacy_and_named_modes_fail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "severity_overrides: {}\n"
            "profiles:\n"
            "  strict: {}\n"
        ),
    )

    with pytest.raises(OverrideConfigError, match="cannot both be defined"):
        load_override_profile_selection(repo_root)


def test_malformed_yaml_raises_config_error(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: [\n",
    )

    with pytest.raises(OverrideConfigError, match="malformed YAML"):
        load_override_profile_selection(repo_root)


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
        load_override_profile_selection(repo_root)


def test_missing_required_mode_keys_fail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(repo_root, "version: 1\n")

    with pytest.raises(OverrideConfigError, match="missing required 'severity_overrides'"):
        load_override_profile_selection(repo_root)


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
        load_override_profile_selection(repo_root)


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
        load_override_profile_selection(repo_root)


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
        load_override_profile_selection(repo_root)


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
        load_override_profile_selection(repo_root)


def test_load_override_profile_keeps_backward_compatible_signature(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        "version: 1\nseverity_overrides: {}\n",
    )

    profile = load_override_profile(repo_root)
    assert profile is not None
    assert profile.tier == {}
    assert profile.rule == {}
    assert profile.rule_tier == {}


def test_policy_metadata_includes_profile_identity_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_override(
        repo_root,
        (
            "version: 1\n"
            "default_profile: strict\n"
            "profiles:\n"
            "  strict:\n"
            "    rule:\n"
            "      META-110: invalid\n"
        ),
    )

    resolved = load_override_profile_selection(repo_root)
    assert resolved is not None
    metadata = build_policy_profile_metadata(resolved)
    assert metadata["active"] is True
    assert metadata["source"] == OVERRIDE_CONFIG_FILENAME
    assert metadata["profile_name"] == "strict"
    assert metadata["selection"] == "config-default"
    assert metadata["available_profiles"] == ["strict"]
