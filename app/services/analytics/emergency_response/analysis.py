"""Emergency lifecycle timing and survival analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime


def analyze_emergency_response(
    events: Sequence[Mapping[str, object]], *, required_sequence: Sequence[str]
) -> Mapping[str, object]:
    """Analyze only recorded Simulator emergency lifecycle evidence.

    Returns:
        Emergency sequence and timing evidence.
    """
    ordered = sorted(events, key=lambda item: str(item.get("occurred_at", "")))
    kinds = [str(item.get("kind")) for item in ordered]
    timestamps = {
        str(item.get("kind")): datetime.fromisoformat(str(item["occurred_at"]))
        for item in ordered
        if item.get("occurred_at")
    }
    perceived = timestamps.get("perceived")
    resolved = timestamps.get("resolved")
    duration = (
        None
        if perceived is None or resolved is None
        else (resolved - perceived).total_seconds()
    )
    return {
        "sequence_status": "complete"
        if all(kind in kinds for kind in required_sequence)
        else "incomplete",
        "required_sequence": list(required_sequence),
        "observed_sequence": kinds,
        "resolution_seconds": duration,
        "survival": next(
            (item.get("survival") for item in reversed(ordered) if "survival" in item),
            None,
        ),
    }
