from __future__ import annotations

from pathlib import Path

from tools.skill_audit.autofix import (
    build_autofix_suggestions,
    render_autofix_markdown,
    render_autofix_text,
    summarize_autofix_suggestions,
)
from tools.skill_audit.findings import Finding


def _finding(
    *, finding_id: str, severity: str, path: str, message: str = "msg"
) -> Finding:
    return Finding(
        id=finding_id,
        severity=severity,
        path=path,
        message=message,
        suggested_fix="fix",
    )


def test_autofix_suggestions_are_deterministic_and_skip_valid_findings() -> None:
    findings = [
        _finding(
            finding_id="META-110",
            severity="invalid",
            path="skills/.curated/zeta/SKILL.md",
        ),
        _finding(
            finding_id="META-001",
            severity="invalid",
            path="skills/.curated/alpha/SKILL.md",
        ),
        _finding(
            finding_id="META-000",
            severity="valid",
            path="skills/.curated/alpha/SKILL.md",
        ),
    ]

    first = build_autofix_suggestions(findings)
    second = build_autofix_suggestions(findings)

    assert [item.rule_id for item in first] == ["META-001", "META-110"]
    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]


def test_autofix_marks_unknown_rule_as_unsupported() -> None:
    findings = [
        _finding(
            finding_id="META-999",
            severity="warning",
            path="skills/.experimental/demo/SKILL.md",
        )
    ]

    suggestions = build_autofix_suggestions(findings)
    assert len(suggestions) == 1
    assert suggestions[0].supported is False
    assert "No deterministic dry-run suggestion" in suggestions[0].reason


def test_autofix_renderers_include_summary_counts() -> None:
    findings = [
        _finding(
            finding_id="META-001",
            severity="invalid",
            path="skills/.curated/demo/SKILL.md",
        ),
        _finding(
            finding_id="META-999",
            severity="warning",
            path="skills/.curated/demo/agents/openai.yaml",
        ),
    ]

    suggestions = build_autofix_suggestions(findings)
    summary = summarize_autofix_suggestions(suggestions)
    assert summary == {
        "total": 2,
        "supported": 1,
        "unsupported": 1,
        "severity_totals": {"warning": 1, "invalid": 1},
    }

    text = render_autofix_text(suggestions)
    assert "Autofix Suggestions (dry-run)" in text
    assert "supported: 1" in text
    assert "unsupported: 1" in text

    markdown = render_autofix_markdown(suggestions)
    assert "# Skill Audit Autofix Suggestions (Dry-Run)" in markdown
    assert "- Supported: 1" in markdown
    assert "- Unsupported: 1" in markdown


def test_autofix_generation_does_not_mutate_files(tmp_path: Path) -> None:
    skill_file = tmp_path / "skills/.curated/demo/SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("original\n", encoding="utf-8")

    findings = [
        _finding(
            finding_id="META-001",
            severity="invalid",
            path="skills/.curated/demo/SKILL.md",
        )
    ]

    before = skill_file.read_text(encoding="utf-8")
    _ = build_autofix_suggestions(findings)
    after = skill_file.read_text(encoding="utf-8")

    assert before == after
