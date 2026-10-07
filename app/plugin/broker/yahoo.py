"""Yahoo Finance market data broker plugin implementation.

Description:
    Implements a zero-credential, web-based market data broker plugin querying
    Yahoo Finance v8 chart and search REST endpoints.
    Within the HaruQuantAI platform, Yahoo Finance serves as an unauthenticated,
    broad-coverage public data feed for global equities, indices, and currency
    pairs. It provides quote summaries, ticker search autocomplete, latest quotes,
    and historical OHLCV candlestick trendbars.
    Because Yahoo Finance does not provide execution gateways, trading and order
    management capabilities are explicitly rejected with canonical capability
    unsupported errors (`BaseBroker._unsupported()`).
    Internally, the class manages a persistent `requests.Session` with a browser
    User-Agent header, normalizes intervals between `TimeFrame` enums and Yahoo query
    parameters (`1m`, `5m`, `60m`, `1d`, `1wk`, `1mo`), and parses JSON responses
    into strongly typed `SymbolInfo`, `Tick`, and `Bar` models.

Purpose:
    FEAT-BROKER-YAHOO: Public Market Data and Historical Bar Provider.
    Implements HTTP-based market quote queries, symbol lookup, and historical bar
    extraction from public Yahoo Finance endpoints without authentication.

Key Capabilities:
    - FR-BROKER-YAHOO-CONNECTIVITY: Connection Probe & HTTP Session Lifecycle
      Associated: `[YahooBroker.connect()]`, `[YahooBroker.disconnect()]`,
      `[YahooBroker.is_connected()]`
      Logging: Emits INFO log upon successful connectivity check and WARNING
      log on HTTP error status or network timeout.
    - FR-BROKER-YAHOO-MARKET-DATA: Real-Time Quotes & Historical Candlestick Bars
      Associated: `[YahooBroker.get_symbol_info()]`,
      `[YahooBroker.get_symbol_tick()]`, `[YahooBroker.get_bars()]`
      Logging: Emits INFO log with bar counts upon parsing chart results,
      and WARNING log if symbol is not found or payload is malformed.
    - FR-BROKER-YAHOO-SYMBOL-SEARCH: Symbol Lookup and Autocomplete
      Associated: `[YahooBroker.get_symbols()]`
      Logging: Emits INFO log with search query match counts.
    - FR-BROKER-YAHOO-TRADE-REJECTION: Unsupported Trade Capability Rejection
      Associated: `[YahooBroker.trade()]`, `[YahooBroker.check_order()]`
      Logging: Emits WARNING log declaring trading capabilities unsupported.

Python API Usage:
    ```python
    from app.plugin.broker import TimeFrame, yahoo

    # Connect and verify public endpoint access
    conn_resp = yahoo.connect()
    assert conn_resp.is_success

    # Retrieve 5 daily bars for Apple
    bars_resp = yahoo.get_bars("AAPL", timeframe=TimeFrame.D1, count=5)
    if bars_resp.is_success:
        for bar in bars_resp.data:
            print(bar.time, bar.close)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/plugin/broker/test_yahoo.py -v --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from app.host.logging import get_logger

from .contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardError,
    StandardResponse,
    SymbolInfo,
    Tick,
    TimeFrame,
)

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

TIMEFRAME_TO_YAHOO_INTERVAL = {
    TimeFrame.M1: "1m",
    TimeFrame.M2: "2m",
    TimeFrame.M5: "5m",
    TimeFrame.M15: "15m",
    TimeFrame.M30: "30m",
    TimeFrame.H1: "60m",
    TimeFrame.H4: "60m",  # Fetched as 60m
    TimeFrame.D1: "1d",
    TimeFrame.W1: "1wk",
    TimeFrame.MN1: "1mo",
}


class YahooBroker(BaseBroker):
    """Yahoo Finance market data broker plugin."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

    def __init__(self, name: str = "Yahoo") -> None:
        """Initialize Yahoo Finance broker plugin."""
        super().__init__(
            name=name,
            capabilities=(
                BrokerCapability.CONNECT
                | BrokerCapability.MARKET_DATA
                | BrokerCapability.SYMBOLS
            ),
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._connected = True

    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Validate live connectivity to Yahoo Finance chart API."""
        self.logger.info("Connecting to Yahoo Finance...")
        try:
            r = self.session.get(
                self.CHART_URL.format(symbol="SPY"),
                params={"range": "1d", "interval": "1d"},
                timeout=10,
            )
            if r.status_code == 200:
                self._connected = True
                return StandardResponse.success(
                    data=True,
                    message="Connected to Yahoo Finance",
                    extensions={"broker": self.name},
                )
            msg = f"Yahoo Finance returned status {r.status_code}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            self._connected = False
            msg = f"Failed to connect to Yahoo Finance: {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="CONNECTION_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    def is_connected(self) -> StandardResponse[bool]:
        """Check whether the Yahoo connection is operational."""
        return StandardResponse.success(
            data=self._connected,
            message="Connected" if self._connected else "Disconnected",
            extensions={"broker": self.name},
        )

    def disconnect(self) -> StandardResponse[bool]:
        """Terminate the active session."""
        self._connected = False
        return StandardResponse.success(
            data=True, message="Disconnected", extensions={"broker": self.name}
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

    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument quote summary and price specifications."""
        sym_clean = symbol.upper().strip()
        url = self.CHART_URL.format(symbol=sym_clean)
        try:
            resp = self.session.get(
                url, params={"range": "1d", "interval": "1d"}, timeout=10
            )
            if resp.status_code != 200:
                msg = (
                    f"Symbol '{sym_clean}' not found on Yahoo: HTTP {resp.status_code}"
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(resp.status_code), message=msg),
                    extensions={"broker": self.name},
                )
            payload = resp.json()
            res_list = payload.get("chart", {}).get("result", [])
            if not res_list:
                msg = f"No data returned for '{sym_clean}'"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NOT_FOUND", message=msg),
                    extensions={"broker": self.name},
                )
            meta = res_list[0].get("meta", {})
            price = float(meta.get("regularMarketPrice", 0.0) or 0.0)
            currency = str(meta.get("currency", "USD"))
            info = SymbolInfo(
                name=sym_clean,
                visible=True,
                select=True,
                bid=price,
                ask=price,
                digits=int(meta.get("priceHint", 2)),
                currency_base=currency,
                currency_profit=currency,
                currency_margin=currency,
                raw=meta,
            )
            return StandardResponse.success(
                data=info, extensions={"broker": self.name, "raw": meta}
            )
        except Exception as e:
            msg = f"Error fetching symbol info for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Search or list symbols matching query string."""
        query = group or "AAPL"
        try:
            resp = self.session.get(
                self.SEARCH_URL, params={"q": query, "quotesCount": 10}, timeout=10
            )
            if resp.status_code != 200:
                msg = f"Search failed: HTTP {resp.status_code}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(resp.status_code), message=msg),
                    extensions={"broker": self.name},
                )
            data = resp.json()
            quotes = data.get("quotes", [])
            symbols: list[SymbolInfo] = []
            for q in quotes:
                sym = q.get("symbol")
                if sym:
                    symbols.append(
                        SymbolInfo(
                            name=sym,
                            visible=True,
                            select=True,
                            currency_base=q.get("currency", "USD"),
                            raw=q,
                        )
                    )
            return StandardResponse.success(
                data=symbols, extensions={"broker": self.name, "raw": quotes}
            )
        except Exception as e:
            msg = f"Failed to search symbols on Yahoo: {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Get latest price tick for a symbol from Yahoo."""
        sym_clean = symbol.upper().strip()
        try:
            url = self.CHART_URL.format(symbol=sym_clean)
            resp = self.session.get(
                url, params={"range": "1d", "interval": "1m"}, timeout=10
            )
            if resp.status_code != 200:
                msg = f"Failed to fetch tick for '{sym_clean}': HTTP {resp.status_code}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(resp.status_code), message=msg),
                    extensions={"broker": self.name},
                )
            payload = resp.json()
            res_list = payload.get("chart", {}).get("result", [])
            if not res_list:
                msg = f"No quote returned for '{sym_clean}'"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )
            meta = res_list[0].get("meta", {})
            price = float(meta.get("regularMarketPrice", 0.0) or 0.0)
            now = datetime.now(UTC)
            t = Tick(time=now, bid=price, ask=price, last=price, raw=meta)
            return StandardResponse.success(
                data=t, extensions={"broker": self.name, "raw": meta}
            )
        except Exception as e:
            msg = f"Error getting tick for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )

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
        params: dict[str, Any] = {"interval": interval}

        if date_from and date_to:
            params["period1"] = int(date_from.timestamp())
            params["period2"] = int(date_to.timestamp())
        # Choose range based on interval
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
                # Filter out null / None entries (e.g. market holidays)
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
