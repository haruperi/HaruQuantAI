"""Tests for FR-BROKER-GENERATE_RAW_BARS."""

from datetime import UTC, datetime

import pytest

from app.contracts.broker.market_data import BrokerBarsRequest
from app.services.broker.mock_feed.config import MockFeedConfig
from app.services.broker.mock_feed.feed import MockBrokerMarketData


@pytest.mark.asyncio
async def test_mock_feed_generate_bars() -> None:
    """Test generating raw bars across specified date range."""
    feed = MockBrokerMarketData(MockFeedConfig(base_price=1.1200))
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)

    req = BrokerBarsRequest(symbol="EURUSD", timeframe="M15", start=start, end=end)
    bars = await feed.retrieve_bars(req)

    assert len(bars) == 4  # 00:00, 00:15, 00:30, 00:45
    assert bars[0].timestamp == start
    assert bars[0].open_price > 1.0
    assert bars[0].high_price >= bars[0].open_price
    assert bars[0].low_price <= bars[0].open_price


@pytest.mark.asyncio
async def test_mock_feed_timeframes() -> None:
    """Test generating bars with various timeframes."""
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)

    # M1
    req_m1 = BrokerBarsRequest(symbol="EURUSD", timeframe="M1", start=start, end=end)
    bars_m1 = await feed.retrieve_bars(req_m1)
    assert len(bars_m1) == 5

    # M5
    req_m5 = BrokerBarsRequest(symbol="EURUSD", timeframe="M5", start=start, end=end)
    bars_m5 = await feed.retrieve_bars(req_m5)
    assert len(bars_m5) == 1

    # D1
    start_d = datetime(2026, 1, 1, tzinfo=UTC)
    end_d = datetime(2026, 1, 3, tzinfo=UTC)
    req_d1 = BrokerBarsRequest(
        symbol="EURUSD", timeframe="D1", start=start_d, end=end_d
    )
    bars_d1 = await feed.retrieve_bars(req_d1)
    assert len(bars_d1) == 2


@pytest.mark.asyncio
async def test_mock_feed_unsupported_timeframe_raises() -> None:
    """Test unsupported timeframe raises ValueError."""
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    req = BrokerBarsRequest(
        symbol="EURUSD", timeframe="INVALID_TF", start=start, end=end
    )
    with pytest.raises(ValueError, match="Unsupported timeframe: 'INVALID_TF'"):
        await feed.retrieve_bars(req)


@pytest.mark.asyncio
async def test_mock_feed_max_bars_cap() -> None:
    """Test that bar generation caps at MAX_SYNTHETIC_BARS."""
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2030, 1, 1, tzinfo=UTC)  # Exceeds 10,000 M1 bars

    req = BrokerBarsRequest(symbol="EURUSD", timeframe="M1", start=start, end=end)
    bars = await feed.retrieve_bars(req)
    assert len(bars) == 10_000


@pytest.mark.asyncio
async def test_mock_feed_inverted_dates_returns_empty() -> None:
    """Test that end <= start returns empty sequence."""
    feed = MockBrokerMarketData()
    start = datetime(2026, 1, 2, tzinfo=UTC)
    end = datetime(2026, 1, 1, tzinfo=UTC)

    req = BrokerBarsRequest(symbol="EURUSD", timeframe="H1", start=start, end=end)
    bars = await feed.retrieve_bars(req)
    assert bars == ()
