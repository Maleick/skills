from pathlib import Path

from tools.skill_audit.rules.references import validate_local_references


def _fixtures_root() -> Path:
    return Path(__file__).parent / "fixtures" / "references"


def test_valid_local_references_return_valid_finding() -> None:
    root = _fixtures_root()
    findings = validate_local_references(root / "valid", root)
    assert len(findings) == 1
    assert findings[0].id == "META-200"
    assert findings[0].severity == "valid"


def test_broken_local_references_are_reported() -> None:
    root = _fixtures_root()
    findings = validate_local_references(root / "invalid-local", root)
    assert len(findings) == 3
    assert all(finding.id == "META-201" for finding in findings)
    assert all(finding.severity == "invalid" for finding in findings)


def test_urls_are_ignored() -> None:
    root = _fixtures_root()
    findings = validate_local_references(root / "url-only", root)
    assert findings == []
