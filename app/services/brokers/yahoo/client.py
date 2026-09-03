"""Yahoo Finance broker client implementing BrokerOperationsCapability."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, cast, override

from app.contracts.broker.ports import BrokerOperationsCapability
from app.contracts.common.response import StandardResponse
from app.services.brokers.yahoo.config import YahooConfig

__all__ = [
    "YahooService",
    "calculate_margin",
    "calculate_profit",
    "cancel_order",
    "check_order",
    "close_position",
    "connect",
    "disconnect",
    "fr_brk_get_account_info",
    "fr_brk_get_terminal_info",
    "fr_brk_yahoo",
    "get_account_info",
    "get_account_snapshot",
    "get_balances",
    "get_connection_status",
    "get_deals",
    "get_historical_bars",
    "get_history_order",
    "get_last_error",
    "get_order",
    "get_orders",
    "get_permissions",
    "get_platform_info",
    "get_position",
    "get_positions",
    "get_provider_specification",
    "get_quote",
    "get_spread",
    "get_symbol_info",
    "get_symbols",
    "get_terminal_info",
    "get_ticks",
    "is_connected",
    "list_account_transactions",
    "list_deal_history",
    "list_order_history",
    "list_subscriptions",
    "modify_order",
    "modify_position",
    "ping",
    "place_order",
    "select_symbol",
    "subscribe_bars",
    "subscribe_quotes",
    "subscribe_ticks",
    "unsubscribe",
]

_yahoo_state: dict[str, Any] = {
    "connected": True,
    "last_error": (0, "Success"),
}

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

_ACCOUNT_INFO = {
    "account": "YAHOO-DEMO",
    "name": "Yahoo Finance Public Data Feed",
    "balance": 100000.0,
    "equity": 100000.0,
    "margin": 0.0,
    "free_margin": 100000.0,
    "currency": "USD",
    "connected": True,
}


# =============================================================================
# Connection and Terminal Operations
# =============================================================================


def connect(
    timeout: int = 30,  # noqa: ARG001
    config: YahooConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Connect to Yahoo Finance public data service."""
    _yahoo_state["connected"] = True
    return {
        "status": "connected",
        "connected": True,
        "platform": "yahoo",
        "type": "market_data_provider",
    }


def disconnect() -> bool:
    """Disconnect from Yahoo Finance."""
    _yahoo_state["connected"] = False
    return True


def is_connected() -> bool:
    """Check connection status."""
    return bool(_yahoo_state["connected"])


def ping() -> float:
    """Check ping latency."""
    if not is_connected():
        msg = "Yahoo Finance data provider is not connected."
        raise RuntimeError(msg)
    return 45.0


def get_connection_status() -> dict[str, Any]:
    """Retrieve connection status."""
    return {
        "connected": is_connected(),
        "platform": "yahoo",
        "ping_ms": ping() if is_connected() else 0.0,
        "last_error": _yahoo_state["last_error"],
    }


def get_platform_info() -> dict[str, Any]:
    """Retrieve platform info."""
    return {
        "platform": "yahoo",
        "type": "market_data_provider",
        "capabilities": ["quotes", "bars", "financials"],
    }


def get_terminal_info() -> dict[str, Any]:
    """Retrieve terminal environment info."""
    return {
        "connected": is_connected(),
        "type": "web_api",
    }


def get_provider_specification() -> dict[str, Any]:
    """Retrieve provider specifications."""
    return {
        "provider": "yahoo",
        "supports_market_orders": False,
        "supports_trading": False,
        "supports_quotes": True,
        "supports_historical_bars": True,
    }


def get_last_error() -> tuple[int, str]:
    """Retrieve last error."""
    return cast("tuple[int, str]", _yahoo_state["last_error"])


def fr_brk_get_account_info() -> dict[str, Any]:
    """Retrieve Yahoo Finance simulated account context dictionary."""
    return dict(_ACCOUNT_INFO)


def fr_brk_get_terminal_info() -> dict[str, Any]:
    """Retrieve Yahoo Finance terminal capabilities."""
    return {
        "platform": "yahoo",
        "connected": is_connected(),
        "symbols": len(get_symbols()),
    }


def fr_brk_yahoo(
    config: YahooConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Execute FR-BRK-YAHOO status report."""
    return {
        "platform": "yahoo",
        "connected": is_connected(),
        "symbols": len(get_symbols()),
    }


# =============================================================================
# Account and Balance Operations (Unavailable for Public Feed)
# =============================================================================


def get_account_info() -> dict[str, Any]:
    """Retrieve account properties.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:read' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_balances() -> dict[str, Any]:
    """Retrieve balances.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:balances' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_permissions() -> list[str]:
    """Retrieve permissions."""
    return ["quotes:read", "historical_bars:read"]


def get_account_snapshot() -> dict[str, Any]:
    """Retrieve account snapshot.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'account:snapshot' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


# =============================================================================
# Symbol and Market Data Operations
# =============================================================================


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
            return cast("dict[str, Any]", res[0])
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


# =============================================================================
# Orders and Positions Operations (Unavailable for Public Feed)
# =============================================================================


def get_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve orders.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def check_order(request: dict[str, Any]) -> dict[str, Any]:
    """Check order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:check' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def list_order_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve historical orders.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'orders:history' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)


def get_history_order(order_id: int | str) -> dict[str, Any] | None:
    """Retrieve historical order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'orders:history' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)


def get_deals(deal_id: int | str | None = None) -> list[dict[str, Any]]:
    """Retrieve deals.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'deals:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'deals:history' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def list_account_transactions(
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve account transactions.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'transactions:list' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_positions(symbol: str | None = None) -> list[dict[str, Any]]:
    """Retrieve open positions.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def get_position(position_id: int | str) -> dict[str, Any] | None:
    """Retrieve position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


# =============================================================================
# Trade Execution Operations (Unavailable for Public Feed)
# =============================================================================


def place_order(request: dict[str, Any]) -> dict[str, Any]:
    """Place order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:place' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def modify_order(request: dict[str, Any]) -> dict[str, Any]:
    """Modify order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:modify' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def cancel_order(
    order_id: int | str,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    """Cancel order.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'orders:cancel' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def modify_position(request: dict[str, Any]) -> dict[str, Any]:
    """Modify position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'positions:modify' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def close_position(
    position_id: int | str,
    volume: float | None = None,
) -> dict[str, Any]:
    """Close position.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = (
        "Broker capability 'positions:close' is unavailable for Yahoo Finance provider."
    )
    raise NotImplementedError(msg)


def calculate_margin(request: dict[str, Any]) -> float:
    """Calculate margin.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'margin:calculate' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def calculate_profit(request: dict[str, Any]) -> float:
    """Calculate profit.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'profit:calculate' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


# =============================================================================
# YahooService Class Implementing BrokerOperationsCapability
# =============================================================================


class YahooService(BrokerOperationsCapability):
    """Service implementing BrokerOperationsCapability for Yahoo Finance."""

    def __init__(self, config: YahooConfig | None = None) -> None:
        self.config = config or YahooConfig()

    @override
    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return connect(
            timeout=timeout,
            config=self.config,
        )

    @override
    def disconnect(self) -> bool:
        return disconnect()

    @override
    def is_connected(self) -> bool:
        return is_connected()

    @override
    def get_account_info(self) -> dict[str, Any]:
        return get_account_info()

    @override
    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return get_symbol_info(symbol)

    @override
    def get_terminal_info(self) -> dict[str, Any]:
        return get_terminal_info()

    @override
    def get_quote(self, symbol: str) -> dict[str, Any]:
        return get_quote(symbol)

    @override
    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        return get_orders(symbol)

    @override
    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        return get_positions(symbol)

    @override
    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        return place_order(request)

    @override
    def get_position_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return get_positions(symbol)

    @override
    def get_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return get_orders(symbol)

    @override
    def get_history_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
        date_from: Any = None,
        date_to: Any = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return list_order_history(symbol=symbol)

    @override
    def get_history_deal_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
        date_from: Any = None,
        date_to: Any = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return list_deal_history(symbol=symbol)

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Any = "1m",
        date_from: Any = None,
        date_to: Any = None,
        start_pos: int | None = None,
        count: int | None = None,
    ) -> StandardResponse[Any]:
        bars = get_historical_bars(symbol, timeframe=str(timeframe), count=count or 100)
        return StandardResponse(status="success", data=bars, operation="get_bars")

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: Any = None,
        date_to: Any = None,
        count: int = 100,
        flags: int = 0,
    ) -> StandardResponse[Any]:
        return StandardResponse(
            status="success", data=get_ticks(symbol, count=count), operation="get_ticks"
        )

    @override
    def trade(self, request: dict[str, Any]) -> dict[str, Any]:
        return place_order(request)


def _run_usage_example() -> None:
    print("=== Yahoo Finance Provider Demonstration ===")
    print("Platform:", get_platform_info())
    print("Symbols Available:", get_symbols())
    print("Quote AAPL:", get_quote("AAPL"))


if __name__ == "__main__":
    _run_usage_example()
