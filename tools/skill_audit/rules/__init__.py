"""Rule pack exports."""

from .parity import validate_metadata_parity
from .references import validate_local_references
from .skill_md import validate_skill_md

# Canonical built-in rules implemented by this validator.
BUILTIN_RULE_IDS: frozenset[str] = frozenset(
    {
        "META-000",
        "META-001",
        "META-002",
        "META-003",
        "META-004",
        "META-005",
        "META-100",
        "META-101",
        "META-102",
        "META-103",
        "META-104",
        "META-110",
        "META-200",
        "META-201",
    }
)

__all__ = [
    "BUILTIN_RULE_IDS",
    "validate_metadata_parity",
    "validate_local_references",
    "validate_skill_md",
]
