"""Unit tests for BrokerClient and TradingClient in app.services.brokers.base.

Description:
    Validates lifecycle hooks, asynchronous dispatch routing, execution receipts,
    context management, and error handling for the foundational BrokerClient
    and TradingClient implementations.

Purpose:
    FEAT-BROKER-BASE: Unit test suite for foundational broker client classes.

Key Capabilities:
    - FR-BROKER-BASE-ROUTING: Verify dispatch routing for symbol queries and
      terminal info lookups.
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
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    TradingClient,
)
from app.services.include.contracts import (
    SymbolInfo,
    TerminalInfo,
)
from app.services.include.enums import ReceiptStatus


class TestBrokerClient:
    """Test suite for BrokerClient in brokers.base."""

    def test_default_lifecycle_and_stubs(self) -> None:
        """Verify default base class methods and lifecycle hooks."""
        client = BrokerClient("base_client")
        assert client.name == "base_client"
        assert bool(client.connected) is False
        client.connect()
        assert bool(client.connected) is True
        client.disconnect()
        assert bool(client.connected) is False

        info = client.get_symbol_info("EURUSD")
        assert isinstance(info, SymbolInfo)
        assert info.name == "EURUSD"
        assert client.get_symbols() == []

        with pytest.raises(BridgeError, match="does not support historical bars"):
            client.get_bars("EURUSD")

        with pytest.raises(BridgeError, match="does not support tick history"):
            client.get_ticks("EURUSD")


class TestTradingClient:
    """Test suite for TradingClient in brokers.base."""

    def test_default_lifecycle_and_stubs(self) -> None:
        """Verify default trading class methods and lifecycle hooks."""
        client = TradingClient("base_trading")
        assert client.name == "base_trading"
        assert bool(client.is_armed) is False
        client.arm()
        assert bool(client.is_armed) is True
        client.disarm()
        assert bool(client.is_armed) is False

        async def run_lifecycle() -> None:
            await client.start()
            assert bool(client.connected) is True
            await client.wait_connected()
            assert bool(client.connected) is True
            await client.close()
            assert bool(client.connected) is False

            async with client as c:
                assert c is client
                assert bool(client.connected) is True

            with pytest.raises(
                NotImplementedError,
                match="does not emit asynchronous transaction events",
            ):
                await client.next_event()

            with pytest.raises(
                NotImplementedError,
                match="does not emit asynchronous transaction events",
            ):
                await client.await_request_event(1)

        asyncio.run(run_lifecycle())

    def test_call_routing_and_receipts(self) -> None:
        """Verify method call routing, receipts, and execution tracking."""
        client = TradingClient("base_trading")
        assert client.last_command_id() is None
        assert client.receipt("nonexistent") is None

        async def run_calls() -> None:
            # Call SymbolInfo.SymbolInfo
            sym = await client.call(
                object_id="client",
                class_name="SymbolInfo",
                method_name="SymbolInfo",
                args=["EURUSD"],
            )
            assert isinstance(sym, SymbolInfo)
            assert sym.name == "EURUSD"
            cmd_id = client.last_command_id()
            assert cmd_id is not None
            rcpt = client.receipt(cmd_id)
            assert rcpt is not None
            assert rcpt.status == ReceiptStatus.RESOLVED

            # Call SymbolInfo.SymbolsGet
            symbols = await client.call(
                object_id="client",
                class_name="SymbolInfo",
                method_name="SymbolsGet",
                args=[],
            )
            assert symbols == []

            # Call TerminalInfo
            terminal = await client.call(
                object_id="client",
                class_name="TerminalInfo",
                method_name="TerminalInfo",
                args=[],
            )
            assert isinstance(terminal, TerminalInfo)
            assert terminal.name == "base_trading"
            assert terminal.connected is True
            assert terminal.trade_allowed is False

            # Unsupported method raises BridgeError and sets REJECTED receipt
            with pytest.raises(
                BridgeError, match=r"base_trading does not support Nonexistent\.Foo"
            ):
                await client.call(
                    object_id="client",
                    class_name="Nonexistent",
                    method_name="Foo",
                    args=[],
                )
            unsupported_cmd_id = client.last_command_id()
            assert unsupported_cmd_id is not None
            unsupported_rcpt = client.receipt(unsupported_cmd_id)
            assert unsupported_rcpt is not None
            assert unsupported_rcpt.status == ReceiptStatus.REJECTED

        asyncio.run(run_calls())
