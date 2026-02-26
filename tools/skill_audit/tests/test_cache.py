from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.skill_audit.cache import (
    CACHE_SCHEMA_VERSION,
    SkillAuditCache,
    build_policy_profile_signature,
    build_rules_signature,
)
from tools.skill_audit.findings import Finding
from tools.skill_audit.override_config import OverrideProfile
from tools.skill_audit.scanner import skill_content_fingerprint, skill_key_for_dir


def _create_skill(repo_root: Path, rel_path: str) -> Path:
    skill_dir = repo_root / rel_path
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: demo\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo\n\n"
            "Use `references/guide.md`.\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        "name: demo\ndescription: Demo skill fixture.\n",
        encoding="utf-8",
    )
    (skill_dir / "references/guide.md").write_text("# Guide\n", encoding="utf-8")
    return skill_dir


def _finding(skill_path: str, *, severity: str = "valid", finding_id: str = "META-000") -> Finding:
    return Finding(
        id=finding_id,
        severity=severity,
        path=f"{skill_path}/SKILL.md",
        message="demo finding",
        suggested_fix="none",
    )


def test_policy_profile_signature_is_deterministic() -> None:
    profile = OverrideProfile(
        tier={"experimental": "warning"},
        rule={"META-001": "invalid"},
        rule_tier={("curated", "META-110"): "warning"},
    )

    first = build_policy_profile_signature(profile)
    second = build_policy_profile_signature(profile)
    assert first == second
    assert build_policy_profile_signature(None) == "default"


def test_rules_signature_is_deterministic() -> None:
    first = build_rules_signature()
    second = build_rules_signature()
    assert first == second


def test_skill_fingerprint_is_deterministic_for_same_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")

    first = skill_content_fingerprint(skill_dir, repo_root)
    second = skill_content_fingerprint(skill_dir, repo_root)
    assert first == second


def test_skill_fingerprint_changes_when_file_content_changes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    baseline = skill_content_fingerprint(skill_dir, repo_root)

    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: demo\n"
            "description: Demo skill fixture.\n"
            "---\n\n"
            "# Demo\n\n"
            "Use `references/guide.md`.\n"
            "changed\n"
        ),
        encoding="utf-8",
    )
    changed = skill_content_fingerprint(skill_dir, repo_root)
    assert baseline != changed


def test_skill_fingerprint_changes_when_file_is_added(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    baseline = skill_content_fingerprint(skill_dir, repo_root)

    (skill_dir / "assets").mkdir(parents=True, exist_ok=True)
    (skill_dir / "assets/logo.txt").write_text("logo\n", encoding="utf-8")
    changed = skill_content_fingerprint(skill_dir, repo_root)
    assert baseline != changed


def test_skill_fingerprint_missing_directory_raises(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    missing = repo_root / "skills/.curated/missing"
    with pytest.raises(RuntimeError):
        skill_content_fingerprint(missing, repo_root)


def test_cache_round_trip_lookup_hit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    skill_key = skill_key_for_dir(skill_dir, repo_root)
    fingerprint = skill_content_fingerprint(skill_dir, repo_root)

    cache = SkillAuditCache(repo_root=repo_root)
    findings = [_finding("skills/.curated/demo")]
    cache.store(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="default",
        rules_signature="rules-v1",
        findings=findings,
    )
    cache.flush()

    reloaded = SkillAuditCache(repo_root=repo_root)
    cached = reloaded.lookup(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="default",
        rules_signature="rules-v1",
    )
    assert cached is not None
    assert cached == findings
    assert reloaded.metadata()["hits"] == 1
    assert reloaded.metadata()["misses"] == 0


def test_cache_miss_when_entry_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _create_skill(repo_root, "skills/.curated/demo")
    cache = SkillAuditCache(repo_root=repo_root)

    result = cache.lookup(
        skill_key="skills/.curated/demo",
        fingerprint="a",
        policy_signature="default",
        rules_signature="rules-v1",
    )
    assert result is None
    assert cache.metadata()["hits"] == 0
    assert cache.metadata()["misses"] == 1


def test_cache_invalidates_on_fingerprint_change(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    skill_key = skill_key_for_dir(skill_dir, repo_root)
    fingerprint = skill_content_fingerprint(skill_dir, repo_root)

    cache = SkillAuditCache(repo_root=repo_root)
    cache.store(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="default",
        rules_signature="rules-v1",
        findings=[_finding("skills/.curated/demo")],
    )
    cache.flush()

    reloaded = SkillAuditCache(repo_root=repo_root)
    result = reloaded.lookup(
        skill_key=skill_key,
        fingerprint="other-fingerprint",
        policy_signature="default",
        rules_signature="rules-v1",
    )
    assert result is None
    assert reloaded.metadata()["invalidations"] == 1
    assert reloaded.metadata()["misses"] == 1


def test_cache_invalidates_on_policy_signature_change(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    skill_key = skill_key_for_dir(skill_dir, repo_root)
    fingerprint = skill_content_fingerprint(skill_dir, repo_root)

    cache = SkillAuditCache(repo_root=repo_root)
    cache.store(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="profile-a",
        rules_signature="rules-v1",
        findings=[_finding("skills/.curated/demo")],
    )
    cache.flush()

    reloaded = SkillAuditCache(repo_root=repo_root)
    result = reloaded.lookup(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="profile-b",
        rules_signature="rules-v1",
    )
    assert result is None
    assert reloaded.metadata()["invalidations"] == 1
    assert reloaded.metadata()["misses"] == 1


def test_cache_invalidates_on_rules_signature_change(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = _create_skill(repo_root, "skills/.curated/demo")
    skill_key = skill_key_for_dir(skill_dir, repo_root)
    fingerprint = skill_content_fingerprint(skill_dir, repo_root)

    cache = SkillAuditCache(repo_root=repo_root)
    cache.store(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="default",
        rules_signature="rules-v1",
        findings=[_finding("skills/.curated/demo")],
    )
    cache.flush()

    reloaded = SkillAuditCache(repo_root=repo_root)
    result = reloaded.lookup(
        skill_key=skill_key,
        fingerprint=fingerprint,
        policy_signature="default",
        rules_signature="rules-v2",
    )
    assert result is None
    assert reloaded.metadata()["invalidations"] == 1
    assert reloaded.metadata()["misses"] == 1


def test_cache_corruption_falls_back_and_refreshes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cache_path = repo_root / ".planning/cache/skill-audit-cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("{not-json", encoding="utf-8")

    cache = SkillAuditCache(repo_root=repo_root)
    assert cache.metadata()["errors"] == 1
    assert cache.warnings

    cache.store(
        skill_key="skills/.curated/demo",
        fingerprint="fp",
        policy_signature="default",
        rules_signature="rules-v1",
        findings=[_finding("skills/.curated/demo")],
    )
    cache.flush()

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == CACHE_SCHEMA_VERSION
    assert "skills/.curated/demo" in payload["entries"]


def test_cache_invalid_entry_payload_is_invalidated(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cache_path = repo_root / ".planning/cache/skill-audit-cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": CACHE_SCHEMA_VERSION,
                "entries": {
                    "skills/.curated/demo": {
                        "fingerprint": "fp",
                        "policy_signature": "default",
                        "rules_signature": "rules-v1",
                        "findings": [{"id": "META-000"}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    cache = SkillAuditCache(repo_root=repo_root)
    result = cache.lookup(
        skill_key="skills/.curated/demo",
        fingerprint="fp",
        policy_signature="default",
        rules_signature="rules-v1",
    )
    assert result is None
    assert cache.metadata()["invalidations"] == 1
    assert cache.metadata()["errors"] == 1


def test_disabled_cache_mode_never_writes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cache = SkillAuditCache(repo_root=repo_root, enabled=False)
    cache.store(
        skill_key="skills/.curated/demo",
        fingerprint="fp",
        policy_signature="default",
        rules_signature="rules-v1",
        findings=[_finding("skills/.curated/demo")],
    )
    cache.flush()

    assert cache.metadata() == {
        "enabled": False,
        "mode": "disabled",
        "hits": 0,
        "misses": 0,
        "invalidations": 0,
        "errors": 0,
    }
    assert not (repo_root / ".planning/cache/skill-audit-cache.json").exists()
