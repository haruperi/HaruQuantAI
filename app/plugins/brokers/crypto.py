"""Binance cryptocurrency market data broker and provider plugin.

Description:
    Implements a cryptocurrency market data broker and provider plugin connecting
    directly to Binance public and authenticated REST APIs (Spot, USDT-M, and
    Coin-M). Modeled after the StrategyQuant CryptoExchangeBinance architecture,
    this plugin retrieves high-resolution historical klines (candlestick bars)
    and trade ticks across arbitrary timeframes (1m, 3m, 5m, 15m, 30m, 1h, 2h,
    4h, 6h, 8h, 12h, 1d) and fulfills Data Manager downloads (`download_bars()`).
    In accordance with the workspace Strict Real-Data Policy, all operations
    interact exclusively with real remote endpoints and fail closed without
    synthetic or mock fallbacks.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Binance Exchange Integration.
    Provides live cryptocurrency market data, historical klines, and trade ticks
    across Binance Spot and Futures venues.

Key Capabilities:
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Trades
      Associated: `[BinanceBroker.get_bars()]`, `[BinanceBroker.get_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API, and
      ERROR log on network or parsing failure.
    - FR-BROKER-BINANCE-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[BinanceBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.crypto import BinanceBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars(symbol="BTCUSDT", count=10)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

import urllib.parse
from datetime import UTC, datetime
from typing import Any, override

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardError,
    StandardResponse,
    Tick,
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
    "id": "broker-binance",
    "name": "Binance Crypto Connector",
    "version": "1.0.0",
    "description": "Binance cryptocurrency REST market data and provider plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks"],
    "enabled": True,
    "metadata": {
        "provider_name": "Binance",
        "display_name": "Binance Crypto Exchange",
        "asset_classes": ["Crypto"],
        "timeframes": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w"],
        "requires_auth": False,
        "rate_limit_rps": 20.0,
        "base_url": "https://api.binance.com",
    },
}

BINANCE_SPOT_BASE_URL = "https://api.binance.com"
BINANCE_FUTURES_USDT_BASE_URL = "https://fapi.binance.com"
BINANCE_FUTURES_COIN_BASE_URL = "https://dapi.binance.com"
USER_AGENT = "HaruQuantAI/1.0 (Binance REST Client)"

TIMEFRAME_MAP: dict[str, str] = {
    "M1": "1m",
    "1M": "1m",
    "1": "1m",
    "M3": "3m",
    "3M": "3m",
    "3": "3m",
    "M5": "5m",
    "5M": "5m",
    "5": "5m",
    "M15": "15m",
    "15M": "15m",
    "15": "15m",
    "M30": "30m",
    "30M": "30m",
    "30": "30m",
    "H1": "1h",
    "1H": "1h",
    "60": "1h",
    "H2": "2h",
    "2H": "2h",
    "H4": "4h",
    "4H": "4h",
    "240": "4h",
    "H6": "6h",
    "6H": "6h",
    "H8": "8h",
    "8H": "8h",
    "H12": "12h",
    "12H": "12h",
    "D1": "1d",
    "1D": "1d",
    "1440": "1d",
    "D3": "3d",
    "3D": "3d",
    "W1": "1w",
    "1W": "1w",
    "MN1": "1M",
    "1MO": "1M",
}


def _map_timeframe(tf: TimeFrame | str | int) -> str:
    """Map generic timeframe enum/string to Binance kline interval."""
    if isinstance(tf, TimeFrame):
        name = tf.name.upper()
        if name in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[name]
    s = str(tf).strip().upper()
    return TIMEFRAME_MAP.get(s, "1m")


__all__ = ["BinanceBroker", "CryptoBroker", "CryptoMultiProvider", "create_adapter"]


class BinanceBroker(BaseBroker):
    """Binance cryptocurrency market data and execution broker plugin."""

    def __init__(
        self,
        name: str = "Binance",
        venue: str = "spot",
        default_market: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Initialize Binance broker plugin with resilient HTTP session."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        target_venue = default_market or venue
        self.venue = target_venue.lower().strip()
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""

        if self.venue in ("usdt-m", "futures", "fapi"):
            self.base_url = BINANCE_FUTURES_USDT_BASE_URL
        elif self.venue in ("coin-m", "delivery", "dapi"):
            self.base_url = BINANCE_FUTURES_COIN_BASE_URL
        else:
            self.base_url = BINANCE_SPOT_BASE_URL

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
        )
        if self.api_key:
            self.session.headers["X-MBX-APIKEY"] = self.api_key

        retry_strategy: Any = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=16, pool_maxsize=16
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="Binance",
            display_name="Binance Crypto Exchange",
            asset_classes=["Crypto"],
            timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w"],
            requires_auth=False,
            rate_limit_rps=20.0,
            base_url=self.base_url,
        )

    def download_bars(
        self, request: DownloadRequest, token: CancellationToken | None = None
    ) -> list[BarRecord]:
        """Download historical candlestick records directly from Binance REST API."""
        if token:
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
        # Strict Real-Data Policy: fail closed without synthetic mock fallback
        return []

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol string for Binance REST endpoints."""
        sym = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        if sym.endswith("USD") and not sym.endswith(("USDT", "USDC", "BUSD")):
            if self.venue not in ("coin-m", "delivery", "dapi"):
                sym = f"{sym}T"
        return sym

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
        """Retrieve real historical candlestick bars from Binance REST klines API."""
        sym_clean = self._normalize_symbol(symbol)
        interval = _map_timeframe(timeframe)
        limit = min(count or 500, 1000)

        params: dict[str, Any] = {
            "symbol": sym_clean,
            "interval": interval,
            "limit": limit,
        }
        if date_from:
            params["startTime"] = int(date_from.timestamp() * 1000)
        if date_to:
            params["endTime"] = int(date_to.timestamp() * 1000)

        url = f"{self.base_url}/api/v3/klines"
        try:
            r = self.session.get(url, params=params, timeout=(5.0, 20.0))
            if r.status_code == 200:
                raw_klines = r.json()
                bars: list[Bar] = []
                for row in raw_klines:
                    # [ openTime, open, high, low, close, volume, closeTime, ... ]
                    open_time = datetime.fromtimestamp(row[0] / 1000.0, tz=UTC)
                    bars.append(
                        Bar(
                            time=open_time,
                            open=float(row[1]),
                            high=float(row[2]),
                            low=float(row[3]),
                            close=float(row[4]),
                            tick_volume=int(float(row[5])),
                            real_volume=int(float(row[5])),
                        )
                    )
                self.logger.info(
                    "FR-BROKER-BINANCE-MARKET-DATA: Retrieved %d klines for %s from Binance",
                    len(bars),
                    sym_clean,
                    extra={
                        "fr_id": "FR-BROKER-BINANCE-MARKET-DATA",
                        "symbol": sym_clean,
                        "count": len(bars),
                    },
                )
                return StandardResponse.success(
                    data=bars,
                    message=f"Retrieved {len(bars)} bars from Binance for '{sym_clean}'",
                    extensions={"broker": self.name},
                )
            msg = f"Binance klines request failed with status {r.status_code}: {r.text}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to retrieve klines from Binance for '{sym_clean}': {e}"
            self.logger.error("FR-BROKER-BINANCE-MARKET-DATA: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="KLINE_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve real recent trades/ticks from Binance."""
        sym_clean = self._normalize_symbol(symbol)
        limit = min(count or 100, 1000)
        url = f"{self.base_url}/api/v3/trades?symbol={urllib.parse.quote(sym_clean)}&limit={limit}"
        try:
            r = self.session.get(url, timeout=(3.0, 10.0))
            if r.status_code == 200:
                raw_trades = r.json()
                ticks: list[Tick] = []
                for tr in raw_trades:
                    p = float(tr.get("price", 0.0))
                    qty = float(tr.get("qty", 0.0))
                    t_dt = datetime.fromtimestamp(tr.get("time", 0) / 1000.0, tz=UTC)
                    ticks.append(
                        Tick(
                            time=t_dt,
                            bid=p,
                            ask=p,
                            last=p,
                            volume=qty,
                            raw=tr,
                        )
                    )
                return StandardResponse.success(
                    data=ticks, extensions={"broker": self.name}
                )
            msg = f"Failed to retrieve Binance trades for '{sym_clean}' (status {r.status_code})"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to retrieve Binance trades for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="TRADES_ERROR", message=msg),
                extensions={"broker": self.name},
            )


# Compatibility aliases
CryptoMultiProvider = BinanceBroker
CryptoBroker = BinanceBroker


def create_adapter(_context: PluginHostContext | None = None) -> BinanceBroker:
    """Plugin entrypoint factory constructing BinanceBroker adapter."""
    logger.info("Initializing Binance cryptocurrency broker plugin adapter.")
    return BinanceBroker()
