"""Unit tests for BaseBrokerBackend in app.services.brokers.base and DataBrokerBackend.

Description:
    Validates lifecycle hooks, asynchronous dispatch routing, execution receipts,
    context management, and error handling for the foundational BaseBrokerBackend
    and DataBrokerBackend adapters.

Purpose:
    FEAT-BROKER-BASE: Unit test suite for foundational broker backend adapters.

Key Capabilities:
    - FR-BROKER-BASE-ROUTING: Verify dispatch routing for symbol queries and
      terminal snapshot lookups.
    - FR-BROKER-BASE-LIFECYCLE: Verify connection session start/stop, readiness
      confirmation, and context management.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_broker_base.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio

import pytest
from app.services.brokers.base import BaseBrokerBackend, BridgeError
from app.services.libs.data import (
    DataBrokerBackend,
    MarketBar,
    MarketTick,
)
from app.services.libs.trading import (
    ReceiptStatus,
    SymbolSnapshot,
    TerminalSnapshot,
)


class TestBaseBrokerBackend:
    """Test suite for BaseBrokerBackend in brokers.base."""

    def test_default_lifecycle_and_stubs(self) -> None:
        """Verify default base class methods and lifecycle hooks."""
        broker = BaseBrokerBackend("base_broker")
        assert broker.name == "base_broker"
        broker.arm()
        broker.disarm()

        async def run_lifecycle() -> None:
            await broker.start()
            assert bool(broker._is_connected)
            await broker.wait_connected()
            assert bool(broker._is_connected)
            await broker.close()
            assert not broker._is_connected

            async with broker as b:
                assert b is broker
                assert bool(broker._is_connected)

            with pytest.raises(
                NotImplementedError,
                match="does not emit asynchronous transaction events",
            ):
                await broker.next_event()

            with pytest.raises(
                NotImplementedError,
                match="does not emit asynchronous transaction events",
            ):
                await broker.await_request_event(1)

        asyncio.run(run_lifecycle())

        info = broker.symbol_info("EURUSD")
        assert isinstance(info, SymbolSnapshot)
        assert info.name == "EURUSD"
        assert broker.symbols_get() == []

    def test_call_routing_and_receipts(self) -> None:
        """Verify method call routing, receipts, and execution tracking."""
        broker = BaseBrokerBackend("base_broker")
        assert broker.last_command_id() is None
        assert broker.receipt("nonexistent") is None

        async def run_calls() -> None:
            # Call SymbolInfo.SymbolInfo
            sym = await broker.call(
                object_id="broker",
                class_name="SymbolInfo",
                method_name="SymbolInfo",
                args=["EURUSD"],
            )
            assert isinstance(sym, SymbolSnapshot)
            assert sym.name == "EURUSD"
            cmd_id = broker.last_command_id()
            assert cmd_id is not None
            rcpt = broker.receipt(cmd_id)
            assert rcpt is not None
            assert rcpt.status == ReceiptStatus.RESOLVED

            # Call SymbolInfo.SymbolsGet
            symbols = await broker.call(
                object_id="broker",
                class_name="SymbolInfo",
                method_name="SymbolsGet",
                args=[],
            )
            assert symbols == []

            # Call TerminalInfo.TerminalInfo
            terminal = await broker.call(
                object_id="broker",
                class_name="TerminalInfo",
                method_name="TerminalInfo",
                args=[],
            )
            assert isinstance(terminal, TerminalSnapshot)
            assert terminal.name == "base_broker"
            assert terminal.connected is True
            assert terminal.trade_allowed is False

            # Unsupported method raises BridgeError and sets REJECTED receipt
            with pytest.raises(
                BridgeError, match=r"base_broker does not support Trading\.OrderSend"
            ):
                await broker.call(
                    object_id="broker",
                    class_name="Trading",
                    method_name="OrderSend",
                    args=[],
                )
            unsupported_cmd_id = broker.last_command_id()
            assert unsupported_cmd_id is not None
            unsupported_rcpt = broker.receipt(unsupported_cmd_id)
            assert unsupported_rcpt is not None
            assert unsupported_rcpt.status == ReceiptStatus.REJECTED

        asyncio.run(run_calls())


class TestDataBrokerBackend:
    """Test suite for DataBrokerBackend in libs.data."""

    def test_default_data_hooks(self) -> None:
        """Verify default data hooks raise BridgeError."""
        broker = DataBrokerBackend("base_data")
        assert broker.name == "base_data"
        assert isinstance(broker, BaseBrokerBackend)

        with pytest.raises(
            BridgeError, match="base_data does not support historical bars"
        ):
            broker.fetch_bars(
                symbol="EURUSD",
                timeframe="M1",
                mode="latest",
                start=0,
                end=0,
                count=100,
                limit=1000,
            )

        with pytest.raises(
            BridgeError, match="base_data does not support tick history"
        ):
            broker.fetch_ticks(
                symbol="EURUSD",
                mode="latest",
                start_ms=0,
                end_ms=0,
                count=100,
                limit=1000,
            )

    def test_market_data_dispatch(self) -> None:
        """Verify MarketData dispatch routing for bars and ticks."""

        class MockDataBroker(DataBrokerBackend):
            def __init__(self) -> None:
                super().__init__("mock_data_broker")

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
            ) -> list[MarketBar]:
                if symbol == "FAIL":
                    raise ValueError("bar failure")
                return [
                    MarketBar(
                        time=1700000000,
                        open=1.1,
                        high=1.2,
                        low=1.0,
                        close=1.15,
                        tick_volume=10,
                        spread=1,
                        real_volume=100,
                    )
                ]

            def fetch_ticks(
                self,
                *,
                symbol: str,
                mode: str,
                start_ms: int,
                end_ms: int,
                count: int,
                limit: int,
            ) -> list[MarketTick]:
                return [
                    MarketTick(
                        time_msc=1700000000000,
                        bid=1.1,
                        ask=1.2,
                        last=1.15,
                        volume=10,
                        flags=6,
                        volume_real=10.0,
                    )
                ]

        broker = MockDataBroker()

        async def run_calls() -> None:
            bars = await broker.call(
                object_id="broker",
                class_name="MarketData",
                method_name="Bars",
                args=["EURUSD", "M1", "latest", 0, 0, 10, 1000],
            )
            assert len(bars) == 1

            ticks = await broker.call(
                object_id="broker",
                class_name="MarketData",
                method_name="Ticks",
                args=["EURUSD", "latest", 0, 0, 10, 1000],
            )
            assert len(ticks) == 1

            with pytest.raises(ValueError, match="bar failure"):
                await broker.call(
                    object_id="broker",
                    class_name="MarketData",
                    method_name="Bars",
                    args=["FAIL", "M1"],
                )

        asyncio.run(run_calls())
