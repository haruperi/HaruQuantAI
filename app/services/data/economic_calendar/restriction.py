"""Pure news-restriction evaluation for FEAT-DATA-11.

This module owns the deterministic mapping from a normalized set of
`EconomicEvent` values (at one symbol) to the normalized ``calendar_state``
string consumed by the Risk domain calendar gate. It has no I/O: callers
supply the relevant events and receive one of the canonical states.

Risk's ``MarketContextEvidence.calendar_state`` expects values drawn from
``"blackout_before"``, ``"event"``, ``"blackout_after"``, plus the inert
``"open"``. Missing calendar evidence is represented by the Data composition
layer as ``"unknown"`` rather than by an empty successful query.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from app.services.data.economic_calendar.events import EconomicEvent, EventImpact

#: Canonical normalized calendar states. ``"unknown"`` is reserved for the
#: composition layer when calendar evidence was not acquired.
CALENDAR_STATE_EVENT: Final[str] = "event"
CALENDAR_STATE_BLACKOUT_BEFORE: Final[str] = "blackout_before"
CALENDAR_STATE_BLACKOUT_AFTER: Final[str] = "blackout_after"
CALENDAR_STATE_OPEN: Final[str] = "open"
CALENDAR_STATE_UNKNOWN: Final[str] = "unknown"


def _meets_minimum(impact: EventImpact, minimum: EventImpact | None) -> bool:
    """Return True when ``impact`` is at least ``minimum`` (or no minimum)."""
    if minimum is None:
        return True
    return impact >= minimum


def evaluate_calendar_state(
    events: list[EconomicEvent],
    at: datetime,
    *,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
) -> str:
    """Return the canonical calendar state for ``at`` given the supplied events.

    Precedence is release-time-then-state: an event whose release window
    contains ``at`` wins over any adjacent blackout. If multiple events are
    simultaneously relevant, the most restrictive state (``event`` before any
    blackout) wins.

    Args:
        events: Relevant economic events for the queried scope (caller is
            responsible for symbol filtering).
        at: Timezone-aware UTC instant. A naive datetime raises ``ValueError``.
        before_minutes: Blackout window applied before each event release.
        after_minutes: Blackout window applied after each event release.
        minimum_impact: Ignore events strictly below this impact level.

    Returns:
        One of ``"event"``, ``"blackout_before"``, ``"blackout_after"``,
        or ``"open"``.

    Raises:
        ValueError: If ``at`` is timezone-naive, or the minute windows are
            negative.
    """
    if at.tzinfo is None:
        raise ValueError("at must be timezone-aware")
    if before_minutes < 0 or after_minutes < 0:
        raise ValueError("blackout minutes must be non-negative")

    candidates = [
        event for event in events if _meets_minimum(event.impact, minimum_impact)
    ]
    if not candidates:
        return CALENDAR_STATE_OPEN

    before = timedelta(minutes=before_minutes)
    after = timedelta(minutes=after_minutes)

    state = CALENDAR_STATE_OPEN
    for event in candidates:
        scheduled = event.scheduled_at
        if scheduled == at:
            return CALENDAR_STATE_EVENT
        if scheduled - before <= at < scheduled:
            state = CALENDAR_STATE_BLACKOUT_BEFORE
            continue
        if scheduled < at <= scheduled + after:
            state = CALENDAR_STATE_BLACKOUT_AFTER
    return state


def is_news_restricted_events(
    events: list[EconomicEvent],
    at: datetime,
    *,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact | None = None,
) -> bool:
    """Return True when ``at`` falls inside any event's blackout window.

    This is the pure-flag analogue of ``is_news_restricted`` and the canonical
    Risk calendar gate: returns ``True`` for any blocking state
    (``event``, ``blackout_before``, ``blackout_after``) and ``False`` only
    for ``open``. The ``unknown`` (empty-events) case is excluded from blocking
    by this pure helper; callers decide their own missing-evidence policy.

    Args:
        events: Relevant economic events for the queried scope.
        at: Timezone-aware UTC instant.
        minutes_before: Blackout minutes before each release.
        minutes_after: Blackout minutes after each release.
        minimum_impact: Ignore events strictly below this impact level.

    Returns:
        ``True`` when ``at`` is inside an event release window or adjacent
        blackout; ``False`` otherwise.

    Raises:
        ValueError: If ``at`` is timezone-naive or blackout minutes negative.
    """
    state = evaluate_calendar_state(
        events,
        at,
        before_minutes=minutes_before,
        after_minutes=minutes_after,
        minimum_impact=minimum_impact,
    )
    return state in {
        CALENDAR_STATE_EVENT,
        CALENDAR_STATE_BLACKOUT_BEFORE,
        CALENDAR_STATE_BLACKOUT_AFTER,
    }


__all__ = [
    "CALENDAR_STATE_BLACKOUT_AFTER",
    "CALENDAR_STATE_BLACKOUT_BEFORE",
    "CALENDAR_STATE_EVENT",
    "CALENDAR_STATE_OPEN",
    "CALENDAR_STATE_UNKNOWN",
    "evaluate_calendar_state",
    "is_news_restricted_events",
]
