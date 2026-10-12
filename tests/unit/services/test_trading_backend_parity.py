"""Verify native forwarding and shared result/authorization contracts.

Description:
    Compare canonical simulator results with bounded native bridge responses.
    A fake writer verifies real timeout uncertainty without a live connection.

Purpose:
    FEAT-TRADING-BACKEND-PARITY: Protect backend-independent calling behavior.

Key Capabilities:
    - FR-TRADING-BACKEND-PARITY: Verify results, dispatch and trade safety.
      Associated: `Trading`, `MT5Backend`, `SimulationBackend`, `Bridge`
      Logging: Only operation metadata from production code is exercised.

Python API Usage:
    Run through pytest; native responses are explicit fixtures, not certification.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_backend_parity.py --no-cov
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.brokers import _simulation_api, simulator
from app.services.brokers.contracts import BridgeError, PropertyValue, SymbolSpec
from app.services.brokers.metatrader import MT5Backend
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import Trading


def test_native_forwarding_and_result_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Native and local operations expose identical facade classes/types."""

    async def scenario() -> None:
        native = MT5Backend(
            auth_token="isolated-test-token", journal_path=tmp_path / "native.db"
        )
        model = SimulationBackend()
        model.add_symbol(SymbolSpec(name="EURUSD"))
        local = Trading(model)
        call = AsyncMock(
            side_effect=[10_000.0, True, "EURUSD", {"ok": True, "value": 0.00001}, 0]
        )
        monkeypatch.setattr(native.bridge, "call", call)
        try:
            assert type(native.account) is type(local.account)
            assert await native.account.Balance() == await local.account.Balance()
            assert await native.symbol.Name("EURUSD") == await local.symbol.Name(
                "EURUSD"
            )
            assert await native.symbol.Name() == await local.symbol.Name()
            assert (
                await native.symbol.InfoDouble("point")
                == await local.symbol.InfoDouble("point")
                == PropertyValue(ok=True, value=0.00001)
            )
            first = call.call_args_list[0].kwargs
            assert first["class_name"] == "AccountInfo"
            assert first["method_name"] == "Balance"
            assert not first["requires_arm"]
            assert first["args"] == []
            assert first["object_id"] == native.account.object_id
            native_mode = await native.account.TradeMode()
            local_mode = await local.account.TradeMode()
            assert type(native_mode) is type(local_mode) is int
            assert native_mode == local_mode
        finally:
            await native.close()
            await local.close()

    asyncio.run(scenario())


def test_expiration_and_naive_time_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both backends receive integer expiration values; naive times fail early."""

    async def scenario() -> None:
        backend = MT5Backend(
            auth_token="isolated-test-token", journal_path=tmp_path / "expiration.db"
        )
        call = AsyncMock(return_value=True)
        monkeypatch.setattr(backend.bridge, "call", call)
        try:
            when = datetime(2026, 1, 1, tzinfo=UTC)
            await backend.trade.BuyLimit(0.1, 1.0, "EURUSD", 0.0, 0.0, 2, when)
            assert call.call_args.kwargs["requires_arm"]
            assert call.call_args.kwargs["args"][6] == int(when.timestamp())
            with pytest.raises(ValueError, match="timezone"):
                await backend.trade.BuyLimit(
                    0.1, 1.0, "EURUSD", 0.0, 0.0, 2, when.replace(tzinfo=None)
                )
            assert call.call_count == 1
        finally:
            await backend.close()

    asyncio.run(scenario())


def test_simulation_logs_exclude_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Native-style print helpers and dispatch logs do not reveal comments."""
    model_logger = Mock()
    handler_logger = Mock()
    monkeypatch.setattr(simulator, "logger", model_logger)
    monkeypatch.setattr(_simulation_api, "logger", handler_logger)

    async def scenario() -> None:
        model = SimulationBackend()
        model.add_symbol(SymbolSpec(name="EURUSD"))
        model.feed_tick("EURUSD", bid=1.1, ask=1.1002)
        facade = Trading(model)
        facade.arm()
        assert await facade.trade.Buy(
            0.1, "EURUSD", 0.0, 0.0, 0.0, "private-comment-marker"
        )
        assert await facade.trade.PrintRequest()
        assert await facade.trade.PrintResult()
        await facade.close()

    asyncio.run(scenario())
    assert model_logger.debug.call_count > 0
    assert handler_logger.debug.call_count > 0
    assert handler_logger.info.call_count == 2
    assert "private-comment-marker" not in repr(model_logger.mock_calls)
    assert "private-comment-marker" not in repr(handler_logger.mock_calls)


class _Writer:
    """Bounded transport that accepts bytes and never responds."""

    def write(self, data: bytes) -> None:
        pass

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass


def test_native_timeout_retains_uncertainty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A transmitted trade timeout still disarms through the canonical API."""

    async def scenario() -> None:
        backend = MT5Backend(
            auth_token="isolated-test-token",
            journal_path=tmp_path / "timeout.db",
            command_timeout=0.001,
        )
        bridge = backend.bridge
        monkeypatch.setattr(bridge, "_writer", _Writer())
        monkeypatch.setattr(bridge, "_authenticated", True)
        bridge._connected.set()
        try:
            facade = Trading(backend)
            facade.arm()
            with pytest.raises(BridgeError, match="timed out") as error:
                await facade.trade.Buy(0.1, "EURUSD")
            assert error.value.uncertain
            assert not bridge.armed
            command = facade.trade.last_command_id
            assert command is not None
            receipt = bridge.receipt(command)
            assert receipt is not None
            assert receipt.status == "uncertain"
        finally:
            await backend.close()

    asyncio.run(scenario())
