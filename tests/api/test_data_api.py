"""Unit tests for capability-aware DataAPI facade."""

from datetime import UTC, datetime
from typing import override

import pytest

from app.api.data import DataAPI
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBars,
    HistoricalBarsRequest,
)
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import ServiceRegistry


class DummyHistoricalBars(HistoricalBars):
    @override
    async def retrieve(self, request: HistoricalBarsRequest) -> tuple[Bar, ...]:
        return (
            Bar(
                datetime=request.start,
                open=1.1000,
                high=1.1050,
                low=1.0990,
                close=1.1020,
                volume=100.0,
            ),
        )


@pytest.mark.asyncio
async def test_data_api_historical_bars_available() -> None:
    """Test DataAPI returns bars when capability is registered."""
    registry = ServiceRegistry()
    service = DummyHistoricalBars()
    registry.register(HISTORICAL_BARS, service, owner_id="FEAT-DATA-RETRIEVE_BARS")

    api = DataAPI(registry)
    assert api.is_historical_bars_available is True
    assert api.is_realtime_ticks_available is False
    assert api.is_bar_cache_available is False

    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="H1",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    bars = await api.get_historical_bars(req)
    assert len(bars) == 1
    assert bars[0].close == 1.1020


@pytest.mark.asyncio
async def test_data_api_historical_bars_unavailable() -> None:
    """Test DataAPI raises CapabilityUnavailableError when capability is absent."""
    registry = ServiceRegistry()
    api = DataAPI(registry)
    assert api.is_historical_bars_available is False

    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="H1",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(CapabilityUnavailableError, match=r"data\.historical-bars@1"):
        await api.get_historical_bars(req)
