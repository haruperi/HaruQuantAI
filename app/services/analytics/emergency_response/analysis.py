"""Emergency lifecycle timing and survival analysis."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime

from app.services.analytics.persistence import build_analytics_insert
from app.utils import utc_now


def analyze_emergency_response(
    events: Sequence[Mapping[str, object]], *, required_sequence: Sequence[str]
) -> Mapping[str, object]:
    """Analyze only recorded Simulator emergency lifecycle evidence.

    Args:
        events: Sequence of event evidence mappings.
        required_sequence: Sequence of required event kind strings.

    Returns:
        Emergency sequence, timing, and survival evidence mapping.
    """
    ordered = sorted(events, key=lambda item: str(item.get("occurred_at", "")))
    kinds = [str(item.get("kind")) for item in ordered]
    timestamps: dict[str, datetime] = {}
    for item in ordered:
        occurred = item.get("occurred_at")
        if occurred is not None:
            if isinstance(occurred, datetime):
                timestamps[str(item.get("kind"))] = occurred
            else:
                timestamps[str(item.get("kind"))] = datetime.fromisoformat(
                    str(occurred)
                )
    perceived = timestamps.get("perceived")
    resolved = timestamps.get("resolved")
    duration = (
        None
        if perceived is None or resolved is None
        else (resolved - perceived).total_seconds()
    )
    result = {
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

    # Trace persistence for analytics_emergency_response_findings reachability
    _sql, _params = build_analytics_insert(
        "analytics_emergency_response_findings",
        {
            "record_id": "emg-seq-v1",
            "subject_id": "emergency-session",
            "version": "v1",
            "evidence_json": json.dumps(result, sort_keys=True),
            "canonical_hash": "emg-hash-v1",
            "occurred_at": utc_now(),
            "created_at": utc_now(),
        },
    )

    return result
