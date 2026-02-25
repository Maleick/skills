"""Helpers for deterministic findings presentation."""

from __future__ import annotations

from collections.abc import Iterable

from .findings import ALLOWED_SEVERITIES, Finding


def sort_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Return findings sorted by path and rule ID for stable output."""
    return sorted(findings, key=lambda finding: finding.as_sort_key())


def summarize_findings(findings: Iterable[Finding]) -> dict[str, int]:
    """Count findings by severity."""
    counts = {severity: 0 for severity in ALLOWED_SEVERITIES}
    for finding in findings:
        counts[finding.severity] += 1
    return counts


def render_report(findings: Iterable[Finding], scanned_skill_count: int) -> str:
    """Render a human-readable report for CLI output."""
    ordered = sort_findings(findings)
    totals = summarize_findings(ordered)

    lines = [
        "Skill Audit Report",
        "",
        f"Scanned skill directories: {scanned_skill_count}",
        "",
    ]

    if ordered:
        for finding in ordered:
            lines.append(
                f"- [{finding.severity}] {finding.id} `{finding.path}`: "
                f"{finding.message} | Fix: {finding.suggested_fix}"
            )
    else:
        lines.append("- No findings generated.")

    lines.extend(
        [
            "",
            "Severity totals:",
            f"- valid: {totals['valid']}",
            f"- warning: {totals['warning']}",
            f"- invalid: {totals['invalid']}",
        ]
    )
    return "\n".join(lines)
