"""Normalized economic-event contracts for FEAT-DATA-11.

Provider-specific calendar rows cross the boundary as a single normalized
`EconomicEvent` so that strategy, risk, and presentation code never reason
about provider dictionaries. Both numeric (`Decimal`) and raw (`str`) values
are preserved: providers commonly publish symbols such as ``178K``,
``3.2%``, ``4.5B`` or a signed ``-0.3%``, and exact parsing should not
destroy that representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import IntEnum
from typing import Any


class EventImpact(IntEnum):
    """Ordered economic-event impact levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(frozen=True, slots=True)
class EconomicEvent:
    """One normalized economic-calendar observation.

    Attributes:
        id: Provider-stable identifier (e.g. ``"<provider>:<provider_event_id>"``).
        provider: Provider name (e.g. ``"scrape:forexfactory"``).
        name: Human-readable event name.
        category: Optional provider category or sector label.
        country: ISO-3166-1 alpha-2 country code, when known.
        currency: ISO-4217 currency code, when known.
        scheduled_at: Timezone-aware UTC release time.
        original_scheduled_at: First observed UTC release time, retained when
            the provider reschedules an event.
        impact: Normalized impact level.
        actual: Released numeric value, when available.
        forecast: Forecasted numeric value, when available.
        previous: Previously-released numeric value, when available.
        revised_previous: Revised prior value when the prior release was
            later corrected, when available.
        actual_raw: Original provider textual ``actual`` representation.
        forecast_raw: Original provider textual ``forecast`` representation.
        previous_raw: Original provider textual ``previous`` representation.
        unit: Optional unit label (e.g. ``"%"`` or ``"K"``).
        source: Original provider/site name.
        source_url: Optional originating URL.
        provider_definition_id: Stable provider event-definition identity.
        source_original: Original publisher or institution URL.
        source_latest: Provider's latest-release URL.
        measures: Provider description of the measured quantity.
        effect: Provider description of the usual currency effect.
        frequency: Provider release-frequency description.
        also_called: Alternative event name.
        event_type: Provider event classification.
        updated_at: Optional last-mutated timestamp for stored events; also the
            event's most recent replay-visibility timestamp.
        first_seen_at: Optional original publication timestamp — when this
            event was first persisted, distinct from a later revision
            recorded through `updated_at` (Trading Cockpit Phase 0
            `TC-IMP-DATA-04`).
    """

    id: str
    provider: str
    name: str
    category: str | None
    country: str | None
    currency: str | None
    scheduled_at: datetime
    impact: EventImpact
    original_scheduled_at: datetime | None = None
    actual: Decimal | None = None
    forecast: Decimal | None = None
    previous: Decimal | None = None
    revised_previous: Decimal | None = None
    actual_raw: str | None = None
    forecast_raw: str | None = None
    previous_raw: str | None = None
    unit: str | None = None
    source: str | None = None
    source_url: str | None = None
    provider_definition_id: str | None = None
    source_original: str | None = None
    source_latest: str | None = None
    measures: str | None = None
    effect: str | None = None
    frequency: str | None = None
    also_called: str | None = None
    event_type: str | None = None
    updated_at: datetime | None = None
    first_seen_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the normalized provider boundary.

        Raises:
            ValueError: If identifiers are blank, timestamps are not aware UTC,
                codes are malformed, or numeric values are non-finite.
        """
        for field_name in ("id", "provider", "name"):
            value = getattr(self, field_name)
            if not value or value != value.strip():
                detail = f"{field_name} must be a non-empty trimmed string"
                raise ValueError(detail)
        for field_name in ("country", "currency"):
            value = getattr(self, field_name)
            if value is not None and (value != value.strip() or value != value.upper()):
                detail = f"{field_name} must be an uppercase trimmed code"
                raise ValueError(detail)
        for field_name in (
            "scheduled_at",
            "original_scheduled_at",
            "updated_at",
            "first_seen_at",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                value.tzinfo is None or value.utcoffset() != timedelta(0)
            ):
                detail = f"{field_name} must be timezone-aware UTC"
                raise ValueError(detail)
        for field_name in ("actual", "forecast", "previous", "revised_previous"):
            value = getattr(self, field_name)
            if value is not None and not value.is_finite():
                detail = f"{field_name} must be finite"
                raise ValueError(detail)


def project_economic_event(event: EconomicEvent) -> dict[str, Any]:
    """Return a detached, secret-safe projection of one normalized event.

    Args:
        event: Internal normalized economic event.

    Returns:
        Public scalar evidence preserving exact and raw provider values.
    """
    return {
        "provider_event_id": event.id,
        "provider": event.provider,
        "name": event.name,
        "category": event.category,
        "country": event.country,
        "currency": event.currency,
        "scheduled_at": event.scheduled_at.isoformat(),
        "original_scheduled_at": (
            None
            if event.original_scheduled_at is None
            else event.original_scheduled_at.isoformat()
        ),
        "impact": event.impact.name.lower(),
        "actual": None if event.actual is None else str(event.actual),
        "forecast": None if event.forecast is None else str(event.forecast),
        "previous": None if event.previous is None else str(event.previous),
        "revised_previous": (
            None if event.revised_previous is None else str(event.revised_previous)
        ),
        "actual_raw": event.actual_raw,
        "forecast_raw": event.forecast_raw,
        "previous_raw": event.previous_raw,
        "unit": event.unit,
        "source": event.source,
        "source_url": event.source_url,
        "provider_definition_id": event.provider_definition_id,
        "source_original": event.source_original,
        "source_latest": event.source_latest,
        "measures": event.measures,
        "effect": event.effect,
        "frequency": event.frequency,
        "also_called": event.also_called,
        "event_type": event.event_type,
        "updated_at": (
            None if event.updated_at is None else event.updated_at.isoformat()
        ),
        "first_seen_at": (
            None if event.first_seen_at is None else event.first_seen_at.isoformat()
        ),
    }


def is_event_visible_at(event: EconomicEvent, as_of: datetime) -> bool:
    """Return whether one event's currently-known state was visible at `as_of`.

    Trading Cockpit Phase 0 reconciliation (`TC-IMP-DATA-04`): a replay
    consumer must never see an event before its original publication, and an
    event whose publication time is unknown is never treated as visible.

    Args:
        event: Normalized economic event to check.
        as_of: Point-in-time UTC boundary supplied by the caller.

    Returns:
        ``True`` only when `event.first_seen_at` is known and does not
        exceed `as_of`; ``False`` otherwise (fail-closed).

    Raises:
        ValueError: If `as_of` is not timezone-aware UTC.
    """
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC")
    if event.first_seen_at is None:
        return False
    return event.first_seen_at <= as_of


__all__ = [
    "EconomicEvent",
    "EventImpact",
    "is_event_visible_at",
    "project_economic_event",
]
