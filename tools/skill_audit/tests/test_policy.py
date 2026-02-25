from tools.skill_audit.findings import Finding
from tools.skill_audit.policy import apply_tier_policy, tier_from_path, translate_finding_severity


def test_tier_from_path_detects_known_tiers() -> None:
    assert tier_from_path("skills/.system/example/SKILL.md") == "system"
    assert tier_from_path("skills/.curated/example/SKILL.md") == "curated"
    assert tier_from_path("skills/.experimental/example/SKILL.md") == "experimental"
    assert tier_from_path("docs/other.md") == "unknown"


def test_experimental_warning_biased_rule_is_downgraded() -> None:
    finding = Finding(
        id="META-110",
        severity="invalid",
        path="skills/.experimental/example/SKILL.md",
        message="mismatch",
        suggested_fix="align metadata",
    )
    translated = translate_finding_severity(finding)
    assert translated.severity == "warning"


def test_experimental_critical_rule_remains_invalid() -> None:
    finding = Finding(
        id="META-001",
        severity="invalid",
        path="skills/.experimental/example/SKILL.md",
        message="missing SKILL.md",
        suggested_fix="create SKILL.md",
    )
    translated = translate_finding_severity(finding)
    assert translated.severity == "invalid"


def test_system_and_curated_tiers_remain_strict() -> None:
    strict_findings = [
        Finding(
            id="META-110",
            severity="invalid",
            path="skills/.system/example/SKILL.md",
            message="mismatch",
            suggested_fix="fix",
        ),
        Finding(
            id="META-110",
            severity="invalid",
            path="skills/.curated/example/SKILL.md",
            message="mismatch",
            suggested_fix="fix",
        ),
    ]
    translated = apply_tier_policy(strict_findings)
    assert translated[0].severity == "invalid"
    assert translated[1].severity == "invalid"
