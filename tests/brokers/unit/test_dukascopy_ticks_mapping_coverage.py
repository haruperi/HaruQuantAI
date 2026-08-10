"""Coverage expansion tests for Dukascopy ticks mapping operations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.brokers.canonical_contracts import BrokerTick
from app.services.brokers.canonical_contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy.mapping import _aggregate_bars, _map_ticks


def test_map_ticks_valid_payload() -> None:
    """Verify mapping one valid Dukascopy web-chart row."""
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    rows = ((int(start.timestamp() * 1000) + 100, 1.234, 1.2345, 2_500_000, 1_500_000),)
    ticks = _map_ticks(
        rows, symbol="EURUSD", start=start, end=start + timedelta(hours=1), limit=10
    )

    assert len(ticks) == 1
    assert ticks[0].symbol == "EURUSD"
    assert ticks[0].ask == Decimal("1.2345")
    assert ticks[0].bid == Decimal("1.234")
    assert ticks[0].ask_quantity == Decimal("1.5")
    assert ticks[0].bid_quantity == Decimal("2.5")


def test_map_ticks_malformed_length() -> None:
    """Verify malformed row length raises _ProviderResponseError."""
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    with pytest.raises(_ProviderResponseError, match="malformed Dukascopy tick row"):
        _map_ticks(
            ((1, 2),),
            symbol="EURUSD",
            start=start,
            end=start + timedelta(hours=1),
            limit=10,
        )


def test_map_ticks_naive_hour() -> None:
    """Verify timezone-naive hour parameter raises ValueError."""
    start = datetime(2026, 7, 6, 12, 0, 0)  # noqa: DTZ001
    with pytest.raises(ValueError, match="timezone-aware"):
        _map_ticks(
            (), symbol="EURUSD", start=start, end=start + timedelta(hours=1), limit=10
        )


def test_aggregate_bars_unsupported_timeframe() -> None:
    """Verify invalid timeframe raises ValueError."""
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    with pytest.raises(ValueError, match="unsupported Dukascopy aggregation timeframe"):
        _aggregate_bars((), symbol="EURUSD", timeframe="INVALID", start=start, end=end)


def test_aggregate_bars_invalid_range() -> None:
    """Verify start >= end or naive datetimes raise ValueError."""
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    end = start - timedelta(hours=1)
    with pytest.raises(
        ValueError, match="ordered UTC-aware Dukascopy bar range is required"
    ):
        _aggregate_bars((), symbol="EURUSD", timeframe="M1", start=start, end=end)


def test_map_ticks_limit_reached() -> None:
    """Verify limit parameter bounds decoded ticks."""
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    stamp = int(start.timestamp() * 1000)
    rows = ((stamp + 100, 1.2, 1.3, 1, 1), (stamp + 200, 1.3, 1.4, 1, 1))
    ticks = _map_ticks(
        rows, symbol="EURUSD", start=start, end=start + timedelta(hours=1), limit=1
    )
    assert len(ticks) == 1


def test_aggregate_bars_filters_out_of_range_and_single_prices() -> None:
    """Verify tick filtering outside window and single-price tick midpoints."""
    t0 = datetime(2026, 7, 6, 11, 59, 0, tzinfo=UTC)  # Before window
    t1 = datetime(2026, 7, 6, 12, 0, 10, tzinfo=UTC)
    t2 = datetime(2026, 7, 6, 12, 0, 20, tzinfo=UTC)
    t3 = datetime(2026, 7, 6, 12, 0, 30, tzinfo=UTC)
    ticks = (
        BrokerTick(
            symbol="EURUSD",
            event_timestamp=t0,
            provider_receipt_timestamp=t0,
            price_unit="quote_currency",
            quantity_unit="provider_volume",
            tick_type="QUOTE",
            bid=Decimal("1.1000"),
        ),
        BrokerTick(
            symbol="EURUSD",
            event_timestamp=t1,
            provider_receipt_timestamp=t1,
            price_unit="quote_currency",
            quantity_unit="provider_volume",
            tick_type="TRADE",
            last_price=Decimal("1.1005"),
        ),
        BrokerTick(
            symbol="EURUSD",
            event_timestamp=t2,
            provider_receipt_timestamp=t2,
            price_unit="quote_currency",
            quantity_unit="provider_volume",
            tick_type="QUOTE",
            bid=Decimal("1.1010"),
        ),
        BrokerTick(
            symbol="EURUSD",
            event_timestamp=t3,
            provider_receipt_timestamp=t3,
            price_unit="quote_currency",
            quantity_unit="provider_volume",
            tick_type="QUOTE",
            ask=Decimal("1.1015"),
        ),
    )
    start = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    end = start + timedelta(minutes=5)
    bars = _aggregate_bars(ticks, symbol="EURUSD", timeframe="M1", start=start, end=end)

    assert len(bars) == 1
    assert bars[0].open == Decimal("1.1005")
    assert bars[0].close == Decimal("1.1015")
    assert bars[0].high == Decimal("1.1015")
    assert bars[0].low == Decimal("1.1005")
