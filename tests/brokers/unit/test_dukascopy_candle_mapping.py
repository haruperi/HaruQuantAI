"""Dukascopy web-chart candle mapping tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.brokers.contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy_ticks.candle_mapping import (
    _map_candles,
    _provider_interval,
)

_START = datetime(2026, 6, 1, 12, tzinfo=UTC)


def test_candle_mapping_preserves_provider_bid_values() -> None:
    """A genuine web-chart row maps without an invented spread."""
    rows = (
        (
            int(_START.timestamp() * 1000),
            1.164620,
            1.165050,
            1.164490,
            1.164730,
            3983.4,
        ),
    )

    bars = _map_candles(
        rows,
        symbol="EURUSD",
        timeframe="H1",
        start=_START,
        end=_START + timedelta(hours=2),
    )

    assert len(bars) == 1
    assert bars[0].open == Decimal("1.16462")
    assert bars[0].high == Decimal("1.16505")
    assert bars[0].trade_volume == Decimal("3983.4")
    assert bars[0].spread is None
    assert bars[0].provider_timeframe == "1HOUR"


def test_candle_mapping_rejects_malformed_and_unordered_rows() -> None:
    """Malformed or duplicate provider timestamps fail closed."""
    timestamp = int(_START.timestamp() * 1000)
    with pytest.raises(_ProviderResponseError):
        _map_candles(
            ((timestamp, 1, 2),),
            symbol="EURUSD",
            timeframe="M1",
            start=_START,
            end=_START + timedelta(minutes=2),
        )
    row = (timestamp, 1, 2, 0, 1, 10)
    with pytest.raises(_ProviderResponseError, match="unordered"):
        _map_candles(
            (row, row),
            symbol="EURUSD",
            timeframe="M1",
            start=_START,
            end=_START + timedelta(minutes=2),
        )


def test_provider_interval_rejects_unsupported_timeframe() -> None:
    """Only verified web-chart intervals are accepted."""
    with pytest.raises(ValueError, match="unsupported"):
        _provider_interval("M7")
