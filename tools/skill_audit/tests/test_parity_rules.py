from pathlib import Path

from tools.skill_audit.rules.parity import validate_metadata_parity


def _fixtures_root() -> Path:
    return Path(__file__).parent / "fixtures" / "parity"


def test_matching_metadata_returns_valid_finding() -> None:
    root = _fixtures_root()
    findings = validate_metadata_parity(root / "match", root)
    assert len(findings) == 1
    assert findings[0].id == "META-100"
    assert findings[0].severity == "valid"


def test_mismatched_metadata_returns_field_findings() -> None:
    root = _fixtures_root()
    findings = validate_metadata_parity(root / "mismatch", root)
    assert len(findings) == 2
    assert all(finding.id == "META-110" for finding in findings)
    assert all(finding.severity == "invalid" for finding in findings)


def test_missing_openai_counterpart_returns_finding() -> None:
    root = _fixtures_root()
    findings = validate_metadata_parity(root / "missing-openai", root)
    assert len(findings) == 1
    assert findings[0].id == "META-101"


def test_missing_skill_counterpart_returns_finding() -> None:
    root = _fixtures_root()
    findings = validate_metadata_parity(root / "missing-skill", root)
    assert len(findings) == 1
    assert findings[0].id == "META-102"


def test_invalid_openai_yaml_returns_finding() -> None:
    root = _fixtures_root()
    findings = validate_metadata_parity(root / "invalid-openai", root)
    assert len(findings) == 1
    assert findings[0].id == "META-103"
