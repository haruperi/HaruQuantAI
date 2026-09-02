"""FR 3: Symbol Specifications, Quotes, Market Data, and Subscriptions."""

from __future__ import annotations

import time
import uuid
from typing import Any

_symbols_db: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "symbol": "EURUSD",
        "base_currency": "EUR",
        "quote_currency": "USD",
        "digits": 5,
        "point": 0.00001,
        "spread": 1.2,
        "lot_min": 0.01,
        "lot_max": 100.0,
        "lot_step": 0.01,
        "contract_size": 100000.0,
        "bid": 1.08500,
        "ask": 1.08512,
        "selected": True,
    },
    "GBPUSD": {
        "symbol": "GBPUSD",
        "base_currency": "GBP",
        "quote_currency": "USD",
        "digits": 5,
        "point": 0.00001,
        "spread": 1.5,
        "lot_min": 0.01,
        "lot_max": 100.0,
        "lot_step": 0.01,
        "contract_size": 100000.0,
        "bid": 1.26400,
        "ask": 1.26415,
        "selected": True,
    },
    "USDJPY": {
        "symbol": "USDJPY",
        "base_currency": "USD",
        "quote_currency": "JPY",
        "digits": 3,
        "point": 0.001,
        "spread": 1.0,
        "lot_min": 0.01,
        "lot_max": 100.0,
        "lot_step": 0.01,
        "contract_size": 100000.0,
        "bid": 154.200,
        "ask": 154.210,
        "selected": True,
    },
    "BTCUSD": {
        "symbol": "BTCUSD",
        "base_currency": "BTC",
        "quote_currency": "USD",
        "digits": 2,
        "point": 0.01,
        "spread": 5.0,
        "lot_min": 0.001,
        "lot_max": 10.0,
        "lot_step": 0.001,
        "contract_size": 1.0,
        "bid": 65000.0,
        "ask": 65005.0,
        "selected": True,
    },
}

_subscriptions: dict[str, dict[str, Any]] = {}


def get_symbols() -> list[str]:
    """Retrieve list of all available symbol names.

    Returns:
        List of symbol strings.
    """
    return sorted(_symbols_db.keys())


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve full specification and trading rules for a symbol.

    Args:
        symbol: Symbol ticker (e.g. 'EURUSD').

    Returns:
        Dictionary containing symbol specification.

    Raises:
        ValueError: If symbol is not supported.
    """
    sym = symbol.upper()
    if sym not in _symbols_db:
        msg = f"Symbol '{symbol}' not found in broker specification."
        raise ValueError(msg)
    return dict(_symbols_db[sym])


def select_symbol(symbol: str, selected: bool = True) -> bool:
    """Select or deselect a symbol in Market Watch / active tracking.

    Args:
        symbol: Symbol ticker.
        selected: Whether the symbol should be selected.

    Returns:
        True if symbol was updated.
    """
    sym = symbol.upper()
    if sym in _symbols_db:
        _symbols_db[sym]["selected"] = selected
        return True
    return False


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve the latest bid/ask quote and timestamp for a symbol.

    Args:
        symbol: Symbol ticker.

    Returns:
        Dictionary with bid, ask, spread, and timestamp.
    """
    sym_info = get_symbol_info(symbol)
    return {
        "symbol": sym_info["symbol"],
        "bid": sym_info["bid"],
        "ask": sym_info["ask"],
        "spread": sym_info["spread"],
        "time": time.time(),
    }


def get_spread(symbol: str) -> float:
    """Retrieve the current spread for a symbol.

    Args:
        symbol: Symbol ticker.

    Returns:
        Current spread as float.
    """
    return float(get_symbol_info(symbol)["spread"])


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent tick data for a symbol.

    Args:
        symbol: Symbol ticker.
        count: Maximum number of ticks to return.

    Returns:
        List of tick dictionaries.
    """
    sym_info = get_symbol_info(symbol)
    now = time.time()
    ticks = []
    for i in range(min(count, 500)):
        t = now - (count - i) * 0.5
        ticks.append(
            {
                "symbol": sym_info["symbol"],
                "time": t,
                "bid": sym_info["bid"] + (i * 0.00001),
                "ask": sym_info["ask"] + (i * 0.00001),
                "volume": 1.0,
            }
        )
    return ticks


def get_historical_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
) -> list[dict[str, Any]]:
    """Retrieve historical OHLCV bars for a symbol and timeframe.

    Args:
        symbol: Symbol ticker.
        timeframe: Bar timeframe (e.g. '1m', '5m', '1h', '1d').
        start: Optional start timestamp.
        end: Optional end timestamp.
        count: Maximum number of bars.

    Returns:
        List of OHLCV bar dictionaries.
    """
    sym_info = get_symbol_info(symbol)
    base_price = float(sym_info["bid"])
    now = time.time()
    step = 60 if timeframe == "1m" else 300
    bars = []
    for i in range(min(count, 500)):
        t = now - (count - i) * step
        bars.append(
            {
                "symbol": sym_info["symbol"],
                "time": t,
                "timeframe": timeframe,
                "open": round(base_price - 0.0005, 5),
                "high": round(base_price + 0.0010, 5),
                "low": round(base_price - 0.0008, 5),
                "close": round(base_price, 5),
                "volume": 150.0,
            }
        )
    return bars


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to streaming quotes for given symbols.

    Args:
        symbols: List of symbol tickers.

    Returns:
        Subscription ID.
    """
    sub_id = f"sub_quotes_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
        "created_at": time.time(),
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to streaming tick data for given symbols.

    Args:
        symbols: List of symbol tickers.

    Returns:
        Subscription ID.
    """
    sub_id = f"sub_ticks_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
        "created_at": time.time(),
    }
    return sub_id


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to streaming bar updates for given symbols.

    Args:
        symbols: List of symbol tickers.
        timeframe: Bar timeframe.

    Returns:
        Subscription ID.
    """
    sub_id = f"sub_bars_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "bars",
        "symbols": [s.upper() for s in symbols],
        "timeframe": timeframe,
        "created_at": time.time(),
    }
    return sub_id


def unsubscribe(sub_id: str) -> bool:
    """Cancel an active market data subscription.

    Args:
        sub_id: Subscription identifier.

    Returns:
        True if subscription existed and was removed.
    """
    if sub_id in _subscriptions:
        del _subscriptions[sub_id]
        return True
    return False


def list_subscriptions() -> list[dict[str, Any]]:
    """List all currently active market data subscriptions.

    Returns:
        List of subscription dictionaries.
    """
    return list(_subscriptions.values())
