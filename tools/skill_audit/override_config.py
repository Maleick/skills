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


@dataclass(frozen=True)
class ResolvedOverrideProfile:
    """Selected override profile metadata used by runtime and reporting."""

    profile: OverrideProfile
    profile_name: str
    selection: str
    available_profiles: tuple[str, ...]


def build_policy_profile_metadata(
    resolved_profile: ResolvedOverrideProfile | None,
    *,
    source_filename: str = OVERRIDE_CONFIG_FILENAME,
) -> dict[str, Any]:
    """Return deterministic policy-profile metadata for reporting surfaces."""
    tier_count = 0
    rule_count = 0
    rule_tier_count = 0
    profile_name = "default"
    selection = "base-default"
    available_profiles: list[str] = []

    if resolved_profile is not None:
        tier_count = len(resolved_profile.profile.tier)
        rule_count = len(resolved_profile.profile.rule)
        rule_tier_count = len(resolved_profile.profile.rule_tier)
        profile_name = resolved_profile.profile_name
        selection = resolved_profile.selection
        available_profiles = list(resolved_profile.available_profiles)

    active = resolved_profile is not None
    return {
        "source": source_filename if active else "default",
        "active": active,
        "mode": "severity-overrides" if active else "base-default",
        "profile_name": profile_name,
        "selection": selection,
        "available_profiles": available_profiles,
        "override_counts": {
            "tier": tier_count,
            "rule": rule_count,
            "rule_tier": rule_tier_count,
            "total": tier_count + rule_count + rule_tier_count,
        },
    }


def default_policy_profile_metadata() -> dict[str, Any]:
    """Return default policy-profile metadata when no override file is active."""
    return build_policy_profile_metadata(None)


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


def _validate_profile_name(raw_name: Any, *, field: str, path: Path) -> str:
    if not isinstance(raw_name, str):
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' profile names must be strings."
        )
    name = raw_name.strip()
    if not name:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'{field}' profile names cannot be empty."
        )
    return name


def _validate_root(raw: dict[str, Any], path: Path) -> None:
    allowed_root = {"version", "severity_overrides", "profiles", "default_profile"}
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

    version = raw["version"]
    if not isinstance(version, int) or version != SUPPORTED_VERSION:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            f"'version' must be integer {SUPPORTED_VERSION}."
        )

    has_legacy = "severity_overrides" in raw
    has_profiles = "profiles" in raw
    if has_legacy and has_profiles:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            "'severity_overrides' and 'profiles' cannot both be defined."
        )
    if not has_legacy and not has_profiles:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: missing required "
            "'severity_overrides' (legacy mode) or 'profiles' (named mode)."
        )

    if "default_profile" in raw and not has_profiles:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: "
            "'default_profile' requires 'profiles'."
        )


def _parse_tier_overrides(raw: dict[str, Any], path: Path, *, prefix: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_tier in sorted(raw):
        tier = _validate_tier_name(raw_tier, field=f"{prefix}.tier", path=path)
        parsed[tier] = _validate_severity(
            raw[raw_tier],
            field=f"{prefix}.tier.{tier}",
            path=path,
        )
    return parsed


def _parse_rule_overrides(raw: dict[str, Any], path: Path, *, prefix: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_rule in sorted(raw):
        rule_id = _validate_rule_id(raw_rule, field=f"{prefix}.rule", path=path)
        parsed[rule_id] = _validate_severity(
            raw[raw_rule],
            field=f"{prefix}.rule.{rule_id}",
            path=path,
        )
    return parsed


def _parse_rule_tier_overrides(
    raw: dict[str, Any],
    path: Path,
    *,
    prefix: str,
) -> dict[tuple[str, str], str]:
    parsed: dict[tuple[str, str], str] = {}
    for raw_tier in sorted(raw):
        tier = _validate_tier_name(raw_tier, field=f"{prefix}.rule_tier", path=path)
        raw_rules = _expect_mapping(
            raw[raw_tier],
            field=f"{prefix}.rule_tier.{tier}",
            path=path,
        )
        for raw_rule in sorted(raw_rules):
            rule_id = _validate_rule_id(
                raw_rule,
                field=f"{prefix}.rule_tier.{tier}",
                path=path,
            )
            parsed[(tier, rule_id)] = _validate_severity(
                raw_rules[raw_rule],
                field=f"{prefix}.rule_tier.{tier}.{rule_id}",
                path=path,
            )
    return parsed


def _parse_overrides(raw: dict[str, Any], path: Path, *, prefix: str) -> OverrideProfile:
    allowed_sections = {"tier", "rule", "rule_tier"}
    unknown = sorted(set(raw) - allowed_sections)
    if unknown:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: unknown "
            f"{prefix} key(s): {', '.join(unknown)}."
        )

    tier_raw = raw.get("tier", {})
    rule_raw = raw.get("rule", {})
    rule_tier_raw = raw.get("rule_tier", {})

    tier = _parse_tier_overrides(
        _expect_mapping(tier_raw, field=f"{prefix}.tier", path=path),
        path,
        prefix=prefix,
    )
    rule = _parse_rule_overrides(
        _expect_mapping(rule_raw, field=f"{prefix}.rule", path=path),
        path,
        prefix=prefix,
    )
    rule_tier = _parse_rule_tier_overrides(
        _expect_mapping(rule_tier_raw, field=f"{prefix}.rule_tier", path=path),
        path,
        prefix=prefix,
    )

    return OverrideProfile(tier=tier, rule=rule, rule_tier=rule_tier)


def _parse_named_profiles(raw: dict[str, Any], path: Path) -> dict[str, OverrideProfile]:
    profiles: dict[str, OverrideProfile] = {}
    for raw_name in sorted(raw):
        name = _validate_profile_name(raw_name, field="profiles", path=path)
        raw_profile = _expect_mapping(raw[raw_name], field=f"profiles.{name}", path=path)
        profiles[name] = _parse_overrides(raw_profile, path, prefix=f"profiles.{name}")
    if not profiles:
        raise OverrideConfigError(
            f"Invalid override config at {_format_path(path)}: 'profiles' cannot be empty."
        )
    return profiles


def _resolve_named_profile(
    *,
    profiles: dict[str, OverrideProfile],
    default_profile: str | None,
    requested_profile: str | None,
    path: Path,
) -> ResolvedOverrideProfile:
    available = tuple(sorted(profiles))

    if requested_profile is not None:
        requested = requested_profile.strip()
        if not requested:
            raise OverrideConfigError(
                f"Invalid override config at {_format_path(path)}: requested profile name is empty."
            )
        if requested not in profiles:
            raise OverrideConfigError(
                f"Invalid override config at {_format_path(path)}: "
                f"requested profile '{requested}' is not defined."
            )
        return ResolvedOverrideProfile(
            profile=profiles[requested],
            profile_name=requested,
            selection="explicit",
            available_profiles=available,
        )

    if default_profile is not None:
        if default_profile not in profiles:
            raise OverrideConfigError(
                f"Invalid override config at {_format_path(path)}: "
                f"default_profile '{default_profile}' is not defined in profiles."
            )
        return ResolvedOverrideProfile(
            profile=profiles[default_profile],
            profile_name=default_profile,
            selection="config-default",
            available_profiles=available,
        )

    if len(profiles) == 1:
        only_name = available[0]
        return ResolvedOverrideProfile(
            profile=profiles[only_name],
            profile_name=only_name,
            selection="single-profile",
            available_profiles=available,
        )

    raise OverrideConfigError(
        f"Invalid override config at {_format_path(path)}: multiple profiles are defined "
        "without default_profile; choose one with --profile or set default_profile."
    )


def load_override_profile_selection(
    repo_root: Path,
    *,
    filename: str = OVERRIDE_CONFIG_FILENAME,
    profile_name: str | None = None,
) -> ResolvedOverrideProfile | None:
    """Load and resolve one active override profile from repository root."""
    config_path = repo_root / filename
    if not config_path.exists():
        if profile_name is not None:
            raise OverrideConfigError(
                f"Invalid override config at {_format_path(config_path)}: "
                f"requested profile '{profile_name}' but file is missing."
            )
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

    if "severity_overrides" in raw:
        if profile_name is not None and profile_name != "default":
            raise OverrideConfigError(
                f"Invalid override config at {_format_path(config_path)}: "
                f"requested profile '{profile_name}' is not defined."
            )
        overrides = _expect_mapping(
            raw["severity_overrides"],
            field="severity_overrides",
            path=config_path,
        )
        parsed = _parse_overrides(overrides, config_path, prefix="severity_overrides")
        selection = "explicit" if profile_name == "default" else "legacy-default"
        return ResolvedOverrideProfile(
            profile=parsed,
            profile_name="default",
            selection=selection,
            available_profiles=("default",),
        )

    raw_profiles = _expect_mapping(raw["profiles"], field="profiles", path=config_path)
    profiles = _parse_named_profiles(raw_profiles, config_path)

    default_profile: str | None = None
    if "default_profile" in raw:
        default_profile = _validate_profile_name(
            raw["default_profile"],
            field="default_profile",
            path=config_path,
        )

    return _resolve_named_profile(
        profiles=profiles,
        default_profile=default_profile,
        requested_profile=profile_name,
        path=config_path,
    )


def load_override_profile(
    repo_root: Path,
    filename: str = OVERRIDE_CONFIG_FILENAME,
    *,
    profile_name: str | None = None,
) -> OverrideProfile | None:
    """Load and validate override profile from repository root."""
    resolved = load_override_profile_selection(
        repo_root,
        filename=filename,
        profile_name=profile_name,
    )
    if resolved is None:
        return None
    return resolved.profile
