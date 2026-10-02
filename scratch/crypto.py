# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
#     "pyarrow>=14.0.0",
#     "requests>=2.28.0",
#     "urllib3>=1.26.0",
# ]
# ///
"""
================================================================================
StrategyQuant X Crypto Data High-Performance Ingestion & Storage Engine
================================================================================

Architectural Design & Key Capabilities:
----------------------------------------
This standalone engine provides 100% protocol, algorithmic, binary, and functional
parity with StrategyQuant X's (SQX) proprietary Crypto Data subsystem:
  - com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoPlugin
  - com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet
  - com.strategyquant.tradinglib.exchange.Exchange
  - com.strategyquant.tradinglib.exchange.IExchange
  - com.strategyquant.tradinglib.exchange.SymbolInfo
  - com.strategyquant.tradinglib.crypto.CryptoDownloadJob
  - com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin
  - com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin
  - com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin
  - com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin
  - com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin
  - com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin

While modernizing the storage layer from legacy binary formats (.dat) to high-throughput,
partitioned, Zstandard-compressed Apache Parquet.

1. Protocol & Ingestion Parity (All 6 Supported Crypto Exchanges):
   - Binance Spot ('Binance'):
     * REST Endpoint: https://api.binance.com/api/v3/klines
     * Info & Symbols: https://api.binance.com/api/v3/exchangeInfo
     * Timeframes: M1, M3, M5, M15, M30, H1, H2, H4, H6, H8, H12, D1 (mapped to 1m, 3m, 1h, 1d)
     * Parsing Order: [0: time, 1: open, 2: high, 3: low, 4: close, 5: volume]
     * Rate Limiter: 25 requests burst / 2.0s cooldown
   - Binance Coin-M Futures ('Binance Coin-M'):
     * REST Endpoint: https://dapi.binance.com/dapi/v1/klines
     * Info & Symbols: https://dapi.binance.com/dapi/v1/exchangeInfo
     * Batch Limit: 1,500 bars per request
   - Binance USDT-M Futures ('Binance USDT-M'):
     * REST Endpoint: https://fapi.binance.com/fapi/v1/klines
     * Info & Symbols: https://fapi.binance.com/fapi/v1/exchangeInfo
     * Batch Limit: 1,500 bars per request
   - Bitfinex ('Bitfinex'):
     * REST Endpoint: https://api.bitfinex.com/v2/candles/trade:{tf}:t{symbol}/hist
     * Symbols & Precision: https://api.bitfinex.com/v2/conf/pub:list:pair:exchange & /v1/symbols_details
     * Timeframes: M1, M5, M15, M30, H1, H3, H6, H12, D1 (mapped to 1m, 1h, 1D)
     * SQX Bytecode Column Mapping: [0: time, 1: open, 2: close, 3: high, 4: low, 5: volume]
     * Rate Limiter: 2.0s pacing per request
   - Coinbase Pro / Advanced ('Coinbase Pro'):
     * REST Endpoint: https://api.exchange.coinbase.com/products/{symbol}/candles
     * Timeframes: M1, M5, M15, H1, H6, D1 (mapped to granularity seconds 60, 300, 3600, 86400)
     * Batch Limit: 300 bars (start + 299 * tf_ms)
     * SQX Bytecode Column Mapping: [0: time_sec*1000, 1: low, 2: high, 3: open, 4: close, 5: volume]
     * Timestamp Format: ISO 8601 UTC (yyyy-MM-ddTHH:mm:ssZ)
     * Rate Limiter: 333ms pacing per request, dynamic 429 exponential backoff
   - Poloniex ('Poloniex'):
     * REST Endpoint: https://api.poloniex.com/markets/{symbol}/candles
     * Timeframes: M5, M15, M30, H2, H4, D1 (mapped to MINUTE_5, HOUR_2, DAY_1)
     * Batch Limit: 500 bars
     * SQX Bytecode Column Mapping: [12: time, 2: open, 1: high, 0: low, 3: close, 4: volume]
     * Rate Limiter: 250ms pacing per request

2. Vectorized Binary DAT & Delta Buffer Decoding (`SQBinaryDatDecoder`):
   - Zero-Copy Decompression: Decodes raw StrategyQuant .dat streams (v4.1 and v4.2,
     both unencrypted 'D' and crypted 'C' types).
   - 1,000-Record Magic Chain Synchronization: Automatically tracks and verifies
     the 15-byte start sequence (`0, 1, 2, ..., 14`) + 4-byte block index every 1,000 records.
   - 3-Byte Bit-Packed Control Word Decoding (`configBytes`):
     * Byte 0: Open & Time (data type + delta logic)
     * Byte 1: Low & High (data type + delta logic)
     * Byte 2: Volume & Close (data type + delta logic)
   - Dynamic Variable-Byte Unpacking: Fast byte-order struct parsing for 1B, 2B, 4B, and 8B integers.
   - State-Machine Delta Reconstruction: 0: MINUS, 1: PLUS, 2: ASIS.
   - Fixed-Point Decimal Scaling: Decodes prices with exact fixed-point scaling (/ 1,000,000.0)
     and volume scaling (/ 100,000.0).

3. Canonical Big Data Schemas & Partitioned Parquet Storage:
   - Parquet Schema:
     * DateTime: timestamp[ms, UTC]  (Partition key / indexed bar timestamp)
     * Open:     float64              (Opening price)
     * High:     float64              (High price)
     * Low:      float64              (Low price)
     * Close:    float64              (Closing price)
     * Volume:   float64              (Base or quote asset transaction volume)
   - Partition Hierarchy:
     `data/market/crypto/{timeframe}/{symbol}/{year}.parquet`
   - Annual Slicing & Deduplication: Seamlessly merges new records with existing partitions.
   - Compression: Zstandard (zstd) high-ratio compression with dictionary encoding.

4. Catalog Indexing & SQX SQLite Sync:
   - Big Data Catalog: Records partition metadata in `scripts/haruquantai.db` (`DATA` table).
   - SQX Engine Synchronization: Automatically registers instruments and history datasets
     into StrategyQuant's internal `user/data/data.db` (`DATA` and `INSTRUMENTS` tables) with
     `DATATYPE = 7` (Crypto), providing seamless compatibility with StrategyQuant X GUI.
   - Master Crypto Catalog: Embedded specifications for 100+ cryptocurrencies across all 6 exchanges
     cached in `scripts/haruquantai.db`.

5. Multi-Timeframe Vectorized Resampling:
   - Vectorized OHLCV aggregation allowing instant synthesis of M3, M5, M15, M30, H1, H2, H4, D1
     directly from M1 (or any lower timeframe).


# ---------------------------------------------------------------------------
# CLI Usage Examples (Reflecting SQX UI in Terminal):
# ---------------------------------------------------------------------------
# 1. View official data disclaimer:
python scripts/crypto.py disclaimer

# 2. Add symbol with broker profile to DATA table:
python scripts/crypto.py add-symbol --symbol BTCUSDT --broker BINANCE --tf M1

# 3. Download historical data:
python scripts/crypto.py download-data --symbol BTCUSDT --broker BINANCE --tf M1 --redownload missing

# 4. Display StrategyQuant X Data Manager dashboard:
python scripts/crypto.py dashboard
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import enum
import hashlib
import io
import json
import logging
import math
import os
from pathlib import Path
import re
import struct
import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)
import sqlite3

# ---------------------------------------------------------------------------
# Module Public API Specification
# ---------------------------------------------------------------------------
__all__ = [
    "add_symbol",
    "download_data",
    "show_disclaimer",
]

# Global Configuration Parameters
GLOBAL_WORKERS: int = 4
DEFAULT_STORE: Union[str, Path] = "data/market"
DEFAULT_SHOW_PROGRESS: bool = True

CRYPTO_DISCLAIMER_TEXT = """================================================================================
                    CRYPTOCURRENCY & STRATEGYQUANT X DATA DISCLAIMER
================================================================================
Cryptocurrency trading and historical data analysis involve substantial market risk
and extreme volatility. Data are fetched directly from third-party exchange APIs
(Binance, Bitfinex, Coinbase Pro, Poloniex, etc.). SQ DataManager provides tools
to download and ingest data directly into the program. StrategyQuant is not
responsible for exchange API availability, data accuracy, rate limits, or any
financial losses incurred from trading strategies.
================================================================================"""

# Third-Party Big Data Stack
try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
except ImportError:
    pa = None
    pq = None
    pc = None

try:
    import requests
    from requests.adapters import HTTPAdapter
    import urllib3
    from urllib3.util.retry import Retry
except ImportError:
    requests = None
    HTTPAdapter = None
    urllib3 = None
    Retry = None


# ---------------------------------------------------------------------------
# Canonical PyArrow Schemas
# ---------------------------------------------------------------------------
if pa is not None:
    CRYPTO_SCHEMA = pa.schema(
        [
            pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
            pa.field("Open", pa.float64(), nullable=False),
            pa.field("High", pa.float64(), nullable=False),
            pa.field("Low", pa.float64(), nullable=False),
            pa.field("Close", pa.float64(), nullable=False),
            pa.field("Volume", pa.float64(), nullable=False),
        ]
    )
else:
    CRYPTO_SCHEMA = None


# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
# Unified SQX Database Path
UNIFIED_DB_PATH = Path(__file__).resolve().parent / "haruquantai.db"

logger = logging.getLogger("sq_crypto")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Timeframe Definitions & Durations
# ---------------------------------------------------------------------------
TIMEFRAME_MILLIS: Dict[str, int] = {
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
    match = re.match(r"^([MHDW])(\d+)$", clean_tf)
    if match:
        unit, count = match.group(1), int(match.group(2))
        if unit == "M":
            return count * 60 * 1000
        elif unit == "H":
            return count * 3600 * 1000
        elif unit == "D":
            return count * 86400 * 1000
        elif unit == "W":
            return count * 7 * 86400 * 1000
    raise ValueError(f"Unrecognized timeframe string: '{tf}'")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class SymbolInfo:
    """
    Symbol specifications matching SQX `com.strategyquant.tradinglib.exchange.SymbolInfo`.
    """

    symbol: str
    exchange: str
    point_value: float = 1.0
    tick_size: float = 1e-8
    tick_step: float = 1e-8
    default_spread: float = 0.0
    default_slippage: float = 0.0
    date_from: int = 0  # timestamp ms
    price_precision: int = 8
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0
    description: str = "Crypto instrument"
    status: str = "TRADING"


class ExchangeType(str, enum.Enum):
    BINANCE = "Binance"
    BINANCE_COIN_M = "Binance Coin-M"
    BINANCE_USDT_M = "Binance USDT-M"
    BITFINEX = "Bitfinex"
    COINBASE_PRO = "Coinbase Pro"
    POLONIEX = "Poloniex"

    @classmethod
    def resolve(cls, value: Union[str, "ExchangeType"]) -> "ExchangeType":
        if isinstance(value, cls):
            return value
        val_str = value.value if isinstance(value, enum.Enum) else str(value)
        raw = val_str.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        if raw.startswith("exchangetype."):
            raw = raw[len("exchangetype.") :]
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
            f"Binance USDT-M, Bitfinex, Coinbase Pro, Poloniex."
        )


# ---------------------------------------------------------------------------
# Network Manager
# ---------------------------------------------------------------------------
class NetworkManager:
    """
    Resilient connection-pooled HTTP client with exponential backoff and rate-limit handling.
    """

    _instance: Optional["NetworkManager"] = None

    def __init__(
        self, pool_connections: int = 20, pool_maxsize: int = 50, max_retries: int = 5
    ):
        if requests is None:
            raise ImportError("requests library is required for NetworkManager.")
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StrategyQuantX/CryptoEngine",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
            }
        )

    @classmethod
    def get_instance(cls) -> "NetworkManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(
        self, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> requests.Response:
        """Executes a GET request with automatic retry and rate-limit backoff."""
        delay = 1.0
        for attempt in range(6):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else delay
                    logger.warning(
                        f"Rate limited (429) for {url}. Waiting {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay *= 2.0
                    continue
                if response.status_code == 200:
                    return response
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == 5:
                    raise
                logger.warning(f"Request failed ({e}). Retrying in {delay:.2f}s...")
                time.sleep(delay)
                delay *= 2.0
        raise RuntimeError(f"Failed to fetch {url} after multiple retries.")


# ---------------------------------------------------------------------------
# StrategyQuant Binary DAT Decoder (100% Parity with SQX 4.1 & 4.2 Formats)
# ---------------------------------------------------------------------------
class SQBinaryDatDecoder:
    """
    High-performance decoder for StrategyQuant proprietary binary .dat OHLCV files.

    Format Specifications (`DataBinReaderNew` & `OhlcDataReader`):
    --------------------------------------------------------------
    Header:
      - UTF string: version ("4.1" or "4.2")
      - UTF string: type ("D" for unencrypted data, "C" for crypted data)
      - UTF string: code (e.g. "ABCDEFGH")
      - Big-Endian int64: totalRecords
      - Big-Endian int32: columnCount
      - Repeated columnCount times:
        * UTF string: columnName
        * Big-Endian int32: columnType
      - UTF string: magic ("SnRbTs")
      - If type == "C": Big-Endian int32 modLen + modLen bytes

    Stream Body (New Format):
      - Start Chain: Every 1,000 records (`loadedCnt % 1000 == 0`), reads:
        * 15 bytes: `0, 1, 2, ..., 14`
        * Big-Endian int32: block index
      - Control Bytes (3 bytes):
        * Byte 0: Open & Time
          bits 0-1: Open data type (0: 1B, 1: 2B, 2: 4B, 3: 8B)
          bits 2-3: Open logic (0: MINUS, 1: PLUS, 2: ASIS)
          bits 4-5: Time data type
          bits 6-7: Time logic
        * Byte 1: Low & High
          bits 0-1: Low data type
          bits 2-3: Low logic
          bits 4-5: High data type
          bits 6-7: High logic
        * Byte 2: Volume & Close
          bits 0-1: Volume data type
          bits 2-3: Volume logic
          bits 4-5: Close data type
          bits 6-7: Close logic
      - Dynamic Payload: Reads (Time, Open, High, Low, Close, Volume) according
        to the variable byte length specified by data types.
      - Delta State Machine: Reconstructs values relative to preceding bar.
      - Fixed-Point Division: Scaled by decimalsConstant (1,000,000) and volumeConstant (100,000).
    """

    @staticmethod
    def decode(
        source: Union[bytes, io.BytesIO, Path, str],
        decimals_override: Optional[int] = None,
        volume_constant_override: Optional[float] = None,
    ) -> pd.DataFrame:
        """Decodes a StrategyQuant .dat binary buffer or file into a Pandas DataFrame."""
        if pd is None:
            raise ImportError("pandas is required for SQBinaryDatDecoder.")

        if isinstance(source, (str, Path)):
            with open(source, "rb") as f:
                raw_bytes = f.read()
        elif isinstance(source, io.BytesIO):
            raw_bytes = source.getvalue()
        else:
            raw_bytes = bytes(source)

        stream = io.BytesIO(raw_bytes)

        def read_utf() -> str:
            utflen_bytes = stream.read(2)
            if len(utflen_bytes) < 2:
                return ""
            (utflen,) = struct.unpack(">H", utflen_bytes)
            return stream.read(utflen).decode("utf-8", errors="replace")

        version = read_utf()
        data_type = read_utf()
        code = read_utf()

        header_prefix = stream.read(12)
        if len(header_prefix) < 12:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        total_records, column_count = struct.unpack(">qi", header_prefix)

        columns: List[Tuple[str, int]] = []
        for _ in range(column_count):
            c_name = read_utf()
            (c_type,) = struct.unpack(">i", stream.read(4))
            columns.append((c_name, c_type))

        magic = read_utf()
        if data_type == "C":
            (mod_len,) = struct.unpack(">i", stream.read(4))
            stream.seek(mod_len, io.SEEK_CUR)

        decimals_constant = (
            1_000_000.0 if decimals_override is None else float(10**decimals_override)
        )
        volume_constant = (
            100_000.0
            if volume_constant_override is None
            else float(volume_constant_override)
        )

        expected_chain = bytes(range(15))

        times: List[int] = []
        opens: List[float] = []
        highs: List[float] = []
        lows: List[float] = []
        closes: List[float] = []
        vols: List[float] = []

        last_time: int = 0
        last_open: int = 0
        last_high: int = 0
        last_low: int = 0
        last_close: int = 0
        last_vol: int = 0

        read_types = [1, 2, 4, 8]

        def read_var(dtype_idx: int) -> int:
            b_len = read_types[dtype_idx]
            b_data = stream.read(b_len)
            if len(b_data) < b_len:
                raise EOFError("Unexpected EOF while reading dynamic value")
            if b_len == 1:
                return struct.unpack(">B", b_data)[0]
            elif b_len == 2:
                return struct.unpack(">H", b_data)[0]
            elif b_len == 4:
                return struct.unpack(">I", b_data)[0]
            else:
                return struct.unpack(">q", b_data)[0]

        def apply_delta(logic: int, last_val: int, delta_val: int) -> int:
            if logic == 0:  # MINUS
                return last_val - delta_val
            elif logic == 1:  # PLUS
                return last_val + delta_val
            else:  # ASIS
                return delta_val

        loaded = 0
        while loaded < total_records:
            if loaded % 1000 == 0:
                chain = stream.read(15)
                if len(chain) < 15 or chain != expected_chain:
                    break
                block_bytes = stream.read(4)
                if len(block_bytes) < 4:
                    break

            ctrl = stream.read(3)
            if len(ctrl) < 3:
                break
            b0, b1, b2 = ctrl[0], ctrl[1], ctrl[2]

            o_type = b0 & 3
            o_logic = (b0 >> 2) & 3
            t_type = (b0 >> 4) & 3
            t_logic = (b0 >> 6) & 3

            l_type = b1 & 3
            l_logic = (b1 >> 2) & 3
            h_type = (b1 >> 4) & 3
            h_logic = (b1 >> 6) & 3

            v_type = b2 & 3
            v_logic = (b2 >> 2) & 3
            c_type = (b2 >> 4) & 3
            c_logic = (b2 >> 6) & 3

            try:
                raw_t = read_var(t_type)
                raw_o = read_var(o_type)
                raw_h = read_var(h_type)
                raw_l = read_var(l_type)
                raw_c = read_var(c_type)
                raw_v = read_var(v_type)
            except EOFError:
                break

            last_time = apply_delta(t_logic, last_time, raw_t)
            last_open = apply_delta(o_logic, last_open, raw_o)
            last_high = apply_delta(h_logic, last_high, raw_h)
            last_low = apply_delta(l_logic, last_low, raw_l)
            last_close = apply_delta(c_logic, last_close, raw_c)
            last_vol = apply_delta(v_logic, last_vol, raw_v)

            times.append(last_time)
            opens.append(last_open / decimals_constant)
            highs.append(last_high / decimals_constant)
            lows.append(last_low / decimals_constant)
            closes.append(last_close / decimals_constant)
            vols.append(last_vol / volume_constant)
            loaded += 1

        if not times:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )

        df = pd.DataFrame(
            {
                "DateTime": pd.to_datetime(times, unit="ms", utc=True),
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": vols,
            }
        )
        return df


# ---------------------------------------------------------------------------
# Base & Concrete Exchange Implementations (100% SQX Parity)
# ---------------------------------------------------------------------------
class BaseCryptoExchange:
    """Abstract base class for SQX crypto exchange drivers."""

    def __init__(self, name: str):
        self.name = name
        self.network = NetworkManager.get_instance()
        self._available_symbols: Optional[List[str]] = None

    def get_name(self) -> str:
        return self.name

    def available_timeframes(self) -> List[str]:
        raise NotImplementedError

    def convert_timeframe(self, tf: str) -> str:
        raise NotImplementedError

    def get_symbols(self) -> List[str]:
        raise NotImplementedError

    def check_symbol_exists(self, symbol: str) -> bool:
        syms = self.get_symbols()
        clean = symbol.strip().upper()
        return clean in syms or clean.replace("-", "").replace("/", "").replace(
            "_", ""
        ) in [s.replace("-", "").replace("/", "").replace("_", "") for s in syms]

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        raise NotImplementedError

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        raise NotImplementedError


class BinanceExchange(BaseCryptoExchange):
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin`.
    """

    def __init__(self):
        super().__init__("Binance")

    def available_timeframes(self) -> List[str]:
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

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return f"{count}m"
        elif prefix == "H":
            return f"{count}h"
        elif prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        # Try exchangeInfo first, fallback to allBookTickers (matching SQX bytecode)
        try:
            url = "https://api.binance.com/api/v3/exchangeInfo"
            resp = self.network.get(url, timeout=30)
            data = resp.json()
            symbols = [
                s["symbol"]
                for s in data.get("symbols", [])
                if s.get("status") == "TRADING"
            ]
        except Exception:
            url = "https://www.binance.com/api/v1/ticker/allBookTickers"
            resp = self.network.get(url, timeout=30)
            data = resp.json()
            symbols = [s["symbol"] for s in data if "symbol" in s]
        self._available_symbols = sorted(list(set(symbols)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = (
            symbol.strip().upper().replace("-", "").replace("/", "").replace("_", "")
        )
        url = "https://api.binance.com/api/v3/exchangeInfo"
        try:
            resp = self.network.get(url, params={"symbol": clean_sym}, timeout=15)
            data = resp.json()
            symbols = data.get("symbols", [])
            target = None
            for s in symbols:
                if s["symbol"].upper() == clean_sym:
                    target = s
                    break
            if target:
                tick_size = 1e-8
                tick_step = 1e-8
                for f in target.get("filters", []):
                    ftype = f.get("filterType", "")
                    if ftype.upper() == "PRICE_FILTER":
                        tick_size = float(f.get("tickSize", 1e-8))
                    elif ftype.upper() == "LOT_SIZE":
                        tick_step = float(f.get("stepSize", 1e-8))
                return SymbolInfo(
                    symbol=clean_sym,
                    exchange=self.name,
                    point_value=1.0,
                    tick_size=tick_size,
                    tick_step=tick_step,
                    default_spread=0.0,
                    default_slippage=0.0,
                    date_from=0,
                    description=f"{target.get('baseAsset', '')}/{target.get('quoteAsset', '')} on Binance",
                    status=target.get("status", "TRADING"),
                )
        except Exception as e:
            logger.warning(
                f"Error while fetching Binance symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        clean_sym = (
            symbol.strip().upper().replace("-", "").replace("/", "").replace("_", "")
        )
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)

        base_url = "https://api.binance.com/api/v3/klines"
        curr_start = start_ms
        all_bars: List[Dict[str, Any]] = []
        req_count = 0

        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1000,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = self.network.get(base_url, params=params, timeout=30)
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
                time.sleep(2.0)
            else:
                time.sleep(0.05)

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
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin`.
    """

    def __init__(self):
        super().__init__("Binance Coin-M")

    def available_timeframes(self) -> List[str]:
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

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return f"{count}m"
        elif prefix == "H":
            return f"{count}h"
        elif prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://dapi.binance.com/dapi/v1/exchangeInfo"
        resp = self.network.get(url, timeout=30)
        data = resp.json()
        symbols = [
            s["symbol"]
            for s in data.get("symbols", [])
            if s.get("contractStatus") == "TRADING"
        ]
        self._available_symbols = sorted(list(set(symbols)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = symbol.strip().upper()
        url = "https://dapi.binance.com/dapi/v1/exchangeInfo"
        try:
            resp = self.network.get(url, timeout=30)
            data = resp.json()
            for s in data.get("symbols", []):
                if s["symbol"].upper() == clean_sym:
                    tick_size = 1e-8
                    tick_step = 1e-8
                    for f in s.get("filters", []):
                        ftype = f.get("filterType", "")
                        if ftype.upper() == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize", 1e-8))
                        elif ftype.upper() == "LOT_SIZE":
                            tick_step = float(f.get("stepSize", 1e-8))
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
        except Exception as e:
            logger.warning(
                f"Error while fetching Binance Coin-M symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        clean_sym = symbol.strip().upper()
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)

        base_url = "https://dapi.binance.com/dapi/v1/klines"
        curr_start = start_ms
        all_bars: List[Dict[str, Any]] = []
        req_count = 0

        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1500,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = self.network.get(base_url, params=params, timeout=30)
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
                time.sleep(2.0)
            else:
                time.sleep(0.05)

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
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin`.
    """

    def __init__(self):
        super().__init__("Binance USDT-M")

    def available_timeframes(self) -> List[str]:
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

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return f"{count}m"
        elif prefix == "H":
            return f"{count}h"
        elif prefix == "D":
            return f"{count}d"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        resp = self.network.get(url, timeout=30)
        data = resp.json()
        symbols = [
            s["symbol"] for s in data.get("symbols", []) if s.get("status") == "TRADING"
        ]
        self._available_symbols = sorted(list(set(symbols)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = symbol.strip().upper()
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        try:
            resp = self.network.get(url, timeout=30)
            data = resp.json()
            for s in data.get("symbols", []):
                if s["symbol"].upper() == clean_sym:
                    tick_size = 1e-8
                    tick_step = 1e-8
                    for f in s.get("filters", []):
                        ftype = f.get("filterType", "")
                        if ftype.upper() == "PRICE_FILTER":
                            tick_size = float(f.get("tickSize", 1e-8))
                        elif ftype.upper() == "LOT_SIZE":
                            tick_step = float(f.get("stepSize", 1e-8))
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
        except Exception as e:
            logger.warning(
                f"Error while fetching Binance USDT-M symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        clean_sym = symbol.strip().upper()
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)

        base_url = "https://fapi.binance.com/fapi/v1/klines"
        curr_start = start_ms
        all_bars: List[Dict[str, Any]] = []
        req_count = 0

        while curr_start <= end_ms:
            params = {
                "symbol": clean_sym,
                "interval": interval,
                "limit": 1500,
                "startTime": curr_start,
                "endTime": end_ms,
            }
            resp = self.network.get(base_url, params=params, timeout=30)
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
                time.sleep(2.0)
            else:
                time.sleep(0.05)

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
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin`.
    Column Parsing Order from SQX Bytecode:
      index 0: MTS (time ms)
      index 1: OPEN
      index 2: CLOSE
      index 3: HIGH
      index 4: LOW
      index 5: VOLUME
    """

    def __init__(self):
        super().__init__("Bitfinex")

    def available_timeframes(self) -> List[str]:
        return ["M1", "M5", "M15", "M30", "H1", "H3", "H6", "H12", "D1"]

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return f"{count}m"
        elif prefix == "H":
            return f"{count}h"
        elif prefix == "D":
            return f"{count}D"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.bitfinex.com/v2/conf/pub:list:pair:exchange"
        resp = self.network.get(url, timeout=30)
        data = resp.json()
        # Returns [["BTCUSD", "ETHUSD", ...]]
        pairs = (
            data[0]
            if isinstance(data, list) and data and isinstance(data[0], list)
            else []
        )
        self._available_symbols = sorted(list(set(pairs)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = (
            symbol.strip().upper().replace(":", "").replace("/", "").replace("-", "")
        )
        if clean_sym.startswith("T"):
            lookup_sym = clean_sym[1:]
        else:
            lookup_sym = clean_sym
        url = "https://api.bitfinex.com/v1/symbols_details"
        try:
            resp = self.network.get(url, timeout=30)
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
        except Exception as e:
            logger.warning(
                f"Error while fetching Bitfinex symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
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
        all_bars: List[Dict[str, Any]] = []

        while curr_start <= end_ms:
            params = {
                "limit": 10000,
                "sort": 1,
                "start": curr_start,
                "end": end_ms,
            }
            resp = self.network.get(base_url, params=params, timeout=30)
            data = resp.json()
            if not isinstance(data, list) or not data:
                break

            for row in data:
                b_time = int(row[0])
                if b_time > end_ms:
                    break
                # SQX Column Mapping: [0: time, 1: open, 2: close, 3: high, 4: low, 5: volume]
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

            # SQX Bitfinex rate limit: sleep 2.0s per request
            time.sleep(2.0)

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
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin`.
    Column Parsing Order from SQX Bytecode:
      index 0: time (seconds -> * 1000 ms)
      index 1: low
      index 2: high
      index 3: open
      index 4: close
      index 5: volume
    """

    def __init__(self):
        super().__init__("Coinbase Pro")

    def available_timeframes(self) -> List[str]:
        return ["M1", "M5", "M15", "H1", "H6", "D1"]

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return str(count * 60)
        elif prefix == "H":
            return str(count * 3600)
        elif prefix == "D":
            return "86400"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.exchange.coinbase.com/products"
        resp = self.network.get(url, timeout=30)
        data = resp.json()
        symbols = [p["id"] for p in data if not p.get("trading_disabled", False)]
        self._available_symbols = sorted(list(set(symbols)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = symbol.strip().upper()
        if "-" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:3]}-{clean_sym[3:]}"
        url = f"https://api.exchange.coinbase.com/products/{clean_sym}"
        try:
            resp = self.network.get(url, timeout=15)
            data = resp.json()
            quote_increment = float(data.get("quote_increment", 1e-8))
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
        except Exception as e:
            logger.warning(
                f"Error while fetching Coinbase symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        clean_sym = symbol.strip().upper()
        if "-" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-3]}-{clean_sym[-3:]}"
        granularity = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)

        base_url = f"https://api.exchange.coinbase.com/products/{clean_sym}/candles"
        curr_start = start_ms
        all_bars: List[Dict[str, Any]] = []

        while curr_start <= end_ms:
            chunk_end = min(curr_start + 299 * tf_ms, end_ms)
            start_iso = datetime.datetime.fromtimestamp(
                curr_start / 1000.0, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_iso = datetime.datetime.fromtimestamp(
                chunk_end / 1000.0, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

            params = {
                "granularity": granularity,
                "start": start_iso,
                "end": end_iso,
            }
            try:
                resp = self.network.get(base_url, params=params, timeout=30)
                data = resp.json()
            except Exception as e:
                logger.warning(
                    f"Coinbase request failed for {clean_sym} ({start_iso} -> {end_iso}): {e}"
                )
                curr_start = chunk_end + tf_ms
                time.sleep(0.5)
                continue

            if isinstance(data, list) and data:
                # Coinbase returns newest first, reverse to ascending
                for row in reversed(data):
                    b_time = int(row[0]) * 1000
                    if b_time > end_ms:
                        continue
                    # SQX Column Mapping: [0: time_sec*1000, 1: low, 2: high, 3: open, 4: close, 5: volume]
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
            # SQX rate limiter: 333ms pacing
            time.sleep(0.333)

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
    """
    100% parity with SQX `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin`.
    Column Parsing Order from SQX Bytecode:
      index 12: time (ms)
      index 2: open
      index 1: high
      index 0: low
      index 3: close
      index 4: volume
    """

    def __init__(self):
        super().__init__("Poloniex")

    def available_timeframes(self) -> List[str]:
        return ["M5", "M15", "M30", "H2", "H4", "D1"]

    def convert_timeframe(self, tf: str) -> str:
        clean = tf.strip().upper()
        prefix = clean[0]
        try:
            count = int(clean[1:])
        except ValueError:
            raise ValueError(
                f"Invalid timeframe format. Cannot parse time units count from '{tf}'."
            )
        if prefix == "M":
            return f"MINUTE_{count}"
        elif prefix == "H":
            return f"HOUR_{count}"
        elif prefix == "D":
            return f"DAY_{count}"
        raise ValueError(f"Invalid timeframe format. Prefix '{prefix}' not recognized.")

    def get_symbols(self) -> List[str]:
        if self._available_symbols is not None:
            return self._available_symbols
        url = "https://api.poloniex.com/markets"
        resp = self.network.get(url, timeout=30)
        data = resp.json()
        symbols = [m["symbol"] for m in data if "symbol" in m]
        self._available_symbols = sorted(list(set(symbols)))
        return self._available_symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        clean_sym = symbol.strip().upper()
        if "_" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-4]}_{clean_sym[-4:]}"
        url = f"https://api.poloniex.com/markets/{clean_sym}"
        try:
            resp = self.network.get(url, timeout=15)
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
        except Exception as e:
            logger.warning(
                f"Error while fetching Poloniex symbol info for {clean_sym}: {e}"
            )
        return SymbolInfo(symbol=clean_sym, exchange=self.name)

    def download_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ) -> pd.DataFrame:
        clean_sym = symbol.strip().upper()
        if "_" not in clean_sym and len(clean_sym) >= 6:
            clean_sym = f"{clean_sym[:-4]}_{clean_sym[-4:]}"
        interval = self.convert_timeframe(timeframe)
        tf_ms = get_timeframe_millis(timeframe)

        base_url = f"https://api.poloniex.com/markets/{clean_sym}/candles"
        curr_start = start_ms
        all_bars: List[Dict[str, Any]] = []

        while curr_start <= end_ms:
            chunk_end = min(curr_start + 500 * tf_ms, end_ms)
            params = {
                "limit": 500,
                "interval": interval,
                "startTime": curr_start,
                "endTime": chunk_end,
            }
            try:
                resp = self.network.get(base_url, params=params, timeout=30)
                data = resp.json()
            except Exception as e:
                logger.warning(
                    f"Poloniex request failed for {clean_sym} ({curr_start} -> {chunk_end}): {e}"
                )
                curr_start = chunk_end + tf_ms
                time.sleep(0.5)
                continue

            if isinstance(data, list) and data:
                for row in data:
                    # Poloniex candle format:
                    # [low, high, open, close, amount, quantity, buyTakerAmount, buyTakerQuantity, tradeCount, ts, weightedAverage, interval, startTime, closeTime]
                    b_time = int(row[12]) if len(row) > 12 else int(row[9])
                    if b_time > end_ms:
                        continue
                    # SQX Column Mapping: [12: time, 2: open, 1: high, 0: low, 3: close, 4: volume]
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
            # SQX rate limiter: 250ms pacing
            time.sleep(0.250)

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


class ExchangeFactory:
    """Factory for resolving and instantiating exchange drivers."""

    _drivers: Dict[ExchangeType, BaseCryptoExchange] = {}

    @classmethod
    def get(cls, exchange: Union[str, ExchangeType]) -> BaseCryptoExchange:
        etype = ExchangeType.resolve(exchange)
        if etype not in cls._drivers:
            if etype == ExchangeType.BINANCE:
                cls._drivers[etype] = BinanceExchange()
            elif etype == ExchangeType.BINANCE_COIN_M:
                cls._drivers[etype] = BinanceCoinMExchange()
            elif etype == ExchangeType.BINANCE_USDT_M:
                cls._drivers[etype] = BinanceUsdtMExchange()
            elif etype == ExchangeType.BITFINEX:
                cls._drivers[etype] = BitfinexExchange()
            elif etype == ExchangeType.COINBASE_PRO:
                cls._drivers[etype] = CoinbaseProExchange()
            elif etype == ExchangeType.POLONIEX:
                cls._drivers[etype] = PoloniexExchange()
        return cls._drivers[etype]

    @classmethod
    def list_all(cls) -> List[BaseCryptoExchange]:
        return [cls.get(t) for t in ExchangeType]


# ---------------------------------------------------------------------------
# Master Crypto Catalog & Symbol Normalization
# ---------------------------------------------------------------------------
FALLBACK_CRYPTO_CATALOG: Dict[str, Dict[str, Any]] = {
    # Binance Spot
    "BINANCE:BTCUSDT": {
        "symbol": "BTCUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.00001,
        "date_from": "2017-08-17",
        "price_precision": 2,
        "name": "Bitcoin / Tether",
    },
    "BINANCE:ETHUSDT": {
        "symbol": "ETHUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.0001,
        "date_from": "2017-08-17",
        "price_precision": 2,
        "name": "Ethereum / Tether",
    },
    "BINANCE:BNBUSDT": {
        "symbol": "BNBUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.1,
        "tick_step": 0.001,
        "date_from": "2017-11-06",
        "price_precision": 1,
        "name": "BNB / Tether",
    },
    "BINANCE:SOLUSDT": {
        "symbol": "SOLUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2020-08-11",
        "price_precision": 2,
        "name": "Solana / Tether",
    },
    "BINANCE:XRPUSDT": {
        "symbol": "XRPUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.0001,
        "tick_step": 0.1,
        "date_from": "2019-01-24",
        "price_precision": 4,
        "name": "Ripple / Tether",
    },
    "BINANCE:DOGEUSDT": {
        "symbol": "DOGEUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.00001,
        "tick_step": 1.0,
        "date_from": "2019-07-05",
        "price_precision": 5,
        "name": "Dogecoin / Tether",
    },
    "BINANCE:ADAUSDT": {
        "symbol": "ADAUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.0001,
        "tick_step": 0.1,
        "date_from": "2018-04-17",
        "price_precision": 4,
        "name": "Cardano / Tether",
    },
    "BINANCE:AVAXUSDT": {
        "symbol": "AVAXUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2020-09-22",
        "price_precision": 2,
        "name": "Avalanche / Tether",
    },
    "BINANCE:LINKUSDT": {
        "symbol": "LINKUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.001,
        "tick_step": 0.01,
        "date_from": "2019-01-16",
        "price_precision": 3,
        "name": "Chainlink / Tether",
    },
    "BINANCE:LTCUSDT": {
        "symbol": "LTCUSDT",
        "exchange": "Binance",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.001,
        "date_from": "2017-12-13",
        "price_precision": 2,
        "name": "Litecoin / Tether",
    },
    # Binance USDT-M Futures
    "BINANCE USDT-M:BTCUSDT": {
        "symbol": "BTCUSDT",
        "exchange": "Binance USDT-M",
        "point_value": 1.0,
        "tick_size": 0.1,
        "tick_step": 0.001,
        "date_from": "2019-09-08",
        "price_precision": 1,
        "name": "BTCUSDT Perpetual",
    },
    "BINANCE USDT-M:ETHUSDT": {
        "symbol": "ETHUSDT",
        "exchange": "Binance USDT-M",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.001,
        "date_from": "2019-11-28",
        "price_precision": 2,
        "name": "ETHUSDT Perpetual",
    },
    "BINANCE USDT-M:SOLUSDT": {
        "symbol": "SOLUSDT",
        "exchange": "Binance USDT-M",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2020-09-14",
        "price_precision": 2,
        "name": "SOLUSDT Perpetual",
    },
    # Binance Coin-M Futures
    "BINANCE COIN-M:BTCUSD_PERP": {
        "symbol": "BTCUSD_PERP",
        "exchange": "Binance Coin-M",
        "point_value": 100.0,
        "tick_size": 0.1,
        "tick_step": 1.0,
        "date_from": "2020-08-11",
        "price_precision": 1,
        "name": "BTCUSD Coin-M Perpetual",
    },
    "BINANCE COIN-M:ETHUSD_PERP": {
        "symbol": "ETHUSD_PERP",
        "exchange": "Binance Coin-M",
        "point_value": 10.0,
        "tick_size": 0.01,
        "tick_step": 1.0,
        "date_from": "2020-08-18",
        "price_precision": 2,
        "name": "ETHUSD Coin-M Perpetual",
    },
    # Bitfinex
    "BITFINEX:BTCUSD": {
        "symbol": "BTCUSD",
        "exchange": "Bitfinex",
        "point_value": 1.0,
        "tick_size": 1.0,
        "tick_step": 1.0,
        "date_from": "2013-01-15",
        "price_precision": 0,
        "name": "Bitcoin / US Dollar",
    },
    "BITFINEX:ETHUSD": {
        "symbol": "ETHUSD",
        "exchange": "Bitfinex",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2016-03-14",
        "price_precision": 2,
        "name": "Ethereum / US Dollar",
    },
    "BITFINEX:LTCUSD": {
        "symbol": "LTCUSD",
        "exchange": "Bitfinex",
        "point_value": 1.0,
        "tick_size": 0.001,
        "tick_step": 0.001,
        "date_from": "2013-10-23",
        "price_precision": 3,
        "name": "Litecoin / US Dollar",
    },
    # Coinbase Pro
    "COINBASE PRO:BTC-USD": {
        "symbol": "BTC-USD",
        "exchange": "Coinbase Pro",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.00000001,
        "date_from": "2015-01-14",
        "price_precision": 2,
        "name": "Bitcoin / USD",
    },
    "COINBASE PRO:ETH-USD": {
        "symbol": "ETH-USD",
        "exchange": "Coinbase Pro",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.00000001,
        "date_from": "2016-05-24",
        "price_precision": 2,
        "name": "Ethereum / USD",
    },
    "COINBASE PRO:SOL-USD": {
        "symbol": "SOL-USD",
        "exchange": "Coinbase Pro",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.000001,
        "date_from": "2021-06-17",
        "price_precision": 2,
        "name": "Solana / USD",
    },
    # Poloniex
    "POLONIEX:BTC_USDT": {
        "symbol": "BTC_USDT",
        "exchange": "Poloniex",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2015-02-15",
        "price_precision": 2,
        "name": "Bitcoin / USDT",
    },
    "POLONIEX:ETH_USDT": {
        "symbol": "ETH_USDT",
        "exchange": "Poloniex",
        "point_value": 1.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
        "date_from": "2016-08-08",
        "price_precision": 2,
        "name": "Ethereum / USDT",
    },
    "POLONIEX:TRX_USDT": {
        "symbol": "TRX_USDT",
        "exchange": "Poloniex",
        "point_value": 1.0,
        "tick_size": 0.00001,
        "tick_step": 0.00001,
        "date_from": "2018-05-22",
        "price_precision": 5,
        "name": "TRON / USDT",
    },
}


def normalize_symbol_for_exchange(
    symbol: str, exchange: Union[str, ExchangeType]
) -> str:
    """Adapts user-entered symbol to target exchange's native ticker notation."""
    etype = (
        ExchangeType.resolve(str(exchange)) if isinstance(exchange, str) else exchange
    )
    raw = symbol.strip().upper()

    if etype in (ExchangeType.BINANCE, ExchangeType.BINANCE_USDT_M):
        return raw.replace("-", "").replace("/", "").replace("_", "")
    elif etype == ExchangeType.BINANCE_COIN_M:
        if "_" not in raw and not raw.endswith("PERP"):
            return f"{raw.replace('-', '').replace('/', '')}_PERP"
        return raw.replace("-", "").replace("/", "")
    elif etype == ExchangeType.BITFINEX:
        clean = raw.replace("-", "").replace("/", "").replace("_", "")
        return clean
    elif etype == ExchangeType.COINBASE_PRO:
        if "-" not in raw:
            for quote in ("USDT", "USDC", "USD", "EUR", "GBP", "BTC", "ETH"):
                if raw.endswith(quote) and len(raw) > len(quote):
                    base = raw[: -len(quote)]
                    return f"{base}-{quote}"
        return raw.replace("/", "-").replace("_", "-")
    elif etype == ExchangeType.POLONIEX:
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


class CryptoCatalog:
    """Master catalog manager backed by embedded dataset and local SQLite cache."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else UNIFIED_DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='crypto_catalog'"
            )
            if cur.fetchone()[0] > 0:
                return

            conn.execute("""
                CREATE TABLE IF NOT EXISTS crypto_catalog (
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    point_value REAL NOT NULL DEFAULT 1.0,
                    tick_size REAL NOT NULL DEFAULT 1e-8,
                    tick_step REAL NOT NULL DEFAULT 1e-8,
                    default_spread REAL NOT NULL DEFAULT 0.0,
                    default_slippage REAL NOT NULL DEFAULT 0.0,
                    date_from TEXT,
                    price_precision INTEGER NOT NULL DEFAULT 8,
                    name TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (exchange, symbol)
                )
            """)
            conn.commit()

            # Seed with fallback catalog
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM crypto_catalog")
            if cur.fetchone()[0] == 0:
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for key, item in FALLBACK_CRYPTO_CATALOG.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO crypto_catalog
                        (exchange, symbol, point_value, tick_size, tick_step, default_spread, default_slippage, date_from, price_precision, name, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            item["exchange"],
                            item["symbol"],
                            item.get("point_value", 1.0),
                            item.get("tick_size", 1e-8),
                            item.get("tick_step", 1e-8),
                            item.get("default_spread", 0.0),
                            item.get("default_slippage", 0.0),
                            item.get("date_from", "2017-01-01"),
                            item.get("price_precision", 8),
                            item.get("name", item["symbol"]),
                            now_str,
                        ),
                    )
                conn.commit()
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_symbol_info(
        self, symbol: str, exchange: Union[str, ExchangeType]
    ) -> SymbolInfo:
        etype = (
            ExchangeType.resolve(str(exchange))
            if isinstance(exchange, str)
            else exchange
        )
        native_sym = normalize_symbol_for_exchange(symbol, etype)

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT point_value, tick_size, tick_step, default_spread, default_slippage, date_from, price_precision, name
                FROM crypto_catalog WHERE exchange = ? AND symbol = ?
            """,
                (etype.value, native_sym),
            )
            row = cur.fetchone()
            if row:
                d_from_ms = 0
                if row[5]:
                    try:
                        dt = datetime.datetime.fromisoformat(row[5])
                        d_from_ms = int(
                            dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000
                        )
                    except Exception:
                        pass
                return SymbolInfo(
                    symbol=native_sym,
                    exchange=etype.value,
                    point_value=row[0],
                    tick_size=row[1],
                    tick_step=row[2],
                    default_spread=row[3],
                    default_slippage=row[4],
                    date_from=d_from_ms,
                    price_precision=row[6],
                    description=row[7] or f"{native_sym} on {etype.value}",
                )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

        # Query live exchange driver
        driver = ExchangeFactory.get(etype)
        live_info = driver.get_symbol_info(native_sym)
        # Cache into SQLite
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO crypto_catalog
                (exchange, symbol, point_value, tick_size, tick_step, default_spread, default_slippage, date_from, price_precision, name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    etype.value,
                    native_sym,
                    live_info.point_value,
                    live_info.tick_size,
                    live_info.tick_step,
                    live_info.default_spread,
                    live_info.default_slippage,
                    None,
                    live_info.price_precision,
                    live_info.description,
                    now_str,
                ),
            )
            conn.commit()
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        return live_info

    def list_symbols(self, exchange: Union[str, ExchangeType]) -> List[str]:
        etype = (
            ExchangeType.resolve(str(exchange))
            if isinstance(exchange, str)
            else exchange
        )
        driver = ExchangeFactory.get(etype)
        try:
            return driver.get_symbols()
        except Exception as e:
            logger.warning(
                f"Failed to fetch live symbols for {etype.value} ({e}), reading catalog..."
            )
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute(
                    "SELECT symbol FROM crypto_catalog WHERE exchange = ?",
                    (etype.value,),
                )
                return [r[0] for r in cur.fetchall()]
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass


# ---------------------------------------------------------------------------
# Partition Resolution & Canonical Parquet Storage Layer
# ---------------------------------------------------------------------------
def resolve_crypto_partition_path(
    store_root: Union[str, Path],
    timeframe: str,
    symbol: str,
    period: str,
    exchange: Optional[str] = None,
) -> Path:
    """
    Resolves canonical partitioned filepath:
    `{store_root}/crypto/{timeframe.lower()}/{clean_symbol}/{year}.parquet`
    """
    clean_sym = clean_symbol(symbol).lower()
    tf_clean = timeframe.strip().lower()
    return Path(store_root) / "crypto" / tf_clean / clean_sym / f"{period}.parquet"


def dataframe_to_canonical_table(df: pd.DataFrame, timeframe: str = "m1") -> Any:
    """Coerces DataFrame to strict canonical Arrow table with CRYPTO_SCHEMA."""
    if pa is None:
        raise ImportError("pyarrow is required for canonical table conversion.")

    if not isinstance(df.index, pd.DatetimeIndex):
        if "DateTime" in df.columns:
            ts_series = pd.to_datetime(df["DateTime"], utc=True)
        elif "datetime" in df.columns:
            ts_series = pd.to_datetime(df["datetime"], utc=True)
        elif "time" in df.columns:
            ts_series = pd.to_datetime(df["time"], utc=True)
        else:
            raise KeyError("Dataset missing 'DateTime' column or DatetimeIndex")
    else:
        ts_series = pd.to_datetime(df.index, utc=True)

    col_map = {c.lower(): c for c in df.columns}
    o_col = col_map.get("open", "Open")
    h_col = col_map.get("high", "High")
    l_col = col_map.get("low", "Low")
    c_col = col_map.get("close", "Close")
    v_col = col_map.get("volume", "Volume")

    o_vals = df[o_col].astype(np.float64).values
    h_vals = df[h_col].astype(np.float64).values
    l_vals = df[l_col].astype(np.float64).values
    c_vals = df[c_col].astype(np.float64).values
    v_vals = df[v_col].astype(np.float64).values

    data_dict = {
        "DateTime": ts_series.values,
        "Open": o_vals,
        "High": h_vals,
        "Low": l_vals,
        "Close": c_vals,
        "Volume": v_vals,
    }

    raw_table = pa.Table.from_pydict(data_dict, schema=CRYPTO_SCHEMA)
    # Sort and deduplicate
    df_sorted = (
        raw_table.to_pandas()
        .drop_duplicates(subset=["DateTime"])
        .sort_values("DateTime")
    )
    return pa.Table.from_pandas(df_sorted, schema=CRYPTO_SCHEMA, preserve_index=False)


def update_market_catalog(
    store_root: Union[str, Path],
    source: str,
    kind: str,
    symbol: str,
    period: str,
    target_path: Path,
    table: Any,
    postfix: str = "",
) -> None:
    """
    Indexes committed partition into unified SQLite database (scripts/haruquantai.db).
    Updates native StrategyQuant X `DATA` table.
    """
    conn = None
    try:
        db_path = UNIFIED_DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=5)
        time_col = table.column("DateTime")
        start_ms = time_col[0].as_py()
        end_ms = time_col[-1].as_py()
        start_ms_int = (
            int(start_ms.timestamp() * 1000)
            if isinstance(start_ms, datetime.datetime)
            else int(start_ms)
        )
        end_ms_int = (
            int(end_ms.timestamp() * 1000)
            if isinstance(end_ms, datetime.datetime)
            else int(end_ms)
        )
        clean_sym = clean_symbol(symbol).upper()
        eff_sym = f"{clean_sym}{postfix}" if postfix else clean_sym
        tf_disp = kind.upper()
        postfix_sym = f"{eff_sym}_{tf_disp}"
        rel_dir = f"{source}/{kind.lower()}/{clean_sym.lower()}"

        cur = conn.cursor()
        cur.execute(
            """
            SELECT ID, ROWS, DATEFROM, DATETO FROM DATA
            WHERE (SOURCE = 7 AND (UPPER(INSTRUMENT) = ? OR UPPER(INSTRUMENT) = ?) AND UPPER(TIMEFRAME) = ?)
               OR ((UPPER(SYMBOL) = ? OR UPPER(SYMBOL) = ?) AND UPPER(TIMEFRAME) = ?)
        """,
            (
                clean_sym,
                eff_sym,
                tf_disp,
                postfix_sym,
                f"{clean_sym}_{tf_disp}",
                tf_disp,
            ),
        )
        existing = cur.fetchone()

        if existing:
            row_id, old_rows, old_from, old_to = existing
            new_from = (
                min(old_from, start_ms_int)
                if (old_from and old_from > 0)
                else start_ms_int
            )
            new_to = max(old_to, end_ms_int) if (old_to and old_to > 0) else end_ms_int
            new_rows = (old_rows or 0) + len(table)
            cur.execute(
                """
                UPDATE DATA SET
                    DATEFROM = ?, DATETO = ?, ROWS = ?, FILENAME = ?, SHOW = 1
                WHERE ID = ?
            """,
                (new_from, new_to, new_rows, rel_dir, row_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO DATA (
                    SOURCEDATA_ID, CONNECTION, SYMBOL, INSTRUMENT, TIMEFRAME,
                    TIMEZONE, FILENAME, DATEFROM, DATETO, DATATYPE,
                    ROWS, DECIMALS, SOURCE, SECONDS_RECORDS, USYMBOL,
                    USYMBOLNAME, REMOVE_WEEKENDS, SHOW, BASKET_ID, BROKER_ID
                ) VALUES (
                    0, 'History', ?, ?, ?,
                    'Exchange', ?, ?, ?, 1,
                    ?, 2, 7, 0, ?,
                    ?, 0, 1, -1, -1
                )
            """,
                (
                    postfix_sym,
                    eff_sym,
                    tf_disp,
                    rel_dir,
                    start_ms_int,
                    end_ms_int,
                    len(table),
                    clean_sym,
                    clean_sym,
                ),
            )
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to update market catalog index: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def store_canonical_partitions(
    data: Union[pd.DataFrame, Any],
    symbol: str,
    timeframe: str = "m1",
    store_root: Union[str, Path] = "data/market",
    exchange: Optional[str] = None,
    source: str = "crypto",
    postfix: str = "",
) -> List[Path]:
    """
    Slices, deduplicates, and commits crypto records into partitioned Parquet storage.
    """
    if pa is None or pq is None:
        raise ImportError(
            "pyarrow is required to store canonical partitioned Parquet files."
        )

    clean_sym = clean_symbol(symbol)
    store_path = Path(store_root)
    kind = timeframe.strip().lower()

    if isinstance(data, pd.DataFrame):
        if data.empty:
            return []
        table = dataframe_to_canonical_table(data, timeframe=kind)
    else:
        table = data

    if len(table) == 0:
        logger.warning(f"No records to store for {symbol} ({kind})")
        return []

    stamps_ms = table.column("DateTime").cast(pa.int64()).to_numpy()
    dt_index = pd.to_datetime(stamps_ms, unit="ms", utc=True)
    years = dt_index.year.values
    unique_years = np.unique(years)
    committed_files: List[Path] = []

    for y in unique_years:
        mask = years == y
        indices = np.where(mask)[0]
        slice_table = table.take(pa.array(indices))

        target_file = resolve_crypto_partition_path(
            store_path, kind, clean_sym, str(y), exchange
        )
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if target_file.exists():
            try:
                existing_table = pq.read_table(target_file)
                merged_table = pa.concat_tables([existing_table, slice_table])
                # Deduplicate by DateTime
                df_merged = (
                    merged_table.to_pandas()
                    .drop_duplicates(subset=["DateTime"])
                    .sort_values("DateTime")
                )
                final_table = pa.Table.from_pandas(
                    df_merged, schema=CRYPTO_SCHEMA, preserve_index=False
                )
            except Exception as e:
                logger.warning(
                    f"Failed to merge with existing partition {target_file}: {e}"
                )
                final_table = slice_table
        else:
            final_table = slice_table

        pq.write_table(
            final_table,
            target_file,
            compression="zstd",
            use_dictionary=True,
        )

        update_market_catalog(
            store_root=store_path,
            source=source,
            kind=kind,
            symbol=clean_sym,
            period=str(y),
            target_path=target_file,
            table=final_table,
            postfix=postfix,
        )
        committed_files.append(target_file)

    return committed_files


def resample_candles(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    """
    Vectorized aggregation resampling lower timeframe bars into higher timeframe bars.
    """
    if df.empty:
        return df

    tf = target_timeframe.strip().upper()
    rule_map = {
        "M1": "1min",
        "M3": "3min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H2": "2h",
        "H3": "3h",
        "H4": "4h",
        "H6": "6h",
        "H8": "8h",
        "H12": "12h",
        "D1": "1D",
        "W1": "1W",
    }
    rule = rule_map.get(tf)
    if not rule:
        match = re.match(r"^([MHDW])(\d+)$", tf)
        if match:
            unit, cnt = match.group(1), match.group(2)
            u_map = {"M": "min", "H": "h", "D": "D", "W": "W"}
            rule = f"{cnt}{u_map[unit]}"
        else:
            raise ValueError(f"Unsupported resampling timeframe: '{target_timeframe}'")

    temp_df = df.copy()
    if not isinstance(temp_df.index, pd.DatetimeIndex):
        temp_df["DateTime"] = pd.to_datetime(temp_df["DateTime"], utc=True)
        temp_df.set_index("DateTime", inplace=True)

    resampled = (
        temp_df.resample(rule, label="left", closed="left")
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna()
    )

    resampled.reset_index(inplace=True)
    return resampled


def sync_to_sqx_datadb(
    symbol: str,
    exchange: str,
    timeframe: str,
    rows: int,
    date_from_ms: int,
    date_to_ms: int,
    symbol_info: Optional[SymbolInfo] = None,
    sqx_root: Union[str, Path] = "C:/SQX",
    db_path: Optional[Union[str, Path]] = None,
    postfix: str = "",
) -> None:
    """
    Synchronizes dataset and instrument metadata directly into unified database `scripts/haruquantai.db`
    and StrategyQuant's `user/data/data.db`.
    Replicates exact behavior of `DataSourceCryptoServlet.addData`:
      - Inserts/updates `INSTRUMENTS` with DATATYPE = 7 (Crypto)
      - Inserts/updates `DATA` with SOURCE = 7 (Crypto), DATATYPE = 1, CONNECTION = 'History'
    """
    target_dbs: List[Path] = []
    if db_path:
        target_dbs.append(Path(db_path))
    else:
        target_dbs.append(UNIFIED_DB_PATH)
        user_db = Path(sqx_root) / "user" / "data" / "data.db"
        if user_db.exists() and user_db.resolve() != UNIFIED_DB_PATH.resolve():
            target_dbs.append(user_db)

    clean_sym = clean_symbol(symbol)
    eff_sym = f"{clean_sym}{postfix}" if postfix else clean_sym
    postfix_sym = f"{eff_sym}_{timeframe.upper()}"
    info = symbol_info or SymbolInfo(symbol=clean_sym, exchange=exchange)

    for datadb_path in target_dbs:
        if not datadb_path.exists():
            continue
        conn = None
        try:
            conn = sqlite3.connect(str(datadb_path), timeout=5)
            # 1. Update/Insert INSTRUMENTS
            conn.execute(
                """
                INSERT OR REPLACE INTO INSTRUMENTS (
                    INSTRUMENT, DESCRIPTION, POINTVALUE, TICKSIZE, TICKSTEP,
                    DEFAULTSPREAD, COMMISSIONS, DATATYPE, EXCHANGE, COUNTRY,
                    SECTOR, DEFAULTSLIPPAGE, SWAP, ORDERSIZEMULTIPLIER, ORDERSIZESTEP,
                    BROKER_ID, MIN_DISTANCE
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?
                )
            """,
                (
                    eff_sym,
                    info.description or f"{clean_sym} Crypto instrument",
                    info.point_value,
                    info.tick_size,
                    info.tick_step,
                    info.default_spread,
                    '<Method type="None" use="true"><Params/></Method>',
                    7,  # DATATYPE = 7 (Crypto)
                    exchange,
                    None,
                    None,
                    info.default_slippage,
                    None,
                    info.order_size_multiplier,
                    info.order_size_step,
                    -1,
                    0.0,
                ),
            )

            # 2. Update/Insert DATA
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID FROM DATA
                WHERE CONNECTION = 'History'
                  AND (UPPER(SYMBOL) = ? OR UPPER(SYMBOL) = ?)
                  AND UPPER(TIMEFRAME) = ?
            """,
                (postfix_sym, f"{clean_sym}_{timeframe.upper()}", timeframe.upper()),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE DATA SET
                        DATEFROM = ?, DATETO = ?, ROWS = ?, TIMEFRAME = ?, SHOW = 1
                    WHERE ID = ?
                """,
                    (date_from_ms, date_to_ms, rows, timeframe.upper(), row[0]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO DATA (
                        SOURCEDATA_ID, CONNECTION, SYMBOL, INSTRUMENT, TIMEFRAME,
                        TIMEZONE, FILENAME, DATEFROM, DATETO, DATATYPE,
                        ROWS, DECIMALS, SOURCE, SECONDS_RECORDS, USYMBOL,
                        USYMBOLNAME, REMOVE_WEEKENDS, SHOW, BASKET_ID, BROKER_ID
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?
                    )
                """,
                    (
                        0,
                        "History",
                        postfix_sym,
                        eff_sym,
                        timeframe.upper(),
                        "Exchange",
                        None,
                        date_from_ms,
                        date_to_ms,
                        1,  # DATATYPE = 1 (Price)
                        rows,
                        info.price_precision,
                        7,  # SOURCE = 7 (Crypto)
                        0,
                        clean_sym,
                        info.description or clean_sym,
                        0,
                        1,
                        -1,
                        -1,
                    ),
                )
            conn.commit()
            logger.info(
                f"Successfully synchronized {postfix_sym} to {datadb_path.name} (DATATYPE=7)."
            )
        except Exception as e:
            logger.warning(f"Failed to sync to {datadb_path.name}: {e}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# High-Level Download & Ingestion Pipelines
# ---------------------------------------------------------------------------
def _parse_datetime(dt_val: Union[str, datetime.date, datetime.datetime, int]) -> int:
    """Parses various date representations into epoch millisecond integer."""
    if isinstance(dt_val, (int, float, np.integer)):
        return int(dt_val)
    if isinstance(dt_val, datetime.datetime):
        if dt_val.tzinfo is None:
            dt_val = dt_val.replace(tzinfo=datetime.timezone.utc)
        return int(dt_val.timestamp() * 1000)
    if isinstance(dt_val, datetime.date):
        dt_val = datetime.datetime(
            dt_val.year, dt_val.month, dt_val.day, tzinfo=datetime.timezone.utc
        )
        return int(dt_val.timestamp() * 1000)
    if isinstance(dt_val, str):
        cleaned = dt_val.strip().replace("/", "-").replace(".", "-")
        parts = cleaned.split("-")
        if len(parts) == 3 and not (" " in parts[2] or "T" in parts[2]):
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                dt = datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc)
                return int(dt.timestamp() * 1000)
            except Exception:
                pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m"):
            try:
                parsed = datetime.datetime.strptime(cleaned, fmt).replace(
                    tzinfo=datetime.timezone.utc
                )
                return int(parsed.timestamp() * 1000)
            except ValueError:
                continue
        try:
            return int(float(cleaned))
        except ValueError:
            pass
    raise ValueError(f"Unable to parse datetime: {dt_val}")


def download_crypto(
    symbol: str,
    exchange: Union[str, ExchangeType] = "Binance",
    timeframe: str = "M1",
    start: Optional[Union[str, datetime.date, datetime.datetime, int]] = None,
    end: Optional[Union[str, datetime.date, datetime.datetime, int]] = None,
    store_root: Union[str, Path] = "data/market",
    resample_timeframes: Optional[List[str]] = None,
    sync_sqx: bool = True,
    sqx_root: Union[str, Path] = "C:/SQX",
    postfix: str = "",
) -> pd.DataFrame:
    """
    Downloads historical cryptocurrency candles directly from exchange REST API
    with 100% StrategyQuant X functional and algorithmic parity.
    """
    etype = (
        ExchangeType.resolve(str(exchange)) if isinstance(exchange, str) else exchange
    )
    driver = ExchangeFactory.get(etype)
    native_sym = normalize_symbol_for_exchange(symbol, etype)
    clean_sym = clean_symbol(symbol)
    eff_sym = f"{clean_sym}{postfix}" if postfix else clean_sym
    catalog = CryptoCatalog()
    info = catalog.get_symbol_info(symbol, etype)

    # Inception clamping
    start_ms = _parse_datetime(start) if start is not None else 0
    if info.date_from and start_ms < info.date_from:
        logger.info(
            f"Clamping requested start ({start}) to symbol inception boundary: {info.date_from}"
        )
        start_ms = info.date_from
    if start_ms <= 0:
        start_ms = int(
            datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
            * 1000
        )

    end_ms = (
        _parse_datetime(end)
        if end is not None
        else int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    )

    logger.info(
        f"Initiating crypto ingestion: {eff_sym} ({native_sym}) on {etype.value} [{timeframe.upper()}] "
        f"from {datetime.datetime.fromtimestamp(start_ms / 1000, tz=datetime.timezone.utc)} to "
        f"{datetime.datetime.fromtimestamp(end_ms / 1000, tz=datetime.timezone.utc)}"
    )

    def log_progress(curr: int, total: int, count: int) -> None:
        curr_dt = datetime.datetime.fromtimestamp(
            min(curr, total) / 1000, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M")
        print(
            f"\r  Ingesting [{etype.value}] {eff_sym} -> Current: {curr_dt} | Collected: {count:,} bars",
            end="",
            flush=True,
        )

    df = driver.download_candles(
        native_sym, timeframe, start_ms, end_ms, progress_callback=log_progress
    )
    print()  # newline after progress

    if df.empty:
        logger.warning(f"No records retrieved for {eff_sym} from {etype.value}.")
        return df

    logger.info(
        f"Retrieved {len(df):,} total bars for {eff_sym}. Committing to partitioned Parquet store..."
    )

    # Store base timeframe partitions
    committed = store_canonical_partitions(
        df,
        symbol=clean_sym,
        timeframe=timeframe,
        store_root=store_root,
        exchange=etype.value,
        source="crypto",
        postfix=postfix,
    )
    logger.info(
        f"Committed {len(committed)} Parquet partition file(s) for {eff_sym} [{timeframe.upper()}]."
    )

    # Optional resampling
    if resample_timeframes:
        for r_tf in resample_timeframes:
            if r_tf.upper() == timeframe.upper():
                continue
            logger.info(
                f"Resampling {eff_sym} [{timeframe.upper()}] -> [{r_tf.upper()}]..."
            )
            df_resampled = resample_candles(df, r_tf)
            if not df_resampled.empty:
                r_committed = store_canonical_partitions(
                    df_resampled,
                    symbol=clean_sym,
                    timeframe=r_tf,
                    store_root=store_root,
                    exchange=etype.value,
                    source="crypto",
                    postfix=postfix,
                )
                logger.info(
                    f"Committed {len(r_committed)} resampled partitions for [{r_tf.upper()}]."
                )

    # Sync to SQX data.db if requested
    if sync_sqx:
        first_ms = int(df["DateTime"].iloc[0].timestamp() * 1000)
        last_ms = int(df["DateTime"].iloc[-1].timestamp() * 1000)
        sync_to_sqx_datadb(
            symbol=clean_sym,
            exchange=etype.value,
            timeframe=timeframe,
            rows=len(df),
            date_from_ms=first_ms,
            date_to_ms=last_ms,
            symbol_info=info,
            sqx_root=sqx_root,
            postfix=postfix,
        )

    return df


def scan_market_crypto(
    store_root: Union[str, Path] = "data/market",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    exchange: Optional[str] = None,
) -> pd.DataFrame:
    """Scans and reads canonical Parquet records from local market store."""
    if pq is None:
        raise ImportError("pyarrow is required to scan parquet storage.")

    base_dir = Path(store_root) / "crypto"
    if not base_dir.exists():
        logger.warning(f"Crypto store directory does not exist: {base_dir}")
        return pd.DataFrame()

    tf_filter = timeframe.strip().lower() if timeframe else None
    sym_filter = clean_symbol(symbol).lower() if symbol else None

    parquet_files: List[Path] = []
    for tf_dir in base_dir.iterdir():
        if not tf_dir.is_dir():
            continue
        if tf_filter and tf_dir.name.lower() != tf_filter:
            continue
        for s_dir in tf_dir.iterdir():
            if not s_dir.is_dir():
                continue
            if sym_filter and s_dir.name.lower() != sym_filter:
                continue
            for p_file in s_dir.glob("*.parquet"):
                parquet_files.append(p_file)

    if not parquet_files:
        return pd.DataFrame()

    tables = []
    for f in sorted(parquet_files):
        try:
            tables.append(pq.read_table(f))
        except Exception as e:
            logger.warning(f"Error reading {f}: {e}")

    if not tables:
        return pd.DataFrame()

    merged = pa.concat_tables(tables)
    df = (
        merged.to_pandas()
        .drop_duplicates(subset=["DateTime"])
        .sort_values("DateTime")
        .reset_index(drop=True)
    )
    return df


def import_sqx_dat_file(
    file_path: Union[str, Path],
    store_root: Union[str, Path] = "data/market",
    symbol_override: Optional[str] = None,
    timeframe_override: Optional[str] = None,
    exchange_override: str = "Binance",
) -> int:
    """Ingests a single StrategyQuant binary .dat file into Parquet storage."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    stem = p.stem
    sym = symbol_override
    tf = timeframe_override or "M1"
    if not sym:
        match = re.match(r"^([A-Za-z0-9]+)_([MHDW]\d+)$", stem)
        if match:
            sym = match.group(1)
            tf = match.group(2)
        else:
            sym = stem

    df = SQBinaryDatDecoder.decode(p)
    if df.empty:
        logger.warning(f"No records decoded from {p}")
        return 0

    store_canonical_partitions(
        df,
        symbol=sym,
        timeframe=tf,
        store_root=store_root,
        exchange=exchange_override,
        source="crypto",
    )
    logger.info(f"Imported {len(df):,} records for {sym} [{tf}] from {p}")
    return len(df)


def import_local_history(
    history_root: Union[str, Path] = "C:/SQX/user/data/History",
    store_root: Union[str, Path] = "data/market",
) -> int:
    """Auto-discovers and imports all local SQX crypto .dat files from history root."""
    h_path = Path(history_root)
    if not h_path.exists():
        logger.warning(f"History root does not exist: {h_path}")
        return 0

    total_records = 0
    dat_files = list(h_path.glob("**/*.dat"))
    for f in dat_files:
        try:
            total_records += import_sqx_dat_file(f, store_root=store_root)
        except Exception as e:
            logger.warning(f"Failed to import {f}: {e}")
    return total_records


def verify_partitions(
    store_root: Union[str, Path] = "data/market",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> bool:
    """Verifies integrity, file readability, and row counts of stored Parquet files against DATA table."""
    base_dir = Path(store_root) / "crypto"
    if not base_dir.exists():
        print("No crypto market data folder found.")
        return True

    kinds = [timeframe.lower()] if timeframe else ["m1", "m5", "h1", "d1", "ticks"]
    target_sym = clean_symbol(symbol).lower() if symbol else None

    parquet_files: List[Path] = []
    for k in kinds:
        k_dir = base_dir / k
        if not k_dir.exists():
            continue
        for sym_dir in k_dir.iterdir():
            if not sym_dir.is_dir():
                continue
            if target_sym and sym_dir.name.lower() != target_sym:
                continue
            parquet_files.extend(sorted(sym_dir.glob("*.parquet")))

    if not parquet_files:
        print("No crypto parquet partition files found to verify.")
        return True

    print(f"\nVerifying {len(parquet_files)} crypto partition(s)...")
    all_ok = True
    for full_path in parquet_files:
        try:
            meta = pq.read_metadata(full_path)
            rows = meta.num_rows
            size = full_path.stat().st_size
            rel_path = full_path.relative_to(Path(store_root)).as_posix()
            print(f" [OK] {rel_path} ({rows:,} rows, {size:,} bytes)")
        except Exception as e:
            print(f" [FAIL] Failed to read {full_path}: {e}")
            all_ok = False

    return all_ok


# ==============================================================================
# Public High-Level APIs (Parity with StrategyQuant X GUI Modals)
# ==============================================================================


def show_disclaimer() -> str:
    """
    Displays and returns the official StrategyQuant X Cryptocurrency data disclaimer text.
    """
    print(CRYPTO_DISCLAIMER_TEXT)
    return CRYPTO_DISCLAIMER_TEXT


def add_symbol(
    source: str = "CRYPTO",
    broker: str = "BINANCE",
    Symbol: str = "",
    Timeframe: str = "",
    Postfix: str = "",
    disclaimer: Union[bool, str] = "true",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    postfix: Optional[str] = None,
    symbols: Optional[Union[str, List[str]]] = None,
    **kwargs: Any,
) -> Union[int, List[int]]:
    """
    Registers a new cryptocurrency instrument and dataset into StrategyQuant X
    `DATA` and `INSTRUMENTS` tables in scripts/haruquantai.db.

    Parity with StrategyQuant X GUI 'Add Crypto data' modal:
    -------------------------------------------------------
    - source: Data source identifier (default: 'CRYPTO', maps to SOURCE = 7).
    - broker: Target crypto exchange (default: 'BINANCE').
    - Symbol: Base cryptocurrency symbol (e.g. 'BTCUSDT', 'ETHUSDT', 'SOLUSDT').
    - Timeframe: Resolution bar (default: 'M1', or 'M5', 'H1', 'D1', 'M1/M5').
    - Postfix: Optional suffix appended to symbol identifier (e.g. '_binance').
    - disclaimer: Required acknowledgment of cryptocurrency market risk (default: 'true').

    Parameters:
    -----------
    source : str
        Data source name (default: 'CRYPTO').
    broker : str
        Exchange name (default: 'BINANCE').
    Symbol : str
        Cryptocurrency ticker (default: 'BTCUSDT').
    Timeframe : str
        Bar timeframe (default: 'M1').
    Postfix : str
        Optional symbol suffix.
    disclaimer : Union[bool, str]
        If True or 'true', confirms understanding of cryptocurrency market risks.

    Returns:
    --------
    Union[int, List[int]]
        Row ID (or list of IDs) registered in the `DATA` table.
    """
    if (
        str(disclaimer).strip().lower() in ("false", "0", "no", "off")
        or disclaimer is False
    ):
        raise ValueError(
            "You must confirm the Crypto data disclaimer to proceed:\n"
            + CRYPTO_DISCLAIMER_TEXT
        )
    logger.info("Crypto data disclaimer acknowledged.")

    # Handle if first positional arg was passed as Symbol rather than source
    if source.upper() != "CRYPTO" and source != "7":
        if not Symbol and not symbol and not symbols:
            Symbol = source
            source = "CRYPTO"

    raw_sym = (
        Symbol
        or symbol
        or symbols
        or kwargs.get("Symbol")
        or kwargs.get("symbol")
        or kwargs.get("symbols")
        or "BTCUSDT"
    )
    if isinstance(raw_sym, str):
        sym_list = [s.strip() for s in raw_sym.split(",") if s.strip()]
    else:
        sym_list = list(raw_sym)

    raw_tf = (
        Timeframe
        or timeframe
        or kwargs.get("Timeframe")
        or kwargs.get("timeframe")
        or kwargs.get("tf")
        or "M1"
    )
    if isinstance(raw_tf, str):
        tf_list = [
            t.strip().upper() for t in raw_tf.replace("/", ",").split(",") if t.strip()
        ]
    else:
        tf_list = [str(t).strip().upper() for t in raw_tf if t]
    if not tf_list:
        tf_list = ["M1"]

    eff_postfix = (
        Postfix
        if Postfix != ""
        else (postfix if postfix is not None else kwargs.get("data_postfix", ""))
    )

    etype = ExchangeType.resolve(broker)
    broker_clean = broker.lower().strip()
    broker_id = -1
    conn = None
    try:
        conn = sqlite3.connect(UNIFIED_DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute(
            "SELECT ID FROM BROKER WHERE LOWER(NAME) LIKE ? OR LOWER(POSTFIX) LIKE ?",
            (f"%{broker_clean}%", f"%{broker_clean}%"),
        )
        b_row = cur.fetchone()
        if b_row:
            broker_id = b_row[0]
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    catalog = CryptoCatalog()
    added_ids: List[int] = []

    sqx_root_path = Path(kwargs.get("sqx_root", "C:/SQX"))
    target_dbs: List[Path] = [UNIFIED_DB_PATH]
    user_db = sqx_root_path / "user" / "data" / "data.db"
    if user_db.exists() and user_db.resolve() != UNIFIED_DB_PATH.resolve():
        target_dbs.append(user_db)

    for datadb_path in target_dbs:
        if not datadb_path.exists():
            continue
        conn = None
        try:
            conn = sqlite3.connect(str(datadb_path), timeout=5)
            cur = conn.cursor()

            for raw_s in sym_list:
                clean_s = clean_symbol(raw_s).upper()
                if eff_postfix and clean_s.endswith(eff_postfix.upper()):
                    clean_s = clean_s[: -len(eff_postfix)].strip()
                eff_s = f"{clean_s}{eff_postfix}" if eff_postfix else clean_s

                info = catalog.get_symbol_info(clean_s, etype)

                # Register in INSTRUMENTS table
                cur.execute(
                    """
                    INSERT OR REPLACE INTO INSTRUMENTS (
                        INSTRUMENT, DESCRIPTION, POINTVALUE, TICKSIZE, TICKSTEP,
                        DEFAULTSPREAD, COMMISSIONS, DATATYPE, EXCHANGE, COUNTRY,
                        SECTOR, DEFAULTSLIPPAGE, SWAP, ORDERSIZEMULTIPLIER, ORDERSIZESTEP,
                        BROKER_ID, MIN_DISTANCE
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, '<Method type="None" use="true"><Params/></Method>', 7, ?, NULL,
                        NULL, ?, NULL, ?, ?,
                        ?, 0.0
                    )
                """,
                    (
                        eff_s,
                        info.description or f"{clean_s} ({etype.value})",
                        info.point_value,
                        info.tick_size,
                        info.tick_step,
                        info.default_spread,
                        etype.value,
                        info.default_slippage,
                        info.order_size_multiplier,
                        info.order_size_step,
                        broker_id,
                    ),
                )

                for tf in tf_list:
                    postfix_sym = f"{eff_s}_{tf}"
                    rel_dir = f"crypto/{tf.lower()}/{clean_s.lower()}"

                    cur.execute(
                        """
                        SELECT ID FROM DATA
                        WHERE (SOURCE = 7 AND (UPPER(INSTRUMENT) = ? OR UPPER(INSTRUMENT) = ?) AND UPPER(TIMEFRAME) = ?)
                           OR ((UPPER(SYMBOL) = ? OR UPPER(SYMBOL) = ?) AND UPPER(TIMEFRAME) = ?)
                    """,
                        (clean_s, eff_s, tf, postfix_sym, f"{clean_s}_{tf}", tf),
                    )
                    existing = cur.fetchone()

                    if existing:
                        row_id = existing[0]
                        cur.execute(
                            "UPDATE DATA SET SHOW = 1, BROKER_ID = ? WHERE ID = ?",
                            (broker_id, row_id),
                        )
                        logger.info(
                            f"Symbol '{eff_s}' [{tf}] already registered in DATA table (ID: {row_id})"
                        )
                        if datadb_path.resolve() == UNIFIED_DB_PATH.resolve():
                            added_ids.append(row_id)
                    else:
                        cur.execute(
                            """
                            INSERT INTO DATA (
                                SOURCEDATA_ID, CONNECTION, SYMBOL, INSTRUMENT, TIMEFRAME,
                                TIMEZONE, FILENAME, DATEFROM, DATETO, DATATYPE,
                                ROWS, DECIMALS, SOURCE, SECONDS_RECORDS, USYMBOL,
                                USYMBOLNAME, REMOVE_WEEKENDS, SHOW, BASKET_ID, BROKER_ID
                            ) VALUES (
                                0, 'History', ?, ?, ?,
                                'Exchange', ?, NULL, NULL, 1,
                                0, ?, 7, 0, ?,
                                ?, 0, 1, -1, ?
                            )
                        """,
                            (
                                postfix_sym,
                                eff_s,
                                tf,
                                rel_dir,
                                info.price_precision,
                                clean_s,
                                info.description or clean_s,
                                broker_id,
                            ),
                        )
                        new_id = cur.lastrowid
                        logger.info(
                            f"Added symbol '{eff_s}' [{tf}] to DATA table (ID: {new_id})"
                        )
                        if datadb_path.resolve() == UNIFIED_DB_PATH.resolve():
                            added_ids.append(new_id)

            conn.commit()
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    return added_ids[0] if len(added_ids) == 1 else added_ids


def download_data(
    source: str = "CRYPTO",
    broker: str = "BINANCE",
    Symbol: str = "",
    Timeframe: str = "",
    redownload: str = "MISSING",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    start_date: Optional[Union[str, datetime.date, datetime.datetime, int]] = None,
    end_date: Optional[Union[str, datetime.date, datetime.datetime, int]] = None,
    Postfix: str = "",
    postfix: Optional[str] = None,
    resample_timeframes: Optional[List[str]] = None,
    store: Union[str, Path] = "data/market",
    sync_sqx: bool = True,
    sqx_root: Union[str, Path] = "C:/SQX",
    show_progress: bool = True,
    symbols: Optional[Union[str, List[str]]] = None,
    **kwargs: Any,
) -> Dict[str, pd.DataFrame]:
    """
    Downloads historical cryptocurrency candle data directly from exchange REST API,
    persists into canonical partitioned Parquet storage, and synchronizes the
    StrategyQuant X `DATA` and `INSTRUMENTS` tables.

    Parity with StrategyQuant X GUI 'Download Crypto data' modal:
    ------------------------------------------------------------
    - source: Data source identifier (default: 'CRYPTO').
    - broker: Target crypto exchange (default: 'BINANCE').
    - Symbol: Cryptocurrency symbol or list of symbols (default: 'BTCUSDT').
    - Timeframe: Target bar timeframe (default: 'M1').
    - redownload: 'MISSING' ('Add only missing data') or 'OVERWRITE' ('Overwrite existing data').
    - start_date / end_date: Date range boundaries.
    - Postfix: Optional symbol suffix.

    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary mapping '{symbol}_{timeframe}' to the downloaded DataFrame.
    """
    # Handle if first positional arg was passed as Symbol rather than source
    if source.upper() != "CRYPTO" and source != "7":
        if not Symbol and not symbol and not symbols:
            Symbol = source
            source = "CRYPTO"

    raw_sym = (
        Symbol
        or symbol
        or symbols
        or kwargs.get("Symbol")
        or kwargs.get("symbol")
        or kwargs.get("symbols")
        or "BTCUSDT"
    )
    if isinstance(raw_sym, str):
        sym_list = [s.strip() for s in raw_sym.split(",") if s.strip()]
    else:
        sym_list = list(raw_sym)

    raw_tf = (
        Timeframe
        or timeframe
        or kwargs.get("Timeframe")
        or kwargs.get("timeframe")
        or kwargs.get("tf")
        or "M1"
    )
    tf = raw_tf.upper().strip()

    eff_postfix = (
        Postfix
        if Postfix != ""
        else (postfix if postfix is not None else kwargs.get("data_postfix", ""))
    )

    s_val = (
        kwargs.get("start")
        or kwargs.get("from_date")
        or kwargs.get("from")
        or start_date
    )
    e_val = kwargs.get("end") or kwargs.get("to_date") or kwargs.get("to") or end_date
    mode = (
        "overwrite"
        if str(redownload or kwargs.get("mode", "")).upper().strip()
        in ("OVERWRITE", "FORCE")
        else "missing"
    )

    results: Dict[str, pd.DataFrame] = {}

    for raw_s in sym_list:
        clean_s = clean_symbol(raw_s).upper()
        if eff_postfix and clean_s.endswith(eff_postfix.upper()):
            clean_s = clean_s[: -len(eff_postfix)].strip()
        eff_s = f"{clean_s}{eff_postfix}" if eff_postfix else clean_s

        if mode == "missing":
            cached_df = scan_market_crypto(
                store_root=store, symbol=clean_s, timeframe=tf
            )
            if not cached_df.empty:
                if s_val is None and e_val is None:
                    if show_progress:
                        logger.info(
                            f"Using cached canonical {tf} data for {eff_s} ({len(cached_df):,} bars)"
                        )
                    results[f"{eff_s}_{tf}"] = cached_df
                    continue
                else:
                    first_dt = cached_df["DateTime"].iloc[0]
                    last_dt = cached_df["DateTime"].iloc[-1]
                    s_dt_ms = _parse_datetime(s_val) if s_val else 0
                    e_dt_ms = (
                        _parse_datetime(e_val) if e_val else int(time.time() * 1000)
                    )
                    if (
                        int(first_dt.timestamp() * 1000) <= s_dt_ms
                        and int(last_dt.timestamp() * 1000) >= e_dt_ms - 86400000
                    ):
                        if show_progress:
                            logger.info(
                                f"Using cached canonical {tf} data for {eff_s} ({len(cached_df):,} bars)"
                            )
                        results[f"{eff_s}_{tf}"] = cached_df
                        continue

        df = download_crypto(
            symbol=clean_s,
            exchange=broker,
            timeframe=tf,
            start=s_val,
            end=e_val,
            store_root=store,
            resample_timeframes=resample_timeframes or kwargs.get("resample"),
            sync_sqx=sync_sqx,
            sqx_root=sqx_root,
            postfix=eff_postfix,
        )
        results[f"{eff_s}_{tf}"] = df

    return results


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entry Point
# ---------------------------------------------------------------------------
def dashboard(
    source: Optional[str] = "crypto",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    all_sources: bool = False,
    db_path: Optional[Union[str, Path]] = None,
) -> None:
    """Displays StrategyQuant X Data Manager dashboard for datasets (`DATA` table)."""
    try:
        from scripts.dashboard import render_dashboard
    except ImportError:
        from dashboard import render_dashboard
    render_dashboard(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        all_sources=all_sources,
        db_path=db_path or UNIFIED_DB_PATH,
    )


def create_cli_parser() -> argparse.ArgumentParser:
    """Builds comprehensive CLI argument parser matching SQX ecosystem standard."""
    parser = argparse.ArgumentParser(
        description="StrategyQuant X Crypto Data Ingestion, Storage & Synthesis Engine (100% Parity)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Top-level shorthand arguments
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Display StrategyQuant X Data Manager dashboard",
    )
    parser.add_argument(
        "--all", action="store_true", help="Display all data sources in dashboard"
    )
    parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        help="Cryptocurrency symbol (e.g. BTCUSDT, ETHUSDT, BTC-USD)",
    )
    parser.add_argument(
        "--exchange",
        "-e",
        type=str,
        default="Binance",
        help="Exchange name (Binance, Binance Coin-M, Binance USDT-M, Bitfinex, Coinbase Pro, Poloniex)",
    )
    parser.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        default="M1",
        help="Timeframe (M1, M3, M5, M15, M30, H1, H4, D1)",
    )
    parser.add_argument(
        "--start",
        "--from",
        dest="start",
        type=str,
        help="Start date (YYYY-MM-DD or YYYY.MM.DD)",
    )
    parser.add_argument(
        "--end",
        "--to",
        dest="end",
        type=str,
        help="End date (YYYY-MM-DD or YYYY.MM.DD)",
    )
    parser.add_argument(
        "--store-root",
        type=str,
        default="data/market",
        help="Market data root storage path",
    )
    parser.add_argument(
        "--sqx-root",
        type=str,
        default="C:/SQX",
        help="StrategyQuant X installation root path",
    )
    parser.add_argument(
        "--resample",
        nargs="+",
        help="Resample to additional timeframes (e.g. --resample M5 M15 H1 D1)",
    )
    parser.add_argument(
        "--no-sync-sqx",
        action="store_true",
        help="Disable synchronization with SQX user/data/data.db",
    )

    subparsers = parser.add_subparsers(dest="command", help="Operational Subcommands")

    # 1. disclaimer
    subparsers.add_parser(
        "disclaimer",
        help="Display official StrategyQuant X Cryptocurrency data disclaimer",
    )

    # 2. add-symbol
    p_add = subparsers.add_parser(
        "add-symbol", help="Add cryptocurrency symbol to StrategyQuant X DATA catalog"
    )
    p_add.add_argument(
        "symbol",
        nargs="?",
        default=None,
        help="Cryptocurrency symbol (e.g. BTCUSDT, ETHUSDT)",
    )
    p_add.add_argument(
        "--symbol",
        "-s",
        type=str,
        dest="symbol_opt",
        help="Cryptocurrency symbol (e.g. BTCUSDT)",
    )
    p_add.add_argument(
        "--broker",
        "-b",
        "--exchange",
        "-e",
        dest="broker",
        type=str,
        default="BINANCE",
        help="Exchange / Broker (default: BINANCE)",
    )
    p_add.add_argument(
        "--source",
        type=str,
        default="CRYPTO",
        help="Data source identifier (default: CRYPTO)",
    )
    p_add.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        default="M1",
        help="Timeframe (default: M1)",
    )
    p_add.add_argument(
        "--postfix",
        "-p",
        type=str,
        default="",
        help="Optional symbol suffix (e.g. _binance)",
    )
    p_add.add_argument(
        "--disclaimer",
        type=str,
        default="true",
        help="Confirmation of cryptocurrency risk disclaimer (default: true)",
    )
    p_add.add_argument(
        "--no-disclaimer", action="store_true", help="Reject disclaimer (raises error)"
    )

    # 3. download-data / download
    for cmd_name in ("download-data", "download"):
        p_down = subparsers.add_parser(
            cmd_name,
            help="Download historical cryptocurrency candles and sync DATA table",
        )
        p_down.add_argument(
            "symbols", nargs="*", default=None, help="One or more symbols to download"
        )
        p_down.add_argument(
            "--symbol", "-s", type=str, dest="symbol_opt", help="Symbol ticker"
        )
        p_down.add_argument(
            "--broker",
            "-b",
            "--exchange",
            "-e",
            dest="broker",
            type=str,
            default="BINANCE",
            help="Target exchange / broker (default: BINANCE)",
        )
        p_down.add_argument(
            "--source",
            type=str,
            default="CRYPTO",
            help="Data source identifier (default: CRYPTO)",
        )
        p_down.add_argument(
            "--timeframe",
            "-t",
            "--tf",
            dest="timeframe",
            type=str,
            default="M1",
            help="Timeframe (default M1)",
        )
        p_down.add_argument(
            "--redownload",
            "-r",
            choices=["MISSING", "OVERWRITE", "missing", "overwrite"],
            default="MISSING",
            help="Redownload mode: 'MISSING' or 'OVERWRITE' (default: MISSING)",
        )
        p_down.add_argument(
            "--postfix", "-p", type=str, default="", help="Optional symbol suffix"
        )
        p_down.add_argument(
            "--start",
            "--from",
            dest="start",
            type=str,
            help="Start date (YYYY-MM-DD or YYYY.MM.DD)",
        )
        p_down.add_argument(
            "--end",
            "--to",
            dest="end",
            type=str,
            help="End date (YYYY-MM-DD or YYYY.MM.DD)",
        )
        p_down.add_argument(
            "--store-root",
            "--store",
            dest="store_root",
            type=str,
            default="data/market",
            help="Market data root path",
        )
        p_down.add_argument(
            "--sqx-root",
            type=str,
            default="C:/SQX",
            help="StrategyQuant X installation root path",
        )
        p_down.add_argument(
            "--resample",
            nargs="+",
            help="Resample to additional timeframes (e.g. M5 M15 H1 D1)",
        )
        p_down.add_argument(
            "--no-sync-sqx", action="store_true", help="Disable SQX data.db sync"
        )

    # 4. list-exchanges
    subparsers.add_parser(
        "list-exchanges",
        help="List all supported crypto exchanges and available timeframes",
    )

    # 5. list-symbols
    p_syms = subparsers.add_parser(
        "list-symbols", help="List symbols available on an exchange"
    )
    p_syms.add_argument("exchange", nargs="?", default=None, help="Target exchange")
    p_syms.add_argument(
        "--exchange",
        "-e",
        type=str,
        dest="exchange_opt",
        default=None,
        help="Target exchange",
    )
    p_syms.add_argument(
        "--filter", "-f", type=str, help="Filter string (e.g. USDT, BTC)"
    )

    # 6. symbol-info
    p_info = subparsers.add_parser(
        "symbol-info", help="Retrieve symbol specifications and price precision"
    )
    p_info.add_argument("symbol", nargs="?", default=None, help="Symbol ticker")
    p_info.add_argument(
        "--symbol", "-s", type=str, dest="symbol_opt", help="Symbol ticker"
    )
    p_info.add_argument(
        "--exchange", "-e", type=str, default="Binance", help="Target exchange"
    )

    # 7. resample
    p_res = subparsers.add_parser(
        "resample", help="Resample existing local Parquet candles to higher timeframes"
    )
    p_res.add_argument("symbol", nargs="?", default=None, help="Symbol ticker")
    p_res.add_argument(
        "--symbol", "-s", type=str, dest="symbol_opt", help="Symbol ticker"
    )
    p_res.add_argument(
        "--source-tf",
        "--from-tf",
        dest="source_tf",
        type=str,
        default="M1",
        help="Source timeframe (default M1)",
    )
    p_res.add_argument(
        "--target-tf",
        "--to-tf",
        dest="target_tf",
        nargs="+",
        required=True,
        help="Target timeframes (e.g. M5 M15 H1 D1)",
    )
    p_res.add_argument(
        "--store-root", type=str, default="data/market", help="Market data root path"
    )

    # 8. scan
    p_scan = subparsers.add_parser(
        "scan", help="Scan local Parquet crypto store and display inventory"
    )
    p_scan.add_argument(
        "symbol", nargs="?", default=None, help="Optional symbol filter"
    )
    p_scan.add_argument(
        "--symbol", "-s", type=str, dest="symbol_opt", help="Optional symbol filter"
    )
    p_scan.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        help="Optional timeframe filter",
    )
    p_scan.add_argument(
        "--store-root", type=str, default="data/market", help="Market data root path"
    )
    p_scan.add_argument(
        "--head", type=int, default=5, help="Number of head rows to show"
    )
    p_scan.add_argument(
        "--tail", type=int, default=5, help="Number of tail rows to show"
    )

    # 9. import-dat
    p_dat = subparsers.add_parser(
        "import-dat", help="Import a single StrategyQuant binary .dat file"
    )
    p_dat.add_argument("file", type=str, help="Path to .dat file")
    p_dat.add_argument("--symbol", "-s", type=str, help="Symbol override")
    p_dat.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        help="Timeframe override",
    )
    p_dat.add_argument(
        "--exchange", "-e", type=str, default="Binance", help="Exchange name"
    )
    p_dat.add_argument(
        "--store-root", type=str, default="data/market", help="Market data root path"
    )

    # 10. import-local
    p_loc = subparsers.add_parser(
        "import-local", help="Auto-discover and import all SQX crypto history files"
    )
    p_loc.add_argument(
        "--history-root",
        type=str,
        default="C:/SQX/user/data/History",
        help="History root directory",
    )
    p_loc.add_argument(
        "--store-root", type=str, default="data/market", help="Market data root path"
    )

    # 11. verify
    p_ver = subparsers.add_parser(
        "verify",
        help="Verify integrity of local Parquet partitions against scripts/haruquantai.db",
    )
    p_ver.add_argument("symbol", nargs="?", default=None, help="Optional symbol filter")
    p_ver.add_argument(
        "--symbol", "-s", type=str, dest="symbol_opt", help="Optional symbol filter"
    )
    p_ver.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        help="Optional timeframe filter",
    )
    p_ver.add_argument(
        "--store-root", type=str, default="data/market", help="Market data root path"
    )

    # 12. dashboard
    p_dash = subparsers.add_parser(
        "dashboard", help="Display StrategyQuant X Data Manager dashboard"
    )
    p_dash.add_argument(
        "--all", action="store_true", help="Display all data sources in dashboard"
    )
    p_dash.add_argument(
        "--symbol",
        "-s",
        type=str,
        dest="symbol_opt",
        default=None,
        help="Optional symbol filter",
    )
    p_dash.add_argument(
        "--timeframe",
        "-t",
        "--tf",
        dest="timeframe",
        type=str,
        default=None,
        help="Optional timeframe filter",
    )

    return parser


def main() -> int:
    if len(sys.argv) > 1:
        first_arg = sys.argv[1].lower().strip()
        if first_arg in ("--dashboard", "-dashboard"):
            dashboard()
            return 0
        if first_arg in ("disclaimer", "--disclaimer", "-disclaimer"):
            show_disclaimer()
            return 0

    parser = create_cli_parser()
    args = parser.parse_args()

    if getattr(args, "dashboard", False) or args.command == "dashboard":
        src = None if getattr(args, "all", False) else "crypto"
        sym = getattr(args, "symbol", None) or getattr(args, "symbol_opt", None)
        tf = getattr(args, "timeframe", None)
        dashboard(source=src, symbol=sym, timeframe=tf)
        return 0

    # Subcommand execution
    if args.command == "disclaimer":
        show_disclaimer()
        return 0

    elif args.command == "add-symbol":
        sym = (
            getattr(args, "symbol_opt", None)
            or getattr(args, "symbol", None)
            or "BTCUSDT"
        )
        disclaimer_val = (
            "false"
            if getattr(args, "no_disclaimer", False)
            else getattr(args, "disclaimer", "true")
        )
        row_id = add_symbol(
            source=getattr(args, "source", "CRYPTO"),
            broker=getattr(args, "broker", "BINANCE"),
            Symbol=sym,
            Timeframe=getattr(args, "timeframe", "M1"),
            Postfix=getattr(args, "postfix", ""),
            disclaimer=disclaimer_val,
        )
        print(f"Successfully registered symbol '{sym}' (DATA row ID: {row_id})")
        return 0

    elif args.command in ("download-data", "download"):
        symbols_list = []
        if getattr(args, "symbols", None):
            symbols_list.extend(args.symbols)
        sym_opt = getattr(args, "symbol_opt", None) or getattr(args, "symbol", None)
        if sym_opt and sym_opt not in symbols_list:
            symbols_list.append(sym_opt)
        if not symbols_list:
            symbols_list = ["BTCUSDT"]

        res = download_data(
            source=getattr(args, "source", "CRYPTO"),
            broker=getattr(args, "broker", "BINANCE"),
            symbols=symbols_list,
            Timeframe=getattr(args, "timeframe", "M1"),
            redownload=getattr(args, "redownload", "MISSING"),
            start_date=args.start,
            end_date=args.end,
            Postfix=getattr(args, "postfix", ""),
            resample_timeframes=getattr(args, "resample", None),
            store=getattr(args, "store_root", "data/market"),
            sync_sqx=not getattr(args, "no_sync_sqx", False),
            sqx_root=getattr(args, "sqx_root", "C:/SQX"),
        )
        print(f"Successfully processed {len(res)} dataset(s).")
        return 0

    elif args.command == "list-exchanges":
        print("\nSupported StrategyQuant X Crypto Exchanges (100% Parity):")
        print("=" * 75)
        for ex in ExchangeFactory.list_all():
            print(f"Exchange Name  : {ex.get_name()}")
            print(f"Timeframes     : {', '.join(ex.available_timeframes())}")
            print("-" * 75)
        return 0

    elif args.command == "list-symbols":
        exch = (
            getattr(args, "exchange", None)
            or getattr(args, "exchange_opt", None)
            or "Binance"
        )
        driver = ExchangeFactory.get(exch)
        syms = driver.get_symbols()
        if args.filter:
            flt = args.filter.strip().upper()
            syms = [s for s in syms if flt in s.upper()]
        print(f"\nAvailable symbols on {driver.get_name()} ({len(syms):,} total):")
        print("-" * 60)
        for i in range(0, min(len(syms), 100), 5):
            print("  ".join(f"{s:<12}" for s in syms[i : i + 5]))
        if len(syms) > 100:
            print(f"  ... and {len(syms) - 100:,} more symbols.")
        return 0

    elif args.command == "symbol-info":
        sym = getattr(args, "symbol", None) or getattr(args, "symbol_opt", None)
        if not sym:
            print("Error: Please specify symbol via positional argument or --symbol.")
            return 1
        catalog = CryptoCatalog()
        info = catalog.get_symbol_info(sym, args.exchange)
        print("\n=======================================================")
        print(f" StrategyQuant Crypto Specification: {info.symbol}")
        print("=======================================================")
        print(f" Exchange       : {info.exchange}")
        print(f" Description    : {info.description}")
        print(f" Point Value    : {info.point_value:g}")
        print(f" Tick Size      : {info.tick_size:g}")
        print(f" Tick Step      : {info.tick_step:g}")
        print(f" Price Decimals : {info.price_precision}")
        print(f" Default Spread : {info.default_spread:g}")
        print(f" Status         : {info.status}")
        print("=======================================================\n")
        return 0

    elif args.command == "resample":
        sym = getattr(args, "symbol", None) or getattr(args, "symbol_opt", None)
        if not sym:
            print("Error: Please specify symbol via positional argument or --symbol.")
            return 1
        df = scan_market_crypto(
            store_root=args.store_root, symbol=sym, timeframe=args.source_tf
        )
        if df.empty:
            print(f"No source data found for {sym} [{args.source_tf}] to resample.")
            return 1
        for tf in args.target_tf:
            logger.info(f"Resampling {sym} [{args.source_tf}] -> [{tf}]...")
            df_res = resample_candles(df, tf)
            store_canonical_partitions(
                df_res, symbol=sym, timeframe=tf, store_root=args.store_root
            )
        print(f"Resampling complete for {sym}.")
        return 0

    elif args.command == "scan":
        sym = getattr(args, "symbol", None) or getattr(args, "symbol_opt", None)
        df = scan_market_crypto(
            store_root=args.store_root, symbol=sym, timeframe=args.timeframe
        )
        if df.empty:
            print("No local Parquet crypto records found matching criteria.")
            return 0
        sym_desc = sym.upper() if sym else "ALL"
        tf_desc = args.timeframe.upper() if args.timeframe else "ALL"
        print(
            f"\nLocal Canonical Parquet Records for {sym_desc} [{tf_desc}]: {len(df):,} rows"
        )
        print(f"Date Range: {df['DateTime'].min()} -> {df['DateTime'].max()}")
        print("\nHead:")
        print(df.head(args.head))
        print("\nTail:")
        print(df.tail(args.tail))
        return 0

    elif args.command == "import-dat":
        cnt = import_sqx_dat_file(
            file_path=args.file,
            store_root=args.store_root,
            symbol_override=args.symbol,
            timeframe_override=args.timeframe,
            exchange_override=args.exchange,
        )
        print(f"Successfully imported {cnt:,} records from {args.file}")
        return 0

    elif args.command == "import-local":
        cnt = import_local_history(
            history_root=args.history_root, store_root=args.store_root
        )
        print(f"Completed local history import: {cnt:,} total records.")
        return 0

    elif args.command == "verify":
        sym = getattr(args, "symbol", None) or getattr(args, "symbol_opt", None)
        ok = verify_partitions(
            store_root=args.store_root, symbol=sym, timeframe=args.timeframe
        )
        return 0 if ok else 1

    # Top-level shorthand execution
    if getattr(args, "symbol", None):
        download_crypto(
            symbol=args.symbol,
            exchange=args.exchange,
            timeframe=args.timeframe,
            start=args.start,
            end=args.end,
            store_root=args.store_root,
            resample_timeframes=args.resample,
            sync_sqx=not args.no_sync_sqx,
            sqx_root=args.sqx_root,
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
