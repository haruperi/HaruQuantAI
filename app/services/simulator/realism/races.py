"""Total ordering for cancel, replace, and fill races."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType


def resolve_cancel_replace_race(
    *,
    fill_at: datetime | None,
    cancel_at: datetime | None,
    replace_at: datetime | None,
) -> Mapping[str, object]:
    """Resolve an execution race using venue-safe total priority.

    Args:
        fill_at: Optional venue fill timestamp.
        cancel_at: Optional venue cancel-accept timestamp.
        replace_at: Optional venue replace-accept timestamp.

    Returns:
        Immutable winning action and ordered evidence. At equal timestamps the
        irreversible venue fill wins, followed by cancel, then replace.

    Raises:
        ValueError: If no event exists or any timestamp is naive.
    """
    events = [
        ("FILL", fill_at, 0),
        ("CANCEL", cancel_at, 1),
        ("REPLACE", replace_at, 2),
    ]
    present = [
        (name, value, priority) for name, value, priority in events if value is not None
    ]
    if not present:
        raise ValueError("at least one race timestamp is required")
    if any(
        value.tzinfo is None or value.utcoffset() is None for _, value, _ in present
    ):
        raise ValueError("race timestamps must be timezone-aware")
    ordered = sorted(present, key=lambda item: (item[1], item[2]))
    return MappingProxyType(
        {
            "winner": ordered[0][0],
            "ordered_actions": tuple(item[0] for item in ordered),
            "resolved_at": ordered[0][1],
        }
    )


__all__ = ["resolve_cancel_replace_race"]
