"""Binance cryptocurrency market data broker and provider plugin.

Description:
    Implements a cryptocurrency market data and execution broker plugin connecting
    directly to Binance public and authenticated REST APIs (Spot, USDT-M, and
    Coin-M). Modeled after the StrategyQuant CryptoExchangeBinance architecture,
    this plugin retrieves real-time order books, live ticker quotes, comprehensive
    exchange metadata, and high-resolution historical klines (candlestick bars)
    across arbitrary timeframes (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d).
    In accordance with the workspace Strict Real-Data Policy, all operations
    interact exclusively with real remote endpoints and fail closed without
    synthetic or mock fallbacks.

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Binance Exchange Integration.
    Provides live cryptocurrency market data, instrument metadata, historical
    klines, and trading contracts across Binance Spot and Futures venues.

Key Capabilities:
    - FR-BROKER-BINANCE-CONNECTIVITY: Live Gateway Connectivity and Server Ping
      Associated: `[BinanceBroker.connect()]`, `[BinanceBroker.is_connected()]`
      Logging: Emits INFO log upon pinging Binance API endpoints.
    - FR-BROKER-BINANCE-EXCHANGE-INFO: Exchange Symbol Catalog and Precision Models
      Associated: `[BinanceBroker.get_symbol_info()]`,
      `[BinanceBroker.get_symbols()]`
      Logging: Emits DEBUG log when caching and returning symbol filter rules.
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Ticker Quotes
      Associated: `[BinanceBroker.get_bars()]`,
      `[BinanceBroker.get_symbol_tick()]`, `[BinanceBroker.get_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API.
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform Typed Provider Compatibility
      Associated: `[BinanceBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO log on download dispatch.

Python API Usage:
    ```python
    from app.plugins.brokers.crypto.adapter import BinanceBroker

    broker = BinanceBroker()
    resp = broker.connect()
    assert resp.is_success

    # Retrieve live BTCUSDT klines
    bars_resp = broker.get_bars(symbol="BTCUSDT", count=10)
    if bars_resp.is_success and bars_resp.data:
        print(f"Latest BTCUSDT close: {bars_resp.data[-1].close}")
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
    SymbolInfo,
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
            capabilities=(
                BrokerCapability.CONNECT
                | BrokerCapability.MARKET_DATA
                | BrokerCapability.SYMBOLS
                | BrokerCapability.MARKET_DEPTH
            ),
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

        retry_strategy = Retry(
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

        self._connected = False
        self._symbols_cache: dict[str, SymbolInfo] = {}

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

    @override
    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Verify active network connectivity to Binance REST API."""
        self.logger.info(
            "FR-BROKER-BINANCE-CONNECTIVITY: Connecting to Binance REST endpoint (%s)...",
            self.base_url,
            extra={
                "fr_id": "FR-BROKER-BINANCE-CONNECTIVITY",
                "base_url": self.base_url,
            },
        )
        try:
            url = f"{self.base_url}/api/v3/ping"
            r = self.session.get(url, timeout=(3.0, 5.0))
            self._connected = r.status_code == 200
            if self._connected:
                return StandardResponse.success(
                    data=True,
                    message=f"Connected to Binance {self.venue.title()} API",
                    extensions={"broker": self.name, "venue": self.venue},
                )
            msg = f"Binance ping returned HTTP {r.status_code}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            self._connected = False
            msg = f"Failed to connect to Binance API: {e}"
            self.logger.error("FR-BROKER-BINANCE-CONNECTIVITY: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="CONNECTION_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def is_connected(self) -> StandardResponse[bool]:
        """Check active connection state."""
        return StandardResponse.success(
            data=self._connected,
            message="Connected" if self._connected else "Disconnected",
            extensions={"broker": self.name},
        )

    @override
    def disconnect(self) -> StandardResponse[bool]:
        """Disconnect session."""
        self._connected = False
        return StandardResponse.success(
            data=True, message="Disconnected", extensions={"broker": self.name}
        )

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol string for Binance REST endpoints."""
        sym = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        if sym.endswith("USD") and not sym.endswith(("USDT", "USDC", "BUSD")):
            if self.venue not in ("coin-m", "delivery", "dapi"):
                sym = f"{sym}T"
        return sym

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications from Binance exchangeInfo."""
        sym_clean = self._normalize_symbol(symbol)
        if sym_clean in self._symbols_cache:
            return StandardResponse.success(
                data=self._symbols_cache[sym_clean],
                extensions={"broker": self.name, "source": "cache"},
            )

        url = f"{self.base_url}/api/v3/exchangeInfo?symbol={urllib.parse.quote(sym_clean)}"
        try:
            r = self.session.get(url, timeout=(3.0, 10.0))
            if r.status_code == 200:
                data = r.json()
                symbols_list = data.get("symbols", [])
                if symbols_list:
                    item = symbols_list[0]
                    # Parse precision filters
                    digits = 8
                    tick_size = 0.00000001
                    step_size = 0.00000001
                    for f in item.get("filters", []):
                        if f.get("filterType") == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize", 0.00000001))
                            tick_str = f"{tick_size:.10f}".rstrip("0")
                            digits = (
                                len(tick_str.split(".")[1]) if "." in tick_str else 0
                            )
                        elif f.get("filterType") == "LOT_SIZE":
                            step_size = float(f.get("stepSize", 0.00000001))

                    info = SymbolInfo(
                        name=sym_clean,
                        visible=True,
                        select=True,
                        point=tick_size,
                        digits=digits,
                        trade_contract_size=1.0,
                        currency_base=item.get("baseAsset", "BTC"),
                        currency_profit=item.get("quoteAsset", "USDT"),
                        currency_margin=item.get("quoteAsset", "USDT"),
                        description=f"Binance {item.get('baseAsset')}/{item.get('quoteAsset')}",
                        exchange="Binance",
                        raw=item,
                    )
                    self._symbols_cache[sym_clean] = info
                    self.logger.debug(
                        "FR-BROKER-BINANCE-EXCHANGE-INFO: Loaded symbol info for %s",
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-BINANCE-EXCHANGE-INFO",
                            "symbol": sym_clean,
                        },
                    )
                    return StandardResponse.success(
                        data=info,
                        extensions={"broker": self.name, "source": "api"},
                    )
            msg = f"Symbol '{sym_clean}' not found on Binance (status {r.status_code})"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to retrieve symbol info from Binance for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="QUERY_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of active symbols from Binance exchangeInfo."""
        url = f"{self.base_url}/api/v3/exchangeInfo"
        try:
            r = self.session.get(url, timeout=(5.0, 15.0))
            if r.status_code == 200:
                data = r.json()
                symbols: list[SymbolInfo] = []
                for item in data.get("symbols", []):
                    if item.get("status") == "TRADING":
                        sym_name = item.get("symbol", "")
                        if not group or group.upper() in sym_name:
                            tick_size = 0.00000001
                            digits = 8
                            for f in item.get("filters", []):
                                if f.get("filterType") == "PRICE_FILTER":
                                    tick_size = float(f.get("tickSize", 0.00000001))
                                    tick_str = f"{tick_size:.10f}".rstrip("0")
                                    digits = (
                                        len(tick_str.split(".")[1])
                                        if "." in tick_str
                                        else 0
                                    )
                            info = SymbolInfo(
                                name=sym_name,
                                visible=True,
                                select=True,
                                point=tick_size,
                                digits=digits,
                                trade_contract_size=1.0,
                                currency_base=item.get("baseAsset", ""),
                                currency_profit=item.get("quoteAsset", ""),
                                currency_margin=item.get("quoteAsset", ""),
                                description=f"Binance {item.get('baseAsset')}/{item.get('quoteAsset')}",
                                exchange="Binance",
                                raw=item,
                            )
                            symbols.append(info)
                            self._symbols_cache[sym_name] = info
                return StandardResponse.success(
                    data=symbols, extensions={"broker": self.name}
                )
            msg = f"Failed to list Binance symbols (status {r.status_code})"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to list Binance symbols: {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="QUERY_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Retrieve real live book ticker quote for symbol from Binance."""
        sym_clean = self._normalize_symbol(symbol)
        url = f"{self.base_url}/api/v3/ticker/bookTicker?symbol={urllib.parse.quote(sym_clean)}"
        try:
            r = self.session.get(url, timeout=(2.0, 5.0))
            if r.status_code == 200:
                data = r.json()
                bid = float(data.get("bidPrice", 0.0))
                ask = float(data.get("askPrice", 0.0))
                tick = Tick(
                    time=datetime.now(UTC),
                    bid=bid,
                    ask=ask,
                    last=bid,
                    volume=float(data.get("bidQty", 0.0)),
                    raw=data,
                )
                return StandardResponse.success(
                    data=tick, extensions={"broker": self.name}
                )
            msg = f"Failed to retrieve Binance tick for '{sym_clean}' (status {r.status_code})"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="NO_DATA", message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to retrieve Binance tick for '{sym_clean}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="FETCH_ERROR", message=msg),
                extensions={"broker": self.name},
            )

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
