"""Markdown remediation report rendering from index payload."""

from __future__ import annotations

from typing import Any

SEVERITY_SECTIONS: tuple[tuple[str, str], ...] = (
    ("invalid", "Invalid Findings"),
    ("warning", "Warning Findings"),
)


def render_markdown_report(index_payload: dict[str, Any]) -> str:
    """Render deterministic markdown remediation report."""
    summary = index_payload["summary"]
    lines: list[str] = [
        "# Skill Audit Remediation Report",
        "",
        "## Summary",
        f"- Skills scanned: {summary['global']['skill_count']}",
        f"- Findings: {summary['global']['finding_count']}",
        "- Severity totals:",
        f"  - invalid: {summary['severity_totals']['invalid']}",
        f"  - warning: {summary['severity_totals']['warning']}",
        f"  - valid: {summary['severity_totals']['valid']}",
        "- Tier totals:",
    ]

    for tier in ("system", "curated", "experimental", "unknown"):
        tier_total = summary["tier_totals"][tier]
        if tier_total["skill_count"] == 0 and tier_total["finding_count"] == 0:
            continue
        lines.append(
            f"  - {tier}: {tier_total['skill_count']} skills, "
            f"{tier_total['finding_count']} findings"
        )

    skills = index_payload["skills"]
    for severity, section_title in SEVERITY_SECTIONS:
        lines.extend(["", f"## {section_title}"])

        grouped: list[tuple[str, list[dict[str, str]]]] = []
        for skill in skills:
            matching = [finding for finding in skill["findings"] if finding["severity"] == severity]
            if matching:
                grouped.append((skill["path"], matching))

        if not grouped:
            lines.append("- None")
            continue

        for skill_path, issues in grouped:
            lines.extend(["", f"### `{skill_path}`"])
            for issue in issues:
                lines.append(
                    f"- `{issue['id']}` `{issue['path']}`: {issue['message']}"
                )
                lines.append(f"  - Fix: {issue['suggested_fix']}")

    return "\n".join(lines)
