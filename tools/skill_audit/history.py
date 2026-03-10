"""Deterministic history snapshot and trend helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HISTORY_SCHEMA_VERSION = 1
SEVERITY_ORDER: tuple[str, ...] = ("valid", "warning", "invalid")
TIER_ORDER: tuple[str, ...] = ("system", "curated", "experimental", "unknown")


class HistorySnapshotError(ValueError):
    """Raised when snapshot payloads are malformed or incompatible."""


def _as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_severity_counts(raw: object) -> dict[str, int]:
    data = raw if isinstance(raw, dict) else {}
    return {severity: _as_int(data.get(severity, 0)) for severity in SEVERITY_ORDER}


def _normalize_tier_totals(raw: object) -> dict[str, dict[str, object]]:
    if not isinstance(raw, dict):
        raw = {}

    ordered_tiers = list(TIER_ORDER)
    extras = sorted(key for key in raw.keys() if key not in set(TIER_ORDER))
    ordered_tiers.extend(extras)

    normalized: dict[str, dict[str, object]] = {}
    for tier in ordered_tiers:
        tier_data = raw.get(tier)
        if not isinstance(tier_data, dict):
            tier_data = {}
        normalized[tier] = {
            "skill_count": _as_int(tier_data.get("skill_count", 0)),
            "finding_count": _as_int(tier_data.get("finding_count", 0)),
            "status_counts": _normalize_severity_counts(tier_data.get("status_counts", {})),
            "severity_totals": _normalize_severity_counts(
                tier_data.get("severity_totals", {})
            ),
        }
    return normalized


def _normalize_policy_profile(raw: object) -> dict[str, object]:
    policy = raw if isinstance(raw, dict) else {}
    raw_override_counts = policy.get("override_counts")
    override_counts = raw_override_counts if isinstance(raw_override_counts, dict) else {}
    available_profiles = policy.get("available_profiles", [])
    if isinstance(available_profiles, list):
        normalized_profiles = sorted(str(item) for item in available_profiles)
    else:
        normalized_profiles = []
    return {
        "source": str(policy.get("source", "default")),
        "active": bool(policy.get("active", False)),
        "mode": str(policy.get("mode", "base-default")),
        "profile_name": str(policy.get("profile_name", "default")),
        "selection": str(policy.get("selection", "base-default")),
        "available_profiles": normalized_profiles,
        "override_counts": {
            "tier": _as_int(override_counts.get("tier", 0)),
            "rule": _as_int(override_counts.get("rule", 0)),
            "rule_tier": _as_int(override_counts.get("rule_tier", 0)),
            "total": _as_int(override_counts.get("total", 0)),
        },
    }


def _normalize_scan(raw: object) -> dict[str, object]:
    scan = raw if isinstance(raw, dict) else {}
    changed_files = scan.get("changed_files", [])
    normalized_changed_files: list[str] = []
    if isinstance(changed_files, list):
        normalized_changed_files = sorted(str(item) for item in changed_files)

    return {
        "mode": str(scan.get("mode", "full")),
        "compare_range": (
            str(scan["compare_range"]) if scan.get("compare_range") is not None else None
        ),
        "changed_file_count": _as_int(scan.get("changed_file_count", 0)),
        "changed_files": normalized_changed_files,
        "impacted_skill_count": _as_int(scan.get("impacted_skill_count", 0)),
        "scanned_skill_count": _as_int(scan.get("scanned_skill_count", 0)),
        "total_skill_count": _as_int(scan.get("total_skill_count", 0)),
        "policy_profile": _normalize_policy_profile(scan.get("policy_profile", {})),
    }


def _normalize_skills(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []

    rows: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        rows.append(
            {
                "path": path,
                "tier": str(item.get("tier", "unknown")),
                "status": str(item.get("status", "valid")),
                "finding_count": _as_int(item.get("finding_count", 0)),
                "severity_counts": _normalize_severity_counts(
                    item.get("severity_counts", {})
                ),
            }
        )

    return sorted(rows, key=lambda row: row["path"])


def _normalize_summary(raw: object) -> dict[str, object]:
    summary = raw if isinstance(raw, dict) else {}
    global_raw = summary.get("global", {}) if isinstance(summary.get("global"), dict) else {}
    return {
        "global": {
            "skill_count": _as_int(global_raw.get("skill_count", 0)),
            "finding_count": _as_int(global_raw.get("finding_count", 0)),
            "total_skill_count": _as_int(global_raw.get("total_skill_count", 0)),
        },
        "severity_totals": _normalize_severity_counts(summary.get("severity_totals", {})),
        "tier_totals": _normalize_tier_totals(summary.get("tier_totals", {})),
    }


def _snapshot_fingerprint(snapshot: dict[str, object]) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_history_snapshot(index_payload: dict[str, Any]) -> dict[str, object]:
    """Build deterministic snapshot payload from index output."""
    snapshot = {
        "summary": _normalize_summary(index_payload.get("summary", {})),
        "scan": _normalize_scan(index_payload.get("scan", {})),
        "skills": _normalize_skills(index_payload.get("skills", [])),
    }
    return {
        "schema_version": HISTORY_SCHEMA_VERSION,
        "fingerprint": _snapshot_fingerprint(snapshot),
        "snapshot": snapshot,
    }


def serialize_history_snapshot(payload: dict[str, object]) -> str:
    """Serialize snapshot payload with deterministic key ordering."""
    return json.dumps(payload, indent=2, sort_keys=True)


def write_history_snapshot(
    path: Path, payload: dict[str, object], force_overwrite: bool
) -> None:
    """Write snapshot payload to disk using overwrite safety rules."""
    if path.exists() and not force_overwrite:
        raise FileExistsError(f"Output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_history_snapshot(payload), encoding="utf-8")


def _validate_snapshot_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise HistorySnapshotError("Snapshot payload must be a JSON object.")

    if _as_int(payload.get("schema_version")) != HISTORY_SCHEMA_VERSION:
        raise HistorySnapshotError(
            f"Unsupported snapshot schema version: {payload.get('schema_version')}"
        )

    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, dict):
        raise HistorySnapshotError("Snapshot payload is missing 'snapshot' object.")

    if "summary" not in snapshot or "scan" not in snapshot or "skills" not in snapshot:
        raise HistorySnapshotError("Snapshot payload is missing required sections.")

    return {
        "schema_version": HISTORY_SCHEMA_VERSION,
        "fingerprint": str(payload.get("fingerprint", "")),
        "snapshot": {
            "summary": _normalize_summary(snapshot.get("summary", {})),
            "scan": _normalize_scan(snapshot.get("scan", {})),
            "skills": _normalize_skills(snapshot.get("skills", [])),
        },
    }


def load_history_snapshot(path: Path) -> dict[str, object]:
    """Load and validate a history snapshot payload."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _validate_snapshot_payload(raw)


def build_trend_summary(
    current_snapshot: dict[str, object], baseline_snapshot: dict[str, object] | None
) -> dict[str, object]:
    """Build deterministic trend summary from current/baseline snapshots."""
    current = _validate_snapshot_payload(current_snapshot)
    if baseline_snapshot is None:
        return {
            "status": "no-baseline",
            "message": "No baseline snapshot available for comparison.",
            "finding_delta": 0,
            "severity_deltas": {severity: 0 for severity in SEVERITY_ORDER},
            "tier_deltas": {},
            "skill_changes": [],
        }

    baseline = _validate_snapshot_payload(baseline_snapshot)

    current_summary = current["snapshot"]["summary"]
    baseline_summary = baseline["snapshot"]["summary"]

    current_global = current_summary["global"]
    baseline_global = baseline_summary["global"]

    finding_delta = _as_int(current_global.get("finding_count", 0)) - _as_int(
        baseline_global.get("finding_count", 0)
    )

    severity_deltas = {
        severity: _as_int(current_summary["severity_totals"].get(severity, 0))
        - _as_int(baseline_summary["severity_totals"].get(severity, 0))
        for severity in SEVERITY_ORDER
    }

    current_tiers = current_summary["tier_totals"]
    baseline_tiers = baseline_summary["tier_totals"]
    tier_names = [tier for tier in TIER_ORDER if tier in current_tiers or tier in baseline_tiers]
    tier_names.extend(
        sorted(
            tier
            for tier in set(current_tiers.keys()) | set(baseline_tiers.keys())
            if tier not in set(TIER_ORDER)
        )
    )

    tier_deltas: dict[str, int] = {}
    for tier in tier_names:
        current_count = _as_int((current_tiers.get(tier) or {}).get("finding_count", 0))
        baseline_count = _as_int((baseline_tiers.get(tier) or {}).get("finding_count", 0))
        tier_deltas[tier] = current_count - baseline_count

    baseline_skills = {
        str(item["path"]): item
        for item in baseline["snapshot"]["skills"]
        if isinstance(item, dict) and "path" in item
    }
    current_skills = {
        str(item["path"]): item
        for item in current["snapshot"]["skills"]
        if isinstance(item, dict) and "path" in item
    }

    skill_changes: list[dict[str, object]] = []
    for path in sorted(set(baseline_skills.keys()) | set(current_skills.keys())):
        before = baseline_skills.get(path)
        after = current_skills.get(path)

        before_status = str(before.get("status", "absent")) if before is not None else "absent"
        after_status = str(after.get("status", "absent")) if after is not None else "absent"
        before_count = _as_int(before.get("finding_count", 0)) if before is not None else 0
        after_count = _as_int(after.get("finding_count", 0)) if after is not None else 0
        delta = after_count - before_count

        if before_status != after_status or delta != 0:
            skill_changes.append(
                {
                    "path": path,
                    "from_status": before_status,
                    "to_status": after_status,
                    "finding_delta": delta,
                }
            )

    return {
        "status": "ok",
        "finding_delta": finding_delta,
        "severity_deltas": severity_deltas,
        "tier_deltas": tier_deltas,
        "skill_changes": skill_changes,
    }


def _signed(value: int) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def render_trend_summary(trend_summary: dict[str, object]) -> str:
    """Render trend summary in deterministic human-readable format."""
    status = str(trend_summary.get("status", "no-baseline"))
    lines = ["Trend Summary", f"- status: {status}"]

    if status != "ok":
        lines.append(
            f"- message: {trend_summary.get('message', 'No baseline snapshot available for comparison.')}"
        )
        return "\n".join(lines)

    lines.append(f"- findings delta: {_signed(_as_int(trend_summary.get('finding_delta', 0)))}")
    lines.append("- severity deltas:")
    raw_severity = trend_summary.get("severity_deltas", {})
    severity = raw_severity if isinstance(raw_severity, dict) else {}
    for level in SEVERITY_ORDER:
        lines.append(f"  - {level}: {_signed(_as_int(severity.get(level, 0)))}")

    lines.append("- tier deltas:")
    raw_tiers = trend_summary.get("tier_deltas", {})
    tiers = raw_tiers if isinstance(raw_tiers, dict) else {}
    tier_order = [tier for tier in TIER_ORDER if tier in tiers]
    tier_order.extend(sorted(tier for tier in tiers.keys() if tier not in set(TIER_ORDER)))
    if tier_order:
        for tier in tier_order:
            lines.append(f"  - {tier}: {_signed(_as_int(tiers.get(tier, 0)))}")
    else:
        lines.append("  - none")

    raw_changes = trend_summary.get("skill_changes", [])
    changes = raw_changes if isinstance(raw_changes, list) else []
    if changes:
        lines.append("- skill changes:")
        for item in changes:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('path', '<unknown>')}: "
                f"{item.get('from_status', 'absent')} -> "
                f"{item.get('to_status', 'absent')} "
                f"(delta {_signed(_as_int(item.get('finding_delta', 0)))})"
            )
    else:
        lines.append("- skill changes: none")

    return "\n".join(lines)
