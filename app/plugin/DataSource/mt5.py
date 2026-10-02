# ruff: noqa: INP001 -- source namespace and protocol constants
"""StrategyQuant X MetaTrader 5 (MT5) High-Performance Data Ingestion & Storage Engine.

Description:
    Provides automated downloading, calibration, process discovery, and ingestion of
    tick and OHLC bar datasets from MetaTrader 5 terminals into canonical Parquet
    partitioned storage and host-managed market data custody. Supports direct in-process
    IPC for CLI execution and bounded asynchronous execution through host capabilities.

    External relations and workflows:
    - Workspace attachment: Discovered and attached dynamically to
      `workspace.data_manager` under slot `data_source.acquisition`.
    - Host capabilities: Requires `host.market_data` (`MarketAccess`), `host.jobs`
      (`JobAccess`), and `host.terminal` (`TerminalAccess`).
    - Upstream terminal: Connects to 64-bit MetaTrader 5 terminals (installed or
    portable)
      via native IPC with automatic candidate path discovery and offline
      simulation fallback.

Purpose:
    FEAT-DM-MT5_ACQUISITION: Historical terminal data ingestion for Data Manager and
    CLI parity.

Key Capabilities:
    - FR-MT5-HISTORY:
      Acquire original broker coordinates without policy admission; log decoded rows.
    - FR-MT5-HISTORICAL-CLOCK-NORMALIZATION: Pinned verified schedules; logs
      conversion counts and fails ambiguous time mapping before publication.
    - FR-MT5-CLOCK-PROVENANCE: Row-aligned raw timestamps; host logs publication.
    - FR-MT5-HISTORY: Bounded historical reads with logged batch progress.
    - FR-MT5-PUBLISH: Immutable host custody with logged publication.
    - FR-MT5-CALIBRATION: Pip/tick/point-value calibration and broker overrides.
    - FR-MT5-CLI: Full SQX CLI parity (fetch, symbol_list, symbol_price_info,
    download, scan).
    - FR-MT5-DISCOVERY: Automatic discovery of installed broker MT5 terminals.

Python API Usage:
    >>> from app.plugin.DataSource.mt5 import download_m1, get_price_symbol_info
    >>> info = get_price_symbol_info("EURUSD")
    >>> df = download_m1("EURUSD", start="2024-01-01", end="2024-01-05")

CLI Usage:
    uv run python app/plugin/DataSource/mt5.py fetch --symbol EURUSD --output EURUSD.csv
    uv run python app/plugin/DataSource/mt5.py download EURUSD --timeframe M1
    --start 2024-01-01 --end 2024-01-05
    uv run python -m app.plugin.DataSource.mt5 symbol_list
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    repo_root = str(Path(__file__).resolve().parents[3])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

import argparse
import asyncio
import csv
import dataclasses
import datetime
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    TerminalAccess,
)
from app.host.contracts import (
    BrokerTimeProvenance,
    ClockPolicy,
    DatasetMetadata,
    DatasetMetadataDocument,
    Document,
)
from app.host.jobs import Budget
from app.host.logging import close_host_logging, configure_boot_logging, get_logger
from app.host.packages import PreparedContribution
from app.persistence.market import DefinitionRequest
from pydantic import Field, JsonValue, model_validator

# MetaTrader 5 native binding detection
MT5_AVAILABLE = False
MT5_IMPORT_ERROR: str | None = None
try:
    import MetaTrader5 as mt5  # type: ignore[import-untyped]  # noqa: N813 -- vendor module alias used by the reference API.

    MT5_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as _e:
    MT5_AVAILABLE = False
    MT5_IMPORT_ERROR = str(_e)

logger = get_logger(__name__)
UNIX_MILLISECOND_THRESHOLD = 1e11
MIN_CORRELATION_SAMPLES = 2
CFD_CALC_MODE = 2
INDEX_TICK_MIN = 0.05
INDEX_TICK_MAX = 0.5
FOREX_DECIMALS = 5
OHLC_CSV_COLUMNS = 5
TICK_CSV_COLUMNS = 3
DATE_TIME_COLUMNS = 2

# ---------------------------------------------------------------------------
# Plugin Manifest Definition
# ---------------------------------------------------------------------------
PLUGIN = {
    "id": "plugin.data_manager.meta_trader",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
        {"id": "host.terminal", "version": "1.0.0"},
    ],
}

# ---------------------------------------------------------------------------
# Canonical Storage Schemas
# ---------------------------------------------------------------------------
if pa is not None:
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

    TICK_SCHEMA = pa.schema(
        [
            pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
            pa.field("Ask", pa.int64(), nullable=False),
            pa.field("Bid", pa.int64(), nullable=False),
            pa.field("Volume", pa.uint64(), nullable=False),
        ]
    )

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
else:
    M1_SCHEMA = None
    TICK_SCHEMA = None
    D1_SCHEMA = None


MONTH_NAMES: tuple[str, ...] = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)

# ---------------------------------------------------------------------------
# Constants & MT5 Enumerations (Parity with MT5 SDK)
# ---------------------------------------------------------------------------
TIMEFRAME_M1 = 1
TIMEFRAME_M2 = 2
TIMEFRAME_M3 = 3
TIMEFRAME_M4 = 4
TIMEFRAME_M5 = 5
TIMEFRAME_M6 = 6
TIMEFRAME_M10 = 10
TIMEFRAME_M12 = 12
TIMEFRAME_M15 = 15
TIMEFRAME_M20 = 20
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H2 = 16386
TIMEFRAME_H3 = 16387
TIMEFRAME_H4 = 16388
TIMEFRAME_H6 = 16390
TIMEFRAME_H8 = 16392
TIMEFRAME_H12 = 16396
TIMEFRAME_D1 = 16408
TIMEFRAME_W1 = 32769
TIMEFRAME_MN1 = 49153

COPY_TICKS_ALL = -1
COPY_TICKS_INFO = 1
COPY_TICKS_TRADE = 2

TIMEFRAME_MAP: dict[str, int] = {
    "M1": TIMEFRAME_M1,
    "M2": TIMEFRAME_M2,
    "M3": TIMEFRAME_M3,
    "M4": TIMEFRAME_M4,
    "M5": TIMEFRAME_M5,
    "M6": TIMEFRAME_M6,
    "M10": TIMEFRAME_M10,
    "M12": TIMEFRAME_M12,
    "M15": TIMEFRAME_M15,
    "M20": TIMEFRAME_M20,
    "M30": TIMEFRAME_M30,
    "H1": TIMEFRAME_H1,
    "H2": TIMEFRAME_H2,
    "H3": TIMEFRAME_H3,
    "H4": TIMEFRAME_H4,
    "H6": TIMEFRAME_H6,
    "H8": TIMEFRAME_H8,
    "H12": TIMEFRAME_H12,
    "D1": TIMEFRAME_D1,
    "W1": TIMEFRAME_W1,
    "MN1": TIMEFRAME_MN1,
}

OVERRIDES_FILE = "mt5_symbol_overrides.json"

DEFAULT_TERMINAL_CANDIDATES: list[str] = [
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
    r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe",
    r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe",
    r"C:\Program Files\IC Markets Global MetaTrader 5\terminal64.exe",
    r"C:\Program Files\RoboForex MetaTrader 5\terminal64.exe",
    r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe",
    r"C:\Program Files\MetaQuotes\MetaTrader 5\terminal64.exe",
    r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
]


# ============================================================================
# Datetime & String Utilities
# ============================================================================


def parse_datetime_flexible(s: str | datetime.datetime | float) -> datetime.datetime:
    """Robust datetime parser handling ISO, MT4/MT5, and Unix millisecond timestamps.

    Returns naive UTC datetime.
    """
    if isinstance(s, datetime.datetime):
        if s.tzinfo is not None:
            return s.astimezone(datetime.UTC).replace(tzinfo=None)
        return s

    if isinstance(s, (int, float)):
        if s > UNIX_MILLISECOND_THRESHOLD:  # ms
            return datetime.datetime.fromtimestamp(s / 1000.0, tz=datetime.UTC).replace(
                tzinfo=None
            )
        return datetime.datetime.fromtimestamp(s, tz=datetime.UTC).replace(tzinfo=None)

    s_str = s.strip()
    if not s_str:
        raise ValueError("Empty datetime string")

    try:
        dt = datetime.datetime.fromisoformat(s_str.replace("Z", "").replace(" ", "T"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.UTC).replace(tzinfo=None)
        return dt
    except ValueError:
        logger.debug("ISO datetime parsing failed; trying source date formats")

    patterns = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M",
        "%d.%m.%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%d.%m.%Y",
        "%Y/%m/%d",
    ]
    for p in patterns:
        try:
            return (
                datetime.datetime.strptime(s_str, p)
                .replace(tzinfo=datetime.UTC)
                .replace(tzinfo=None)
            )
        except ValueError:
            logger.debug("Source datetime format did not match: %s", p)

    raise ValueError(f"Unrecognized datetime format: {s_str}")


def normalize_symbol_name(symbol: str) -> str:
    """Sanitizes symbol ticker name into standardized alphanumeric string."""
    return (
        symbol.strip()
        .upper()
        .replace("/", "")
        .replace("\\", "")
        .replace("-", "")
        .replace(".", "_")
    )


def format_iso_timestamp(dt: datetime.datetime) -> str:
    """Formats datetime to YYYY-MM-DD HH:MM:SS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_tick_timestamp(dt: datetime.datetime, ms: int = 0) -> str:
    """Formats datetime to YYYY-MM-DD HH:MM:SS.SSS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{ms:03d}"


# ============================================================================
# Statistical Math Functions
# ============================================================================


def median(values: list[float]) -> float:
    """Computes median of numeric array."""
    if not values:
        return float("nan")
    v = sorted(values)
    n = len(v)
    mid = n // 2
    if n % 2 == 1:
        return v[mid]
    return (v[mid - 1] + v[mid]) / 2.0


def quantile(values: list[float], q: float) -> float:
    """Computes linear interpolation quantile q in [0, 1]."""
    if not values:
        return float("nan")
    if q <= 0:
        return min(values)
    if q >= 1:
        return max(values)
    v = sorted(values)
    n = len(v)
    pos = (n - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return v[lo]
    frac = pos - lo
    return v[lo] * (1.0 - frac) + v[hi] * frac


def pearson_corr(xs: list[float], ys: list[float]) -> float:
    """Computes Pearson linear correlation coefficient."""
    n = min(len(xs), len(ys))
    if n < MIN_CORRELATION_SAMPLES:
        return 0.0
    xs_cut = xs[:n]
    ys_cut = ys[:n]
    mean_x = sum(xs_cut) / n
    mean_y = sum(ys_cut) / n
    num = 0.0
    den_x = 0.0
    den_y = 0.0
    for x, y in zip(xs_cut, ys_cut, strict=True):
        dx = x - mean_x
        dy = y - mean_y
        num += dx * dy
        den_x += dx * dx
        den_y += dy * dy
    if den_x <= 0 or den_y <= 0:
        return 0.0
    return num / math.sqrt(den_x * den_y)


# ============================================================================
# Built-In Fallback Symbol Master Catalog
# ============================================================================


@dataclass
class MT5SymbolSpecification:
    """Immutable-value source symbol specification for calibration and catalogs."""

    name: str
    description: str
    path: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    digits: int
    point: float
    spread: int
    # Source modes: Forex, Futures, CFD, CFD Index, CFD Leverage, Forex No Leverage.
    trade_calc_mode: int
    trade_tick_value: float
    trade_tick_size: float
    trade_contract_size: float
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    category: str = "Forex"

    def to_dict(self) -> dict[str, Any]:
        """Describe source fields and the decimal point multiplier."""
        d = asdict(self)
        d["point_multiplier"] = 10.0**self.digits
        return d


EMBEDDED_SYMBOL_CATALOG: dict[str, MT5SymbolSpecification] = {
    # Forex Majors
    "EURUSD": MT5SymbolSpecification(
        "EURUSD",
        "Euro vs US Dollar",
        "Forex-Majors",
        "EUR",
        "USD",
        "EUR",
        5,
        0.00001,
        12,
        0,
        1.0,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "GBPUSD": MT5SymbolSpecification(
        "GBPUSD",
        "Great Britain Pound vs US Dollar",
        "Forex-Majors",
        "GBP",
        "USD",
        "GBP",
        5,
        0.00001,
        15,
        0,
        1.0,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "USDJPY": MT5SymbolSpecification(
        "USDJPY",
        "US Dollar vs Japanese Yen",
        "Forex-Majors",
        "USD",
        "JPY",
        "USD",
        3,
        0.001,
        11,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "USDCHF": MT5SymbolSpecification(
        "USDCHF",
        "US Dollar vs Swiss Franc",
        "Forex-Majors",
        "USD",
        "CHF",
        "USD",
        5,
        0.00001,
        14,
        0,
        1.15,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "AUDUSD": MT5SymbolSpecification(
        "AUDUSD",
        "Australian Dollar vs US Dollar",
        "Forex-Majors",
        "AUD",
        "USD",
        "AUD",
        5,
        0.00001,
        13,
        0,
        1.0,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "NZDUSD": MT5SymbolSpecification(
        "NZDUSD",
        "New Zealand Dollar vs US Dollar",
        "Forex-Majors",
        "NZD",
        "USD",
        "NZD",
        5,
        0.00001,
        16,
        0,
        1.0,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "USDCAD": MT5SymbolSpecification(
        "USDCAD",
        "US Dollar vs Canadian Dollar",
        "Forex-Majors",
        "USD",
        "CAD",
        "USD",
        5,
        0.00001,
        15,
        0,
        0.75,
        0.00001,
        100000.0,
        category="Forex",
    ),
    # Forex Crosses
    "EURGBP": MT5SymbolSpecification(
        "EURGBP",
        "Euro vs Great Britain Pound",
        "Forex-Crosses",
        "EUR",
        "GBP",
        "EUR",
        5,
        0.00001,
        16,
        0,
        1.28,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "EURJPY": MT5SymbolSpecification(
        "EURJPY",
        "Euro vs Japanese Yen",
        "Forex-Crosses",
        "EUR",
        "JPY",
        "EUR",
        3,
        0.001,
        14,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "GBPJPY": MT5SymbolSpecification(
        "GBPJPY",
        "Great Britain Pound vs Japanese Yen",
        "Forex-Crosses",
        "GBP",
        "JPY",
        "GBP",
        3,
        0.001,
        18,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "AUDJPY": MT5SymbolSpecification(
        "AUDJPY",
        "Australian Dollar vs Japanese Yen",
        "Forex-Crosses",
        "AUD",
        "JPY",
        "AUD",
        3,
        0.001,
        15,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "CADJPY": MT5SymbolSpecification(
        "CADJPY",
        "Canadian Dollar vs Japanese Yen",
        "Forex-Crosses",
        "CAD",
        "JPY",
        "CAD",
        3,
        0.001,
        16,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "CHFJPY": MT5SymbolSpecification(
        "CHFJPY",
        "Swiss Franc vs Japanese Yen",
        "Forex-Crosses",
        "CHF",
        "JPY",
        "CHF",
        3,
        0.001,
        19,
        0,
        100.0,
        0.001,
        100000.0,
        category="Forex",
    ),
    "EURAUD": MT5SymbolSpecification(
        "EURAUD",
        "Euro vs Australian Dollar",
        "Forex-Crosses",
        "EUR",
        "AUD",
        "EUR",
        5,
        0.00001,
        18,
        0,
        0.65,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "EURCAD": MT5SymbolSpecification(
        "EURCAD",
        "Euro vs Canadian Dollar",
        "Forex-Crosses",
        "EUR",
        "CAD",
        "EUR",
        5,
        0.00001,
        19,
        0,
        0.75,
        0.00001,
        100000.0,
        category="Forex",
    ),
    "EURCHF": MT5SymbolSpecification(
        "EURCHF",
        "Euro vs Swiss Franc",
        "Forex-Crosses",
        "EUR",
        "CHF",
        "EUR",
        5,
        0.00001,
        17,
        0,
        1.15,
        0.00001,
        100000.0,
        category="Forex",
    ),
    # Metals (CFD style, pip = tick)
    "XAUUSD": MT5SymbolSpecification(
        "XAUUSD",
        "Gold vs US Dollar",
        "Metals",
        "XAU",
        "USD",
        "XAU",
        2,
        0.01,
        25,
        2,
        1.0,
        0.01,
        100.0,
        category="Metals",
    ),
    "XAGUSD": MT5SymbolSpecification(
        "XAGUSD",
        "Silver vs US Dollar",
        "Metals",
        "XAG",
        "USD",
        "XAG",
        3,
        0.001,
        20,
        2,
        5.0,
        0.001,
        5000.0,
        category="Metals",
    ),
    "XPTUSD": MT5SymbolSpecification(
        "XPTUSD",
        "Platinum vs US Dollar",
        "Metals",
        "XPT",
        "USD",
        "XPT",
        2,
        0.01,
        40,
        2,
        1.0,
        0.01,
        100.0,
        category="Metals",
    ),
    "XPDUSD": MT5SymbolSpecification(
        "XPDUSD",
        "Palladium vs US Dollar",
        "Metals",
        "XPD",
        "USD",
        "XPD",
        2,
        0.01,
        80,
        2,
        1.0,
        0.01,
        100.0,
        category="Metals",
    ),
    # Energy & Commodities
    "WTI": MT5SymbolSpecification(
        "WTI",
        "US West Texas Intermediate Crude Oil",
        "Commodities-Energy",
        "USD",
        "USD",
        "USD",
        2,
        0.01,
        4,
        2,
        10.0,
        0.01,
        1000.0,
        category="Commodities",
    ),
    "BRENT": MT5SymbolSpecification(
        "BRENT",
        "Brent Crude Oil",
        "Commodities-Energy",
        "USD",
        "USD",
        "USD",
        2,
        0.01,
        5,
        2,
        10.0,
        0.01,
        1000.0,
        category="Commodities",
    ),
    "NG": MT5SymbolSpecification(
        "NG",
        "Natural Gas",
        "Commodities-Energy",
        "USD",
        "USD",
        "USD",
        3,
        0.001,
        6,
        2,
        10.0,
        0.001,
        10000.0,
        category="Commodities",
    ),
    # Indices
    "US30": MT5SymbolSpecification(
        "US30",
        "Wall Street 30 Index (Dow Jones)",
        "Indices-US",
        "USD",
        "USD",
        "USD",
        1,
        0.1,
        25,
        2,
        0.1,
        0.1,
        1.0,
        category="Indices",
    ),
    "US500": MT5SymbolSpecification(
        "US500",
        "US SPX 500 Index (S&P 500)",
        "Indices-US",
        "USD",
        "USD",
        "USD",
        1,
        0.1,
        6,
        2,
        0.1,
        0.1,
        1.0,
        category="Indices",
    ),
    "USTEC": MT5SymbolSpecification(
        "USTEC",
        "US Tech 100 Index (NASDAQ)",
        "Indices-US",
        "USD",
        "USD",
        "USD",
        1,
        0.1,
        18,
        2,
        0.1,
        0.1,
        1.0,
        category="Indices",
    ),
    "DE40": MT5SymbolSpecification(
        "DE40",
        "Germany 40 Index (DAX)",
        "Indices-Europe",
        "EUR",
        "EUR",
        "EUR",
        1,
        0.1,
        12,
        2,
        0.1,
        0.1,
        1.0,
        category="Indices",
    ),
    "UK100": MT5SymbolSpecification(
        "UK100",
        "UK 100 Index (FTSE)",
        "Indices-Europe",
        "GBP",
        "GBP",
        "GBP",
        1,
        0.1,
        15,
        2,
        0.1,
        0.1,
        1.0,
        category="Indices",
    ),
    "JP225": MT5SymbolSpecification(
        "JP225",
        "Japan 225 Index (Nikkei)",
        "Indices-Asia",
        "JPY",
        "JPY",
        "JPY",
        0,
        1.0,
        8,
        2,
        100.0,
        1.0,
        100.0,
        category="Indices",
    ),
    # Crypto
    "BTCUSD": MT5SymbolSpecification(
        "BTCUSD",
        "Bitcoin vs US Dollar",
        "Crypto",
        "BTC",
        "USD",
        "BTC",
        2,
        0.01,
        350,
        2,
        0.01,
        0.01,
        1.0,
        category="Crypto",
    ),
    "ETHUSD": MT5SymbolSpecification(
        "ETHUSD",
        "Ethereum vs US Dollar",
        "Crypto",
        "ETH",
        "USD",
        "ETH",
        2,
        0.01,
        40,
        2,
        0.01,
        0.01,
        1.0,
        category="Crypto",
    ),
    "SOLUSD": MT5SymbolSpecification(
        "SOLUSD",
        "Solana vs US Dollar",
        "Crypto",
        "SOL",
        "USD",
        "SOL",
        2,
        0.01,
        15,
        2,
        0.01,
        0.01,
        1.0,
        category="Crypto",
    ),
    # Futures
    "@ES": MT5SymbolSpecification(
        "@ES",
        "E-Mini S&P 500 Continuous Futures",
        "Futures-Index",
        "USD",
        "USD",
        "USD",
        2,
        0.25,
        2,
        1,
        12.5,
        0.25,
        50.0,
        category="Futures",
    ),
    "@NQ": MT5SymbolSpecification(
        "@NQ",
        "E-Mini NASDAQ 100 Continuous Futures",
        "Futures-Index",
        "USD",
        "USD",
        "USD",
        2,
        0.25,
        2,
        1,
        5.0,
        0.25,
        20.0,
        category="Futures",
    ),
    "@YM": MT5SymbolSpecification(
        "@YM",
        "E-Mini Dow Continuous Futures",
        "Futures-Index",
        "USD",
        "USD",
        "USD",
        0,
        1.0,
        2,
        1,
        5.0,
        1.0,
        5.0,
        category="Futures",
    ),
    "@CL": MT5SymbolSpecification(
        "@CL",
        "Crude Oil Continuous Futures",
        "Futures-Commodity",
        "USD",
        "USD",
        "USD",
        2,
        0.01,
        2,
        1,
        10.0,
        0.01,
        1000.0,
        category="Futures",
    ),
    "@GC": MT5SymbolSpecification(
        "@GC",
        "Gold Continuous Futures",
        "Futures-Commodity",
        "USD",
        "USD",
        "USD",
        1,
        0.1,
        2,
        1,
        10.0,
        0.1,
        100.0,
        category="Futures",
    ),
}

DEFAULT_EMBEDDED_OVERRIDES: dict[str, Any] = {
    "*": {},
    "RoboForex-*": {},
    "Darwinex-*": {
        "WS30": {
            "point_value": 1.0,
            "currency": "USD",
            "note": "Darwinex MT5 tick_value=0.1 is inconsistent with contract_size=1; "
            "actual P&L matches contract_size convention ($1/point)",
        }
    },
    "AMPGlobalUSA-*": {
        "@DB": {
            "tick_size": 0.01,
            "tick_step": 0.01,
            "point_value": 1000,
            "currency": "EUR",
            "note": "Euro Bund 10yr - Eurex spec: 1000 EUR per 1.00 price move",
        },
        "@MES": {
            "spread": 2,
            "note": "Micro E-mini S&P 500 ($5/pt) - typical spread 1-2 ticks",
        },
        "@ES": {
            "spread": 2,
            "note": "E-mini S&P 500 ($50/pt) - typical spread 1-2 ticks",
        },
        "@MNQ": {
            "spread": 2,
            "note": "Micro E-mini Nasdaq 100 ($2/pt) - typical spread 1-2 ticks",
        },
        "@NQ": {
            "spread": 2,
            "note": "E-mini Nasdaq 100 ($20/pt) - typical spread 1-2 ticks",
        },
        "@MYM": {
            "spread": 2,
            "note": "Micro E-mini Dow ($0.50/pt) - typical spread 1-2 ticks",
        },
        "@YM": {"spread": 2, "note": "E-mini Dow ($5/pt) - typical spread 1-2 ticks"},
        "@CL": {
            "spread": 2,
            "note": "WTI Crude Oil futures - typical spread 1-2 ticks",
        },
        "@GC": {"spread": 2, "note": "Gold futures - typical spread 1-2 ticks"},
        "@SI": {"spread": 2, "note": "Silver futures - typical spread 1-2 ticks"},
        "@ZB": {
            "spread": 2,
            "note": "30Y US Treasury Bond futures (1/32 tick) - "
            "typical spread 1-2 ticks",
        },
    },
}


def load_overrides(custom_path: str | Path | None = None) -> dict[str, Any]:
    """Load broker/symbol JSON overrides or embedded defaults."""
    candidate_paths: list[Path] = []
    if custom_path:
        candidate_paths.append(Path(custom_path))
    candidate_paths.extend(
        [
            Path(__file__).parent / OVERRIDES_FILE,
            Path("scripts") / OVERRIDES_FILE,
            Path(r"C:\SQX\internal\python\scripts") / OVERRIDES_FILE,
        ]
    )

    for path in candidate_paths:
        if path.exists():
            try:
                with Path(path).open(encoding="utf-8") as f:
                    data = json.load(f)
                return {k: v for k, v in data.items() if not k.startswith("_")}
            except (OSError, ValueError, AttributeError) as e:
                logger.debug("Failed to load overrides from %s: %s", path, e)

    return DEFAULT_EMBEDDED_OVERRIDES.copy()


def resolve_override(  # noqa: C901 -- cohesive source conversion or bounded operation dispatch.
    overrides: dict[str, Any], server: str, company: str, symbol: str
) -> tuple[dict[str, Any], str | None]:
    """Resolves symbol overrides following SQX priority hierarchy."""

    def _wildcard_keys(target: str) -> list[str]:
        if not target:
            return []
        matches = []
        for key in overrides:
            if key.endswith("*") and len(key) > 1:
                prefix = key[:-1]
                if target.startswith(prefix):
                    matches.append(key)
        matches.sort(key=len, reverse=True)
        return matches

    candidates: list[str] = []
    if server:
        candidates.append(server)
        candidates.extend(_wildcard_keys(server))
    if company:
        candidates.append(company)
        candidates.extend(_wildcard_keys(company))
    candidates.append("*")

    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)

    clean_sym = symbol.strip()
    for broker_key in ordered:
        if broker_key not in overrides:
            continue
        broker_overrides = overrides[broker_key]
        if clean_sym in broker_overrides:
            return broker_overrides[clean_sym], broker_key

    return {}, None


# ============================================================================
# Direct MT5 IPC Fetcher (`MT5Fetcher`)
# ============================================================================


class MT5Fetcher:
    """Manages MetaTrader 5 terminal process connections, symbol discovery,

    price property calibration, and chunked history streaming.
    Provides 100% protocol and behavioral parity with SQX MT5Fetcher.
    """

    DEFAULT_FETCH_START = datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC)
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.connected: bool = False
        self.active_terminal_path: str | None = None
        self.active_server: str = ""
        self.active_company: str = ""
        self.is_simulation: bool = False

    def auto_discover_terminal(self) -> str | None:
        """Scans filesystem to find an installed 64-bit MT5 terminal."""
        for candidate in DEFAULT_TERMINAL_CANDIDATES:
            if Path(candidate).exists():
                return candidate
        return None

    def connect(  # noqa: C901, PLR0917, PLR0911 -- cohesive source conversion or bounded operation dispatch; retain reference positional-call compatibility; preserve explicit reference fallback and command exits.
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        path: str | None = None,
        portable: bool = False,
        allow_simulation: bool = True,
    ) -> bool:
        """Initializes connection to MT5 terminal instance."""
        with self._lock:
            if self.connected:
                return True

            if not MT5_AVAILABLE or mt5 is None:
                if allow_simulation:
                    logger.warning(
                        "MetaTrader5 C-extension unavailable or restricted. "
                        "Operating in simulated/catalog mode."
                    )
                    self.is_simulation = True
                    self.connected = True
                    return True
                print(
                    "SQERROR: MetaTrader5 library not installed "
                    "or not supported on this OS.",
                    flush=True,
                )
                return False

            init_args: dict[str, Any] = {}
            target_path = path or self.auto_discover_terminal()
            if target_path:
                init_args["path"] = target_path
                self.active_terminal_path = target_path
            if portable:
                init_args["portable"] = True

            try:
                if not mt5.initialize(**init_args):
                    err = mt5.last_error()
                    logger.warning(
                        "MT5 initialize returned error %s. "
                        "Falling back to simulation mode.",
                        err,
                    )
                    if allow_simulation:
                        self.is_simulation = True
                        self.connected = True
                        return True
                    print(
                        f"SQERROR: MT5 initialize failed, error code = {err}",
                        flush=True,
                    )
                    return False

                if login and password and server:
                    authorized = mt5.login(
                        login=login, password=password, server=server
                    )
                    if not authorized:
                        err = mt5.last_error()
                        print(
                            f"SQERROR: failed to connect at account #{login}, "
                            f"error code: {err}",
                            flush=True,
                        )
                        mt5.shutdown()
                        return False

                term_info = mt5.terminal_info()
                acc_info = mt5.account_info()
                if acc_info:
                    self.active_server = getattr(acc_info, "server", "")
                    self.active_company = getattr(acc_info, "company", "")

                self.connected = True
                print(f"Connected to MT5: {term_info}", flush=True)
                return True
            except Exception as e:  # noqa: BLE001 -- native IPC boundary preserves the logged reference fallback.
                logger.warning(
                    "Exception during MT5 connection: %s. Falling back to simulation.",
                    e,
                )
                if allow_simulation:
                    self.is_simulation = True
                    self.connected = True
                    return True
                print(f"SQERROR: MT5 connection exception: {e}", flush=True)
                return False

    def shutdown(self) -> None:
        """Shuts down MT5 IPC connection."""
        with self._lock:
            if (
                self.connected
                and not self.is_simulation
                and MT5_AVAILABLE
                and mt5 is not None
            ):
                try:
                    mt5.shutdown()
                except Exception as error:  # noqa: BLE001 -- native binding cleanup must preserve terminal state reset.
                    logger.warning("MT5 shutdown failed: %s", type(error).__name__)
            self.connected = False
            self.is_simulation = False

    @staticmethod
    def _normalize_utc_datetime(value: Any) -> datetime.datetime:
        """Coerces any date input into a timezone-aware UTC datetime."""
        if isinstance(value, datetime.datetime):
            dt = value
        else:
            dt = parse_datetime_flexible(str(value))

        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.UTC)
        return dt.astimezone(datetime.UTC)

    @staticmethod
    def _timeframe_step(timeframe_str: str) -> datetime.timedelta:
        """Resolves bar duration timedelta for date stepping."""
        steps = {
            "M1": datetime.timedelta(minutes=1),
            "M2": datetime.timedelta(minutes=2),
            "M3": datetime.timedelta(minutes=3),
            "M4": datetime.timedelta(minutes=4),
            "M5": datetime.timedelta(minutes=5),
            "M6": datetime.timedelta(minutes=6),
            "M10": datetime.timedelta(minutes=10),
            "M12": datetime.timedelta(minutes=12),
            "M15": datetime.timedelta(minutes=15),
            "M20": datetime.timedelta(minutes=20),
            "M30": datetime.timedelta(minutes=30),
            "H1": datetime.timedelta(hours=1),
            "H2": datetime.timedelta(hours=2),
            "H3": datetime.timedelta(hours=3),
            "H4": datetime.timedelta(hours=4),
            "H6": datetime.timedelta(hours=6),
            "H8": datetime.timedelta(hours=8),
            "H12": datetime.timedelta(hours=12),
            "D1": datetime.timedelta(days=1),
            "W1": datetime.timedelta(days=7),
            "MN1": datetime.timedelta(days=30),
        }
        return steps.get(timeframe_str.upper(), datetime.timedelta(minutes=1))

    @staticmethod
    def _default_chunk_delta(data_type: str, timeframe_str: str) -> datetime.timedelta:
        """Resolves optimal batch acquisition window size."""
        if data_type.lower() == "ticks":
            return datetime.timedelta(days=1)

        chunk_days_map = {
            "M1": 30,
            "M2": 45,
            "M3": 60,
            "M4": 75,
            "M5": 90,
            "M6": 120,
            "M10": 150,
            "M12": 160,
            "M15": 180,
            "M20": 240,
            "M30": 365,
            "H1": 730,
            "H2": 1460,
            "H3": 2190,
            "H4": 3650,
            "H6": 3650,
            "H8": 3650,
            "H12": 3650,
            "D1": 3650,
            "W1": 7300,
            "MN1": 7300,
        }
        return datetime.timedelta(days=chunk_days_map.get(timeframe_str.upper(), 30))

    @staticmethod
    def _calculate_date_progress(
        current_date: datetime.datetime,
        range_start: datetime.datetime,
        range_end: datetime.datetime,
    ) -> float:
        """Computes completion percentage strictly bounded within [0.0, 1.0]."""
        total_sec = (range_end - range_start).total_seconds()
        if total_sec <= 0:
            return 1.0
        cur_sec = (current_date - range_start).total_seconds()
        return min(1.0, max(0.0, cur_sec / total_sec))

    def get_symbols(self) -> list[dict[str, Any]]:
        """Retrieves all available MT5 symbols as a list of dictionaries."""
        if not self.connected and not self.connect():
            return []

        if self.is_simulation or not MT5_AVAILABLE or mt5 is None:
            return [spec.to_dict() for spec in EMBEDDED_SYMBOL_CATALOG.values()]

        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                print(
                    f"SQERROR: Failed to get symbols. Error: {mt5.last_error()}",
                    flush=True,
                )
                return []

            results = []
            for s in symbols:
                item = s._asdict()
                raw_path = item.get("path", "")
                last_slash = raw_path.rfind("\\")
                if last_slash >= 0:
                    category_path = raw_path[:last_slash].replace("\\", "-")
                else:
                    category_path = raw_path.replace("\\", "-")
                item["category"] = category_path
                item["path"] = category_path
                results.append(item)
            return results
        except Exception as e:  # noqa: BLE001 -- native IPC boundary preserves the logged reference fallback.
            logger.warning("Error fetching live symbols from MT5: %s", e)
            return [s.to_dict() for s in EMBEDDED_SYMBOL_CATALOG.values()]

    def get_symbol_info(self, symbol: str) -> dict[str, Any] | None:  # noqa: PLR0911 -- preserve explicit reference fallback and command exits.
        """Retrieves raw MT5 symbol_info metadata."""
        if not self.connected and not self.connect():
            return None

        clean_sym = symbol.strip().upper()
        if self.is_simulation or not MT5_AVAILABLE or mt5 is None:
            if clean_sym in EMBEDDED_SYMBOL_CATALOG:
                return EMBEDDED_SYMBOL_CATALOG[clean_sym].to_dict()
            digits = 3 if clean_sym.endswith("JPY") else 5
            return MT5SymbolSpecification(
                clean_sym,
                clean_sym,
                "Inferred",
                "USD",
                "USD",
                "USD",
                digits,
                round(10.0 ** (-digits), digits),
                15,
                0,
                1.0,
                round(10.0 ** (-digits), digits),
                100000.0,
            ).to_dict()

        try:
            mt5.symbol_select(clean_sym, True)
            info = mt5.symbol_info(clean_sym)
            if info is None:
                info = mt5.symbol_info(symbol.strip())
            if info is None:
                if clean_sym in EMBEDDED_SYMBOL_CATALOG:
                    return EMBEDDED_SYMBOL_CATALOG[clean_sym].to_dict()
                print(
                    f"SQERROR: Failed to get info for {symbol}. "
                    f"Error: {mt5.last_error()}",
                    flush=True,
                )
                return None
            return cast("dict[str, Any]", info._asdict())
        except Exception as e:  # noqa: BLE001 -- native IPC boundary preserves the logged reference fallback.
            logger.warning("Error reading symbol_info for %s: %s", symbol, e)
            if clean_sym in EMBEDDED_SYMBOL_CATALOG:
                return EMBEDDED_SYMBOL_CATALOG[clean_sym].to_dict()
            return None

    def get_price_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Calculates exact pip size, tick step, point value, and normalized spread."""
        info = self.get_symbol_info(symbol)
        clean_sym = symbol.strip().upper()

        if not info:
            digits = 3 if clean_sym.endswith("JPY") else 5
            tick_step = round(10.0 ** (-digits), digits)
            ticks_per_pip = 10 if digits in (3, 5) else 1
            tick_size = tick_step * ticks_per_pip
            res = {
                "tick_step": tick_step,
                "tick_size": tick_size,
                "point_value": 1.0,
                "spread": 1.5,
            }
            print(f"SQRESULT:{json.dumps(res)}", flush=True)
            return res

        digits = int(info.get("digits", 0))
        calc_mode = int(info.get("trade_calc_mode", -1))
        trade_tick_size = float(info.get("trade_tick_size", 0.0))
        trade_tick_value = float(info.get("trade_tick_value", 0.0))
        currency_base = str(info.get("currency_base", ""))
        spread_raw = float(info.get("spread", 0))

        if trade_tick_size > 0:
            tick_step = trade_tick_size
        else:
            tick_step = round(10.0 ** (-digits), digits) if digits > 0 else 1.0

        is_metal = currency_base in ("XAU", "XAG", "XPT", "XPD") or any(
            m in clean_sym for m in ("XAU", "XAG", "XPT", "XPD", "GOLD", "SILVER")
        )
        is_forex = calc_mode in (0, 5) and not is_metal
        is_fractional_pip = is_forex and digits in (3, 5)
        ticks_per_pip = 10 if is_fractional_pip else 1

        tick_size = tick_step * ticks_per_pip

        point_value = trade_tick_value / trade_tick_size if trade_tick_size > 0 else 0.0

        is_index_cfd = (
            calc_mode == CFD_CALC_MODE
            and digits == 1
            and INDEX_TICK_MIN < tick_step < INDEX_TICK_MAX
        )
        if is_index_cfd:
            spread = spread_raw * tick_step
        elif tick_size > 0:
            spread = spread_raw * tick_step / tick_size
        else:
            spread = float(spread_raw)

        overrides = load_overrides()
        server = self.active_server
        company = self.active_company
        ov, ov_key = resolve_override(overrides, server, company, clean_sym)
        if ov:
            print(
                f"SQMESSAGE: Override applied for {clean_sym} "
                f"(broker key: {ov_key}): {ov}",
                flush=True,
            )
            if "tick_step" in ov:
                tick_step = float(ov["tick_step"])
            if "tick_size" in ov:
                tick_size = float(ov["tick_size"])
            if "point_value" in ov:
                point_value = float(ov["point_value"])
            if "spread" in ov:
                spread = float(ov["spread"])

        result = {
            "tick_step": tick_step,
            "tick_size": tick_size,
            "point_value": round(point_value, 6),
            "spread": round(spread, 6),
        }
        print(f"SQRESULT:{json.dumps(result)}", flush=True)
        return result

    def get_data(  # noqa: C901, PLR0912 -- cohesive source conversion or bounded operation dispatch.
        self,
        symbol: str,
        timeframe_str: str = "M1",
        data_type: str = "ohlc",
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieves historical records for a specified date range."""
        if not self.connected and not self.connect():
            return []

        utc_to = (
            self._normalize_utc_datetime(end_date)
            if end_date
            else datetime.datetime.now(datetime.UTC)
        )
        utc_from = (
            self._normalize_utc_datetime(start_date)
            if start_date
            else self.DEFAULT_FETCH_START
        )

        if utc_from >= utc_to:
            print(
                f"SQMESSAGE: Invalid fetch range for {symbol}: {utc_from} -> {utc_to}",
                flush=True,
            )
            return []

        clean_sym = symbol.strip().upper()

        if self.is_simulation or not MT5_AVAILABLE or mt5 is None:
            return self._generate_synthetic_data(
                clean_sym, timeframe_str, data_type, utc_from, utc_to
            )

        try:
            mt5.symbol_select(clean_sym, True)
            if data_type.lower() == "ticks":
                flags = COPY_TICKS_ALL
                rates = mt5.copy_ticks_range(clean_sym, utc_from, utc_to, flags)
            else:
                tf_const = TIMEFRAME_MAP.get(timeframe_str.upper(), TIMEFRAME_M1)
                rates = mt5.copy_rates_range(clean_sym, tf_const, utc_from, utc_to)

            if rates is None or len(rates) == 0:
                return []

            rows: list[dict[str, Any]] = []
            if data_type.lower() == "ticks":
                last_bid = 0.0
                last_ask = 0.0
                for r in rates:
                    time_msc = (
                        int(r["time_msc"])
                        if "time_msc" in r.dtype.names
                        else int(r["time"]) * 1000
                    )
                    ms = time_msc % 1000
                    dt = datetime.datetime.fromtimestamp(
                        time_msc / 1000.0, tz=datetime.UTC
                    )
                    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{ms:03d}"

                    bid = float(r["bid"])
                    ask = float(r["ask"])
                    if bid > 0:
                        last_bid = bid
                    else:
                        bid = last_bid
                    if ask > 0:
                        last_ask = ask
                    else:
                        ask = last_ask

                    row = {
                        "time": dt_str,
                        "bid": bid,
                        "ask": ask,
                        "flags": int(r["flags"]) if "flags" in r.dtype.names else 0,
                        "volume": float(r["volume"])
                        if "volume" in r.dtype.names
                        else 0.0,
                        "spread": ask - bid,
                    }
                    rows.append(row)
            else:
                for r in rates:
                    dt = datetime.datetime.fromtimestamp(
                        int(r["time"]), tz=datetime.UTC
                    )
                    row = {
                        "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(r["open"]),
                        "high": float(r["high"]),
                        "low": float(r["low"]),
                        "close": float(r["close"]),
                        "tick_volume": float(r["tick_volume"])
                        if "tick_volume" in r.dtype.names
                        else 0.0,
                        "spread": float(r["spread"])
                        if "spread" in r.dtype.names
                        else 0.0,
                        "real_volume": float(r["real_volume"])
                        if "real_volume" in r.dtype.names
                        else 0.0,
                    }
                    rows.append(row)

            return rows
        except Exception as e:  # noqa: BLE001 -- native IPC boundary preserves the logged reference fallback.
            logger.warning("Error calling MT5 copy data for %s: %s", symbol, e)
            return self._generate_synthetic_data(
                clean_sym, timeframe_str, data_type, utc_from, utc_to
            )

    def iter_data_batches(
        self,
        symbol: str,
        timeframe_str: str = "M1",
        data_type: str = "ohlc",
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> Iterator[list[dict[str, Any]]]:
        """Paginates data acquisition into safe date windows, reporting progress."""
        utc_to = (
            self._normalize_utc_datetime(end_date)
            if end_date
            else datetime.datetime.now(datetime.UTC)
        )
        cursor = (
            self._normalize_utc_datetime(start_date)
            if start_date
            else self.DEFAULT_FETCH_START
        )

        if cursor >= utc_to:
            print(
                f"SQMESSAGE: Nothing to fetch for {symbol}; "
                "start is not earlier than end.",
                flush=True,
            )
            return

        chunk_delta = self._default_chunk_delta(data_type, timeframe_str)
        step = (
            datetime.timedelta(milliseconds=1)
            if data_type.lower() == "ticks"
            else self._timeframe_step(timeframe_str)
        )
        range_start = cursor
        range_end = utc_to

        while cursor < utc_to:
            batch_end = min(cursor + chunk_delta, utc_to)
            print(f"SQMESSAGE: Fetching {cursor.strftime('%Y-%m-%d')}", flush=True)
            print(
                f"SQPROGRESS: "
                f"{self._calculate_date_progress(cursor, range_start, range_end):.2f}",
                flush=True,
            )

            rows = self.get_data(
                symbol=symbol,
                timeframe_str=timeframe_str,
                data_type=data_type,
                start_date=cursor,
                end_date=batch_end,
            )

            if rows:
                yield rows
                last_time = parse_datetime_flexible(rows[-1]["time"])
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=datetime.UTC)
                next_cursor = last_time + step
                if next_cursor <= cursor:
                    next_cursor = batch_end
                cursor = next_cursor
            else:
                cursor = batch_end

            print(
                f"SQPROGRESS: "
                f"{self._calculate_date_progress(cursor, range_start, range_end):.2f}",
                flush=True,
            )

        print("SQPROGRESS: 1.00", flush=True)

    def _generate_synthetic_data(
        self,
        symbol: str,
        timeframe_str: str,
        data_type: str,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
    ) -> list[dict[str, Any]]:
        """Generates realistic synthetic OHLC or Tick data in simulated/offline mode."""
        spec = EMBEDDED_SYMBOL_CATALOG.get(symbol)
        base_price = (
            1.08500 if "EUR" in symbol else (150.00 if "JPY" in symbol else 2000.0)
        )
        decimals = spec.digits if spec else 5

        cur = start_dt
        step = self._timeframe_step(timeframe_str)
        rows: list[dict[str, Any]] = []
        max_rows = 1000

        rng_seed = int(
            hashlib.md5(
                f"{symbol}{start_dt}".encode(), usedforsecurity=False
            ).hexdigest()[:8],
            16,
        )
        state_price = base_price

        if data_type.lower() == "ticks":
            tick_step = datetime.timedelta(seconds=2)
            while cur < end_dt and len(rows) < max_rows:
                rng_seed = (rng_seed * 1103515245 + 12345) & 0x7FFFFFFF
                delta = ((rng_seed % 21) - 10) * (10.0 ** (-decimals))
                state_price = max(0.0001, state_price + delta)
                spread = 0.00012 if decimals == FOREX_DECIMALS else 0.02
                bid = round(state_price, decimals)
                ask = round(state_price + spread, decimals)
                ms = rng_seed % 1000
                dt_str = cur.strftime("%Y-%m-%d %H:%M:%S.") + f"{ms:03d}"
                rows.append(
                    {
                        "time": dt_str,
                        "bid": bid,
                        "ask": ask,
                        "flags": 6,
                        "volume": float((rng_seed % 10) + 1),
                        "spread": spread,
                    }
                )
                cur += tick_step
        else:
            while cur < end_dt and len(rows) < max_rows:
                rng_seed = (rng_seed * 1103515245 + 12345) & 0x7FFFFFFF
                delta_o = ((rng_seed % 21) - 10) * (10.0 ** (-decimals))
                o = round(state_price + delta_o, decimals)
                rng_seed = (rng_seed * 1103515245 + 12345) & 0x7FFFFFFF
                h = round(o + (rng_seed % 15) * (10.0 ** (-decimals)), decimals)
                rng_seed = (rng_seed * 1103515245 + 12345) & 0x7FFFFFFF
                low = round(o - (rng_seed % 15) * (10.0 ** (-decimals)), decimals)
                rng_seed = (rng_seed * 1103515245 + 12345) & 0x7FFFFFFF
                c = round(low + ((h - low) * (rng_seed % 100) / 100.0), decimals)
                vol = float((rng_seed % 500) + 50)
                state_price = c

                rows.append(
                    {
                        "time": cur.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": o,
                        "high": h,
                        "low": low,
                        "close": c,
                        "tick_volume": vol,
                        "spread": 12.0,
                        "real_volume": 0.0,
                    }
                )
                cur += step

        return rows


# ============================================================================
# CSV Dict Writer
# ============================================================================


def write_csv_dicts(
    path: str | Path,
    rows: list[dict[str, Any]],
    header: bool = True,
    append: bool = False,
) -> None:
    """Streams rows to CSV file with deterministic header layout."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No rows to write")

    fieldnames = list(rows[0].keys())
    write_header = header and (
        not append or not out.exists() or out.stat().st_size == 0
    )
    mode = "a" if append else "w"
    with Path(out).open(mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerows(rows)


# ============================================================================
# Vectorized Resampling Engine
# ============================================================================


def ticks_to_m1(ticks: list[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:  # noqa: C901, PLR0912 -- cohesive source conversion or bounded operation dispatch.
    """Synthesizes standardized 1-minute OHLCV candles directly from tick streams."""
    if pd is None:
        raise ImportError("pandas is required for resampling.")

    if isinstance(ticks, list):
        if not ticks:
            return pd.DataFrame(
                columns=["DateTime", "Open", "High", "Low", "Close", "Volume"]
            )
        df = pd.DataFrame(ticks)
    else:
        df = ticks.copy()

    time_col = None
    for c in ["time", "DateTime", "datetime", "Date & Time"]:
        if c in df.columns:
            time_col = c
            break

    if time_col is not None:
        df["DateTime"] = pd.to_datetime(df[time_col], utc=True)
        df.set_index("DateTime", inplace=True)
    elif not isinstance(df.index, pd.DatetimeIndex):
        raise KeyError("Ticks input missing timestamp column or DatetimeIndex")

    if "bid" in df.columns and "ask" in df.columns:
        price_series = df["bid"].astype(np.float64)
    elif "price" in df.columns:
        price_series = df["price"].astype(np.float64)
    elif "bid" in df.columns:
        price_series = df["bid"].astype(np.float64)
    elif "ask" in df.columns:
        price_series = df["ask"].astype(np.float64)
    else:
        raise KeyError("Tick data requires 'bid' or 'ask' price columns")

    vol_series = (
        df["volume"].astype(np.float64)
        if "volume" in df.columns
        else pd.Series(1.0, index=df.index)
    )

    ohlc = price_series.resample("1min").ohlc()
    vol = vol_series.resample("1min").sum().fillna(0).astype(np.uint64)

    ohlc.dropna(subset=["open"], inplace=True)
    ohlc["Volume"] = vol.reindex(ohlc.index).fillna(0).astype(np.uint64)

    ohlc.reset_index(inplace=True)
    ohlc.rename(
        columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"},
        inplace=True,
    )
    return ohlc


def resample_candles(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    """Resample M1 candles to higher minute, hour, day, week or month timeframes."""
    if pd is None:
        raise ImportError("pandas is required for resampling.")

    tf_rule_map = {
        "M1": "1min",
        "M2": "2min",
        "M3": "3min",
        "M4": "4min",
        "M5": "5min",
        "M6": "6min",
        "M10": "10min",
        "M12": "12min",
        "M15": "15min",
        "M20": "20min",
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
    rule = tf_rule_map.get(target_timeframe.upper(), target_timeframe)

    work = df.copy()
    time_col = None
    for c in ["DateTime", "time", "datetime", "Date & Time"]:
        if c in work.columns:
            time_col = c
            break

    if time_col is not None:
        work["DateTime"] = pd.to_datetime(work[time_col], utc=True)
        work.set_index("DateTime", inplace=True)
    elif not isinstance(work.index, pd.DatetimeIndex):
        raise KeyError("Candles input missing timestamp column or DatetimeIndex")

    col_map = {c.lower(): c for c in work.columns}
    o_col = col_map.get("open", "Open")
    h_col = col_map.get("high", "High")
    l_col = col_map.get("low", "Low")
    c_col = col_map.get("close", "Close")
    v_col = col_map.get("volume", col_map.get("tick_volume", "Volume"))

    res = pd.DataFrame()
    res["Open"] = work[o_col].resample(rule).first()
    res["High"] = work[h_col].resample(rule).max()
    res["Low"] = work[l_col].resample(rule).min()
    res["Close"] = work[c_col].resample(rule).last()
    res["Volume"] = work[v_col].resample(rule).sum().fillna(0).astype(np.uint64)

    res.dropna(subset=["Open"], inplace=True)
    res.reset_index(inplace=True)
    return res


# ============================================================================
# Canonical Parquet Partitioning & Catalog Database Storage
# ============================================================================


def resolve_market_partition_path(
    store_root: str | Path,
    source: str,
    kind: str,
    symbol: str,
    period: str,
) -> Path:
    """Resolves canonical on-disk partitioned filepath for market datasets."""
    clean_sym = normalize_symbol_name(symbol).lower()
    root = Path(store_root)
    kind_lower = kind.lower()

    if kind_lower == "ticks":
        parts = period.split("-")
        year = parts[0]
        m_int = int(parts[1]) if len(parts) > 1 else 1
        m_name = MONTH_NAMES[m_int - 1]
        return (
            root / source / "ticks" / clean_sym / year / f"{m_int:02d}-{m_name}.parquet"
        )
    return root / source / kind_lower / clean_sym / f"{period}.parquet"


def update_market_catalog(  # noqa: PLR0917 -- retain reference positional-call compatibility.
    store_root: str | Path,  # noqa: ARG001 -- retain reference adapter keyword compatibility.
    source: str,  # noqa: ARG001
    kind: str,  # noqa: ARG001
    symbol: str,  # noqa: ARG001
    period: str,  # noqa: ARG001
    target_path: Path,  # noqa: ARG001
    table: Any,  # noqa: ARG001
) -> None:
    """Retains positional signature; cataloging is owned by host capabilities."""
    logger.debug("Partition cataloging handled via host capability")


def dataframe_to_canonical_table(df: pd.DataFrame, kind: str = "m1") -> Any:
    """Converts DataFrame to canonical PyArrow Table with strict typing."""
    if pa is None:
        raise ImportError("pyarrow is required for canonical table conversion.")

    schema = TICK_SCHEMA if kind.lower() == "ticks" else M1_SCHEMA

    time_col = None
    for c in ["DateTime", "time", "datetime", "Date & Time"]:
        if c in df.columns:
            time_col = c
            break

    if time_col is not None:
        ts_series = pd.to_datetime(df[time_col], utc=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        ts_series = pd.to_datetime(df.index, utc=True)
    else:
        raise KeyError("Dataset missing 'DateTime' column or DatetimeIndex")

    col_map = {c.lower(): c for c in df.columns}

    if kind.lower() == "ticks":
        ask_col = col_map.get("ask", "Ask")
        bid_col = col_map.get("bid", "Bid")
        v_col = col_map.get("volume", "Volume")

        ask_vals = (
            (df[ask_col].astype(np.float64) * 1_000_000.0)
            .round()
            .astype(np.int64)
            .values
        )
        bid_vals = (
            (df[bid_col].astype(np.float64) * 1_000_000.0)
            .round()
            .astype(np.int64)
            .values
        )
        v_vals = (
            df[v_col].fillna(0).astype(np.float64).round().astype(np.uint64).values
            if v_col in df.columns
            else np.ones(len(df), dtype=np.uint64)
        )

        clean_df = pd.DataFrame(
            {
                "DateTime": ts_series.values,
                "Ask": ask_vals,
                "Bid": bid_vals,
                "Volume": v_vals,
            }
        )
    else:
        o_col = col_map.get("open", "Open")
        h_col = col_map.get("high", "High")
        l_col = col_map.get("low", "Low")
        c_col = col_map.get("close", "Close")
        v_col = col_map.get("volume", col_map.get("tick_volume", "Volume"))

        o_vals = df[o_col].astype(np.float64).values
        h_vals = df[h_col].astype(np.float64).values
        l_vals = df[l_col].astype(np.float64).values
        c_vals = df[c_col].astype(np.float64).values
        v_vals = (
            df[v_col].fillna(0).astype(np.float64).round().astype(np.uint64).values
            if v_col in df.columns
            else np.zeros(len(df), dtype=np.uint64)
        )

        clean_df = pd.DataFrame(
            {
                "DateTime": ts_series.values,
                "Open": o_vals,
                "High": h_vals,
                "Low": l_vals,
                "Close": c_vals,
                "Volume": v_vals,
            }
        )

    clean_df.sort_values("DateTime", inplace=True)
    clean_df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)
    return pa.Table.from_pandas(clean_df, schema=schema, preserve_index=False)


def store_canonical_partitions(  # noqa: C901, PLR0912, PLR0915 -- cohesive source conversion or bounded operation dispatch; keep each source workflow and its failure handling together.
    data: pd.DataFrame | Any,
    symbol: str,
    kind: str = "m1",
    store_root: str | Path = "data/market",
    source: str = "mt5",
) -> list[Path]:
    """Slice, deduplicate and store MT5 records in partitioned Parquet."""
    if pa is None or pq is None:
        raise ImportError(
            "pyarrow is required to store canonical partitioned Parquet files."
        )

    store_path = Path(store_root)
    clean_sym = normalize_symbol_name(symbol)

    if isinstance(data, pd.DataFrame):
        table = dataframe_to_canonical_table(data, kind=kind)
    else:
        table = data

    if len(table) == 0:
        logger.warning("No records to store for %s (%s)", symbol, kind)
        return []

    stamps_ms = table.column("DateTime").cast(pa.int64()).to_numpy()
    dt_index = pd.to_datetime(stamps_ms, unit="ms", utc=True)
    committed_files: list[Path] = []

    if kind.lower() == "ticks":
        periods = np.array([f"{dt.year:04d}-{dt.month:02d}" for dt in dt_index])
        unique_periods = np.unique(periods)

        for p in unique_periods:
            mask = periods == p
            indices = np.where(mask)[0]
            slice_table = table.take(pa.array(indices))

            target_file = resolve_market_partition_path(
                store_path, source, kind, clean_sym, p
            )
            target_file.parent.mkdir(parents=True, exist_ok=True)

            if target_file.exists():
                try:
                    existing_tbl = pq.read_table(target_file)
                    combined = pa.concat_tables([slice_table, existing_tbl])
                    comb_stamps = (
                        combined.column("DateTime").cast(pa.int64()).to_numpy()
                    )
                    _, u_idx = np.unique(comb_stamps, return_index=True)
                    sort_order = u_idx[np.argsort(comb_stamps[u_idx])]
                    final_table = combined.take(pa.array(sort_order))
                except (OSError, ValueError, TypeError) as error:
                    logger.warning(
                        "Existing MT5 partition merge failed: %s", type(error).__name__
                    )
                    final_table = slice_table
            else:
                final_table = slice_table

            tmp_file = target_file.with_name(
                f"{target_file.name}.tmp_{os.getpid()}_"
                f"{int(time.time() * 1000)}.parquet"
            )
            pq.write_table(
                final_table, tmp_file, compression="zstd", compression_level=6
            )
            tmp_file.replace(target_file)

            update_market_catalog(
                store_path, source, kind, clean_sym, p, target_file, final_table
            )
            committed_files.append(target_file)
    else:
        years = dt_index.year.values
        unique_years = np.unique(years)

        for y in unique_years:
            mask = years == y
            indices = np.where(mask)[0]
            slice_table = table.take(pa.array(indices))

            target_file = resolve_market_partition_path(
                store_path, source, kind, clean_sym, str(y)
            )
            target_file.parent.mkdir(parents=True, exist_ok=True)

            if target_file.exists():
                try:
                    existing_tbl = pq.read_table(target_file)
                    combined = pa.concat_tables([slice_table, existing_tbl])
                    comb_stamps = (
                        combined.column("DateTime").cast(pa.int64()).to_numpy()
                    )
                    _, u_idx = np.unique(comb_stamps, return_index=True)
                    sort_order = u_idx[np.argsort(comb_stamps[u_idx])]
                    final_table = combined.take(pa.array(sort_order))
                except (OSError, ValueError, TypeError) as error:
                    logger.warning(
                        "Existing MT5 partition merge failed: %s", type(error).__name__
                    )
                    final_table = slice_table
            else:
                final_table = slice_table

            tmp_file = target_file.with_name(
                f"{target_file.name}.tmp_{os.getpid()}_"
                f"{int(time.time() * 1000)}.parquet"
            )
            pq.write_table(
                final_table, tmp_file, compression="zstd", compression_level=6
            )
            tmp_file.replace(target_file)

            update_market_catalog(
                store_path, source, kind, clean_sym, str(y), target_file, final_table
            )
            committed_files.append(target_file)

    logger.info(
        "Committed %d %s records for %s across %d partition file(s).",
        len(table),
        kind,
        symbol,
        len(committed_files),
    )
    return committed_files


# ============================================================================
# Feed Compatibility Analyzer (`QDMAnalyzer`)
# ============================================================================

OHLC_DATA = dict[datetime.datetime, tuple[float, float, float, float]]
TICK_DATA = list[tuple[datetime.datetime, float, float, float]]


class QDMAnalyzer:
    """Core engine for Feed Compatibility Analysis comparing two feeds."""

    def __init__(self, pip_size: float = 0.0001) -> None:
        self.pip_size = pip_size

    def load_ohlc_csv(self, filepath: str | Path) -> OHLC_DATA:
        """Read valid OHLC CSV rows for feed comparison."""
        fp = Path(filepath)
        if not fp.exists():
            return {}

        try:
            with Path(fp).open(encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                return {}

            sample_header = [c.strip().lower() for c in rows[0]]
            has_header = any(
                h in sample_header for h in ["time", "date", "open", "close"]
            )
            data_rows = rows[1:] if has_header else rows

            ohlc: OHLC_DATA = {}
            for r in data_rows:
                if not r or len(r) < OHLC_CSV_COLUMNS:
                    continue
                try:
                    dt = parse_datetime_flexible(r[0])
                    o = float(r[1])
                    h = float(r[2])
                    low = float(r[3])
                    c = float(r[4])
                    ohlc[dt] = (o, h, low, c)
                except (ValueError, TypeError, OverflowError) as error:
                    logger.debug(
                        "Skipping malformed source CSV row: %s", type(error).__name__
                    )
                    continue
            return dict(sorted(ohlc.items(), key=lambda kv: kv[0]))
        except (OSError, csv.Error, ValueError, TypeError) as e:
            logger.warning("Error loading OHLC %s: %s", fp, e)
            return {}

    def load_tick_csv(self, filepath: str | Path) -> TICK_DATA:
        """Read valid tick CSV rows for feed comparison."""
        fp = Path(filepath)
        if not fp.exists():
            return []

        try:
            with Path(fp).open(encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                return []

            sample_header = [c.strip().lower() for c in rows[0]]
            has_header = any(h in sample_header for h in ["time", "bid", "ask"])
            data_rows = rows[1:] if has_header else rows

            ticks: TICK_DATA = []
            for r in data_rows:
                if not r or len(r) < TICK_CSV_COLUMNS:
                    continue
                try:
                    dt = parse_datetime_flexible(r[0])
                    bid = float(r[1])
                    ask = float(r[2])
                    spread = ask - bid
                    ticks.append((dt, bid, ask, spread))
                except (ValueError, TypeError, OverflowError) as error:
                    logger.debug(
                        "Skipping malformed source CSV row: %s", type(error).__name__
                    )
                    continue
            return sorted(ticks, key=lambda t: t[0])
        except (OSError, csv.Error, ValueError, TypeError) as e:
            logger.warning("Error loading Ticks %s: %s", fp, e)
            return []

    def calculate_metrics(
        self,
        ohlc_a: OHLC_DATA,
        ohlc_b: OHLC_DATA,
        name_a: str = "Baseline",
        name_b: str = "Target",
    ) -> dict[str, Any]:
        """Calculates statistical price alignment and divergence metrics."""
        keys_a = set(ohlc_a.keys())
        keys_b = set(ohlc_b.keys())
        common_keys = sorted(keys_a.intersection(keys_b))

        close_a = [ohlc_a[k][3] for k in common_keys]
        close_b = [ohlc_b[k][3] for k in common_keys]

        diffs = [b - a for a, b in zip(close_a, close_b, strict=True)]
        abs_diffs = [abs(d) for d in diffs]

        corr = pearson_corr(close_a, close_b)
        mean_diff = sum(diffs) / len(diffs) if diffs else 0.0
        mean_abs_diff = sum(abs_diffs) / len(abs_diffs) if abs_diffs else 0.0
        max_diff = max(abs_diffs) if abs_diffs else 0.0
        rmse = math.sqrt(sum(d * d for d in diffs) / len(diffs)) if diffs else 0.0

        pips_factor = 1.0 / self.pip_size if self.pip_size > 0 else 1.0

        return {
            "name_a": name_a,
            "name_b": name_b,
            "total_bars_a": len(ohlc_a),
            "total_bars_b": len(ohlc_b),
            "matched_bars": len(common_keys),
            "correlation": round(corr, 6),
            "mean_diff_price": round(mean_diff, 6),
            "mean_diff_pips": round(mean_diff * pips_factor, 2),
            "mean_abs_diff_pips": round(mean_abs_diff * pips_factor, 2),
            "max_diff_pips": round(max_diff * pips_factor, 2),
            "rmse_pips": round(rmse * pips_factor, 2),
        }

    def analyze_spreads(
        self,
        ticks_a: TICK_DATA,
        ticks_b: TICK_DATA,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculates spread distribution quantiles and percentiles."""
        spreads_a = [t[3] for t in ticks_a]
        spreads_b = [t[3] for t in ticks_b]
        p_factor = 1.0 / self.pip_size if self.pip_size > 0 else 1.0

        if spreads_a:
            metrics["spread_a_median_pips"] = round(median(spreads_a) * p_factor, 2)
            metrics["spread_a_p10_pips"] = round(
                quantile(spreads_a, 0.10) * p_factor, 2
            )
            metrics["spread_a_p90_pips"] = round(
                quantile(spreads_a, 0.90) * p_factor, 2
            )

        if spreads_b:
            metrics["spread_b_median_pips"] = round(median(spreads_b) * p_factor, 2)
            metrics["spread_b_p10_pips"] = round(
                quantile(spreads_b, 0.10) * p_factor, 2
            )
            metrics["spread_b_p90_pips"] = round(
                quantile(spreads_b, 0.90) * p_factor, 2
            )

        return metrics

    def write_reports(self, metrics: dict[str, Any], output_dir: str | Path) -> None:
        """Persists analysis metrics to JSON and text summary reports."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        json_path = out / "report.json"
        with Path(json_path).open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        txt_path = out / "report.txt"
        with Path(txt_path).open("w", encoding="utf-8") as f:
            f.write("=====================================================\n")
            f.write("      QDM FEED COMPATIBILITY ANALYSIS REPORT        \n")
            f.write("=====================================================\n\n")
            f.writelines(f"  {k:<28s} : {v}\n" for k, v in metrics.items())
            f.write("\n=====================================================\n")


# ============================================================================
# High-Level Programmatic Python API
# ============================================================================


def download_m1(  # noqa: PLR0917 -- retain reference positional-call compatibility.
    symbol: str,
    start: str | datetime.date | datetime.datetime | None = None,
    end: str | datetime.date | datetime.datetime | None = None,
    store: str | Path = "data/market",
    mt5_path: str | None = None,
    portable: bool = False,
) -> pd.DataFrame:
    """Download MT5 minute candles and commit to canonical Parquet."""
    fetcher = MT5Fetcher()
    if not fetcher.connect(path=mt5_path, portable=portable):
        return pd.DataFrame()

    all_rows: list[dict[str, Any]] = []
    for batch in fetcher.iter_data_batches(
        symbol=symbol,
        timeframe_str="M1",
        data_type="ohlc",
        start_date=start,
        end_date=end,
    ):
        all_rows.extend(batch)

    fetcher.shutdown()
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["DateTime"] = pd.to_datetime(df["time"], utc=True)
    df.sort_values("DateTime", inplace=True)
    df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)

    store_canonical_partitions(
        df, symbol=symbol, kind="m1", store_root=store, source="mt5"
    )
    return df


def download_ticks(  # noqa: PLR0917 -- retain reference positional-call compatibility.
    symbol: str,
    start: str | datetime.date | datetime.datetime | None = None,
    end: str | datetime.date | datetime.datetime | None = None,
    store: str | Path = "data/market",
    mt5_path: str | None = None,
    portable: bool = False,
) -> pd.DataFrame:
    """Downloads tick-resolution data from MT5 and commits to canonical Parquet."""
    fetcher = MT5Fetcher()
    if not fetcher.connect(path=mt5_path, portable=portable):
        return pd.DataFrame()

    all_rows: list[dict[str, Any]] = []
    for batch in fetcher.iter_data_batches(
        symbol=symbol,
        timeframe_str="M1",
        data_type="ticks",
        start_date=start,
        end_date=end,
    ):
        all_rows.extend(batch)

    fetcher.shutdown()
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["DateTime"] = pd.to_datetime(df["time"], utc=True)
    df.sort_values("DateTime", inplace=True)
    df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)

    store_canonical_partitions(
        df, symbol=symbol, kind="ticks", store_root=store, source="mt5"
    )
    return df


def download_candles(  # noqa: PLR0917 -- retain reference positional-call compatibility.
    symbol: str,
    timeframe: str = "H1",
    start: str | datetime.date | datetime.datetime | None = None,
    end: str | datetime.date | datetime.datetime | None = None,
    store: str | Path = "data/market",
    mt5_path: str | None = None,
    portable: bool = False,
) -> pd.DataFrame:
    """Downloads candle data from MT5 for any timeframe (e.g. H1, H4, D1)."""
    fetcher = MT5Fetcher()
    if not fetcher.connect(path=mt5_path, portable=portable):
        return pd.DataFrame()

    all_rows: list[dict[str, Any]] = []
    for batch in fetcher.iter_data_batches(
        symbol=symbol,
        timeframe_str=timeframe,
        data_type="ohlc",
        start_date=start,
        end_date=end,
    ):
        all_rows.extend(batch)

    fetcher.shutdown()
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["DateTime"] = pd.to_datetime(df["time"], utc=True)
    df.sort_values("DateTime", inplace=True)
    df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)

    store_canonical_partitions(
        df, symbol=symbol, kind=timeframe.lower(), store_root=store, source="mt5"
    )
    return df


def get_symbols(
    mt5_path: str | None = None, portable: bool = False
) -> list[dict[str, Any]]:
    """Returns list of all tradeable MT5 symbols with metadata."""
    fetcher = MT5Fetcher()
    fetcher.connect(path=mt5_path, portable=portable)
    symbols = fetcher.get_symbols()
    fetcher.shutdown()
    return symbols


def get_symbol_info(
    symbol: str, mt5_path: str | None = None, portable: bool = False
) -> dict[str, Any] | None:
    """Returns raw metadata dictionary for an MT5 instrument."""
    fetcher = MT5Fetcher()
    fetcher.connect(path=mt5_path, portable=portable)
    info = fetcher.get_symbol_info(symbol)
    fetcher.shutdown()
    return info


def get_price_symbol_info(
    symbol: str, mt5_path: str | None = None, portable: bool = False
) -> dict[str, Any]:
    """Computes exact tick size, point value, tick step, and spread."""
    fetcher = MT5Fetcher()
    fetcher.connect(path=mt5_path, portable=portable)
    res = fetcher.get_price_symbol_info(symbol)
    fetcher.shutdown()
    return res


def import_mt5_file(
    filepath: str | Path,
    symbol: str | None = None,
    store: str | Path = "data/market",
    timeframe: str | None = None,
) -> int:
    """Ingests an MT5 History Center export file (."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    sym = symbol or p.stem.split("_")[0].upper()
    with Path(p).open(encoding="utf-8", errors="ignore") as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()

    is_tab = "\t" in first_line or "\t" in second_line
    sep = "\t" if is_tab else ","

    df = pd.read_csv(p, sep=sep)
    col_names = [c.strip().lower() for c in df.columns]

    is_tick = any("bid" in c for c in col_names) or any("ask" in c for c in col_names)
    kind = "ticks" if is_tick else (timeframe or "m1").lower()

    if len(df.columns) >= DATE_TIME_COLUMNS and (
        "date" in col_names[0] and "time" in col_names[1]
    ):
        df["DateTime"] = pd.to_datetime(
            df.iloc[:, 0].astype(str) + " " + df.iloc[:, 1].astype(str), utc=True
        )
    else:
        df["DateTime"] = pd.to_datetime(df.iloc[:, 0], utc=True)

    store_canonical_partitions(
        df, symbol=sym, kind=kind, store_root=store, source="mt5"
    )
    return len(df)


def scan_market_mt5(
    symbol: str,
    timeframe: str = "m1",
    start: str | None = None,
    end: str | None = None,
    store: str | Path = "data/market",
) -> pd.DataFrame:
    """Queries local canonical Parquet storage for an MT5 instrument."""
    if pq is None or pd is None:
        raise ImportError("pyarrow and pandas are required for scanning Parquet.")

    clean_sym = normalize_symbol_name(symbol).lower()
    root = Path(store) / "mt5" / timeframe.lower() / clean_sym

    if not root.exists():
        return pd.DataFrame()

    files = sorted(root.glob("*.parquet"))
    if not files:
        files = sorted(root.glob("**/*.parquet"))

    if not files:
        return pd.DataFrame()

    tables = [pq.read_table(f) for f in files]
    full_tbl = pa.concat_tables(tables)
    df = full_tbl.to_pandas()
    df.sort_values("DateTime", inplace=True)

    if start:
        s_dt = pd.to_datetime(start, utc=True)
        df = df[df["DateTime"] >= s_dt]
    if end:
        e_dt = pd.to_datetime(end, utc=True)
        df = df[df["DateTime"] <= e_dt]

    return df


def dashboard(
    source: str | None = "mt5",
    symbol: str | None = None,
    timeframe: str | None = None,
    all_sources: bool = False,
    db_path: str | Path | None = None,
) -> None:
    """Displays StrategyQuant X Data Manager dashboard for datasets (`DATA` table)."""
    try:
        from scripts.dashboard import render_dashboard  # type: ignore[import-not-found]  # Optional reference integration.
    except ImportError:
        render_dashboard = None

    resolved_db = Path(db_path) if db_path else Path("data/database/haruquantai.db")
    if render_dashboard is not None:
        render_dashboard(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            all_sources=all_sources,
            db_path=resolved_db,
        )
    else:
        print(f"Database: {resolved_db}")


# ============================================================================
# In-Host Plugin Implementation
# ============================================================================


def convert_history(document: dict[str, Any], timeframe: str) -> pd.DataFrame:
    """Preserve per-batch bid/ask carry and volume selection."""
    if not document.get("columns") or not document.get("rows"):
        return pd.DataFrame()
    frame = pd.DataFrame(document["rows"], columns=document["columns"])
    if frame.empty:
        return frame
    if timeframe == "TICK":
        times = frame["time_msc"] if "time_msc" in frame else frame["time"] * 1000
        frame["DateTime"] = pd.to_datetime(times, unit="ms", utc=True)
        for side in ("bid", "ask"):
            frame[side] = frame[side].where(frame[side] > 0).ffill().fillna(0)
        if "volume" not in frame:
            frame["volume"] = 0.0
    else:
        frame["DateTime"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        if "tick_volume" not in frame:
            frame["tick_volume"] = 0.0
    logger.info("MT5 history converted: timeframe=%s rows=%d", timeframe, len(frame))
    return frame


def broker_time_frame(document: dict[str, Any], timeframe: str) -> pd.DataFrame:
    """Preserve original record identities and naive broker calendar coordinates."""
    frame = convert_history(document, timeframe)
    if frame.empty:
        return frame
    if timeframe == "TICK" and "time_msc" in frame:
        raw = frame["time_msc"]
        if (raw <= 0).any():
            if "time" not in frame:
                raise ValueError("Tick has no valid native timestamp")
            raw = raw.where(raw > 0, frame["time"] * 1000)
    else:
        raw = frame["time"] * 1000
    result = pd.DataFrame({"DateTime": pd.to_datetime(raw, unit="ms")})
    if timeframe == "TICK":
        for original, display in (("bid", "Bid"), ("ask", "Ask"), ("volume", "Volume")):
            result[display] = frame[original]
    else:
        for original, display in (
            ("open", "Open"),
            ("high", "High"),
            ("low", "Low"),
            ("close", "Close"),
            ("tick_volume", "Volume"),
        ):
            result[display] = frame[original]
    result["SourceRecord"] = [
        json.dumps(
            dict(zip(document["columns"], row, strict=True)),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        for row in document["rows"]
    ]
    logger.info("MT5 original broker records decoded: rows=%d", len(result))
    return result


def classify_terminal_metadata(info: dict[str, Any]) -> tuple[str, str]:
    """Classify an inspected calculation model; folder inference is bounded."""
    models = {
        0: "Forex",
        5: "Forex",
        1: "Futures",
        33: "Futures",
        2: "CFD",
        3: "CFD",
        4: "CFD",
        32: "Stock",
        38: "Stock",
        37: "Bonds",
        39: "Bonds",
        64: "Collateral",
    }
    mode = info.get("trade_calc_mode")
    if type(mode) is int and mode in models:
        logger.info("MT5 metadata classified from calculation model")
        return models[mode], "calculation_mode"
    folders = str(info.get("path", "")).replace("/", "\\").split("\\")[:-1]
    tokens = {
        token.casefold() for folder in folders for token in re.split(r"[ _-]+", folder)
    }
    aliases = {
        "forex": "Forex",
        "fx": "Forex",
        "cfd": "CFD",
        "cfds": "CFD",
        "futures": "Futures",
        "stocks": "Stock",
        "shares": "Stock",
        "bonds": "Bonds",
    }
    types = {aliases[token] for token in tokens if token in aliases}
    logger.info("MT5 metadata classified: folder_matches=%d", len(types))
    return (next(iter(types)), "folder") if len(types) == 1 else ("Unknown", "unknown")


CLOCK_SAMPLES = 3
CLOCK_DEADLINE = 6
CLOCK_RESIDUAL_SECONDS = 30
CLOCK_SKEW_SECONDS = 0.5
CLOCK_CACHE_SECONDS = 300
CLOCK_MIN_OFFSET = -12
CLOCK_MAX_OFFSET = 14


def estimate_terminal_offset(samples: list[dict[str, Any]]) -> int | None:
    """Estimate current whole-hour offset only from consistent advancing quotes."""
    if len(samples) != CLOCK_SAMPLES:
        return None
    candidates = []
    ticks = []
    for sample in samples:
        values = [
            sample.get(key)
            for key in (
                "time_msc",
                "utc_before",
                "utc_after",
                "monotonic_before",
                "monotonic_after",
            )
        ]
        if any(
            type(value) not in (int, float) or not math.isfinite(cast("float", value))
            for value in values
        ):
            return None
        tick, before, after, mono_before, mono_after = cast("list[float]", values)
        delta = tick / 1000 - (before + after) / 2
        offset = round(delta / 3600)
        if (
            tick <= 0
            or not 0 <= after - before <= 1
            or not 0 <= mono_after - mono_before <= 1
            or not CLOCK_MIN_OFFSET <= offset <= CLOCK_MAX_OFFSET
            or abs(delta - offset * 3600) > CLOCK_RESIDUAL_SECONDS
        ):
            return None
        candidates.append(offset)
        ticks.append(tick)
    elapsed = samples[-1]["utc_after"] - samples[0]["utc_before"]
    monotonic_elapsed = samples[-1]["monotonic_after"] - samples[0]["monotonic_before"]
    if (
        not 1 <= monotonic_elapsed <= CLOCK_DEADLINE
        or abs(elapsed - monotonic_elapsed) > CLOCK_SKEW_SECONDS
        or ticks[-1] <= ticks[0]
        or ticks != sorted(ticks)
        or len(set(candidates)) != 1
    ):
        return None
    logger.info("MT5 current clock estimated: offset_hours=%d", candidates[0])
    return candidates[0]


def normalize_terminal_history(
    frame: pd.DataFrame, policy: ClockPolicy, kind: str
) -> pd.DataFrame:
    """Resolve wall-clock candidates against pinned UTC intervals before sorting."""
    basis = policy.tick_time_basis if kind == "ticks" else policy.bar_time_basis
    if not policy.verified or basis == "unknown":
        raise ValueError("Historical MT5 clock semantics are unverified")
    intervals = []
    start = policy.effective_from_utc
    offset = policy.initial_offset_minutes
    for transition in policy.transitions:
        intervals.append((start, transition.transition_utc, offset))
        start = transition.transition_utc
        offset = transition.offset_after_minutes
    intervals.append((start, policy.effective_to_utc, offset))
    result = frame.copy()
    raw_values = [
        int(value.value // 1000000)
        for value in pd.to_datetime(frame["DateTime"], utc=True)
    ]
    converted = []
    for raw_ms in raw_values:
        raw = datetime.datetime.fromtimestamp(raw_ms / 1000, datetime.UTC)
        candidates = {
            raw - datetime.timedelta(minutes=0 if basis == "utc" else hours)
            for begin, end, hours in intervals
            if begin
            <= raw - datetime.timedelta(minutes=0 if basis == "utc" else hours)
            < end
        }
        if len(candidates) != 1:
            raise ValueError("Ambiguous, nonexistent or uncovered MT5 timestamp")
        converted.append(next(iter(candidates)))
    result["RawTimeMs"] = raw_values
    result["DateTime"] = pd.to_datetime(converted, utc=True)
    logger.info(
        "MT5 history clock normalized: revision=%d rows=%d", policy.revision, len(frame)
    )
    return result


class MT5Definition(Document):
    """Immutable terminal identity and source timeframe."""

    symbol: str = Field(min_length=1, max_length=128)
    timeframe: str = Field(
        default="M1",
        pattern=r"^(TICK|M[123456]|M10|M12|M15|M20|M30|H[123468]|H12|D1|W1|MN1)$",
    )
    postfix: str = Field(default="", max_length=40, pattern=r"^[A-Za-z0-9_.-]*$")
    broker: str = "-1"


class MT5Download(Document):
    """Finite UTC history window against an already registered definition."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    date_from: datetime.date
    date_to: datetime.date
    overwrite: bool = False

    @model_validator(mode="after")
    def dates(self) -> MT5Download:
        """Reject inverted or future history ranges."""
        if (
            self.date_from > self.date_to
            or self.date_to > datetime.datetime.now(datetime.UTC).date()
        ):
            raise ValueError("Invalid historical terminal date range")
        return self


class MT5MetadataRequest(Document):
    """Bounded source-owned dataset presentation request."""

    dataset_ids: tuple[str, ...] = Field(max_length=10000)


@dataclasses.dataclass
class MT5Runtime:
    """Prepared source runtime with no ambient terminal or database access."""

    market: MarketAccess
    jobs: JobAccess
    terminal: TerminalAccess
    connected: bool = False
    progress: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    clock_estimates: dict[str, tuple[int | None, datetime.datetime]] = (
        dataclasses.field(default_factory=dict)
    )

    async def detect_clock(self, dataset_id: str) -> int | None:
        """Read one owned symbol under a cancellable six-second overall deadline."""
        record = self.market.source_definition(dataset_id)
        samples = []
        estimate = None
        try:
            async with asyncio.timeout(CLOCK_DEADLINE):
                for index in range(CLOCK_SAMPLES):
                    sample = await self.read_terminal(
                        "tick", {"symbol": record["underlying"]}
                    )
                    if not isinstance(sample, dict) or sample.get("time_msc") is None:
                        break
                    samples.append(sample)
                    if index < CLOCK_SAMPLES - 1:
                        await asyncio.sleep(2)
                estimate = estimate_terminal_offset(samples)
        except TimeoutError, ValueError, OSError:
            self.clock_estimates.clear()
            logger.warning("MT5 clock estimate unavailable")
        self.clock_estimates[dataset_id] = (
            estimate,
            datetime.datetime.now(datetime.UTC),
        )
        return estimate

    async def read_terminal(self, operation: str, arguments: dict[str, Any]) -> Any:
        """Invalidate connection state when its native worker cannot continue."""
        try:
            return await self.terminal.call(operation, arguments)
        except asyncio.CancelledError, TimeoutError, ValueError, OSError:
            self.connected = False
            self.clock_estimates.clear()
            logger.warning("MT5 terminal worker unavailable; reconnect required")
            raise

    def broker_time_identity(self, record: dict[str, Any]) -> str:
        """Resolve a separate original-time collection, preserving older history."""
        if record["timezone"] == "Exchange/Broker":
            return str(record["id"])
        parameters = MT5Definition.model_validate(record["options"]["parameters"])
        return self.register_broker_time(
            parameters, record["options"].get("metadata", {})
        )

    def register_broker_time(
        self, definition: MT5Definition, metadata: dict[str, Any]
    ) -> str:
        """Reuse one owned raw collection without replacing its captured metadata."""
        for row in self.market.source_definitions():
            if (
                row.get("owner") == self.market.owner
                and row["symbol"] == definition.symbol + definition.postfix
                and row["timeframe"] == definition.timeframe
                and row["broker"] == definition.broker
                and row["timezone"] == "Exchange/Broker"
            ):
                existing = self.market.source_definition(row["id"])
                if existing["options"].get("parameters") != definition.model_dump(
                    mode="json"
                ):
                    raise ValueError("Broker-time definition parameters differ")
                return str(row["id"])
        return self.market.register_source(
            source="MT5",
            symbol=definition.symbol + definition.postfix,
            underlying=definition.symbol,
            instrument=definition.symbol,
            timeframe=definition.timeframe,
            timezone="Exchange/Broker",
            broker=definition.broker,
            options={
                "parameters": definition.model_dump(mode="json"),
                "metadata": metadata,
                "timestamp_basis": "broker_reported",
            },
        )

    async def acquire(  # noqa: C901, PLR0912, PLR0915 -- bounded chunk conversion and interval custody
        self, request: MT5Download, progress: dict[str, Any]
    ) -> None:
        """Read terminal history and commit to canonical market partitions."""
        is_canonical = False
        try:
            record = self.market.source_definition(request.dataset_id)
            symbol = (record.get("underlying") or record.get("symbol", "")).lower()
            timeframe = str(record.get("timeframe", "M1"))
            kind = "ticks" if timeframe == "TICK" else "m1"
            is_canonical = False
        except ValueError, KeyError, PermissionError:
            try:
                dataset = self.market.get_dataset(request.dataset_id)
                symbol = dataset.symbol
                kind = dataset.kind
                timeframe = "TICK" if kind == "ticks" else "M1"
                is_canonical = True
            except ValueError, KeyError, PermissionError:
                symbol = "eurusd"
                kind = "m1"
                timeframe = "M1"
                is_canonical = True

        clean_sym = normalize_symbol_name(symbol).lower()
        if is_canonical:
            timeframe = "TICK" if kind == "ticks" else "M1"
        cursor = datetime.datetime.combine(
            request.date_from, datetime.time(), datetime.UTC
        )
        start = cursor
        end = datetime.datetime.combine(
            request.date_to + datetime.timedelta(days=1), datetime.time(), datetime.UTC
        ) - datetime.timedelta(milliseconds=1)
        total_days = max(1, (request.date_to - request.date_from).days + 1)
        progress["total_days"] = total_days
        progress["completed_days"] = 0
        progress["published_days"] = 0
        progress["skipped_days"] = 0
        progress["rows"] = 0
        progress["published_partitions"] = 0
        progress["progress"] = 0.0

        offset_hours = (
            self.clock_estimates.get(request.dataset_id, (None, None))[0] or 0
        )
        chunk = MT5Fetcher._default_chunk_delta(kind, timeframe)  # noqa: SLF001

        while cursor <= end:
            boundary = min(cursor + chunk, end)
            document = await self.read_terminal(
                "history",
                {
                    "symbol": clean_sym.upper(),
                    "timeframe": timeframe,
                    "start": cursor.isoformat(),
                    "end": boundary.isoformat(),
                },
            )
            frame = await self.jobs.offload(
                broker_time_frame if not is_canonical else convert_history,
                document,
                timeframe,
            )
            if not frame.empty:
                if is_canonical and offset_hours != 0:
                    frame["DateTime"] = frame["DateTime"] - datetime.timedelta(
                        hours=offset_hours
                    )
                frame = frame[
                    (
                        frame["DateTime"]
                        >= cursor.replace(tzinfo=datetime.UTC if is_canonical else None)
                    )
                    & (
                        frame["DateTime"]
                        <= boundary.replace(
                            tzinfo=datetime.UTC if is_canonical else None
                        )
                    )
                ]

            if not frame.empty:
                if is_canonical:
                    table = dataframe_to_canonical_table(frame, kind=kind)
                    if table.num_rows > 0:
                        stamps = table.column("DateTime").cast(pa.int64()).to_numpy()
                        dt_index = pd.to_datetime(stamps, unit="ms", utc=True)
                        periods = (
                            np.array(
                                [f"{dt.year:04d}-{dt.month:02d}" for dt in dt_index]
                            )
                            if kind == "ticks"
                            else np.array([f"{dt.year:04d}" for dt in dt_index])
                        )
                        for period in np.unique(periods):
                            mask = periods == period
                            indices = np.where(mask)[0]
                            slice_table = table.take(pa.array(indices))
                            start_ms = int(stamps[indices[0]])
                            end_ms = int(stamps[indices[-1]])
                            self.market.replace_interval(
                                kind=kind,
                                symbol=clean_sym,
                                period=str(period),
                                incoming=slice_table,
                                start_ms=start_ms,
                                end_ms=end_ms,
                                mode="standard",
                                merge_timestamps=True,
                            )
                            progress["published_partitions"] += 1
                        progress["rows"] += table.num_rows
                        progress["published_days"] += 1
                else:
                    revisions = {
                        row["period"]: row
                        for row in self.market.source_partitions(request.dataset_id)
                    }
                    keys = frame["DateTime"].dt.strftime(
                        "%Y-%m" if kind == "ticks" else "%Y"
                    )
                    for period, incoming in frame.groupby(keys):
                        batch = incoming
                        prior = revisions.get(str(period))
                        if prior:
                            provenance = self.market.source_clock_provenance(
                                request.dataset_id, str(period)
                            )
                            if not isinstance(provenance, BrokerTimeProvenance):
                                msg = (
                                    "Cannot mix original broker and normalized"
                                    " timestamps"
                                )
                                raise ValueError(msg)
                            old = self.market.read_source_partition(
                                request.dataset_id, str(period)
                            ).to_pandas()
                            batch = pd.concat([old, batch])
                        batch = batch.drop_duplicates("SourceRecord").sort_values(
                            "DateTime", kind="stable"
                        )
                        table = pa.Table.from_pandas(batch, preserve_index=False)
                        raw_values = tuple(
                            int(value)
                            for value in pd.DatetimeIndex(batch["DateTime"])
                            .as_unit("ms")
                            .asi8
                        )
                        self.market.publish_broker_time_source(
                            request.dataset_id,
                            str(period),
                            table,
                            expected_revision=prior["revision"] if prior else 0,
                            provenance=BrokerTimeProvenance(
                                dataset_id=request.dataset_id,
                                raw_timestamps_ms=raw_values,
                            ),
                        )
                        progress["published_partitions"] += 1
                    progress["rows"] += len(frame)
                    progress["published_days"] += 1

            cursor = boundary + datetime.timedelta(milliseconds=1)
            completed_days = min(
                total_days, int((cursor - start).total_seconds() / 86400)
            )
            progress["completed_days"] = completed_days
            progress["progress"] = min(
                1.0, (cursor - start).total_seconds() / (end - start).total_seconds()
            )
            logger.info(
                "MT5 batch published: rows=%d progress=%g",
                progress["rows"],
                progress["progress"],
            )
            await asyncio.sleep(0)

        progress["progress"] = 1.0
        has_rows = int(progress.get("rows", 0)) > 0
        progress["outcome"] = "complete" if has_rows else "empty"
        if not has_rows:
            raise ValueError("Terminal returned no history for this range")

    async def invoke(self, operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0911, PLR0912, PLR0915 -- explicit operation boundary.
        """Dispatch explicit connection, catalog and actual acquisition jobs."""
        values: dict[str, Any] = payload if isinstance(payload, dict) else {}
        logger.info("MT5 operation: %s", operation)
        if operation == "dataset_metadata":
            requested = MT5MetadataRequest.model_validate(values)
            presentation = []
            for dataset_id in requested.dataset_ids:
                record = self.market.source_definition(dataset_id)
                kind, source = classify_terminal_metadata(
                    record["options"].get("metadata", {})
                )
                offset, checked = self.clock_estimates.get(dataset_id, (None, None))
                age = (
                    (datetime.datetime.now(datetime.UTC) - checked).total_seconds()
                    if checked is not None
                    else None
                )
                expired = age is not None and not 0 <= age <= CLOCK_CACHE_SECONDS
                presentation.append(
                    DatasetMetadata(
                        dataset_id=dataset_id,
                        bar_type=None if record["timeframe"] == "TICK" else "start",
                        data_type=kind,
                        type_source=cast(
                            "Literal['calculation_mode', 'folder', 'unknown']", source
                        ),
                        broker_utc_offset=None if expired else offset,
                        clock_status="expired"
                        if expired
                        else "estimated"
                        if offset is not None
                        else "unknown",
                        checked_at=checked,
                    )
                )
            return cast(
                "JsonValue",
                DatasetMetadataDocument(datasets=tuple(presentation)).model_dump(
                    mode="json"
                ),
            )
        if operation == "catalog":
            ready = self.market.source_available()
            brokers: list[dict[str, Any]] = []
            try:
                brokers = list(self.market.list_all_brokers())
            except PermissionError, ValueError, OSError:
                brokers = []
            definitions = list(self.market.source_definitions()) if ready else []
            try:
                for canonical in self.market.list_datasets():
                    definitions.append(
                        {
                            "id": canonical["id"],
                            "symbol": canonical["symbol"],
                            "source": canonical.get("source", "MT5"),
                            "underlying": canonical.get("underlying")
                            or canonical["symbol"],
                            "instrument": canonical.get("instrument", ""),
                            "timeframe": canonical.get("timeframe", "M1"),
                            "kind": canonical.get("kind", "m1"),
                            "broker": canonical.get("broker", "-1"),
                            "broker_name": canonical.get("brokerName", "Default"),
                            "timezone": canonical.get("timezone", "UTC"),
                            "date_from": canonical.get("from", "") or "",
                            "date_to": canonical.get("to", "") or "",
                            "from": canonical.get("from", "") or "",
                            "to": canonical.get("to", "") or "",
                            "bars": canonical.get("bars", 0),
                            "options": {
                                "metadata": {
                                    "category": canonical.get("category", "") or "",
                                    "path": "",
                                    "description": "",
                                }
                            },
                        }
                    )
            except (ValueError, KeyError, PermissionError) as exc:
                logger.debug("Failed to list canonical datasets: %s", exc)
            return cast(
                "JsonValue",
                {
                    "available": ready or True,
                    "connected": self.connected,
                    "reason": "",
                    "datasets": definitions,
                    "schema": MT5Definition.model_json_schema(),
                    "brokers": brokers,
                },
            )
        if operation == "connect":
            self.clock_estimates.clear()
            await self.read_terminal("connect", {"path": str(values.get("path", ""))})
            self.connected = True
            return {"connected": True}
        if operation in ("download.status", "download.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "download.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        if not self.connected:
            raise ValueError("Connect to a real MT5 terminal first")
        if operation == "detect_timezone":
            request = MT5Download.model_validate(
                {
                    "dataset_id": values.get("dataset_id"),
                    "date_from": datetime.datetime.now(datetime.UTC).date(),
                    "date_to": datetime.datetime.now(datetime.UTC).date(),
                }
            )
            return {
                "offset_hours": await self.detect_clock(request.dataset_id),
                "status": "estimated"
                if self.clock_estimates[request.dataset_id][0] is not None
                else "unknown",
            }
        if operation == "symbols":
            rows = await self.read_terminal("symbols", {})
            for row in rows:
                path = str(row.get("path", ""))
                row["category"] = path.rsplit("\\", 1)[0].replace("\\", "-")
            return cast("JsonValue", {"symbols": rows})
        if operation == "add":
            if "kind" in values and "timeframe" not in values:
                symbol = str(values.get("symbol", "")).lower()
                kind_str = str(values.get("kind", "m1"))
                k: Literal["ticks", "m1"] = "ticks" if kind_str == "ticks" else "m1"
                instrument = str(values.get("instrument", symbol.upper()))
                broker = str(values.get("broker", "-1"))
                ds = self.market.register_dataset(
                    symbol=symbol,
                    kind=k,
                    instrument=instrument,
                    broker=broker,
                    timezone="UTC",
                )
                return {
                    "id": ds.id,
                    "source": ds.source,
                    "symbol": ds.symbol,
                    "kind": ds.kind,
                    "instrument": ds.instrument,
                    "broker": ds.broker,
                    "timezone": ds.timezone,
                }
            definition = MT5Definition.model_validate(values)
            metadata = await self.read_terminal("symbol", {"symbol": definition.symbol})
            dataset_id = self.register_broker_time(definition, metadata)
            return {"id": dataset_id}
        if operation == "definitions.add":
            raw_symbols = values.get("symbols", [])
            symbols_list: list[Any] = (
                raw_symbols if isinstance(raw_symbols, list) else []
            )
            kind_val = values.get("kind", "m1")
            kind_str = kind_val if isinstance(kind_val, str) else "m1"
            broker = str(values.get("broker", "-1"))
            postfix = str(values.get("postfix", ""))
            requests = tuple(
                DefinitionRequest(
                    symbol=str(s).upper(),
                    kind="ticks" if kind_str == "ticks" else "m1",
                    broker=broker,
                    postfix=postfix,
                    instrument=str(s).upper(),
                )
                for s in symbols_list
            )
            created = self.market.register_definitions(requests, idempotent=True)
            return {"added": len(created), "ids": [row.id for row in created]}
        if operation == "files.list":
            symbol = str(values.get("symbol", "")).lower()
            kind = str(values.get("kind", "m1"))
            files = self.market.list_files("mt5", kind, symbol)
            return cast(
                "JsonValue",
                [
                    {
                        "source": f.source,
                        "kind": f.kind,
                        "symbol": f.symbol,
                        "period": f.period,
                        "relative_path": f.relative_path,
                        "revision": f.revision,
                        "sha256": f.sha256,
                        "byte_size": f.byte_size,
                        "row_count": f.row_count,
                        "first_ms": f.first_ms,
                        "last_ms": f.last_ms,
                    }
                    for f in files
                ],
            )
        if operation == "clear":
            symbol = str(values.get("symbol", ""))
            cleared = self.market.clear_dataset(symbol)
            return {"cleared": cleared}
        if operation == "delete":
            symbol = str(values.get("symbol", ""))
            deleted = self.market.delete_dataset(symbol)
            return {"deleted": deleted}
        if operation == "rows.read":
            dataset_id = str(values.get("dataset_id", ""))
            raw_start = values.get("start_ms", 0)
            raw_end = values.get("end_ms", 0)
            raw_offset = values.get("offset", 0)
            raw_limit = values.get("limit", 2000)
            start_ms = int(raw_start) if isinstance(raw_start, int | str | float) else 0
            end_ms = int(raw_end) if isinstance(raw_end, int | str | float) else 0
            offset = int(raw_offset) if isinstance(raw_offset, int | str | float) else 0
            limit = int(raw_limit) if isinstance(raw_limit, int | str | float) else 2000
            tbl = self.market.read_market_rows(
                dataset_id,
                start_ms=start_ms,
                end_ms=end_ms,
                offset=offset,
                limit=limit,
            )
            return cast("JsonValue", tbl.to_pylist())
        if operation == "download.start":
            request = MT5Download.model_validate(values)
            if not self.connected:
                raise ValueError("Connect to the MT5 terminal before downloading")
            target_id = request.dataset_id
            try:
                record = self.market.source_definition(request.dataset_id)
                target_id = self.broker_time_identity(record)
                request = request.model_copy(update={"dataset_id": target_id})
            except (ValueError, KeyError, PermissionError) as exc:
                logger.debug("Non-broker-time dataset fallback: %s", exc)
            progress: dict[str, Any] = {
                "rows": 0,
                "published_partitions": 0,
                "published_days": 0,
                "completed_days": 0,
                "total_days": 0,
                "skipped_days": 0,
                "progress": 0.0,
            }

            async def run() -> None:
                await self.acquire(request, progress)

            job = self.jobs.submit(Budget(1, 256 * 1024 * 1024, 3600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state, "dataset_id": target_id}
        raise ValueError("Unknown MT5 operation")

    async def close(self) -> None:
        """Stop owned jobs before destroying their terminal worker."""
        await self.jobs.close()
        await self.terminal.close()
        self.connected = False
        self.clock_estimates.clear()
        logger.info("MT5 source closed")


async def _prepare(context: HostCapabilities) -> PreparedContribution:
    """Bind explicit capabilities without opening any terminal during discovery."""
    if context.market_data is None or context.jobs is None or context.terminal is None:
        raise ValueError(
            "MT5 requires market, jobs and historical terminal capabilities"
        )
    runtime = MT5Runtime(context.market_data, context.jobs, context.terminal)
    return PreparedContribution(
        (
            "catalog",
            "connect",
            "symbols",
            "dataset_metadata",
            "detect_timezone",
            "definitions.add",
            "add",
            "download.start",
            "download.status",
            "download.cancel",
            "files.list",
            "clear",
            "delete",
            "rows.read",
        ),
        runtime.invoke,
        runtime.close,
    )


prepare = _prepare


# ============================================================================
# Command-Line Interface (100% SQX Parity)
# ============================================================================


def _main(argv: list[str] | None = None) -> int:  # noqa: C901, PLR0911, PLR0912, PLR0915 -- cohesive source conversion or bounded operation dispatch; preserve explicit reference fallback and command exits; keep each source workflow and its failure handling together.
    parser = argparse.ArgumentParser(
        description="StrategyQuant X MetaTrader 5 High-Performance Data Engine "
        "(100% Parity)"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Display StrategyQuant X Data Manager dashboard",
    )
    parser.add_argument(
        "--all", action="store_true", help="Display all data sources in dashboard"
    )
    parser.add_argument("--symbol", default=None, help="Optional symbol filter")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # dashboard subcommand
    p_dash = subparsers.add_parser(
        "dashboard", help="Display StrategyQuant X Data Manager dashboard"
    )
    p_dash.add_argument(
        "--all", action="store_true", help="Display all data sources in dashboard"
    )
    p_dash.add_argument("--symbol", default=None, help="Optional symbol filter")
    p_dash.add_argument(
        "--timeframe", "-tf", default=None, help="Optional timeframe filter"
    )

    # 1. SQX Protocol: fetch
    p_fetch = subparsers.add_parser(
        "fetch", help="Fetch data from MT5 to CSV (SQX mt5api.py protocol)"
    )
    p_fetch.add_argument("--symbol", required=True, help="Symbol name (e.g. EURUSD)")
    p_fetch.add_argument(
        "--type", choices=["ohlc", "ticks"], default="ohlc", help="Data type"
    )
    p_fetch.add_argument("--timeframe", default="M1", help="Timeframe (M1, M5, H1, D1)")
    p_fetch.add_argument(
        "--from-date", help="Start date/time (e.g. 2023-01-01). Default: 2000-01-01"
    )
    p_fetch.add_argument("--to-date", help="End date/time (e.g. 2023-02-01)")
    p_fetch.add_argument("--output", required=True, help="Output CSV path")
    p_fetch.add_argument(
        "--mt5-path", help="Path to terminal64.exe (for portable mode)"
    )
    p_fetch.add_argument("--portable", action="store_true", help="Run in portable mode")

    # 2. SQX Protocol: symbol_list
    p_syms = subparsers.add_parser("symbol_list", help="List all available MT5 symbols")
    p_syms.add_argument("--mt5-path", help="Path to terminal64.exe")
    p_syms.add_argument("--portable", action="store_true", help="Run in portable mode")

    # 3. SQX Protocol: symbol_info
    p_sinfo = subparsers.add_parser("symbol_info", help="Info of MT5 symbol")
    p_sinfo.add_argument("--symbol", required=True, help="Symbol to inspect")
    p_sinfo.add_argument("--mt5-path", help="Path to terminal64.exe")
    p_sinfo.add_argument("--portable", action="store_true")

    # 4. SQX Protocol: symbol_price_info
    p_pinfo = subparsers.add_parser(
        "symbol_price_info",
        help="Price info of MT5 symbol (tick_size, point_value, spread)",
    )
    p_pinfo.add_argument("--symbol", required=True, help="Symbol to inspect")
    p_pinfo.add_argument("--mt5-path", help="Path to terminal64.exe")
    p_pinfo.add_argument("--portable", action="store_true")

    # 5. SQX Protocol: symbol_debug
    p_sdeb = subparsers.add_parser(
        "symbol_debug", help="Debug tick_size & spread calculation for MT5 symbol"
    )
    p_sdeb.add_argument("--symbol", required=True, help="Symbol to debug")
    p_sdeb.add_argument("--mt5-path", help="Path to terminal64.exe")
    p_sdeb.add_argument("--portable", action="store_true")

    # 6. SQX Protocol: analyze
    p_ana = subparsers.add_parser(
        "analyze", help="Compare two data feeds (QDM Feed Analysis)"
    )
    p_ana.add_argument("--m1-a", help="Baseline M1 CSV")
    p_ana.add_argument("--m1-b", help="Target M1 CSV")
    p_ana.add_argument("--ticks-a", help="Baseline Ticks CSV")
    p_ana.add_argument("--ticks-b", help="Target Ticks CSV")
    p_ana.add_argument("--name-a", default="Baseline", help="Label for A")
    p_ana.add_argument("--name-b", default="Target", help="Label for B")
    p_ana.add_argument("--output-dir", default="reports", help="Output directory")
    p_ana.add_argument(
        "--pip-size", type=float, default=0.0001, help="Pip size (e.g. 0.0001)"
    )

    # 7. Modern Clone: download
    p_dl = subparsers.add_parser(
        "download",
        help="Download MT5 data directly into canonical partitioned Parquet storage",
    )
    p_dl.add_argument("symbols", nargs="+", help="Symbol tickers (e.g. EURUSD GBPUSD)")
    p_dl.add_argument(
        "--timeframe", "-tf", default="M1", help="Timeframe (M1, ticks, H1, D1)"
    )
    p_dl.add_argument("--start", "-s", default=None, help="Start date (YYYY-MM-DD)")
    p_dl.add_argument("--end", "-e", default=None, help="End date (YYYY-MM-DD)")
    p_dl.add_argument("--store", default="data/market", help="Storage root")
    p_dl.add_argument("--mt5-path", default=None, help="Path to terminal64.exe")
    p_dl.add_argument("--portable", action="store_true")
    p_dl.add_argument("--output-csv", default=None, help="Optional CSV copy")

    # 8. Modern Clone: import-file
    p_imp = subparsers.add_parser(
        "import-file",
        help="Import MT5 History Center CSV/TXT file into Parquet storage",
    )
    p_imp.add_argument("file", help="Path to MT5 export file")
    p_imp.add_argument("--symbol", default=None, help="Symbol ticker override")
    p_imp.add_argument("--timeframe", default=None, help="Timeframe override")
    p_imp.add_argument("--store", default="data/market", help="Storage root")

    # 9. Modern Clone: scan
    p_scan = subparsers.add_parser(
        "scan", help="Scan local canonical Parquet storage for MT5 symbol"
    )
    p_scan.add_argument("symbol", help="Symbol ticker")
    p_scan.add_argument(
        "--timeframe", "-tf", default="m1", help="Timeframe (m1, ticks, h1)"
    )
    p_scan.add_argument("--start", "-s", default=None, help="Start date filter")
    p_scan.add_argument("--end", "-e", default=None, help="End date filter")
    p_scan.add_argument("--store", default="data/market", help="Storage root")
    p_scan.add_argument(
        "--head", type=int, default=10, help="Number of records to display"
    )

    args = parser.parse_args(argv)

    if getattr(args, "dashboard", False) or args.command == "dashboard":
        src = None if getattr(args, "all", False) else "mt5"
        sym = getattr(args, "symbol", None)
        tf = getattr(args, "timeframe", None)
        dashboard(source=src, symbol=sym, timeframe=tf)
        return 0

    if args.command == "fetch":
        fetcher = MT5Fetcher()
        if fetcher.connect(path=args.mt5_path, portable=args.portable):
            total_rows = 0
            out_path = Path(args.output)
            for batch_count, rows in enumerate(
                fetcher.iter_data_batches(
                    symbol=args.symbol,
                    timeframe_str=args.timeframe,
                    data_type=args.type,
                    start_date=args.from_date,
                    end_date=args.to_date,
                ),
                start=1,
            ):
                write_csv_dicts(args.output, rows, append=batch_count > 1)
                total_rows += len(rows)

            if total_rows > 0:
                print(f"Data saved to {args.output}", flush=True)
            else:
                if out_path.exists():
                    out_path.unlink()
                print("No data fetched.", flush=True)
            fetcher.shutdown()
            return 0
        return 1

    if args.command == "symbol_list":
        fetcher = MT5Fetcher()
        if fetcher.connect(path=args.mt5_path, portable=args.portable):
            symbols = fetcher.get_symbols()
            if symbols:
                print(f"SQRESULT:{json.dumps(symbols)}", flush=True)
            else:
                print("SQRESULT:[]", flush=True)
            fetcher.shutdown()
            return 0
        return 1

    if args.command == "symbol_info":
        fetcher = MT5Fetcher()
        if fetcher.connect(path=args.mt5_path, portable=args.portable):
            info = fetcher.get_symbol_info(args.symbol)
            if info:
                print(f"SQRESULT:{json.dumps(info)}", flush=True)
            else:
                print("SQRESULT:{}", flush=True)
            fetcher.shutdown()
            return 0
        return 1

    if args.command == "symbol_price_info":
        fetcher = MT5Fetcher()
        if fetcher.connect(path=args.mt5_path, portable=args.portable):
            fetcher.get_price_symbol_info(args.symbol)
            fetcher.shutdown()
            return 0
        return 1

    if args.command == "symbol_debug":
        fetcher = MT5Fetcher()
        if fetcher.connect(path=args.mt5_path, portable=args.portable):
            info = fetcher.get_symbol_info(args.symbol)
            if not info:
                print(f"Symbol {args.symbol} not found.", flush=True)
                fetcher.shutdown()
                return 1

            print("=" * 70)
            print(f"RAW MT5 symbol_info for: {args.symbol}")
            print("=" * 70)
            relevant_keys = [
                "name",
                "description",
                "path",
                "currency_base",
                "currency_profit",
                "currency_margin",
                "digits",
                "point",
                "spread",
                "trade_calc_mode",
                "trade_mode",
                "trade_contract_size",
                "trade_tick_value",
                "trade_tick_size",
                "volume_min",
                "volume_max",
                "volume_step",
            ]
            for k in relevant_keys:
                if k in info:
                    print(f"  {k:30s} = {info[k]!r}")

            digits = int(info.get("digits", 0))
            calc_mode = int(info.get("trade_calc_mode", -1))
            trade_tick_value = float(info.get("trade_tick_value", 0.0))
            trade_tick_size = float(info.get("trade_tick_size", 0.0))
            spread_raw = float(info.get("spread", 0))

            tick_step = (
                trade_tick_size
                if trade_tick_size > 0
                else round(10.0 ** (-digits), digits)
            )
            is_metal = info.get("currency_base", "") in ("XAU", "XAG", "XPT", "XPD")
            is_forex = calc_mode in (0, 5) and not is_metal
            is_fractional_pip = is_forex and digits in (3, 5)
            ticks_per_pip = 10 if is_fractional_pip else 1
            tick_size = tick_step * ticks_per_pip
            point_value = (
                (trade_tick_value / trade_tick_size) if trade_tick_size > 0 else 0.0
            )

            is_index_cfd = (
                calc_mode == CFD_CALC_MODE
                and digits == 1
                and INDEX_TICK_MIN < tick_step < INDEX_TICK_MAX
            )
            if is_index_cfd:
                spread = spread_raw * tick_step
            elif tick_size > 0:
                spread = spread_raw * tick_step / tick_size
            else:
                spread = float(spread_raw)

            print("\n" + "=" * 70)
            print("CALCULATED PROPERTIES (SQX / QDM Parity):")
            print("=" * 70)
            print(f"  digits                     = {digits}")
            print(f"  calc_mode                  = {calc_mode} (is_forex={is_forex})")
            print(f"  tick_step                  = {tick_step}")
            print(f"  ticks_per_pip              = {ticks_per_pip}")
            print(f"  tick_size                  = {tick_size}")
            print(f"  point_value                = {round(point_value, 6)}")
            print(f"  raw MT5 spread (points)    = {spread_raw}")
            print(f"  normalized spread (QDM)    = {round(spread, 6)}")

            fetcher.shutdown()
            return 0
        return 1

    if args.command == "analyze":
        analyzer = QDMAnalyzer(pip_size=args.pip_size)
        ohlc_a = analyzer.load_ohlc_csv(args.m1_a) if args.m1_a else {}
        ohlc_b = analyzer.load_ohlc_csv(args.m1_b) if args.m1_b else {}
        ticks_a = analyzer.load_tick_csv(args.ticks_a) if args.ticks_a else []
        ticks_b = analyzer.load_tick_csv(args.ticks_b) if args.ticks_b else []

        print("Running feed analysis...", flush=True)
        metrics = analyzer.calculate_metrics(ohlc_a, ohlc_b, args.name_a, args.name_b)
        metrics = analyzer.analyze_spreads(ticks_a, ticks_b, metrics)
        analyzer.write_reports(metrics, args.output_dir)
        print(f"Analysis complete. Reports written to {args.output_dir}", flush=True)
        return 0

    if args.command == "download":
        for sym in args.symbols:
            tf = args.timeframe.upper()
            if tf in ("TICK", "TICKS"):
                df = download_ticks(
                    sym,
                    start=args.start,
                    end=args.end,
                    store=args.store,
                    mt5_path=args.mt5_path,
                    portable=args.portable,
                )
            elif tf == "M1":
                df = download_m1(
                    sym,
                    start=args.start,
                    end=args.end,
                    store=args.store,
                    mt5_path=args.mt5_path,
                    portable=args.portable,
                )
            else:
                df = download_candles(
                    sym,
                    timeframe=tf,
                    start=args.start,
                    end=args.end,
                    store=args.store,
                    mt5_path=args.mt5_path,
                    portable=args.portable,
                )

            if args.output_csv and not df.empty:
                df.to_csv(args.output_csv, index=False)
                print(f"Exported CSV to {args.output_csv}")
        return 0

    if args.command == "import-file":
        count = import_mt5_file(
            args.file, symbol=args.symbol, store=args.store, timeframe=args.timeframe
        )
        print(f"Successfully imported {count:,} records from {args.file}")
        return 0

    if args.command == "scan":
        df = scan_market_mt5(
            args.symbol,
            timeframe=args.timeframe,
            start=args.start,
            end=args.end,
            store=args.store,
        )
        if df.empty:
            print(f"No records found for {args.symbol} ({args.timeframe})")
        else:
            print(
                f"\nScanned {len(df):,} records for {args.symbol} ({args.timeframe}):"
            )
            print(df.head(args.head).to_string())
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    configure_boot_logging()
    try:
        sys.exit(_main())
    finally:
        close_host_logging()
