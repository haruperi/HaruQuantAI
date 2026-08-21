"""Tests for FR-DATA-NORMALIZE_BARS."""

from datetime import UTC, datetime

from app.contracts.broker.market_data import BrokerRawBar
from app.services.data.historical_bars.normalize import (
    normalize_bars,
    normalize_raw_bar,
)


def test_normalize_raw_bar() -> None:
    """Test normalizing a single raw broker bar into Bar DTO."""
    now = datetime.now(UTC)
    raw = BrokerRawBar(
        timestamp=now,
        open_price=1.1000,
        high_price=1.1050,
        low_price=1.0990,
        close_price=1.1020,
        volume=500.0,
    )

    bar = normalize_raw_bar(raw)
    assert bar.datetime == now
    assert bar.open == 1.1000
    assert bar.high == 1.1050
    assert bar.low == 1.0990
    assert bar.close == 1.1020
    assert bar.volume == 500.0


def test_normalize_bars_batch() -> None:
    """Test batch normalizing sequence of raw bars."""
    now = datetime.now(UTC)
    raws = [
        BrokerRawBar(
            timestamp=now,
            open_price=1.0,
            high_price=1.1,
            low_price=0.9,
            close_price=1.05,
            volume=10.0,
        ),
        BrokerRawBar(
            timestamp=now,
            open_price=1.05,
            high_price=1.2,
            low_price=1.0,
            close_price=1.15,
            volume=20.0,
        ),
    ]

    bars = normalize_bars(raws)
    assert len(bars) == 2
    assert bars[0].open == 1.0
    assert bars[1].close == 1.15
