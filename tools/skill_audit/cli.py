"""CLI entrypoint for repository skill audit scans."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .indexing import build_skill_index
from .markdown_report import render_markdown_report
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
    return parser


def _write_text(path: Path, content: str, force_overwrite: bool) -> None:
    if path.exists() and not force_overwrite:
        raise FileExistsError(f"Output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    index_payload = build_skill_index(skill_dirs=skill_dirs, findings=ordered, repo_root=repo_root)
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

    if args.json:
        print(json.dumps(index_payload, indent=2))
    else:
        print(render_report(ordered, scanned_skill_count=len(skill_dirs)))

    return 1 if totals["invalid"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
