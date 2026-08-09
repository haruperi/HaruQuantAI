"""Deterministic curricula, checkride, remediation, and expiry policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime


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

    Returns:
        Qualification status and evidence summary.
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
    return {
        "curriculum_version": curriculum_version,
        "status": status,
        "missing_prerequisites": missing,
        "attempt_count": len(attempts),
        "valid_until": valid_until.isoformat(),
        "leaderboard_eligible": status == "qualified",
    }
