"""Classification of a temporal gap as expected or anomalous.

A missing bar is not automatically a defect. Markets close on weekends, at session
boundaries, and on holidays, and a detector that reports every closure as missing data
is worse than useless — it trains operators to ignore quality evidence.

This module separates the two. ``classify_gap`` answers whether a gap falls inside a
declared non-trading window; ``quality/adversarial.detect_unexpected_gaps`` uses it to
report only the gaps that need explaining.

**Reconciliation is not here.** ``feeds/runtime.reconcile_feed_gap`` mutates live feed
state — buffer counters, last error, gap count — which is feed lifecycle rather than
temporal truth. Hosting it in ``time`` would put runtime state in the layer everything
else depends on. It stays with feeds.

Classification is pure: it reads no clock and performs no I/O, so the same gap and the
same session rules always classify identically.
"""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

from app.utils import logger

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from app.services.data.time_sessions.contracts import SessionWindow

__all__ = [
    "GapType",
    "classify_gap",
]

# Saturday and Sunday in `datetime.weekday()` terms.
_WEEKEND_DAYS = frozenset({5, 6})


def _is_weekend_interval(gap_start: datetime, gap_end: datetime) -> bool:
    """Report whether a half-open gap contains weekend time only.

    Args:
        gap_start: First missing moment, aware UTC.
        gap_end: First observed moment after the gap, aware UTC.

    Returns:
        ``True`` when every instant in ``[gap_start, gap_end)`` is on Saturday or
        Sunday.
    """
    cursor = gap_start
    while cursor < gap_end:
        if cursor.weekday() not in _WEEKEND_DAYS:
            return False
        next_midnight = (cursor + timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        cursor = min(next_midnight, gap_end)
    return True


class GapType(StrEnum):
    """Why a stretch of missing observations exists.

    Attributes:
        EXPECTED_WEEKEND: The gap falls entirely on a weekend.
        EXPECTED_SESSION_BREAK: The gap falls outside every declared session window.
        UNEXPECTED: The gap overlaps a window where trading was expected.
        UNVERIFIED: No session evidence was supplied, so the gap cannot be classified.
    """

    EXPECTED_WEEKEND = "EXPECTED_WEEKEND"
    EXPECTED_SESSION_BREAK = "EXPECTED_SESSION_BREAK"
    UNEXPECTED = "UNEXPECTED"
    UNVERIFIED = "UNVERIFIED"


def _overlaps_any_session(
    gap_start: datetime, gap_end: datetime, sessions: Sequence[SessionWindow]
) -> bool:
    """Report whether a gap interval overlaps any declared session window.

    The gap is the half-open interval ``[gap_start, gap_end)``: ``gap_end`` is the first
    observation *after* the gap, so it is not itself missing. Testing the endpoints for
    membership instead of testing the interval for overlap would misclassify a gap that
    ends exactly when a session opens — the moment trading resumed would be read as
    proof that trading had been expected throughout.

    Args:
        gap_start: First missing moment, aware UTC.
        gap_end: First observation after the gap, aware UTC.
        sessions: Declared session windows.

    Returns:
        ``True`` when any session was open during the gap.
    """
    return any(
        session.opens_at < gap_end and session.closes_at > gap_start
        for session in sessions
    )


def classify_gap(
    gap_start: datetime,
    gap_end: datetime,
    sessions: Sequence[SessionWindow] | None = None,
) -> GapType:
    """Classify one gap against declared session windows.

    Weekend-only intervals are inherently classified as ``EXPECTED_WEEKEND``. For
    every other gap, the function returns ``UNVERIFIED`` rather than guessing when no
    session evidence is supplied. That distinction matters: an unverified gap is not
    the same as a gap known to be benign.

    Args:
        gap_start: Aware UTC timestamp of the first missing moment.
        gap_end: Aware UTC timestamp of the first observation after the gap.
        sessions: Declared session windows covering the gap period. ``None`` or empty
            means no evidence is available.

    Returns:
        The gap classification.

    Raises:
        ValueError: If ``gap_end`` does not follow ``gap_start``.
    """
    logger.debug("Classifying a temporal gap")
    if gap_end <= gap_start:
        raise ValueError("gap_end must follow gap_start")

    if _is_weekend_interval(gap_start, gap_end):
        return GapType.EXPECTED_WEEKEND

    if not sessions:
        return GapType.UNVERIFIED

    # A gap is expected when no declared session was open at any point during it.
    if _overlaps_any_session(gap_start, gap_end, sessions):
        return GapType.UNEXPECTED
    return GapType.EXPECTED_SESSION_BREAK
