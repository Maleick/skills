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
    scan = index_payload.get("scan", {})
    scan_mode = scan.get("mode", "full")
    compare_range = scan.get("compare_range")
    changed_file_count = scan.get("changed_file_count", 0)
    impacted_skill_count = scan.get("impacted_skill_count", summary["global"]["skill_count"])
    scanned_skill_count = scan.get("scanned_skill_count", summary["global"]["skill_count"])
    total_skill_count = scan.get("total_skill_count", summary["global"]["skill_count"])
    policy_profile = scan.get("policy_profile", {})
    policy_active = bool(policy_profile.get("active", False))
    policy_source = str(policy_profile.get("source", "default"))
    policy_mode = str(policy_profile.get("mode", "base-default"))
    raw_override_counts = policy_profile.get("override_counts", {})
    if isinstance(raw_override_counts, dict):
        policy_counts = {
            "tier": int(raw_override_counts.get("tier", 0)),
            "rule": int(raw_override_counts.get("rule", 0)),
            "rule_tier": int(raw_override_counts.get("rule_tier", 0)),
            "total": int(raw_override_counts.get("total", 0)),
        }
    else:
        policy_counts = {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0}
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
        "- Scan scope:",
        f"  - mode: {scan_mode}",
        (
            f"  - compare range: {compare_range}"
            if compare_range is not None
            else "  - compare range: working-tree (unstaged + staged + untracked)"
        ),
        f"  - changed files considered: {changed_file_count}",
        f"  - impacted skills: {impacted_skill_count}",
        f"  - scanned skills: {scanned_skill_count} of {total_skill_count}",
        "- Policy profile:",
        f"  - active: {'yes' if policy_active else 'no'}",
        f"  - source: {policy_source}",
        f"  - mode: {policy_mode}",
        (
            "  - overrides: "
            f"tier={policy_counts['tier']}, "
            f"rule={policy_counts['rule']}, "
            f"rule+tier={policy_counts['rule_tier']}, "
            f"total={policy_counts['total']}"
        ),
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
