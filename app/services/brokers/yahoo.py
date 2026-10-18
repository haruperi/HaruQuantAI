"""Yahoo Finance market data and symbol metadata broker implementation.

Description:
    Implements a zero-credential, web-based market data broker querying Yahoo Finance
    v8 chart and v7 quote REST endpoints. Conforms directly to the canonical
    `TradingBackend` protocol and Stage 2C `data.provider` specification. Provides
    normalized historical candlestick bars (`MarketData.Bars`) and symbol
    specifications (`SymbolInfo`). Enforces strict timeframe guards, rejecting
    tick data requests, and maps upstream HTTP 429/5xx status codes to typed provider errors.

Purpose:
    FEAT-BROKER-YAHOO: Public Market Data and Symbol Metadata Provider.

Key Capabilities:
    - FR-BROKER-YAHOO-MARKET-DATA: Historical Candlestick Bars Ingestion
      Associated: `[YahooBroker.fetch_bars()]`, `[YahooBroker.read_history()]`
      Logging: Emits INFO log upon parsing chart results, and WARNING log if
      symbol is not found, rate limit is exceeded, or payload is malformed.
    - FR-BROKER-YAHOO-SYMBOL-METADATA: Symbol Metadata and Quote Resolution
      Associated: `[YahooBroker.symbol_info()]`, `[YahooBroker.symbols_get()]`
      Logging: Emits INFO log upon quote resolution, and WARNING on request failure.
    - FR-BROKER-YAHOO-HEALTH: Remote Endpoint Health and Latency Inspection
      Associated: `[YahooBroker.check_health()]`
      Logging: Emits INFO on reachable probe and WARNING on network or rate limit failure.

Python API Usage:
    ```python
    from app.services.brokers.yahoo import YahooBroker
    from app.workspace.data_manager.history import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = YahooBroker()
    health = broker.check_health()
    bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    broker.close_sync()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.yahoo
    ```
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderError,
    ProviderHealth,
    ProviderRateLimitError,
    ProviderUnsupportedError,
)
from app.services.include.contracts import SymbolInfo
from app.workspace.data_manager import Timeframe
from app.workspace.data_manager.history import DataBrokerBackend

MARKET_DATA_FR = "FR-BROKER-YAHOO-MARKET-DATA"
SYMBOL_METADATA_FR = "FR-BROKER-YAHOO-SYMBOL-METADATA"
HEALTH_FR = "FR-BROKER-YAHOO-HEALTH"

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

PLUGIN_MANIFEST: dict[str, Any] = {
    "id": "yahoo",
    "name": "Yahoo Finance",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "yahoo:create_adapter",
    "description": "Yahoo Finance public market data and symbol metadata provider",
    "capabilities": ["data.fetch"],
}

__all__ = ["PLUGIN_MANIFEST", "YahooBroker", "create_adapter", "main"]

logger = get_logger(__name__)


class YahooBroker(DataBrokerBackend):
    """Yahoo Finance market data and symbol metadata broker."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
    COOKIE_URL = "https://fc.yahoo.com"
    CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"

    def __init__(
        self,
        name: str = "Yahoo",
        cache_dir: str | Path | None = None,
    ) -> None:
        """Initialize Yahoo Finance broker backend."""
        super().__init__(name=name)
        self.session = create_http_session(
            USER_AGENT, retries=2, backoff=0.5, pool_size=8
        )
        self.crumb: str | None = None
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._is_connected = True
        self.capabilities = ProviderCapabilities(
            provider_id="yahoo",
            display_name="Yahoo Finance",
            category="Equities",
            supported_timeframes=(
                "M1",
                "M2",
                "M5",
                "M15",
                "M30",
                "H1",
                "D1",
                "W1",
                "MN1",
            ),
            supported_modes=("bars",),
            requires_auth=False,
            rate_limit_rps=2.0,
            default_timeout_seconds=15.0,
            supports_pagination=False,
            has_local_archive=self.cache_dir is not None and self.cache_dir.exists(),
            description="Yahoo Finance public market data and symbol metadata provider",
        )

    def check_health(self) -> ProviderHealth:
        """Verify reachability and latency of Yahoo Finance quote endpoints."""
        t0 = time.monotonic()
        try:
            crumb = self._ensure_crumb()
            params: dict[str, Any] = {"symbols": "AAPL"}
            if crumb:
                params["crumb"] = crumb
            resp = self.session.get(
                self.QUOTE_URL,
                params=params,
                timeout=5.0,
            )
            latency = (time.monotonic() - t0) * 1000.0
            if resp.status_code == 200:
                logger.info(
                    "%s: Health check SUCCESS (latency=%.2fms)",
                    HEALTH_FR,
                    latency,
                    extra={"fr_id": HEALTH_FR, "latency_ms": latency},
                )
                return ProviderHealth(
                    provider_id="yahoo",
                    status="HEALTHY",
                    connected=True,
                    message="Yahoo Finance REST endpoints reachable",
                    latency_ms=latency,
                    capabilities=self.capabilities,
                )
            if resp.status_code == 429:
                logger.warning(
                    "%s: Health check RATE_LIMITED (latency=%.2fms)",
                    HEALTH_FR,
                    latency,
                    extra={"fr_id": HEALTH_FR, "status_code": 429},
                )
                return ProviderHealth(
                    provider_id="yahoo",
                    status="DEGRADED",
                    connected=False,
                    message="Yahoo Finance rate limit encountered (HTTP 429)",
                    latency_ms=latency,
                    capabilities=self.capabilities,
                )
            logger.warning(
                "%s: Health check UNEXPECTED_STATUS HTTP %d",
                HEALTH_FR,
                resp.status_code,
                extra={"fr_id": HEALTH_FR, "status_code": resp.status_code},
            )
            return ProviderHealth(
                provider_id="yahoo",
                status="DEGRADED",
                connected=False,
                message=f"Yahoo Finance returned HTTP {resp.status_code}",
                latency_ms=latency,
                capabilities=self.capabilities,
            )
        except Exception as exc:
            latency = (time.monotonic() - t0) * 1000.0
            logger.warning(
                "%s: Health check UNREACHABLE: %s",
                HEALTH_FR,
                exc,
                extra={"fr_id": HEALTH_FR, "error": str(exc)},
            )
            return ProviderHealth(
                provider_id="yahoo",
                status="UNHEALTHY",
                connected=False,
                message=f"Yahoo Finance unreachable: {exc}",
                latency_ms=latency,
                capabilities=self.capabilities,
            )

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
        if tf_clean in ("TICK", "TICKS"):
            raise ProviderUnsupportedError(
                "Yahoo Finance does not provide tick-level data",
                provider="yahoo",
            )
        if tf_clean in TIMEFRAME_TO_YAHOO_INTERVAL:
            return TIMEFRAME_TO_YAHOO_INTERVAL[tf_clean]
        for tf_str, interval in TIMEFRAME_TO_YAHOO_INTERVAL.items():
            if tf_clean.endswith(tf_str) or tf_str.endswith(tf_clean):
                return interval
        raise ProviderUnsupportedError(
            f"Unsupported timeframe '{timeframe}' for Yahoo Finance",
            provider="yahoo",
        )

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

        cache_file: Path | None = None
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"{sym_clean}_{interval}.json"

        try:
            url = self.CHART_URL.format(symbol=sym_clean)
            resp = execute_bounded_get(
                self.session, url, params=params, provider="yahoo"
            )
            if resp.status_code == 429:
                logger.warning(
                    "%s: Yahoo rate limit exceeded for %s",
                    MARKET_DATA_FR,
                    sym_clean,
                    extra={"fr_id": MARKET_DATA_FR, "symbol": sym_clean},
                )
                raise ProviderRateLimitError(
                    f"Yahoo Finance rate limit exceeded (HTTP 429) for {sym_clean}",
                    provider="yahoo",
                )
            if resp.status_code >= 500:
                logger.warning(
                    "%s: Yahoo upstream service error HTTP %d for %s",
                    MARKET_DATA_FR,
                    resp.status_code,
                    sym_clean,
                    extra={"fr_id": MARKET_DATA_FR, "status_code": resp.status_code},
                )
                raise ProviderError(
                    f"Yahoo upstream server error HTTP {resp.status_code}",
                    code="UPSTREAM_UNAVAILABLE",
                    status_code=503,
                    provider="yahoo",
                )
            if resp.status_code != 200:
                raise BridgeError(
                    f"Yahoo API failed with HTTP {resp.status_code}",
                    code="REMOTE_ERROR",
                )

            payload = resp.json()
            if cache_file is not None:
                cache_file.write_text(json.dumps(payload), encoding="utf-8")

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
                    h = float(highs[i])
                    l = float(lows[i])
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

            logger.info(
                "%s: Parsed %d bars for %s (%s)",
                MARKET_DATA_FR,
                len(deduped),
                sym_clean,
                interval,
                extra={
                    "fr_id": MARKET_DATA_FR,
                    "count": len(deduped),
                    "symbol": sym_clean,
                },
            )
            return deduped
        except Exception as exc:
            if isinstance(exc, (BridgeError, ProviderError)):
                raise
            raise BridgeError(
                f"Error downloading Yahoo bars for {sym_clean}: {exc}",
                code="DOWNLOAD_ERROR",
            ) from exc

    @override
    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str,
        start_ms: int,
        end_ms: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Reject tick data requests, as Yahoo Finance does not provide ticks."""
        del symbol, mode, start_ms, end_ms, count, limit
        logger.warning(
            "%s: Rejected tick download request on Yahoo Finance",
            MARKET_DATA_FR,
            extra={"fr_id": MARKET_DATA_FR},
        )
        raise ProviderUnsupportedError(
            "Yahoo Finance does not provide tick-level market data",
            provider="yahoo",
        )

    @override
    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Acquire historical bars conforming to typed request model."""
        if request.kind == "ticks" or request.timeframe.upper() == "TICK":
            raise ProviderUnsupportedError(
                "Yahoo Finance does not support tick history",
                provider="yahoo",
            )
        page = super().read_history(request, token)
        page.provenance = {"source": "yahoo_v8_chart", "url": self.CHART_URL}
        return page

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve instrument specifications as a canonical SymbolInfo."""
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
                "%s: Could not fetch live quote for %s from Yahoo: %s",
                SYMBOL_METADATA_FR,
                sym_clean,
                exc,
                extra={"fr_id": SYMBOL_METADATA_FR, "symbol": sym_clean},
            )

        logger.info(
            "%s: Resolved symbol info for %s (price=%.2f)",
            SYMBOL_METADATA_FR,
            sym_clean,
            price,
            extra={"fr_id": SYMBOL_METADATA_FR, "symbol": sym_clean, "price": price},
        )
        return SymbolInfo(
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
        logger.info(
            "%s: Returning default Yahoo symbol list (%d items)",
            SYMBOL_METADATA_FR,
            len(DEFAULT_SYMBOLS),
            extra={"fr_id": SYMBOL_METADATA_FR, "count": len(DEFAULT_SYMBOLS)},
        )
        return list(DEFAULT_SYMBOLS)


def create_adapter(context: PluginHostContext | None = None) -> YahooBroker:
    """Factory creating configured YahooBroker adapter."""
    del context
    return YahooBroker()


def main() -> None:
    """Demonstrate executable usage of YahooBroker."""
    broker = YahooBroker()
    health = broker.check_health()
    logger.info("Yahoo Health: %s (connected=%s)", health.status, health.connected)
    symbols = broker.symbols_get()
    logger.info("Supported symbols: %s...", symbols[:3])
    info = broker.symbol_info("AAPL")
    logger.info("AAPL info: digits=%s point=%s", info.digits, info.point)
    broker.close_sync()


if __name__ == "__main__":
    main()
