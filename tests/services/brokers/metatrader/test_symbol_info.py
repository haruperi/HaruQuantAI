"""Unit tests for MetaTrader 5 FR 3: Symbol Specifications and Subscriptions."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._symbol_info as sym_mod
import pytest
from app.services.brokers.metatrader._symbol_info import (
    get_historical_bars,
    get_quote,
    get_spread,
    get_symbol_info,
    get_symbols,
    get_ticks,
    list_subscriptions,
    select_symbol,
    subscribe_bars,
    subscribe_quotes,
    subscribe_ticks,
    unsubscribe,
)


def test_symbols_and_quotes_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify symbols, info, and quote retrieval."""
    sym1 = MagicMock()
    sym1.name = "EURUSD"
    sym2 = MagicMock()
    sym2.name = "GBPUSD"

    mock_info = MagicMock()
    mock_info._asdict.return_value = {
        "name": "EURUSD",
        "digits": 5,
        "spread": 12,
        "trade_contract_size": 100000.0,
    }

    mock_tick = MagicMock()
    mock_tick.bid = 1.08500
    mock_tick.ask = 1.08512
    mock_tick.time = 1788375000.0

    monkeypatch.setattr(sym_mod.mt5, "symbols_get", lambda: (sym1, sym2))
    monkeypatch.setattr(
        sym_mod.mt5, "symbol_info", lambda s: mock_info if s == "EURUSD" else None
    )
    monkeypatch.setattr(
        sym_mod.mt5, "symbol_info_tick", lambda s: mock_tick if s == "EURUSD" else None
    )
    monkeypatch.setattr(sym_mod.mt5, "symbol_select", lambda s, e: s == "EURUSD")

    symbols = get_symbols()
    assert symbols == ["EURUSD", "GBPUSD"]

    info = get_symbol_info("EURUSD")
    assert info["name"] == "EURUSD"

    monkeypatch.setattr(sym_mod.mt5, "last_error", lambda: (-1, "Not found"))
    with pytest.raises(ValueError, match="Symbol 'INVALID' not found in MetaTrader 5"):
        get_symbol_info("INVALID")

    assert select_symbol("EURUSD", True) is True

    quote = get_quote("EURUSD")
    assert quote["bid"] == 1.08500
    assert quote["ask"] == 1.08512
    assert quote["spread"] == pytest.approx(0.00012, rel=1e-3)

    assert get_spread("EURUSD") == pytest.approx(0.00012, rel=1e-3)


def test_ticks_and_bars_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify tick data and historical bar queries."""
    mock_ticks = [(1788375000, 1.08500, 1.08512, 0.0, 1.0)]
    mock_rates = [(1788375000, 1.08450, 1.08550, 1.08420, 1.08500, 100.0, 0, 0)]

    monkeypatch.setattr(sym_mod.mt5, "copy_ticks_from", lambda s, t, c, f: mock_ticks)
    monkeypatch.setattr(
        sym_mod.mt5, "copy_rates_from_pos", lambda s, tf, p, c: mock_rates
    )

    ticks = get_ticks("EURUSD", count=1)
    assert len(ticks) == 1
    assert ticks[0]["bid"] == 1.08500

    bars = get_historical_bars("EURUSD", timeframe="1m", count=1)
    assert len(bars) == 1
    assert bars[0]["open"] == 1.08450


def test_symbols_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify symbols query failure raises RuntimeError."""
    monkeypatch.setattr(sym_mod.mt5, "symbols_get", lambda: None)
    monkeypatch.setattr(
        sym_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve symbols from MetaTrader 5"
    ):
        get_symbols()


def test_subscriptions() -> None:
    """Verify subscribing and unsubscribing."""
    sub_q = subscribe_quotes(["EURUSD"])
    assert sub_q.startswith("mt5_sub_quotes_")

    sub_t = subscribe_ticks(["EURUSD"])
    assert sub_t.startswith("mt5_sub_ticks_")

    sub_b = subscribe_bars(["EURUSD"], "1m")
    assert sub_b.startswith("mt5_sub_bars_")

    subs = list_subscriptions()
    assert len(subs) >= 3

    assert unsubscribe(sub_q) is True
    assert unsubscribe("nonexistent_sub") is False
