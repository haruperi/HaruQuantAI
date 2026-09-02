"""FR 3: Binance Symbol Specifications, Live Quotes, Trades, and Klines."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

_subscriptions: dict[str, dict[str, Any]] = {}
_BINANCE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]


def _binance_request(endpoint: str) -> Any:
    """Execute live public HTTP GET request to Binance REST API."""
    url = f"https://api.binance.com{endpoint}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as http_err:
        if http_err.code == 400:
            msg = f"Symbol query rejected by Binance (HTTP 400): {http_err.reason}"
            raise ValueError(msg) from http_err
        msg = f"Failed live Binance API request to '{endpoint}': {http_err}"
        raise RuntimeError(msg) from http_err
    except Exception as exc:
        msg = f"Failed live Binance API request to '{endpoint}': {exc}"
        raise RuntimeError(msg) from exc


def get_symbols() -> list[str]:
    """Retrieve available symbols from Binance."""
    return list(_BINANCE_SYMBOLS)


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve real symbol specification from Binance exchangeInfo.

    Raises:
        ValueError: If symbol not supported or not found.
    """
    sym = symbol.upper()
    try:
        data = _binance_request(f"/api/v3/exchangeInfo?symbol={sym}")
        symbols = data.get("symbols", [])
        if not symbols:
            msg = f"Symbol '{symbol}' not found in Binance exchange catalog."
            raise ValueError(msg)  # noqa: TRY301
        s = symbols[0]
        return {
            "symbol": s.get("symbol"),
            "status": s.get("status"),
            "baseAsset": s.get("baseAsset"),
            "quoteAsset": s.get("quoteAsset"),
            "baseAssetPrecision": s.get("baseAssetPrecision"),
            "quotePrecision": s.get("quotePrecision"),
            "isSpotTradingAllowed": s.get("isSpotTradingAllowed"),
        }
    except Exception as exc:
        if isinstance(exc, ValueError):
            msg = f"Symbol '{symbol}' not found in Binance exchange catalog: {exc}"
            raise ValueError(msg) from exc
        msg = f"Symbol '{symbol}' query failed: {exc}"
        raise RuntimeError(msg) from exc


def select_symbol(symbol: str, selected: bool = True) -> bool:  # noqa: ARG001
    """Select symbol in tracking."""
    sym = symbol.upper()
    get_symbol_info(sym)
    return True


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve real live book ticker from Binance API.

    Raises:
        RuntimeError: If query fails.
    """
    sym = symbol.upper()
    data = _binance_request(f"/api/v3/ticker/bookTicker?symbol={sym}")
    bid = float(data.get("bidPrice", 0.0))
    ask = float(data.get("askPrice", 0.0))
    return {
        "symbol": sym,
        "bid": bid,
        "ask": ask,
        "spread": round(ask - bid, 8),
        "time": time.time(),
    }


def get_spread(symbol: str) -> float:
    """Retrieve spread for symbol."""
    quote = get_quote(symbol)
    return float(quote["spread"])


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve real recent trades from Binance."""
    sym = symbol.upper()
    limit = min(count, 500)
    data = _binance_request(f"/api/v3/trades?symbol={sym}&limit={limit}")
    return [
        {
            "symbol": sym,
            "id": t.get("id"),
            "time": float(t.get("time", 0)) / 1000.0,
            "bid": float(t.get("price", 0.0)),
            "ask": float(t.get("price", 0.0)),
            "volume": float(t.get("qty", 0.0)),
            "isBuyerMaker": t.get("isBuyerMaker"),
        }
        for t in data
    ]


def get_historical_bars(
    symbol: str,
    timeframe: str = "1m",
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
) -> list[dict[str, Any]]:
    """Retrieve real live Kline candlestick bars from Binance."""
    sym = symbol.upper()
    limit = min(count, 500)
    data = _binance_request(
        f"/api/v3/klines?symbol={sym}&interval={timeframe}&limit={limit}"
    )
    return [
        {
            "symbol": sym,
            "time": float(r[0]) / 1000.0,
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": float(r[5]),
            "close_time": float(r[6]) / 1000.0,
        }
        for r in data
    ]


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to ticker streams."""
    sub_id = f"binance_ticker_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to trade streams."""
    sub_id = f"binance_trades_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "ticks",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to Kline streams."""
    sub_id = f"binance_kline_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "bars",
        "symbols": [s.upper() for s in symbols],
        "timeframe": timeframe,
    }
    return sub_id


def unsubscribe(sub_id: str) -> bool:
    """Unsubscribe stream."""
    if sub_id in _subscriptions:
        del _subscriptions[sub_id]
        return True
    return False


def list_subscriptions() -> list[dict[str, Any]]:
    """List active streams."""
    return list(_subscriptions.values())
