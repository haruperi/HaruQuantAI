"""Unit tests for capability-aware BrokerAPI facade."""

from datetime import UTC, datetime
from typing import override

import pytest

from app.api.broker import BrokerAPI
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import ServiceRegistry


class DummyBrokerFeed(BrokerMarketData):
    @override
    async def retrieve_bars(
        self, request: BrokerBarsRequest
    ) -> tuple[BrokerRawBar, ...]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=1.2000,
                high_price=1.2050,
                low_price=1.1990,
                close_price=1.2020,
                volume=500.0,
            ),
        )


@pytest.mark.asyncio
async def test_broker_api_market_data_available() -> None:
    """Test BrokerAPI retrieves raw bars when market data capability is active."""
    registry = ServiceRegistry()
    feed = DummyBrokerFeed()
    registry.register(BROKER_MARKET_DATA, feed, owner_id="FEAT-BROKER-FEED_MOCK")

    api = BrokerAPI(registry)
    assert api.is_market_data_available is True
    assert api.is_execution_available is False

    req = BrokerBarsRequest(
        symbol="GBPUSD",
        timeframe="M5",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    bars = await api.get_raw_bars(req)
    assert len(bars) == 1
    assert bars[0].close_price == 1.2020


@pytest.mark.asyncio
async def test_broker_api_market_data_unavailable() -> None:
    """Test BrokerAPI raises CapabilityUnavailableError when market data is absent."""
    registry = ServiceRegistry()
    api = BrokerAPI(registry)
    assert api.is_market_data_available is False

    req = BrokerBarsRequest(
        symbol="GBPUSD",
        timeframe="M5",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(CapabilityUnavailableError, match=r"broker\.market-data@1"):
        await api.get_raw_bars(req)
