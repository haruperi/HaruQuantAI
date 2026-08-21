"""Tests for FR-DATA-RETRIEVE_BARS use case coordination."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import override

import pytest

from app.contracts.broker.market_data import (
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.contracts.data.historical_bars import HistoricalBarsRequest
from app.services.data.historical_bars.retrieve import HistoricalBarsService


class DummyBrokerMarketData(BrokerMarketData):
    """Test double implementing BrokerMarketData protocol."""

    @override
    async def retrieve_bars(self, request: BrokerBarsRequest) -> Sequence[BrokerRawBar]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=1.1000,
                high_price=1.1050,
                low_price=1.0990,
                close_price=1.1020,
                volume=100.0,
            ),
        )


@pytest.mark.asyncio
async def test_historical_bars_service_retrieve() -> None:
    """Test retrieving and normalizing historical bars via use case service."""
    broker_feed = DummyBrokerMarketData()
    service = HistoricalBarsService(market_data=broker_feed)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 30, tzinfo=UTC)
    req = HistoricalBarsRequest(symbol="EURUSD", timeframe="M5", start=start, end=end)

    bars = await service.retrieve(req)
    assert len(bars) == 1
    assert bars[0].datetime == start
    assert bars[0].open == 1.1000
    assert bars[0].close == 1.1020


@pytest.mark.asyncio
async def test_historical_bars_service_invalid_request_raises() -> None:
    """Test that invalid request parameters raise ValueError before calling broker."""
    broker_feed = DummyBrokerMarketData()
    service = HistoricalBarsService(market_data=broker_feed)

    invalid_req = HistoricalBarsRequest(
        symbol="",
        timeframe="M1",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="Symbol must not be empty"):
        await service.retrieve(invalid_req)
