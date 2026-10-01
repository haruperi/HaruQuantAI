# ruff: noqa: INP001, PLR2004 -- singular namespace and source protocol constants
"""Owner-script crypto exchanges under host lifecycle and custody.

Description:
    Preserves six exchange adapters' symbols, request windows and candle fields.
    Uses injected sessions, host jobs and immutable source partitions.
Purpose:
    FEAT-DM-CRYPTO_ACQUISITION: Crypto source attached to Data Manager.
Key Capabilities:
    - FR-CRYPTO-ACQUIRE: Source exchange pagination; logs request completion.
    - FR-CRYPTO-PUBLISH: Immutable host publication; logs rows and partitions.
Python API Usage:
    contribution = await prepare(capabilities)
    catalog = await contribution.invoke("catalog", {})
CLI Usage:
    uv run pytest tests/plugin/DataSource/test_crypto.py --no-cov
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import enum
import re
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from typing import Any, cast, override

import httpx
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import HostCapabilities, JobAccess, MarketAccess
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.network import NetworkResult, SourceNetwork
from app.host.packages import PreparedContribution
from pydantic import Field, JsonValue, model_validator

logger = get_logger(__name__)

PLUGIN = {
    "id": "plugin.data_manager.crypto",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.network", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
    ],
}

TIMEFRAME_MILLIS: dict[str, int] = {
    "M1": 60 * 1000,
    "M3": 3 * 60 * 1000,
    "M5": 5 * 60 * 1000,
    "M15": 15 * 60 * 1000,
    "M30": 30 * 60 * 1000,
    "H1": 60 * 60 * 1000,
    "H2": 2 * 60 * 60 * 1000,
    "H3": 3 * 60 * 60 * 1000,
    "H4": 4 * 60 * 60 * 1000,
    "H6": 6 * 60 * 60 * 1000,
    "H8": 8 * 60 * 60 * 1000,
    "H12": 12 * 60 * 60 * 1000,
    "D1": 24 * 60 * 60 * 1000,
    "W1": 7 * 24 * 60 * 60 * 1000,
}


def get_timeframe_millis(tf: str) -> int:
    """Returns duration of standard timeframe in milliseconds."""
    clean_tf = tf.strip().upper()
    if clean_tf in TIMEFRAME_MILLIS:
        return TIMEFRAME_MILLIS[clean_tf]
    match = re.match("^([MHDW])(\\d+)$", clean_tf)
    if match:
        unit, count = (match.group(1), int(match.group(2)))
        if unit == "M":
            return count * 60 * 1000
        if unit == "H":
            return count * 3600 * 1000
        if unit == "D":
            return count * 86400 * 1000
        if unit == "W":
            return count * 7 * 86400 * 1000
    raise ValueError(f"Unrecognized timeframe string: '{tf}'")


@dataclasses.dataclass
class SymbolInfo:
    """Owner-script SymbolInfo behavior with explicit transport injection."""

    symbol: str
    exchange: str
    point_value: float = 1.0
    tick_size: float = 1e-08
    tick_step: float = 1e-08
    default_spread: float = 0.0
    default_slippage: float = 0.0
    date_from: int = 0
    price_precision: int = 8
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0
    description: str = "Crypto instrument"
    status: str = "TRADING"


class ExchangeType(str, enum.Enum):  # noqa: UP042 -- preserve source enum string behavior.
    """Supported owner-script exchange identities."""

    BINANCE = "Binance"
    BINANCE_COIN_M = "Binance Coin-M"
    BINANCE_USDT_M = "Binance USDT-M"
    BITFINEX = "Bitfinex"
    COINBASE_PRO = "Coinbase Pro"
    POLONIEX = "Poloniex"

    @classmethod
    def resolve(cls, value: str | ExchangeType) -> ExchangeType:  # noqa: PLR0911 -- source aliases.
        """Resolve source exchange names and aliases."""
        if isinstance(value, cls):
            return value
        val_str = value.value if isinstance(value, enum.Enum) else str(value)
        raw = val_str.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        raw = raw.removeprefix("exchangetype.")
        if raw in ("binance", "binancespot", "spot"):
            return cls.BINANCE
        if raw in ("binancecoinm", "coinm", "dapi", "binancedapi"):
            return cls.BINANCE_COIN_M
        if raw in ("binanceusdtm", "usdtm", "fapi", "binancefapi", "futures"):
            return cls.BINANCE_USDT_M
        if raw in ("bitfinex", "bfx"):
            return cls.BITFINEX
        if raw in ("coinbase", "coinbasepro", "cbp", "gdax"):
            return cls.COINBASE_PRO
        if raw in ("poloniex", "polo"):
            return cls.POLONIEX
        raise ValueError(
            f"Unsupported exchange '{value}'. Available: Binance, Binance Coin-M, "
            "Binance USDT-M, Bitfinex, Coinbase Pro, Poloniex."
        )


class BaseCryptoExchange:
    """Owner-script BaseCryptoExchange behavior with explicit transport injection."""

    def __init__(self, name: str, network: CryptoNetwork) -> None:
        self.name = name
        self.network = network
        self._available_symbols: list[str] | None = None

    def get_name(self) -> str:
        """Return this prepared exchange name."""
        return self.name

    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        raise NotImplementedError

    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        raise NotImplementedError

    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        raise NotImplementedError

    async def check_symbol_exists(self, symbol: str) -> bool:
        """Check the normalized symbol against the real exchange catalog."""
        syms = await self.get_symbols()
        clean = symbol.strip().upper()
        return clean in syms or clean.replace("-", "").replace("/", "").replace(
            "_", ""
        ) in [s.replace("-", "").replace("/", "").replace("_", "") for s in syms]

    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        raise NotImplementedError

    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        raise NotImplementedError


class BinanceExchange(BaseCryptoExchange):
    """Owner-script BinanceExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Binance", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return [
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H2",
            "H4",
            "H6",
            "H8",
            "H12",
            "D1",
        ]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return f"{count}m"
        if prefix == "H":
            return f"{count}h"
        if prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        try:
            url = "https://api.binance.com/api/v3/exchangeInfo"
            resp = await self.network.get(url, request_seconds=30)
            data = resp.json()
            symbols = [
                s["symbol"]
                for s in data.get("symbols", [])
                if s.get("status") == "TRADING"
            ]
        except ValueError, TypeError, KeyError, IndexError, httpx.HTTPError:
            url = "https://www.binance.com/api/v1/ticker/allBookTickers"
            resp = await self.network.get(url, request_seconds=30)
            data = resp.json()
            symbols = [s["symbol"] for s in data if "symbol" in s]
        self._available_symbols = sorted(set(symbols))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = (
            symbol.strip().upper().replace("-", "").replace("/", "").replace("_", "")
        )
        url = "https://api.binance.com/api/v3/exchangeInfo"
        try:
            resp = await self.network.get(
                url, params={"symbol": clean_sym}, request_seconds=15
            )
            data = resp.json()
            symbols = data.get("symbols", [])
            target = None
            for s in symbols:
                if s["symbol"].upper() == clean_sym:
                    target = s
                    break
            if target:
                tick_size = 1e-08
                tick_step = 1e-08
                for f in target.get("filters", []):
                    ftype = f.get("filterType", "")
                    if ftype.upper() == "PRICE_FILTER":
                        tick_size = float(f.get("tickSize", 1e-08))
                    elif ftype.upper() == "LOT_SIZE":
                        tick_step = float(f.get("stepSize", 1e-08))
                return SymbolInfo(
                    symbol=clean_sym,
                    exchange=self.name,
                    point_value=1.0,
                    tick_size=tick_size,
                    tick_step=tick_step,
                    default_spread=0.0,
                    default_slippage=0.0,
                    date_from=0,
                    description=(
                        f"{target.get('baseAsset', '')}/"
                        f"{target.get('quoteAsset', '')} on Binance"
                    ),
                    status=target.get("status", "TRADING"),
                )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Binance symbol info for %s: %s", clean_sym, e
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = (
            symbol.strip().upper().replace("-", "").replace("/", "").replace("_", "")
        )
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = "https://api.binance.com/api/v3/klines"
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        req_count = 0
        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1000,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = await self.network.get(base_url, params=params, request_seconds=30)
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for row in data:
                b_time = int(row[0])
                if b_time > end_ms:
                    break
                all_bars.append(
                    {
                        "DateTime": b_time,
                        "Open": float(row[1]),
                        "High": float(row[2]),
                        "Low": float(row[3]),
                        "Close": float(row[4]),
                        "Volume": float(row[5]),
                    }
                )
            last_time = int(data[-1][0])
            curr_start = last_time + tf_ms
            req_count += 1
            if req_count % 25 == 0:
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(0.05)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
            if len(data) < 1000:
                break
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


class BinanceCoinMExchange(BaseCryptoExchange):
    """Owner-script BinanceCoinMExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Binance Coin-M", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return [
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H2",
            "H4",
            "H6",
            "H8",
            "H12",
            "D1",
        ]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return f"{count}m"
        if prefix == "H":
            return f"{count}h"
        if prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://dapi.binance.com/dapi/v1/exchangeInfo"
        resp = await self.network.get(url, request_seconds=30)
        data = resp.json()
        symbols = [
            s["symbol"]
            for s in data.get("symbols", [])
            if s.get("contractStatus") == "TRADING"
        ]
        self._available_symbols = sorted(set(symbols))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = symbol.strip().upper()
        url = "https://dapi.binance.com/dapi/v1/exchangeInfo"
        try:
            resp = await self.network.get(url, request_seconds=30)
            data = resp.json()
            for s in data.get("symbols", []):
                if s["symbol"].upper() == clean_sym:
                    tick_size = 1e-08
                    tick_step = 1e-08
                    for f in s.get("filters", []):
                        ftype = f.get("filterType", "")
                        if ftype.upper() == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize", 1e-08))
                        elif ftype.upper() == "LOT_SIZE":
                            tick_step = float(f.get("stepSize", 1e-08))
                    return SymbolInfo(
                        symbol=clean_sym,
                        exchange=self.name,
                        point_value=1.0,
                        tick_size=tick_size,
                        tick_step=tick_step,
                        default_spread=0.0,
                        default_slippage=0.0,
                        date_from=0,
                        description=f"{s.get('pair', '')} Coin-M Futures",
                        status=s.get("contractStatus", "TRADING"),
                    )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Binance Coin-M symbol info for %s: %s",
                clean_sym,
                e,
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = symbol.strip().upper()
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = "https://dapi.binance.com/dapi/v1/klines"
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        req_count = 0
        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1500,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = await self.network.get(base_url, params=params, request_seconds=30)
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for row in data:
                b_time = int(row[0])
                if b_time > end_ms:
                    break
                all_bars.append(
                    {
                        "DateTime": b_time,
                        "Open": float(row[1]),
                        "High": float(row[2]),
                        "Low": float(row[3]),
                        "Close": float(row[4]),
                        "Volume": float(row[5]),
                    }
                )
            last_time = int(data[-1][0])
            curr_start = last_time + tf_ms
            req_count += 1
            if req_count % 25 == 0:
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(0.05)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
            if len(data) < 1500:
                break
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


class BinanceUsdtMExchange(BaseCryptoExchange):
    """Owner-script BinanceUsdtMExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Binance USDT-M", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return [
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H2",
            "H4",
            "H6",
            "H8",
            "H12",
            "D1",
        ]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return f"{count}m"
        if prefix == "H":
            return f"{count}h"
        if prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        resp = await self.network.get(url, request_seconds=30)
        data = resp.json()
        symbols = [
            s["symbol"] for s in data.get("symbols", []) if s.get("status") == "TRADING"
        ]
        self._available_symbols = sorted(set(symbols))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = symbol.strip().upper()
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        try:
            resp = await self.network.get(url, request_seconds=30)
            data = resp.json()
            for s in data.get("symbols", []):
                if s["symbol"].upper() == clean_sym:
                    tick_size = 1e-08
                    tick_step = 1e-08
                    for f in s.get("filters", []):
                        ftype = f.get("filterType", "")
                        if ftype.upper() == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize", 1e-08))
                        elif ftype.upper() == "LOT_SIZE":
                            tick_step = float(f.get("stepSize", 1e-08))
                    return SymbolInfo(
                        symbol=clean_sym,
                        exchange=self.name,
                        point_value=1.0,
                        tick_size=tick_size,
                        tick_step=tick_step,
                        default_spread=0.0,
                        default_slippage=0.0,
                        date_from=0,
                        description=f"{s.get('pair', '')} USDT-M Futures",
                        status=s.get("status", "TRADING"),
                    )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Binance USDT-M symbol info for %s: %s",
                clean_sym,
                e,
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = symbol.strip().upper()
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = "https://fapi.binance.com/fapi/v1/klines"
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        req_count = 0
        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1500,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = await self.network.get(base_url, params=params, request_seconds=30)
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for row in data:
                b_time = int(row[0])
                if b_time > end_ms:
                    break
                all_bars.append(
                    {
                        "DateTime": b_time,
                        "Open": float(row[1]),
                        "High": float(row[2]),
                        "Low": float(row[3]),
                        "Close": float(row[4]),
                        "Volume": float(row[5]),
                    }
                )
            last_time = int(data[-1][0])
            curr_start = last_time + tf_ms
            req_count += 1
            if req_count % 25 == 0:
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(0.05)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
            if len(data) < 1500:
                break
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


class BitfinexExchange(BaseCryptoExchange):
    """Owner-script BitfinexExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Bitfinex", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return ["M1", "M5", "M15", "M30", "H1", "H3", "H6", "H12", "D1"]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return f"{count}m"
        if prefix == "H":
            return f"{count}h"
        if prefix == "D":
            return f"{count}D"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.bitfinex.com/v2/conf/pub:list:pair:exchange"
        resp = await self.network.get(url, request_seconds=30)
        data = resp.json()
        pairs = (
            data[0]
            if isinstance(data, list) and data and isinstance(data[0], list)
            else []
        )
        self._available_symbols = sorted(set(pairs))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = (
            symbol.strip().upper().replace(":", "").replace("/", "").replace("-", "")
        )
        lookup_sym = clean_sym.removeprefix("T")
        url = "https://api.bitfinex.com/v1/symbols_details"
        try:
            resp = await self.network.get(url, request_seconds=30)
            data = resp.json()
            for s in data:
                if s.get("pair", "").upper() == lookup_sym.lower():
                    price_precision = int(s.get("price_precision", 8))
                    tick = 10.0 ** (-price_precision)
                    return SymbolInfo(
                        symbol=clean_sym,
                        exchange=self.name,
                        point_value=1.0,
                        tick_size=tick,
                        tick_step=tick,
                        default_spread=0.0,
                        default_slippage=0.0,
                        price_precision=price_precision,
                        description=f"{lookup_sym} on Bitfinex",
                    )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Bitfinex symbol info for %s: %s", clean_sym, e
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = (
            symbol.strip().upper().replace(":", "").replace("/", "").replace("-", "")
        )
        prefix_sym = clean_sym if clean_sym.startswith("t") else f"t{clean_sym}"
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = (
            f"https://api.bitfinex.com/v2/candles/trade:{interval}:{prefix_sym}/hist"
        )
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        while curr_start <= end_ms:
            params = {"limit": 10000, "sort": 1, "start": curr_start, "end": end_ms}
            resp = await self.network.get(base_url, params=params, request_seconds=30)
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for row in data:
                b_time = int(row[0])
                if b_time > end_ms:
                    break
                all_bars.append(
                    {
                        "DateTime": b_time,
                        "Open": float(row[1]),
                        "High": float(row[3]),
                        "Low": float(row[4]),
                        "Close": float(row[2]),
                        "Volume": float(row[5]),
                    }
                )
            last_time = int(data[-1][0])
            curr_start = last_time + tf_ms
            await asyncio.sleep(2.0)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
            if len(data) < 10000:
                break
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


class CoinbaseProExchange(BaseCryptoExchange):
    """Owner-script CoinbaseProExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Coinbase Pro", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return ["M1", "M5", "M15", "H1", "H6", "D1"]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return str(count * 60)
        if prefix == "H":
            return str(count * 3600)
        if prefix == "D":
            return "86400"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.exchange.coinbase.com/products"
        resp = await self.network.get(url, request_seconds=30)
        data = resp.json()
        symbols = [p["id"] for p in data if not p.get("trading_disabled", False)]
        self._available_symbols = sorted(set(symbols))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = symbol.strip().upper()
        if "-" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:3]}-{clean_sym[3:]}"
        url = f"https://api.exchange.coinbase.com/products/{clean_sym}"
        try:
            resp = await self.network.get(url, request_seconds=15)
            data = resp.json()
            quote_increment = float(data.get("quote_increment", 1e-08))
            return SymbolInfo(
                symbol=clean_sym,
                exchange=self.name,
                point_value=1.0,
                tick_size=quote_increment,
                tick_step=quote_increment,
                default_spread=0.0,
                default_slippage=0.0,
                description=f"{data.get('display_name', clean_sym)} on Coinbase",
                status=data.get("status", "online"),
            )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Coinbase symbol info for %s: %s", clean_sym, e
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = symbol.strip().upper()
        if "-" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-3]}-{clean_sym[-3:]}"
        granularity = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = f"https://api.exchange.coinbase.com/products/{clean_sym}/candles"
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        while curr_start <= end_ms:
            chunk_end = min(curr_start + 299 * tf_ms, end_ms)
            start_iso = datetime.datetime.fromtimestamp(
                curr_start / 1000.0, tz=datetime.UTC
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_iso = datetime.datetime.fromtimestamp(
                chunk_end / 1000.0, tz=datetime.UTC
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            params = {"granularity": granularity, "start": start_iso, "end": end_iso}
            try:
                resp = await self.network.get(
                    base_url, params=params, request_seconds=30
                )
                data = resp.json()
            except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
                logger.warning(
                    "Coinbase request failed for %s (%s -> %s): %s",
                    clean_sym,
                    start_iso,
                    end_iso,
                    e,
                )
                self.network.failed_requests += 1
                curr_start = chunk_end + tf_ms
                await asyncio.sleep(0.5)
                continue
            if isinstance(data, list) and data:
                for row in reversed(data):
                    b_time = int(row[0]) * 1000
                    if b_time > end_ms:
                        continue
                    all_bars.append(
                        {
                            "DateTime": b_time,
                            "Open": float(row[3]),
                            "High": float(row[2]),
                            "Low": float(row[1]),
                            "Close": float(row[4]),
                            "Volume": float(row[5]),
                        }
                    )
            curr_start = chunk_end + tf_ms
            await asyncio.sleep(0.333)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


class PoloniexExchange(BaseCryptoExchange):
    """Owner-script PoloniexExchange behavior with explicit transport injection."""

    def __init__(self, network: CryptoNetwork) -> None:
        super().__init__("Poloniex", network)

    @override
    def available_timeframes(self) -> list[str]:
        """Return the source exchange intervals."""
        return ["M5", "M15", "M30", "H2", "H4", "D1"]

    @override
    def convert_timeframe(self, tf: str) -> str:
        """Convert a source timeframe into exchange notation."""
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            ) from None
        if prefix == "M":
            return f"MINUTE_{count}"
        if prefix == "H":
            return f"HOUR_{count}"
        if prefix == "D":
            return f"DAY_{count}"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    @override
    async def get_symbols(self) -> list[str]:
        """Retrieve and cache the exchange symbol listing."""
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.poloniex.com/markets"
        resp = await self.network.get(url, request_seconds=30)
        data = resp.json()
        symbols = [m["symbol"] for m in data if "symbol" in m]
        self._available_symbols = sorted(set(symbols))
        return self._available_symbols

    @override
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Read source metadata, retaining the source fallback policy."""
        clean_sym = symbol.strip().upper()
        if "_" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-4]}_{clean_sym[-4:]}"
        url = f"https://api.poloniex.com/markets/{clean_sym}"
        try:
            resp = await self.network.get(url, request_seconds=15)
            data = resp.json()
            trade_limit = (
                data[0].get("symbolTradeLimit", {})
                if isinstance(data, list) and data
                else {}
            )
            price_scale = int(trade_limit.get("priceScale", 8))
            tick = 10.0 ** (-price_scale)
            return SymbolInfo(
                symbol=clean_sym,
                exchange=self.name,
                point_value=1.0,
                tick_size=tick,
                tick_step=tick,
                default_spread=0.0,
                default_slippage=0.0,
                price_precision=price_scale,
                description=f"{clean_sym} on Poloniex",
            )
        except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
            logger.warning(
                "Error while fetching Poloniex symbol info for %s: %s", clean_sym, e
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    @override
    async def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Retrieve source candle windows with exchange field ordering."""
        clean_sym = symbol.strip().upper()
        if "_" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-4]}_{clean_sym[-4:]}"
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)
        base_url = f"https://api.poloniex.com/markets/{clean_sym}/candles"
        curr_start = start_ms
        all_bars: list[dict[str, Any]] = []
        while curr_start <= end_ms:
            chunk_end = min(curr_start + 500 * tf_ms, end_ms)
            params = {
                "limit": 500,
                "interval": interval,
                "startTime": curr_start,
                "endTime": chunk_end,
            }
            try:
                resp = await self.network.get(
                    base_url, params=params, request_seconds=30
                )
                data = resp.json()
            except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError) as e:
                logger.warning(
                    "Poloniex request failed for %s (%s -> %s): %s",
                    clean_sym,
                    curr_start,
                    chunk_end,
                    e,
                )
                self.network.failed_requests += 1
                curr_start = chunk_end + tf_ms
                await asyncio.sleep(0.5)
                continue
            if isinstance(data, list) and data:
                for row in data:
                    b_time = int(row[12]) if len(row) > 12 else int(row[9])
                    if b_time > end_ms:
                        continue
                    all_bars.append(
                        {
                            "DateTime": b_time,
                            "Open": float(row[2]),
                            "High": float(row[1]),
                            "Low": float(row[0]),
                            "Close": float(row[3]),
                            "Volume": float(row[4]),
                        }
                    )
            curr_start = chunk_end + tf_ms
            await asyncio.sleep(0.25)
            if progress_callback:
                progress_callback(curr_start, end_ms, len(all_bars))
        if not all_bars:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(all_bars)
        df["DateTime"] = pd.to_datetime(df["DateTime"], unit="ms", utc=True)
        df.drop_duplicates(subset=["DateTime"], inplace=True)
        df.sort_values(by="DateTime", inplace=True)
        return df.reset_index(drop=True)


def normalize_symbol_for_exchange(  # noqa: C901, PLR0911 -- source notation policies.
    symbol: str, exchange: str | ExchangeType
) -> str:
    """Adapts user-entered symbol to target exchange's native ticker notation."""
    etype = (
        ExchangeType.resolve(str(exchange)) if isinstance(exchange, str) else exchange
    )
    raw = symbol.strip().upper()
    if etype in (ExchangeType.BINANCE, ExchangeType.BINANCE_USDT_M):
        return raw.replace("-", "").replace("/", "").replace("_", "")
    if etype == ExchangeType.BINANCE_COIN_M:
        if "_" not in raw and (not raw.endswith("PERP")):
            return f"{raw.replace('-', '').replace('/', '')}_PERP"
        return raw.replace("-", "").replace("/", "")
    if etype == ExchangeType.BITFINEX:
        return raw.replace("-", "").replace("/", "").replace("_", "")
    if etype == ExchangeType.COINBASE_PRO:
        if "-" not in raw:
            for quote in ("USDT", "USDC", "USD", "EUR", "GBP", "BTC", "ETH"):
                if raw.endswith(quote) and len(raw) > len(quote):
                    base = raw[: -len(quote)]
                    return f"{base}-{quote}"
        return raw.replace("/", "-").replace("_", "-")
    if etype == ExchangeType.POLONIEX:
        if "_" not in raw:
            for quote in ("USDT", "USDC", "USD", "BTC", "ETH", "TRX"):
                if raw.endswith(quote) and len(raw) > len(quote):
                    base = raw[: -len(quote)]
                    return f"{base}_{quote}"
        return raw.replace("/", "_").replace("-", "_")
    return raw


def clean_symbol(symbol: str) -> str:
    """Returns canonical sanitized alphanumeric symbol string for storage."""
    return (
        symbol.strip()
        .upper()
        .replace("-", "")
        .replace("/", "")
        .replace("_", "")
        .replace(":", "")
    )


@dataclasses.dataclass
class CryptoNetwork:
    """Prepared exchange transport with explicit bounded retries."""

    session: SourceNetwork
    failed_requests: int = 0

    @staticmethod
    def retry_seconds(value: str) -> float:
        """Interpret the source adapter's Retry-After seconds or HTTP date."""
        if re.fullmatch(r"\s*[0-9]+\s*", value):
            return float(value)
        when = parsedate_to_datetime(value)
        if when.tzinfo is None:
            when = when.replace(tzinfo=datetime.UTC)
        return max(0.0, (when - datetime.datetime.now(datetime.UTC)).total_seconds())

    async def adapter_get(
        self, url: str, params: dict[str, Any] | None, request_seconds: int
    ) -> NetworkResult:
        """Preserve five inner adapter retries and urllib3's backoff sequence."""
        for attempt in range(6):
            try:
                response = await self.session.get(
                    url, params=params, request_seconds=request_seconds
                )
            except httpx.HTTPError:
                if attempt == 5:
                    raise
                delay = 0.0 if attempt == 0 else 1.5 * 2**attempt
            else:
                retryable = response.status in (429, 500, 502, 503, 504) or (
                    response.status == 413 and response.retry_after is not None
                )
                if not retryable or attempt == 5:
                    return response
                delay = 0.0 if attempt == 0 else 1.5 * 2**attempt
                if response.retry_after:
                    delay = self.retry_seconds(response.retry_after) or delay
            logger.warning(
                "Crypto adapter retry: attempt=%d delay=%g", attempt + 1, delay
            )
            if delay:
                await asyncio.sleep(delay)
        raise RuntimeError("Crypto adapter retry exhaustion")

    async def get(
        self, url: str, params: dict[str, Any] | None = None, request_seconds: int = 30
    ) -> NetworkResult:
        """Retrieve JSON bytes through the host-owned session."""
        delay = 1.0
        for attempt in range(6):
            try:
                response = await self.adapter_get(url, params, request_seconds)
                if response.status == 429:
                    wait = (
                        float(response.retry_after) if response.retry_after else delay
                    )
                    logger.warning("Crypto rate limit: delay=%g", wait)
                    await asyncio.sleep(wait)
                    delay *= 2
                    continue
                if response.status < 400:
                    return response
                if attempt == 5:
                    break
                logger.warning(
                    "Crypto HTTP retry: status=%d attempt=%d",
                    response.status,
                    attempt + 1,
                )
            except httpx.HTTPError:
                if attempt == 5:
                    break
                logger.warning("Crypto transport retry: attempt=%d", attempt + 1)
            await asyncio.sleep(delay)
            delay *= 2
        self.failed_requests += 1
        raise ValueError("Crypto provider request failed after bounded retries")


class CryptoDefinition(Document):
    """Explicit exchange, source symbol and interval identity."""

    exchange: ExchangeType = ExchangeType.BINANCE
    symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_:/.-]+$")
    timeframe: str = Field(default="M1", pattern=r"^[MHDW][1-9][0-9]*$")
    postfix: str = Field(default="", max_length=40, pattern=r"^[A-Za-z0-9_.-]*$")


class CryptoDownload(Document):
    """Finite date-range acquisition for a stored source identity."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    date_from: datetime.date
    date_to: datetime.date
    overwrite: bool = False

    @model_validator(mode="after")
    def dates(self) -> CryptoDownload:
        """Reject inverted or future source windows."""
        if (
            self.date_from > self.date_to
            or self.date_to > datetime.datetime.now(datetime.UTC).date()
        ):
            raise ValueError("Invalid historical crypto date range")
        return self


@dataclasses.dataclass
class CryptoRuntime:
    """Prepared exchange drivers with host-owned jobs and durable custody."""

    market: MarketAccess
    jobs: JobAccess
    drivers: dict[ExchangeType, BaseCryptoExchange]
    progress: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)

    async def acquire(self, request: CryptoDownload, progress: dict[str, Any]) -> None:
        """Retain source floating volume and yearly partition merge semantics."""
        record = self.market.source_definition(request.dataset_id)
        parameters = CryptoDefinition.model_validate(record["options"]["parameters"])
        driver = copy.copy(self.drivers[parameters.exchange])
        driver.network = CryptoNetwork(driver.network.session)
        start = int(
            datetime.datetime.combine(
                request.date_from, datetime.time(), datetime.UTC
            ).timestamp()
            * 1000
        )
        end = (
            int(
                datetime.datetime.combine(
                    request.date_to + datetime.timedelta(days=1),
                    datetime.time(),
                    datetime.UTC,
                ).timestamp()
                * 1000
            )
            - 1
        )
        initial_failures = driver.network.failed_requests

        def report(current: int, total: int, rows: int) -> None:
            if rows > 500_000:
                raise ValueError("Choose a smaller acquisition date range")
            progress.update(
                current_ms=current,
                end_ms=total,
                rows=rows,
                progress=min(1.0, max(0.0, (current - start) / (end - start + 1))),
            )
            logger.info(
                "Crypto acquisition progress: id=%s rows=%d", request.dataset_id, rows
            )

        frame = await driver.download_candles(
            normalize_symbol_for_exchange(parameters.symbol, parameters.exchange),
            parameters.timeframe,
            start,
            end,
            report,
        )
        if frame.empty:
            raise ValueError("Crypto source returned no rows for this range")
        revisions = {
            row["period"]: row
            for row in self.market.source_partitions(request.dataset_id)
        }
        for year, incoming in frame.groupby(frame["DateTime"].dt.year):
            await asyncio.sleep(0)
            period = str(year)
            prior = revisions.get(period)
            merged = incoming
            if prior:
                old = self.market.read_source_partition(
                    request.dataset_id, period
                ).to_pandas()
                merged = (
                    pd.concat([old, incoming])
                    .drop_duplicates(
                        subset=["DateTime"],
                        keep="last" if request.overwrite else "first",
                    )
                    .sort_values("DateTime")
                )
            schema = pa.schema(
                [
                    pa.field("DateTime", pa.timestamp("ms", tz="UTC")),
                    *[
                        pa.field(name, pa.float64())
                        for name in ("Open", "High", "Low", "Close", "Volume")
                    ],
                ]
            )
            table = pa.Table.from_pandas(merged, schema=schema, preserve_index=False)
            self.market.publish_source(
                request.dataset_id,
                period,
                table,
                expected_revision=prior["revision"] if prior else 0,
            )
            progress["published_partitions"] += 1
        if driver.network.failed_requests > initial_failures:
            raise ValueError("Partial crypto acquisition: some source requests failed")
        logger.info(
            "Crypto acquisition published: id=%s rows=%d",
            request.dataset_id,
            len(frame),
        )

    async def invoke(self, operation: str, payload: JsonValue) -> JsonValue:
        """Dispatch source-owned validation, catalog queries and genuine jobs."""
        logger.info("Crypto operation: %s", operation)
        values = payload if isinstance(payload, dict) else {}
        if operation == "catalog":
            ready = self.market.source_available()
            return cast(
                "JsonValue",
                {
                    "available": ready,
                    "reason": ""
                    if ready
                    else "Script-backed catalog migration is required",
                    "datasets": self.market.source_definitions() if ready else [],
                    "schema": CryptoDefinition.model_json_schema(),
                    "exchanges": [
                        {
                            "name": kind.value,
                            "timeframes": driver.available_timeframes(),
                        }
                        for kind, driver in self.drivers.items()
                    ],
                },
            )
        if operation == "symbols":
            exchange = ExchangeType.resolve(str(values.get("exchange", "Binance")))
            return cast(
                "JsonValue", {"symbols": await self.drivers[exchange].get_symbols()}
            )
        if operation == "add":
            definition = CryptoDefinition.model_validate(values)
            driver = self.drivers[definition.exchange]
            if definition.timeframe not in driver.available_timeframes():
                raise ValueError("Timeframe unsupported by this exchange")
            symbol = normalize_symbol_for_exchange(
                definition.symbol, definition.exchange
            )
            if not await driver.check_symbol_exists(symbol):
                raise ValueError("Symbol unavailable on selected exchange")
            info = await driver.get_symbol_info(symbol)
            dataset_id = self.market.register_source(
                source="Crypto",
                symbol=clean_symbol(symbol) + definition.postfix,
                underlying=symbol,
                instrument=clean_symbol(symbol),
                timeframe=definition.timeframe,
                broker=definition.exchange.value,
                options={
                    "parameters": definition.model_dump(mode="json"),
                    "metadata": dataclasses.asdict(info),
                },
            )
            return {"id": dataset_id}
        if operation == "download.start":
            request = CryptoDownload.model_validate(values)
            self.market.source_definition(request.dataset_id)
            progress: dict[str, Any] = {
                "rows": 0,
                "published_partitions": 0,
                "current_ms": 0,
                "end_ms": 0,
            }

            async def run() -> None:
                await self.acquire(request, progress)

            job = self.jobs.submit(Budget(1, 256 * 1024 * 1024, 3600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("download.status", "download.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "download.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        raise ValueError("Unknown crypto operation")

    async def close(self) -> None:
        """Stop owned jobs and close all private exchange sessions."""
        await self.jobs.close()
        for driver in self.drivers.values():
            await driver.network.session.close()
        logger.info("Crypto source closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Create source-local drivers without import-time registration or networking."""
    if context.market_data is None or context.jobs is None or context.network is None:
        raise ValueError("Crypto requires market data, jobs and network capabilities")
    definitions: tuple[
        tuple[
            ExchangeType, Callable[[CryptoNetwork], BaseCryptoExchange], tuple[str, ...]
        ],
        ...,
    ] = (
        (
            ExchangeType.BINANCE,
            BinanceExchange,
            ("https://api.binance.com", "https://www.binance.com"),
        ),
        (
            ExchangeType.BINANCE_COIN_M,
            BinanceCoinMExchange,
            ("https://dapi.binance.com",),
        ),
        (
            ExchangeType.BINANCE_USDT_M,
            BinanceUsdtMExchange,
            ("https://fapi.binance.com",),
        ),
        (ExchangeType.BITFINEX, BitfinexExchange, ("https://api.bitfinex.com",)),
        (
            ExchangeType.COINBASE_PRO,
            CoinbaseProExchange,
            ("https://api.exchange.coinbase.com",),
        ),
        (ExchangeType.POLONIEX, PoloniexExchange, ("https://api.poloniex.com",)),
    )
    drivers = {
        kind: factory(CryptoNetwork(context.network.source_session(origins)))
        for kind, factory, origins in definitions
    }
    runtime = CryptoRuntime(context.market_data, context.jobs, drivers)
    return PreparedContribution(
        (
            "catalog",
            "symbols",
            "add",
            "download.start",
            "download.status",
            "download.cancel",
        ),
        runtime.invoke,
        runtime.close,
    )
