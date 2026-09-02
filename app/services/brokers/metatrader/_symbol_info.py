"""FR 3: MetaTrader 5 Symbol Specifications, Quotes, and Subscriptions."""

from __future__ import annotations

import contextlib
import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.metatrader.client import MetaTraderClient

_TIMEFRAME_MAP_FALLBACK: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 16385,
    "4h": 16388,
    "1d": 16408,
    "1w": 32769,
}

_module_subscriptions: dict[str, dict[str, Any]] = {}


def _resolve_client(client: MetaTraderClient | Any | None = None) -> Any:
    """Resolve the provided client instance or fall back to the active default."""
    if client is not None:
        return client
    from app.services.brokers.metatrader.client import get_default_client

    return get_default_client()


def _get_subscriptions_registry(client_inst: Any) -> dict[str, dict[str, Any]]:
    """Return the client subscriptions dictionary, or module fallback."""
    if hasattr(client_inst, "subscriptions") and isinstance(
        client_inst.subscriptions, dict
    ):
        return client_inst.subscriptions
    return _module_subscriptions


def get_symbols(
    client: MetaTraderClient | Any | None = None,
) -> list[str]:
    """Retrieve list of all available symbol tickers in MetaTrader 5.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        List of symbol strings.

    Raises:
        RuntimeError: If symbols query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    symbols = mt5.symbols_get()
    if symbols is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Symbols query failed")
        )
        msg = f"Failed to retrieve symbols from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return sorted([s.name for s in symbols])


def get_symbol_info(
    symbol: str,
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve symbol specifications and trading limits.

    Args:
        symbol: Symbol ticker.
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary containing symbol specification.

    Raises:
        ValueError: If symbol is not found in MT5.
        RuntimeError: If MT5 package is unavailable.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    info = mt5.symbol_info(sym)
    if info is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Symbol query failed")
        )
        msg = f"Symbol '{symbol}' not found in MetaTrader 5: [{err[0]}] {err[1]}"
        raise ValueError(msg)

    return info._asdict()


def select_symbol(
    symbol: str,
    selected: bool = True,
    client: MetaTraderClient | Any | None = None,
) -> bool:
    """Select or deselect symbol in Market Watch.

    Args:
        symbol: Symbol ticker.
        selected: Enable or disable in Market Watch.
        client: Optional MetaTraderClient instance.

    Returns:
        True if successful.

    Raises:
        RuntimeError: If symbol select call fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    result = mt5.symbol_select(sym, selected)
    if not result:
        err = mt5.last_error() if hasattr(mt5, "last_error") else (-1, "Select failed")
        msg = f"Failed to select symbol '{symbol}' in MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)
    return True


def get_quote(
    symbol: str,
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve live quote for symbol.

    Args:
        symbol: Symbol ticker.
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary containing current bid, ask, and spread.

    Raises:
        RuntimeError: If quote query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Quote query failed")
        )
        msg = f"Failed to retrieve quote for '{symbol}' from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    bid = float(getattr(tick, "bid", 0.0))
    ask = float(getattr(tick, "ask", 0.0))
    t_val = float(getattr(tick, "time", time.time()))

    return {
        "symbol": sym,
        "bid": bid,
        "ask": ask,
        "spread": round(ask - bid, 5),
        "time": t_val,
    }


def get_spread(
    symbol: str,
    client: MetaTraderClient | Any | None = None,
) -> float:
    """Retrieve current spread for symbol in points/pip value.

    Args:
        symbol: Symbol ticker.
        client: Optional MetaTraderClient instance.

    Returns:
        Floating point spread value.
    """
    quote = get_quote(symbol, client=client)
    return float(quote["spread"])


def get_ticks(
    symbol: str,
    count: int = 100,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve historical tick records for symbol.

    Args:
        symbol: Symbol ticker.
        count: Number of recent ticks to return.
        client: Optional MetaTraderClient instance.

    Returns:
        List of tick dictionaries.

    Raises:
        RuntimeError: If tick history query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    copy_ticks_flag = getattr(mt5, "COPY_TICKS_ALL", -1)
    ticks = mt5.copy_ticks_from(sym, int(time.time()), count, copy_ticks_flag)
    if ticks is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Ticks query failed")
        )
        msg = f"Failed to retrieve ticks for '{symbol}' from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    result: list[dict[str, Any]] = []
    for t in ticks:
        result.append(
            {
                "symbol": sym,
                "time": float(t[0]),
                "bid": float(t[1]),
                "ask": float(t[2]),
                "last": float(t[3]),
                "volume": float(t[4]),
            }
        )
    return result


def get_historical_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve historical OHLCV bars for symbol.

    Args:
        symbol: Symbol ticker.
        timeframe: Bar timeframe string (1m, 5m, 1h, 1d, etc.).
        start: Optional start timestamp.
        end: Optional end timestamp.
        count: Maximum number of bars to retrieve.
        client: Optional MetaTraderClient instance.

    Returns:
        List of bar dictionaries.

    Raises:
        RuntimeError: If bar query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    sym = symbol.upper()
    tf_val = getattr(mt5, f"TIMEFRAME_M{timeframe[:-1]}", None)
    if tf_val is None:
        tf_val = _TIMEFRAME_MAP_FALLBACK.get(timeframe, 1)

    rates = mt5.copy_rates_from_pos(sym, tf_val, 0, count)
    if rates is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Rates query failed")
        )
        msg = f"Failed to retrieve bars for '{symbol}' from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    bars: list[dict[str, Any]] = []
    for r in rates:
        bars.append(
            {
                "symbol": sym,
                "time": float(r[0]),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "tick_volume": float(r[5]),
                "spread": int(r[6]),
                "real_volume": float(r[7]),
            }
        )
    return bars


def subscribe_quotes(
    symbols: list[str],
    client: MetaTraderClient | Any | None = None,
) -> str:
    """Subscribe to quote streaming updates for symbols.

    Args:
        symbols: List of symbol tickers.
        client: Optional MetaTraderClient instance.

    Returns:
        Subscription string handle.
    """
    client_inst = _resolve_client(client)
    registry = _get_subscriptions_registry(client_inst)
    sub_id = f"mt5_sub_quotes_{uuid.uuid4().hex[:8]}"
    for sym in symbols:
        with contextlib.suppress(Exception):
            select_symbol(sym, selected=True, client=client_inst)
    registry[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(
    symbols: list[str],
    client: MetaTraderClient | Any | None = None,
) -> str:
    """Subscribe to tick update streaming for symbols.

    Args:
        symbols: List of symbol tickers.
        client: Optional MetaTraderClient instance.

    Returns:
        Subscription string handle.
    """
    client_inst = _resolve_client(client)
    registry = _get_subscriptions_registry(client_inst)
    sub_id = f"mt5_sub_ticks_{uuid.uuid4().hex[:8]}"
    for sym in symbols:
        with contextlib.suppress(Exception):
            select_symbol(sym, selected=True, client=client_inst)
    registry[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_bars(
    symbols: list[str],
    timeframe: str,
    client: MetaTraderClient | Any | None = None,
) -> str:
    """Subscribe to bar update streaming for symbols and timeframe.

    Args:
        symbols: List of symbol tickers.
        timeframe: Bar timeframe string.
        client: Optional MetaTraderClient instance.

    Returns:
        Subscription string handle.
    """
    client_inst = _resolve_client(client)
    registry = _get_subscriptions_registry(client_inst)
    sub_id = f"mt5_sub_bars_{uuid.uuid4().hex[:8]}"
    for sym in symbols:
        with contextlib.suppress(Exception):
            select_symbol(sym, selected=True, client=client_inst)
    registry[sub_id] = {
        "id": sub_id,
        "type": "bars",
        "symbols": [s.upper() for s in symbols],
        "timeframe": timeframe,
    }
    return sub_id


def unsubscribe(
    sub_id: str,
    client: MetaTraderClient | Any | None = None,
) -> bool:
    """Cancel subscription by subscription handle.

    Args:
        sub_id: Subscription handle string.
        client: Optional MetaTraderClient instance.

    Returns:
        True if subscription existed and was removed.
    """
    client_inst = _resolve_client(client)
    registry = _get_subscriptions_registry(client_inst)
    if sub_id in registry:
        del registry[sub_id]
        return True
    return False


def list_subscriptions(
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """List active streaming subscriptions.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        List of subscription descriptor dictionaries.
    """
    client_inst = _resolve_client(client)
    registry = _get_subscriptions_registry(client_inst)
    return list(registry.values())
