"""Binance cryptocurrency market data and symbol metadata broker implementation.

Description:
    Implements a cryptocurrency market data and symbol catalog broker connecting
    directly to Binance public REST APIs (Spot, USDT-M, and Coin-M).
    Conforms directly to the canonical `TradingBackend` protocol via `DataBrokerBackend`.
    Provides normalized historical candlestick bars (`MarketData.Bars`), trade ticks
    (`MarketData.Ticks`), and symbol specifications (`SymbolSnapshot`).

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Binance Exchange Integration.

Key Capabilities:
    - FR-BROKER-BINANCE-SYMBOLS: Binance ExchangeInfo Symbol Resolution
      Associated: `[BinanceBroker.symbol_info()]`, `[BinanceBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found or request fails.
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Trades
      Associated: `[BinanceBroker.fetch_bars()]`, `[BinanceBroker.fetch_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API, and
      ERROR log on network or parsing failure.

Python API Usage:
    ```python
    from app.services.brokers.crypto import BinanceBroker
    from app.workspace.data_manager.history import get_historical_bars, get_ticks
    from app.workspace.data_manager import Timeframe

    broker = BinanceBroker()
    bars = await get_historical_bars(broker, "BTCUSDT", Timeframe.PERIOD_H1, count=5)
    assert len(bars) > 0
    ticks = await get_ticks(broker, "BTCUSDT", count=5)
    assert len(ticks) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker binance`
"""

from __future__ import annotations

from typing import Any, override

import requests
from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._http import execute_bounded_get
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
    ProviderUnsupportedError,
    ProviderValidationError,
)
from app.services.trading import SymbolSnapshot
from app.workspace.data_manager import Timeframe
from app.workspace.data_manager.history import DataBrokerBackend
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__name__)

USER_AGENT = "HaruQuantAI-BinanceConnector/1.0"

SPOT_BASE_URL = "https://api.binance.com"
FUTURES_USDT_BASE_URL = "https://fapi.binance.com"
FUTURES_COIN_BASE_URL = "https://dapi.binance.com"

BINANCE_SPOT_BASE_URL = SPOT_BASE_URL
BINANCE_FUTURES_USDT_BASE_URL = FUTURES_USDT_BASE_URL
BINANCE_FUTURES_COIN_BASE_URL = FUTURES_COIN_BASE_URL

TIMEFRAME_MAP: dict[str, str] = {
    "M1": "1m",
    "1M": "1m",
    Timeframe.PERIOD_M1.value: "1m",
    "M3": "3m",
    "3M": "3m",
    Timeframe.PERIOD_M3.value: "3m",
    "M5": "5m",
    "5M": "5m",
    Timeframe.PERIOD_M5.value: "5m",
    "M15": "15m",
    "15M": "15m",
    Timeframe.PERIOD_M15.value: "15m",
    "M30": "30m",
    "30M": "30m",
    Timeframe.PERIOD_M30.value: "30m",
    "H1": "1h",
    "1H": "1h",
    Timeframe.PERIOD_H1.value: "1h",
    "H2": "2h",
    "2H": "2h",
    Timeframe.PERIOD_H2.value: "2h",
    "H4": "4h",
    "4H": "4h",
    Timeframe.PERIOD_H4.value: "4h",
    "D1": "1d",
    "1D": "1d",
    Timeframe.PERIOD_D1.value: "1d",
    "W1": "1w",
    "1W": "1w",
    Timeframe.PERIOD_W1.value: "1w",
    "MN1": "1M",
    "1MN": "1M",
    Timeframe.PERIOD_MN1.value: "1M",
}

DEFAULT_CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "ADAUSDT",
    "XRPUSDT",
]

PLUGIN_MANIFEST = {
    "id": "crypto",
    "name": "Crypto",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "crypto:create_adapter",
    "description": "Cryptocurrency exchanges provider (Binance, Bitfinex, Coinbase, Poloniex)",
    "capabilities": ["data.fetch"],
}

__all__ = [
    "BINANCE_FUTURES_COIN_BASE_URL",
    "BINANCE_FUTURES_USDT_BASE_URL",
    "BINANCE_SPOT_BASE_URL",
    "BinanceBroker",
    "CryptoBroker",
    "PLUGIN_MANIFEST",
    "_calc_digits",
    "_map_timeframe",
    "create_adapter",
    "main",
]


def _calc_digits(tick_size: float) -> int:
    """Derive decimal digits from tickSize."""
    if tick_size <= 0:
        return 0
    s = f"{tick_size:.10f}".rstrip("0")
    if "." in s:
        return len(s.split(".")[1])
    return 0


def _map_timeframe(timeframe: str) -> str:
    """Map timeframe to Binance interval string."""
    tf_str = str(timeframe).upper().strip()
    return TIMEFRAME_MAP.get(tf_str, "1m")


class BinanceBroker(DataBrokerBackend):
    """Binance cryptocurrency market data and symbol catalog broker."""

    def __init__(
        self,
        name: str = "Binance",
        default_market: str = "spot",
        venue: str | None = None,
        api_key: str | None = None,
        exchange: str = "binance",
    ) -> None:
        """Initialize Binance broker."""
        super().__init__(name=name)
        self.exchange = exchange.lower().strip()
        self.venue = (venue or default_market).lower().strip()
        if self.venue in ("usdt-m", "fapi", "futures_usdt"):
            self.base_url = FUTURES_USDT_BASE_URL
            self.api_prefix = "/fapi/v1"
        elif self.venue in ("coin-m", "dapi", "futures_coin"):
            self.base_url = FUTURES_COIN_BASE_URL
            self.api_prefix = "/dapi/v1"
        else:
            self.base_url = SPOT_BASE_URL
            self.api_prefix = "/api/v3"

        self.session = requests.Session()
        if api_key:
            self.session.headers["X-MBX-APIKEY"] = api_key
        retries: Any = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=16)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"User-Agent": USER_AGENT})

        self._symbols_cache: dict[str, SymbolSnapshot] = {}

        self.capabilities = ProviderCapabilities(
            provider_id="crypto",
            display_name="Crypto",
            category="Crypto",
            supported_timeframes=(
                "M1",
                "M5",
                "M15",
                "M30",
                "H1",
                "H2",
                "H4",
                "D1",
                "W1",
            ),
            supported_modes=("bars", "ticks"),
            requires_auth=False,
            rate_limit_rps=10.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=False,
            description="Cryptocurrency exchange provider (Binance, Bitfinex, Coinbase, Poloniex)",
        )
        self._exchange_adapters: dict[str, Any] = {}

    @override
    def close_sync(self) -> None:
        """Close session resources synchronously."""
        self._is_connected = False
        if hasattr(self, "session"):
            self.session.close()
        for adapter in getattr(self, "_exchange_adapters", {}).values():
            if hasattr(adapter, "session") and adapter.session is not self.session:
                adapter.session.close()

    @override
    async def close(self) -> None:
        """Close session resources asynchronously."""
        self.close_sync()

    def check_health(self) -> Any:
        """Inspect exchange connectivity."""
        try:
            r = self.session.get(f"{self.base_url}{self.api_prefix}/ping", timeout=5.0)
            conn = r.status_code == 200
            return ProviderHealth(
                provider_id="crypto",
                status="available" if conn else "failed",
                connected=conn,
                message=f"Exchange '{self.exchange}' ping OK"
                if conn
                else f"Ping status {r.status_code}",
                capabilities=self.capabilities,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_id="crypto",
                status="failed",
                connected=False,
                message=f"Ping error: {exc}",
                capabilities=self.capabilities,
            )

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol string."""
        sym = symbol.strip().upper().replace("/", "").replace("_", "").replace("-", "")
        if sym.endswith(":USDT"):
            sym = sym[:-5] + "USDT"
        return sym

    def _map_timeframe(self, timeframe: str) -> str:
        """Map timeframe to Binance interval string."""
        tf_str = str(timeframe).upper().strip()
        return TIMEFRAME_MAP.get(tf_str, "1h")

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Resolve instrument specifications as canonical SymbolSnapshot."""
        sym_clean = self._normalize_symbol(symbol)
        if sym_clean in self._symbols_cache:
            return self._symbols_cache[sym_clean]

        url = f"{self.base_url}{self.api_prefix}/exchangeInfo"
        try:
            r = self.session.get(url, params={"symbol": sym_clean}, timeout=(5.0, 10.0))
            if r.status_code == 200:
                data = r.json()
                symbols_list = data.get("symbols", [])
                if symbols_list:
                    s_data = symbols_list[0]
                    tick_size = 0.01
                    step_size = 1.0
                    for f in s_data.get("filters", []):
                        ft = f.get("filterType")
                        if ft == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize") or 0.01)
                        elif ft == "LOT_SIZE":
                            step_size = float(f.get("stepSize") or 1.0)
                    dec = _calc_digits(tick_size)
                    snap = SymbolSnapshot(
                        name=sym_clean,
                        custom=False,
                        digits=dec,
                        point=tick_size,
                        currency_base=s_data.get("baseAsset", ""),
                        currency_profit=s_data.get("quoteAsset", ""),
                        trade_contract_size=step_size,
                        trade_tick_size=tick_size,
                        trade_tick_value=tick_size,
                    )
                    self._symbols_cache[sym_clean] = snap
                    return snap
        except Exception as exc:
            self.logger.warning(
                "FR-BROKER-BINANCE-SYMBOLS: Error fetching exchangeInfo: %s", exc
            )

        snap = SymbolSnapshot(name=sym_clean, digits=2, point=0.01)
        self._symbols_cache[sym_clean] = snap
        return snap

    @override
    def symbols_get(self) -> list[str]:
        """Return default popular symbols or cached symbols."""
        if self._symbols_cache:
            return list(self._symbols_cache.keys())
        return list(DEFAULT_CRYPTO_SYMBOLS)

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
        """Retrieve real historical candlestick bars from configured crypto exchange."""
        del mode
        if self.exchange == "bitfinex":
            from app.services.brokers.exchanges.bitfinex import BitfinexExchangeAdapter

            return BitfinexExchangeAdapter(session=self.session).fetch_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                count=count,
                limit=limit,
            )
        if self.exchange == "coinbase":
            from app.services.brokers.exchanges.coinbase import CoinbaseExchangeAdapter

            return CoinbaseExchangeAdapter(session=self.session).fetch_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                count=count,
                limit=limit,
            )
        if self.exchange == "poloniex":
            from app.services.brokers.exchanges.poloniex import PoloniexExchangeAdapter

            return PoloniexExchangeAdapter(session=self.session).fetch_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                count=count,
                limit=limit,
            )

        sym_clean = self._normalize_symbol(symbol)
        interval = self._map_timeframe(timeframe)
        url = f"{self.base_url}{self.api_prefix}/klines"
        target_count = count if count > 0 else limit
        req_limit = min(target_count or 500, 1000)

        params: dict[str, Any] = {
            "symbol": sym_clean,
            "interval": interval,
            "limit": req_limit,
        }
        if start > 0 and 0 < end < 2**40 and end >= start:
            params["startTime"] = start * 1000
            params["endTime"] = end * 1000
        elif 0 < end < 2**40 and start == 0:
            params["endTime"] = end * 1000
        elif start > 0:
            params["startTime"] = start * 1000

        try:
            r = execute_bounded_get(
                self.session,
                url,
                params=params,
                provider="crypto:binance",
            )
            if r.status_code != 200:
                raise BridgeError(
                    f"Binance klines request failed with status {r.status_code}: {r.text}",
                    code="REMOTE_ERROR",
                )
            raw_klines: list[list[Any]] = r.json()
            rows: list[dict[str, Any]] = []
            for row in raw_klines:
                open_ts_ms = int(row[0])
                o = float(row[1])
                h = float(row[2])
                l = float(row[3])
                c = float(row[4])
                vol = float(row[5])
                count_trades = int(row[8])
                rows.append(
                    {
                        "time": int(open_ts_ms / 1000),
                        "open": o,
                        "high": h,
                        "low": l,
                        "close": c,
                        "tick_volume": count_trades if count_trades > 0 else int(vol),
                        "spread": 0,
                        "real_volume": vol,
                    }
                )

            rows.sort(key=lambda item: item["time"])
            deduped: list[dict[str, Any]] = []
            last_t: int | None = None
            for row_item in rows:
                if last_t is None or row_item["time"] > last_t:
                    deduped.append(row_item)
                    last_t = row_item["time"]

            if target_count and len(deduped) > target_count:
                deduped = deduped[-target_count:]
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to retrieve klines from Binance for '{sym_clean}': {exc}",
                code="KLINE_ERROR",
            ) from exc

    @override
    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str = "latest",
        start_ms: int = 0,
        end_ms: int = 0,
        count: int = 0,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Retrieve historical aggregate trades from Binance REST API."""
        del mode
        sym_clean = self._normalize_symbol(symbol)
        target_count = count if count > 0 else limit
        req_limit = min(target_count or 100, 1000)
        url = f"{self.base_url}{self.api_prefix}/aggTrades"
        params: dict[str, Any] = {
            "symbol": sym_clean,
            "limit": req_limit,
        }
        if start_ms > 0:
            params["startTime"] = start_ms
        if end_ms > 0:
            params["endTime"] = end_ms

        try:
            r = execute_bounded_get(
                self.session,
                url,
                params=params,
                provider="crypto:binance",
            )
            if r.status_code != 200:
                raise BridgeError(
                    f"Binance aggTrades request failed with status {r.status_code}: {r.text}",
                    code="REMOTE_ERROR",
                )
            raw_trades: list[dict[str, Any]] = r.json()
            rows: list[dict[str, Any]] = []
            for t in raw_trades:
                p = float(t.get("p") or 0.0)
                qty = float(t.get("q") or 0.0)
                t_ms = int(t.get("T") or 0)
                rows.append(
                    {
                        "time_msc": t_ms,
                        "bid": p,
                        "ask": p,
                        "last": p,
                        "volume": qty,
                        "flags": 0,
                        "volume_real": qty,
                    }
                )
            rows.sort(key=lambda r: r["time_msc"])
            if target_count and len(rows) > target_count:
                rows = rows[-target_count:]
            return rows
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to retrieve trades from Binance for '{sym_clean}': {exc}",
                code="TRADES_ERROR",
            ) from exc

    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Fetch historical records adhering to Stage 2C contract."""
        request.validate()
        exch = (request.exchange or self.exchange or "binance").lower().strip()
        if exch not in ("binance", "bitfinex", "coinbase", "poloniex"):
            raise ProviderValidationError(
                f"Unknown crypto exchange '{exch}'. Supported: binance, bitfinex, coinbase, poloniex",
                provider="crypto",
            )

        if exch in ("bitfinex", "coinbase", "poloniex"):
            if request.kind == "ticks" or request.timeframe.upper() == "TICK":
                raise ProviderUnsupportedError(
                    f"{exch.capitalize()} exchange does not support tick history; only bars are supported",
                    provider="crypto",
                )

        start_sec = request.start_epoch() or 0
        end_sec = request.end_epoch() or 0

        if exch == "bitfinex":
            if "bitfinex" not in self._exchange_adapters:
                from app.services.brokers.exchanges.bitfinex import (
                    BitfinexExchangeAdapter,
                )

                self._exchange_adapters["bitfinex"] = BitfinexExchangeAdapter(
                    session=self.session
                )
            bf_adapter = self._exchange_adapters["bitfinex"]
            rows = bf_adapter.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                count=request.count,
                start=start_sec,
                end=end_sec,
                token=token,
            )
            return HistoryPage(
                provider="crypto",
                symbol=request.symbol,
                timeframe=request.timeframe,
                kind=request.kind,
                rows=rows,
                is_complete=True,
                provenance={"exchange": "bitfinex"},
            )
        if exch == "coinbase":
            if "coinbase" not in self._exchange_adapters:
                from app.services.brokers.exchanges.coinbase import (
                    CoinbaseExchangeAdapter,
                )

                self._exchange_adapters["coinbase"] = CoinbaseExchangeAdapter(
                    session=self.session
                )
            cb_adapter = self._exchange_adapters["coinbase"]
            rows = cb_adapter.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                count=request.count,
                start=start_sec,
                end=end_sec,
                token=token,
            )
            return HistoryPage(
                provider="crypto",
                symbol=request.symbol,
                timeframe=request.timeframe,
                kind=request.kind,
                rows=rows,
                is_complete=True,
                provenance={"exchange": "coinbase"},
            )
        if exch == "poloniex":
            if "poloniex" not in self._exchange_adapters:
                from app.services.brokers.exchanges.poloniex import (
                    PoloniexExchangeAdapter,
                )

                self._exchange_adapters["poloniex"] = PoloniexExchangeAdapter(
                    session=self.session
                )
            px_adapter = self._exchange_adapters["poloniex"]
            rows = px_adapter.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                count=request.count,
                start=start_sec,
                end=end_sec,
                token=token,
            )
            return HistoryPage(
                provider="crypto",
                symbol=request.symbol,
                timeframe=request.timeframe,
                kind=request.kind,
                rows=rows,
                is_complete=True,
                provenance={"exchange": "poloniex"},
            )

        # Default: Binance
        if token is not None:
            token.check_cancelled()
        if request.kind == "ticks" or request.timeframe.upper() == "TICK":
            rows = self.fetch_ticks(
                symbol=request.symbol,
                mode=request.mode,
                start_ms=(request.start_epoch() or 0) * 1000,
                end_ms=(request.end_epoch() or 0) * 1000,
                count=request.count,
                limit=request.limit,
            )
        else:
            rows = self.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                mode=request.mode,
                start=start_sec,
                end=end_sec,
                count=request.count,
                limit=request.limit,
            )
        return HistoryPage(
            provider="crypto",
            symbol=request.symbol,
            timeframe=request.timeframe,
            kind=request.kind,
            rows=rows,
            is_complete=True,
            provenance={"exchange": "binance"},
        )


CryptoBroker = BinanceBroker


def create_adapter(context: PluginHostContext | None = None) -> BinanceBroker:
    """Factory creating configured BinanceBroker adapter."""
    del context
    return BinanceBroker()


def main() -> None:
    """Demonstrate executable usage of BinanceBroker."""
    broker = BinanceBroker()
    health = broker.check_health()
    logger.info("Binance health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
