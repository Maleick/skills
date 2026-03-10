"""Typed findings model used by audit rules and reporting."""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_SEVERITIES: tuple[str, ...] = ("valid", "warning", "invalid")


@dataclass(frozen=True)
class Finding:
    """Normalized finding payload for validator output."""

    id: str
    severity: str
    path: str
    message: str
    suggested_fix: str

    def __post_init__(self) -> None:
        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Unsupported severity '{self.severity}'. "
                f"Expected one of: {', '.join(ALLOWED_SEVERITIES)}"
            )

        for field_name in ("id", "path", "message", "suggested_fix"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Finding field '{field_name}' must be a non-empty string")

    def as_sort_key(self) -> tuple[str, str, str, str]:
        return (self.path, self.id, self.severity, self.message)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }
