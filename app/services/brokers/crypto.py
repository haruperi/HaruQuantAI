"""Binance and cryptocurrency exchange market data and symbol metadata broker.

Description:
    Implements a cryptocurrency market data and symbol catalog broker connecting
    directly to Binance (Spot, USDT-M, and Coin-M) and supported exchange venues
    (Bitfinex, Coinbase, and Poloniex). Conforms directly to the canonical
    `TradingBackend` protocol via `DataBrokerBackend`. Provides normalized
    historical candlestick bars (`MarketData.Bars`), trade ticks
    (`MarketData.Ticks`), and symbol specifications (`SymbolInfo`).

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Cryptocurrency exchange integrations.

Key Capabilities:
    - FR-BROKER-BINANCE-SYMBOLS: Binance ExchangeInfo Symbol Resolution
      Associated: `[BinanceBroker.symbol_info()]`, `[BinanceBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found or request fails.
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Trades
      Associated: `[BinanceBroker.fetch_bars()]`, `[BinanceBroker.fetch_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API, and
      ERROR log on network or parsing failure.
    - FR-BROKER-BITFINEX-CANDLES: Fetch and normalize historical candles from Bitfinex API v2.
      Associated: `[BitfinexExchangeAdapter.fetch_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.
    - FR-BROKER-COINBASE-CANDLES: Fetch and normalize historical candles from Coinbase API.
      Associated: `[CoinbaseExchangeAdapter.fetch_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.
    - FR-BROKER-POLONIEX-CANDLES: Fetch and normalize historical candles from Poloniex API.
      Associated: `[PoloniexExchangeAdapter.fetch_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.

Python API Usage:
    ```python
    from app.services.brokers.crypto import BinanceBroker
    from app.services.include.data import get_historical_bars, get_ticks
    from app.services.include.enums import Timeframe

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

from datetime import UTC, datetime
from typing import Any, override

import requests
from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._http import create_http_session, execute_bounded_get
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
from app.services.include.contracts import SymbolInfo
from app.services.include.data import DataBrokerBackend
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

USER_AGENT = "HaruQuantAI-BinanceConnector/1.0"

SPOT_BASE_URL = "https://api.binance.com"
FUTURES_USDT_BASE_URL = "https://fapi.binance.com"
FUTURES_COIN_BASE_URL = "https://dapi.binance.com"

BINANCE_SPOT_BASE_URL = SPOT_BASE_URL
BINANCE_FUTURES_USDT_BASE_URL = FUTURES_USDT_BASE_URL
BINANCE_FUTURES_COIN_BASE_URL = FUTURES_COIN_BASE_URL

BINANCE_TIMEFRAME_MAP: dict[Timeframe, str] = {
    Timeframe.PERIOD_M1: "1m",
    Timeframe.PERIOD_M3: "3m",
    Timeframe.PERIOD_M5: "5m",
    Timeframe.PERIOD_M15: "15m",
    Timeframe.PERIOD_M30: "30m",
    Timeframe.PERIOD_H1: "1h",
    Timeframe.PERIOD_H2: "2h",
    Timeframe.PERIOD_H4: "4h",
    Timeframe.PERIOD_D1: "1d",
    Timeframe.PERIOD_W1: "1w",
    Timeframe.PERIOD_MN1: "1M",
}

TIMEFRAME_MAP = BINANCE_TIMEFRAME_MAP

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
    "BINANCE_TIMEFRAME_MAP",
    "BITFINEX_CANDLES_FR",
    "BITFINEX_TIMEFRAME_MAP",
    "BinanceBroker",
    "BitfinexExchangeAdapter",
    "COINBASE_CANDLES_FR",
    "COINBASE_GRANULARITY_MAP",
    "COINBASE_SUPPORTED_GRANULARITIES",
    "CoinbaseExchangeAdapter",
    "CryptoBroker",
    "PLUGIN_MANIFEST",
    "POLONIEX_CANDLES_FR",
    "POLONIEX_INTERVAL_MAP",
    "PoloniexExchangeAdapter",
    "TIMEFRAME_MAP",
    "_calc_digits",
    "_map_timeframe",
    "create_adapter",
    "main",
]

BITFINEX_CANDLES_FR = "FR-BROKER-BITFINEX-CANDLES"
COINBASE_CANDLES_FR = "FR-BROKER-COINBASE-CANDLES"
POLONIEX_CANDLES_FR = "FR-BROKER-POLONIEX-CANDLES"

BITFINEX_TIMEFRAME_MAP: dict[Timeframe, str] = {
    Timeframe.PERIOD_M1: "1m",
    Timeframe.PERIOD_M5: "5m",
    Timeframe.PERIOD_M15: "15m",
    Timeframe.PERIOD_M30: "30m",
    Timeframe.PERIOD_H1: "1h",
    Timeframe.PERIOD_H3: "3h",
    Timeframe.PERIOD_H6: "6h",
    Timeframe.PERIOD_H12: "12h",
    Timeframe.PERIOD_D1: "1D",
    Timeframe.PERIOD_W1: "1W",
    Timeframe.PERIOD_MN1: "1M",
}

COINBASE_SUPPORTED_GRANULARITIES: frozenset[int] = frozenset(
    {60, 300, 900, 3600, 21600, 86400}
)

COINBASE_GRANULARITY_MAP: dict[Timeframe, int] = {
    Timeframe.PERIOD_M1: 60,
    Timeframe.PERIOD_M5: 300,
    Timeframe.PERIOD_M15: 900,
    Timeframe.PERIOD_H1: 3600,
    Timeframe.PERIOD_H6: 21600,
    Timeframe.PERIOD_D1: 86400,
}

POLONIEX_INTERVAL_MAP: dict[Timeframe, str] = {
    Timeframe.PERIOD_M1: "MINUTE_1",
    Timeframe.PERIOD_M5: "MINUTE_5",
    Timeframe.PERIOD_M15: "MINUTE_15",
    Timeframe.PERIOD_M30: "MINUTE_30",
    Timeframe.PERIOD_H1: "HOUR_1",
    Timeframe.PERIOD_H2: "HOUR_2",
    Timeframe.PERIOD_H4: "HOUR_4",
    Timeframe.PERIOD_H6: "HOUR_6",
    Timeframe.PERIOD_H12: "HOUR_12",
    Timeframe.PERIOD_D1: "DAY_1",
    Timeframe.PERIOD_W1: "WEEK_1",
    Timeframe.PERIOD_MN1: "MONTH_1",
}


class BitfinexExchangeAdapter:
    """Read-only market data adapter for Bitfinex exchange."""

    BASE_URL = "https://api-pub.bitfinex.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-BitfinexAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 1000,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Bitfinex v2 candles endpoint."""
        sym = symbol.strip().upper()
        if not sym.startswith("T"):
            sym = f"t{sym}"

        parsed_tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_M1)
        tf = BITFINEX_TIMEFRAME_MAP.get(parsed_tf, "1m")
        url = f"{self.BASE_URL}/v2/candles/trade:{tf}:{sym}/hist"

        target_limit = min(max(count, limit), 1000)
        params: dict[str, Any] = {"limit": target_limit, "sort": 1}
        if start and start > 0:
            params["start"] = start * 1000 if start < 100_000_000_000 else start
        if end and end > 0:
            params["end"] = end * 1000 if end < 100_000_000_000 else end

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:bitfinex",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Bitfinex returned status %d for %s",
                BITFINEX_CANDLES_FR,
                resp.status_code,
                sym,
            )
            return []

        payload = resp.json()
        if not isinstance(payload, list):
            return []

        rows: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                continue
            # Layout: [MTS, OPEN, CLOSE, HIGH, LOW, VOLUME]
            mts, o, c, h, l, v = item[0], item[1], item[2], item[3], item[4], item[5]
            rows.append(
                {
                    "time": int(mts // 1000),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "tick_volume": int(v) if v else 1,
                    "spread": 0,
                    "real_volume": int(v) if v else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        logger.debug(
            "%s: Retrieved %d bars for %s", BITFINEX_CANDLES_FR, len(rows), sym
        )
        return rows


class CoinbaseExchangeAdapter:
    """Read-only market data adapter for Coinbase exchange."""

    BASE_URL = "https://api.exchange.coinbase.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-CoinbaseAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 300,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Coinbase products candles endpoint."""
        sym = symbol.strip().upper()
        if "-" not in sym:
            if sym.endswith("USDT"):
                sym = f"{sym[:-4]}-USDT"
            elif sym.endswith("USD"):
                sym = f"{sym[:-3]}-USD"

        parsed_tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_M1)
        sec = parsed_tf.to_seconds()
        gran = sec if sec in COINBASE_SUPPORTED_GRANULARITIES else 60
        url = f"{self.BASE_URL}/products/{sym}/candles"

        params: dict[str, Any] = {"granularity": gran}
        if start and start > 0:
            ts = start if start < 100_000_000_000 else start // 1000
            params["start"] = datetime.fromtimestamp(ts, tz=UTC).isoformat()
        if end and end > 0:
            ts = end if end < 100_000_000_000 else end // 1000
            params["end"] = datetime.fromtimestamp(ts, tz=UTC).isoformat()

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:coinbase",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Coinbase returned status %d for %s",
                COINBASE_CANDLES_FR,
                resp.status_code,
                sym,
            )
            return []

        payload = resp.json()
        if not isinstance(payload, list):
            return []

        rows: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                continue
            # Layout: [time, low, high, open, close, volume]
            t, low_val, high_val, open_val, close_val, vol = (
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
            )
            rows.append(
                {
                    "time": int(t),
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "close": float(close_val),
                    "tick_volume": int(vol) if vol else 1,
                    "spread": 0,
                    "real_volume": int(vol) if vol else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        target_count = count if count > 0 else limit
        if target_count and len(rows) > target_count:
            rows = rows[-target_count:]

        logger.debug(
            "%s: Retrieved %d bars for %s", COINBASE_CANDLES_FR, len(rows), sym
        )
        return rows


class PoloniexExchangeAdapter:
    """Read-only market data adapter for Poloniex exchange."""

    BASE_URL = "https://api.poloniex.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-PoloniexAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 500,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Poloniex markets candles endpoint."""
        sym = symbol.strip().upper()
        if "_" not in sym:
            if sym.endswith("USDT"):
                sym = f"{sym[:-4]}_USDT"
            elif sym.endswith("USD"):
                sym = f"{sym[:-3]}_USD"

        parsed_tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_M1)
        interval = POLONIEX_INTERVAL_MAP.get(parsed_tf, "MINUTE_1")
        url = f"{self.BASE_URL}/markets/{sym}/candles"

        target_limit = min(max(count, limit), 500)
        params: dict[str, Any] = {"interval": interval, "limit": target_limit}
        if start and start > 0:
            params["startTime"] = start * 1000 if start < 100_000_000_000 else start
        if end and end > 0:
            params["endTime"] = end * 1000 if end < 100_000_000_000 else end

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:poloniex",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Poloniex returned status %d for %s",
                POLONIEX_CANDLES_FR,
                resp.status_code,
                sym,
            )
            return []

        payload = resp.json()
        if not isinstance(payload, list):
            return []

        rows: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 13:
                continue
            # Layout: [low, high, open, close, amount, quantity, buyTakerAmount, buyTakerQuantity, tradeCount, ts, weightedAverage, interval, startTime, closeTime]
            low_val, high_val, open_val, close_val, qty, start_ts = (
                item[0],
                item[1],
                item[2],
                item[3],
                item[5],
                item[12],
            )
            rows.append(
                {
                    "time": int(start_ts // 1000),
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "close": float(close_val),
                    "tick_volume": int(float(qty)) if qty else 1,
                    "spread": 0,
                    "real_volume": int(float(qty)) if qty else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        logger.debug(
            "%s: Retrieved %d bars for %s", POLONIEX_CANDLES_FR, len(rows), sym
        )
        return rows


def _calc_digits(tick_size: float) -> int:
    """Derive decimal digits from tickSize."""
    if tick_size <= 0:
        return 0
    s = f"{tick_size:.10f}".rstrip("0")
    if "." in s:
        return len(s.split(".")[1])
    return 0


def _map_timeframe(timeframe: str | Timeframe) -> str:
    """Map timeframe to Binance interval string."""
    tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_M1)
    return BINANCE_TIMEFRAME_MAP.get(tf, "1m")


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

        self.session = create_http_session(
            user_agent=USER_AGENT, retries=3, backoff=0.3, pool_size=16
        )
        if api_key:
            self.session.headers["X-MBX-APIKEY"] = api_key

        self._symbols_cache: dict[str, SymbolInfo] = {}

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
        super().close_sync()
        for adapter in getattr(self, "_exchange_adapters", {}).values():
            if hasattr(adapter, "session") and adapter.session is not self.session:
                adapter.session.close()

    def _get_exchange_adapter(self, exch: str) -> Any:
        """Resolve and cache sub-exchange adapters."""
        if exch not in self._exchange_adapters:
            if exch == "bitfinex":
                self._exchange_adapters["bitfinex"] = BitfinexExchangeAdapter(
                    session=self.session
                )
            elif exch == "coinbase":
                self._exchange_adapters["coinbase"] = CoinbaseExchangeAdapter(
                    session=self.session
                )
            elif exch == "poloniex":
                self._exchange_adapters["poloniex"] = PoloniexExchangeAdapter(
                    session=self.session
                )
        return self._exchange_adapters[exch]

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

    def _map_timeframe(self, timeframe: str | Timeframe) -> str:
        """Map timeframe to Binance interval string."""
        tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_H1)
        return BINANCE_TIMEFRAME_MAP.get(tf, "1h")

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve instrument specifications as canonical SymbolInfo."""
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
                    snap = SymbolInfo(
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

        snap = SymbolInfo(name=sym_clean, digits=2, point=0.01)
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
        if self.exchange in ("bitfinex", "coinbase", "poloniex"):
            adapter = self._get_exchange_adapter(self.exchange)
            return adapter.fetch_bars(  # type: ignore[no-any-return]
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
                r_vol = int(vol) if vol >= 1.0 else (1 if vol > 0 else 0)
                rows.append(
                    {
                        "time": int(open_ts_ms / 1000),
                        "open": o,
                        "high": h,
                        "low": l,
                        "close": c,
                        "tick_volume": count_trades if count_trades > 0 else r_vol,
                        "spread": 0,
                        "real_volume": r_vol,
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
                t_vol = int(qty) if qty >= 1.0 else (1 if qty > 0 else 0)
                rows.append(
                    {
                        "time_msc": t_ms,
                        "bid": p,
                        "ask": p,
                        "last": p,
                        "volume": t_vol,
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

    @override
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
            adapter = self._get_exchange_adapter(exch)
            rows = adapter.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                count=request.count,
                start=request.start_epoch() or 0,
                end=request.end_epoch() or 0,
                token=token,
            )
            return HistoryPage(
                provider="crypto",
                symbol=request.symbol,
                timeframe=request.timeframe,
                kind=request.kind,
                rows=rows,
                is_complete=True,
                provenance={"exchange": exch},
            )

        page = super().read_history(request, token=token)
        page.provenance = {"exchange": "binance"}
        return page


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
