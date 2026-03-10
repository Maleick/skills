#!/usr/bin/env python3
"""Shared protocol constants and validation helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

ALLOWED_STATES = ("inbox", "assigned", "in_progress", "review", "done", "failed")
ALLOWED_ROLES = ("Orchestrator", "Builder", "Reviewer", "Ops")

ALLOWED_TRANSITIONS = {
    ("inbox", "assigned"),
    ("assigned", "in_progress"),
    ("in_progress", "review"),
    ("review", "done"),
    ("review", "failed"),
}

TRANSITION_AUTHORITY: dict[tuple[str, str], set[str]] = {
    ("inbox", "assigned"): {"Orchestrator"},
    ("assigned", "in_progress"): {"Builder"},
    ("in_progress", "review"): {"Builder"},
    ("review", "done"): {"Reviewer"},
    ("review", "failed"): {"Reviewer"},
}

RUNTIME_COUPLED_PATTERNS = [
    re.compile(r"\bopenclaw\b", re.IGNORECASE),
    re.compile(r"\bdiscord\b", re.IGNORECASE),
    re.compile(r"\bsessions_send\b", re.IGNORECASE),
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso8601(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def isoformat_utc(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_runtime_coupled(text: str | None) -> bool:
    sample = (text or "").strip()
    if not sample:
        return False
    return any(pattern.search(sample) for pattern in RUNTIME_COUPLED_PATTERNS)


def deterministic_claim_owner(worker_ids: list[str]) -> str | None:
    ids = sorted(worker_id.strip() for worker_id in worker_ids if worker_id and worker_id.strip())
    return ids[0] if ids else None


def validate_task_card_semantics(task_card: dict[str, Any], *, now: datetime | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ts_now = now or now_utc()

    state = str(task_card.get("state", "")).strip()
    claimed_until_raw = task_card.get("claimed_until")

    created_at_raw = task_card.get("created_at")
    updated_at_raw = task_card.get("updated_at")

    created_at = None
    updated_at = None
    try:
        created_at = parse_iso8601(created_at_raw)
    except Exception as exc:
        errors.append(f"created_at is not valid date-time: {exc}")
    try:
        updated_at = parse_iso8601(updated_at_raw)
    except Exception as exc:
        errors.append(f"updated_at is not valid date-time: {exc}")

    if created_at and updated_at and updated_at < created_at:
        errors.append("updated_at must be >= created_at")

    parsed_claimed_until = None
    if claimed_until_raw is not None:
        try:
            parsed_claimed_until = parse_iso8601(str(claimed_until_raw))
        except Exception as exc:
            errors.append(f"claimed_until is not valid date-time: {exc}")

    if state == "in_progress":
        if parsed_claimed_until is None:
            errors.append("in_progress task requires non-null claimed_until")
        elif parsed_claimed_until <= ts_now:
            errors.append("in_progress task requires non-expired claimed_until")
    elif parsed_claimed_until and parsed_claimed_until <= ts_now:
        warnings.append("claimed_until is expired for non-in_progress task")

    owner_role = str(task_card.get("owner_role", "")).strip()
    if owner_role not in ALLOWED_ROLES:
        errors.append(f"owner_role must be one of {', '.join(ALLOWED_ROLES)}")

    if state not in ALLOWED_STATES:
        errors.append(f"state must be one of {', '.join(ALLOWED_STATES)}")

    verification = task_card.get("verification") or []
    if isinstance(verification, list):
        for index, row in enumerate(verification):
            if not isinstance(row, dict):
                errors.append(f"verification[{index}] must be an object")
                continue
            command = str(row.get("command", "")).strip()
            if not command:
                errors.append(f"verification[{index}].command must be non-empty")
            if is_runtime_coupled(command):
                warnings.append(f"verification[{index}] contains runtime-coupled command text")

    next_action = str(task_card.get("next_action", "")).strip()
    if is_runtime_coupled(next_action):
        warnings.append("next_action contains runtime-coupled content")

    return errors, warnings


def validate_transition(
    *,
    from_state: str,
    to_state: str,
    actor_role: str,
    actor_id: str | None = None,
    author_id: str | None = None,
    claimed_until: str | None = None,
    now: datetime | None = None,
    adapter_mode: bool = False,
    allow_runtime_coupled: bool = False,
    runtime_text: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ts_now = now or now_utc()

    source = from_state.strip()
    target = to_state.strip()
    role = actor_role.strip()
    actor = (actor_id or "").strip()
    author = (author_id or "").strip()

    if source not in ALLOWED_STATES:
        errors.append(f"from-state '{source}' is invalid")
    if target not in ALLOWED_STATES:
        errors.append(f"to-state '{target}' is invalid")
    if role not in ALLOWED_ROLES:
        errors.append(f"actor-role '{role}' is invalid")

    transition = (source, target)
    if transition not in ALLOWED_TRANSITIONS:
        errors.append(f"transition {source} -> {target} is not allowed")

    allowed_roles = TRANSITION_AUTHORITY.get(transition)
    if allowed_roles and role not in allowed_roles:
        allowed_display = ", ".join(sorted(allowed_roles))
        errors.append(
            f"actor role '{role}' is not authorized for {source} -> {target}; expected one of: {allowed_display}"
        )

    if source == "review" and target in {"done", "failed"} and actor and author and actor == author:
        errors.append("self-approval is not allowed: actor_id must differ from author_id")

    parsed_claimed_until = None
    if claimed_until is not None and str(claimed_until).strip() not in {"", "null", "None"}:
        try:
            parsed_claimed_until = parse_iso8601(claimed_until)
        except Exception as exc:
            errors.append(f"claimed_until is not valid date-time: {exc}")

    if source == "in_progress":
        if parsed_claimed_until is None:
            errors.append("transition from in_progress requires claimed_until")
        elif parsed_claimed_until <= ts_now:
            errors.append("transition from in_progress requires non-expired claimed_until")

    if adapter_mode and not allow_runtime_coupled and is_runtime_coupled(runtime_text):
        errors.append("runtime-coupled command/reference blocked in adapter mode")

    if adapter_mode and not runtime_text:
        warnings.append("adapter-mode enabled with no runtime text provided")

    return {
        "allowed": len(errors) == 0,
        "from_state": source,
        "to_state": target,
        "actor_role": role,
        "actor_id": actor,
        "author_id": author,
        "adapter_mode": adapter_mode,
        "allow_runtime_coupled": allow_runtime_coupled,
        "runtime_text": runtime_text or "",
        "checked_at": isoformat_utc(ts_now),
        "errors": errors,
        "warnings": warnings,
    }
