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
        updated_at: Optional last-mutated timestamp for stored events.
    """

    id: str
    provider: str
    name: str
    category: str | None
    country: str | None
    currency: str | None
    scheduled_at: datetime
    impact: EventImpact
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
    updated_at: datetime | None = None

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
        for field_name in ("scheduled_at", "updated_at"):
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


__all__ = ["EconomicEvent", "EventImpact"]
