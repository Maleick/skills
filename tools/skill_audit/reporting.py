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


def _policy_profile_from_scan_metadata(
    scan_metadata: dict[str, object] | None,
) -> tuple[bool, str, str, dict[str, int]]:
    active = False
    source = "default"
    mode = "base-default"
    counts = {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0}

    if scan_metadata is None:
        return active, source, mode, counts

    raw_profile = scan_metadata.get("policy_profile")
    if not isinstance(raw_profile, dict):
        return active, source, mode, counts

    active = bool(raw_profile.get("active", False))
    source = str(raw_profile.get("source", source))
    mode = str(raw_profile.get("mode", mode))

    raw_counts = raw_profile.get("override_counts")
    if isinstance(raw_counts, dict):
        counts = {
            "tier": int(raw_counts.get("tier", 0)),
            "rule": int(raw_counts.get("rule", 0)),
            "rule_tier": int(raw_counts.get("rule_tier", 0)),
            "total": int(raw_counts.get("total", 0)),
        }

    return active, source, mode, counts


def render_report(
    findings: Iterable[Finding],
    scanned_skill_count: int,
    scan_metadata: dict[str, object] | None = None,
) -> str:
    """Render a human-readable report for CLI output."""
    ordered = sort_findings(findings)
    totals = summarize_findings(ordered)

    mode = "full"
    compare_range = None
    changed_file_count = 0
    impacted_skill_count = scanned_skill_count
    total_skill_count = scanned_skill_count
    policy_active = False
    policy_source = "default"
    policy_mode = "base-default"
    policy_counts = {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0}
    if scan_metadata is not None:
        mode = str(scan_metadata.get("mode", mode))
        compare_range = scan_metadata.get("compare_range")
        changed_file_count = int(scan_metadata.get("changed_file_count", 0))
        impacted_skill_count = int(
            scan_metadata.get("impacted_skill_count", impacted_skill_count)
        )
        total_skill_count = int(scan_metadata.get("total_skill_count", total_skill_count))
    (
        policy_active,
        policy_source,
        policy_mode,
        policy_counts,
    ) = _policy_profile_from_scan_metadata(scan_metadata)

    lines = [
        "Skill Audit Report",
        "",
        f"Scan mode: {mode}",
        (
            f"Compare range: {compare_range}"
            if compare_range is not None
            else "Compare range: working-tree (unstaged + staged + untracked)"
        ),
        f"Changed files considered: {changed_file_count}",
        f"Impacted skill directories: {impacted_skill_count}",
        f"Scanned skill directories: {scanned_skill_count} of {total_skill_count}",
        f"Policy profile active: {'yes' if policy_active else 'no'}",
        f"Policy source: {policy_source}",
        f"Policy mode: {policy_mode}",
        (
            "Policy overrides: "
            f"tier={policy_counts['tier']}, "
            f"rule={policy_counts['rule']}, "
            f"rule+tier={policy_counts['rule_tier']}, "
            f"total={policy_counts['total']}"
        ),
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
