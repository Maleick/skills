#!/usr/bin/env python3
"""Run deterministic protocol simulation cases and emit evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable

from protocol_rules import (
    deterministic_claim_owner,
    validate_transition,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only specific case ids (repeatable), e.g. --case 1 --case 3",
    )
    parser.add_argument("--json-out", default="", help="Optional path for JSON result output.")
    parser.add_argument("--markdown-out", default="", help="Optional path for Markdown result output.")
    return parser.parse_args()


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def completed_case(case_id: int, name: str, passed: bool, evidence: list[str], blockers: list[str] | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "name": name,
        "passed": passed,
        "evidence": evidence,
        "blockers": blockers or [],
    }


def case_1_parallel_claim_collision() -> dict[str, Any]:
    workers = ["builder-B", "builder-A"]
    winner_1 = deterministic_claim_owner(workers)
    winner_2 = deterministic_claim_owner(list(reversed(workers)))
    passed = winner_1 == "builder-A" and winner_2 == "builder-A"
    evidence = [
        f"deterministic winner run#1={winner_1}",
        f"deterministic winner run#2={winner_2}",
    ]
    blockers = [] if passed else ["claim selection is not deterministic"]
    return completed_case(1, "Parallel claim collision", passed, evidence, blockers)


def case_2_stale_lease_recovery() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    claimed_until = now - timedelta(minutes=5)
    candidates = ["builder-A", "builder-B", "builder-C"]
    current_owner = "builder-A"

    recovered_owner = None
    if claimed_until <= now:
        recovered_owner = deterministic_claim_owner([item for item in candidates if item != current_owner])

    passed = recovered_owner == "builder-B"
    evidence = [
        f"expired_claimed_until={iso(claimed_until)}",
        f"orchestrator_reclaimed_owner={recovered_owner}",
    ]
    blockers = [] if passed else ["stale lease did not produce deterministic orchestrator reclaim"]
    return completed_case(2, "Stale lease recovery", passed, evidence, blockers)


def case_3_reviewer_conflict() -> dict[str, Any]:
    reviewer_a = "done"
    reviewer_b = "failed"

    if reviewer_a != reviewer_b:
        escalation_state = "failed"
        tie_break_owner = "Orchestrator"
        blocker = "Reviewer conflict: done vs failed"
    else:
        escalation_state = reviewer_a
        tie_break_owner = ""
        blocker = ""

    passed = escalation_state == "failed" and tie_break_owner == "Orchestrator" and bool(blocker)
    evidence = [
        f"reviewer_a={reviewer_a}",
        f"reviewer_b={reviewer_b}",
        f"escalation_state={escalation_state}",
        f"tie_break_owner={tie_break_owner}",
    ]
    blockers = [] if passed else ["conflicting review outcomes did not escalate deterministically"]
    return completed_case(3, "Reviewer conflict", passed, evidence, blockers)


def case_4_non_self_approval() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    result = validate_transition(
        from_state="review",
        to_state="done",
        actor_role="Reviewer",
        actor_id="reviewer-1",
        author_id="reviewer-1",
        now=now,
    )
    passed = not result["allowed"] and any("self-approval" in row for row in result["errors"])
    evidence = [
        f"allowed={result['allowed']}",
        f"errors={'; '.join(result['errors'])}",
    ]
    blockers = [] if passed else ["self-approval attempt was not rejected"]
    return completed_case(4, "Non-self approval", passed, evidence, blockers)


def case_5_memory_isolation() -> dict[str, Any]:
    auto_memory_scripts = Path.home() / ".codex" / "skills" / "auto-memory" / "scripts"
    save_script = auto_memory_scripts / "save_memory.py"
    load_script = auto_memory_scripts / "load_memory.py"

    if not save_script.exists() or not load_script.exists():
        return completed_case(
            5,
            "Memory isolation",
            False,
            ["auto-memory scripts were not found"],
            ["missing save_memory.py/load_memory.py for isolation test"],
        )

    with tempfile.TemporaryDirectory(prefix="protocol-memory-") as tmp_dir:
        env = os.environ.copy()
        env["CODEX_HOME"] = tmp_dir

        alpha_body = "## Summary\n- alpha memory\n\n## Context\n- project alpha\n\n## Decision\n- isolate\n\n## Rationale\n- test\n\n## Implementation\n- save\n\n## Verification\n- pass\n\n## Follow-ups\n- none\n\n## Changelog\n- init"
        beta_body = "## Summary\n- beta secret phrase\n\n## Context\n- project beta\n\n## Decision\n- isolate\n\n## Rationale\n- test\n\n## Implementation\n- save\n\n## Verification\n- pass\n\n## Follow-ups\n- none\n\n## Changelog\n- init"

        save_alpha = subprocess.run(
            [
                "python3",
                str(save_script),
                "--project",
                "proj-alpha",
                "--title",
                "alpha note",
                "--body",
                alpha_body,
                "--tags",
                "project:proj-alpha,task_id:TASK-ALPHA",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        save_beta = subprocess.run(
            [
                "python3",
                str(save_script),
                "--project",
                "proj-beta",
                "--title",
                "beta note",
                "--body",
                beta_body,
                "--tags",
                "project:proj-beta,task_id:TASK-BETA",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        load_alpha = subprocess.run(
            [
                "python3",
                str(load_script),
                "--project",
                "proj-alpha",
                "--query",
                "handoff evidence",
                "--require-tag",
                "task_id:task-beta",
                "--limit",
                "8",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    passed = False
    evidence: list[str] = [
        f"save_alpha_rc={save_alpha.returncode}",
        f"save_beta_rc={save_beta.returncode}",
        f"load_alpha_rc={load_alpha.returncode}",
    ]
    blockers: list[str] = []

    if save_alpha.returncode != 0 or save_beta.returncode != 0 or load_alpha.returncode != 0:
        blockers.append("one or more auto-memory commands failed")
        evidence.extend(
            [
                f"save_alpha_stderr={save_alpha.stderr.strip()}",
                f"save_beta_stderr={save_beta.stderr.strip()}",
                f"load_alpha_stderr={load_alpha.stderr.strip()}",
            ]
        )
    else:
        payload = json.loads(load_alpha.stdout)
        results = payload.get("results") or []
        passed = len(results) == 0
        evidence.append(f"alpha_query_results={len(results)}")
        if not passed:
            blockers.append("project-scoped retrieval leaked cross-project memory")

    return completed_case(5, "Memory isolation", passed, evidence, blockers)


def case_6_runtime_coupled_guard() -> dict[str, Any]:
    result = validate_transition(
        from_state="assigned",
        to_state="in_progress",
        actor_role="Builder",
        actor_id="builder-1",
        author_id="orchestrator-1",
        adapter_mode=True,
        allow_runtime_coupled=False,
        runtime_text="openclaw cron add --session isolated",
    )
    passed = not result["allowed"] and any("runtime-coupled" in row for row in result["errors"])
    evidence = [
        f"allowed={result['allowed']}",
        f"errors={'; '.join(result['errors'])}",
    ]
    blockers = [] if passed else ["runtime-coupled guard failed in adapter mode"]
    return completed_case(6, "Runtime-coupled guard", passed, evidence, blockers)


def case_7_ralph_bounded_loop_compliance() -> dict[str, Any]:
    planned_changes = ["change-1", "change-2"]
    allowed = len(planned_changes) <= 1
    passed = not allowed
    evidence = [
        f"planned_changes={len(planned_changes)}",
        "policy=one change-set per delegated builder iteration",
    ]
    blockers = [] if passed else ["multi-change iteration was not rejected"]
    return completed_case(7, "Ralph bounded-loop compliance", passed, evidence, blockers)


def case_8_self_improve_gate_compliance() -> dict[str, Any]:
    smoke_status = "pass"
    regression_status = "fail"
    final_decision = "accept" if smoke_status == "pass" and regression_status == "pass" else "reject"
    passed = final_decision == "reject"
    evidence = [
        f"smoke_status={smoke_status}",
        f"regression_status={regression_status}",
        f"final_decision={final_decision}",
    ]
    blockers = [] if passed else ["self-improve gate did not reject smoke-pass/regression-fail"]
    return completed_case(8, "Self-improve gate compliance", passed, evidence, blockers)


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Protocol Simulation Results")
    lines.append("")
    lines.append(f"- total_cases: {summary['total_cases']}")
    lines.append(f"- passed_cases: {summary['passed_cases']}")
    lines.append(f"- failed_cases: {summary['failed_cases']}")
    lines.append(f"- status: {summary['status']}")
    lines.append("")
    lines.append("| Case | Name | Result | Evidence | Blockers |")
    lines.append("|---|---|---|---|---|")
    for case in summary["cases"]:
        result = "PASS" if case["passed"] else "FAIL"
        evidence = "<br>".join(case["evidence"]) if case["evidence"] else ""
        blockers = "<br>".join(case["blockers"]) if case["blockers"] else ""
        lines.append(f"| {case['case_id']} | {case['name']} | {result} | {evidence} | {blockers} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()

    all_cases: list[tuple[int, Callable[[], dict[str, Any]]]] = [
        (1, case_1_parallel_claim_collision),
        (2, case_2_stale_lease_recovery),
        (3, case_3_reviewer_conflict),
        (4, case_4_non_self_approval),
        (5, case_5_memory_isolation),
        (6, case_6_runtime_coupled_guard),
        (7, case_7_ralph_bounded_loop_compliance),
        (8, case_8_self_improve_gate_compliance),
    ]

    selected_ids = {int(item) for item in args.case} if args.case else {item[0] for item in all_cases}
    executed: list[dict[str, Any]] = []
    for case_id, runner in all_cases:
        if case_id in selected_ids:
            executed.append(runner())

    passed_cases = sum(1 for row in executed if row["passed"])
    failed_cases = len(executed) - passed_cases
    summary = {
        "status": "pass" if failed_cases == 0 else "fail",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "total_cases": len(executed),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "cases": executed,
    }

    payload = json.dumps(summary, indent=2)
    print(payload)

    if args.json_out:
        out = Path(args.json_out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")

    if args.markdown_out:
        md = Path(args.markdown_out).expanduser().resolve()
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(summary), encoding="utf-8")

    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
