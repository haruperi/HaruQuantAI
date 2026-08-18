"""Research-only qualification of market gaps from persisted holiday events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.services.data.economic_calendar.profiling import (
    _get_symbol_event_profile_raw,
)
from app.services.data.economic_calendar.store import EconomicEventStore


@dataclass(frozen=True, slots=True)
class CalendarClosureEvidence:
    """One non-authoritative calendar-day holiday support interval."""

    event_id: str
    provider: str
    opens_at: datetime
    closes_at: datetime
    classification_basis: str


def _is_holiday(event: object) -> tuple[bool, str]:
    """Return whether persisted evidence explicitly or legibly names a holiday.

    Args:
        event: Persisted calendar event record.

    Returns:
        Tuple of (is_holiday_flag, classification_basis).
    """
    event_type = str(getattr(event, "event_type", "") or "").strip().lower()
    if event_type == "holiday":
        return True, "provider_event_type"
    words = str(getattr(event, "name", "")).lower().replace("-", " ").split()
    return ("holiday" in words, "legacy_title_word")


def resolve_calendar_closures(
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    request_id: str,
) -> tuple[CalendarClosureEvidence, ...]:
    """Resolve complete persisted holiday support for one registered symbol.

    Args:
        symbol: Exact registered symbol-event profile identity.
        start: Inclusive UTC evidence bound.
        end: Exclusive UTC evidence bound.
        request_id: Caller trace identity.

    Returns:
        Ordered non-authoritative calendar support. Empty means unavailable,
        incomplete, irrelevant, or absent evidence and therefore fails closed.
    """
    store = EconomicEventStore()
    if store.missing_intervals(start, end, request_id=request_id):
        return ()
    profile = _get_symbol_event_profile_raw(symbol)
    response = store.query(
        start,
        end,
        currencies=tuple(sorted(profile.currencies)),
        # Persistence stores the normalized currency in the legacy ``country``
        # column when available. Supplying both filters would require one row to
        # equal a currency and a country simultaneously instead of applying the
        # public profile's relevance union.
        countries=None,
        request_id=request_id,
    )
    if response.status != "success" or response.data is None:
        return ()
    closures: list[CalendarClosureEvidence] = []
    for event in response.data:
        holiday, basis = _is_holiday(event)
        if not holiday:
            continue
        day_start = event.scheduled_at.astimezone(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        closures.append(
            CalendarClosureEvidence(
                event_id=f"{event.provider}:{event.id}",
                provider=event.provider,
                opens_at=day_start,
                closes_at=day_start + timedelta(days=1),
                classification_basis=basis,
            )
        )
    return tuple(closures)


__all__ = ["CalendarClosureEvidence", "resolve_calendar_closures"]
