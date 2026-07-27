"""Unit tests for normalized economic-event contracts (FR-DATA-123)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact


def _event(**overrides: object) -> EconomicEvent:
    """Build one minimal valid event applying the supplied overrides."""
    base: dict[str, object] = {
        "id": "ff:1",
        "provider": "scrape:forexfactory",
        "name": "Non-Farm Employment Change",
        "category": None,
        "country": "US",
        "currency": "USD",
        "scheduled_at": datetime(2026, 1, 2, 12, 30, tzinfo=UTC),
        "impact": EventImpact.HIGH,
        "actual": Decimal(216000),
        "forecast": Decimal(170000),
        "previous": Decimal(173000),
        "actual_raw": "216K",
        "forecast_raw": "170K",
        "previous_raw": "173K",
        "unit": "K",
        "source": "forexfactory",
        "source_url": None,
        "updated_at": None,
    }
    base.update(overrides)
    return EconomicEvent(**base)  # type: ignore[arg-type]


def test_event_impact_is_ordered_int_enum() -> None:
    """Impact members expose exactly the requested ordered three-value contract."""
    assert int(EventImpact.LOW) == 1
    assert int(EventImpact.MEDIUM) == 2
    assert int(EventImpact.HIGH) == 3
    assert EventImpact.HIGH > EventImpact.MEDIUM
    assert tuple(EventImpact) == (
        EventImpact.LOW,
        EventImpact.MEDIUM,
        EventImpact.HIGH,
    )


def test_economic_event_defaults_optionals_none() -> None:
    """Required-argument construction leaves optionals None unchanged."""
    event = EconomicEvent(
        id="ff:1",
        provider="scrape:forexfactory",
        name="NFP",
        category=None,
        country="US",
        currency="USD",
        scheduled_at=datetime(2026, 1, 2, 12, 30, tzinfo=UTC),
        impact=EventImpact.HIGH,
    )
    assert event.actual is None
    assert event.forecast is None
    assert event.previous is None
    assert event.revised_previous is None
    assert event.actual_raw is None
    assert event.forecast_raw is None
    assert event.previous_raw is None
    assert event.unit is None
    assert event.source is None
    assert event.source_url is None
    assert event.updated_at is None


def test_economic_event_is_frozen() -> None:
    """The contract is immutable; assignment raises."""
    event = _event()
    with pytest.raises(FrozenInstanceError):
        event.actual = Decimal(0)  # type: ignore[misc]


def test_economic_event_preserves_both_numeric_and_raw() -> None:
    """Both the parsed Decimal and the original provider text survive."""
    event = _event(actual=Decimal("0.3"), actual_raw="0.3%", unit="%")
    assert event.actual == Decimal("0.3")
    assert event.actual_raw == "0.3%"
    assert event.unit == "%"


@pytest.mark.parametrize("field", ["id", "provider", "name"])
def test_economic_event_rejects_blank_required_text(field: str) -> None:
    """Required normalized text cannot be empty or padded."""
    with pytest.raises(ValueError, match=field):
        _event(**{field: " "})


def test_economic_event_rejects_naive_or_non_utc_timestamp() -> None:
    """Normalized timestamps must be timezone-aware UTC."""
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        _event(
            scheduled_at=datetime(2026, 1, 2, 12, 30, tzinfo=UTC).replace(tzinfo=None)
        )


def test_economic_event_rejects_non_finite_numeric_values() -> None:
    """Normalized numeric values cannot contain NaN or infinity."""
    with pytest.raises(ValueError, match="actual must be finite"):
        _event(actual=Decimal("NaN"))
