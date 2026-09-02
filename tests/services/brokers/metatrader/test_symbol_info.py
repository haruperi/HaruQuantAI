"""Unit tests for MetaTrader 5 FR 3: Symbol Specifications and Subscriptions."""

from __future__ import annotations

from unittest.mock import MagicMock

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
from app.services.brokers.metatrader.client import MetaTraderClient


def test_symbols_and_quotes_success() -> None:
    """Verify symbols, info, and quote retrieval via client instance."""
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

    mock_mt5 = MagicMock()
    mock_mt5.symbols_get.return_value = (sym1, sym2)
    mock_mt5.symbol_info.side_effect = lambda s: mock_info if s == "EURUSD" else None
    mock_mt5.symbol_info_tick.side_effect = lambda s: (
        mock_tick if s == "EURUSD" else None
    )
    mock_mt5.symbol_select.side_effect = lambda s, e: s == "EURUSD"
    mock_mt5.last_error.return_value = (-1, "Not found")

    client = MetaTraderClient(mt5_module=mock_mt5)

    symbols = get_symbols(client=client)
    assert symbols == ["EURUSD", "GBPUSD"]

    info = get_symbol_info("EURUSD", client=client)
    assert info["name"] == "EURUSD"

    with pytest.raises(ValueError, match="Symbol 'INVALID' not found in MetaTrader 5"):
        get_symbol_info("INVALID", client=client)

    assert select_symbol("EURUSD", True, client=client) is True

    quote = get_quote("EURUSD", client=client)
    assert quote["bid"] == 1.08500
    assert quote["ask"] == 1.08512
    assert quote["spread"] == pytest.approx(0.00012, rel=1e-3)

    assert get_spread("EURUSD", client=client) == pytest.approx(0.00012, rel=1e-3)


def test_ticks_and_bars_success() -> None:
    """Verify tick data and historical bar queries via client instance."""
    mock_ticks = [(1788375000, 1.08500, 1.08512, 0.0, 1.0)]
    mock_rates = [(1788375000, 1.08450, 1.08550, 1.08420, 1.08500, 100.0, 0, 0)]

    mock_mt5 = MagicMock()
    mock_mt5.copy_ticks_from.return_value = mock_ticks
    mock_mt5.copy_rates_from_pos.return_value = mock_rates

    client = MetaTraderClient(mt5_module=mock_mt5)

    ticks = get_ticks("EURUSD", count=1, client=client)
    assert len(ticks) == 1
    assert ticks[0]["bid"] == 1.08500

    bars = get_historical_bars("EURUSD", timeframe="1m", count=1, client=client)
    assert len(bars) == 1
    assert bars[0]["open"] == 1.08450


def test_symbols_failure_raises_error() -> None:
    """Verify symbols query failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.symbols_get.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve symbols from MetaTrader 5"
    ):
        get_symbols(client=client)


def test_subscriptions() -> None:
    """Verify subscribing and unsubscribing via client instance."""
    mock_mt5 = MagicMock()
    mock_mt5.symbol_select.return_value = True

    client = MetaTraderClient(mt5_module=mock_mt5)

    sub_q = subscribe_quotes(["EURUSD"], client=client)
    assert sub_q.startswith("mt5_sub_quotes_")

    sub_t = subscribe_ticks(["EURUSD"], client=client)
    assert sub_t.startswith("mt5_sub_ticks_")

    sub_b = subscribe_bars(["EURUSD"], "1m", client=client)
    assert sub_b.startswith("mt5_sub_bars_")

    subs = list_subscriptions(client=client)
    assert len(subs) >= 3

    assert unsubscribe(sub_q, client=client) is True
    assert unsubscribe("nonexistent_sub", client=client) is False
