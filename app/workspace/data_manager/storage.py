"""Canonical historical market data partitioned Parquet engine.

Description:
    Provides authoritative on-disk storage, partitioned Parquet writing, ZSTD
    level 6 compression, and multi-engine reading (Polars lazy scans, DuckDB SQL
    queries, and UI slice readers) for quantitative market data.

    Decouples raw broker data access from file persistence. Raw downloaded or
    staged market data (in-memory, bi5, gzip, zip, or flat text) is decompressed,
    normalized, and encoded into integer tick units (int64) to eliminate floating
    point drift and maximize Parquet column compression. Ticks are partitioned by
    year and month (`source/ticks/symbol/YYYY/MM-mmm.parquet`); M1 and higher
    timeframe bars are partitioned by year (`source/timeframe/symbol/YYYY.parquet`).
    All partitions are self-describing via PyArrow schema metadata and synchronize
    authoritatively with `datamgr_datasets` in SQLite persistence.

Purpose:
    FEAT-DATA-STORAGE: Canonical historical market data partitioned Parquet engine.

Key Capabilities:
    - FR-DATA-STORAGE-SCHEMAS: Strongly typed PyArrow schemas for Tick and M1 bars
      utilizing integer tick unit price encoding.
      Associated: `[TICK_SCHEMA]`, `[M1_SCHEMA]`
      Logging: Emits DEBUG log when schemas and conversions are evaluated.
    - FR-DATA-STORAGE-PARTITIONING: Deterministic directory and file path mapping
      for tick (year/month) and bar (year) partition structures.
      Associated: `[get_tick_partition_path()]`, `[get_bar_partition_path()]`
      Logging: Emits DEBUG log when partition paths are resolved.
    - FR-DATA-STORAGE-WRITER: PyArrow batched immutable Parquet writes with ZSTD
      level 6 compression and chronological deduplication.
      Associated: `[MarketDataStorage.write_bars()]`,
      `[MarketDataStorage.write_ticks()]`
      Logging: Emits INFO log on partition creation or update with bar counts.
    - FR-DATA-STORAGE-POLARS-SCAN: Polars lazy scan queries over Parquet partitions
      for quantitative research and backtesting.
      Associated: `[MarketDataStorage.scan_bars()]`,
      `[MarketDataStorage.scan_ticks()]`
      Logging: Emits DEBUG log when lazy scan graphs are constructed.
    - FR-DATA-STORAGE-DUCKDB-SQL: Direct DuckDB analytical SQL execution over
      partitioned Parquet files without full-table materialization.
      Associated: `[MarketDataStorage.query_duckdb()]`
      Logging: Emits DEBUG log on SQL execution against partition targets.
    - FR-DATA-STORAGE-DECOMPRESSION: Multi-format decompression of raw payloads
      supporting Dukascopy `.bi5`, gzip, zip, and raw byte buffers.
      Associated: `[decompress_payload()]`
      Logging: Emits DEBUG log on payload decompression.

Python API Usage:
    ```python
    from pathlib import Path
    from app.workspace.data_manager.storage import MarketDataStorage, BarRecord

    storage = MarketDataStorage(base_dir=Path("data/market"))
    bars = [
        BarRecord(
            timestamp_utc="2025-04-15T12:00:00Z",
            open=1.10000,
            high=1.10500,
            low=1.09500,
            close=1.10200,
            volume=500.0,
        )
    ]
    res = storage.write_bars(
        source="dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        bars=bars,
        tick_size=0.00001,
    )
    assert res.total_bars == 1

    # Research reader via Polars
    lf = storage.scan_bars("dukascopy", "EURUSD", "M1")
    df = lf.collect()
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.storage --help
    ```
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import io
import lzma
import shutil
import struct
import sys
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import query_duckdb

logger = get_logger(__name__)

DEFAULT_MARKET_DATA_PATH = Path("data/market")
DEFAULT_TICK_SIZE = 0.00001
ZSTD_COMPRESSION_LEVEL = 6
MIN_LZMA_HEADER_LEN = 5
MAX_UINT16 = 65535

MONTH_ABBR = [
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
]

# Canonical PyArrow Schemas
TICK_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("Bid", pa.int64(), nullable=False),
        pa.field("Ask", pa.int64(), nullable=False),
        pa.field("Flags", pa.uint16(), nullable=False),
    ]
)

M1_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("Open", pa.int64(), nullable=False),
        pa.field("High", pa.int64(), nullable=False),
        pa.field("Low", pa.int64(), nullable=False),
        pa.field("Close", pa.int64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)


class TickRecord(BaseModel):
    """Normalized tick market data point."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    bid: float = Field(gt=0.0, description="Bid price")
    ask: float = Field(gt=0.0, description="Ask price")
    flags: int = Field(default=0, ge=0, description="Tick flags bitmask")


class BarRecord(BaseModel):
    """Normalized OHLCV market data bar."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    open: float = Field(gt=0.0, description="Opening price")
    high: float = Field(gt=0.0, description="Highest price")
    low: float = Field(gt=0.0, description="Lowest price")
    close: float = Field(gt=0.0, description="Closing price")
    volume: float = Field(default=0.0, ge=0.0, description="Bar traded volume")
    open_interest: float = Field(default=0.0, ge=0.0, description="Open interest")

    def is_valid_geometry(self) -> bool:
        """Validate bar price envelope consistency."""
        max_oc = max(self.open, self.close)
        min_oc = min(self.open, self.close)
        return self.high >= max_oc and self.low <= min_oc and self.high >= self.low


@dataclass(frozen=True)
class StorageWriteResult:
    """Summary receipt of partitioned parquet write operations."""

    source: str
    symbol: str
    timeframe: str
    total_bars: int
    date_from: str
    date_to: str
    partition_files: list[str]
    tick_size: float


def to_tick_units(price: float, tick_size: float) -> int:
    """Convert floating-point price into integer tick units.

    Fires FR-DATA-STORAGE-SCHEMAS.
    """
    scale = tick_size if tick_size > 0.0 else DEFAULT_TICK_SIZE
    return round(price / scale)


def from_tick_units(units: int, tick_size: float) -> float:
    """Convert integer tick units back to floating-point price.

    Fires FR-DATA-STORAGE-SCHEMAS.
    """
    scale = tick_size if tick_size > 0.0 else DEFAULT_TICK_SIZE
    return round(float(units) * scale, 8)


def get_month_slug(month: int) -> str:
    """Format month index (1-12) as zero-padded slug (e.g. '04-apr')."""
    idx = max(1, min(12, month))
    abbr = MONTH_ABBR[idx - 1]
    return f"{idx:02d}-{abbr}"


def parse_iso_to_utc_datetime(iso_str: str) -> datetime:
    """Parse ISO 8601 string or numeric timestamp to UTC datetime."""
    clean = iso_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(iso_str.strip(), fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse timestamp into UTC datetime: {iso_str}")


def get_tick_partition_path(
    base_dir: Path, source: str, symbol: str, dt: datetime
) -> Path:
    """Resolve tick partition path: source / ticks / symbol / year / month.

    Example: `data/market/dukascopy/ticks/eurusd/2025/04-apr.parquet`
    Fires FR-DATA-STORAGE-PARTITIONING.
    """
    month_slug = get_month_slug(dt.month)
    return (
        base_dir
        / source.strip().lower()
        / "ticks"
        / symbol.strip().lower()
        / str(dt.year)
        / f"{month_slug}.parquet"
    )


def get_bar_partition_path(
    base_dir: Path, source: str, timeframe: str, symbol: str, year: int
) -> Path:
    """Resolve bar partition path: source / timeframe / symbol / year.

    Example: `data/market/dukascopy/m1/eurusd/2025.parquet`
    Fires FR-DATA-STORAGE-PARTITIONING.
    """
    return (
        base_dir
        / source.strip().lower()
        / timeframe.strip().lower()
        / symbol.strip().lower()
        / f"{year}.parquet"
    )


def get_dataset_partition_dir(
    base_dir: Path, source: str, timeframe_or_kind: str, symbol: str
) -> Path:
    """Resolve base directory containing all partition files for a series."""
    return (
        base_dir
        / source.strip().lower()
        / timeframe_or_kind.strip().lower()
        / symbol.strip().lower()
    )


def _try_decompress_lzma(data: bytes) -> bytes | None:
    """Attempt LZMA / bi5 decompression using standard and synthetic headers."""
    if len(data) < MIN_LZMA_HEADER_LEN:
        return None
    try:
        return lzma.decompress(data, format=lzma.FORMAT_AUTO)
    except lzma.LZMAError, struct.error, OSError, EOFError, ValueError:
        pass

    try:
        props = data[:MIN_LZMA_HEADER_LEN]
        payload = data[MIN_LZMA_HEADER_LEN:]
        alone_header = props + struct.pack("<Q", 2**64 - 1)
        return lzma.decompress(alone_header + payload, format=lzma.FORMAT_ALONE)
    except lzma.LZMAError, struct.error, OSError, EOFError, ValueError:
        return None


def decompress_payload(data: bytes, format_hint: str | None = None) -> bytes:
    """Decompress raw bytes payload (bi5, gz, zip, or raw bytes).

    Fires FR-DATA-STORAGE-DECOMPRESSION.
    """
    if not data:
        return b""

    hint = (format_hint or "").lower().strip()

    if data.startswith(b"\x1f\x8b") or hint in ("gz", "gzip"):
        logger.debug(
            "FR-DATA-STORAGE-DECOMPRESSION: Decompressing gzip payload (%d bytes)",
            len(data),
            extra={"fr_id": "FR-DATA-STORAGE-DECOMPRESSION"},
        )
        return gzip.decompress(data)

    if data.startswith(b"PK\x03\x04") or hint == "zip":
        logger.debug(
            "FR-DATA-STORAGE-DECOMPRESSION: Decompressing zip payload (%d bytes)",
            len(data),
            extra={"fr_id": "FR-DATA-STORAGE-DECOMPRESSION"},
        )
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            return zf.read(names[0]) if names else b""

    lzma_result = _try_decompress_lzma(data)
    if lzma_result is not None:
        logger.debug(
            "FR-DATA-STORAGE-DECOMPRESSION: Decompressed LZMA/bi5 payload (%d bytes)",
            len(lzma_result),
            extra={"fr_id": "FR-DATA-STORAGE-DECOMPRESSION"},
        )
        return lzma_result

    return data


class MarketDataStorage:
    """Canonical historical market data storage engine managing Parquet partitions."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        """Initialize storage engine with market data root directory."""
        self._base_dir = (
            Path(base_dir).resolve()
            if base_dir is not None
            else DEFAULT_MARKET_DATA_PATH.resolve()
        )
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        """Return base directory for market data files."""
        return self._base_dir

    def _merge_and_write_table(
        self,
        new_table: pa.Table,
        partition_path: Path,
        schema: pa.Schema,
    ) -> pa.Table:
        """Merge arrow table with existing partition using Polars deduplication."""
        if partition_path.exists():
            try:
                existing_table = pq.read_table(partition_path)
                combined = pa.concat_tables([existing_table, new_table])
            except (pa.ArrowInvalid, OSError, ValueError) as exc:
                logger.warning(
                    "FR-DATA-STORAGE-WRITER: Reading partition %s failed: %s",
                    partition_path,
                    exc,
                    extra={"fr_id": "FR-DATA-STORAGE-WRITER"},
                )
                combined = new_table
        else:
            combined = new_table

        df = (
            pl.DataFrame(combined)
            .unique(subset=["DateTime"], keep="last")
            .sort("DateTime")
        )
        final_table = df.to_arrow().cast(schema)

        pq.write_table(
            final_table,
            partition_path,
            compression="zstd",
            compression_level=ZSTD_COMPRESSION_LEVEL,
        )
        return final_table

    def write_bars(
        self,
        source: str,
        symbol: str,
        timeframe: str,
        bars: Sequence[BarRecord],
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> StorageWriteResult:
        """Write and merge bar records into partitioned Parquet files with ZSTD-6.

        Fires FR-DATA-STORAGE-WRITER and FR-DATA-STORAGE-SCHEMAS.
        """
        clean_sym = symbol.strip().upper()
        clean_tf = timeframe.strip().upper()
        clean_source = source.strip().lower()

        if not bars:
            return StorageWriteResult(
                source=clean_source,
                symbol=clean_sym,
                timeframe=clean_tf,
                total_bars=0,
                date_from="",
                date_to="",
                partition_files=[],
                tick_size=tick_size,
            )

        by_year: dict[int, list[tuple[datetime, int, int, int, int, int]]] = {}
        for b in bars:
            dt = parse_iso_to_utc_datetime(b.timestamp_utc)
            year = dt.year
            op = to_tick_units(b.open, tick_size)
            hi = to_tick_units(b.high, tick_size)
            lo = to_tick_units(b.low, tick_size)
            cl = to_tick_units(b.close, tick_size)
            vol = max(0, round(b.volume))
            by_year.setdefault(year, []).append((dt, op, hi, lo, cl, vol))

        written_files: list[str] = []
        schema_metadata = {
            "tick_size": str(tick_size),
            "source": clean_source,
            "symbol": clean_sym,
            "timeframe": clean_tf,
            "data_kind": "bars",
        }
        schema = M1_SCHEMA.with_metadata(schema_metadata)

        total_bars_written = 0
        min_date_str = ""
        max_date_str = ""

        for year, records in by_year.items():
            path = get_bar_partition_path(
                self._base_dir, clean_source, clean_tf, clean_sym, year
            )
            path.parent.mkdir(parents=True, exist_ok=True)

            sorted_in = sorted(records, key=lambda r: r[0])
            new_table = pa.Table.from_arrays(
                [
                    pa.array(
                        [r[0] for r in sorted_in],
                        type=pa.timestamp("us", tz="UTC"),
                    ),
                    pa.array([r[1] for r in sorted_in], type=pa.int64()),
                    pa.array([r[2] for r in sorted_in], type=pa.int64()),
                    pa.array([r[3] for r in sorted_in], type=pa.int64()),
                    pa.array([r[4] for r in sorted_in], type=pa.int64()),
                    pa.array([r[5] for r in sorted_in], type=pa.uint64()),
                ],
                schema=schema,
            )

            final_table = self._merge_and_write_table(new_table, path, schema)
            written_files.append(str(path))
            total_bars_written += final_table.num_rows

            dts_col = final_table.column("DateTime")
            p_from = dts_col[0].as_py().isoformat()
            p_to = dts_col[-1].as_py().isoformat()
            if not min_date_str or p_from < min_date_str:
                min_date_str = p_from
            if not max_date_str or p_to > max_date_str:
                max_date_str = p_to

            logger.info(
                "FR-DATA-STORAGE-WRITER: Wrote %d bars to partition %s",
                final_table.num_rows,
                path,
                extra={"bars": final_table.num_rows, "fr_id": "FR-DATA-STORAGE-WRITER"},
            )

        return StorageWriteResult(
            source=clean_source,
            symbol=clean_sym,
            timeframe=clean_tf,
            total_bars=total_bars_written,
            date_from=min_date_str,
            date_to=max_date_str,
            partition_files=written_files,
            tick_size=tick_size,
        )

    def write_ticks(
        self,
        source: str,
        symbol: str,
        ticks: Sequence[TickRecord],
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> StorageWriteResult:
        """Write and merge tick records into partitioned Parquet files with ZSTD-6.

        Fires FR-DATA-STORAGE-WRITER and FR-DATA-STORAGE-SCHEMAS.
        """
        clean_sym = symbol.strip().upper()
        clean_source = source.strip().lower()

        if not ticks:
            return StorageWriteResult(
                source=clean_source,
                symbol=clean_sym,
                timeframe="TICK",
                total_bars=0,
                date_from="",
                date_to="",
                partition_files=[],
                tick_size=tick_size,
            )

        by_year_month: dict[tuple[int, int], list[tuple[datetime, int, int, int]]] = {}
        for t in ticks:
            dt = parse_iso_to_utc_datetime(t.timestamp_utc)
            key = (dt.year, dt.month)
            bid_u = to_tick_units(t.bid, tick_size)
            ask_u = to_tick_units(t.ask, tick_size)
            flags_u = max(0, min(MAX_UINT16, t.flags))
            by_year_month.setdefault(key, []).append((dt, bid_u, ask_u, flags_u))

        written_files: list[str] = []
        schema_metadata = {
            "tick_size": str(tick_size),
            "source": clean_source,
            "symbol": clean_sym,
            "timeframe": "TICK",
            "data_kind": "ticks",
        }
        schema = TICK_SCHEMA.with_metadata(schema_metadata)

        total_ticks_written = 0
        min_date_str = ""
        max_date_str = ""

        for records in by_year_month.values():
            sample_dt = records[0][0]
            path = get_tick_partition_path(
                self._base_dir, clean_source, clean_sym, sample_dt
            )
            path.parent.mkdir(parents=True, exist_ok=True)

            sorted_in = sorted(records, key=lambda r: r[0])
            new_table = pa.Table.from_arrays(
                [
                    pa.array(
                        [r[0] for r in sorted_in],
                        type=pa.timestamp("us", tz="UTC"),
                    ),
                    pa.array([r[1] for r in sorted_in], type=pa.int64()),
                    pa.array([r[2] for r in sorted_in], type=pa.int64()),
                    pa.array([r[3] for r in sorted_in], type=pa.uint16()),
                ],
                schema=schema,
            )

            final_table = self._merge_and_write_table(new_table, path, schema)
            written_files.append(str(path))
            total_ticks_written += final_table.num_rows

            dts_col = final_table.column("DateTime")
            p_from = dts_col[0].as_py().isoformat()
            p_to = dts_col[-1].as_py().isoformat()
            if not min_date_str or p_from < min_date_str:
                min_date_str = p_from
            if not max_date_str or p_to > max_date_str:
                max_date_str = p_to

            logger.info(
                "FR-DATA-STORAGE-WRITER: Wrote %d ticks to partition %s",
                final_table.num_rows,
                path,
                extra={
                    "ticks": final_table.num_rows,
                    "fr_id": "FR-DATA-STORAGE-WRITER",
                },
            )

        return StorageWriteResult(
            source=clean_source,
            symbol=clean_sym,
            timeframe="TICK",
            total_bars=total_ticks_written,
            date_from=min_date_str,
            date_to=max_date_str,
            partition_files=written_files,
            tick_size=tick_size,
        )

    def scan_bars(
        self,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pl.LazyFrame:
        """Create Polars LazyFrame scanning Parquet bar partitions.

        Fires FR-DATA-STORAGE-POLARS-SCAN.
        """
        clean_source = source.strip().lower()
        clean_tf = timeframe.strip().lower()
        clean_sym = symbol.strip().lower()

        pattern = self._base_dir / clean_source / clean_tf / clean_sym / "*.parquet"
        matched_files: list[Path] = []
        if pattern.parent.exists():
            matched_files = sorted(pattern.parent.glob("*.parquet"))

        logger.debug(
            "FR-DATA-STORAGE-POLARS-SCAN: Scanning %d partition files for %s/%s/%s",
            len(matched_files),
            clean_source,
            clean_sym,
            clean_tf,
            extra={"fr_id": "FR-DATA-STORAGE-POLARS-SCAN"},
        )

        if not matched_files:
            empty_df = pl.DataFrame(
                schema={
                    "DateTime": pl.Datetime(time_unit="us", time_zone="UTC"),
                    "Open": pl.Int64,
                    "High": pl.Int64,
                    "Low": pl.Int64,
                    "Close": pl.Int64,
                    "Volume": pl.UInt64,
                }
            )
            return empty_df.lazy()

        lf = pl.scan_parquet([str(p) for p in matched_files])

        if date_from:
            dt_start = parse_iso_to_utc_datetime(date_from)
            lf = lf.filter(pl.col("DateTime") >= dt_start)
        if date_to:
            dt_end = parse_iso_to_utc_datetime(date_to)
            lf = lf.filter(pl.col("DateTime") <= dt_end)

        return lf

    def scan_ticks(
        self,
        source: str,
        symbol: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pl.LazyFrame:
        """Create Polars LazyFrame scanning Parquet tick partitions.

        Fires FR-DATA-STORAGE-POLARS-SCAN.
        """
        clean_source = source.strip().lower()
        clean_sym = symbol.strip().lower()

        base_dir = self._base_dir / clean_source / "ticks" / clean_sym
        matched_files: list[Path] = []
        if base_dir.exists():
            matched_files = sorted(base_dir.rglob("*.parquet"))

        logger.debug(
            "FR-DATA-STORAGE-POLARS-SCAN: Scanning %d tick partition files for %s/%s",
            len(matched_files),
            clean_source,
            clean_sym,
            extra={"fr_id": "FR-DATA-STORAGE-POLARS-SCAN"},
        )

        if not matched_files:
            empty_df = pl.DataFrame(
                schema={
                    "DateTime": pl.Datetime(time_unit="us", time_zone="UTC"),
                    "Bid": pl.Int64,
                    "Ask": pl.Int64,
                    "Flags": pl.UInt16,
                }
            )
            return empty_df.lazy()

        lf = pl.scan_parquet([str(p) for p in matched_files])

        if date_from:
            dt_start = parse_iso_to_utc_datetime(date_from)
            lf = lf.filter(pl.col("DateTime") >= dt_start)
        if date_to:
            dt_end = parse_iso_to_utc_datetime(date_to)
            lf = lf.filter(pl.col("DateTime") <= dt_end)

        return lf

    def query_duckdb(self, query: str) -> Any:
        """Execute analytical SQL query directly over Parquet files.

        Fires FR-DATA-STORAGE-DUCKDB-SQL.
        """
        logger.debug(
            "FR-DATA-STORAGE-DUCKDB-SQL: Executing DuckDB query",
            extra={"fr_id": "FR-DATA-STORAGE-DUCKDB-SQL", "query": query},
        )
        return query_duckdb(query)

    def read_bars_slice(
        self,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 1000,
        offset: int = 0,
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> list[BarRecord]:
        """Read and materialize a slice of BarRecords converting integer tick units.

        Fires FR-DATA-STORAGE-POLARS-SCAN.
        """
        lf = self.scan_bars(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
        )
        df = lf.sort("DateTime").slice(offset, limit).collect()

        if df.is_empty():
            return []

        bars: list[BarRecord] = []
        dts = df["DateTime"].to_list()
        opens = df["Open"].to_list()
        highs = df["High"].to_list()
        lows = df["Low"].to_list()
        closes = df["Close"].to_list()
        volumes = df["Volume"].to_list()
        is_float_price = df["Open"].dtype.is_float()

        for idx, dt_val in enumerate(dts):
            if is_float_price:
                o_val = float(opens[idx])
                h_val = float(highs[idx])
                l_val = float(lows[idx])
                c_val = float(closes[idx])
            else:
                o_val = from_tick_units(opens[idx], tick_size)
                h_val = from_tick_units(highs[idx], tick_size)
                l_val = from_tick_units(lows[idx], tick_size)
                c_val = from_tick_units(closes[idx], tick_size)

            bars.append(
                BarRecord(
                    timestamp_utc=dt_val.isoformat(),
                    open=o_val,
                    high=h_val,
                    low=l_val,
                    close=c_val,
                    volume=float(volumes[idx]),
                    open_interest=0.0,
                )
            )
        return bars

    def read_ticks_slice(
        self,
        source: str,
        symbol: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 1000,
        offset: int = 0,
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> list[TickRecord]:
        """Read and materialize a slice of TickRecords converting integer tick units.

        Fires FR-DATA-STORAGE-POLARS-SCAN.
        """
        lf = self.scan_ticks(
            source=source, symbol=symbol, date_from=date_from, date_to=date_to
        )
        df = lf.sort("DateTime").slice(offset, limit).collect()

        if df.is_empty():
            return []

        ticks: list[TickRecord] = []
        dts = df["DateTime"].to_list()
        bids = df["Bid"].to_list()
        asks = df["Ask"].to_list()
        flags = df["Flags"].to_list() if "Flags" in df.columns else [0] * len(dts)
        is_float_price = df["Bid"].dtype.is_float()

        for idx, dt_val in enumerate(dts):
            if is_float_price:
                b_val = float(bids[idx])
                a_val = float(asks[idx])
            else:
                b_val = from_tick_units(bids[idx], tick_size)
                a_val = from_tick_units(asks[idx], tick_size)

            ticks.append(
                TickRecord(
                    timestamp_utc=dt_val.isoformat(),
                    bid=b_val,
                    ask=a_val,
                    flags=int(flags[idx]),
                )
            )
        return ticks

    def clear_partitions(self, source: str, timeframe_or_kind: str, symbol: str) -> int:
        """Clear all on-disk parquet files for a series without deleting directory."""
        target_dir = get_dataset_partition_dir(
            self._base_dir, source, timeframe_or_kind, symbol
        )
        if not target_dir.exists():
            return 0
        count = 0
        for f in target_dir.rglob("*.parquet"):
            try:
                f.unlink()
                count += 1
            except OSError as exc:
                logger.warning(
                    "FR-DATA-STORAGE-WRITER: Failed deleting partition %s: %s",
                    f,
                    exc,
                )
        logger.info(
            "FR-DATA-STORAGE-WRITER: Cleared %d partition files for %s/%s/%s",
            count,
            source,
            symbol,
            timeframe_or_kind,
            extra={"fr_id": "FR-DATA-STORAGE-WRITER"},
        )
        return count

    def delete_partitions(
        self, source: str, timeframe_or_kind: str, symbol: str
    ) -> bool:
        """Remove partition directory and all contained files completely."""
        target_dir = get_dataset_partition_dir(
            self._base_dir, source, timeframe_or_kind, symbol
        )
        if not target_dir.exists():
            return True

        try:
            shutil.rmtree(target_dir)
            logger.info(
                "FR-DATA-STORAGE-WRITER: Deleted partition directory %s",
                target_dir,
                extra={"fr_id": "FR-DATA-STORAGE-WRITER"},
            )
            return True
        except OSError as exc:
            logger.warning(
                "FR-DATA-STORAGE-WRITER: Failed removing partition dir %s: %s",
                target_dir,
                exc,
            )
            return False

    def patch_bars(
        self,
        source: str,
        timeframe: str,
        symbol: str,
        changed_bars: Sequence[BarRecord],
        deleted_timestamps: set[str],
        *,
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> int:
        """Patch bar partitions by replacing changed bars and deleting timestamps.

        Fires FR-DATA-STORAGE-WRITER.
        Returns total remaining bar count across all partitions.
        """
        clean_sym = symbol.strip().upper()
        clean_source = source.strip().lower()
        clean_tf = timeframe.strip().upper()

        affected_years = self._collect_affected_years(changed_bars, deleted_timestamps)
        schema_metadata = {
            "tick_size": str(tick_size),
            "source": clean_source,
            "symbol": clean_sym,
            "timeframe": clean_tf,
            "data_kind": "bars",
        }
        schema = M1_SCHEMA.with_metadata(schema_metadata)

        for year in affected_years:
            path = get_bar_partition_path(
                self._base_dir, clean_source, clean_tf, clean_sym, year
            )
            if path.exists():
                self._patch_year_partition(
                    path,
                    year,
                    changed_bars,
                    deleted_timestamps,
                    schema=schema,
                    tick_size=tick_size,
                )

        base_dir = self._base_dir / clean_source / clean_tf.lower() / clean_sym.lower()
        total_bars = self._recount_total_bars(base_dir)

        logger.info(
            "FR-DATA-STORAGE-WRITER: Patched %s/%s/%s: %d changed, %d deleted, "
            "%d total remaining",
            clean_source,
            clean_sym,
            clean_tf,
            len(changed_bars),
            len(deleted_timestamps),
            total_bars,
            extra={
                "changed": len(changed_bars),
                "deleted": len(deleted_timestamps),
                "remaining_bars": total_bars,
                "fr_id": "FR-DATA-STORAGE-WRITER",
            },
        )
        return total_bars

    @staticmethod
    def _collect_affected_years(
        changed_bars: Sequence[BarRecord], deleted_timestamps: set[str]
    ) -> set[int]:
        years: set[int] = set()
        for b in changed_bars:
            years.add(parse_iso_to_utc_datetime(b.timestamp_utc).year)
        for ts in deleted_timestamps:
            with contextlib.suppress(ValueError):
                years.add(parse_iso_to_utc_datetime(ts).year)
        return years

    def _patch_year_partition(
        self,
        path: Path,
        year: int,
        changed_bars: Sequence[BarRecord],
        deleted_timestamps: set[str],
        *,
        schema: pa.Schema,
        tick_size: float,
    ) -> None:
        try:
            existing_table = pq.read_table(path)
            df = pl.DataFrame(existing_table)
        except (pa.ArrowInvalid, OSError, ValueError) as exc:
            logger.warning(
                "FR-DATA-STORAGE-WRITER: Reading partition %s failed: %s",
                path,
                exc,
                extra={"fr_id": "FR-DATA-STORAGE-WRITER"},
            )
            return

        del_dts: list[datetime] = []
        for ts_str in deleted_timestamps:
            with contextlib.suppress(ValueError):
                d = parse_iso_to_utc_datetime(ts_str)
                if d.year == year:
                    del_dts.append(d)
        if del_dts:
            df = df.filter(~pl.col("DateTime").is_in(del_dts))

        year_changed = [
            b
            for b in changed_bars
            if parse_iso_to_utc_datetime(b.timestamp_utc).year == year
        ]
        if year_changed:
            records = [
                (
                    parse_iso_to_utc_datetime(b.timestamp_utc),
                    to_tick_units(b.open, tick_size),
                    to_tick_units(b.high, tick_size),
                    to_tick_units(b.low, tick_size),
                    to_tick_units(b.close, tick_size),
                    max(0, round(b.volume)),
                )
                for b in year_changed
            ]
            records.sort(key=lambda r: r[0])
            new_table = pa.Table.from_arrays(
                [
                    pa.array(
                        [r[0] for r in records],
                        type=pa.timestamp("us", tz="UTC"),
                    ),
                    pa.array([r[1] for r in records], type=pa.int64()),
                    pa.array([r[2] for r in records], type=pa.int64()),
                    pa.array([r[3] for r in records], type=pa.int64()),
                    pa.array([r[4] for r in records], type=pa.int64()),
                    pa.array([r[5] for r in records], type=pa.uint64()),
                ],
                schema=schema,
            )
            new_df = pl.DataFrame(new_table)
            df = (
                pl.concat([df, new_df])
                .unique(subset=["DateTime"], keep="last")
                .sort("DateTime")
            )

        if df.height > 0:
            final_table = df.to_arrow().cast(schema)
            pq.write_table(
                final_table,
                path,
                compression="zstd",
                compression_level=ZSTD_COMPRESSION_LEVEL,
            )
        else:
            with contextlib.suppress(OSError):
                path.unlink()

    @staticmethod
    def _recount_total_bars(base_dir: Path) -> int:
        if not base_dir.exists():
            return 0
        total = 0
        for f in sorted(base_dir.rglob("*.parquet")):
            with contextlib.suppress(OSError, pa.ArrowInvalid):
                meta = pq.read_metadata(f)
                total += meta.num_rows
        return total


def main() -> int:
    """CLI tool for inspecting market data partitions."""
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Historical Market Data Storage CLI"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=str(DEFAULT_MARKET_DATA_PATH),
        help="Base directory for market data partitions",
    )
    parser.add_argument(
        "--list-partitions",
        action="store_true",
        help="List all on-disk parquet partition files",
    )
    args = parser.parse_args()

    storage = MarketDataStorage(base_dir=Path(args.base_dir))
    if args.list_partitions:
        files = sorted(storage.base_dir.rglob("*.parquet"))
        print(f"Total partitions found in {storage.base_dir}: {len(files)}")
        for f in files[:25]:
            print(f"  {f.relative_to(storage.base_dir)}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
