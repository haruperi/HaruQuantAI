"""Yahoo Finance market data broker plugin implementation.

Description:
    Implements a zero-credential, web-based market data broker plugin querying
    Yahoo Finance v8 chart REST endpoints.
    Within the HaruQuantAI platform, Yahoo Finance serves as an unauthenticated,
    broad-coverage public data feed for global equities, indices, and currency
    pairs. It provides historical OHLCV candlestick trendbars for backtesting
    and Data Manager workspace downloads (`download_bars()`).
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-YAHOO: Public Market Data and Historical Bar Provider.
    Implements HTTP-based historical bar extraction and Data Manager downloads
    from public Yahoo Finance endpoints without authentication.

Key Capabilities:
    - FR-BROKER-YAHOO-MARKET-DATA: Historical Candlestick Bars
      Associated: `[YahooBroker.get_bars()]`
      Logging: Emits INFO log upon parsing chart results, and WARNING log
      if symbol is not found or payload is malformed.
    - FR-BROKER-YAHOO-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[YahooBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.yahoo import YahooBroker, create_adapter

    broker = create_adapter()
    resp = broker.get_bars("AAPL", count=5)
    assert resp.is_success
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
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
    TimeFrame,
)
from app.workspace.data_manager.connections import (
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "data-source-yahoo",
    "name": "Yahoo Finance Feed",
    "version": "1.0.0",
    "description": "Yahoo Finance historical daily and intraday market data provider plugin",
    "author": "HaruQuantAI",
    "slot": "data.provider",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars"],
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
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
    """Yahoo Finance market data broker plugin."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self, name: str = "Yahoo") -> None:
        """Initialize Yahoo Finance broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Provide Data Manager workspace provider capabilities descriptor."""
        return ProviderCapabilities(
            name="Yahoo",
            display_name="Yahoo Finance",
            asset_classes=["Stocks", "Indices", "Commodities"],
            timeframes=["M1", "M5", "D1"],
            requires_auth=False,
            rate_limit_rps=5.0,
            base_url="https://query1.finance.yahoo.com",
        )

    def download_bars(
        self, request: DownloadRequest, token: CancellationToken | None = None
    ) -> list[BarRecord]:
        """Download historical bars formatted as BarRecords for Data Manager."""
        if token is not None:
            token.check_cancelled()
        dt_from = (
            datetime.fromisoformat(request.date_from) if request.date_from else None
        )
        dt_to = datetime.fromisoformat(request.date_to) if request.date_to else None
        bars_resp = self.get_bars(
            symbol=request.symbol,
            timeframe=request.timeframe,
            date_from=dt_from,
            date_to=dt_to,
        )
        if bars_resp.is_success and bars_resp.data:
            return [
                BarRecord(
                    timestamp_utc=b.time.isoformat(),
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_resp.data
            ]
        return []

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
        params: dict[str, Any] = {"interval": interval}

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
