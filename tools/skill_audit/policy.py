"""Tier-aware severity policy helpers."""

from __future__ import annotations

from collections.abc import Iterable

from .findings import Finding

TIER_SYSTEM = "system"
TIER_CURATED = "curated"
TIER_EXPERIMENTAL = "experimental"
TIER_UNKNOWN = "unknown"

WARNING_BIASED_EXPERIMENTAL_RULE_IDS: frozenset[str] = frozenset(
    {
        "META-110",  # field parity mismatch
        "META-201",  # missing local reference
    }
)


def tier_from_path(path: str) -> str:
    """Infer skill tier from a repository-relative finding path."""
    normalized = path.replace("\\", "/")
    if normalized.startswith("skills/.system/"):
        return TIER_SYSTEM
    if normalized.startswith("skills/.curated/"):
        return TIER_CURATED
    if normalized.startswith("skills/.experimental/"):
        return TIER_EXPERIMENTAL
    return TIER_UNKNOWN


def translate_finding_severity(finding: Finding) -> Finding:
    """Apply tier policy to one finding."""
    if finding.severity != "invalid":
        return finding

    tier = tier_from_path(finding.path)
    if (
        tier == TIER_EXPERIMENTAL
        and finding.id in WARNING_BIASED_EXPERIMENTAL_RULE_IDS
    ):
        return Finding(
            id=finding.id,
            severity="warning",
            path=finding.path,
            message=finding.message,
            suggested_fix=finding.suggested_fix,
        )
    return finding


def apply_tier_policy(findings: Iterable[Finding]) -> list[Finding]:
    """Return findings after tier policy translation."""
    return [translate_finding_severity(finding) for finding in findings]
