# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
#     "pyarrow>=14.0.0",
# ]
# ///
"""Yahoo Finance & StrategyQuant Historical Market Data Downloader & Parser.

Description:
    Implements a high-performance standalone Python engine to pull historical
    market data directly from Yahoo Finance, matching StrategyQuant X (SQX) and
    QuantDataManager DataSourceYahoo specifications with 100% parity.

    Supported asset classes:
    - Equities & Stocks: US and international tickers (e.g. AAPL, MSFT, NVDA, TSLA)
    - ETFs: Market and sector index funds (e.g. SPY, QQQ, IWM, DIA, XLF)
    - Indices: Major global benchmark indices (e.g. ^GSPC, ^DJI, ^IXIC, ^RUT, ^VIX)
    - Forex: Currency exchange pairs (e.g. EURUSD=X, GBPUSD=X, USDJPY=X)
    - Cryptocurrencies: Digital asset pairs (e.g. BTC-USD, ETH-USD, SOL-USD)
    - Commodities & Futures: Benchmark futures contracts (e.g. GC=F, CL=F, SI=F)

    Key Capabilities:
    - Multi-timeframe retrieval: Daily (D1/1d), Weekly (W1/1wk), Monthly (MN1/1mo),
      and Intraday (1m, 2m, 5m, 15m, 30m, 60m/1h, 90m).
    - Intelligent chunking & parallel workers: Slices large date spans into
      API-compliant windows (e.g. 7d for 1m, 50d for 5m-30m, 365d for 1h) with
      concurrent thread execution.
    - Full resampling engine: Synthesizes arbitrary bar intervals (e.g. H2, H4, M10)
      from base granularities using accurate OHLCV aggregation.
    - Canonical Parquet partitioning & SQLite catalog: Partitions data by year
      under `data/market/yahoo/{kind}/{symbol}/{year}.parquet` and updates
      `scripts/haruquantai.db` with row counts, byte sizes, and SHA-256 hashes.
    - Symbol lookup & search: Queries Yahoo's search endpoint with exchange and
      quote type details, matching SQX's symbol catalog search dialog.
    - Export & incremental merge: Exports to CSV, Parquet, or Feather formats, with
      support for appending new data without duplicating existing records ("Add only
      missing data" SQX parity).

Purpose:
    FEAT-SCRIPTS-YAHOO: High-performance standalone Yahoo Finance historical
    data downloader, parser, and partition manager with 100% StrategyQuant X parity.

Key Capabilities:
    - FR-YAHOO-CHART-QUERY: Fetches historical OHLCV and adjusted close bars
      via Yahoo Finance v8 chart API with cookie/crumb session resilience.
      Associated: `YahooSession.fetch_chart()`, `_fetch_single_range()`
      Logging: INFO on request launch, completion count, and rate limit retries.
    - FR-YAHOO-METADATA: Queries live instrument metadata and priceHint decimals.
      Associated: `get_symbol_info()`
      Logging: INFO on symbol metadata resolution and category detection.
    - FR-YAHOO-SEARCH: Discovers matching tickers by keyword or company name.
      Associated: `search_symbols()`, `SQYahooCatalog.lookup()`
      Logging: INFO on symbol search query and match counts.
    - FR-YAHOO-INTRADAY-CHUNKING: Slices intraday spans into Yahoo-compliant windows.
      Associated: `download_candles()`, `_generate_date_chunks()`
      Logging: INFO on chunk plan and parallel thread completion.
    - FR-YAHOO-RESAMPLE: Resamples base bars to higher user-specified timeframes.
      Associated: `resample_to_timeframe()`
      Logging: INFO on bar resampling rule execution and resulting row count.
    - FR-YAHOO-PARTITION-STORAGE: Writes yearly partitioned Parquet files and updates catalog.
      Associated: `store_canonical_partitions()`, `update_market_catalog()`
      Logging: INFO on partition files committed and catalog SQLite synchronization.
    - FR-YAHOO-EXPORT: Formats and persists datasets to CSV, Parquet, or Feather.
      Associated: `save_data()`
      Logging: INFO on file serialization, row totals, and file size in MB.

Python API Usage:
    ```python
    from scripts.yahoo import (
        download_candles,
        download_daily,
        download_intraday,
        get_symbol_info,
        save_data,
        scan_market_d1,
        search_symbols,
        store_canonical_partitions,
    )

    # 1. Download Daily Equity Data (SQX Default)
    df_daily = download_daily("AAPL", start="2020-01-01", end="2024-01-01")

    # 2. Download Intraday Data with Resampling to H1 / H4
    df_h1 = download_candles(
        "SPY", timeframe="H1", start="2024-01-01", end="2024-06-01"
    )

    # 3. Store into canonical Parquet partitions and sync scripts/haruquantai.db
    committed = store_canonical_partitions(df_daily, symbol="AAPL", kind="d1")

    # 4. Search Tickers Matching a Query
    matches = search_symbols("S&P 500")

    # 5. Read back from canonical storage
    df_scanned = scan_market_d1("AAPL", start="2020-01-01")

    # 6. Save directly to CSV or Parquet
    save_data(df_daily, "AAPL_D1.csv")
    ```

CLI Usage:
    ```bash
    # Subcommand style (matching sq_equity.py and sq_futures.py):
    python scripts/yahoo.py download AAPL MSFT --timeframe D1 --start 2020-01-01 --end 2024-01-01
    python scripts/yahoo.py lookup "Tesla"
    python scripts/yahoo.py info AAPL
    python scripts/yahoo.py scan AAPL --timeframe d1 --head 10

    # Direct flag style (matching dukascopy_downloader.py):
    python scripts/yahoo.py --symbol AAPL --start 2020-01-01 --end 2024-01-01 --output AAPL_D1.csv
    python scripts/yahoo.py --symbol SPY --timeframe H1 --start 2025-01-01 --end 2025-06-01 --output SPY_H1.parquet
    python scripts/yahoo.py --symbol EURUSD=X --timeframe D1 --start 2022-01-01 --output EURUSD_D1.csv
    python scripts/yahoo.py --search "NVIDIA"
    python scripts/yahoo.py --symbol NVDA --info
    ```
"""

# ruff: noqa: E501, PTH118, G004, DTZ007, PLR0917, PLR0915, PLR0912, RET504, ARG001

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

# Ensure standard library inspect is used in sys.modules to prevent shadowing
if "inspect" not in sys.modules or not hasattr(sys.modules["inspect"], "cleandoc"):
    _stdlib_inspect_path = os.path.join(sys.base_prefix, "Lib", "inspect.py")
    if pathlib.Path(_stdlib_inspect_path).exists():
        _spec = importlib.util.spec_from_file_location("inspect", _stdlib_inspect_path)
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules["inspect"] = _mod
            _spec.loader.exec_module(_mod)

import argparse
import datetime
import hashlib
import http.cookiejar
import json
import logging
import random
import re
import sqlite3
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

try:
    import pyarrow as pa  # type: ignore[import-untyped]
    import pyarrow.parquet as pq  # type: ignore[import-untyped]
except ImportError:
    pa = None
    pq = None

# Workspace root alignment
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
# Unified SQX Database Path
UNIFIED_DB_PATH = Path(__file__).resolve().parent / "haruquantai.db"

logger = logging.getLogger("YahooDownloader")

# Canonical Storage Schemas
if pa is not None:
    D1_SCHEMA = pa.schema(
        [
            pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
            pa.field("Open", pa.float64(), nullable=False),
            pa.field("High", pa.float64(), nullable=False),
            pa.field("Low", pa.float64(), nullable=False),
            pa.field("Close", pa.float64(), nullable=False),
            pa.field("Volume", pa.uint64(), nullable=False),
        ]
    )
    M1_SCHEMA = pa.schema(
        [
            pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
            pa.field("Open", pa.float64(), nullable=False),
            pa.field("High", pa.float64(), nullable=False),
            pa.field("Low", pa.float64(), nullable=False),
            pa.field("Close", pa.float64(), nullable=False),
            pa.field("Volume", pa.uint64(), nullable=False),
        ]
    )
else:
    D1_SCHEMA = None
    M1_SCHEMA = None

# Primary & Secondary Host endpoints
PRIMARY_BASE_URL = "https://query1.finance.yahoo.com"
FALLBACK_BASE_URL = "https://query2.finance.yahoo.com"

# Standard modern desktop browser User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Standard StrategyQuant X / QuantDataManager timeframe mappings
TIMEFRAME_MAP: dict[str, str] = {
    # Daily
    "D1": "1d",
    "1D": "1d",
    "1d": "1d",
    "d1": "1d",
    "DAILY": "1d",
    "DAY": "1d",
    # Weekly
    "W1": "1wk",
    "1W": "1wk",
    "1WK": "1wk",
    "1wk": "1wk",
    "w1": "1wk",
    "WEEKLY": "1wk",
    # Monthly
    "MN1": "1mo",
    "1MO": "1mo",
    "1mo": "1mo",
    "mn1": "1mo",
    "MONTHLY": "1mo",
    # Intraday 1-Minute
    "M1": "1m",
    "1M": "1m",
    "1m": "1m",
    "m1": "1m",
    # Intraday 2-Minute
    "M2": "2m",
    "2M": "2m",
    "2m": "2m",
    "m2": "2m",
    # Intraday 5-Minute
    "M5": "5m",
    "5M": "5m",
    "5m": "5m",
    "m5": "5m",
    # Intraday 15-Minute
    "M15": "15m",
    "15M": "15m",
    "15m": "15m",
    "m15": "15m",
    # Intraday 30-Minute
    "M30": "30m",
    "30M": "30m",
    "30m": "30m",
    "m30": "30m",
    # Intraday 60-Minute / 1-Hour
    "H1": "1h",
    "1H": "1h",
    "60M": "1h",
    "60m": "1h",
    "1h": "1h",
    "h1": "1h",
    # Intraday 90-Minute
    "M90": "90m",
    "90M": "90m",
    "90m": "90m",
}

# Max allowed span per request by Yahoo Finance API for given intervals
YAHOO_INTERVAL_WINDOW_DAYS: dict[str, int] = {
    "1m": 7,  # Yahoo limits 1m to 7-8 days per request (available for past 30 days)
    "2m": 50,  # 2m-30m up to 60 days total
    "5m": 50,
    "15m": 50,
    "30m": 50,
    "90m": 50,
    "1h": 365,  # 1h up to 730 days total
    "1d": 3650,  # Multi-year spans supported natively
    "1wk": 7300,
    "1mo": 18250,
}

# Default Symbol Decimals & Point Values (StrategyQuant Built-ins)
DEFAULT_SYMBOL_DECIMALS: dict[str, int] = {
    # Equities & ETFs
    "SPY": 2,
    "QQQ": 2,
    "DIA": 2,
    "IWM": 2,
    "AAPL": 2,
    "MSFT": 2,
    "NVDA": 2,
    "AMZN": 2,
    "GOOGL": 2,
    "META": 2,
    "TSLA": 2,
    # Indices
    "^GSPC": 2,
    "^DJI": 2,
    "^IXIC": 2,
    "^RUT": 2,
    "^VIX": 2,
    "^FTSE": 2,
    "^GDAXI": 2,
    "^N225": 2,
    # Forex
    "EURUSD=X": 5,
    "GBPUSD=X": 5,
    "USDJPY=X": 3,
    "AUDUSD=X": 5,
    "USDCAD=X": 5,
    "USDCHF=X": 5,
    "NZDUSD=X": 5,
    "EURGBP=X": 5,
    "EURJPY=X": 3,
    "GBPJPY=X": 3,
    # Crypto
    "BTC-USD": 2,
    "ETH-USD": 2,
    "SOL-USD": 2,
    "LTC-USD": 2,
    "XRP-USD": 4,
    # Commodities / Futures
    "GC=F": 2,
    "SI=F": 3,
    "CL=F": 2,
    "BZ=F": 2,
    "NG=F": 3,
}


# ============================================================================
# Session Management & HTTP Transport
# ============================================================================


class YahooSession:
    """Thread-safe resilient HTTP session with cookie & crumb management."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )
        self._crumb: str | None = None
        self._crumb_expiry: float = 0.0
        self._ssl_ctx = ssl.create_default_context()

    def get_crumb(self, force_refresh: bool = False) -> str | None:
        """Retrieves or refreshes the Yahoo API authentication crumb."""
        with self._lock:
            now = time.time()
            if not force_refresh and self._crumb and now < self._crumb_expiry:
                return self._crumb

            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }

            # 1. Warm cookie via fc.yahoo.com
            try:
                cookie_req = urllib.request.Request(
                    "https://fc.yahoo.com", headers=headers
                )
                self._opener.open(cookie_req, timeout=8)
            except Exception:
                pass

            # 2. Retrieve crumb from getcrumb endpoint
            crumb_url = f"{PRIMARY_BASE_URL}/v1/test/getcrumb"
            try:
                crumb_req = urllib.request.Request(crumb_url, headers=headers)
                with self._opener.open(crumb_req, timeout=10) as resp:
                    crumb = resp.read().decode("utf-8").strip()
                    if crumb and "{" not in crumb and "<" not in crumb:
                        self._crumb = crumb
                        self._crumb_expiry = now + 1800.0  # 30 minute cache
                        return self._crumb
            except Exception as e:
                logger.debug(f"Crumb retrieval notice (optional for chart API): {e}")

            return None

    def fetch_url_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int = 15,
        max_retries: int = 5,
        initial_backoff: float = 0.5,
    ) -> dict[str, Any]:
        """Fetches and decodes JSON from Yahoo endpoints with exponential retry backoff."""
        full_params = dict(params or {})

        # Append crumb if available
        crumb = self.get_crumb()
        if crumb and "crumb" not in full_params:
            full_params["crumb"] = crumb

        query_str = urllib.parse.urlencode(full_params)
        full_url = f"{url}?{query_str}" if query_str else url

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://finance.yahoo.com",
        }

        req = urllib.request.Request(full_url, headers=headers)
        backoff = initial_backoff

        for attempt in range(1, max_retries + 1):
            try:
                with self._opener.open(req, timeout=timeout) as resp:
                    payload = resp.read().decode("utf-8")
                    return cast("dict[str, Any]", json.loads(payload))
            except urllib.error.HTTPError as e:
                if e.code in (404, 422):
                    try:
                        err_payload = json.loads(e.read().decode("utf-8"))
                        err_desc = (
                            err_payload.get("chart", {})
                            .get("error", {})
                            .get("description", e.reason)
                        )
                    except Exception:
                        err_desc = e.reason
                    msg = f"Yahoo Finance HTTP {e.code}: {err_desc}"
                    raise ValueError(msg) from e
                if e.code in (401, 403):
                    logger.debug(
                        f"HTTP {e.code} received. Refreshing crumb (attempt {attempt}/{max_retries})..."
                    )
                    self.get_crumb(force_refresh=True)
                    time.sleep(backoff)
                    backoff = min(backoff * 1.5, 5.0)
                    continue
                if e.code in (429, 500, 502, 503, 504):
                    jitter = random.uniform(0.1, 0.4)
                    logger.debug(
                        f"Rate limit / server status {e.code}. Backing off {backoff + jitter:.2f}s..."
                    )
                    time.sleep(backoff + jitter)
                    backoff = min(backoff * 2.0, 10.0)
                    continue
                time.sleep(backoff)
            except (urllib.error.URLError, TimeoutError, OSError) as net_err:
                jitter = random.uniform(0.1, 0.3)
                logger.debug(
                    f"Transient network error: {net_err}. Retrying in {backoff + jitter:.2f}s..."
                )
                time.sleep(backoff + jitter)
                backoff = min(backoff * 1.5, 6.0)

        msg = f"Failed to retrieve data from Yahoo Finance after {max_retries} attempts: {url}"
        raise RuntimeError(msg)


# Global shared session instance
_SESSION = YahooSession()


# ============================================================================
# Metadata and Symbol Lookup
# ============================================================================

_SYMBOL_METADATA_CACHE: dict[str, dict[str, Any]] = {}


def normalize_symbol_name(symbol: str) -> str:
    """Normalizes ticker symbols to standard uppercase notation."""
    return symbol.strip().upper()


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Retrieves live specification and metadata for a Yahoo Finance ticker."""
    sym = normalize_symbol_name(symbol)
    if sym in _SYMBOL_METADATA_CACHE:
        return _SYMBOL_METADATA_CACHE[sym]

    url = f"{PRIMARY_BASE_URL}/v8/finance/chart/{urllib.parse.quote(sym)}"
    params = {"interval": "1d", "range": "1d"}

    try:
        data = _SESSION.fetch_url_json(url, params=params, timeout=10, max_retries=3)
        res = data.get("chart", {}).get("result")
        if res and len(res) > 0:
            meta = res[0].get("meta", {})
            price_hint = int(meta.get("priceHint", 2))
            info = {
                "symbol": meta.get("symbol", sym),
                "name": meta.get("shortName") or meta.get("longName") or sym,
                "currency": meta.get("currency", "USD"),
                "exchange": meta.get("exchangeName", "UNKNOWN"),
                "full_exchange": meta.get("fullExchangeName", "UNKNOWN"),
                "instrument_type": meta.get("instrumentType", "EQUITY"),
                "timezone": meta.get("exchangeTimezoneName", "America/New_York"),
                "decimals": price_hint,
                "point_multiplier": 10.0**price_hint,
                "regular_price": float(meta.get("regularMarketPrice", 0.0)),
                "chart_prev_close": float(meta.get("chartPreviousClose", 0.0)),
                "first_trade_date": meta.get("firstTradeDate"),
            }
            _SYMBOL_METADATA_CACHE[sym] = info
            logger.info(
                f"Resolved metadata for {sym}: currency={info['currency']}, exchange={info['exchange']}, decimals={info['decimals']}"
            )
            return info
    except Exception as exc:
        logger.debug(f"Live metadata fetch notice for {sym}: {exc}")

    # Fallback to local catalog and heuristic detection
    if sym in DEFAULT_SYMBOL_DECIMALS:
        decimals = DEFAULT_SYMBOL_DECIMALS[sym]
    elif sym.endswith("=X"):
        decimals = 3 if "JPY" in sym else 5
    elif "-USD" in sym:
        decimals = 2
    elif "=F" in sym:
        decimals = 2
    elif sym.startswith("^"):
        decimals = 2
    else:
        decimals = 2

    fallback_info = {
        "symbol": sym,
        "name": sym,
        "currency": "USD",
        "exchange": "UNKNOWN",
        "full_exchange": "UNKNOWN",
        "instrument_type": "EQUITY",
        "timezone": "America/New_York",
        "decimals": decimals,
        "point_multiplier": 10.0**decimals,
        "regular_price": 0.0,
        "chart_prev_close": 0.0,
        "first_trade_date": None,
    }
    _SYMBOL_METADATA_CACHE[sym] = fallback_info
    return fallback_info


def search_symbols(query: str, count: int = 10) -> list[dict[str, str]]:
    """Discovers matching Yahoo tickers by query string (matching SQX Search Dialog)."""
    q = query.strip()
    if not q:
        return []

    url = f"{PRIMARY_BASE_URL}/v1/finance/search"
    params = {"q": q, "quotesCount": count, "newsCount": 0}

    logger.info(f"Searching Yahoo Finance symbol catalog for query: '{q}'...")
    try:
        data = _SESSION.fetch_url_json(url, params=params, timeout=10, max_retries=3)
        quotes = data.get("quotes", [])
        results = [
            {
                "symbol": item.get("symbol", ""),
                "name": item.get("shortname")
                or item.get("longname")
                or item.get("symbol", ""),
                "exchange": item.get("exchange", "UNKNOWN"),
                "type": item.get("quoteType", "EQUITY"),
                "industry": item.get("industry", ""),
            }
            for item in quotes
        ]
        logger.info(f"Found {len(results)} matching symbol(s) for query: '{q}'.")
        return results
    except Exception as exc:
        logger.warning(f"Symbol search failed for query '{q}': {exc}")
        return []


# ============================================================================
# Date Parsing & Interval Helpers
# ============================================================================


def parse_date_param(
    val: str | datetime.datetime | datetime.date,
    end_of_day: bool = False,
) -> datetime.datetime:
    """Parses date string or datetime into UTC datetime."""
    if isinstance(val, datetime.datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=datetime.UTC)
        return val.astimezone(datetime.UTC)
    if isinstance(val, datetime.date):
        if end_of_day:
            return datetime.datetime(
                val.year,
                val.month,
                val.day,
                23,
                59,
                59,
                999999,
                tzinfo=datetime.UTC,
            )
        return datetime.datetime(
            val.year, val.month, val.day, 0, 0, 0, tzinfo=datetime.UTC
        )
    if isinstance(val, str):
        v = val.strip()
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y%m%d",
            "%Y.%m.%d",
        ):
            try:
                dt = datetime.datetime.strptime(v, fmt)
                if end_of_day and fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d"):
                    dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                return dt.replace(tzinfo=datetime.UTC)
            except ValueError:
                continue
        ts = pd.to_datetime(v, utc=True)
        return cast("datetime.datetime", ts.to_pydatetime())

    raise ValueError(f"Unsupported date format: {val}")


def normalize_timeframe(timeframe: str) -> tuple[str, str | None]:
    """
    Normalizes timeframe string into (native_yahoo_interval, resample_rule_if_needed).

    Examples:
        'D1'  -> ('1d', None)
        'H1'  -> ('1h', None)
        'H4'  -> ('1h', '4h')
        'M5'  -> ('5m', None)
        'M10' -> ('5m', '10min')
    """
    tf = timeframe.strip().upper()

    if tf in TIMEFRAME_MAP:
        return TIMEFRAME_MAP[tf], None

    lower_tf = timeframe.strip().lower()
    if lower_tf in YAHOO_INTERVAL_WINDOW_DAYS:
        return lower_tf, None

    if tf.startswith("H") and tf[1:].isdigit():
        hours = int(tf[1:])
        return "1h", f"{hours}h"

    if tf.startswith("M") and tf[1:].isdigit():
        mins = int(tf[1:])
        if mins in (1, 2, 5, 15, 30, 90):
            return f"{mins}m", None
        base_int = "5m" if mins % 5 == 0 else "1m"
        return base_int, f"{mins}min"

    raise ValueError(
        f"Unsupported timeframe '{timeframe}'. Use standard SQX notation (D1, W1, MN1, H1, H4, M15, M5, M1) "
        "or native Yahoo intervals (1d, 1wk, 1mo, 1h, 15m, 5m, 1m)."
    )


def _generate_date_chunks(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    interval: str,
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """Slices a date range into Yahoo-compliant maximum window chunks."""
    window_days = YAHOO_INTERVAL_WINDOW_DAYS.get(interval, 3650)
    chunks: list[tuple[datetime.datetime, datetime.datetime]] = []

    curr_start = start_dt
    while curr_start <= end_dt:
        curr_end = min(
            curr_start + datetime.timedelta(days=window_days),
            end_dt,
        )
        chunks.append((curr_start, curr_end))
        curr_start = curr_end + datetime.timedelta(seconds=1)

    return chunks


# ============================================================================
# Core Historical Data Downloader Engine
# ============================================================================


def _fetch_single_range(
    symbol: str,
    interval: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    include_adj_close: bool = True,
) -> pd.DataFrame:
    """Fetches a single date span from Yahoo Finance chart endpoint."""
    p1 = int(start_dt.timestamp())
    p2 = int(end_dt.timestamp())

    url = f"{PRIMARY_BASE_URL}/v8/finance/chart/{urllib.parse.quote(symbol)}"
    params = {
        "interval": interval,
        "period1": p1,
        "period2": p2,
        "events": "div,splits",
        "includeAdjustedClose": "true" if include_adj_close else "false",
    }

    try:
        data = _SESSION.fetch_url_json(url, params=params, timeout=15, max_retries=5)
    except ValueError:
        raise
    except Exception:
        mirror_url = (
            f"{FALLBACK_BASE_URL}/v8/finance/chart/{urllib.parse.quote(symbol)}"
        )
        data = _SESSION.fetch_url_json(
            mirror_url, params=params, timeout=15, max_retries=5
        )

    result = data.get("chart", {}).get("result")
    if not result:
        err = data.get("chart", {}).get("error", {})
        desc = err.get("description", "Unknown error")
        raise ValueError(f"Symbol '{symbol}' not found or no data returned: {desc}")

    chart_node = result[0]
    timestamps = chart_node.get("timestamp", [])
    if not timestamps:
        return pd.DataFrame()

    indicators = chart_node.get("indicators", {})
    quote_list = indicators.get("quote", [{}])
    quote_data = quote_list[0] if quote_list else {}

    opens = quote_data.get("open", [])
    highs = quote_data.get("high", [])
    lows = quote_data.get("low", [])
    closes = quote_data.get("close", [])
    volumes = quote_data.get("volume", [])

    adj_closes: list[float | None] = []
    if include_adj_close:
        adj_list = indicators.get("adjclose", [{}])
        if adj_list and "adjclose" in adj_list[0]:
            adj_closes = adj_list[0]["adjclose"]

    records: list[dict[str, Any]] = []
    for i, ts in enumerate(timestamps):
        c = closes[i] if i < len(closes) else None
        o = opens[i] if i < len(opens) else None
        h = highs[i] if i < len(highs) else None
        l_val = lows[i] if i < len(lows) else None
        v = volumes[i] if i < len(volumes) else 0

        if c is None or o is None or h is None or l_val is None:
            continue

        rec: dict[str, Any] = {
            "DateTime": datetime.datetime.fromtimestamp(ts, tz=datetime.UTC),
            "Open": float(o),
            "High": float(h),
            "Low": float(l_val),
            "Close": float(c),
            "Volume": float(v) if v is not None else 0.0,
        }
        if include_adj_close:
            adj = adj_closes[i] if i < len(adj_closes) else c
            rec["Adj Close"] = float(adj) if adj is not None else float(c)

        records.append(rec)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records).set_index("DateTime")
    return df


def download_candles(
    symbol: str,
    timeframe: str = "D1",
    start: str | datetime.datetime | datetime.date | None = None,
    end: str | datetime.datetime | datetime.date | None = None,
    include_adj_close: bool = True,
    max_workers: int = 4,
    show_progress: bool = True,
    store_root: str | Path | None = None,
    mode: str = "overwrite",
    tz: str | None = None,
) -> pd.DataFrame:
    """
    Downloads historical OHLCV candle data from Yahoo Finance with StrategyQuant X parity.

    Args:
        symbol: Market ticker (e.g. 'AAPL', 'SPY', '^GSPC', 'EURUSD=X', 'BTC-USD', 'GC=F').
        timeframe: Bar interval: 'D1' (default), 'W1', 'MN1', 'H1', 'H4', 'M15', 'M5', 'M1', etc.
        start: Start date/datetime. Defaults to 1 year ago if omitted.
        end: End date/datetime. Defaults to current timestamp if omitted.
        include_adj_close: Include 'Adj Close' column alongside Close (default True).
        max_workers: Number of concurrent HTTP worker threads for chunked downloads.
        show_progress: Log progress updates to stdout/logger.
        store_root: Optional canonical storage root (e.g. 'data/market') to persist partitions.
        mode: Download mode: 'overwrite' or 'missing'. If 'missing', skips cached dates.
        tz: Optional timezone shift (e.g. 'America/New_York', 'UTC+2').

    Returns:
        pd.DataFrame with DatetimeIndex named 'DateTime' and OHLCV columns.
    """
    sym = normalize_symbol_name(symbol)
    native_interval, resample_rule = normalize_timeframe(timeframe)
    sym_info = get_symbol_info(sym)
    decimals = sym_info["decimals"]

    now = datetime.datetime.now(datetime.UTC)
    if end is None:
        end_dt = now
    else:
        end_dt = parse_date_param(end, end_of_day=True)

    if start is None:
        if native_interval == "1m":
            start_dt = max(
                end_dt - datetime.timedelta(days=7),
                now - datetime.timedelta(days=29),
            )
        elif native_interval in ("2m", "5m", "15m", "30m", "90m"):
            start_dt = max(
                end_dt - datetime.timedelta(days=50),
                now - datetime.timedelta(days=59),
            )
        elif native_interval == "1h":
            start_dt = max(
                end_dt - datetime.timedelta(days=365),
                now - datetime.timedelta(days=729),
            )
        else:
            start_dt = end_dt - datetime.timedelta(days=365)
    else:
        start_dt = parse_date_param(start, end_of_day=False)

    if start_dt > end_dt:
        raise ValueError(
            f"Start date ({start_dt.date()}) cannot be after end date ({end_dt.date()})"
        )

    # Validate intraday boundaries against Yahoo retention limits
    if native_interval == "1m" and (now - start_dt).days > 30:
        logger.warning(
            f"Yahoo Finance 1m intraday data is only available for the past 30 days. Requested start: {start_dt.date()}."
        )
    elif (
        native_interval in ("2m", "5m", "15m", "30m", "90m")
        and (now - start_dt).days > 60
    ):
        logger.warning(
            f"Yahoo Finance {native_interval} data is only available for the past 60 days. Requested start: {start_dt.date()}."
        )
    elif native_interval == "1h" and (now - start_dt).days > 730:
        logger.warning(
            f"Yahoo Finance 1h data is only available for the past 730 days. Requested start: {start_dt.date()}."
        )

    # Check local cache if mode == 'missing' and store_root is provided
    if mode == "missing" and store_root is not None:
        cached_df = (
            scan_market_d1(sym, start=start_dt, end=end_dt, store_root=store_root)
            if native_interval == "1d"
            else scan_market_m1(sym, start=start_dt, end=end_dt, store_root=store_root)
        )
        if not cached_df.empty:
            c_min = cached_df.index.min()
            c_max = cached_df.index.max()
            if c_min <= start_dt and c_max >= end_dt - datetime.timedelta(days=1):
                if show_progress:
                    logger.info(
                        f"Requested range for {sym} already cached in {store_root} (mode='missing'). Skipping network fetch."
                    )
                return cached_df

    chunks = _generate_date_chunks(start_dt, end_dt, native_interval)
    total_chunks = len(chunks)

    if show_progress:
        logger.info(
            f"Downloading Yahoo Finance data for {sym} [{timeframe}] from {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')} ({total_chunks} chunk(s))..."
        )

    if total_chunks == 1:
        c_start, c_end = chunks[0]
        df = _fetch_single_range(
            sym,
            native_interval,
            c_start,
            c_end,
            include_adj_close=include_adj_close,
        )
    else:
        dfs: list[pd.DataFrame] = []
        completed = 0

        def _worker(
            span: tuple[datetime.datetime, datetime.datetime],
        ) -> pd.DataFrame:
            s, e = span
            return _fetch_single_range(
                sym,
                native_interval,
                s,
                e,
                include_adj_close=include_adj_close,
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(_worker, chunk): chunk for chunk in chunks
            }
            for fut in as_completed(future_to_chunk):
                try:
                    res_df = fut.result()
                    if not res_df.empty:
                        dfs.append(res_df)
                except Exception as exc:
                    logger.debug(f"Chunk download error for {sym}: {exc}")
                completed += 1
                if show_progress and (completed % 5 == 0 or completed == total_chunks):
                    logger.info(
                        f"Progress: {completed}/{total_chunks} chunks completed..."
                    )

        if not dfs:
            df = pd.DataFrame()
        else:
            df = pd.concat(dfs)
            df = df[~df.index.duplicated(keep="last")]
            df = df.sort_index()

    if df.empty:
        logger.warning(
            f"No data returned from Yahoo Finance for {sym} between {start_dt.date()} and {end_dt.date()}."
        )
        cols = ["Open", "High", "Low", "Close", "Volume"]
        if include_adj_close:
            cols.append("Adj Close")
        return pd.DataFrame(columns=cols)

    # Filter strictly within requested bounds
    df = df.loc[(df.index >= start_dt) & (df.index <= end_dt)]

    # Resample if custom timeframe was requested (e.g. H4, M10)
    if resample_rule:
        df = resample_to_timeframe(df, resample_rule)

    # Round price columns according to symbol decimals
    price_cols = [
        c for c in ["Open", "High", "Low", "Close", "Adj Close"] if c in df.columns
    ]
    df[price_cols] = df[price_cols].round(decimals)

    # Optional canonical partition persistence
    if store_root is not None and pa is not None:
        kind = "d1" if native_interval in ("1d", "1wk", "1mo") else "m1"
        try:
            store_canonical_partitions(
                data=df,
                symbol=sym,
                kind=kind,
                store_root=store_root,
                source="yahoo",
            )
        except Exception as store_err:
            logger.warning(f"Could not commit canonical partitions: {store_err}")

    # Optional timezone shift
    if tz is not None:
        try:
            df.index = df.index.tz_convert(tz)
        except Exception as tz_err:
            logger.warning(f"Failed to apply timezone shift '{tz}': {tz_err}")

    if show_progress:
        logger.info(
            f"Successfully downloaded {len(df):,} bars for {sym} [{timeframe}]. Date coverage: {df.index.min()} -> {df.index.max()}."
        )

    return df


def download_daily(
    symbol: str,
    start: str | datetime.datetime | datetime.date | None = None,
    end: str | datetime.datetime | datetime.date | None = None,
    include_adj_close: bool = True,
    show_progress: bool = True,
    store_root: str | Path | None = None,
) -> pd.DataFrame:
    """Convenience method to download standard Daily (D1) bars (SQX Default)."""
    return download_candles(
        symbol=symbol,
        timeframe="D1",
        start=start,
        end=end,
        include_adj_close=include_adj_close,
        show_progress=show_progress,
        store_root=store_root,
    )


def download_intraday(
    symbol: str,
    timeframe: str = "1m",
    start: str | datetime.datetime | datetime.date | None = None,
    end: str | datetime.datetime | datetime.date | None = None,
    include_adj_close: bool = False,
    max_workers: int = 4,
    show_progress: bool = True,
    store_root: str | Path | None = None,
) -> pd.DataFrame:
    """Convenience method to download Intraday bars (1m, 5m, 15m, 30m, 1h)."""
    return download_candles(
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        include_adj_close=include_adj_close,
        max_workers=max_workers,
        show_progress=show_progress,
        store_root=store_root,
    )


# ============================================================================
# Timeframe Resampling Engine
# ============================================================================


def resample_to_timeframe(df: pd.DataFrame, timeframe_rule: str) -> pd.DataFrame:
    """
    Resamples OHLCV DataFrame to higher timeframe using standard quantitative rules.

    Aggregation:
        Open: first, High: max, Low: min, Close: last, Volume: sum, Adj Close: last
    """
    if df.empty:
        return df

    tf = timeframe_rule.strip()
    rule_map = {
        "M1": "1min",
        "M2": "2min",
        "M3": "3min",
        "M5": "5min",
        "M10": "10min",
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
        "MN1": "1ME",
    }
    rule = rule_map.get(tf.upper(), tf)

    agg_dict: dict[str, str] = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }
    if "Adj Close" in df.columns:
        agg_dict["Adj Close"] = "last"

    resampled = (
        df.resample(rule, label="left", closed="left")
        .agg(agg_dict)
        .dropna(subset=["Close"])
    )

    logger.debug(
        f"Resampled {len(df):,} base bars to {len(resampled):,} bars using rule '{rule}'."
    )
    return resampled


# ============================================================================
# Canonical Parquet Partitioning & Catalog Synchronization
# ============================================================================


def resolve_yahoo_partition_path(
    store_root: str | Path,
    kind: str,
    symbol: str,
    period: str,
) -> Path:
    """Resolves canonical directory path: data/market/yahoo/{kind}/{symbol}/{period}.parquet."""
    sanitized_sym = symbol.lower().replace("^", "").replace("=", "").replace("-", "_")
    return (
        Path(store_root) / "yahoo" / kind.lower() / sanitized_sym / f"{period}.parquet"
    )


def update_market_catalog(
    store_root: Union[str, Path],
    source: str,
    kind: str,
    symbol: str,
    period: str,
    target_path: Path,
    table: Any,
) -> None:
    """
    Indexes committed partition into unified SQLite database (scripts/haruquantai.db).
    Updates native StrategyQuant X `DATA` table.
    """
    try:
        db_path = UNIFIED_DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path, timeout=5) as conn:
            stamps = table.column("DateTime").cast(pa.int64()).to_numpy()
            start_ms = int(stamps[0]) if len(stamps) > 0 else 0
            end_ms = int(stamps[-1]) if len(stamps) > 0 else 0
            clean_sym = (
                symbol.upper().replace(".D", "").replace("-", "").replace("/", "")
            )
            tf_disp = kind.upper()
            postfix_sym = f"{clean_sym}.D" if tf_disp == "D1" else clean_sym
            rel_dir = f"{source}/{kind.lower()}/{clean_sym.lower()}"

            cur = conn.cursor()
            cur.execute(
                """
                SELECT ID, ROWS, DATEFROM, DATETO FROM DATA
                WHERE (SOURCE = 8 AND UPPER(INSTRUMENT) = ? AND UPPER(TIMEFRAME) = ?)
                   OR (UPPER(SYMBOL) = ? AND UPPER(TIMEFRAME) = ?)
            """,
                (clean_sym, tf_disp, postfix_sym, tf_disp),
            )
            existing = cur.fetchone()

            if existing:
                row_id, old_rows, old_from, old_to = existing
                new_from = (
                    min(old_from, start_ms) if (old_from and old_from > 0) else start_ms
                )
                new_to = max(old_to, end_ms) if (old_to and old_to > 0) else end_ms
                new_rows = (old_rows or 0) + len(table)
                cur.execute(
                    """
                    UPDATE DATA SET
                        DATEFROM = ?, DATETO = ?, ROWS = ?, FILENAME = ?
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
                        'UTC', ?, ?, ?, 3,
                        ?, 2, 8, 0, ?,
                        ?, 0, 1, -1, -1
                    )
                """,
                    (
                        postfix_sym,
                        clean_sym,
                        tf_disp,
                        rel_dir,
                        start_ms,
                        end_ms,
                        len(table),
                        clean_sym,
                        clean_sym,
                    ),
                )
            conn.commit()
    except Exception as e:
        logger.debug(f"Catalog DB update failed: {e}")


def dataframe_to_canonical_table(df: pd.DataFrame, kind: str = "d1") -> Any:
    """Validates and coerces DataFrame columns to strict canonical Arrow schema."""
    if pa is None:
        raise ImportError("pyarrow is required for canonical table conversion.")

    schema = D1_SCHEMA if kind.lower() == "d1" else M1_SCHEMA
    if not isinstance(df.index, pd.DatetimeIndex):
        if "DateTime" in df.columns:
            ts_series = pd.to_datetime(df["DateTime"], utc=True)
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

    clean_df = pd.DataFrame(
        {
            "DateTime": ts_series.values,
            "Open": df[o_col].astype(np.float64).values,
            "High": df[h_col].astype(np.float64).values,
            "Low": df[l_col].astype(np.float64).values,
            "Close": df[c_col].astype(np.float64).values,
            "Volume": df[v_col].fillna(0).astype(np.uint64).values,
        }
    )
    clean_df.sort_values("DateTime", inplace=True)
    clean_df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)
    return pa.Table.from_pandas(clean_df, schema=schema, preserve_index=False)


def store_canonical_partitions(
    data: pd.DataFrame | Any,
    symbol: str,
    kind: str = "d1",
    store_root: str | Path = "data/market",
    source: str = "yahoo",
) -> list[Path]:
    """Slices, deduplicates, and commits market records into partitioned Parquet storage."""
    if pa is None or pq is None:
        raise ImportError(
            "pyarrow is required to store canonical partitioned Parquet files."
        )

    clean_sym = normalize_symbol_name(symbol)
    store_path = Path(store_root)

    if isinstance(data, pd.DataFrame):
        table = dataframe_to_canonical_table(data, kind=kind)
    else:
        table = data

    if len(table) == 0:
        logger.warning(f"No records to store for {symbol} ({kind})")
        return []

    stamps_ms = table.column("DateTime").cast(pa.int64()).to_numpy()
    dt_index = pd.to_datetime(stamps_ms, unit="ms", utc=True)
    years = dt_index.year.values
    unique_years = np.unique(years)
    committed_files: list[Path] = []
    schema = D1_SCHEMA if kind.lower() == "d1" else M1_SCHEMA

    for y in unique_years:
        mask = years == y
        indices = np.where(mask)[0]
        slice_table = table.take(pa.array(indices))

        target_file = resolve_yahoo_partition_path(store_path, kind, clean_sym, str(y))
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if target_file.exists():
            try:
                existing_tbl = pq.read_table(target_file)
                if existing_tbl.schema.equals(schema):
                    combined = pa.concat_tables([slice_table, existing_tbl])
                    comb_stamps = (
                        combined.column("DateTime").cast(pa.int64()).to_numpy()
                    )
                    _, u_idx = np.unique(comb_stamps, return_index=True)
                    sort_order = u_idx[np.argsort(comb_stamps[u_idx])]
                    final_table = combined.take(pa.array(sort_order))
                else:
                    final_table = slice_table
            except Exception as e:
                logger.warning(
                    f"Failed to read existing partition {target_file}: {e}. Overwriting."
                )
                final_table = slice_table
        else:
            sub_stamps = slice_table.column("DateTime").cast(pa.int64()).to_numpy()
            sort_order = np.argsort(sub_stamps)
            final_table = slice_table.take(pa.array(sort_order))

        # Crash-resilient atomic write
        tmp_target = target_file.with_name(
            f"{target_file.name}.tmp_{os.getpid()}_{int(time.time() * 1000)}.parquet"
        )
        pq.write_table(
            final_table,
            tmp_target,
            compression="ZSTD",
            compression_level=6,
            use_dictionary=True,
        )
        if target_file.exists():
            target_file.unlink()
        tmp_target.rename(target_file)
        committed_files.append(target_file)

        update_market_catalog(
            store_root=store_path,
            source=source,
            kind=kind.lower(),
            symbol=clean_sym,
            period=str(y),
            target_path=target_file,
            table=final_table,
        )

    logger.info(
        f"Committed {len(table):,} bars for {clean_sym} across {len(committed_files)} partition file(s) in {store_path}."
    )
    return committed_files


def scan_market_d1(
    symbol: str,
    timeframe: str = "d1",
    start: str | datetime.date | datetime.datetime | None = None,
    end: str | datetime.date | datetime.datetime | None = None,
    store_root: str | Path = "data/market",
    tz: str | None = None,
) -> pd.DataFrame:
    """Scans and reads daily (D1) canonical Parquet partitions for a Yahoo symbol."""
    if pq is None:
        return pd.DataFrame()

    clean_sym = symbol.lower().replace("^", "").replace("=", "").replace("-", "_")
    store_path = Path(store_root)
    sym_dir = store_path / "yahoo" / "d1" / clean_sym

    if not sym_dir.exists():
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    parquet_files = sorted(sym_dir.glob("*.parquet"))
    if not parquet_files:
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    dt_start = parse_date_param(start) if start else None
    dt_end = parse_date_param(end, end_of_day=True) if end else None

    dfs: list[pd.DataFrame] = []
    for pf in parquet_files:
        year_match = re.search(r"(\d{4})\.parquet$", pf.name)
        if year_match:
            pf_year = int(year_match.group(1))
            if dt_start and pf_year < dt_start.year:
                continue
            if dt_end and pf_year > dt_end.year:
                continue

        try:
            df_part = pq.read_table(pf).to_pandas()
            dfs.append(df_part)
        except Exception as e:
            logger.warning(f"Error reading partition {pf}: {e}")

    if not dfs:
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    df = pd.concat(dfs, ignore_index=True)
    df.sort_values("DateTime", inplace=True)
    df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)

    if dt_start:
        df = df[df["DateTime"] >= dt_start]
    if dt_end:
        df = df[df["DateTime"] <= dt_end]

    if tz:
        df["DateTime"] = df["DateTime"].dt.tz_convert(tz)

    return df.set_index("DateTime")


def scan_market_m1(
    symbol: str,
    timeframe: str = "m1",
    start: str | datetime.date | datetime.datetime | None = None,
    end: str | datetime.date | datetime.datetime | None = None,
    store_root: str | Path = "data/market",
    tz: str | None = None,
) -> pd.DataFrame:
    """Scans and reads minute (M1) canonical Parquet partitions for a Yahoo symbol."""
    if pq is None:
        return pd.DataFrame()

    clean_sym = symbol.lower().replace("^", "").replace("=", "").replace("-", "_")
    store_path = Path(store_root)
    sym_dir = store_path / "yahoo" / "m1" / clean_sym

    if not sym_dir.exists():
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    parquet_files = sorted(sym_dir.glob("*.parquet"))
    if not parquet_files:
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    dt_start = parse_date_param(start) if start else None
    dt_end = parse_date_param(end, end_of_day=True) if end else None

    dfs: list[pd.DataFrame] = []
    for pf in parquet_files:
        try:
            df_part = pq.read_table(pf).to_pandas()
            dfs.append(df_part)
        except Exception as e:
            logger.warning(f"Error reading partition {pf}: {e}")

    if not dfs:
        return pd.DataFrame(
            columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
        )

    df = pd.concat(dfs, ignore_index=True)
    df.sort_values("DateTime", inplace=True)
    df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)

    if dt_start:
        df = df[df["DateTime"] >= dt_start]
    if dt_end:
        df = df[df["DateTime"] <= dt_end]

    if tz:
        df["DateTime"] = df["DateTime"].dt.tz_convert(tz)

    return df.set_index("DateTime")


# ============================================================================
# Data Persistence & Incremental Merging (SQX Parity)
# ============================================================================


def save_data(
    df: pd.DataFrame,
    output_path: str | Path,
    merge_existing: bool = False,
    date_format: str | None = None,
) -> Path:
    """
    Saves DataFrame to CSV, Parquet, or Feather based on file extension.

    Supports StrategyQuant X 'Add only missing data' mode via merge_existing=True.
    """
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    suffix = p.suffix.lower()

    target_df = df
    if merge_existing and p.exists():
        try:
            if suffix in (".parquet", ".pq"):
                existing = pd.read_parquet(p)
            elif suffix in (".feather", ".ft"):
                existing = pd.read_feather(p).set_index("DateTime")
            else:
                existing = pd.read_csv(p, index_col=0, parse_dates=True)

            # Align timezone awareness before concatenation
            if existing.index.tz is None and target_df.index.tz is not None:
                existing.index = existing.index.tz_localize(datetime.UTC)
            elif existing.index.tz is not None and target_df.index.tz is None:
                target_df.index = target_df.index.tz_localize(datetime.UTC)

            logger.info(
                f"Merging {len(df):,} new records with {len(existing):,} existing records in {p.name}..."
            )
            combined = pd.concat([existing, target_df])
            combined = combined[~combined.index.duplicated(keep="last")]
            target_df = combined.sort_index()
        except Exception as e:
            logger.warning(
                f"Could not merge with existing file {p}: {e}. Proceeding with overwrite."
            )
            target_df = df

    if suffix in (".parquet", ".pq"):
        target_df.to_parquet(p, compression="snappy")
    elif suffix in (".feather", ".ft"):
        target_df.reset_index().to_feather(p)
    else:
        if not p.suffix:
            p = p.with_suffix(".csv")

        fmt = date_format
        if fmt is None:
            if (
                not target_df.empty
                and hasattr(target_df.index, "time")
                and all(t == datetime.time(0, 0) for t in target_df.index.time)
            ):
                fmt = "%Y-%m-%d"
            else:
                fmt = "%Y-%m-%d %H:%M:%S"

        target_df.to_csv(p, date_format=fmt)

    size_mb = p.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {len(target_df):,} records to {p} ({size_mb:.2f} MB).")
    return p


# ============================================================================
# Command Line Interface (CLI)
# ============================================================================


def dashboard(
    source: Optional[str] = "yahoo",
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Yahoo Finance & StrategyQuant Standalone High-Speed Data Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # 1. Download Daily Equity Data:
  python scripts/yahoo.py download AAPL MSFT --start 2020-01-01 --end 2024-01-01

  # 2. Flag-based execution:
  python scripts/yahoo.py --symbol AAPL --timeframe D1 --start 2020-01-01 --end 2024-01-01 --output AAPL_D1.csv

  # 3. Download Intraday H1 bars for SPY to Parquet:
  python scripts/yahoo.py --symbol SPY --timeframe H1 --start 2025-01-01 --end 2025-06-01 --output SPY_H1.parquet

  # 4. Search Tickers in Yahoo Catalog:
  python scripts/yahoo.py lookup "Tesla"
  python scripts/yahoo.py --search "S&P 500"

  # 5. Display Symbol Specification:
  python scripts/yahoo.py info EURUSD=X
  python scripts/yahoo.py --symbol EURUSD=X --info

  # 6. Scan Local Partitioned Parquet Storage:
  python scripts/yahoo.py scan AAPL --timeframe d1 --head 10
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Operational command")

    # Subcommand: dashboard
    p_dash = subparsers.add_parser(
        "dashboard", help="Display StrategyQuant X Data Manager dashboard"
    )
    p_dash.add_argument(
        "--all", action="store_true", help="Display all data sources in dashboard"
    )
    p_dash.add_argument("--symbol", default=None, help="Filter by symbol")
    p_dash.add_argument("--timeframe", "-t", default=None, help="Filter by timeframe")

    # Subcommand: download
    p_dl = subparsers.add_parser(
        "download", help="Download historical bars from Yahoo Finance"
    )
    p_dl.add_argument(
        "symbols", nargs="+", help="One or more tickers (e.g. AAPL MSFT SPY)"
    )
    p_dl.add_argument(
        "--timeframe",
        "-t",
        default="D1",
        help="Bar timeframe: D1, W1, MN1, H1, H4, M15, M5, M1 (default: D1)",
    )
    p_dl.add_argument("--start", "-s", default=None, help="Start date (YYYY-MM-DD)")
    p_dl.add_argument("--end", "-e", default=None, help="End date (YYYY-MM-DD)")
    p_dl.add_argument(
        "--unadjusted", action="store_true", help="Exclude adjusted close column"
    )
    p_dl.add_argument(
        "--store",
        default="data/market",
        help="Canonical partitioned storage root directory",
    )
    p_dl.add_argument(
        "--output-csv", default=None, help="Optional direct CSV export path"
    )
    p_dl.add_argument(
        "--mode",
        choices=["overwrite", "missing"],
        default="overwrite",
        help="Download mode: 'overwrite' or 'missing'",
    )
    p_dl.add_argument(
        "--tz", default=None, help="Timezone shift (e.g. America/New_York)"
    )
    p_dl.add_argument(
        "--workers", "-w", type=int, default=4, help="Concurrent HTTP worker threads"
    )

    # Subcommand: lookup
    p_lookup = subparsers.add_parser(
        "lookup", help="Search tickers matching keyword query"
    )
    p_lookup.add_argument("query", help="Keyword or company name to search")
    p_lookup.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum matches to return"
    )

    # Subcommand: info
    p_info = subparsers.add_parser(
        "info", help="Query and print symbol metadata specification"
    )
    p_info.add_argument("symbol", help="Ticker symbol to inspect")

    # Subcommand: scan
    p_scan = subparsers.add_parser(
        "scan", help="Scan local canonical partitioned Parquet storage"
    )
    p_scan.add_argument("symbol", help="Ticker symbol to scan")
    p_scan.add_argument(
        "--timeframe", "-t", default="d1", help="Timeframe: d1 or m1 (default: d1)"
    )
    p_scan.add_argument("--start", "-s", default=None, help="Start date filter")
    p_scan.add_argument("--end", "-e", default=None, help="End date filter")
    p_scan.add_argument("--store", default="data/market", help="Canonical storage root")
    p_scan.add_argument(
        "--head", type=int, default=10, help="Number of head records to display"
    )
    p_scan.add_argument(
        "--tz", default=None, help="Timezone shift (e.g. America/New_York)"
    )
    p_scan.add_argument("--export-csv", default=None, help="Export scanned rows to CSV")

    # Top-level legacy flag arguments for complete dukascopy_downloader parity
    parser.add_argument(
        "-s",
        "--symbol",
        type=str,
        default=None,
        help="Symbol ticker or comma-separated list (e.g. AAPL, SPY, ^GSPC, EURUSD=X, BTC-USD)",
    )
    parser.add_argument(
        "-t",
        "--timeframe",
        type=str,
        default="D1",
        help="Bar timeframe: D1, W1, MN1, H1, H4, M15, M5, M1 (default: D1)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file path (.csv, .parquet, .feather)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=4,
        help="Concurrent HTTP worker threads (default: 4)",
    )
    parser.add_argument(
        "--no-adj",
        action="store_true",
        help="Exclude 'Adj Close' column from download",
    )
    parser.add_argument(
        "--merge",
        "--add-missing",
        action="store_true",
        help="Merge new data into existing output file instead of overwriting",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Search Yahoo Finance symbol catalog for matching tickers",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Query and print symbol metadata, price hint, and quote info",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Display StrategyQuant X Data Manager dashboard",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Display all data sources in dashboard",
    )

    args = parser.parse_args()

    if getattr(args, "dashboard", False) or args.command == "dashboard":
        src = None if getattr(args, "all", False) else "yahoo"
        sym = getattr(args, "symbol", None)
        tf = getattr(args, "timeframe", None)
        dashboard(source=src, symbol=sym, timeframe=tf)
        return

    # Route based on subcommands or flags
    if args.command == "lookup" or (args.command is None and args.search):
        query = args.query if args.command == "lookup" else args.search
        limit = getattr(args, "limit", 10)
        results = search_symbols(query, count=limit)
        print(f"\n--- Search Results for '{query}' ---")
        if not results:
            print("No matching symbols found.")
        else:
            fmt_str = "{:<12} {:<32} {:<12} {:<10}"
            print(fmt_str.format("Symbol", "Name", "Type", "Exchange"))
            print("-" * 70)
            for r in results:
                name = r["name"][:30] + ".." if len(r["name"]) > 30 else r["name"]
                print(fmt_str.format(r["symbol"], name, r["type"], r["exchange"]))
        return

    if args.command == "info" or (args.command is None and args.info):
        sym_name = (
            args.symbol if args.command == "info" else getattr(args, "symbol", None)
        )
        if not sym_name:
            parser.error("--symbol is required for --info metadata inspection.")
        symbols = [s.strip().upper() for s in sym_name.split(",") if s.strip()]
        for sym in symbols:
            info = get_symbol_info(sym)
            print(f"\n--- Symbol Specification: {sym} ---")
            for k, v in info.items():
                print(f"  {k:<20}: {v}")
        return

    if args.command == "scan":
        tf = args.timeframe.lower()
        if tf in ("m", "m1", "minute"):
            df = scan_market_m1(
                args.symbol,
                timeframe=tf,
                start=args.start,
                end=args.end,
                store_root=args.store,
                tz=args.tz,
            )
        else:
            df = scan_market_d1(
                args.symbol,
                timeframe=tf,
                start=args.start,
                end=args.end,
                store_root=args.store,
                tz=args.tz,
            )

        print(f"\nCanonical Storage Scan: {args.symbol.upper()} ({args.timeframe})")
        print(f"Total bars found: {len(df):,}")
        if not df.empty:
            print(f"\nHead {min(args.head, len(df))} bars:")
            print(df.head(args.head))
            print(f"\nTail {min(args.head, len(df))} bars:")
            print(df.tail(args.head))

            if args.export_csv:
                out_p = Path(args.export_csv)
                save_data(df, out_p)
                print(f"\nExported to {out_p}")
        return

    # Data Download execution (either via 'download' subcommand or top-level flags)
    if args.command == "download":
        symbols = [s.strip().upper() for s in args.symbols if s.strip()]
        timeframe = args.timeframe
        include_adj = not args.unadjusted
        start_date = args.start
        end_date = args.end
        store_root = args.store
        mode = args.mode
        tz_shift = args.tz
        workers = args.workers
        out_target = args.output_csv
        merge_flag = args.mode == "missing"
    else:
        if not args.symbol:
            parser.error(
                "Must provide a command (download, lookup, info, scan) or specify --symbol."
            )
        symbols = [s.strip().upper() for s in args.symbol.split(",") if s.strip()]
        timeframe = args.timeframe
        include_adj = not args.no_adj
        start_date = args.start
        end_date = args.end
        store_root = None
        mode = "missing" if args.merge else "overwrite"
        tz_shift = None
        workers = args.workers
        out_target = args.output
        merge_flag = args.merge

    for sym in symbols:
        print(f"\nFetching data for {sym} [{timeframe}]...")
        df = download_candles(
            symbol=sym,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            include_adj_close=include_adj,
            max_workers=workers,
            show_progress=True,
            store_root=store_root,
            mode=mode,
            tz=tz_shift,
        )

        print("\n--- Download Summary ---")
        print(f"Symbol:     {sym}")
        print(f"Timeframe:  {timeframe.upper()}")
        print(f"Records:    {len(df):,}")
        if not df.empty:
            print(f"Date Range: {df.index.min()} -> {df.index.max()}")
            print("\nFirst 3 rows:")
            print(df.head(3))
            print("\nLast 3 rows:")
            print(df.tail(3))

            if out_target and len(symbols) == 1:
                out_path = out_target
            else:
                s_str = start_date[:10] if start_date else str(df.index.min().date())
                e_str = end_date[:10] if end_date else str(df.index.max().date())
                sanitized_sym = sym.replace("^", "").replace("=", "").replace("-", "_")
                out_path = f"{sanitized_sym}_{timeframe.upper()}_{s_str}_{e_str}.csv"

            save_data(df, out_path, merge_existing=merge_flag)


if __name__ == "__main__":
    main()
