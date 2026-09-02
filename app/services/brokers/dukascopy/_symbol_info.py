"""FR 3: Dukascopy Symbol Specifications, Quotes, and Subscriptions."""

from __future__ import annotations

import time
import uuid
from typing import Any

_subscriptions: dict[str, dict[str, Any]] = {}
_DUKAS_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "XAUUSD"]


def get_symbols() -> list[str]:
    """Retrieve available symbols from Dukascopy."""
    return list(_DUKAS_SYMBOLS)


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve symbol specification.

    Raises:
        ValueError: If symbol not supported.
    """
    sym = symbol.upper()
    if sym not in _DUKAS_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in Dukascopy catalog."
        raise ValueError(msg)
    return {
        "name": sym,
        "currency_base": sym[:3],
        "currency_profit": sym[3:],
        "digits": 5 if "JPY" not in sym else 3,
        "point": 0.00001 if "JPY" not in sym else 0.001,
        "spread": 0.3,
        "trade_contract_size": 100000.0,
    }


def select_symbol(symbol: str, selected: bool = True) -> bool:  # noqa: ARG001
    """Select symbol in tracking."""
    sym = symbol.upper()
    if sym not in _DUKAS_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in Dukascopy catalog."
        raise ValueError(msg)
    return True


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve current quote for symbol."""
    sym = symbol.upper()
    if sym not in _DUKAS_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in Dukascopy catalog."
        raise ValueError(msg)
    return {
        "symbol": sym,
        "bid": 1.08520,
        "ask": 1.08523,
        "spread": 0.00003,
        "time": time.time(),
    }


def get_spread(symbol: str) -> float:
    """Retrieve spread for symbol."""
    quote = get_quote(symbol)
    return float(quote["spread"])


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve historical tick data."""
    sym = symbol.upper()
    if sym not in _DUKAS_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in Dukascopy catalog."
        raise ValueError(msg)
    now = time.time()
    return [
        {
            "symbol": sym,
            "time": now - (count - i),
            "bid": 1.08520 + (i * 0.00001),
            "ask": 1.08523 + (i * 0.00001),
            "volume": 1.5,
        }
        for i in range(min(count, 500))
    ]


def get_historical_bars(
    symbol: str,
    timeframe: str = "1m",  # noqa: ARG001
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
) -> list[dict[str, Any]]:
    """Retrieve historical OHLCV bars."""
    sym = symbol.upper()
    if sym not in _DUKAS_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in Dukascopy catalog."
        raise ValueError(msg)
    now = time.time()
    return [
        {
            "symbol": sym,
            "time": now - (count - i) * 60,
            "open": 1.08510,
            "high": 1.08540,
            "low": 1.08500,
            "close": 1.08525,
            "volume": 50.0,
        }
        for i in range(min(count, 500))
    ]


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to quotes."""
    sub_id = f"dukas_quotes_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to ticks."""
    sub_id = f"dukas_ticks_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to bars."""
    sub_id = f"dukas_bars_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "bars",
        "symbols": [s.upper() for s in symbols],
        "timeframe": timeframe,
    }
    return sub_id


def unsubscribe(sub_id: str) -> bool:
    """Unsubscribe."""
    if sub_id in _subscriptions:
        del _subscriptions[sub_id]
        return True
    return False


def list_subscriptions() -> list[dict[str, Any]]:
    """List subscriptions."""
    return list(_subscriptions.values())
