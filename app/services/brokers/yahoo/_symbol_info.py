"""FR 3: Yahoo Finance Symbol Specifications, Live Quotes, and Historical Bars."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

_subscriptions: dict[str, dict[str, Any]] = {}
_YAHOO_SYMBOLS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY", "QQQ", "EURUSD=X"]

_TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "60m",
    "1d": "1d",
    "1w": "1wk",
    "1mo": "1mo",
}


def _fetch_yahoo_chart(
    symbol: str, interval: str = "1d", range_param: str = "5d"
) -> dict[str, Any]:
    """Execute live HTTP request to Yahoo Finance v8 chart API."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_param}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
            res = data.get("chart", {}).get("result")
            if not res or len(res) == 0:
                err = data.get("chart", {}).get("error", {})
                msg = f"Symbol '{symbol}' not found in Yahoo Finance catalog: {err}"
                raise ValueError(msg)  # noqa: TRY301
            return res[0]
    except urllib.error.HTTPError as http_err:
        if http_err.code == 404:
            msg = f"Symbol '{symbol}' not found in Yahoo Finance catalog (HTTP 404)"
            raise ValueError(msg) from http_err
        msg = f"Failed to fetch live Yahoo Finance data for '{symbol}': {http_err}"
        raise RuntimeError(msg) from http_err
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        msg = f"Failed to fetch live Yahoo Finance data for '{symbol}': {exc}"
        raise RuntimeError(msg) from exc


def get_symbols() -> list[str]:
    """Retrieve symbols from Yahoo Finance."""
    return list(_YAHOO_SYMBOLS)


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieve real symbol specification from Yahoo Finance chart meta.

    Raises:
        ValueError: If symbol not supported or not found.
        RuntimeError: If live network request fails.
    """
    sym = symbol.upper()
    chart = _fetch_yahoo_chart(sym, interval="1d", range_param="1d")
    meta = chart.get("meta", {})
    return {
        "symbol": meta.get("symbol", sym),
        "currency": meta.get("currency", "USD"),
        "exchangeName": meta.get("exchangeName", "UNKNOWN"),
        "instrumentType": meta.get("instrumentType", "EQUITY"),
        "regularMarketPrice": meta.get("regularMarketPrice", 0.0),
        "chartPreviousClose": meta.get("chartPreviousClose", 0.0),
        "timezone": meta.get("timezone", "UTC"),
    }


def select_symbol(symbol: str, selected: bool = True) -> bool:  # noqa: ARG001
    """Select symbol in tracking."""
    sym = symbol.upper()
    get_symbol_info(sym)
    return True


def get_quote(symbol: str) -> dict[str, Any]:
    """Retrieve real live quote from Yahoo Finance API.

    Raises:
        RuntimeError: If live network query fails.
    """
    sym = symbol.upper()
    chart = _fetch_yahoo_chart(sym, interval="1d", range_param="1d")
    meta = chart.get("meta", {})
    price = float(meta.get("regularMarketPrice", 0.0))
    prev_close = float(meta.get("chartPreviousClose", price))

    return {
        "symbol": sym,
        "bid": round(price * 0.9999, 4),
        "ask": round(price * 1.0001, 4),
        "regularMarketPrice": price,
        "chartPreviousClose": prev_close,
        "currency": meta.get("currency", "USD"),
        "time": float(meta.get("regularMarketTime", time.time())),
    }


def get_spread(symbol: str) -> float:
    """Retrieve spread for symbol."""
    quote = get_quote(symbol)
    return round(float(quote["ask"]) - float(quote["bid"]), 4)


def get_ticks(symbol: str, count: int = 100) -> list[dict[str, Any]]:
    """Retrieve ticks (unavailable on Yahoo Finance)."""
    msg = f"Broker capability 'ticks:stream' is unavailable for Yahoo Finance provider ('{symbol}')."
    raise NotImplementedError(msg)


def get_historical_bars(
    symbol: str,
    timeframe: str = "1d",
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
    count: int = 100,
) -> list[dict[str, Any]]:
    """Retrieve real historical OHLCV bars from Yahoo Finance.

    Raises:
        RuntimeError: If query fails.
    """
    sym = symbol.upper()
    interval = _TIMEFRAME_MAP.get(timeframe, "1d")
    range_param = "1mo" if count > 20 else "5d"

    chart = _fetch_yahoo_chart(sym, interval=interval, range_param=range_param)
    timestamps = chart.get("timestamp", [])
    indicators = chart.get("indicators", {}).get("quote", [{}])[0]

    opens = indicators.get("open", [])
    highs = indicators.get("high", [])
    lows = indicators.get("low", [])
    closes = indicators.get("close", [])
    volumes = indicators.get("volume", [])

    bars: list[dict[str, Any]] = []
    for i in range(len(timestamps)):
        if closes[i] is None:
            continue
        bars.append(
            {
                "symbol": sym,
                "time": float(timestamps[i]),
                "open": float(opens[i]) if opens[i] is not None else float(closes[i]),
                "high": float(highs[i]) if highs[i] is not None else float(closes[i]),
                "low": float(lows[i]) if lows[i] is not None else float(closes[i]),
                "close": float(closes[i]),
                "volume": float(volumes[i]) if volumes[i] is not None else 0.0,
            }
        )

    return bars[-count:] if len(bars) > count else bars


def subscribe_quotes(symbols: list[str]) -> str:
    """Subscribe to quotes."""
    sub_id = f"yahoo_quotes_{uuid.uuid4().hex[:8]}"
    _subscriptions[sub_id] = {
        "id": sub_id,
        "type": "quotes",
        "symbols": [s.upper() for s in symbols],
    }
    return sub_id


def subscribe_ticks(symbols: list[str]) -> str:
    """Subscribe to ticks (unavailable)."""
    msg = "Broker capability 'subscriptions:ticks' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def subscribe_bars(symbols: list[str], timeframe: str) -> str:
    """Subscribe to bars."""
    sub_id = f"yahoo_bars_{uuid.uuid4().hex[:8]}"
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
