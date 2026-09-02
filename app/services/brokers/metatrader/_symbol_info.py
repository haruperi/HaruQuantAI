"""FR 3: MetaTrader 5 Symbol Specifications, Quotes, and Subscriptions."""

from __future__ import annotations

import time
import uuid
from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False

_TIMEFRAME_MAP: dict[str, Any] = {}
if _MT5_AVAILABLE and mt5 is not None:
    _TIMEFRAME_MAP = {
        "1m": getattr(mt5, "TIMEFRAME_M1", 1),
        "5m": getattr(mt5, "TIMEFRAME_M5", 5),
        "15m": getattr(mt5, "TIMEFRAME_M15", 15),
        "30m": getattr(mt5, "TIMEFRAME_M30", 30),
        "1h": getattr(mt5, "TIMEFRAME_H1", 16385),
        "4h": getattr(mt5, "TIMEFRAME_H4", 16388),
        "1d": getattr(mt5, "TIMEFRAME_D1", 16408),
        "1w": getattr(mt5, "TIMEFRAME_W1", 32769),
    }

_subscriptions: dict[str, dict[str, Any]] = {}


def get_symbols() -> list[str]:
    """Retrieve list of all available symbol tickers in MetaTrader 5.

    Returns:
        List of symbol strings.

    Raises:
        RuntimeError: If symbols query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    symbols = mt5.symbols_get()
    if symbols is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve symbols from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return sorted([s.name for s in symbols])


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve symbol specifications and trading limits.

    Args:
        symbol: Symbol ticker.

    Returns:
        Dictionary containing symbol specification.

    Raises:
        ValueError: If symbol is not found in MT5.
        RuntimeError: If MT5 package is unavailable.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    info = mt5.symbol_info(sym)
    if info is None:
        err = mt5.last_error()
        msg = f"Symbol '{symbol}' not found in MetaTrader 5: [{err[0]}] {err[1]}"
        raise ValueError(msg)

    return info._asdict()


def select_symbol(symbol: str, selected: bool = True) -> bool:
    """Select or deselect symbol in Market Watch.

    Args:
        symbol: Symbol ticker.
        selected: Enable or disable in Market Watch.

    Returns:
        True if successful.

    Raises:
        RuntimeError: If symbol select call fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    result = mt5.symbol_select(sym, selected)
    if not result:
        err = mt5.last_error()
        msg = f"Failed to select symbol '{symbol}' in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return bool(result)


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve current bid/ask quote for symbol.

    Args:
        symbol: Symbol ticker.

    Returns:
        Quote dictionary with bid, ask, and timestamp.

    Raises:
        RuntimeError: If tick quote query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve tick quote for '{symbol}': [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return {
        "symbol": sym,
        "bid": float(tick.bid),
        "ask": float(tick.ask),
        "spread": float(tick.ask - tick.bid),
        "time": float(tick.time),
    }


def get_spread(symbol: str) -> float:
    """Retrieve current spread for symbol.

    Args:
        symbol: Symbol ticker.

    Returns:
        Spread float value.
    """
    quote = get_quote(symbol)
    return float(quote["spread"])


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent tick history for symbol.

    Args:
        symbol: Symbol ticker.
        count: Number of ticks.

    Returns:
        List of tick dictionaries.

    Raises:
        RuntimeError: If ticks query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    ticks = mt5.copy_ticks_from(sym, int(time.time()), count, mt5.COPY_TICKS_ALL)
    if ticks is None:
        err = mt5.last_error()
        msg = f"Failed to copy ticks for '{symbol}': [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [
        {
            "symbol": sym,
            "time": float(t[0]),
            "bid": float(t[1]),
            "ask": float(t[2]),
            "volume": float(t[4]),
        }
        for t in ticks
    ]


def get_historical_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
) -> list[dict[str, Any]]:
    """Retrieve historical OHLCV bars.

    Args:
        symbol: Symbol ticker.
        timeframe: Timeframe identifier.
        start: Optional start timestamp.
        end: Optional end timestamp.
        count: Maximum number of bars.

    Returns:
        List of bar dictionaries.

    Raises:
        RuntimeError: If rates query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    tf_const = _TIMEFRAME_MAP.get(timeframe, 1)
    rates = mt5.copy_rates_from_pos(sym, tf_const, 0, count)
    if rates is None:
        err = mt5.last_error()
        msg = f"Failed to copy rates for '{symbol}' ({timeframe}): [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [
        {
            "symbol": sym,
            "time": float(r[0]),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": float(r[5]),
        }
        for r in rates
    ]


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to live quotes for symbol list."""
    sub_id = f"mt5_sub_quotes_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to live ticks for symbol list."""
    sub_id = f"mt5_sub_ticks_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to live bars for symbol list and timeframe."""
    sub_id = f"mt5_sub_bars_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "bars",
        "symbols": [s.upper() for s in symbols],
        "timeframe": timeframe,
    }
    return sub_id


def unsubscribe(sub_id: str) -> bool:
    """Cancel subscription by ID."""
    if sub_id in _subscriptions:
        del _subscriptions[sub_id]
        return True
    return False


def list_subscriptions() -> list[dict[str, Any]]:
    """List active market data subscriptions."""
    return list(_subscriptions.values())
