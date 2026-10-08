"""Binance cryptocurrency market data and symbol metadata broker plugin.

Description:
    Implements a cryptocurrency market data and symbol catalog broker plugin connecting
    directly to Binance public and authenticated REST APIs (Spot, USDT-M, and
    Coin-M). Modeled after the StrategyQuant CryptoExchangeBinance architecture,
    this plugin retrieves real-time instrument specifications via `exchangeInfo`
    (`get_symbol_info()`, `get_symbols()`, `get_num_of_symbols()`), high-resolution
    historical klines (candlestick bars), and trade ticks across arbitrary timeframes
    (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d).
    In accordance with the workspace Strict Real-Data Policy, all operations
    interact exclusively with real remote endpoints and fail closed without
    synthetic or mock fallbacks.
    All non-market-data and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Binance Exchange Integration.
    Provides live cryptocurrency market data, dynamic symbol resolution, historical
    klines, and trade ticks across Binance Spot and Futures venues.

Key Capabilities:
    - FR-BROKER-BINANCE-SYMBOLS: Binance ExchangeInfo Symbol Resolution
      Associated: `[BinanceBroker.get_symbol_info()]`, `[BinanceBroker.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found or request fails.
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Trades
      Associated: `[BinanceBroker.get_bars()]`, `[BinanceBroker.get_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API, and
      ERROR log on network or parsing failure.

Python API Usage:
    ```python
    from app.plugins.brokers.crypto import BinanceBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("BTCUSDT")
    if info_resp.is_success and info_resp.data:
        print(info_resp.data.description, info_resp.data.digits)

    bars_resp = broker.get_bars(symbol="BTCUSDT", count=10)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.brokers.crypto
    ```
"""

from __future__ import annotations

import sys
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

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "broker-binance",
    "name": "Binance Crypto Connector",
    "version": "1.0.0",
    "description": "Binance cryptocurrency REST market data and symbol catalog broker plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks", "symbols"],
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


def _calc_digits(tick_size: float) -> int:
    """Calculate quotation digits precision from tick size."""
    if tick_size >= 1.0 or tick_size <= 0:
        return 0
    s = f"{tick_size:.8f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


__all__ = ["BinanceBroker", "create_adapter"]


class BinanceBroker(BaseBroker):
    """Binance cryptocurrency market data and symbol catalog broker plugin."""

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
            capabilities=(BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS),
        )
        target_venue = default_market or venue
        self.venue = target_venue.lower().strip()
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""

        if self.venue in ("usdt-m", "futures", "fapi"):
            self.base_url = BINANCE_FUTURES_USDT_BASE_URL
            self.api_prefix = "/fapi/v1"
        elif self.venue in ("coin-m", "delivery", "dapi"):
            self.base_url = BINANCE_FUTURES_COIN_BASE_URL
            self.api_prefix = "/dapi/v1"
        else:
            self.base_url = BINANCE_SPOT_BASE_URL
            self.api_prefix = "/api/v3"

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

        self._symbols_cache: dict[str, SymbolInfo] = {}
        self._catalog_ordered: list[SymbolInfo] = []
        self._exchange_info_loaded: bool = False

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol string for Binance REST endpoints."""
        sym = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        if sym.endswith("USD") and not sym.endswith(("USDT", "USDC", "BUSD")):
            if self.venue not in ("coin-m", "delivery", "dapi"):
                sym = f"{sym}T"
        return sym

    def _parse_symbol_info(self, sym_data: dict[str, Any]) -> SymbolInfo:
        """Parse raw Binance exchangeInfo symbol dictionary into canonical SymbolInfo."""
        sym = sym_data.get("symbol", "")
        base_asset = sym_data.get("baseAsset", "")
        quote_asset = sym_data.get("quoteAsset", "")

        tick_size = 0.01
        step_size = 1.0

        for f in sym_data.get("filters", []):
            ft = f.get("filterType")
            if ft == "PRICE_FILTER":
                tick_size = float(f.get("tickSize") or 0.01)
            elif ft == "LOT_SIZE":
                step_size = float(f.get("stepSize") or 1.0)

        dec = _calc_digits(tick_size)

        return SymbolInfo(
            name=sym,
            custom=False,
            digits=dec,
            point=tick_size,
            currency_base=base_asset,
            currency_profit=quote_asset,
            description=f"{sym} ({base_asset}/{quote_asset})",
            category="Crypto",
            path=f"Crypto/Binance/{self.venue.upper()}",
            trade_contract_size=step_size,
            trade_tick_size=tick_size,
            trade_tick_value=tick_size,
            raw=sym_data,
        )

    def _ensure_exchange_info(self) -> None:
        """Fetch and cache full Binance exchangeInfo catalog."""
        if self._exchange_info_loaded:
            return

        url = f"{self.base_url}{self.api_prefix}/exchangeInfo"
        try:
            r = self.session.get(url, timeout=(5.0, 15.0))
            if r.status_code == 200:
                data = r.json()
                symbols_list = data.get("symbols", [])
                ordered: list[SymbolInfo] = []
                cache: dict[str, SymbolInfo] = {}

                for s_data in symbols_list:
                    # Only index trading symbols or all symbols
                    info = self._parse_symbol_info(s_data)
                    cache[info.name] = info
                    ordered.append(info)

                self._symbols_cache.update(cache)
                self._catalog_ordered = ordered
                self._exchange_info_loaded = True
                self.logger.info(
                    "FR-BROKER-BINANCE-SYMBOLS: Loaded %d instruments from Binance exchangeInfo (%s)",
                    len(ordered),
                    self.venue,
                    extra={
                        "fr_id": "FR-BROKER-BINANCE-SYMBOLS",
                        "count": len(ordered),
                        "venue": self.venue,
                    },
                )
            else:
                self.logger.warning(
                    "FR-BROKER-BINANCE-SYMBOLS: exchangeInfo request failed with status %d: %s",
                    r.status_code,
                    r.text[:200],
                )
        except Exception as exc:
            self.logger.warning(
                "FR-BROKER-BINANCE-SYMBOLS: Error fetching exchangeInfo: %s", exc
            )

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for a Binance symbol."""
        sym_clean = self._normalize_symbol(symbol)

        # Check in-memory cache first
        if sym_clean in self._symbols_cache:
            info = self._symbols_cache[sym_clean]
            self.logger.info(
                "FR-BROKER-BINANCE-SYMBOLS: Resolved symbol info for %s from cache",
                sym_clean,
                extra={"fr_id": "FR-BROKER-BINANCE-SYMBOLS", "symbol": sym_clean},
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{symbol}'",
                extensions={"broker": self.name},
            )

        # Query single symbol exchangeInfo endpoint directly
        url = f"{self.base_url}{self.api_prefix}/exchangeInfo"
        try:
            r = self.session.get(url, params={"symbol": sym_clean}, timeout=(5.0, 10.0))
            if r.status_code == 200:
                data = r.json()
                symbols_list = data.get("symbols", [])
                if symbols_list:
                    info = self._parse_symbol_info(symbols_list[0])
                    self._symbols_cache[sym_clean] = info
                    self.logger.info(
                        "FR-BROKER-BINANCE-SYMBOLS: Resolved symbol info for %s from exchangeInfo",
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-BINANCE-SYMBOLS",
                            "symbol": sym_clean,
                        },
                    )
                    return StandardResponse.success(
                        data=info,
                        message=f"Symbol info retrieved for '{symbol}'",
                        extensions={"broker": self.name},
                    )

            msg = f"Symbol '{symbol}' not found on Binance {self.venue}"
            self.logger.warning(
                "FR-BROKER-BINANCE-SYMBOLS: %s (status %d)", msg, r.status_code
            )
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )
        except Exception as exc:
            msg = f"Failed to fetch symbol info for '{symbol}' from Binance: {exc}"
            self.logger.error("FR-BROKER-BINANCE-SYMBOLS: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="REQUEST_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve available symbols from Binance exchangeInfo, optionally filtered by quote asset/group."""
        self._ensure_exchange_info()
        symbols = self._catalog_ordered

        if group:
            g_upper = group.strip().upper()
            symbols = [
                s
                for s in symbols
                if (s.currency_profit and s.currency_profit.upper() == g_upper)
                or (s.category and g_upper in s.category.upper())
                or (s.path and g_upper in s.path.upper())
            ]
            self.logger.info(
                "FR-BROKER-BINANCE-SYMBOLS: Filtered Binance symbols by group '%s', count=%d",
                group,
                len(symbols),
                extra={
                    "fr_id": "FR-BROKER-BINANCE-SYMBOLS",
                    "group": group,
                    "count": len(symbols),
                },
            )
            return StandardResponse.success(
                data=symbols,
                message=f"Retrieved {len(symbols)} symbols matching group '{group}'",
                extensions={"broker": self.name},
            )

        self.logger.info(
            "FR-BROKER-BINANCE-SYMBOLS: Retrieved all %d symbols from Binance",
            len(symbols),
            extra={"fr_id": "FR-BROKER-BINANCE-SYMBOLS", "count": len(symbols)},
        )
        return StandardResponse.success(
            data=symbols,
            message="Retrieved all Binance symbols",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the total number of instruments available on Binance."""
        self._ensure_exchange_info()
        count = len(self._catalog_ordered)
        self.logger.info(
            "FR-BROKER-BINANCE-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-BINANCE-SYMBOLS", "count": count},
        )
        return StandardResponse.success(data=count, extensions={"broker": self.name})

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

        url = f"{self.base_url}{self.api_prefix}/klines"
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
        url = (
            f"{self.base_url}{self.api_prefix}/trades"
            f"?symbol={urllib.parse.quote(sym_clean)}&limit={limit}"
        )
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


def create_adapter(_context: PluginHostContext | None = None) -> BinanceBroker:
    """Plugin entrypoint factory constructing BinanceBroker adapter."""
    logger.info("Initializing Binance cryptocurrency broker plugin adapter.")
    return BinanceBroker()


if __name__ == "__main__":
    print("=" * 60)
    print("Binance Crypto Broker Plugin Self-Test")
    print("=" * 60)

    broker = create_adapter()

    # 1. Test symbol info query
    info_resp = broker.get_symbol_info("BTCUSDT")
    print(
        f"[1] Symbol Info BTCUSDT: success={info_resp.is_success}, "
        f"description='{info_resp.data.description if info_resp.data else None}', "
        f"digits={info_resp.data.digits if info_resp.data else None}"
    )
    assert info_resp.is_success, f"BTCUSDT symbol info failed: {info_resp.message}"
    assert info_resp.data is not None
    assert info_resp.data.name == "BTCUSDT"

    # 2. Test total count
    count_resp = broker.get_num_of_symbols()
    print(f"[2] Total Symbols: {count_resp.data}")
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data > 100

    # 3. Test symbols listing
    syms_resp = broker.get_symbols(group="USDT")
    print(f"[3] USDT Symbols count: {len(syms_resp.data) if syms_resp.data else 0}")
    assert syms_resp.is_success
    assert syms_resp.data is not None
    assert len(syms_resp.data) > 0

    # 4. Test historical klines
    bars_resp = broker.get_bars("BTCUSDT", count=5)
    print(
        f"[4] Live Klines BTCUSDT: success={bars_resp.is_success}, "
        f"count={len(bars_resp.data) if bars_resp.data else 0}"
    )
    assert bars_resp.is_success, f"Bars retrieval failed: {bars_resp.message}"
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 5

    # 5. Test real ticks
    ticks_resp = broker.get_ticks("BTCUSDT", count=5)
    print(
        f"[5] Live Ticks BTCUSDT: success={ticks_resp.is_success}, "
        f"count={len(ticks_resp.data) if ticks_resp.data else 0}"
    )
    assert ticks_resp.is_success, f"Ticks retrieval failed: {ticks_resp.message}"
    assert ticks_resp.data is not None
    assert len(ticks_resp.data) == 5

    # 6. Test trading rejection
    from app.plugins.brokers.contracts import TradeRequest

    trade_resp = broker.trade(TradeRequest(symbol="BTCUSDT", volume=0.001))
    print(
        f"[6] Trade Rejection: success={trade_resp.is_success}, "
        f"message='{trade_resp.message}'"
    )
    assert not trade_resp.is_success
    assert "doesn't have trading capabilities" in trade_resp.message

    print("=" * 60)
    print("ALL BINANCE CRYPTO SELF-TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
