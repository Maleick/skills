"""CLI entrypoint for repository skill audit scans."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .policy import apply_tier_policy
from .reporting import render_report, sort_findings, summarize_findings
from .rules import validate_local_references, validate_metadata_parity, validate_skill_md
from .scanner import discover_skill_dirs


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
        "--json",
        action="store_true",
        help="Emit report as JSON instead of text.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        skill_dirs = discover_skill_dirs(repo_root)
        findings = []
        for skill_dir in skill_dirs:
            findings.extend(validate_skill_md(skill_dir, repo_root))
            findings.extend(validate_metadata_parity(skill_dir, repo_root))
            findings.extend(validate_local_references(skill_dir, repo_root))
    except OSError as exc:
        print(f"runtime-error: {exc}", file=sys.stderr)
        return 2

    ordered = sort_findings(apply_tier_policy(findings))
    totals = summarize_findings(ordered)

    if args.json:
        payload = {
            "scanned_skill_count": len(skill_dirs),
            "severity_totals": totals,
            "findings": [finding.to_dict() for finding in ordered],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(render_report(ordered, scanned_skill_count=len(skill_dirs)))

    return 1 if totals["invalid"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
