"""Unit tests for FR 3: Symbol Specifications, Quotes, and Subscriptions."""

from __future__ import annotations

import pytest
from app.services.brokers.operations._symbol_info import (
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


def test_symbols_and_quotes() -> None:
    """Verify symbol listing, info lookups, and quote queries."""
    symbols = get_symbols()
    assert "EURUSD" in symbols
    assert "GBPUSD" in symbols

    info = get_symbol_info("EURUSD")
    assert info["symbol"] == "EURUSD"
    assert info["contract_size"] == 100000.0

    with pytest.raises(ValueError, match="not found in broker specification"):
        get_symbol_info("INVALID_SYM")

    assert select_symbol("EURUSD", True) is True
    assert select_symbol("NONEXISTENT", True) is False

    quote = get_quote("EURUSD")
    assert quote["bid"] > 0
    assert quote["ask"] > quote["bid"]

    spread = get_spread("EURUSD")
    assert spread > 0


def test_ticks_and_historical_bars() -> None:
    """Verify tick data and historical bar generation."""
    ticks = get_ticks("EURUSD", count=10)
    assert len(ticks) == 10
    assert ticks[0]["bid"] > 0

    bars = get_historical_bars("EURUSD", timeframe="1m", count=20)
    assert len(bars) == 20
    assert "open" in bars[0]
    assert "high" in bars[0]
    assert "low" in bars[0]
    assert "close" in bars[0]


def test_market_data_subscriptions() -> None:
    """Verify subscribing and unsubscribing from quotes, ticks, and bars."""
    sub_q = subscribe_quotes(["EURUSD", "GBPUSD"])
    assert sub_q.startswith("sub_quotes_")

    sub_t = subscribe_ticks(["EURUSD"])
    assert sub_t.startswith("sub_ticks_")

    sub_b = subscribe_bars(["EURUSD"], "1m")
    assert sub_b.startswith("sub_bars_")

    subs = list_subscriptions()
    assert len(subs) >= 3

    assert unsubscribe(sub_q) is True
    assert unsubscribe("nonexistent_sub") is False
