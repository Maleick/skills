"""Persistent cache helpers for deterministic skill-audit reuse."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .findings import Finding
from .policy import WARNING_BIASED_EXPERIMENTAL_RULE_IDS
from .rules import BUILTIN_RULE_IDS
from .rules import parity as parity_rules
from .rules import references as reference_rules
from .rules import skill_md as skill_md_rules

if TYPE_CHECKING:
    from .override_config import OverrideProfile

CACHE_SCHEMA_VERSION = 1
CACHE_RULESET_VERSION = 1
DEFAULT_CACHE_RELATIVE_PATH = Path(".planning/cache/skill-audit-cache.json")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_policy_profile_signature(
    override_profile: OverrideProfile | None,
    *,
    active_profile_name: str | None = None,
) -> str:
    """Return deterministic signature for active policy profile inputs."""
    if override_profile is None:
        return "default"

    payload = {
        "profile_name": active_profile_name or "default",
        "tier": {tier: override_profile.tier[tier] for tier in sorted(override_profile.tier)},
        "rule": {rule: override_profile.rule[rule] for rule in sorted(override_profile.rule)},
        "rule_tier": [
            {
                "tier": tier,
                "rule": rule_id,
                "severity": override_profile.rule_tier[(tier, rule_id)],
            }
            for tier, rule_id in sorted(override_profile.rule_tier)
        ],
    }
    return _sha256_text(_stable_json(payload))


def _read_module_hash(path: Path) -> bytes:
    try:
        return hashlib.sha256(path.read_bytes()).digest()
    except OSError:
        return b"<unreadable>"


def build_rules_signature() -> str:
    """Return deterministic signature for built-in rule and policy behavior."""
    hasher = hashlib.sha256()
    hasher.update(f"ruleset-version:{CACHE_RULESET_VERSION}".encode("utf-8"))
    hasher.update(b"\0")

    for rule_id in sorted(BUILTIN_RULE_IDS):
        hasher.update(rule_id.encode("utf-8"))
        hasher.update(b"\0")
    for rule_id in sorted(WARNING_BIASED_EXPERIMENTAL_RULE_IDS):
        hasher.update(rule_id.encode("utf-8"))
        hasher.update(b"\0")

    module_files: set[Path] = set()
    for module in (skill_md_rules, parity_rules, reference_rules):
        module_file = Path(getattr(module, "__file__", ""))
        if module_file.exists():
            module_files.add(module_file.resolve())
    policy_file = Path(__file__).resolve().parent / "policy.py"
    if policy_file.exists():
        module_files.add(policy_file.resolve())

    for module_file in sorted(module_files, key=lambda path: path.as_posix()):
        hasher.update(module_file.name.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(_read_module_hash(module_file))
        hasher.update(b"\0")

    return hasher.hexdigest()


@dataclass
class CacheStats:
    enabled: bool
    mode: str
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    errors: int = 0

    def as_scan_metadata(self) -> dict[str, int | bool | str]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "errors": self.errors,
        }


@dataclass
class SkillAuditCache:
    """Repository-local persistent cache keyed per skill by deterministic signatures."""

    repo_root: Path
    enabled: bool = True
    cache_path: Path | None = None
    _entries: dict[str, dict[str, Any]] = field(init=False, default_factory=dict)
    _dirty: bool = field(init=False, default=False)
    _warnings: list[str] = field(init=False, default_factory=list)
    _stats: CacheStats = field(init=False)

    def __post_init__(self) -> None:
        resolved_root = self.repo_root.resolve()
        object.__setattr__(self, "repo_root", resolved_root)
        path = self.cache_path
        if path is None:
            path = resolved_root / DEFAULT_CACHE_RELATIVE_PATH
        else:
            path = path.resolve()
        object.__setattr__(self, "cache_path", path)
        object.__setattr__(
            self,
            "_stats",
            CacheStats(enabled=self.enabled, mode="read-write" if self.enabled else "disabled"),
        )
        if self.enabled:
            self._load()

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def metadata(self) -> dict[str, int | bool | str]:
        return self._stats.as_scan_metadata()

    def _warn(self, message: str) -> None:
        self._stats.errors += 1
        self._warnings.append(message)

    def _load(self) -> None:
        assert self.cache_path is not None
        if not self.cache_path.exists():
            self._entries = {}
            return

        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._warn(
                f"Cache file '{self.cache_path}' is malformed JSON ({exc.__class__.__name__}); "
                "recomputing and refreshing cache."
            )
            self._entries = {}
            self._dirty = True
            return
        except OSError as exc:
            self._warn(
                f"Cache file '{self.cache_path}' is unreadable ({exc.__class__.__name__}); "
                "recomputing without cache reuse."
            )
            self._entries = {}
            return

        if not isinstance(raw, dict):
            self._warn(
                f"Cache file '{self.cache_path}' has invalid root format; "
                "recomputing and refreshing cache."
            )
            self._entries = {}
            self._dirty = True
            return

        schema_version = raw.get("schema_version")
        if schema_version != CACHE_SCHEMA_VERSION:
            self._warn(
                f"Cache schema mismatch at '{self.cache_path}' "
                f"(found={schema_version}, expected={CACHE_SCHEMA_VERSION}); recomputing cache."
            )
            self._entries = {}
            self._dirty = True
            return

        raw_entries = raw.get("entries", {})
        if not isinstance(raw_entries, dict):
            self._warn(
                f"Cache entries at '{self.cache_path}' are not a mapping; "
                "recomputing and refreshing cache."
            )
            self._entries = {}
            self._dirty = True
            return

        self._entries = dict(raw_entries)

    def _invalidate_entry(self, skill_key: str) -> None:
        self._stats.invalidations += 1
        self._stats.misses += 1
        self._entries.pop(skill_key, None)
        self._dirty = True

    def _coerce_cached_findings(self, raw_findings: object, skill_key: str) -> list[Finding] | None:
        if not isinstance(raw_findings, list):
            self._warn(
                f"Cache entry for '{skill_key}' has invalid findings payload; "
                "entry invalidated and recomputed."
            )
            return None

        findings: list[Finding] = []
        for raw in raw_findings:
            if not isinstance(raw, dict):
                self._warn(
                    f"Cache entry for '{skill_key}' includes non-object finding; "
                    "entry invalidated and recomputed."
                )
                return None
            try:
                findings.append(
                    Finding(
                        id=str(raw["id"]),
                        severity=str(raw["severity"]),
                        path=str(raw["path"]),
                        message=str(raw["message"]),
                        suggested_fix=str(raw["suggested_fix"]),
                    )
                )
            except (KeyError, ValueError) as exc:
                self._warn(
                    f"Cache entry for '{skill_key}' contains invalid finding fields "
                    f"({exc.__class__.__name__}); entry invalidated and recomputed."
                )
                return None
        return findings

    def lookup(
        self,
        *,
        skill_key: str,
        fingerprint: str,
        policy_signature: str,
        rules_signature: str,
    ) -> list[Finding] | None:
        if not self.enabled:
            return None

        entry = self._entries.get(skill_key)
        if entry is None:
            self._stats.misses += 1
            return None
        if not isinstance(entry, dict):
            self._invalidate_entry(skill_key)
            self._warn(
                f"Cache entry for '{skill_key}' has invalid shape; entry invalidated and recomputed."
            )
            return None

        if entry.get("fingerprint") != fingerprint:
            self._invalidate_entry(skill_key)
            return None
        if entry.get("policy_signature") != policy_signature:
            self._invalidate_entry(skill_key)
            return None
        if entry.get("rules_signature") != rules_signature:
            self._invalidate_entry(skill_key)
            return None

        findings = self._coerce_cached_findings(entry.get("findings"), skill_key)
        if findings is None:
            self._invalidate_entry(skill_key)
            return None

        self._stats.hits += 1
        return findings

    def store(
        self,
        *,
        skill_key: str,
        fingerprint: str,
        policy_signature: str,
        rules_signature: str,
        findings: list[Finding],
    ) -> None:
        if not self.enabled:
            return

        ordered_findings = sorted(findings, key=lambda finding: finding.as_sort_key())
        self._entries[skill_key] = {
            "fingerprint": fingerprint,
            "policy_signature": policy_signature,
            "rules_signature": rules_signature,
            "findings": [finding.to_dict() for finding in ordered_findings],
        }
        self._dirty = True

    def flush(self) -> None:
        if not self.enabled or not self._dirty:
            return
        assert self.cache_path is not None

        ordered_entries = {key: self._entries[key] for key in sorted(self._entries)}
        payload = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "entries": ordered_entries,
        }

        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            self._dirty = False
        except OSError as exc:
            self._warn(
                f"Failed to write cache file '{self.cache_path}' "
                f"({exc.__class__.__name__}); continuing without cache persistence."
            )
