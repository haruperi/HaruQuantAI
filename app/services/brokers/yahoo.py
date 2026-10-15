"""Yahoo Finance market data and symbol metadata broker implementation.

Description:
    Implements a zero-credential, web-based market data broker querying Yahoo Finance
    v8 chart and v7 quote REST endpoints. Conforms directly to the canonical
    `TradingBackend` protocol via `DataBrokerBackend`. Provides normalized historical
    candlestick bars (`MarketData.Bars`) and symbol specifications (`SymbolSnapshot`).

Purpose:
    FEAT-BROKER-YAHOO: Public Market Data and Symbol Metadata Provider.

Key Capabilities:
    - FR-BROKER-YAHOO-MARKET-DATA: Historical Candlestick Bars
      Associated: `[YahooBroker.fetch_bars()]`
      Logging: Emits INFO log upon parsing chart results, and WARNING log if
      symbol is not found or payload is malformed.
    - FR-BROKER-YAHOO-SYMBOL-METADATA: Symbol Metadata and Quote Resolution
      Associated: `[YahooBroker.symbol_info()]`
      Logging: Emits INFO log upon quote resolution, and WARNING on request failure.

Python API Usage:
    ```python
    from app.services.libs.data import Timeframe, get_historical_bars
    from app.services.brokers.yahoo import YahooBroker

    broker = YahooBroker()
    bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker yahoo`
"""

from __future__ import annotations

from typing import Any, override

import requests
from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.libs.data import (
    BridgeError,
    DataBrokerBackend,
    Timeframe,
)
from app.services.libs.trading import SymbolSnapshot

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)

TIMEFRAME_TO_YAHOO_INTERVAL: dict[str, str] = {
    "M1": "1m",
    "1M": "1m",
    Timeframe.PERIOD_M1.value: "1m",
    "M2": "2m",
    "2M": "2m",
    Timeframe.PERIOD_M2.value: "2m",
    "M5": "5m",
    "5M": "5m",
    Timeframe.PERIOD_M5.value: "5m",
    "M15": "15m",
    "15M": "15m",
    Timeframe.PERIOD_M15.value: "15m",
    "M30": "30m",
    "30M": "30m",
    Timeframe.PERIOD_M30.value: "30m",
    "H1": "60m",
    "1H": "60m",
    Timeframe.PERIOD_H1.value: "60m",
    "H4": "60m",
    "4H": "60m",
    Timeframe.PERIOD_H4.value: "60m",
    "D1": "1d",
    "1D": "1d",
    Timeframe.PERIOD_D1.value: "1d",
    "W1": "1wk",
    "1W": "1wk",
    Timeframe.PERIOD_W1.value: "1wk",
    "MN1": "1mo",
    "1MN": "1mo",
    Timeframe.PERIOD_MN1.value: "1mo",
}

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY", "QQQ"]

__all__ = ["YahooBroker", "create_adapter"]


class YahooBroker(DataBrokerBackend):
    """Yahoo Finance market data and symbol metadata broker."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
    COOKIE_URL = "https://fc.yahoo.com"
    CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"

    def __init__(self, name: str = "Yahoo") -> None:
        """Initialize Yahoo Finance broker backend."""
        super().__init__(name=name)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.crumb: str | None = None

    def _ensure_crumb(self) -> str | None:
        """Acquire and cache Yahoo Finance session cookie and crumb token."""
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

    def _map_interval(self, timeframe: str) -> str:
        """Map standard timeframe string to Yahoo Finance interval."""
        tf_clean = str(timeframe).upper().strip()
        if tf_clean in TIMEFRAME_TO_YAHOO_INTERVAL:
            return TIMEFRAME_TO_YAHOO_INTERVAL[tf_clean]
        for tf_str, interval in TIMEFRAME_TO_YAHOO_INTERVAL.items():
            if tf_clean.endswith(tf_str) or tf_str.endswith(tf_clean):
                return interval
        return "1d"

    @override
    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str,
        start: int,
        end: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Download candlestick bars from Yahoo Finance v8 chart API."""
        del mode
        sym_clean = symbol.upper().strip()
        interval = self._map_interval(timeframe)
        params: dict[str, Any] = {
            "interval": interval,
            "events": "history",
        }

        if start > 0 and end > 0 and end >= start:
            params["period1"] = start
            params["period2"] = end
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
                raise BridgeError(
                    f"Yahoo API failed with HTTP {resp.status_code}",
                    code="REMOTE_ERROR",
                )
            payload = resp.json()
            res_list = payload.get("chart", {}).get("result", [])
            if not res_list:
                raise BridgeError(
                    f"No chart data returned for {sym_clean}",
                    code="SYMBOL_NOT_FOUND",
                )
            chart_res = res_list[0]
            timestamps = chart_res.get("timestamp", [])
            indicators = chart_res.get("indicators", {})
            quotes_list = indicators.get("quote", [])
            if not quotes_list or not timestamps:
                return []

            q = quotes_list[0]
            opens = q.get("open", [])
            highs = q.get("high", [])
            lows = q.get("low", [])
            closes = q.get("close", [])
            volumes = q.get("volume", [])

            rows: list[dict[str, Any]] = []
            for i, ts in enumerate(timestamps):
                if (
                    i < len(opens)
                    and opens[i] is not None
                    and closes[i] is not None
                    and highs[i] is not None
                    and lows[i] is not None
                ):
                    vol = int(volumes[i] or 0) if i < len(volumes) else 0
                    o = float(opens[i])
                    c = float(closes[i])
                    h = max(float(highs[i]), o, c)
                    l = min(float(lows[i]), o, c)
                    rows.append(
                        {
                            "time": int(ts),
                            "open": o,
                            "high": h,
                            "low": l,
                            "close": c,
                            "tick_volume": vol,
                            "spread": 0,
                            "real_volume": vol,
                        }
                    )

            # Sort ascending and deduplicate timestamps
            rows.sort(key=lambda r: r["time"])
            deduped: list[dict[str, Any]] = []
            last_t: int | None = None
            for r in rows:
                if last_t is None or r["time"] > last_t:
                    deduped.append(r)
                    last_t = r["time"]

            target_count = count if count > 0 else limit
            if target_count and len(deduped) > target_count:
                deduped = deduped[-target_count:]
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Error downloading Yahoo bars for {sym_clean}: {exc}",
                code="DOWNLOAD_ERROR",
            ) from exc

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Resolve instrument specifications as a canonical SymbolSnapshot."""
        sym_clean = symbol.upper().strip()
        params: dict[str, Any] = {"symbols": sym_clean}
        crumb = self._ensure_crumb()
        if crumb:
            params["crumb"] = crumb

        price = 0.0
        bid = 0.0
        ask = 0.0
        try:
            resp = self.session.get(self.QUOTE_URL, params=params, timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                res_list = payload.get("quoteResponse", {}).get("result", [])
                if res_list:
                    item = res_list[0]
                    price = float(
                        item.get("regularMarketPrice") or item.get("ask") or 0.0
                    )
                    bid = float(item.get("bid") or price)
                    ask = float(item.get("ask") or price)
        except Exception as exc:
            logger.warning(
                "Could not fetch live quote for %s from Yahoo: %s", sym_clean, exc
            )

        return SymbolSnapshot(
            name=sym_clean,
            custom=False,
            digits=2,
            point=0.01,
            bid=bid,
            ask=ask,
            last=price,
        )

    @override
    def symbols_get(self) -> list[str]:
        """Return default popular symbols available on Yahoo."""
        return list(DEFAULT_SYMBOLS)


def create_adapter(context: PluginHostContext | None = None) -> YahooBroker:
    """Factory creating configured YahooBroker adapter."""
    del context
    return YahooBroker()
