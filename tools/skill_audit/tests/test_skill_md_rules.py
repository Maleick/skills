from pathlib import Path

from tools.skill_audit.rules.skill_md import validate_skill_md


def _fixtures_root() -> Path:
    return Path(__file__).parent / "fixtures"


def test_valid_skill_md_fixture_returns_valid_finding() -> None:
    fixtures_root = _fixtures_root()
    skill_dir = fixtures_root / "skills_valid/sample-skill"

    findings = validate_skill_md(skill_dir, fixtures_root)
    assert len(findings) == 1
    assert findings[0].id == "META-000"
    assert findings[0].severity == "valid"


def test_missing_skill_md_file_returns_invalid_finding() -> None:
    fixtures_root = _fixtures_root()
    skill_dir = fixtures_root / "skills_invalid/missing-file"

    findings = validate_skill_md(skill_dir, fixtures_root)
    assert len(findings) == 1
    assert findings[0].id == "META-001"
    assert findings[0].severity == "invalid"
    assert "Create SKILL.md" in findings[0].suggested_fix


def test_missing_frontmatter_returns_invalid_finding() -> None:
    fixtures_root = _fixtures_root()
    skill_dir = fixtures_root / "skills_invalid/missing-frontmatter"

    findings = validate_skill_md(skill_dir, fixtures_root)
    assert len(findings) == 1
    assert findings[0].id == "META-002"
    assert findings[0].severity == "invalid"


def test_missing_required_frontmatter_keys_returns_invalid(tmp_path: Path) -> None:
    repo_root = tmp_path
    skill_dir = repo_root / "sample-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: sample\n---\nBody", encoding="utf-8")

    findings = validate_skill_md(skill_dir, repo_root)
    assert len(findings) == 1
    assert findings[0].id == "META-005"
    assert "description" in findings[0].message
