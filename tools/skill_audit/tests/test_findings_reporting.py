import pytest

from tools.skill_audit.findings import Finding
from tools.skill_audit.reporting import render_report, summarize_findings


def test_finding_rejects_invalid_severity() -> None:
    with pytest.raises(ValueError):
        Finding(
            id="META-999",
            severity="fatal",
            path="skills/.curated/example/SKILL.md",
            message="bad severity",
            suggested_fix="use a supported severity",
        )


def test_summarize_findings_counts_each_severity() -> None:
    findings = [
        Finding(
            id="META-000",
            severity="valid",
            path="skills/.curated/a/SKILL.md",
            message="ok",
            suggested_fix="none",
        ),
        Finding(
            id="META-010",
            severity="warning",
            path="skills/.curated/b/SKILL.md",
            message="warn",
            suggested_fix="fix soon",
        ),
        Finding(
            id="META-020",
            severity="invalid",
            path="skills/.curated/c/SKILL.md",
            message="invalid",
            suggested_fix="fix now",
        ),
    ]

    assert summarize_findings(findings) == {"valid": 1, "warning": 1, "invalid": 1}


def test_render_report_is_deterministic_and_includes_totals() -> None:
    findings = [
        Finding(
            id="META-020",
            severity="invalid",
            path="skills/.curated/zeta/SKILL.md",
            message="missing file",
            suggested_fix="create file",
        ),
        Finding(
            id="META-010",
            severity="warning",
            path="skills/.curated/alpha/SKILL.md",
            message="minor issue",
            suggested_fix="adjust content",
        ),
    ]

    report = render_report(
        findings,
        scanned_skill_count=2,
        scan_metadata={
            "mode": "changed-files",
            "changed_file_count": 1,
            "impacted_skill_count": 2,
            "scanned_skill_count": 2,
            "total_skill_count": 4,
            "policy_profile": {
                "source": ".skill-audit-overrides.yaml",
                "active": True,
                "mode": "severity-overrides",
                "override_counts": {"tier": 1, "rule": 0, "rule_tier": 1, "total": 2},
            },
            "cache": {
                "enabled": True,
                "mode": "read-write",
                "hits": 1,
                "misses": 1,
                "invalidations": 0,
                "errors": 0,
            },
        },
    )
    assert "Scan mode: changed-files" in report
    assert "Scanned skill directories: 2 of 4" in report
    assert "Policy profile active: yes" in report
    assert "Policy source: .skill-audit-overrides.yaml" in report
    assert "Policy mode: severity-overrides" in report
    assert "Policy overrides: tier=1, rule=0, rule+tier=1, total=2" in report
    assert "Cache enabled: yes" in report
    assert "Cache mode: read-write" in report
    assert "Cache stats: hits=1, misses=1, invalidations=0, errors=0" in report
    assert report.index("skills/.curated/alpha/SKILL.md") < report.index(
        "skills/.curated/zeta/SKILL.md"
    )
    assert "- valid: 0" in report
    assert "- warning: 1" in report
    assert "- invalid: 1" in report
