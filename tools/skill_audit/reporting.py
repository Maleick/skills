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
) -> tuple[bool, str, str, str, str, dict[str, int]]:
    active = False
    source = "default"
    mode = "base-default"
    profile_name = "default"
    selection = "base-default"
    counts = {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0}

    if scan_metadata is None:
        return active, source, mode, profile_name, selection, counts

    raw_profile = scan_metadata.get("policy_profile")
    if not isinstance(raw_profile, dict):
        return active, source, mode, profile_name, selection, counts

    active = bool(raw_profile.get("active", False))
    source = str(raw_profile.get("source", source))
    mode = str(raw_profile.get("mode", mode))
    profile_name = str(raw_profile.get("profile_name", profile_name))
    selection = str(raw_profile.get("selection", selection))

    raw_counts = raw_profile.get("override_counts")
    if isinstance(raw_counts, dict):
        counts = {
            "tier": int(raw_counts.get("tier", 0)),
            "rule": int(raw_counts.get("rule", 0)),
            "rule_tier": int(raw_counts.get("rule_tier", 0)),
            "total": int(raw_counts.get("total", 0)),
        }

    return active, source, mode, profile_name, selection, counts


def _cache_profile_from_scan_metadata(
    scan_metadata: dict[str, object] | None,
) -> tuple[bool, str, dict[str, int]]:
    enabled = False
    mode = "disabled"
    stats = {"hits": 0, "misses": 0, "invalidations": 0, "errors": 0}

    if scan_metadata is None:
        return enabled, mode, stats

    raw_cache = scan_metadata.get("cache")
    if not isinstance(raw_cache, dict):
        return enabled, mode, stats

    enabled = bool(raw_cache.get("enabled", False))
    mode = str(raw_cache.get("mode", mode))
    stats = {
        "hits": int(raw_cache.get("hits", 0)),
        "misses": int(raw_cache.get("misses", 0)),
        "invalidations": int(raw_cache.get("invalidations", 0)),
        "errors": int(raw_cache.get("errors", 0)),
    }
    return enabled, mode, stats


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
    policy_profile_name = "default"
    policy_selection = "base-default"
    policy_counts = {"tier": 0, "rule": 0, "rule_tier": 0, "total": 0}
    cache_enabled = False
    cache_mode = "disabled"
    cache_stats = {"hits": 0, "misses": 0, "invalidations": 0, "errors": 0}
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
        policy_profile_name,
        policy_selection,
        policy_counts,
    ) = _policy_profile_from_scan_metadata(scan_metadata)
    cache_enabled, cache_mode, cache_stats = _cache_profile_from_scan_metadata(scan_metadata)

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
        f"Policy profile: {policy_profile_name}",
        f"Policy selection: {policy_selection}",
        (
            "Policy overrides: "
            f"tier={policy_counts['tier']}, "
            f"rule={policy_counts['rule']}, "
            f"rule+tier={policy_counts['rule_tier']}, "
            f"total={policy_counts['total']}"
        ),
        f"Cache enabled: {'yes' if cache_enabled else 'no'}",
        f"Cache mode: {cache_mode}",
        (
            "Cache stats: "
            f"hits={cache_stats['hits']}, "
            f"misses={cache_stats['misses']}, "
            f"invalidations={cache_stats['invalidations']}, "
            f"errors={cache_stats['errors']}"
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
