"""Binance and cryptocurrency exchange market data and symbol metadata clients.

Description:
    Implements cryptocurrency market data and symbol catalog clients connecting
    directly to Binance (Spot, USDT-M, and Coin-M) and supported exchange venues
    (Bitfinex, Coinbase, and Poloniex). Conforms directly to the uniform `BrokerClient`
    interface. Provides normalized historical candlestick bars (`MarketBar`),
    trade ticks (`MarketTick`), and symbol specifications (`SymbolInfo`).

Purpose:
    FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE: Cryptocurrency exchange integrations.

Key Capabilities:
    - FR-BROKER-BINANCE-SYMBOLS: Binance ExchangeInfo Symbol Resolution
      Associated: `[BinanceClient.get_symbol_info()]`, `[BinanceClient.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found or request fails.
    - FR-BROKER-BINANCE-MARKET-DATA: Historical Kline Extraction and Real Trades
      Associated: `[BinanceClient.get_bars()]`, `[BinanceClient.get_ticks()]`
      Logging: Emits INFO log with bar counts retrieved from Binance API, and
      ERROR log on network or parsing failure.
    - FR-BROKER-BITFINEX-CANDLES: Fetch and normalize historical candles from Bitfinex API v2.
      Associated: `[BitfinexExchangeAdapter.get_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.
    - FR-BROKER-COINBASE-CANDLES: Fetch and normalize historical candles from Coinbase API.
      Associated: `[CoinbaseExchangeAdapter.get_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.
    - FR-BROKER-POLONIEX-CANDLES: Fetch and normalize historical candles from Poloniex API.
      Associated: `[PoloniexExchangeAdapter.get_bars()]`
      Logging: Emits DEBUG when requesting candles and logging received record counts.

Python API Usage:
    ```python
    from app.services.brokers.crypto import BinanceClient
    from app.services.include.enums import Timeframe

    client = BinanceClient()
    bars = client.get_bars("BTCUSDT", Timeframe.PERIOD_H1, count=5)
    assert len(bars) > 0
    ticks = client.get_ticks("BTCUSDT", count=5)
    assert len(ticks) > 0
    client.disconnect()
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker binance`
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, override

import requests
from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    create_http_session,
    epoch_millis,
    epoch_seconds,
    execute_bounded_get,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
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

__all__ = [
    "BinanceClient",
    "BitfinexClient",
    "CoinbaseClient",
    "CryptoClient",
    "PoloniexClient",
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

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str | Timeframe,
        start: int = 0,
        end: int = 0,
        count: int = 0,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Fetch historical candlestick bars from Bitfinex API v2."""
        tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_H1)
        interval = BITFINEX_TIMEFRAME_MAP.get(tf, "1h")
        sym = symbol.strip().upper().replace("/", "").replace("_", "").replace("-", "")
        if not sym.startswith("t"):
            sym = f"t{sym}"

        params: dict[str, Any] = {"limit": min(count or limit, 1000), "sort": 1}
        if start > 0:
            params["start"] = start * 1000
        if end > 0:
            params["end"] = end * 1000

        url = f"{self.BASE_URL}/v2/candles/trade:{interval}:{sym}/hist"
        r = execute_bounded_get(
            self.session, url, params=params, provider="crypto:bitfinex"
        )
        if r.status_code == 429:
            raise BridgeError(
                "Bitfinex rate limit exceeded (HTTP 429)", code="RATE_LIMITED"
            )
        if r.status_code != 200:
            raise BridgeError(
                f"Bitfinex candle fetch failed: HTTP {r.status_code}",
                code="REMOTE_ERROR",
            )

        data = r.json()
        if not isinstance(data, list):
            raise BridgeError(
                f"Invalid Bitfinex candle payload for {sym}: expected list, got {type(data).__name__}",
                code="INVALID_PAYLOAD",
            )

        bars: list[MarketBar] = []
        for c in data:
            if not isinstance(c, list) or len(c) < 6:
                raise BridgeError(
                    f"Malformed Bitfinex candle record for {sym}",
                    code="INVALID_PAYLOAD",
                )
            ts_ms, open_p, close_p, high_p, low_p, vol = c[:6]
            r_vol = int(vol) if vol >= 1.0 else (1 if vol > 0 else 0)
            bars.append(
                MarketBar(
                    time=int(ts_ms / 1000),
                    open=float(open_p),
                    high=float(high_p),
                    low=float(low_p),
                    close=float(close_p),
                    tick_volume=r_vol,
                    spread=0,
                    real_volume=r_vol,
                )
            )

        bars.sort(key=lambda b: b.time)
        logger.debug(
            "%s: Retrieved %d bars for %s", BITFINEX_CANDLES_FR, len(bars), sym
        )
        return bars


class CoinbaseExchangeAdapter:
    """Read-only market data adapter for Coinbase API."""

    BASE_URL = "https://api.exchange.coinbase.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-CoinbaseAdapter/1.0")

    def _format_product_id(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if "-" in s:
            return s
        for quote in ("USDT", "USD", "EUR", "GBP", "BTC"):
            if s.endswith(quote) and len(s) > len(quote):
                return f"{s[: -len(quote)]}-{quote}"
        return s

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str | Timeframe,
        start: int = 0,
        end: int = 0,
        count: int = 0,
        limit: int = 300,
    ) -> list[MarketBar]:
        """Fetch historical candles from Coinbase API."""
        tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_M1)
        granularity = COINBASE_GRANULARITY_MAP.get(tf, 60)
        product_id = self._format_product_id(symbol)

        params: dict[str, Any] = {"granularity": granularity}
        if start > 0:
            params["start"] = datetime.fromtimestamp(start, tz=UTC).isoformat()
        if end > 0:
            params["end"] = datetime.fromtimestamp(end, tz=UTC).isoformat()

        url = f"{self.BASE_URL}/products/{product_id}/candles"
        r = execute_bounded_get(
            self.session, url, params=params, provider="crypto:coinbase"
        )
        if r.status_code == 429:
            raise BridgeError(
                "Coinbase rate limit exceeded (HTTP 429)", code="RATE_LIMITED"
            )
        if r.status_code != 200:
            raise BridgeError(
                f"Coinbase candle fetch failed: HTTP {r.status_code}",
                code="REMOTE_ERROR",
            )

        data = r.json()
        if not isinstance(data, list):
            raise BridgeError(
                f"Invalid Coinbase candle payload for {product_id}: expected list, got {type(data).__name__}",
                code="INVALID_PAYLOAD",
            )

        bars: list[MarketBar] = []
        for c in data:
            if not isinstance(c, list) or len(c) < 6:
                raise BridgeError(
                    f"Malformed Coinbase candle record for {product_id}",
                    code="INVALID_PAYLOAD",
                )
            ts, low_p, high_p, open_p, close_p, vol = c[:6]
            r_vol = int(vol) if vol >= 1.0 else (1 if vol > 0 else 0)
            bars.append(
                MarketBar(
                    time=int(ts),
                    open=float(open_p),
                    high=float(high_p),
                    low=float(low_p),
                    close=float(close_p),
                    tick_volume=r_vol,
                    spread=0,
                    real_volume=r_vol,
                )
            )

        bars.sort(key=lambda b: b.time)
        target_count = count if count > 0 else limit
        if target_count and len(bars) > target_count:
            bars = bars[-target_count:]
        logger.debug(
            "%s: Retrieved %d bars for %s", COINBASE_CANDLES_FR, len(bars), product_id
        )
        return bars


class PoloniexExchangeAdapter:
    """Read-only market data adapter for Poloniex API."""

    BASE_URL = "https://api.poloniex.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-PoloniexAdapter/1.0")

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if "_" in s:
            return s
        for quote in ("USDT", "USD", "BTC", "USDC", "ETH"):
            if s.endswith(quote) and len(s) > len(quote):
                return f"{s[: -len(quote)]}_{quote}"
        return s

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str | Timeframe,
        start: int = 0,
        end: int = 0,
        count: int = 0,
        limit: int = 500,
    ) -> list[MarketBar]:
        """Fetch historical candlestick bars from Poloniex API."""
        tf = Timeframe.resolve(timeframe, default=Timeframe.PERIOD_H1)
        interval = POLONIEX_INTERVAL_MAP.get(tf, "HOUR_1")
        sym = self._format_symbol(symbol)

        params: dict[str, Any] = {"limit": min(count or limit, 500)}
        if start > 0:
            params["startTime"] = start * 1000
        if end > 0:
            params["endTime"] = end * 1000

        url = f"{self.BASE_URL}/markets/{sym}/candles"
        params["interval"] = interval
        r = execute_bounded_get(
            self.session, url, params=params, provider="crypto:poloniex"
        )
        if r.status_code == 429:
            raise BridgeError(
                "Poloniex rate limit exceeded (HTTP 429)", code="RATE_LIMITED"
            )
        if r.status_code != 200:
            raise BridgeError(
                f"Poloniex candle fetch failed: HTTP {r.status_code}",
                code="REMOTE_ERROR",
            )

        data = r.json()
        if not isinstance(data, list):
            raise BridgeError(
                f"Invalid Poloniex candle payload for {sym}: expected list, got {type(data).__name__}",
                code="INVALID_PAYLOAD",
            )

        bars: list[MarketBar] = []
        for c in data:
            if not isinstance(c, list) or len(c) < 14:
                raise BridgeError(
                    f"Malformed Poloniex candle record for {sym}",
                    code="INVALID_PAYLOAD",
                )
            low_val, high_val, open_val, close_val, qty = c[0], c[1], c[2], c[3], c[5]
            start_ts = int(c[12]) if len(c) > 12 else 0
            bars.append(
                MarketBar(
                    time=int(start_ts / 1000),
                    open=float(open_val),
                    high=float(high_val),
                    low=float(low_val),
                    close=float(close_val),
                    tick_volume=int(float(qty)) if qty else 1,
                    spread=0,
                    real_volume=int(float(qty)) if qty else 1,
                )
            )

        bars.sort(key=lambda b: b.time)
        logger.debug(
            "%s: Retrieved %d bars for %s", POLONIEX_CANDLES_FR, len(bars), sym
        )
        return bars


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


class CryptoClient(BrokerClient):
    """Uniform cryptocurrency client supporting Binance, Bitfinex, Coinbase, Poloniex."""

    def __init__(
        self,
        name: str = "Crypto",
        default_market: str = "spot",
        venue: str | None = None,
        api_key: str | None = None,
        exchange: str = "binance",
    ) -> None:
        """Initialize cryptocurrency broker client."""
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
        self._exchange_adapters: dict[str, Any] = {}
        self._connected = True

    @override
    def disconnect(self) -> None:
        """Close session resources."""
        super().disconnect()
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
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve instrument specifications strictly from Binance exchangeInfo."""
        sym_clean = self._normalize_symbol(symbol)
        if sym_clean in self._symbols_cache:
            return self._symbols_cache[sym_clean]

        url = f"{self.base_url}{self.api_prefix}/exchangeInfo"
        r = execute_bounded_get(
            self.session,
            url,
            params={"symbol": sym_clean},
            timeout=(5.0, 10.0),
            provider="crypto:binance",
        )
        if r.status_code != 200:
            raise BridgeError(
                f"Binance exchangeInfo request failed for '{sym_clean}' with HTTP {r.status_code}: {r.text}",
                code="REMOTE_ERROR",
            )
        data = r.json()
        symbols_list = data.get("symbols", []) if isinstance(data, dict) else []
        if not symbols_list:
            raise BridgeError(
                f"Symbol '{sym_clean}' not found in Binance exchangeInfo",
                code="SYMBOL_NOT_FOUND",
            )
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

    @override
    def get_symbols(self) -> list[str]:
        """Return default popular symbols or cached symbols."""
        if self._symbols_cache:
            return list(self._symbols_cache.keys())
        return list(DEFAULT_CRYPTO_SYMBOLS)

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Retrieve real historical candlestick bars from configured crypto exchange."""
        del start_pos
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)

        if self.exchange in ("bitfinex", "coinbase", "poloniex"):
            adapter = self._get_exchange_adapter(self.exchange)
            exchange_bars: list[MarketBar] = adapter.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start_sec,
                end=end_sec,
                count=count or 0,
                limit=limit,
            )
            return exchange_bars

        sym_clean = self._normalize_symbol(symbol)
        interval = self._map_timeframe(timeframe)
        url = f"{self.base_url}{self.api_prefix}/klines"
        req_limit = min(count or 500, 1000)
        params: dict[str, Any] = {
            "symbol": sym_clean,
            "interval": interval,
            "limit": req_limit,
        }
        if start_sec > 0 and 0 < end_sec < 2**40 and end_sec >= start_sec:
            params["startTime"] = start_sec * 1000
            params["endTime"] = end_sec * 1000
        elif 0 < end_sec < 2**40 and start_sec == 0:
            params["endTime"] = end_sec * 1000
        elif start_sec > 0:
            params["startTime"] = start_sec * 1000

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
            bars: list[MarketBar] = []
            for row in raw_klines:
                open_ts_ms = int(row[0])
                o = float(row[1])
                h = float(row[2])
                l = float(row[3])
                c = float(row[4])
                vol = float(row[5])
                count_trades = int(row[8])
                r_vol = int(vol) if vol >= 1.0 else (1 if vol > 0 else 0)
                bars.append(
                    MarketBar(
                        time=int(open_ts_ms / 1000),
                        open=o,
                        high=h,
                        low=l,
                        close=c,
                        tick_volume=count_trades if count_trades > 0 else r_vol,
                        spread=0,
                        real_volume=r_vol,
                    )
                )

            bars.sort(key=lambda item: item.time)
            deduped: list[MarketBar] = []
            last_t: int | None = None
            for b in bars:
                if last_t is None or b.time > last_t:
                    deduped.append(b)
                    last_t = b.time

            if count and len(deduped) > count:
                deduped = deduped[-count:]
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to retrieve klines from Binance for '{sym_clean}': {exc}",
                code="KLINE_ERROR",
            ) from exc

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Retrieve historical aggregate trades from Binance REST API."""
        if self.exchange in ("bitfinex", "coinbase", "poloniex"):
            raise BridgeError(
                f"{self.exchange.capitalize()} exchange does not support tick history; only bars are supported",
                code="UNSUPPORTED_OPERATION",
            )
        sym_clean = self._normalize_symbol(symbol)
        target_count = count or limit or 100
        req_limit = min(target_count, 1000)
        url = f"{self.base_url}{self.api_prefix}/aggTrades"
        params: dict[str, Any] = {
            "symbol": sym_clean,
            "limit": req_limit,
        }
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_ms = epoch_millis(s)
        end_ms = epoch_millis(e)
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
            ticks: list[MarketTick] = []
            for t in raw_trades:
                p = float(t.get("p") or 0.0)
                qty = float(t.get("q") or 0.0)
                t_ms = int(t.get("T") or 0)
                t_vol = int(qty) if qty >= 1.0 else (1 if qty > 0 else 0)
                ticks.append(
                    MarketTick(
                        time_msc=t_ms,
                        bid=p,
                        ask=p,
                        last=p,
                        volume=t_vol,
                        flags=0,
                        volume_real=qty,
                    )
                )
            ticks.sort(key=lambda item: item.time_msc)
            if count and len(ticks) > count:
                ticks = ticks[-count:]
            return ticks
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to retrieve trades from Binance for '{sym_clean}': {exc}",
                code="TRADES_ERROR",
            ) from exc


class BinanceClient(CryptoClient):
    """Binance cryptocurrency client."""

    def __init__(
        self,
        name: str = "Binance",
        default_market: str = "spot",
        venue: str | None = None,
        api_key: str | None = None,
        exchange: str = "binance",
    ) -> None:
        super().__init__(
            name=name,
            default_market=default_market,
            venue=venue,
            api_key=api_key,
            exchange=exchange,
        )


class BitfinexClient(CryptoClient):
    """Bitfinex cryptocurrency client."""

    def __init__(self, name: str = "Bitfinex") -> None:
        super().__init__(name=name, exchange="bitfinex")


class CoinbaseClient(CryptoClient):
    """Coinbase cryptocurrency client."""

    def __init__(self, name: str = "Coinbase") -> None:
        super().__init__(name=name, exchange="coinbase")


class PoloniexClient(CryptoClient):
    """Poloniex cryptocurrency client."""

    def __init__(self, name: str = "Poloniex") -> None:
        super().__init__(name=name, exchange="poloniex")


def create_adapter(context: Any | None = None) -> BinanceClient:
    """Factory creating configured BinanceClient adapter."""
    del context
    return BinanceClient()


def main() -> None:
    """Demonstrate executable usage of BinanceClient."""
    client = BinanceClient()
    symbols = client.get_symbols()
    logger.info("Binance symbols: %s", symbols[:3])
    client.disconnect()


if __name__ == "__main__":
    main()
