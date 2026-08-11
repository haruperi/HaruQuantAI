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

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.utils import generate_id

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
    """Return True when ``impact`` is at least ``minimum`` (or no minimum).

    Args:
        impact: The ``impact`` argument.
        minimum: The ``minimum`` argument.

    Returns:
        The result produced by the operation.
    """
    if minimum is None:
        return True
    return impact >= minimum


def _evaluate_calendar_state_raw(
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


def evaluate_calendar_state(
    events: list[EconomicEvent],
    at: datetime,
    *,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
) -> StandardResponse[str]:
    """Return the canonical calendar state for ``at`` given the supplied events.

    Args:
        events: Relevant economic events for the queried scope.
        at: Timezone-aware UTC instant.
        before_minutes: Blackout window applied before each event release.
        after_minutes: Blackout window applied after each event release.
        minimum_impact: Ignore events strictly below this impact level.

    Returns:
        Standard response carrying one of ``"event"``, ``"blackout_before"``,
        ``"blackout_after"``, or ``"open"``.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when ``at`` is timezone-naive or the
            minute windows are negative.
    """

    def _raw() -> str:
        """Evaluate the calendar state and translate validation failures.

        Returns:
            The point-in-time calendar state.

        Raises:
            DataError: If the calendar-state inputs are invalid.
        """
        try:
            return _evaluate_calendar_state_raw(
                events,
                at,
                before_minutes=before_minutes,
                after_minutes=after_minutes,
                minimum_impact=minimum_impact,
            )
        except ValueError as error:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "calendar_state"},
            ) from error

    return run_data_operation(
        operation="data.economic_calendar.evaluate_calendar_state",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=_raw,
    )


def _is_news_restricted_events_raw(
    events: list[EconomicEvent],
    at: datetime,
    *,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact | None = None,
) -> bool:
    """Return True when ``at`` falls inside any event's blackout window.

    Pure-flag analogue of ``is_news_restricted`` and the canonical Risk
    calendar gate: returns ``True`` for any blocking state and ``False`` only
    for ``open``. The ``unknown`` (empty-events) case is excluded from blocking
    by this helper; callers decide their own missing-evidence policy.

    Args:
        events: The ``events`` argument.
        at: The ``at`` argument.
        minutes_before: The ``minutes_before`` argument.
        minutes_after: The ``minutes_after`` argument.
        minimum_impact: The ``minimum_impact`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If ``at`` is timezone-naive or blackout minutes negative.
    """
    state = _evaluate_calendar_state_raw(
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


def is_news_restricted_events(
    events: list[EconomicEvent],
    at: datetime,
    *,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact | None = None,
) -> StandardResponse[bool]:
    """Return True when ``at`` falls inside any event's blackout window.

    Args:
        events: Relevant economic events for the queried scope.
        at: Timezone-aware UTC instant.
        minutes_before: Blackout minutes before each release.
        minutes_after: Blackout minutes after each release.
        minimum_impact: Ignore events strictly below this impact level.

    Returns:
        Standard response carrying ``True`` when ``at`` is inside an event
        release window or adjacent blackout; ``False`` otherwise.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when ``at`` is timezone-naive or the
            blackout minutes are negative.
    """

    def _raw() -> bool:
        """Evaluate the news restriction and translate validation failures.

        Returns:
            Whether the supplied instant is news restricted.

        Raises:
            DataError: If the restriction inputs are invalid.
        """
        try:
            return _is_news_restricted_events_raw(
                events,
                at,
                minutes_before=minutes_before,
                minutes_after=minutes_after,
                minimum_impact=minimum_impact,
            )
        except ValueError as error:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "news_restriction"},
            ) from error

    return run_data_operation(
        operation="data.economic_calendar.is_news_restricted_events",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = [
    "CALENDAR_STATE_BLACKOUT_AFTER",
    "CALENDAR_STATE_BLACKOUT_BEFORE",
    "CALENDAR_STATE_EVENT",
    "CALENDAR_STATE_OPEN",
    "CALENDAR_STATE_UNKNOWN",
    "evaluate_calendar_state",
    "is_news_restricted_events",
]
