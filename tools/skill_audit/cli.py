"""CLI entrypoint for repository skill audit scans."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .findings import Finding
from .indexing import build_skill_index
from .markdown_report import render_markdown_report
from .override_config import OverrideConfigError, load_override_profile
from .policy import (
    TIER_CURATED,
    TIER_EXPERIMENTAL,
    TIER_SYSTEM,
    apply_tier_policy,
    tier_from_path,
)
from .reporting import render_report, sort_findings, summarize_findings
from .rules import validate_local_references, validate_metadata_parity, validate_skill_md
from .scanner import (
    discover_changed_files,
    discover_skill_dirs,
    filter_impacted_skill_dirs,
    impacted_skill_keys,
)

SEVERITY_RANK: dict[str, int] = {"valid": 0, "warning": 1, "invalid": 2}
ALLOWED_GATE_TIERS: tuple[str, ...] = (
    TIER_SYSTEM,
    TIER_CURATED,
    TIER_EXPERIMENTAL,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a baseline skill audit across skills/.system, skills/.curated, "
            "and skills/.experimental."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory. Defaults to current working directory.",
    )
    parser.add_argument(
        "--changed-files",
        action="store_true",
        help=(
            "Scan only skill directories impacted by changed files "
            "(unstaged + staged + untracked by default)."
        ),
    )
    parser.add_argument(
        "--compare-range",
        default=None,
        help=(
            "Git compare range for changed-file discovery (for example "
            "`origin/main...HEAD`). Requires `--changed-files`."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON index payload to stdout.",
    )
    parser.add_argument(
        "--json-out",
        help="Write JSON index payload to this file path.",
    )
    parser.add_argument(
        "--markdown-out",
        help="Write markdown remediation report to this file path.",
    )
    parser.add_argument(
        "--output-dir",
        help=(
            "Optional output directory for stable filenames when explicit paths "
            "are not provided (`skill-index.json`, `skill-remediation.md`)."
        ),
    )
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="Allow overwriting existing output files.",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Enable CI gating mode with compact gate-oriented output.",
    )
    parser.add_argument(
        "--max-severity",
        choices=("valid", "warning", "invalid"),
        default=None,
        help=(
            "Highest allowed severity in CI mode. "
            "Default in CI mode is 'warning' (fail on invalid findings only)."
        ),
    )
    parser.add_argument(
        "--tiers",
        default=None,
        help=(
            "Comma-separated gate scope tiers for CI mode: "
            "system,curated,experimental."
        ),
    )
    parser.add_argument(
        "--verbose-ci",
        action="store_true",
        help="Show full in-scope finding details in CI mode.",
    )
    return parser


def _write_text(path: Path, content: str, force_overwrite: bool) -> None:
    if path.exists() and not force_overwrite:
        raise FileExistsError(f"Output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _parse_gate_tiers(raw_tiers: str | None) -> tuple[str, ...] | None:
    if raw_tiers is None:
        return None
    candidates = [part.strip().lower() for part in raw_tiers.split(",")]
    if not candidates or any(not item for item in candidates):
        raise ValueError(
            "Invalid --tiers value. Use a comma-separated list of: "
            "system,curated,experimental."
        )

    unique = set(candidates)
    unknown = sorted(unique - set(ALLOWED_GATE_TIERS))
    if unknown:
        raise ValueError(
            f"Unknown tier value(s) in --tiers: {', '.join(unknown)}. "
            "Allowed values: system,curated,experimental."
        )
    return tuple(tier for tier in ALLOWED_GATE_TIERS if tier in unique)


def _validate_ci_config(
    *,
    ci_mode: bool,
    max_severity: str | None,
    max_severity_explicit: bool,
    tiers: tuple[str, ...] | None,
    verbose_ci: bool,
) -> str | None:
    if verbose_ci and not ci_mode:
        raise ValueError("--verbose-ci requires --ci.")

    if max_severity is not None and not ci_mode:
        raise ValueError("--max-severity requires --ci.")

    if tiers is not None and not ci_mode:
        raise ValueError("--tiers requires --ci.")

    if not ci_mode:
        return None

    resolved = max_severity or "warning"
    if max_severity_explicit and resolved == "warning" and tiers is None:
        raise ValueError(
            "Warning-tolerant CI mode requires explicit --tiers scope."
        )

    return resolved


def _validate_scan_config(changed_files_mode: bool, compare_range: str | None) -> None:
    if compare_range is not None and not changed_files_mode:
        raise ValueError("--compare-range requires --changed-files.")


def _filter_findings_by_tier(
    findings: list[Finding], tiers: tuple[str, ...] | None
) -> list[Finding]:
    if tiers is None:
        return findings
    allowed = set(tiers)
    return [finding for finding in findings if tier_from_path(finding.path) in allowed]


def _is_gate_failure(findings: list[Finding], max_severity: str) -> bool:
    threshold = SEVERITY_RANK[max_severity]
    return any(SEVERITY_RANK[finding.severity] > threshold for finding in findings)


def _build_scan_metadata(
    *,
    mode: str,
    compare_range: str | None,
    changed_files: list[str],
    impacted_skill_count: int,
    scanned_skill_dirs: list[Path],
    repo_root: Path,
    total_skill_count: int,
) -> dict[str, object]:
    root = repo_root.resolve()
    scanned_skills: list[str] = []
    for skill_dir in scanned_skill_dirs:
        try:
            scanned_skills.append(skill_dir.resolve().relative_to(root).as_posix())
        except ValueError:
            scanned_skills.append(skill_dir.as_posix())
    scanned_skills.sort()
    return {
        "mode": mode,
        "compare_range": compare_range,
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "impacted_skill_count": impacted_skill_count,
        "scanned_skill_count": len(scanned_skill_dirs),
        "total_skill_count": total_skill_count,
        "scanned_skills": scanned_skills,
    }


def _render_ci_report(
    *,
    in_scope_findings: list[Finding],
    scan_metadata: dict[str, object],
    max_severity: str,
    tiers: tuple[str, ...] | None,
    verbose: bool,
) -> str:
    in_scope_totals = summarize_findings(in_scope_findings)
    policy_failed = _is_gate_failure(in_scope_findings, max_severity)
    scope_label = "all" if tiers is None else ",".join(tiers)
    result_label = "FAIL" if policy_failed else "PASS"
    lines = [
        "Skill Audit CI Gate",
        f"Result: {result_label}",
        f"Threshold: {max_severity}",
        f"Scope tiers: {scope_label}",
        f"Scan mode: {scan_metadata['mode']}",
        (
            f"Compare range: {scan_metadata['compare_range']}"
            if scan_metadata["compare_range"] is not None
            else "Compare range: working-tree (unstaged + staged + untracked)"
        ),
        f"Changed files considered: {scan_metadata['changed_file_count']}",
        (
            "Scanned skill directories: "
            f"{scan_metadata['scanned_skill_count']} "
            f"of {scan_metadata['total_skill_count']}"
        ),
        (
            "In-scope findings: "
            f"{len(in_scope_findings)} "
            f"(valid={in_scope_totals['valid']}, "
            f"warning={in_scope_totals['warning']}, "
            f"invalid={in_scope_totals['invalid']})"
        ),
    ]

    if verbose:
        lines.append("")
        lines.append("In-scope details:")
        if in_scope_findings:
            for finding in in_scope_findings:
                lines.append(
                    f"- [{finding.severity}] {finding.id} `{finding.path}`: "
                    f"{finding.message} | Fix: {finding.suggested_fix}"
                )
        else:
            lines.append("- None")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        parsed_tiers = _parse_gate_tiers(args.tiers)
        max_severity = _validate_ci_config(
            ci_mode=args.ci,
            max_severity=args.max_severity,
            max_severity_explicit=args.max_severity is not None,
            tiers=parsed_tiers,
            verbose_ci=args.verbose_ci,
        )
        _validate_scan_config(args.changed_files, args.compare_range)
    except ValueError as exc:
        print(f"runtime-error: {exc}", file=sys.stderr)
        return 2

    try:
        override_profile = load_override_profile(repo_root)
        all_skill_dirs = discover_skill_dirs(repo_root)
        changed_files: list[str] = []
        if args.changed_files:
            changed_files = discover_changed_files(repo_root, compare_range=args.compare_range)
            skill_dirs = filter_impacted_skill_dirs(
                all_skill_dirs,
                repo_root,
                changed_files,
            )
            scan_mode = "changed-files"
            impacted_skill_count = len(impacted_skill_keys(changed_files))
        else:
            skill_dirs = all_skill_dirs
            scan_mode = "full"
            impacted_skill_count = len(skill_dirs)

        scan_metadata = _build_scan_metadata(
            mode=scan_mode,
            compare_range=args.compare_range,
            changed_files=changed_files,
            impacted_skill_count=impacted_skill_count,
            scanned_skill_dirs=skill_dirs,
            repo_root=repo_root,
            total_skill_count=len(all_skill_dirs),
        )
        findings = []
        for skill_dir in skill_dirs:
            findings.extend(validate_skill_md(skill_dir, repo_root))
            findings.extend(validate_metadata_parity(skill_dir, repo_root))
            findings.extend(validate_local_references(skill_dir, repo_root))
    except (OSError, RuntimeError, OverrideConfigError) as exc:
        print(f"runtime-error: {exc}", file=sys.stderr)
        return 2

    ordered = sort_findings(apply_tier_policy(findings, override_profile=override_profile))
    index_payload = build_skill_index(
        skill_dirs=skill_dirs,
        findings=ordered,
        repo_root=repo_root,
        scan_metadata=scan_metadata,
    )
    markdown_payload = render_markdown_report(index_payload)
    totals = summarize_findings(ordered)

    json_out: Path | None = Path(args.json_out) if args.json_out else None
    markdown_out: Path | None = Path(args.markdown_out) if args.markdown_out else None

    if args.output_dir:
        output_dir = Path(args.output_dir)
        if json_out is None:
            json_out = output_dir / "skill-index.json"
        if markdown_out is None:
            markdown_out = output_dir / "skill-remediation.md"

    if json_out is not None:
        try:
            _write_text(json_out, json.dumps(index_payload, indent=2), args.force_overwrite)
            print(f"Wrote JSON index: {json_out}")
        except OSError as exc:
            print(f"runtime-error: {exc}", file=sys.stderr)
            return 2

    if markdown_out is not None:
        try:
            _write_text(markdown_out, markdown_payload, args.force_overwrite)
            print(f"Wrote markdown report: {markdown_out}")
        except OSError as exc:
            print(f"runtime-error: {exc}", file=sys.stderr)
            return 2

    if args.ci and max_severity is not None:
        in_scope_findings = _filter_findings_by_tier(ordered, parsed_tiers)
        policy_failed = _is_gate_failure(in_scope_findings, max_severity=max_severity)
        if args.json:
            print(json.dumps(index_payload, indent=2))
        else:
            print(
                _render_ci_report(
                    in_scope_findings=in_scope_findings,
                    scan_metadata=scan_metadata,
                    max_severity=max_severity,
                    tiers=parsed_tiers,
                    verbose=args.verbose_ci,
                )
            )
        return 1 if policy_failed else 0

    if args.json:
        print(json.dumps(index_payload, indent=2))
    else:
        print(
            render_report(
                ordered,
                scanned_skill_count=len(skill_dirs),
                scan_metadata=scan_metadata,
            )
        )

    return 1 if totals["invalid"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
