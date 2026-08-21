"""Tests for historical-bars use-case coordination."""

from __future__ import annotations

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
    """Broker test double recording the effective request."""

    def __init__(self) -> None:
        self.last_request: BrokerBarsRequest | None = None

    @override
    async def retrieve_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        self.last_request = request
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
    broker = DummyBrokerMarketData()
    service = HistoricalBarsService(market_data=broker)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    request = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="M5",
        start=start,
        end=datetime(2026, 1, 1, 0, 30, tzinfo=UTC),
    )
    bars = await service.retrieve(request)
    assert len(bars) == 1
    assert bars[0].datetime == start
    assert bars[0].open == 1.1000
    assert bars[0].close == 1.1020


@pytest.mark.asyncio
async def test_blank_timeframe_uses_configured_default() -> None:
    """The documented default_timeframe is an actual runtime fallback."""
    broker = DummyBrokerMarketData()
    service = HistoricalBarsService(
        market_data=broker,
        default_timeframe="H1",
    )
    await service.retrieve(
        HistoricalBarsRequest(
            symbol="EURUSD",
            timeframe="   ",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
        )
    )
    assert broker.last_request is not None
    assert broker.last_request.timeframe == "H1"


@pytest.mark.asyncio
async def test_historical_bars_service_invalid_request_raises() -> None:
    broker = DummyBrokerMarketData()
    service = HistoricalBarsService(market_data=broker)
    with pytest.raises(ValueError, match="Symbol must not be empty"):
        await service.retrieve(
            HistoricalBarsRequest(
                symbol="",
                timeframe="M1",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
