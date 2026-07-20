"""Shared normalization helpers for market data sources."""

import math
from datetime import UTC
from typing import Any

import pandas as pd

from app.utils.logger import logger

VOLUME_KIND_TICK: str = "tick_volume"
VOLUME_KIND_REAL: str = "real_volume"
VOLUME_KIND_BROKER: str = "broker_volume"
VOLUME_KIND_SYNTHETIC: str = "synthetic_volume"
VOLUME_KIND_UNKNOWN: str = "unknown"

_BROKER_BACKED_SOURCES: frozenset[str] = frozenset(
    {"mt5", "ctrader", "dukascopy", "binance", "yahoo"}
)

_PRICE_FIELDS: tuple[str, ...] = ("open", "high", "low", "close", "bid", "ask", "last")


def resolve_volume_kind(source: str, data_kind: str) -> str:
    """Disclose the volume kind represented by a source's bar/volume records.

    Args:
        source: Source adapter identifier (e.g. 'synthetic', 'mt5', 'csv').
        data_kind: Requested data kind ('ohlcv', 'ticks', 'spreads', 'volume').

    Returns:
        str: One of 'tick_volume', 'real_volume', 'broker_volume',
        'synthetic_volume', or 'unknown'.
    """
    if data_kind not in ("ohlcv", "volume"):
        return VOLUME_KIND_UNKNOWN
    if source == "synthetic":
        return VOLUME_KIND_SYNTHETIC
    if source in _BROKER_BACKED_SOURCES:
        return VOLUME_KIND_BROKER
    return VOLUME_KIND_TICK


def _is_non_finite(value: float) -> bool:
    """Return True for NaN or +/-infinity values."""
    return math.isnan(value) or math.isinf(value)


def _timestamp_flags(timestamp: Any, previous_timestamp: str | None) -> list[str]:  # noqa: ANN401
    """Detect duplicate/non-monotonic timestamp ordering against the prior record."""
    if previous_timestamp is None:
        return []
    try:
        current_dt = pd.to_datetime(timestamp)
        previous_dt = pd.to_datetime(previous_timestamp)
    except (ValueError, TypeError):
        return ["missing_field"]
    if current_dt == previous_dt:
        return ["duplicate_timestamp"]
    if current_dt < previous_dt:
        return ["non_monotonic_timestamp"]
    return []


def _price_field_flags(record: dict[str, Any]) -> list[str]:
    """Detect non-finite, negative, or zero prices across known price fields."""
    flags: list[str] = []
    for price_field in _PRICE_FIELDS:
        if price_field not in record:
            continue
        try:
            value = float(record[price_field])
        except (TypeError, ValueError):
            continue
        if _is_non_finite(value):
            flags.append("non_finite_price")
        elif value < 0:
            flags.append("negative_price")
        elif value == 0:
            flags.append("zero_price")
    return flags


def _ohlc_range_flags(record: dict[str, Any]) -> list[str]:
    """Detect out-of-range OHLC and inverted bid/ask boundaries."""
    flags: list[str] = []
    if "high" in record and "low" in record:
        try:
            if float(record["low"]) > float(record["high"]):
                flags.append("out_of_range_ohlc")
        except (TypeError, ValueError):
            pass
    if "bid" in record and "ask" in record:
        try:
            if float(record["ask"]) < float(record["bid"]):
                flags.append("inverted_bid_ask")
        except (TypeError, ValueError):
            pass
    return flags


def build_data_quality_flags(
    record: dict[str, Any],
    *,
    previous_timestamp: str | None = None,
) -> list[str]:
    """Compute deterministic data-quality flags for one normalized record.

    This is a diagnostic-only helper: it reports issues, it never repairs,
    interpolates, or silently drops fields.

    Args:
        record: Normalized OHLCV, tick, or spread record.
        previous_timestamp: Immediately preceding record's timestamp string,
            used to detect duplicate or non-monotonic timestamps.

    Returns:
        list[str]: Bounded, deterministic quality flag identifiers.
    """
    timestamp = record.get("timestamp")
    if not timestamp:
        return ["missing_field"]

    return [
        *_timestamp_flags(timestamp, previous_timestamp),
        *_price_field_flags(record),
        *_ohlc_range_flags(record),
    ]


def summarize_data_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize deterministic data-quality flags across a record batch.

    Use this to expose quality evidence at the official tool boundary without
    embedding per-record diagnostic keys into the native compatibility record
    shape.

    Args:
        records: Normalized OHLCV, tick, or spread records.

    Returns:
        dict[str, Any]: Mapping with `flagged_record_count` and
        `flag_counts` (flag identifier to occurrence count).
    """
    flag_counts: dict[str, int] = {}
    flagged_record_count = 0
    previous_timestamp: str | None = None
    for record in records:
        flags = build_data_quality_flags(record, previous_timestamp=previous_timestamp)
        if flags:
            flagged_record_count += 1
            for flag in flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        previous_timestamp = record.get("timestamp", previous_timestamp)

    logger.debug(
        f"summarize_data_quality: {flagged_record_count} of {len(records)} "
        f"record(s) flagged across {len(flag_counts)} flag type(s)."
    )
    return {
        "flagged_record_count": flagged_record_count,
        "flag_counts": flag_counts,
    }


def normalize_timestamp_value(value: Any) -> str:  # noqa: ANN401
    """Return a UTC ISO timestamp string for provider or file values.

    Args:
        value: Timestamp-like provider value.

    Returns:
        str: ISO formatted timestamp string.
    """
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(pd.to_datetime(value).isoformat())


def bars_dataframe_to_records(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    source: str,
) -> list[dict[str, Any]]:
    """Convert a provider OHLCV dataframe into normalized gateway records.

    Args:
        df: Provider dataframe with standard OHLCV columns.
        symbol: Requested financial symbol.
        timeframe: Requested bar timeframe.
        source: Source identifier.

    Returns:
        list[dict[str, Any]]: Normalized OHLCV dictionaries.
    """
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        volume = float(row["Volume"])
        records.append(
            {
                "timestamp": normalize_timestamp_value(row["Timestamp"]),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": volume,
                "tick_volume": volume,
                "real_volume": 0.0,
                "spread": float(row["Spread"]),
                "source": source,
                "symbol": symbol,
                "timeframe": timeframe,
            }
        )
    return records


def ticks_dataframe_to_records(
    df: pd.DataFrame,
    symbol: str,
    source: str,
) -> list[dict[str, Any]]:
    """Convert a provider tick dataframe into normalized gateway records.

    Args:
        df: Provider dataframe with standard tick columns.
        symbol: Requested financial symbol.
        source: Source identifier.

    Returns:
        list[dict[str, Any]]: Normalized tick dictionaries.
    """
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        records.append(
            {
                "timestamp": normalize_timestamp_value(row["Timestamp"]),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
                "last": float(row["last"]),
                "volume": float(row["volume"]),
                "spread": float(row["spread"]),
                "source": source,
                "symbol": symbol,
            }
        )
    return records


def mt5_ticks_dataframe_to_records(
    df: pd.DataFrame,
    symbol: str,
    source: str,
) -> list[dict[str, Any]]:
    """Convert an MT5 tick dataframe into normalized gateway records.

    Args:
        df: MT5 tick dataframe.
        symbol: Requested financial symbol.
        source: Source identifier.

    Returns:
        list[dict[str, Any]]: Normalized tick dictionaries.
    """
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        time_msc = int(row.get("time_msc", 0))
        if time_msc > 0:
            dt = pd.to_datetime(time_msc, unit="ms", utc=True)
        else:
            dt = pd.to_datetime(int(row.get("time", 0)), unit="s", utc=True)

        bid = float(row.get("bid", 0.0))
        ask = float(row.get("ask", 0.0))
        records.append(
            {
                "timestamp": dt.isoformat(),
                "bid": bid,
                "ask": ask,
                "last": float(row.get("last", 0.0)),
                "volume": float(row.get("volume", 0.0)),
                "spread": ask - bid,
                "source": source,
                "symbol": symbol,
            }
        )
    return records


def _normalize_mt5_file_record(
    record: dict[str, Any],
    symbol: str,
    timeframe: str,
    source: str,
) -> dict[str, Any]:
    """Normalize a single MT5-style file record."""
    date_val = record.get("<DATE>") or record.get("DATE") or ""
    time_val = record.get("<TIME>") or record.get("TIME") or "00:00:00"
    dt_str = f"{str(date_val).replace('.', '-')} {time_val}"
    try:
        dt = pd.to_datetime(dt_str)
        dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
        ts_str = dt.isoformat()
    except (ValueError, TypeError):
        ts_str = dt_str

    def get_float(key: str) -> float:
        val = record.get(key)
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    tick_vol = get_float("<TICKVOL>")
    return {
        "timestamp": ts_str,
        "open": get_float("<OPEN>"),
        "high": get_float("<HIGH>"),
        "low": get_float("<LOW>"),
        "close": get_float("<CLOSE>"),
        "volume": tick_vol,
        "tick_volume": tick_vol,
        "real_volume": get_float("<VOL>"),
        "spread": get_float("<SPREAD>"),
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
    }


def _normalize_standard_file_record(
    record: dict[str, Any],
    symbol: str,
    timeframe: str,
    source: str,
) -> dict[str, Any]:
    """Normalize a single standard OHLCV-style file record."""
    norm_record = dict(record)
    if "timestamp" in norm_record:
        try:
            dt = pd.to_datetime(norm_record["timestamp"])
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
            norm_record["timestamp"] = dt.isoformat()
        except (ValueError, TypeError) as ex:
            logger.warning(
                f"Failed to parse timestamp {norm_record.get('timestamp')}: {ex}"
            )
    norm_record.setdefault("source", source)
    norm_record.setdefault("symbol", symbol)
    norm_record.setdefault("timeframe", timeframe)
    norm_record.setdefault("tick_volume", norm_record.get("volume", 0.0))
    norm_record.setdefault("real_volume", 0.0)
    norm_record.setdefault("spread", 0.0)
    if "volume" not in norm_record:
        norm_record["volume"] = norm_record.get("tick_volume", 0.0)
    return norm_record


def normalize_file_records(
    records: list[dict[str, Any]],
    symbol: str,
    timeframe: str,
    source: str,
) -> list[dict[str, Any]]:
    """Normalize raw or MT5 file records to standard OHLCV schema.

    Args:
        records: Raw records loaded from local files.
        symbol: Requested financial symbol.
        timeframe: Requested bar timeframe.
        source: Source identifier.

    Returns:
        list[dict[str, Any]]: Normalized OHLCV dictionaries.
    """
    if not records:
        return []

    first = records[0]
    is_mt5_style = any(str(k).startswith("<") and str(k).endswith(">") for k in first)

    normalized = []
    for record in records:
        if is_mt5_style:
            normalized.append(
                _normalize_mt5_file_record(record, symbol, timeframe, source)
            )
        else:
            normalized.append(
                _normalize_standard_file_record(record, symbol, timeframe, source)
            )
    return normalized
