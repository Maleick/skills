from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.skill_audit.history import (
    HistorySnapshotError,
    build_history_snapshot,
    build_trend_summary,
    load_history_snapshot,
    render_trend_summary,
    serialize_history_snapshot,
    write_history_snapshot,
)


def _sample_index_payload() -> dict[str, object]:
    return {
        "scan": {
            "mode": "changed-files",
            "compare_range": "HEAD~1..HEAD",
            "changed_file_count": 1,
            "changed_files": ["skills/.curated/demo/SKILL.md"],
            "impacted_skill_count": 1,
            "scanned_skill_count": 1,
            "total_skill_count": 2,
            "policy_profile": {
                "source": ".skill-audit-overrides.yaml",
                "active": True,
                "mode": "named-profiles",
                "profile_name": "strict",
                "selection": "explicit",
                "available_profiles": ["strict", "balanced"],
                "override_counts": {"tier": 0, "rule": 1, "rule_tier": 0, "total": 1},
            },
        },
        "summary": {
            "global": {
                "skill_count": 1,
                "finding_count": 1,
                "total_skill_count": 2,
            },
            "severity_totals": {"valid": 0, "warning": 0, "invalid": 1},
            "tier_totals": {
                "system": {
                    "skill_count": 0,
                    "finding_count": 0,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 0},
                },
                "curated": {
                    "skill_count": 1,
                    "finding_count": 1,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 1},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 1},
                },
                "experimental": {
                    "skill_count": 0,
                    "finding_count": 0,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 0},
                },
                "unknown": {
                    "skill_count": 0,
                    "finding_count": 0,
                    "status_counts": {"valid": 0, "warning": 0, "invalid": 0},
                    "severity_totals": {"valid": 0, "warning": 0, "invalid": 0},
                },
            },
        },
        "skills": [
            {
                "path": "skills/.curated/demo",
                "tier": "curated",
                "status": "invalid",
                "finding_count": 1,
                "severity_counts": {"valid": 0, "warning": 0, "invalid": 1},
            }
        ],
    }


def test_snapshot_is_deterministic_for_identical_input() -> None:
    payload = _sample_index_payload()
    first = build_history_snapshot(payload)
    second = build_history_snapshot(payload)

    assert first == second
    assert first["schema_version"] == 1
    assert isinstance(first["fingerprint"], str)

    text_first = serialize_history_snapshot(first)
    text_second = serialize_history_snapshot(second)
    assert text_first == text_second


def test_snapshot_write_respects_force_overwrite(tmp_path: Path) -> None:
    out_path = tmp_path / "history/snapshot.json"
    snapshot = build_history_snapshot(_sample_index_payload())

    write_history_snapshot(out_path, snapshot, force_overwrite=False)
    assert out_path.exists()

    with pytest.raises(FileExistsError):
        write_history_snapshot(out_path, snapshot, force_overwrite=False)

    write_history_snapshot(out_path, snapshot, force_overwrite=True)
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["fingerprint"] == snapshot["fingerprint"]


def test_load_history_snapshot_rejects_invalid_schema(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(
        json.dumps({"schema_version": 999, "snapshot": {}}),
        encoding="utf-8",
    )

    with pytest.raises(HistorySnapshotError):
        load_history_snapshot(bad_path)


def test_trend_summary_reports_deltas_and_skill_changes() -> None:
    baseline_payload = _sample_index_payload()
    current_payload = _sample_index_payload()

    baseline_payload["summary"]["global"]["finding_count"] = 2
    baseline_payload["summary"]["severity_totals"]["invalid"] = 2
    baseline_payload["summary"]["tier_totals"]["curated"]["finding_count"] = 2
    baseline_payload["summary"]["tier_totals"]["curated"]["severity_totals"]["invalid"] = 2
    baseline_payload["skills"][0]["finding_count"] = 2
    baseline_payload["skills"][0]["severity_counts"]["invalid"] = 2

    baseline = build_history_snapshot(baseline_payload)
    current = build_history_snapshot(current_payload)

    trend = build_trend_summary(current, baseline)
    assert trend["status"] == "ok"
    assert trend["finding_delta"] == -1
    assert trend["severity_deltas"]["invalid"] == -1
    assert trend["tier_deltas"]["curated"] == -1
    assert trend["skill_changes"]

    rendered = render_trend_summary(trend)
    assert "Trend Summary" in rendered
    assert "status: ok" in rendered
    assert "findings delta: -1" in rendered


def test_trend_summary_without_baseline_is_non_fatal() -> None:
    current = build_history_snapshot(_sample_index_payload())
    trend = build_trend_summary(current, None)

    assert trend["status"] == "no-baseline"
    rendered = render_trend_summary(trend)
    assert "status: no-baseline" in rendered
    assert "No baseline snapshot available" in rendered
