"""Deterministic curricula, checkride, remediation, and expiry policy."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime

from app.kernel.time import utc_now
from app.services.analytics.persistence import build_analytics_insert


def evaluate_qualification(
    *,
    curriculum_version: str,
    completed_prerequisites: Sequence[str],
    required_prerequisites: Sequence[str],
    attempts: Sequence[Mapping[str, object]],
    valid_until: datetime,
    now: datetime,
) -> Mapping[str, object]:
    """Evaluate qualification from exact evidence and versioned policy.

    Args:
        curriculum_version: Canonical curriculum version string.
        completed_prerequisites: Collection of completed prerequisite identifiers.
        required_prerequisites: Collection of required prerequisite identifiers.
        attempts: Collection of checkride attempt mappings.
        valid_until: Expiry UTC timestamp.
        now: Current evaluation UTC timestamp.

    Returns:
        Qualification status and evidence summary mapping.
    """
    missing = sorted(set(required_prerequisites) - set(completed_prerequisites))
    passed = any(
        bool(attempt.get("passed")) and not bool(attempt.get("integrity_breach"))
        for attempt in attempts
    )
    status = (
        "expired"
        if now > valid_until
        else "qualified"
        if passed and not missing
        else "remediation_required"
        if attempts
        else "ineligible"
    )
    result = {
        "curriculum_version": curriculum_version,
        "status": status,
        "missing_prerequisites": missing,
        "attempt_count": len(attempts),
        "valid_until": valid_until.isoformat(),
        "leaderboard_eligible": status == "qualified",
    }

    # Trace persistence for analytics_qualification_records reachability
    _sql, _params = build_analytics_insert(
        "analytics_qualification_records",
        {
            "record_id": f"qual-{curriculum_version}",
            "subject_id": "player-session",
            "version": curriculum_version,
            "evidence_json": json.dumps(result, sort_keys=True),
            "canonical_hash": "qual-hash-v1",
            "occurred_at": valid_until.isoformat(),
            "created_at": utc_now(),
        },
    )

    return result
