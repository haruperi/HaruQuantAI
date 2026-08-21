"""Tests for deterministic mock broker bar generation."""

from datetime import UTC, datetime

import pytest

from app.contracts.broker.market_data import BrokerBarsRequest
from app.services.broker.mock_feed.config import MockFeedConfig
from app.services.broker.mock_feed.feed import MockBrokerMarketData


@pytest.mark.asyncio
async def test_mock_feed_generate_bars() -> None:
    feed = MockBrokerMarketData(MockFeedConfig(base_price=1.1200))
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    bars = await feed.retrieve_bars(
        BrokerBarsRequest(symbol="EURUSD", timeframe="M15", start=start, end=end)
    )
    assert len(bars) == 4
    assert bars[0].timestamp == start
    assert bars[0].high_price >= bars[0].open_price
    assert bars[0].low_price <= bars[0].open_price


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("timeframe", "end", "expected"),
    [
        ("M1", datetime(2026, 1, 1, 0, 5, tzinfo=UTC), 5),
        ("M5", datetime(2026, 1, 1, 0, 5, tzinfo=UTC), 1),
        ("M30", datetime(2026, 1, 1, 1, 0, tzinfo=UTC), 2),
        ("H1", datetime(2026, 1, 1, 4, 0, tzinfo=UTC), 4),
        ("H4", datetime(2026, 1, 1, 8, 0, tzinfo=UTC), 2),
        ("D1", datetime(2026, 1, 3, 0, 0, tzinfo=UTC), 2),
        ("W1", datetime(2026, 1, 15, 0, 0, tzinfo=UTC), 2),
    ],
)
async def test_mock_feed_supported_timeframes(
    timeframe: str,
    end: datetime,
    expected: int,
) -> None:
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = await feed.retrieve_bars(
        BrokerBarsRequest(symbol="EURUSD", timeframe=timeframe, start=start, end=end)
    )
    assert len(bars) == expected


@pytest.mark.asyncio
async def test_mock_feed_unknown_timeframe_raises() -> None:
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)
    with pytest.raises(ValueError, match="Unsupported timeframe"):
        await feed.retrieve_bars(
            BrokerBarsRequest(symbol="EURUSD", timeframe="UNKNOWN", start=start, end=end)
        )


@pytest.mark.asyncio
async def test_mock_feed_max_bars_cap() -> None:
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2030, 1, 1, tzinfo=UTC)
    bars = await feed.retrieve_bars(
        BrokerBarsRequest(symbol="EURUSD", timeframe="M1", start=start, end=end)
    )
    assert len(bars) == 10_000


@pytest.mark.asyncio
async def test_mock_feed_inverted_dates_returns_empty() -> None:
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 2, tzinfo=UTC)
    end = datetime(2026, 1, 1, tzinfo=UTC)
    bars = await feed.retrieve_bars(
        BrokerBarsRequest(symbol="EURUSD", timeframe="H1", start=start, end=end)
    )
    assert bars == ()
