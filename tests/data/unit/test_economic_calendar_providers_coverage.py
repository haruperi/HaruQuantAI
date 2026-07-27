"""Unit tests for economic_calendar/providers.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.providers import (
    CalendarScrapeProvider,
    _currency_for,
    _matches_scope,
    _unit,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def test_unit_helper() -> None:
    """Test _unit helper with %, K, M, B suffixes."""
    assert _unit("10.5%") == "%"
    assert _unit("250K") == "K"
    assert _unit("1.5m") == "M"
    assert _unit("2.1B") == "B"
    assert _unit(None, "100") is None


def test_currency_for_helper() -> None:
    """
    Test _currency_for helper with explicit currency, currency in country slot, and country lookup.
    """
    assert _currency_for(None, "USD") == "USD"
    assert _currency_for("USD", None) == "USD"
    assert _currency_for("US", None) == "USD"
    assert _currency_for("UNKNOWN", None) is None
    assert _currency_for(None, None) is None


def test_matches_scope_helper() -> None:
    """Test _matches_scope matching currency and country filters."""
    ev = EconomicEvent(
        id="evt1",
        provider="scrape:forexfactory",
        name="CPI",
        category=None,
        country="US",
        currency="USD",
        scheduled_at=_NOW,
        impact=EventImpact.HIGH,
        actual=None,
        forecast=None,
        previous=None,
        revised_previous=None,
        actual_raw=None,
        forecast_raw=None,
        previous_raw=None,
        unit=None,
        source="forexfactory",
        source_url=None,
        updated_at=None,
    )
    assert _matches_scope(ev, None, None) is True
    assert _matches_scope(ev, ("USD",), None) is True
    assert _matches_scope(ev, ("EUR",), None) is False
    assert _matches_scope(ev, None, ("US",)) is True
    assert _matches_scope(ev, None, ("DE",)) is False


@pytest.mark.anyio
async def test_calendar_scrape_provider_invalid_window() -> None:
    """Test get_events raises VALIDATION_FAILED when start >= end or naive."""
    transport = MagicMock()
    provider = CalendarScrapeProvider(transport)

    with pytest.raises(DataError) as exc_info:
        await provider.get_events(_NOW, _NOW - timedelta(hours=1))
    assert exc_info.value.code == "VALIDATION_FAILED"

    with pytest.raises(DataError) as exc_info:
        await provider.get_events(datetime.now(UTC), _NOW)
    assert exc_info.value.code == "VALIDATION_FAILED"
