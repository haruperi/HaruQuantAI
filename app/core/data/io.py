"""Canonical market data partition I/O and dynamic resampling.

Description:
    Reads canonical partitions and resamples bars using the shared timeframe
    owner, guarding positive source and target intervals before processing data.
Purpose:
    FEAT-DATA-TIMEFRAMES: Consume one timeframe duration contract.
Key Capabilities:
    - FR-data-io-timeframes: Shared owner emits DEBUG conversion records;
      focused tests verify duration handling and reject unsafe intervals.
Python API Usage:
    DataIO.resample_bars(frame, "H7")
CLI Usage:
    uv run pytest tests/core/data/test_io.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

import polars as pl

from app.core.data import timeframes
from app.core.data.market_storage import price_columns
from app.core.lib.errors import DomainError

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["DataIO"]


class DataIO:
    """Low-level reader and resampling engine for canonical Parquet partitions."""

    @staticmethod
    def empty_frame(timeframe: str, *, decode: bool = True) -> pl.DataFrame:
        """Create an empty Polars DataFrame matching the canonical schema."""
        price_type = pl.Float64 if decode else pl.Int64
        if timeframe.upper() == "TICK":
            schema: dict[str, Any] = {
                "DateTime": pl.Datetime("us", "UTC"),
                "Bid": price_type,
                "Ask": price_type,
                "Flags": pl.UInt16,
            }
        else:
            schema = {
                "DateTime": pl.Datetime("us", "UTC"),
                "Open": price_type,
                "High": price_type,
                "Low": price_type,
                "Close": price_type,
                "Volume": pl.UInt64,
            }
        return pl.DataFrame(schema=schema)

    @classmethod
    def read_partitions(
        cls,
        paths: Sequence[str | Path],
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        decode: bool = True,
        tick_size: float = 0.0001,
        timeframe: str = "M1",
    ) -> pl.DataFrame:
        """Scan Parquet partitions, applying time bounds and price decoding."""
        if not paths:
            return cls.empty_frame(timeframe, decode=decode)

        str_paths: list[str] = []
        for path in paths:
            p = Path(path)
            if not p.is_file():
                raise DomainError(
                    code="CORRUPT_DATASET_STORAGE",
                    message=f"Partition file missing on disk: {p}",
                )
            str_paths.append(str(p))

        lazy = pl.scan_parquet(str_paths)
        if start is not None:
            lazy = lazy.filter(pl.col("DateTime") >= start)
        if end is not None:
            lazy = lazy.filter(pl.col("DateTime") <= end)

        lazy = lazy.sort("DateTime")

        if decode:
            step = float(tick_size)
            prices = price_columns(timeframe)
            schema = lazy.collect_schema()
            exp = Decimal(str(step)).as_tuple().exponent
            precision = max(0, -exp if isinstance(exp, int) else 0)
            lazy = lazy.with_columns(
                [
                    (pl.col(column).cast(pl.Float64) * step).round(precision)
                    for column in prices
                    if column in schema and schema[column].is_integer()
                ]
            )

        frame = lazy.collect()
        if frame.is_empty():
            return cls.empty_frame(timeframe, decode=decode)
        return frame

    @classmethod
    def resample_bars(
        cls,
        frame: pl.DataFrame,
        target_timeframe: str,
        source_timeframe: str = "M1",
    ) -> pl.DataFrame:
        """Resample minute-bar observations to a higher timeframe interval."""
        source_sec = timeframes.timeframe_to_seconds(source_timeframe)
        target_sec = timeframes.timeframe_to_seconds(target_timeframe)

        if source_sec <= 0 or target_sec <= 0:
            raise DomainError(
                code="UNSUPPORTED_RESAMPLING",
                message="Tick data cannot be resampled via bar dynamic grouping",
            )

        if target_sec < source_sec:
            msg = (
                f"Cannot downsample from {source_timeframe} ({source_sec}s) "
                f"to {target_timeframe} ({target_sec}s)"
            )
            raise DomainError(code="UNSUPPORTED_RESAMPLING", message=msg)

        if frame.is_empty() or target_sec == source_sec:
            return frame.clone()

        interval = f"{target_sec}s"
        return (
            frame.group_by_dynamic(
                "DateTime",
                every=interval,
                closed="left",
                label="left",
            )
            .agg(
                [
                    pl.col("Open").first(),
                    pl.col("High").max(),
                    pl.col("Low").min(),
                    pl.col("Close").last(),
                    pl.col("Volume").sum(),
                ]
            )
            .filter(pl.col("Open").is_not_null() & pl.col("Close").is_not_null())
            .sort("DateTime")
        )
