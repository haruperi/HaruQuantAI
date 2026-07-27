"""Coverage expansion tests for Dukascopy ticks mapping operations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.brokers.contracts import BrokerTick
from app.services.brokers.contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy_ticks.mapping import (
    _RECORD,
    _aggregate_bars,
    _map_ticks,
)


def test_map_ticks_valid_payload() -> None:
    """Verify decoding valid Dukascopy BI5 binary record payload."""
    hour = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    # Binary record: 100ms, ask 123450, bid 123400, ask_vol 1.5, bid_vol 2.5
    data = _RECORD.pack(100, 123450, 123400, 1.5, 2.5)
    ticks = _map_ticks(data, symbol="EURUSD", hour=hour, price_divisor=100000, limit=10)

    assert len(ticks) == 1
    assert ticks[0].symbol == "EURUSD"
    assert ticks[0].ask == Decimal("1.2345")
    assert ticks[0].bid == Decimal("1.234")
    assert ticks[0].ask_quantity == Decimal("1.5")
    assert ticks[0].bid_quantity == Decimal("2.5")


def test_map_ticks_malformed_length() -> None:
    """Verify malformed payload byte length raises _ProviderResponseError."""
    hour = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    with pytest.raises(
        _ProviderResponseError, match="malformed Dukascopy BI5 record length"
    ):
        _map_ticks(b"1234", symbol="EURUSD", hour=hour, price_divisor=100000, limit=10)


def test_map_ticks_naive_hour() -> None:
    """Verify timezone-naive hour parameter raises ValueError."""
    hour = datetime(2026, 7, 6, 12, 0, 0)  # noqa: DTZ001
    data = _RECORD.pack(100, 123450, 123400, 1.5, 2.5)
    with pytest.raises(ValueError, match="Dukascopy hour must be timezone-aware"):
        _map_ticks(data, symbol="EURUSD", hour=hour, price_divisor=100000, limit=10)


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
    hour = datetime(2026, 7, 6, 12, 0, 0, tzinfo=UTC)
    data = _RECORD.pack(100, 123450, 123400, 1.5, 2.5) + _RECORD.pack(
        200, 123460, 123410, 1.5, 2.5
    )
    ticks = _map_ticks(data, symbol="EURUSD", hour=hour, price_divisor=100000, limit=1)
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
