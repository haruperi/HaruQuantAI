"""Yahoo Finance market data and symbol metadata broker plugin implementation.

Description:
    Implements a zero-credential, web-based market data and symbol metadata broker
    plugin querying Yahoo Finance v8 chart and v7 quote REST endpoints.
    Within the HaruQuantAI platform, Yahoo Finance serves as an unauthenticated,
    broad-coverage public data feed for global equities, indices, and currency
    pairs. It provides historical OHLCV candlestick trendbars for backtesting
    and live execution, as well as real-time symbol metadata lookups
    (`get_symbol_info()`) utilizing session crumb negotiation. All non-market-data
    and trading methods cleanly fallback to BaseBroker default unsupported
    capability handling.

Purpose:
    FEAT-BROKER-YAHOO: Public Market Data and Symbol Metadata Provider.
    Implements HTTP-based historical bar extraction and symbol metadata resolution
    from public Yahoo Finance endpoints.

Key Capabilities:
    - FR-BROKER-YAHOO-MARKET-DATA: Historical Candlestick Bars
      Associated: `[YahooBroker.get_bars()]`
      Logging: Emits INFO log upon parsing chart results, and WARNING log
      if symbol is not found or payload is malformed.
    - FR-BROKER-YAHOO-SYMBOL-METADATA: Symbol Metadata and Quote Resolution
      Associated: `[YahooBroker.get_symbol_info()]`, `[YahooBroker._ensure_crumb()]`
      Logging: Emits INFO log upon acquiring crumb or parsing quote response,
      and WARNING log if symbol is not found, request fails, or crumb errors.

Python API Usage:
    ```python
    from app.plugins.brokers.yahoo import YahooBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("AAPL", count=5)
    assert bars_resp.is_success
    info_resp = broker.get_symbol_info("AAPL")
    assert info_resp.is_success
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.brokers.yahoo
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, override

import requests

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardError,
    StandardResponse,
    SymbolInfo,
    TimeFrame,
)

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "data-source-yahoo",
    "name": "Yahoo Finance Feed",
    "version": "1.0.0",
    "description": (
        "Yahoo Finance historical daily and intraday market data provider plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "data.provider",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "Yahoo",
        "display_name": "Yahoo Finance",
        "asset_classes": ["Stocks", "Indices", "Commodities"],
        "timeframes": ["M1", "M5", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 5.0,
        "base_url": "https://query1.finance.yahoo.com",
    },
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)

TIMEFRAME_TO_YAHOO_INTERVAL = {
    TimeFrame.M1: "1m",
    TimeFrame.M2: "2m",
    TimeFrame.M5: "5m",
    TimeFrame.M15: "15m",
    TimeFrame.M30: "30m",
    TimeFrame.H1: "60m",
    TimeFrame.H4: "60m",
    TimeFrame.D1: "1d",
    TimeFrame.W1: "1wk",
    TimeFrame.MN1: "1mo",
}


__all__ = ["YahooBroker", "create_adapter"]


class YahooBroker(BaseBroker):
    """Yahoo Finance market data and symbol metadata broker plugin."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
    COOKIE_URL = "https://fc.yahoo.com"
    CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"

    def __init__(self, name: str = "Yahoo") -> None:
        """Initialize Yahoo Finance broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS,
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.crumb: str | None = None

    def _ensure_crumb(self) -> str | None:
        """Acquire and cache Yahoo Finance session cookie and crumb token.

        Returns:
            Cached or newly acquired crumb token, or None if acquisition fails.
        """
        if self.crumb is not None:
            return self.crumb
        try:
            self.session.get(self.COOKIE_URL, timeout=10)
            crumb_resp = self.session.get(self.CRUMB_URL, timeout=10)
            if crumb_resp.status_code == 200 and crumb_resp.text:
                crumb_val = crumb_resp.text.strip()
                if crumb_val and "<html>" not in crumb_val.lower():
                    self.crumb = crumb_val
                    logger.info("Acquired Yahoo Finance session crumb token.")
                    return self.crumb
            logger.warning(
                "Failed to acquire Yahoo Finance crumb: HTTP %s",
                crumb_resp.status_code,
            )
            return None
        except Exception as exc:
            logger.warning("Error negotiating Yahoo Finance crumb token: %s", exc)
            return None

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications and quote metadata from Yahoo v7 quote endpoint."""
        sym_clean = symbol.upper().strip()
        params: dict[str, Any] = {"symbols": sym_clean}
        crumb = self._ensure_crumb()
        if crumb:
            params["crumb"] = crumb

        try:
            resp = self.session.get(self.QUOTE_URL, params=params, timeout=15)
            if resp.status_code == 401 and not crumb:
                crumb = self._ensure_crumb()
                if crumb:
                    params["crumb"] = crumb
                    resp = self.session.get(self.QUOTE_URL, params=params, timeout=15)

            if resp.status_code != 200:
                msg = (
                    f"Failed to fetch symbol info for '{sym_clean}': HTTP "
                    f"{resp.status_code}"
                )
                logger.warning(
                    "Failed to fetch symbol info for '%s': HTTP %s",
                    sym_clean,
                    resp.status_code,
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(resp.status_code), message=msg),
                    extensions={"broker": self.name},
                )

            payload = resp.json()
            res_list = payload.get("quoteResponse", {}).get("result", [])
            if not res_list:
                msg = f"Symbol '{sym_clean}' not found on Yahoo Finance"
                logger.warning("Symbol '%s' not found on Yahoo Finance", sym_clean)
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
                    extensions={"broker": self.name},
                )

            item = res_list[0]
            short_name = (
                item.get("shortName")
                or item.get("longName")
                or item.get("symbol")
                or sym_clean
            )
            exchange = item.get("exchange") or "UNKNOWN"
            price = float(item.get("regularMarketPrice") or item.get("ask") or 0.0)
            bid = float(item.get("bid") or price)
            ask = float(item.get("ask") or price)

            info = SymbolInfo(
                name=sym_clean,
                custom=False,
                digits=2,
                point=0.01,
                bid=bid,
                ask=ask,
                last=price,
                currency_base=item.get("currency") or "USD",
                currency_profit=item.get("currency") or "USD",
                description=f"{short_name} ({exchange})",
                exchange=exchange,
                path=exchange,
                raw=item,
            )
            logger.info(
                "Retrieved Yahoo symbol info for '%s': %s on %s",
                sym_clean,
                short_name,
                exchange,
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{sym_clean}'",
                extensions={"broker": self.name},
            )
        except Exception as exc:
            msg = f"Error fetching symbol info for '{sym_clean}': {exc}"
            logger.warning(
                "Error fetching symbol info for '%s': %s",
                sym_clean,
                exc,
            )
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    def _map_interval(self, timeframe: TimeFrame | str | int) -> str:
        """Map standard TimeFrame to Yahoo Finance interval string."""
        if isinstance(timeframe, TimeFrame):
            return TIMEFRAME_TO_YAHOO_INTERVAL.get(timeframe, "1d")
        str_val = str(timeframe).upper().strip()
        for tf in TimeFrame:
            if tf.value == str_val:
                return TIMEFRAME_TO_YAHOO_INTERVAL.get(tf, "1d")
        for unit in ("MN", "M", "H", "D", "W"):
            if str_val.endswith(unit) and str_val[: -len(unit)].isdigit():
                reversed_val = f"{unit}{str_val[: -len(unit)]}"
                for tf in TimeFrame:
                    if tf.value == reversed_val:
                        return TIMEFRAME_TO_YAHOO_INTERVAL.get(tf, "1d")
        lower_val = str_val.lower()
        if lower_val in TIMEFRAME_TO_YAHOO_INTERVAL.values():
            return lower_val
        return "1d"

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Download candlestick bars from Yahoo Finance v8 chart API."""
        sym_clean = symbol.upper().strip()
        interval = self._map_interval(timeframe)
        params: dict[str, Any] = {
            "interval": interval,
            "events": "history",
        }

        if date_from and date_to:
            params["period1"] = int(date_from.timestamp())
            params["period2"] = int(date_to.timestamp())
        elif interval in ("1m", "2m", "5m"):
            params["range"] = "5d"
        elif interval in ("15m", "30m", "60m"):
            params["range"] = "1mo"
        elif interval in ("1d", "1wk"):
            params["range"] = "1y"
        else:
            params["range"] = "2y"

        try:
            url = self.CHART_URL.format(symbol=sym_clean)
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                msg = f"Failed to fetch bars for '{sym_clean}': HTTP {resp.status_code}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(resp.status_code), message=msg),
                    extensions={"broker": self.name},
                )
            payload = resp.json()
            res_list = payload.get("chart", {}).get("result", [])
            if not res_list:
                msg = f"No chart data for '{sym_clean}'"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )
            chart_res = res_list[0]
            timestamps = chart_res.get("timestamp", [])
            indicators = chart_res.get("indicators", {})
            quotes_list = indicators.get("quote", [])
            if not quotes_list or not timestamps:
                return StandardResponse.success(
                    data=[],
                    message="Empty bar set",
                    extensions={"broker": self.name},
                )

            q = quotes_list[0]
            opens = q.get("open", [])
            highs = q.get("high", [])
            lows = q.get("low", [])
            closes = q.get("close", [])
            volumes = q.get("volume", [])

            bars: list[Bar] = []
            for i, ts in enumerate(timestamps):
                if (
                    i < len(opens)
                    and opens[i] is not None
                    and closes[i] is not None
                    and highs[i] is not None
                    and lows[i] is not None
                ):
                    bar_dt = datetime.fromtimestamp(ts, tz=UTC)
                    vol = int(volumes[i] or 0) if i < len(volumes) else 0
                    bars.append(
                        Bar(
                            time=bar_dt,
                            open=float(opens[i]),
                            high=float(highs[i]),
                            low=float(lows[i]),
                            close=float(closes[i]),
                            tick_volume=vol,
                            real_volume=vol,
                        )
                    )

            if count and len(bars) > count:
                bars = bars[-count:]

            return StandardResponse.success(
                data=bars,
                message=f"Retrieved {len(bars)} bars for '{sym_clean}'",
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Error downloading bars for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )


def create_adapter(_context: PluginHostContext | None = None) -> YahooBroker:
    """Plugin entrypoint factory constructing the Yahoo Finance broker adapter."""
    logger.info("Initializing Yahoo Finance broker plugin adapter.")
    return YahooBroker()


if __name__ == "__main__":
    from app.plugins.brokers import get_bars, get_symbol_info

    yahoo = YahooBroker()

    y_info = get_symbol_info(broker=yahoo, symbol="AAPL")
    print(
        f"Symbol Info: {y_info.data.description if y_info.data else 'None'}, "
        f"Exchange: {y_info.data.exchange if y_info.data else 'None'}"
    )
    assert y_info.is_success
    assert y_info.data is not None

    y_bars = get_bars(broker=yahoo, symbol="AAPL", timeframe=TimeFrame.D1, count=5)
    print(f"Bars count: {len(y_bars.data) if y_bars.data else 0}")
    print(y_bars.data)
    assert y_bars.is_success
    assert y_bars.data is not None
    assert len(y_bars.data) == 5
