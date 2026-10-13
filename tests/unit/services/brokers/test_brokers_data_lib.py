"""Unit tests verifying app.services.libs.data compatibility with all data brokers.

Description:
    Tests that DataBrokerBackend instances conform to the TradingBackend protocol and
    can be used seamlessly by high-level quant data APIs in app.services.libs.data:
    specifically `get_historical_bars` and `get_ticks`.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    MarketBar,
    SymbolSpec,
    Timeframe,
)
from app.services.brokers.crypto import BinanceBroker
from app.services.brokers.darwinex import DarwinexBroker
from app.services.brokers.dukascopy import DukascopyBroker
from app.services.brokers.files import FilesBroker
from app.services.brokers.simulator import SimulationBackend
from app.services.brokers.sq_equity import SQEquityBroker
from app.services.brokers.sq_futures import SQFuturesBroker
from app.services.brokers.yahoo import YahooBroker
from app.services.libs.data import get_historical_bars, get_ticks


class DummyDataBroker(DataBrokerBackend):
    """Minimal test broker returning synthesized bars conforming to OHLC."""

    def __init__(self) -> None:
        super().__init__(name="Dummy")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str,
        start: int,
        end: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        del symbol, timeframe, mode, start, end, limit
        n = count if count > 0 else 5
        return [
            {
                "time": 1704110000 + i * 60,
                "open": 100.0 + i,
                "high": 105.0 + i,
                "low": 95.0 + i,
                "close": 102.0 + i,
                "tick_volume": 10 * (i + 1),
                "spread": 0,
                "real_volume": 10 * (i + 1),
            }
            for i in range(n)
        ]

    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str = "latest",
        start_ms: int = 0,
        end_ms: int = 0,
        count: int = 0,
        limit: int = 1000,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        del symbol, mode, start_ms, end_ms, limit, kwargs
        n = count if count > 0 else 5
        return [
            {
                "time_msc": (1704110000 + i) * 1000,
                "bid": 100.0 + i * 0.1,
                "ask": 100.1 + i * 0.1,
                "last": 100.05 + i * 0.1,
                "volume": 1,
                "flags": 0,
                "volume_real": 1.0,
            }
            for i in range(n)
        ]


def test_base_broker_trading_backend_bars_dispatch() -> None:
    """Verify that get_historical_bars works directly with DataBrokerBackend."""

    async def scenario() -> None:
        broker = DummyDataBroker()
        bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_M1, count=5)
        assert len(bars) == 5
        assert bars[0].open == 100.0
        assert bars[0].close == 102.0
        assert bars[0].high == 105.0
        assert bars[0].low == 95.0

    asyncio.run(scenario())


def test_base_broker_trading_backend_ticks_dispatch() -> None:
    """Verify that get_ticks works directly with DataBrokerBackend."""

    async def scenario() -> None:
        broker = DummyDataBroker()
        ticks = await get_ticks(broker, "EURUSD", count=5)
        assert len(ticks) == 5
        assert ticks[0].bid == 100.0
        assert ticks[0].ask == 100.1

    asyncio.run(scenario())


def test_simulation_backend_bars() -> None:
    """Verify get_historical_bars works with SimulationBackend."""

    async def scenario() -> None:
        sim = SimulationBackend()
        sim.add_symbol(SymbolSpec(name="EURUSD"))
        bars_seeded = [
            MarketBar(
                time=1704100000 + i * 60,
                open=1.0850,
                high=1.0860,
                low=1.0840,
                close=1.0855,
                tick_volume=10,
                spread=1,
                real_volume=10,
            )
            for i in range(10)
        ]
        sim.seed_bar_history("EURUSD", Timeframe.PERIOD_M1, bars_seeded)
        bars = await get_historical_bars(sim, "EURUSD", Timeframe.PERIOD_M1, count=10)
        assert len(bars) == 10

    asyncio.run(scenario())


def test_yahoo_broker_with_data_lib() -> None:
    """Verify YahooBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = YahooBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 154.0,
                "tick_volume": 1000,
                "spread": 0,
                "real_volume": 1000,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "AAPL", Timeframe.PERIOD_D1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 154.0

    asyncio.run(scenario())


def test_binance_broker_with_data_lib() -> None:
    """Verify BinanceBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = BinanceBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 42000.0,
                "high": 42500.0,
                "low": 41900.0,
                "close": 42300.0,
                "tick_volume": 50,
                "spread": 0,
                "real_volume": 50,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "BTCUSDT", Timeframe.PERIOD_H1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 42300.0

    asyncio.run(scenario())


def test_dukascopy_broker_with_data_lib() -> None:
    """Verify DukascopyBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = DukascopyBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 1.0850,
                "high": 1.0860,
                "low": 1.0845,
                "close": 1.0855,
                "tick_volume": 200,
                "spread": 0,
                "real_volume": 200,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "EURUSD", Timeframe.PERIOD_M1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 1.0855

    asyncio.run(scenario())


def test_darwinex_broker_with_data_lib() -> None:
    """Verify DarwinexBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = DarwinexBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 1.0850,
                "high": 1.0860,
                "low": 1.0845,
                "close": 1.0855,
                "tick_volume": 200,
                "spread": 0,
                "real_volume": 200,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "EURUSD", Timeframe.PERIOD_M1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 1.0855

    asyncio.run(scenario())


def test_sq_equity_broker_with_data_lib() -> None:
    """Verify SQEquityBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = SQEquityBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 180.0,
                "high": 182.0,
                "low": 179.0,
                "close": 181.5,
                "tick_volume": 500,
                "spread": 0,
                "real_volume": 500,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "AAPL", Timeframe.PERIOD_D1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 181.5

    asyncio.run(scenario())


def test_sq_futures_broker_with_data_lib() -> None:
    """Verify SQFuturesBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = SQFuturesBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 4800.0,
                "high": 4820.0,
                "low": 4790.0,
                "close": 4810.0,
                "tick_volume": 1000,
                "spread": 0,
                "real_volume": 1000,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "@ES", Timeframe.PERIOD_D1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 4810.0

    asyncio.run(scenario())


def test_files_broker_with_data_lib() -> None:
    """Verify FilesBroker integrates with get_historical_bars."""

    async def scenario() -> None:
        broker = FilesBroker()
        mock_bars = [
            {
                "time": 1704110400,
                "open": 1.1,
                "high": 1.12,
                "low": 1.09,
                "close": 1.11,
                "tick_volume": 100,
                "spread": 0,
                "real_volume": 100,
            }
        ]
        with patch.object(broker, "fetch_bars", return_value=mock_bars):
            bars = await get_historical_bars(
                broker, "EURUSD", Timeframe.PERIOD_D1, count=1
            )
            assert len(bars) == 1
            assert bars[0].close == 1.11

    asyncio.run(scenario())
