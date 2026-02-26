from tools.skill_audit.markdown_report import render_markdown_report


def test_markdown_report_grouping_detail_and_valid_summary_only() -> None:
    payload = {
        "skill_count": 2,
        "summary": {
            "global": {"skill_count": 2, "finding_count": 4},
            "severity_totals": {"valid": 1, "warning": 1, "invalid": 2},
            "tier_totals": {
                "system": {
                    "skill_count": 1,
                    "finding_count": 3,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 1},
                    "severity_totals": {"valid": 1, "warning": 0, "invalid": 2},
                },
                "curated": {
                    "skill_count": 1,
                    "finding_count": 1,
                    "status_counts": {"valid": 0, "warning": 1, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 1, "invalid": 0},
                },
                "experimental": {
                    "skill_count": 0,
                    "finding_count": 0,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 0},
                },
                "unknown": {
                    "skill_count": 0,
                    "finding_count": 0,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 0},
                },
            },
        },
        "skills": [
            {
                "path": "skills/.curated/beta",
                "tier": "curated",
                "status": "warning",
                "finding_count": 1,
                "severity_counts": {"valid": 0, "warning": 1, "invalid": 0},
                "metadata": {},
                "findings": [
                    {
                        "id": "META-110",
                        "severity": "warning",
                        "path": "skills/.curated/beta/SKILL.md",
                        "message": "mismatch",
                        "suggested_fix": "align values",
                    }
                ],
            },
            {
                "path": "skills/.system/alpha",
                "tier": "system",
                "status": "invalid",
                "finding_count": 3,
                "severity_counts": {"valid": 1, "warning": 0, "invalid": 2},
                "metadata": {},
                "findings": [
                    {
                        "id": "META-001",
                        "severity": "invalid",
                        "path": "skills/.system/alpha/SKILL.md",
                        "message": "missing file",
                        "suggested_fix": "add file",
                    },
                    {
                        "id": "META-201",
                        "severity": "invalid",
                        "path": "skills/.system/alpha/references/missing.md",
                        "message": "broken ref",
                        "suggested_fix": "fix path",
                    },
                    {
                        "id": "META-100",
                        "severity": "valid",
                        "path": "skills/.system/alpha/SKILL.md",
                        "message": "ok",
                        "suggested_fix": "none",
                    },
                ],
            },
        ],
    }

    report = render_markdown_report(payload)
    assert "## Invalid Findings" in report
    assert "## Warning Findings" in report
    assert "## Valid Findings" not in report
    assert "- Scan scope:" in report
    assert "  - mode: full" in report
    assert "  - scanned skills: 2 of 2" in report
    assert "- Policy profile:" in report
    assert "  - active: no" in report
    assert "  - source: default" in report
    assert "  - mode: base-default" in report
    assert "  - overrides: tier=0, rule=0, rule+tier=0, total=0" in report
    assert "  - valid: 1" in report
    assert "`META-001` `skills/.system/alpha/SKILL.md`" in report
    assert "Fix: add file" in report
    assert report.index("## Invalid Findings") < report.index("## Warning Findings")
    assert report.index("skills/.system/alpha") < report.index("skills/.curated/beta")
