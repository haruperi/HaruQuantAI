"""Canonical market frames and provider storage folder names.

Description:
    Encode market observations and resolve provider storage directories without
    changing provider identities or dataset keys.
Purpose:
    FEAT-MARKET-STORAGE: canonical market history serialization and folder ownership.
Key Capabilities:
    - FR-MARKET-STORAGE-tick-volume: preserve recorded uint64 volume and unknown flags.
      Logging: DEBUG records tick encoding; regression tests verify the log.
    - FR-MARKET-STORAGE-provider-folders: map SQ provider IDs to equity/futures folders.
      Logging: DEBUG records folder resolution; mapping regressions verify the log.
Python API Usage:
    provider_storage_name("sq_futures")  # futures
CLI Usage:
    uv run pytest tests/workspace/data_manager/test_sources.py --no-cov
"""

from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa

from app.core.host.logging import get_logger

logger = get_logger(__name__)


def provider_storage_name(provider: str) -> str:
    """Resolve storage-only naming while preserving the provider identifier."""
    safe_component(provider)
    folder = {"sq_equity": "equity", "sq_futures": "futures"}.get(provider, provider)
    logger.debug("FR-MARKET-STORAGE-provider-folders: %s -> %s", provider, folder)
    return folder


TICK_SCHEMA = pa.schema(
    [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Bid", pa.int64()),
        ("Ask", pa.int64()),
        ("Flags", pa.uint16()),
        ("Volume", pa.uint64()),
    ]
)
M1_SCHEMA = pa.schema(
    [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Open", pa.int64()),
        ("High", pa.int64()),
        ("Low", pa.int64()),
        ("Close", pa.int64()),
        ("Volume", pa.uint64()),
    ]
)
_PRICE_MAX = 2**63 - 1
_PRICE_MIN = -(2**63)
_GRID_TOLERANCE = Decimal("0.000001")


def safe_component(value: str) -> str:
    """Validate a filesystem/catalog identity without changing its meaning."""
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[A-Za-z0-9@^$][A-Za-z0-9_.@^$=+-]*", value)
        or ".." in value
        or value.endswith(".")
    ):
        raise ValueError("Use a safe alphanumeric source or symbol")
    return value


def price_columns(timeframe: str) -> list[str]:
    """Return canonical price columns for a supported historical resolution."""
    if timeframe not in (
        "TICK",
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
        "M6",
        "M10",
        "M12",
        "M15",
        "M20",
        "M30",
        "H1",
        "H2",
        "H3",
        "H4",
        "H6",
        "H8",
        "H12",
        "D1",
        "W1",
        "MN1",
    ):
        raise ValueError("Unsupported historical resolution")
    return ["Bid", "Ask"] if timeframe == "TICK" else ["Open", "High", "Low", "Close"]


def _units(value: Any, step: Decimal) -> int:
    try:
        number = Decimal(str(value)) / step
        rounded = number.to_integral_value(rounding=ROUND_HALF_EVEN)
        if not number.is_finite() or abs(number - rounded) > _GRID_TOLERANCE:
            raise ValueError("Price is non-finite or off the instrument tick grid")
        result = int(rounded)
    except (InvalidOperation, OverflowError) as error:
        raise ValueError("Invalid price") from error
    if not _PRICE_MIN <= result <= _PRICE_MAX:
        raise ValueError("Price exceeds signed int64 tick units")
    return result


def _unsigned(value: Any, bits: int) -> int:
    try:
        number = Decimal(str(value))
        if (
            not number.is_finite()
            or number != number.to_integral_value()
            or not 0 <= number < 2**bits
        ):
            raise ValueError("Volume/flags must be non-negative in-range integers")
        return int(number)
    except InvalidOperation as error:
        raise ValueError("Invalid volume or flags") from error


def unsigned_values(
    frame: pd.DataFrame, name: str, bits: int, *, nullable: bool
) -> list[int | None]:
    """Validate integer attributes without inventing values for unknown fields."""
    if name not in frame:
        return [None if nullable else 0] * len(frame)
    return [
        None if nullable and pd.isna(value) else _unsigned(value, bits)
        for value in frame[name]
    ]


def encode_attributes(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    """Encode recorded unsigned attributes, retaining explicitly unknown values."""
    if timeframe != "TICK":
        return {"Volume": unsigned_values(frame, "Volume", 64, nullable=False)}
    logger.debug(
        "FR-MARKET-STORAGE-tick-volume: encoded %d ticks with nullable volumes",
        len(frame),
    )
    return {
        "Flags": unsigned_values(frame, "Flags", 16, nullable=True),
        "Volume": unsigned_values(frame, "Volume", 64, nullable=True),
    }


def encode_frame(frame: pd.DataFrame, timeframe: str, tick_size: float) -> pa.Table:
    """Validate a provider frame and encode prices once into canonical tick units."""
    prices = price_columns(timeframe)
    step = Decimal(str(tick_size))
    if not step.is_finite() or step <= 0:
        raise ValueError("tick_size must be positive and finite")
    if frame.empty or any(column not in frame for column in prices):
        raise ValueError("A non-empty frame with all required prices is required")
    timestamps = frame.get("DateTime", frame.index)
    if "DateTime" not in frame and not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("A UTC DateTime column or DatetimeIndex is required")
    dates = pd.to_datetime(timestamps, utc=True, errors="raise")
    if dates.isna().any():
        raise ValueError("Observation timestamps cannot be missing")
    data: dict[str, Any] = {"DateTime": dates}
    for column in prices:
        data[column] = [_units(value, step) for value in frame[column]]
    data.update(encode_attributes(frame, timeframe))
    if timeframe != "TICK":
        if any(
            not low <= min(open_, close) <= max(open_, close) <= high
            for open_, high, low, close in zip(
                data["Open"], data["High"], data["Low"], data["Close"], strict=True
            )
        ):
            raise ValueError("Invalid OHLC ordering")
        if any(date.second or date.microsecond for date in dates):
            raise ValueError("M1 observations must align to minute boundaries")
    elif any(ask < bid for bid, ask in zip(data["Bid"], data["Ask"], strict=True)):
        raise ValueError("Ask cannot be below bid")
    schema = (TICK_SCHEMA if timeframe == "TICK" else M1_SCHEMA).with_metadata(
        {
            b"haruquantai.price_encoding": b"integer-ticks-v1",
            b"haruquantai.tick_size": str(tick_size).encode(),
        }
    )
    return pa.table(data, schema=schema).sort_by("DateTime")


def catalog_paths(row: dict[str, Any]) -> list[str]:
    """Resolve active catalog files; fall back only for pre-manifest datasets."""
    lineage = json.loads(row.get("lineage_json") or "{}")
    if "partitions" in lineage:
        paths = lineage["partitions"]
        if not isinstance(paths, list) or any(
            not isinstance(path, str) for path in paths
        ):
            raise ValueError("Invalid dataset manifest")
        return paths
    path = Path(row.get("path") or "")
    return (
        [str(path)]
        if path.is_file()
        else [
            str(item)
            for item in sorted(path.rglob("*.parquet"))
            if not any(part.startswith(".") for part in item.relative_to(path).parts)
        ]
        if row.get("path")
        else []
    )


def scan_catalog(row: dict[str, Any], *, decode: bool = False) -> pl.LazyFrame:
    """Scan the active snapshot lazily, optionally decoding integer tick prices."""
    paths = catalog_paths(row)
    if not paths:
        raise ValueError("Dataset has no published partitions")
    schema = (
        pl.Schema(
            {
                "DateTime": pl.Datetime("us", "UTC"),
                "Bid": pl.Int64(),
                "Ask": pl.Int64(),
                "Flags": pl.UInt16(),
                "Volume": pl.UInt64(),
            }
        )
        if row["timeframe"] == "TICK"
        else None
    )
    lazy = pl.scan_parquet(paths, schema=schema, missing_columns="insert")
    if decode:
        lineage = json.loads(row.get("lineage_json") or "{}")
        step = float(lineage["tick_size"])
        prices = price_columns(row["timeframe"])
        schema = lazy.collect_schema()
        exp = Decimal(str(step)).as_tuple().exponent
        precision = max(0, -exp if isinstance(exp, int) else 0)
        lazy = lazy.with_columns(
            [
                (pl.col(column).cast(pl.Float64) * step).round(precision)
                for column in prices
                if schema[column].is_integer()
            ]
        )
    return lazy
