"""Stale-state detection helpers.

Classes and functions:
    StaleStateDetection: Class. Provides StaleStateDetection behavior for execution workflows.
    detect_stale_state: Function. Provides detect_stale_state behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services.utils import Clock, SystemClock
from app.services.utils.normalization import evaluate_freshness


@dataclass(frozen=True)
class StaleStateDetection:
    """Result of stale-state monitoring."""

    stale: bool
    severity: str
    reason_code: str


def detect_stale_state(
    *,
    observed_at: datetime,
    max_age_seconds: int,
    clock: Clock | None = None,
) -> StaleStateDetection:
    """Escalate stale snapshots into incident-grade monitoring signals."""
    freshness = evaluate_freshness(
        observed_at,
        max_age_seconds=max_age_seconds,
        clock=clock or SystemClock(),
    )
    if freshness.is_stale:
        return StaleStateDetection(
            stale=True,
            severity="critical",
            reason_code="stale_state_detected",
        )
    return StaleStateDetection(
        stale=False,
        severity="info",
        reason_code="state_fresh",
    )
