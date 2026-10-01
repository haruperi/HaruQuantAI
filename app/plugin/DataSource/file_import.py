# ruff: noqa: INP001, PLR2004 -- singular namespace and preserved source thresholds
"""Owner-script file acquisition and format interpretation.

Description:
    Parses supplied file contents with the owner's predefined formats, date
    parsing, sparse MT5 tick correction and canonical Arrow conversion.
    Host jobs and immutable custody own execution and durable publication.
Purpose:
    FEAT-DM-FILE_IMPORT: Real file import attached exclusively to Data Manager.
Key Capabilities:
    - FR-FILE-PARSE: Source parser and auto-detection; logs parsed record counts.
    - FR-FILE-PUBLISH: Revisioned host publication; logs dataset/partition counts.
Python API Usage:
    contribution = await prepare(capabilities)
    preview = await contribution.invoke("preview", request)
CLI Usage:
    uv run pytest tests/plugin/DataSource/test_file_import.py --no-cov
"""

from __future__ import annotations

import asyncio
import io
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    SettingsAccess,
)
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.packages import PreparedContribution
from app.persistence.market import M1_SCHEMA, TICK_SCHEMA
from pydantic import Field, JsonValue

logger = get_logger(__name__)

PLUGIN = {
    "id": "plugin.data_manager.file_import",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
        {"id": "host.settings", "version": "1.0.0", "required": False},
    ],
    "inputs": [{"name": "content", "type": "text", "units": "UTF-8"}],
    "outputs": [{"name": "partition", "type": "arrow", "units": "source-specific"}],
}


@dataclass
class _CustomDataFormat:
    """
    StrategyQuant X File Format descriptor.

    Preserved owner-script descriptor; independent parity is not asserted.
    """

    name: str
    separator: str
    date_format: str
    time_format: str | None = None
    skip_rows: int = 0
    skip_columns: int = 0
    predefined: bool = False
    columns: list[str] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "separator": self.separator,
            "dateFormat": self.date_format,
            "timeFormat": self.time_format or "",
            "skipRows": self.skip_rows,
            "skipColumns": self.skip_columns,
            "predefined": self.predefined,
            "columnTypes": self.columns,
            "order": self.order,
        }

    @property
    def is_tick_format(self) -> bool:
        cols_lower = [c.lower() for c in self.columns]
        return "bid" in cols_lower or "ask" in cols_lower or "tick" in self.name.lower()

    @property
    def has_two_volumes(self) -> bool:
        vols = [c for c in self.columns if c.lower() == "volume"]
        return len(vols) >= 2


PREDEFINED_FORMATS: list[_CustomDataFormat] = [
    # 1. MetaTrader 4 (Bar data)
    _CustomDataFormat(
        name="MetaTrader4",
        separator=",",
        date_format="yyyy.MM.dd",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 2. MetaTrader 5 (Bar data with 2 trailing unused columns)
    _CustomDataFormat(
        name="MetaTrader5",
        separator="\t",
        date_format="yyyy.MM.dd",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=[
            "Date",
            "Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Unused",
            "Unused",
        ],
        order=0,
    ),
    # 3. MetaTrader 5 Tick Data (High order)
    _CustomDataFormat(
        name="MetaTrader5 Tick Data",
        separator="\t",
        date_format="yyyy.MM.dd",
        time_format="HH:mm:ss.SSS",
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Bid", "Ask"],
        order=100,
    ),
    # 4. SQ Tick Downloader
    _CustomDataFormat(
        name="SQ Tick Downloader",
        separator=",",
        date_format="yyyy.MM.dd HH:mm:ss.SSS",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date & Time", "Bid", "Ask", "Volume", "Volume"],
        order=0,
    ),
    # 5. SQ3 Tick Export
    _CustomDataFormat(
        name="SQ3 Tick Export",
        separator=",",
        date_format="dd.MM.yyyy HH:mm:ss",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date & Time", "Ask", "Bid", "Volume"],
        order=0,
    ),
    # 6. DukasCopy Tick Data
    _CustomDataFormat(
        name="DukasCopy Tick Data",
        separator=",",
        date_format="dd.MM.yyyy HH:mm:ss",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date & Time", "Ask", "Bid", "Volume", "Volume"],
        order=0,
    ),
    # 7. MetaTrader4 tick export
    _CustomDataFormat(
        name="MetaTrader4 tick export",
        separator=",",
        date_format="yyyy.MM.dd HH:mm:ss",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date & Time", "Ask", "Bid", "Volume"],
        order=0,
    ),
    # 8. NinjaTrader data
    _CustomDataFormat(
        name="NinjaTrader data",
        separator=";",
        date_format="yyyyMMdd",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 9. NinjaTrader data (sqDataExport)
    _CustomDataFormat(
        name="NinjaTrader data (sqDataExport)",
        separator=";",
        date_format="MM/dd/yyyy HH:mm",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=[
            "Date",
            "Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Unused",
            "Unused",
            "Volume",
        ],
        order=0,
    ),
    # 10. AZ-Invest Range/Renko data
    _CustomDataFormat(
        name="AZ-Invest Range/Renko data",
        separator=",",
        date_format="yyyy.MM.dd HH:mm:ss",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date & Time", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 11. Tradestation
    _CustomDataFormat(
        name="Tradestation",
        separator=",",
        date_format="MM/dd/yyyy HH:mm",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Open", "High", "Low", "Close", "Volume", "Volume"],
        order=0,
    ),
    # 12. MultiCharts
    _CustomDataFormat(
        name="MultiCharts",
        separator=",",
        date_format="MM/dd/yyyy",
        time_format=None,
        skip_rows=1,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 13. Kibot daily data
    _CustomDataFormat(
        name="Kibot daily data",
        separator=",",
        date_format="MM/dd/yyyy",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 14. Kibot intraday data
    _CustomDataFormat(
        name="Kibot intraday data",
        separator=",",
        date_format="MM/dd/yyyy",
        time_format=None,
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
        order=0,
    ),
    # 15. Kibot tick data
    _CustomDataFormat(
        name="Kibot tick data",
        separator=",",
        date_format="MM/dd/yyyy",
        time_format="HH:mm:ss",
        skip_rows=0,
        skip_columns=0,
        predefined=True,
        columns=["Date", "Time", "Unused", "Bid", "Ask", "Volume"],
        order=0,
    ),
]


def _java_date_format_to_python(java_fmt: str) -> str:
    """Translate Java SimpleDateFormat into Python strptime format."""
    token_map = [
        ("yyyy", "%Y"),
        ("yy", "%y"),
        ("MM", "%m"),
        ("M", "%m"),
        ("dd", "%d"),
        ("d", "%d"),
        ("HH", "%H"),
        ("H", "%H"),
        ("hh", "%I"),
        ("h", "%I"),
        ("mm", "%M"),
        ("m", "%M"),
        ("ss", "%S"),
        ("s", "%S"),
        ("SSS", "%f"),
        ("a", "%p"),
    ]
    pattern = "|".join(re.escape(k) for k, _ in token_map)
    d = dict(token_map)
    return re.sub(pattern, lambda m: d[m.group(0)], java_fmt)


def _parse_date_time_components(  # noqa: C901, PLR0911, PLR0912 -- preserved source fallback sequence.
    date_val: str,
    time_val: str | None,
    date_format: str,
    time_format: str | None = None,
) -> datetime | None:
    """Parse date and optional time according to the source specification."""
    d_clean = date_val.strip()
    if not d_clean:
        return None

    if "epoch" in date_format.lower() or "millis" in date_format.lower():
        try:
            val = int(d_clean)
            return datetime.fromtimestamp(val / 1000.0, tz=UTC)
        except ValueError:
            return None
    if "seconds" in date_format.lower():
        try:
            val = int(d_clean)
            return datetime.fromtimestamp(val, tz=UTC)
        except ValueError:
            return None

    combined_str = d_clean
    combined_fmt = date_format

    if time_val is not None and time_val.strip():
        t_clean = time_val.strip()
        combined_str = f"{d_clean} {t_clean}"
        if time_format:
            combined_fmt = f"{date_format} {time_format}"
        elif " " in date_format:
            combined_fmt = date_format
        elif len(t_clean) == 8 and t_clean.count(":") == 2:
            combined_fmt = f"{date_format} HH:mm:ss"
        elif len(t_clean) == 5 and t_clean.count(":") == 1:
            combined_fmt = f"{date_format} HH:mm"
        elif "." in t_clean:
            combined_fmt = f"{date_format} HH:mm:ss.SSS"
        else:
            combined_fmt = f"{date_format} HH:mm:ss"

    py_fmt = _java_date_format_to_python(combined_fmt)
    try:
        dt = datetime.strptime(combined_str, py_fmt).replace(tzinfo=UTC)
        return dt.replace(tzinfo=UTC)
    except ValueError:
        pass

    fallback_fmts = [
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%Y%m%d %H:%M:%S",
        "%Y%m%d %H:%M",
        "%Y%m%d",
        "%Y.%m.%d",
        "%Y-%m-%d",
        "%d%m%Y",
    ]
    for fb in fallback_fmts:
        try:
            return datetime.strptime(combined_str, fb).replace(tzinfo=UTC)
        except ValueError:
            pass

    return None


def _parse_double_special(val: str) -> float:
    """Parse numeric values, including European comma decimals."""
    s = val.strip().replace(" ", "")
    if not s:
        return 0.0
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s)


def _correct_mt5_tick_data(
    records: list[tuple[datetime, float, float, float]],
) -> list[tuple[datetime, float, float, float]]:
    """
    MT5 Tick Feed Sparse Price Correction.

    Holds forward the last known non-zero Bid and Ask values.
    """
    if not records:
        return []

    corrected: list[tuple[datetime, float, float, float]] = []
    last_bid: float | None = None
    last_ask: float | None = None

    for r in records:
        dt, ask, bid, vol = r
        if ask > 0:
            last_ask = ask
        if bid > 0:
            last_bid = bid

        eff_ask = ask if ask > 0 else (last_ask if last_ask is not None else 0.0)
        eff_bid = bid if bid > 0 else (last_bid if last_bid is not None else 0.0)

        if eff_ask > 0 and eff_bid == 0:
            eff_bid = eff_ask
        elif eff_bid > 0 and eff_ask == 0:
            eff_ask = eff_bid

        corrected.append((dt, eff_ask, eff_bid, vol))

    return corrected


def _heuristic_format_detection(sample_lines: list[str]) -> _CustomDataFormat | None:
    """Fallback heuristic detection identifying delimiters and column shapes."""
    if not sample_lines:
        return None

    first = sample_lines[0]
    sep = ","
    if first.count("\t") > first.count(","):
        sep = "\t"
    elif first.count(";") > first.count(","):
        sep = ";"

    tokens = [t.strip() for t in first.split(sep) if t.strip()]
    num_cols = len(tokens)

    if num_cols >= 7:
        return _CustomDataFormat(
            name="Auto-Detected-OHLCV",
            separator=sep,
            date_format="yyyy.MM.dd",
            skip_rows=0,
            skip_columns=0,
            columns=["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
        )
    if num_cols == 4:
        return _CustomDataFormat(
            name="Auto-Detected-Tick",
            separator=sep,
            date_format="yyyy.MM.dd HH:mm:ss",
            skip_rows=0,
            skip_columns=0,
            columns=["Date & Time", "Ask", "Bid", "Volume"],
        )

    return None


def _read_and_parse_file(  # noqa: C901, PLR0912, PLR0915 -- preserved source parser.
    text: str,
    fmt: _CustomDataFormat,
    error_handling: int = 0,
    timeframe: str = "auto",
    show_progress: bool = True,
) -> tuple[pd.DataFrame, str]:
    """Parse supplied text with the owner script's policies."""
    t0 = time.perf_counter()
    cols = fmt.columns
    is_tick = fmt.is_tick_format

    date_idx: int | None = None
    time_idx: int | None = None
    dt_idx: int | None = None
    open_idx: int | None = None
    high_idx: int | None = None
    low_idx: int | None = None
    close_idx: int | None = None
    ask_idx: int | None = None
    bid_idx: int | None = None
    vol_indices: list[int] = []

    for i, c in enumerate(cols):
        cl = c.lower().strip()
        if cl == "date":
            date_idx = i
        elif cl == "time":
            time_idx = i
        elif cl in ("date & time", "datetime"):
            dt_idx = i
        elif cl == "open":
            open_idx = i
        elif cl == "high":
            high_idx = i
        elif cl == "low":
            low_idx = i
        elif cl == "close":
            close_idx = i
        elif cl == "ask":
            ask_idx = i
        elif cl == "bid":
            bid_idx = i
        elif cl == "volume":
            vol_indices.append(i)

    sep = fmt.separator
    skip_r = fmt.skip_rows
    skip_c = fmt.skip_columns
    date_fmt = fmt.date_format
    time_fmt = fmt.time_format

    ts_list: list[int] = []
    open_list: list[float] = []
    high_list: list[float] = []
    low_list: list[float] = []
    close_list: list[float] = []
    ask_list: list[float] = []
    bid_list: list[float] = []
    vol_list: list[float] = []

    line_num = 0
    errors_encountered = 0

    with io.StringIO(text) as f:
        for _ in range(skip_r):
            f.readline()
            line_num += 1

        for line in f:
            line_num += 1
            line_str = line.strip()
            if not line_str:
                continue

            parts = line_str.split(sep)
            if skip_c > 0:
                parts = parts[skip_c:]

            if len(parts) < len(cols):
                errors_encountered += 1
                if error_handling == 0:
                    raise ValueError(
                        f"Line {line_num}: expected {len(cols)} columns, "
                        f"got {len(parts)}"
                    )
                continue

            # Parse timestamp
            d_val: str | None = None
            t_val: str | None = None
            if dt_idx is not None:
                d_val = parts[dt_idx]
            elif date_idx is not None:
                d_val = parts[date_idx]
                if time_idx is not None:
                    t_val = parts[time_idx]

            if not d_val:
                errors_encountered += 1
                if error_handling == 0:
                    raise ValueError(f"Line {line_num}: missing date value")
                continue

            parsed_dt = _parse_date_time_components(d_val, t_val, date_fmt, time_fmt)
            if parsed_dt is None:
                errors_encountered += 1
                if error_handling == 0:
                    raise ValueError(
                        f"Line {line_num}: could not parse date "
                        f"'{d_val}' with format '{date_fmt}'"
                    )
                continue

            epoch_ms = int(parsed_dt.timestamp() * 1000)

            # Parse volume
            total_vol = 0.0
            for vi in vol_indices:
                if vi < len(parts):
                    try:
                        total_vol += _parse_double_special(parts[vi])
                    except ValueError:
                        logger.warning("File volume ignored at line %d", line_num)

            try:
                if is_tick:
                    ask_v = (
                        _parse_double_special(parts[ask_idx])
                        if ask_idx is not None
                        else 0.0
                    )
                    bid_v = (
                        _parse_double_special(parts[bid_idx])
                        if bid_idx is not None
                        else 0.0
                    )
                    ask_list.append(ask_v)
                    bid_list.append(bid_v)
                    vol_list.append(total_vol)
                    ts_list.append(epoch_ms)
                else:
                    op = (
                        _parse_double_special(parts[open_idx])
                        if open_idx is not None
                        else 0.0
                    )
                    hi = (
                        _parse_double_special(parts[high_idx])
                        if high_idx is not None
                        else 0.0
                    )
                    lo = (
                        _parse_double_special(parts[low_idx])
                        if low_idx is not None
                        else 0.0
                    )
                    close_value = (
                        _parse_double_special(parts[close_idx])
                        if close_idx is not None
                        else 0.0
                    )
                    open_list.append(op)
                    high_list.append(hi)
                    low_list.append(lo)
                    close_list.append(close_value)
                    vol_list.append(total_vol)
                    ts_list.append(epoch_ms)
            except (ValueError, IndexError, OverflowError) as e:
                errors_encountered += 1
                if error_handling == 0:
                    raise ValueError(
                        f"Line {line_num}: error parsing numeric prices: {e}"
                    ) from e
                continue

    if not ts_list:
        logger.warning("No records parsed from supplied content")
        return pd.DataFrame(), "UNKNOWN"

    ts_arr = np.array(ts_list, dtype=np.int64)

    # MT5 tick correction if applicable
    if is_tick and "metatrader5" in fmt.name.lower():
        corrected = _correct_mt5_tick_data(
            list(
                zip(
                    [datetime.fromtimestamp(t / 1000.0, tz=UTC) for t in ts_list],
                    ask_list,
                    bid_list,
                    vol_list,
                    strict=True,
                )
            )
        )
        ask_arr = np.array([c[1] for c in corrected], dtype=np.float64)
        bid_arr = np.array([c[2] for c in corrected], dtype=np.float64)
        vol_arr = np.array([c[3] for c in corrected], dtype=np.float64)
    elif is_tick:
        ask_arr = np.array(ask_list, dtype=np.float64)
        bid_arr = np.array(bid_list, dtype=np.float64)
        vol_arr = np.array(vol_list, dtype=np.float64)
    else:
        open_arr = np.array(open_list, dtype=np.float64)
        high_arr = np.array(high_list, dtype=np.float64)
        low_arr = np.array(low_list, dtype=np.float64)
        close_arr = np.array(close_list, dtype=np.float64)
        vol_arr = np.array(vol_list, dtype=np.float64)

    # Chronological validation & auto-reversal
    if len(ts_arr) > 1 and ts_arr[0] > ts_arr[-1]:
        if show_progress:
            logger.info(
                "File supplied content is in descending chronological order. Reversing."
            )
        ts_arr = ts_arr[::-1]
        vol_arr = vol_arr[::-1]
        if is_tick:
            ask_arr = ask_arr[::-1]
            bid_arr = bid_arr[::-1]
        else:
            open_arr = open_arr[::-1]
            high_arr = high_arr[::-1]
            low_arr = low_arr[::-1]
            close_arr = close_arr[::-1]

    # Timeframe determination
    resolved_tf = timeframe.upper().strip()
    if resolved_tf in ("AUTO", "RECOGNIZE AUTOMATICALLY"):
        if is_tick:
            resolved_tf = "TICK"
        elif len(ts_arr) > 1:
            diffs = np.diff(ts_arr)
            diffs = diffs[diffs > 0]
            if len(diffs) > 0:
                med_ms = np.median(diffs)
                if med_ms <= 1000:
                    resolved_tf = "TICK"
                elif 50000 <= med_ms <= 70000:
                    resolved_tf = "M1"
                elif 280000 <= med_ms <= 320000:
                    resolved_tf = "M5"
                elif 850000 <= med_ms <= 950000:
                    resolved_tf = "M15"
                elif 1700000 <= med_ms <= 1900000:
                    resolved_tf = "M30"
                elif 3500000 <= med_ms <= 3700000:
                    resolved_tf = "H1"
                elif 14000000 <= med_ms <= 15000000:
                    resolved_tf = "H4"
                elif 80000000 <= med_ms <= 90000000:
                    resolved_tf = "D1"
                else:
                    resolved_tf = "M1"
            else:
                resolved_tf = "M1"
        else:
            resolved_tf = "M1"

    dt_series = pd.to_datetime(ts_arr, unit="ms", utc=True)
    if is_tick:
        df = pd.DataFrame(
            {
                "timestamp": dt_series,
                "ask": ask_arr,
                "bid": bid_arr,
                "volume": np.round(vol_arr).astype(np.uint64),
            }
        )
    else:
        df = pd.DataFrame(
            {
                "timestamp": dt_series,
                "open": open_arr,
                "high": high_arr,
                "low": low_arr,
                "close": close_arr,
                "volume": np.round(vol_arr).astype(np.uint64),
            }
        )

    elapsed = time.perf_counter() - t0
    rate = len(df) / max(elapsed, 0.001)
    if show_progress:
        logger.info(
            "Parsed %d records (%s) from supplied content in %.2fs (%.0f rows/sec)",
            len(df),
            resolved_tf,
            elapsed,
            rate,
        )

    df.attrs["ignored_rows"] = errors_encountered
    return df, resolved_tf


def _ticks_to_m1(
    ts_ms: np.ndarray,
    asks: np.ndarray,
    bids: np.ndarray,
    vols: np.ndarray,
    candle_type: str = "BID",
) -> pd.DataFrame:
    """Transforms raw tick arrays into standardized 1-minute (M1) OHLCV candle bars."""
    if len(ts_ms) == 0:
        return pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

    prices = asks if candle_type.upper() == "ASK" else bids
    minute_ts = (ts_ms // 60000) * 60000
    unique_minutes, first_indices = np.unique(minute_ts, return_index=True)

    _, last_rev = np.unique(minute_ts[::-1], return_index=True)
    last_indices = len(minute_ts) - 1 - last_rev

    opens = prices[first_indices]
    closes = prices[last_indices]
    highs = np.maximum.reduceat(prices, first_indices)
    lows = np.minimum.reduceat(prices, first_indices)
    tot_vols = np.add.reduceat(vols, first_indices)

    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(unique_minutes, unit="ms", utc=True),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": np.round(tot_vols).astype(np.uint64),
        }
    )


def _resample_m1(df_m1: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resamples M1 candles to higher timeframes (M5..D1, W1)."""
    tf = timeframe.lower().strip()
    if df_m1.empty or tf == "m1":
        return df_m1

    freq_map = {
        "m5": "5min",
        "m15": "15min",
        "m30": "30min",
        "h1": "1h",
        "h2": "2h",
        "h4": "4h",
        "d1": "1D",
        "w1": "1W",
    }
    freq = freq_map.get(tf, tf)
    ts_col = "timestamp" if "timestamp" in df_m1.columns else "DateTime"
    df_idx = df_m1.set_index(ts_col)
    open_c = "open" if "open" in df_m1.columns else "Open"
    high_c = "high" if "high" in df_m1.columns else "High"
    low_c = "low" if "low" in df_m1.columns else "Low"
    close_c = "close" if "close" in df_m1.columns else "Close"
    vol_c = "volume" if "volume" in df_m1.columns else "Volume"

    return (
        df_idx.resample(freq)
        .agg(
            {
                open_c: "first",
                high_c: "max",
                low_c: "min",
                close_c: "last",
                vol_c: "sum",
            }
        )
        .dropna()
        .reset_index()
    )


def _dataframe_to_canonical_m1(df: pd.DataFrame) -> Any:
    if pa is None or M1_SCHEMA is None:
        raise ImportError("pyarrow is required for canonical parquet conversion.")
    if df.empty:
        return pa.Table.from_arrays(
            [
                pa.array([], type=pa.timestamp("ms", tz="UTC")),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.uint64()),
            ],
            schema=M1_SCHEMA,
        )

    ts_col = "timestamp" if "timestamp" in df.columns else "DateTime"
    ts = df[ts_col].values
    if ts.dtype.kind == "M":
        ts_ms = ts.astype("datetime64[ms]").astype(np.int64)
    else:
        ts_ms = (
            pd.to_datetime(ts, utc=True)
            .values.astype("datetime64[ms]")
            .astype(np.int64)
        )

    dt_arr = pa.array(ts_ms, type=pa.timestamp("ms", tz="UTC"))
    open_arr = pa.array(
        df["open" if "open" in df.columns else "Open"].values.astype(np.float64),
        type=pa.float64(),
    )
    high_arr = pa.array(
        df["high" if "high" in df.columns else "High"].values.astype(np.float64),
        type=pa.float64(),
    )
    low_arr = pa.array(
        df["low" if "low" in df.columns else "Low"].values.astype(np.float64),
        type=pa.float64(),
    )
    close_arr = pa.array(
        df["close" if "close" in df.columns else "Close"].values.astype(np.float64),
        type=pa.float64(),
    )
    vol_col = "volume" if "volume" in df.columns else "Volume"
    vol_arr = pa.array(np.round(df[vol_col].values).astype(np.uint64), type=pa.uint64())

    return pa.Table.from_arrays(
        [dt_arr, open_arr, high_arr, low_arr, close_arr, vol_arr], schema=M1_SCHEMA
    )


def _dataframe_to_canonical_ticks(df: pd.DataFrame) -> Any:
    if pa is None or TICK_SCHEMA is None:
        raise ImportError("pyarrow is required for canonical parquet conversion.")
    if df.empty:
        return pa.Table.from_arrays(
            [
                pa.array([], type=pa.timestamp("ms", tz="UTC")),
                pa.array([], type=pa.int64()),
                pa.array([], type=pa.int64()),
                pa.array([], type=pa.uint64()),
            ],
            schema=TICK_SCHEMA,
        )

    ts_col = "timestamp" if "timestamp" in df.columns else "DateTime"
    ts = df[ts_col].values
    if ts.dtype.kind == "M":
        ts_ms = ts.astype("datetime64[ms]").astype(np.int64)
    else:
        ts_ms = (
            pd.to_datetime(ts, utc=True)
            .values.astype("datetime64[ms]")
            .astype(np.int64)
        )

    dt_arr = pa.array(ts_ms, type=pa.timestamp("ms", tz="UTC"))
    ask_col = "ask" if "ask" in df.columns else "Ask"
    bid_col = "bid" if "bid" in df.columns else "Bid"

    ask_vals = df[ask_col].values
    bid_vals = df[bid_col].values
    if ask_vals.dtype == np.int64:
        ask_scaled = ask_vals
        bid_scaled = bid_vals
    else:
        ask_scaled = np.round(ask_vals * 1_000_000).astype(np.int64)
        bid_scaled = np.round(bid_vals * 1_000_000).astype(np.int64)

    if "volume" in df.columns:
        vol_arr = np.round(df["volume"].values).astype(np.uint64)
    elif "Volume" in df.columns:
        vol_arr = np.round(df["Volume"].values).astype(np.uint64)
    else:
        vol_arr = np.zeros(len(df), dtype=np.uint64)

    return pa.Table.from_arrays(
        [
            dt_arr,
            pa.array(ask_scaled, type=pa.int64()),
            pa.array(bid_scaled, type=pa.int64()),
            pa.array(vol_arr, type=pa.uint64()),
        ],
        schema=TICK_SCHEMA,
    )


def detect_format(  # noqa: C901, PLR0912 -- source format scoring sequence.
    text: str, custom: tuple[_CustomDataFormat, ...] = ()
) -> _CustomDataFormat | None:
    """Apply source candidate ordering and price/date tests to supplied text."""
    sample_lines = [line.strip() for line in text.splitlines()[:50] if line.strip()][
        :25
    ]
    if not sample_lines:
        return None
    all_candidates = sorted(
        [*custom, *PREDEFINED_FORMATS], key=lambda fmt: fmt.order, reverse=True
    )

    for cand in all_candidates:
        test_slice = sample_lines[cand.skip_rows :]
        if not test_slice:
            continue

        sep = cand.separator
        success_count = 0
        total_eval = min(len(test_slice), 10)

        for line in test_slice[:total_eval]:
            parts = line.split(sep)
            if cand.skip_columns > 0:
                parts = parts[cand.skip_columns :]

            if len(parts) < len(cand.columns):
                break

            date_str: str | None = None
            time_str: str | None = None
            has_price = False

            for c_idx, c_name in enumerate(cand.columns):
                if c_idx >= len(parts):
                    break
                val = parts[c_idx].strip()
                if c_name == "Date":
                    date_str = val
                elif c_name == "Time":
                    time_str = val
                elif c_name == "Date & Time":
                    date_str = val
                elif c_name in ("Open", "Close", "High", "Low", "Ask", "Bid"):
                    try:
                        _parse_double_special(val)
                        has_price = True
                    except ValueError:
                        pass

            if date_str and has_price:
                parsed_dt = _parse_date_time_components(
                    date_val=date_str,
                    time_val=time_str,
                    date_format=cand.date_format,
                    time_format=cand.time_format,
                )
                if parsed_dt is not None:
                    success_count += 1

        if success_count >= max(2, total_eval // 2):
            return cand

    return _heuristic_format_detection(sample_lines)


class FormatSpec(Document):
    """Immutable source format settings exposed by catalog schema."""

    name: str = Field(min_length=1, max_length=80)
    separator: str = Field(default=",", min_length=1, max_length=4)
    date_format: str = Field(default="yyyy.MM.dd", min_length=1, max_length=100)
    time_format: str | None = Field(default=None, max_length=100)
    skip_rows: int = Field(default=0, ge=0, le=10000)
    skip_columns: int = Field(default=0, ge=0, le=100)
    columns: tuple[
        Literal[
            "Date",
            "Time",
            "Date & Time",
            "Ask",
            "Bid",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Unused",
        ],
        ...,
    ] = Field(min_length=1, max_length=100)

    def descriptor(self) -> _CustomDataFormat:
        """Build the parser's local descriptor without filesystem lookup."""
        return _CustomDataFormat(**{**self.model_dump(), "columns": list(self.columns)})


class FileRequest(Document):
    """Bounded uploaded content and explicit parser options."""

    content: str = Field(min_length=1, max_length=8 * 1024 * 1024)
    format: FormatSpec
    symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    instrument: str = Field(default="", max_length=80)
    timeframe: Literal[
        "auto", "TICK", "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
    ] = "auto"
    error_handling: Literal[0, 1] = 0


class FileDefinition(Document):
    """Explicit empty file-data definition, ready for later real imports."""

    symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    instrument: str = Field(min_length=1, max_length=80)
    timeframe: Literal["TICK", "M1", "D1"] = "M1"


def parse_request(request: FileRequest) -> tuple[pd.DataFrame, str]:
    """Execute the source parser against supplied text only."""
    frame, timeframe = _read_and_parse_file(
        request.content,
        request.format.descriptor(),
        error_handling=request.error_handling,
        timeframe=request.timeframe,
    )
    if request.format.descriptor().is_tick_format:
        timeframe = "TICK"
    elif timeframe == "TICK":
        raise ValueError("Tick timeframe requires tick columns")
    return frame, timeframe


def import_tables(
    frame: pd.DataFrame, timeframe: str, is_tick: bool
) -> tuple[tuple[str, Any, bool], ...]:
    """Preserve raw ticks and the script's default BID minute candles."""
    if not is_tick:
        return ((timeframe, _dataframe_to_canonical_m1(frame), False),)
    stamps = frame["timestamp"].to_numpy(dtype="datetime64[ms]").astype(np.int64)
    minutes = _ticks_to_m1(
        stamps,
        frame["ask"].to_numpy(),
        frame["bid"].to_numpy(),
        frame["volume"].to_numpy(),
    )
    return (
        ("TICK", _dataframe_to_canonical_ticks(frame), True),
        ("M1", _dataframe_to_canonical_m1(minutes), False),
    )


@dataclass
class FileRuntime:
    """Prepared file source; host custody owns every durable write."""

    market: MarketAccess
    jobs: JobAccess
    settings: SettingsAccess | None = None
    progress: dict[str, dict[str, Any]] = field(default_factory=dict)

    def custom_formats(self) -> tuple[FormatSpec, ...]:
        """Read only this source's validated custom descriptors."""
        if self.settings is None:
            return ()
        saved = self.settings.get("formats") or {"formats": []}
        return tuple(FormatSpec.model_validate(item) for item in saved["formats"])

    def edit_format(self, operation: str, values: dict[str, JsonValue]) -> JsonValue:
        """Persist explicit format edits through host settings custody."""
        if self.settings is None:
            raise ValueError("Custom format settings capability unavailable")
        formats = {fmt.name: fmt for fmt in self.custom_formats()}
        if operation == "formats.save":
            fmt = FormatSpec.model_validate(values.get("format"))
            if (
                fmt.name in {item.name for item in PREDEFINED_FORMATS}
                or fmt.name == "Custom"
            ):
                raise ValueError("Choose a unique custom format name")
            if fmt.name in formats and not values.get("replace", False):
                raise ValueError("Custom format already exists")
            formats[fmt.name] = fmt
        else:
            name = values.get("name")
            if not isinstance(name, str) or name not in formats:
                raise ValueError("Custom format unavailable")
            del formats[name]
        self.settings.set(
            "formats",
            {"formats": [fmt.model_dump(mode="json") for fmt in formats.values()]},
        )
        return {"success": True}

    async def acquire(self, request: FileRequest, progress: dict[str, Any]) -> None:
        """Parse, convert and publish the owner's yearly/monthly partitions."""
        frame, timeframe = await self.jobs.offload(parse_request, request)
        if frame.empty:
            raise ValueError("No usable rows in supplied file")
        is_tick = request.format.descriptor().is_tick_format
        tables = await self.jobs.offload(import_tables, frame, timeframe, is_tick)
        progress["ignored_rows"] = int(frame.attrs.get("ignored_rows", 0))
        progress["total_partitions"] = sum(
            len(
                set(
                    pd.to_datetime(
                        table.column("DateTime").cast(pa.int64()).to_numpy(),
                        unit="ms",
                        utc=True,
                    ).strftime("%Y-%m" if ticks else "%Y")
                )
            )
            for _, table, ticks in tables
        )
        for index, (period_timeframe, table, ticks) in enumerate(tables):
            dataset_id = await self.publish_table(
                request, period_timeframe, table, ticks, progress
            )
            if index == 0:
                progress["dataset_id"] = dataset_id
        progress["rows"] = len(frame)
        logger.info(
            "File import published: id=%s rows=%d", progress["dataset_id"], len(frame)
        )

    async def publish_table(
        self,
        request: FileRequest,
        timeframe: str,
        table: Any,
        is_tick: bool,
        progress: dict[str, Any],
    ) -> str:
        """Merge a script output into revision-checked host partitions."""
        dataset_id = self.market.register_source(
            source="File import",
            symbol=request.symbol,
            underlying=request.symbol,
            instrument=request.instrument or request.symbol,
            timeframe=timeframe,
            options={},
        )
        stamps = table.column("DateTime").cast(pa.int64()).to_numpy()
        dates = pd.to_datetime(stamps, unit="ms", utc=True)
        periods = dates.strftime("%Y-%m" if is_tick else "%Y")
        revisions = {
            record["period"]: record
            for record in self.market.source_partitions(dataset_id)
        }
        for period in sorted(set(periods)):
            await asyncio.sleep(0)
            incoming = table.take(pa.array(np.where(periods == period)[0]))
            prior = revisions.get(period)
            if prior:
                old = self.market.read_source_partition(dataset_id, period)
                combined = pa.concat_tables([incoming, old])
                combined_stamps = (
                    combined.column("DateTime").cast(pa.int64()).to_numpy()
                )
                _, unique_indices = np.unique(combined_stamps, return_index=True)
                order = unique_indices[np.argsort(combined_stamps[unique_indices])]
                final = combined.take(pa.array(order))
            else:
                part_stamps = incoming.column("DateTime").cast(pa.int64()).to_numpy()
                final = incoming.take(pa.array(np.argsort(part_stamps)))
            self.market.publish_source(
                dataset_id,
                period,
                final,
                expected_revision=prior["revision"] if prior else 0,
            )
            progress["published_partitions"] += 1
        return dataset_id

    async def invoke(self, operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0911 -- cohesive source operation boundary.
        """Validate all operations without interpreting browser state as data."""
        logger.info("File import operation: %s", operation)
        values = payload if isinstance(payload, dict) else {}
        if operation == "add":
            definition = FileDefinition.model_validate(values)
            dataset_id = self.market.register_source(
                source="File import",
                symbol=definition.symbol,
                underlying=definition.symbol,
                instrument=definition.instrument,
                timeframe=definition.timeframe,
                options={},
            )
            return {"id": dataset_id}
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
                    "formats": [fmt.to_dict() for fmt in PREDEFINED_FORMATS],
                    "custom_formats": [
                        fmt.descriptor().to_dict() for fmt in self.custom_formats()
                    ],
                    "schema": FileRequest.model_json_schema(),
                },
            )
        if operation in ("formats.save", "formats.delete"):
            return self.edit_format(operation, values)
        if operation == "detect":
            text = values.get("content")
            if not isinstance(text, str) or not text:
                raise ValueError("Supply file contents for detection")
            detected = detect_format(
                text, tuple(fmt.descriptor() for fmt in self.custom_formats())
            )
            if detected is None:
                raise ValueError("Select a file format and map its columns")
            return cast("JsonValue", detected.to_dict())
        if operation == "preview":
            frame, timeframe = parse_request(FileRequest.model_validate(values))
            return cast(
                "JsonValue",
                {
                    "timeframe": timeframe,
                    "rows": len(frame),
                    "ignored_rows": int(frame.attrs.get("ignored_rows", 0)),
                    "preview": [
                        {**row, "timestamp": row["timestamp"].isoformat()}
                        for row in frame.head(20).to_dict("records")
                    ],
                },
            )
        if operation == "import.start":
            if not self.market.source_available():
                raise ValueError("Script-backed catalog migration is required")
            request = FileRequest.model_validate(values)
            progress = {
                "rows": 0,
                "published_partitions": 0,
                "total_partitions": 0,
                "ignored_rows": 0,
            }

            async def run() -> None:
                await self.acquire(request, progress)

            job = self.jobs.submit(Budget(1, 256 * 1024 * 1024, 600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("import.status", "import.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "import.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        raise ValueError("Unknown file import operation")

    async def close(self) -> None:
        """Stop owned jobs before dropping this source's local state."""
        await self.jobs.close()
        logger.info("File import source closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Attach the cohesive parser through explicit host capabilities."""
    if context.market_data is None or context.jobs is None:
        raise ValueError("File import requires market data and job capabilities")
    runtime = FileRuntime(context.market_data, context.jobs, context.settings)
    return PreparedContribution(
        (
            "catalog",
            "add",
            "formats.save",
            "formats.delete",
            "detect",
            "preview",
            "import.start",
            "import.status",
            "import.cancel",
        ),
        runtime.invoke,
        runtime.close,
    )
