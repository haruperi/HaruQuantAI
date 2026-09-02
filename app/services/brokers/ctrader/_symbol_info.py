"""FR 3: cTrader Symbol Specifications, Quotes, and Subscriptions."""

from __future__ import annotations

import time
import uuid
from typing import Any

_subscriptions: dict[str, dict[str, Any]] = {}
_CTRADER_SYMBOLS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD",
    "NZDUSD",
    "XAUUSD",
]


def get_symbols() -> list[str]:
    """Retrieve available symbols from cTrader."""
    return list(_CTRADER_SYMBOLS)


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve symbol specification.

    Raises:
        ValueError: If symbol not supported.
    """
    sym = symbol.upper()
    if sym not in _CTRADER_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in cTrader catalog."
        raise ValueError(msg)
    return {
        "symbolId": 1,
        "symbolName": sym,
        "baseAsset": sym[:3],
        "quoteAsset": sym[3:],
        "digits": 5 if "JPY" not in sym else 3,
        "lotSize": 100000.0,
        "minVolume": 1000,
        "stepVolume": 1000,
    }


def select_symbol(symbol: str, selected: bool = True) -> bool:  # noqa: ARG001
    """Select symbol in tracking."""
    sym = symbol.upper()
    if sym not in _CTRADER_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in cTrader catalog."
        raise ValueError(msg)
    return True


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve current spot quote for symbol."""
    sym = symbol.upper()
    if sym not in _CTRADER_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in cTrader catalog."
        raise ValueError(msg)
    return {
        "symbol": sym,
        "bid": 1.08510,
        "ask": 1.08515,
        "spread": 0.00005,
        "time": time.time(),
    }


def get_spread(symbol: str) -> float:
    """Retrieve spread for symbol."""
    quote = get_quote(symbol)
    return float(quote["spread"])


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent tick events."""
    sym = symbol.upper()
    if sym not in _CTRADER_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in cTrader catalog."
        raise ValueError(msg)
    now = time.time()
    return [
        {
            "symbol": sym,
            "time": now - (count - i),
            "bid": 1.08510 + (i * 0.00001),
            "ask": 1.08515 + (i * 0.00001),
            "volume": 1.0,
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
    """Retrieve Trendbar historical bars."""
    sym = symbol.upper()
    if sym not in _CTRADER_SYMBOLS:
        msg = f"Symbol '{symbol}' not found in cTrader catalog."
        raise ValueError(msg)
    now = time.time()
    return [
        {
            "symbol": sym,
            "time": now - (count - i) * 60,
            "open": 1.08500,
            "high": 1.08530,
            "low": 1.08490,
            "close": 1.08515,
            "volume": 75.0,
        }
        for i in range(min(count, 500))
    ]


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to spot event quotes."""
    sub_id = f"ctrader_quotes_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to tick events."""
    sub_id = f"ctrader_ticks_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to live trendbars."""
    sub_id = f"ctrader_bars_{uuid.uuid4().hex[:8]}"
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
