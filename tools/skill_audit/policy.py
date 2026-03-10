"""Tier-aware severity policy helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .findings import Finding

if TYPE_CHECKING:
    from .override_config import OverrideProfile

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


def _with_severity(finding: Finding, severity: str) -> Finding:
    if finding.severity == severity:
        return finding
    return Finding(
        id=finding.id,
        severity=severity,
        path=finding.path,
        message=finding.message,
        suggested_fix=finding.suggested_fix,
    )


def _apply_base_default(finding: Finding) -> Finding:
    """Apply default built-in policy without repository overrides."""
    if finding.severity != "invalid":
        return finding

    tier = tier_from_path(finding.path)
    if (
        tier == TIER_EXPERIMENTAL
        and finding.id in WARNING_BIASED_EXPERIMENTAL_RULE_IDS
    ):
        return _with_severity(finding, "warning")
    return finding


def _resolve_override_severity(
    finding: Finding, override_profile: OverrideProfile | None
) -> str | None:
    if override_profile is None:
        return None

    tier = tier_from_path(finding.path)

    # Most-specific precedence: rule+tier > rule > tier.
    rule_tier_key = (tier, finding.id)
    if rule_tier_key in override_profile.rule_tier:
        return override_profile.rule_tier[rule_tier_key]
    if finding.id in override_profile.rule:
        return override_profile.rule[finding.id]
    if tier in override_profile.tier:
        return override_profile.tier[tier]

    return None


def translate_finding_severity(
    finding: Finding, override_profile: OverrideProfile | None = None
) -> Finding:
    """Apply repository overrides and built-in tier policy to one finding."""
    override_severity = _resolve_override_severity(finding, override_profile)
    if override_severity is not None:
        return _with_severity(finding, override_severity)
    return _apply_base_default(finding)


def apply_tier_policy(
    findings: Iterable[Finding], override_profile: OverrideProfile | None = None
) -> list[Finding]:
    """Return findings after repository override and tier-policy translation."""
    return [
        translate_finding_severity(finding, override_profile=override_profile)
        for finding in findings
    ]
