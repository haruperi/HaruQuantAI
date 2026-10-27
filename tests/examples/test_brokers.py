"""Exercise the trading walkthrough exclusively against the seeded simulator."""

import asyncio
from unittest.mock import AsyncMock

import pandas as pd
import pytest
from app.include.contracts import SymbolInfo, SymbolTrade
from app.include.enums import OrderFilling
from app.workspace.trading import Trading
from scripts.examples import brokers


@pytest.mark.parametrize(
    "modes,execution,expected",
    [
        (["Fill or Kill", "Immediate or Cancel"], "Market", OrderFilling.FOK),
        (["Immediate or Cancel"], "Market", OrderFilling.IOC),
        ([], "Exchange", OrderFilling.RETURN),
    ],
)
def test_example_filling_uses_nested_trade_policy(modes, execution, expected):
    info = SymbolInfo(trade=SymbolTrade(filling=modes, execution=execution))
    assert brokers._symbol_filling(info) == expected


def test_market_execution_requires_supported_filling():
    with pytest.raises(brokers.ExampleError, match="filling policy"):
        brokers._symbol_filling(SymbolInfo(trade=SymbolTrade(filling=[])))


def test_walkthrough_completes_on_simulator(monkeypatch, capsys):
    original_sleep = asyncio.sleep

    async def yield_without_delay(_seconds):
        await original_sleep(0)

    monkeypatch.setattr(brokers.asyncio, "sleep", yield_without_delay)
    backend = brokers.create_backend("simulator")
    asyncio.run(brokers.run_examples(backend, allow_writes=True))
    output = capsys.readouterr().out
    assert "Examples completed successfully." in output
    assert "Opened owned position" in output
    assert "Modified owned position" in output
    assert "Broker connection closed successfully" in output
    assert backend.positions() == []
    assert backend.orders() == []


def test_symbol_preview_accepts_mt5_tick_dictionary(monkeypatch, capsys):
    backend = brokers.create_backend("simulator")
    trading = Trading(backend)
    monkeypatch.setattr(
        trading.symbol, "SymbolInfoTick", AsyncMock(return_value={"last": 1.12345})
    )

    async def preview():
        await trading.start()
        try:
            await brokers.example_04_symbol(brokers.ExampleContext(trading))
        finally:
            await trading.close()

    asyncio.run(preview())
    assert "Last: 1.12345" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["bars", "ticks"])
def test_history_preview_preserves_returned_dataframe(monkeypatch, capsys, kind):
    frame = pd.DataFrame(
        {"Open": [42.5], "Close": [43.5]}
        if kind == "bars"
        else {"Bid": [42.5], "Ask": [43.5]},
        index=pd.to_datetime(["2026-01-01"], utc=True),
    )
    reader = AsyncMock(return_value=frame)
    monkeypatch.setattr(
        brokers, "get_historical_bars" if kind == "bars" else "get_ticks", reader
    )
    ctx = brokers.ExampleContext(Trading(brokers.create_backend("simulator")))
    example = (
        brokers.example_05_historical_bars
        if kind == "bars"
        else brokers.example_06_tick_data
    )
    asyncio.run(example(ctx))
    output = capsys.readouterr().out
    assert str(frame.head()) in output
    assert "1970-01-01" not in output


def test_history_read_retries_only_not_ready(monkeypatch):
    monkeypatch.setattr(brokers.asyncio, "sleep", AsyncMock())
    reader = AsyncMock(
        side_effect=[brokers.BridgeError("Loading", code="DATA_NOT_READY"), "ready"]
    )
    assert asyncio.run(brokers._read_history(reader)) == "ready"
    assert reader.await_count == 2
    reader = AsyncMock(
        side_effect=brokers.BridgeError("Loading", code="DATA_NOT_READY")
    )
    with pytest.raises(brokers.BridgeError):
        asyncio.run(brokers._read_history(reader))
    assert reader.await_count == 3
    reader = AsyncMock(
        side_effect=brokers.BridgeError("Disconnected", code="NOT_CONNECTED")
    )
    with pytest.raises(brokers.BridgeError):
        asyncio.run(brokers._read_history(reader))
    assert reader.await_count == 1


def test_read_only_cli_disables_order_writes(monkeypatch):
    runner = AsyncMock(return_value=[])
    monkeypatch.setattr(brokers, "run_examples", runner)
    monkeypatch.setattr(brokers, "create_backend", lambda name: object())
    monkeypatch.setattr(brokers, "ALLOW_LIVE_TRADING", True)
    assert brokers.main(["--read-only"]) == 0
    assert runner.call_args.kwargs["allow_writes"] is False
