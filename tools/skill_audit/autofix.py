"""Dry-run autofix suggestion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .findings import Finding


@dataclass(frozen=True)
class AutofixSuggestion:
    """Normalized dry-run suggestion for a finding."""

    rule_id: str
    severity: str
    path: str
    supported: bool
    reason: str
    suggested_change: str
    preview: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "supported": self.supported,
            "reason": self.reason,
            "suggested_change": self.suggested_change,
            "preview": self.preview,
        }


def _unsupported_suggestion(finding: Finding) -> AutofixSuggestion:
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=False,
        reason="No deterministic dry-run suggestion is defined for this rule.",
        suggested_change=(
            "Review the finding details and apply a manual fix using the rule's "
            "suggested_fix guidance."
        ),
        preview=None,
    )


def _suggest_meta_001(finding: Finding) -> AutofixSuggestion:
    preview = (
        "---\n"
        "name: <skill-name>\n"
        "description: <skill-description>\n"
        "---\n"
    )
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=True,
        reason="SKILL.md is missing and blocks metadata validation.",
        suggested_change="Create SKILL.md with required frontmatter keys `name` and `description`.",
        preview=preview,
    )


def _suggest_meta_00x_frontmatter(finding: Finding) -> AutofixSuggestion:
    preview = (
        "---\n"
        "name: <skill-name>\n"
        "description: <skill-description>\n"
        "---\n"
    )
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=True,
        reason="Frontmatter structure is invalid or incomplete.",
        suggested_change="Repair YAML frontmatter and include non-empty `name` and `description` values.",
        preview=preview,
    )


def _suggest_meta_101_102(finding: Finding) -> AutofixSuggestion:
    counterpart = "agents/openai.yaml" if finding.id == "META-101" else "SKILL.md"
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=True,
        reason="Skill package metadata counterparts must exist in pairs.",
        suggested_change=f"Create missing `{counterpart}` and align metadata fields with its counterpart.",
        preview=None,
    )


def _suggest_meta_110(finding: Finding) -> AutofixSuggestion:
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=True,
        reason="Metadata fields differ between SKILL.md and agents/openai.yaml.",
        suggested_change="Update one side so `name` and `description` values match exactly.",
        preview=None,
    )


def _suggest_meta_201(finding: Finding) -> AutofixSuggestion:
    return AutofixSuggestion(
        rule_id=finding.id,
        severity=finding.severity,
        path=finding.path,
        supported=True,
        reason="A referenced local file path does not resolve.",
        suggested_change="Create the missing local path or update the reference to an existing file.",
        preview=None,
    )


_SUGGESTION_BUILDERS: dict[str, Callable[[Finding], AutofixSuggestion]] = {
    "META-001": _suggest_meta_001,
    "META-002": _suggest_meta_00x_frontmatter,
    "META-003": _suggest_meta_00x_frontmatter,
    "META-004": _suggest_meta_00x_frontmatter,
    "META-005": _suggest_meta_00x_frontmatter,
    "META-101": _suggest_meta_101_102,
    "META-102": _suggest_meta_101_102,
    "META-110": _suggest_meta_110,
    "META-201": _suggest_meta_201,
}


def build_autofix_suggestions(findings: Iterable[Finding]) -> list[AutofixSuggestion]:
    """Return deterministic dry-run suggestions for non-valid findings."""
    ordered = sorted(findings, key=lambda item: item.as_sort_key())
    suggestions: list[AutofixSuggestion] = []
    for finding in ordered:
        if finding.severity == "valid":
            continue
        builder = _SUGGESTION_BUILDERS.get(finding.id)
        suggestions.append(builder(finding) if builder is not None else _unsupported_suggestion(finding))
    return suggestions


def summarize_autofix_suggestions(
    suggestions: Iterable[AutofixSuggestion],
) -> dict[str, object]:
    """Summarize supported/unsupported suggestion totals."""
    rows = list(suggestions)
    warning_count = sum(1 for row in rows if row.severity == "warning")
    invalid_count = sum(1 for row in rows if row.severity == "invalid")
    supported_count = sum(1 for row in rows if row.supported)
    unsupported_count = len(rows) - supported_count
    return {
        "total": len(rows),
        "supported": supported_count,
        "unsupported": unsupported_count,
        "severity_totals": {
            "warning": warning_count,
            "invalid": invalid_count,
        },
    }


def render_autofix_text(suggestions: Iterable[AutofixSuggestion]) -> str:
    """Render plain-text dry-run suggestions."""
    rows = list(suggestions)
    summary = summarize_autofix_suggestions(rows)

    lines = [
        "Autofix Suggestions (dry-run)",
        f"- total: {summary['total']}",
        f"- supported: {summary['supported']}",
        f"- unsupported: {summary['unsupported']}",
        (
            "- severity totals: "
            f"warning={summary['severity_totals']['warning']}, "
            f"invalid={summary['severity_totals']['invalid']}"
        ),
    ]

    if not rows:
        lines.append("- no non-valid findings available for suggestions")
        return "\n".join(lines)

    lines.append("- suggestions:")
    for row in rows:
        support_label = "supported" if row.supported else "unsupported"
        lines.append(
            f"  - [{support_label}] {row.rule_id} `{row.path}`: {row.reason}"
        )
        lines.append(f"    - Suggested change: {row.suggested_change}")
        if row.preview:
            lines.append(f"    - Preview: {row.preview.replace(chr(10), ' | ')}")

    return "\n".join(lines)


def render_autofix_markdown(suggestions: Iterable[AutofixSuggestion]) -> str:
    """Render markdown dry-run suggestion report."""
    rows = list(suggestions)
    summary = summarize_autofix_suggestions(rows)

    lines = [
        "# Skill Audit Autofix Suggestions (Dry-Run)",
        "",
        "## Summary",
        f"- Total suggestions: {summary['total']}",
        f"- Supported: {summary['supported']}",
        f"- Unsupported: {summary['unsupported']}",
        (
            "- Severity totals: "
            f"warning={summary['severity_totals']['warning']}, "
            f"invalid={summary['severity_totals']['invalid']}"
        ),
    ]

    if not rows:
        lines.extend(["", "No dry-run suggestions generated."])
        return "\n".join(lines)

    lines.extend(["", "## Suggestions"])
    for row in rows:
        support_label = "supported" if row.supported else "unsupported"
        lines.extend(
            [
                "",
                f"### `{row.rule_id}` `{row.path}`",
                f"- Status: {support_label}",
                f"- Reason: {row.reason}",
                f"- Suggested change: {row.suggested_change}",
            ]
        )
        if row.preview:
            lines.extend(["- Preview:", "```text", row.preview.rstrip(), "```"])

    return "\n".join(lines)
