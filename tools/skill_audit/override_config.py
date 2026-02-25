"""Repository override config parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .findings import ALLOWED_SEVERITIES
from .rules import BUILTIN_RULE_IDS

OVERRIDE_CONFIG_FILENAME = ".skill-audit-overrides.yaml"
SUPPORTED_VERSION = 1
ALLOWED_TIERS: tuple[str, ...] = ("system", "curated", "experimental")


class OverrideConfigError(ValueError):
    """Raised when override config parsing or validation fails."""


@dataclass(frozen=True)
class OverrideProfile:
    """Validated override profile used by policy resolution."""

    tier: dict[str, str]
    rule: dict[str, str]
    rule_tier: dict[tuple[str, str], str]


def _format_path(path: Path) -> str:
    return path.as_posix()


def _expect_mapping(value: Any, *, field: str, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' must be a mapping."
        )
    return value


def _validate_severity(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str):
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' must be a string severity."
        )
    severity = value.strip().lower()
    if severity not in ALLOWED_SEVERITIES:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' has unsupported severity '{value}'. "
            f"Allowed: {', '.join(ALLOWED_SEVERITIES)}."
        )
    return severity


def _validate_rule_id(rule_id: Any, *, field: str, path: Path) -> str:
    if not isinstance(rule_id, str):
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' rule IDs must be strings."
        )
    if rule_id not in BUILTIN_RULE_IDS:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' references unknown rule ID '{rule_id}'."
        )
    return rule_id


def _validate_tier_name(tier: Any, *, field: str, path: Path) -> str:
    if not isinstance(tier, str):
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' tier keys must be strings."
        )
    normalized = tier.strip().lower()
    if normalized not in ALLOWED_TIERS:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' references unknown tier '{tier}'. "
            f"Allowed: {', '.join(ALLOWED_TIERS)}."
        )
    return normalized


def _validate_root(raw: dict[str, Any], path: Path) -> None:
    allowed_root = {"version", "severity_overrides"}
    unknown = sorted(set(raw) - allowed_root)
    if unknown:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: unknown top-level "
            f"key(s): {', '.join(unknown)}."
        )
    if "version" not in raw:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: missing required "
            "'version' key."
        )
    if "severity_overrides" not in raw:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: missing required "
            "'severity_overrides' key."
        )

    version = raw["version"]
    if not isinstance(version, int) or version != SUPPORTED_VERSION:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'version' must be integer {SUPPORTED_VERSION}."
        )


def _parse_tier_overrides(raw: dict[str, Any], path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_tier in sorted(raw):
        tier = _validate_tier_name(raw_tier, field="severity_overrides.tier", path=path)
        parsed[tier] = _validate_severity(
            raw[raw_tier],
            field=f"severity_overrides.tier.{tier}",
            path=path,
        )
    return parsed


def _parse_rule_overrides(raw: dict[str, Any], path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_rule in sorted(raw):
        rule_id = _validate_rule_id(raw_rule, field="severity_overrides.rule", path=path)
        parsed[rule_id] = _validate_severity(
            raw[raw_rule],
            field=f"severity_overrides.rule.{rule_id}",
            path=path,
        )
    return parsed


def _parse_rule_tier_overrides(
    raw: dict[str, Any],
    path: Path,
) -> dict[tuple[str, str], str]:
    parsed: dict[tuple[str, str], str] = {}
    for raw_tier in sorted(raw):
        tier = _validate_tier_name(raw_tier, field="severity_overrides.rule_tier", path=path)
        raw_rules = _expect_mapping(
            raw[raw_tier],
            field=f"severity_overrides.rule_tier.{tier}",
            path=path,
        )
        for raw_rule in sorted(raw_rules):
            rule_id = _validate_rule_id(
                raw_rule,
                field=f"severity_overrides.rule_tier.{tier}",
                path=path,
            )
            parsed[(tier, rule_id)] = _validate_severity(
                raw_rules[raw_rule],
                field=f"severity_overrides.rule_tier.{tier}.{rule_id}",
                path=path,
            )
    return parsed


def _parse_overrides(raw: dict[str, Any], path: Path) -> OverrideProfile:
    allowed_sections = {"tier", "rule", "rule_tier"}
    unknown = sorted(set(raw) - allowed_sections)
    if unknown:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: unknown "
            f"severity_overrides key(s): {', '.join(unknown)}."
        )

    tier_raw = raw.get("tier", {})
    rule_raw = raw.get("rule", {})
    rule_tier_raw = raw.get("rule_tier", {})

    tier = _parse_tier_overrides(
        _expect_mapping(tier_raw, field="severity_overrides.tier", path=path),
        path,
    )
    rule = _parse_rule_overrides(
        _expect_mapping(rule_raw, field="severity_overrides.rule", path=path),
        path,
    )
    rule_tier = _parse_rule_tier_overrides(
        _expect_mapping(rule_tier_raw, field="severity_overrides.rule_tier", path=path),
        path,
    )

    return OverrideProfile(tier=tier, rule=rule, rule_tier=rule_tier)


def load_override_profile(
    repo_root: Path,
    filename: str = OVERRIDE_CONFIG_FILENAME,
) -> OverrideProfile | None:
    """Load and validate override profile from repository root."""
    config_path = repo_root / filename
    if not config_path.exists():
        return None

    try:
        raw_loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(config_path)}: "
            f"malformed YAML ({exc.__class__.__name__})."
        ) from exc
    except OSError as exc:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(config_path)}: {exc}"
        ) from exc

    if raw_loaded is None:
        raw_loaded = {}

    raw = _expect_mapping(raw_loaded, field="root", path=config_path)
    _validate_root(raw, config_path)
    overrides = _expect_mapping(raw["severity_overrides"], field="severity_overrides", path=config_path)
    return _parse_overrides(overrides, config_path)
