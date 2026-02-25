from pathlib import Path

from tools.skill_audit.findings import Finding
from tools.skill_audit.indexing import build_skill_index


def _create_skill(repo_root: Path, rel_path: str, name: str, description: str) -> Path:
    skill_dir = repo_root / rel_path
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    (skill_dir / "agents/openai.yaml").write_text(
        f"name: {name}\ndescription: {description}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_build_skill_index_core_contract_and_status(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    skill_a = _create_skill(repo_root, "skills/.curated/alpha", "alpha", "alpha desc")
    skill_b = _create_skill(repo_root, "skills/.experimental/bravo", "bravo", "bravo desc")

    findings = [
        Finding(
            id="META-001",
            severity="invalid",
            path="skills/.curated/alpha/SKILL.md",
            message="missing field",
            suggested_fix="add field",
        ),
        Finding(
            id="META-110",
            severity="warning",
            path="skills/.experimental/bravo/SKILL.md",
            message="mismatch",
            suggested_fix="align metadata",
        ),
        Finding(
            id="META-100",
            severity="valid",
            path="skills/.experimental/bravo/SKILL.md",
            message="ok",
            suggested_fix="none",
        ),
    ]

    payload = build_skill_index([skill_a, skill_b], findings, repo_root)
    assert payload["skill_count"] == 2
    assert payload["scan"]["mode"] == "full"
    assert payload["scan"]["scanned_skill_count"] == 2
    assert payload["scan"]["total_skill_count"] == 2
    assert payload["summary"]["global"]["finding_count"] == 3
    assert payload["summary"]["global"]["total_skill_count"] == 2
    assert payload["summary"]["severity_totals"] == {"valid": 1, "warning": 1, "invalid": 1}

    alpha = next(skill for skill in payload["skills"] if skill["path"] == "skills/.curated/alpha")
    bravo = next(
        skill for skill in payload["skills"] if skill["path"] == "skills/.experimental/bravo"
    )

    assert alpha["status"] == "invalid"
    assert alpha["finding_count"] == 1
    assert bravo["status"] == "warning"
    assert bravo["finding_count"] == 2
    assert set(alpha["metadata"]) >= {
        "name",
        "description",
        "has_skill_md",
        "has_openai_yaml",
    }


def test_build_skill_index_is_deterministic(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_a = _create_skill(repo_root, "skills/.system/one", "one", "desc one")
    skill_b = _create_skill(repo_root, "skills/.curated/two", "two", "desc two")

    findings = [
        Finding(
            id="META-010",
            severity="warning",
            path="skills/.curated/two/SKILL.md",
            message="warn",
            suggested_fix="fix",
        ),
        Finding(
            id="META-001",
            severity="invalid",
            path="skills/.system/one/SKILL.md",
            message="invalid",
            suggested_fix="fix",
        ),
    ]

    first = build_skill_index([skill_b, skill_a], findings, repo_root)
    second = build_skill_index([skill_a, skill_b], findings, repo_root)
    assert first == second


def test_build_skill_index_uses_provided_scan_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_a = _create_skill(repo_root, "skills/.system/one", "one", "desc one")

    findings: list[Finding] = []
    scan_metadata = {
        "mode": "changed-files",
        "compare_range": "HEAD~1..HEAD",
        "changed_files": ["skills/.system/one/SKILL.md"],
        "changed_file_count": 1,
        "impacted_skill_count": 1,
        "scanned_skill_count": 1,
        "total_skill_count": 3,
        "scanned_skills": ["skills/.system/one"],
    }

    payload = build_skill_index([skill_a], findings, repo_root, scan_metadata=scan_metadata)
    assert payload["scan"] == scan_metadata
    assert payload["summary"]["global"]["total_skill_count"] == 3
