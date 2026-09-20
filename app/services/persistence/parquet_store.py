"""Partitioned columnar market data time-series store with Zstandard compression.

Feature:
    FEAT-PERSISTENCE-PARQUET

Purpose:
    Provides partitioned columnar storage for historical OHLCV bars and tick sequences
    using Apache Arrow and Parquet with Zstandard compression (DEC-PERSISTENCE-001).
    Partitions are organized by symbol, timeframe, and calendar year:
    `<market_dir>/<symbol>/<timeframe>/<year>.parquet`.

Invariants:
    * All timestamps are normalized to timezone-aware UTC datetime.
    * Writes are atomic via transient files and atomic filesystem replacement.
    * Existing partitions are merged and deduplicated on timestamp ascending.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import override

import pyarrow as pa
import pyarrow.parquet as pq

from app.contracts.persistence import (
    PARQUET_STORE_SERVICE,
    BarRecord,
    MarketSeriesPartition,
    ParquetStorageError,
    TickRecord,
)
from app.contracts.persistence import (
    ParquetStoreService as IParquetStoreService,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

logger = get_logger(__name__)

BARS_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("timestamp_utc", pa.timestamp("us")),
        pa.field("open", pa.float64()),
        pa.field("high", pa.float64()),
        pa.field("low", pa.float64()),
        pa.field("close", pa.float64()),
        pa.field("volume", pa.float64()),
        pa.field("ticks", pa.int64()),
    ]
)

TICKS_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("timestamp_utc", pa.timestamp("us")),
        pa.field("bid", pa.float64()),
        pa.field("ask", pa.float64()),
        pa.field("bid_volume", pa.float64()),
        pa.field("ask_volume", pa.float64()),
    ]
)


def _to_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert datetime to naive UTC timestamp for Parquet storage."""
    return _to_utc(dt).replace(tzinfo=None)


def _atomic_write_table(table: pa.Table, target_file: Path) -> None:
    """Write PyArrow table atomically using temporary file and replacement."""
    target_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target_file.with_name(
        f"{target_file.stem}.tmp_{uuid.uuid4().hex[:8]}.parquet"
    )
    try:
        pq.write_table(table, temp_file, compression="zstd", compression_level=3)
        temp_file.replace(target_file)
    finally:
        temp_file.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class ParquetConfig:
    """Configuration for Parquet columnar store.

    Attributes:
        market_dir: Base directory for partitioned Parquet storage.
    """

    market_dir: Path = Path("data/market")


class ParquetStoreServiceImpl(IParquetStoreService):
    """Concrete implementation of ParquetStoreService."""

    def __init__(self, config: ParquetConfig | None = None) -> None:
        """Initialize Parquet store service with configuration.

        Args:
            config: Optional Parquet storage configuration.
        """
        self._config = config or ParquetConfig()
        self._config.market_dir.mkdir(parents=True, exist_ok=True)

    def _get_partition_path(self, symbol: str, timeframe: str, year: int) -> Path:
        """Construct canonical partition path."""
        return self._config.market_dir / symbol.upper() / timeframe / f"{year}.parquet"

    def _read_bars_file(self, file_path: Path) -> list[BarRecord]:
        """Read and parse BarRecord objects from a single Parquet file."""
        if not file_path.is_file():
            return []

        try:
            table = pq.read_table(file_path)
            timestamps = table.column("timestamp_utc").to_pylist()
            opens = table.column("open").to_pylist()
            highs = table.column("high").to_pylist()
            lows = table.column("low").to_pylist()
            closes = table.column("close").to_pylist()
            volumes = table.column("volume").to_pylist()
            ticks_col = table.column("ticks").to_pylist()

            bars: list[BarRecord] = []
            for i in range(len(timestamps)):
                ts = _to_utc(timestamps[i])
                bars.append(
                    BarRecord(
                        timestamp_utc=ts,
                        open=float(opens[i]),
                        high=float(highs[i]),
                        low=float(lows[i]),
                        close=float(closes[i]),
                        volume=float(volumes[i]),
                        ticks=int(ticks_col[i]),
                    )
                )
            return bars
        except Exception as exc:
            msg = f"Failed to read Parquet bars from {file_path}: {exc}"
            logger.exception("parquet_bars_read_failed", path=str(file_path))
            raise ParquetStorageError(msg) from exc

    def _read_ticks_file(self, file_path: Path) -> list[TickRecord]:
        """Read and parse TickRecord objects from a single Parquet file."""
        if not file_path.is_file():
            return []

        try:
            table = pq.read_table(file_path)
            timestamps = table.column("timestamp_utc").to_pylist()
            bids = table.column("bid").to_pylist()
            asks = table.column("ask").to_pylist()
            bid_vols = table.column("bid_volume").to_pylist()
            ask_vols = table.column("ask_volume").to_pylist()

            ticks: list[TickRecord] = []
            for i in range(len(timestamps)):
                ts = _to_utc(timestamps[i])
                ticks.append(
                    TickRecord(
                        timestamp_utc=ts,
                        bid=float(bids[i]),
                        ask=float(asks[i]),
                        bid_volume=float(bid_vols[i]),
                        ask_volume=float(ask_vols[i]),
                    )
                )
            return ticks
        except Exception as exc:
            msg = f"Failed to read Parquet ticks from {file_path}: {exc}"
            logger.exception("parquet_ticks_read_failed", path=str(file_path))
            raise ParquetStorageError(msg) from exc

    @override
    def write_bars(self, symbol: str, timeframe: str, bars: Sequence[BarRecord]) -> int:
        """Write bars into partitioned columnar Parquet files.

        Args:
            symbol: Ticker symbol (e.g. 'EURUSD').
            timeframe: Bar timeframe (e.g. 'M1', 'H1').
            bars: Sequence of BarRecord objects.

        Returns:
            Number of bars written.

        Raises:
            ParquetStorageError: If Parquet writing fails.
        """
        if not bars:
            return 0

        # Partition by calendar year
        by_year: dict[int, list[BarRecord]] = defaultdict(list)
        for b in bars:
            ts_utc = _to_utc(b.timestamp_utc)
            by_year[ts_utc.year].append(
                BarRecord(
                    timestamp_utc=ts_utc,
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=b.volume,
                    ticks=b.ticks,
                )
            )

        total_written = 0
        for year, year_bars in by_year.items():
            target_path = self._get_partition_path(symbol, timeframe, year)
            merged: dict[datetime, BarRecord] = {}

            if target_path.is_file():
                for existing_bar in self._read_bars_file(target_path):
                    merged[existing_bar.timestamp_utc] = existing_bar

            for new_bar in year_bars:
                merged[new_bar.timestamp_utc] = new_bar

            sorted_bars = sorted(merged.values(), key=lambda b: b.timestamp_utc)
            table = pa.Table.from_pydict(
                {
                    "timestamp_utc": [
                        _to_naive_utc(b.timestamp_utc) for b in sorted_bars
                    ],
                    "open": [b.open for b in sorted_bars],
                    "high": [b.high for b in sorted_bars],
                    "low": [b.low for b in sorted_bars],
                    "close": [b.close for b in sorted_bars],
                    "volume": [b.volume for b in sorted_bars],
                    "ticks": [b.ticks for b in sorted_bars],
                },
                schema=BARS_SCHEMA,
            )

            try:
                _atomic_write_table(table, target_path)
                total_written += len(year_bars)
            except Exception as exc:
                msg = f"Failed to write Parquet bars to {target_path}: {exc}"
                logger.exception("parquet_bars_write_failed", path=str(target_path))
                raise ParquetStorageError(msg) from exc

        logger.info(
            "parquet_bars_written",
            symbol=symbol.upper(),
            timeframe=timeframe,
            count=total_written,
        )
        return total_written

    @override
    def read_bars(
        self,
        symbol: str,
        timeframe: str,
        *,
        start_time_utc: datetime | None = None,
        end_time_utc: datetime | None = None,
        limit: int | None = None,
    ) -> list[BarRecord]:
        """Read bars for a symbol and timeframe within optional time range.

        Args:
            symbol: Ticker symbol.
            timeframe: Bar timeframe.
            start_time_utc: Optional starting UTC timestamp filter.
            end_time_utc: Optional ending UTC timestamp filter.
            limit: Optional maximum number of bars to return.

        Returns:
            List of filtered BarRecord objects sorted ascending by timestamp.
        """
        sym_dir = self._config.market_dir / symbol.upper() / timeframe
        if not sym_dir.is_dir():
            return []

        start_norm = _to_utc(start_time_utc) if start_time_utc else None
        end_norm = _to_utc(end_time_utc) if end_time_utc else None

        partition_files = sorted(sym_dir.glob("*.parquet"))
        collected: list[BarRecord] = []

        for p_file in partition_files:
            if not p_file.stem.isdigit():
                continue
            year = int(p_file.stem)
            if start_norm and year < start_norm.year:
                continue
            if end_norm and year > end_norm.year:
                continue

            for bar in self._read_bars_file(p_file):
                if start_norm and bar.timestamp_utc < start_norm:
                    continue
                if end_norm and bar.timestamp_utc > end_norm:
                    continue
                collected.append(bar)

        collected.sort(key=lambda b: b.timestamp_utc)
        if limit is not None and limit > 0:
            return collected[:limit]
        return collected

    @override
    def write_ticks(self, symbol: str, ticks: Sequence[TickRecord]) -> int:
        """Write ticks into partitioned columnar Parquet files.

        Args:
            symbol: Ticker symbol.
            ticks: Sequence of TickRecord objects.

        Returns:
            Number of ticks written.

        Raises:
            ParquetStorageError: If Parquet writing fails.
        """
        if not ticks:
            return 0

        by_year: dict[int, list[TickRecord]] = defaultdict(list)
        for t in ticks:
            ts_utc = _to_utc(t.timestamp_utc)
            by_year[ts_utc.year].append(
                TickRecord(
                    timestamp_utc=ts_utc,
                    bid=t.bid,
                    ask=t.ask,
                    bid_volume=t.bid_volume,
                    ask_volume=t.ask_volume,
                )
            )

        total_written = 0
        for year, year_ticks in by_year.items():
            target_path = self._get_partition_path(symbol, "tick", year)
            merged: dict[datetime, TickRecord] = {}

            if target_path.is_file():
                for existing_tick in self._read_ticks_file(target_path):
                    merged[existing_tick.timestamp_utc] = existing_tick

            for new_tick in year_ticks:
                merged[new_tick.timestamp_utc] = new_tick

            sorted_ticks = sorted(merged.values(), key=lambda t: t.timestamp_utc)
            table = pa.Table.from_pydict(
                {
                    "timestamp_utc": [
                        _to_naive_utc(t.timestamp_utc) for t in sorted_ticks
                    ],
                    "bid": [t.bid for t in sorted_ticks],
                    "ask": [t.ask for t in sorted_ticks],
                    "bid_volume": [t.bid_volume for t in sorted_ticks],
                    "ask_volume": [t.ask_volume for t in sorted_ticks],
                },
                schema=TICKS_SCHEMA,
            )

            try:
                _atomic_write_table(table, target_path)
                total_written += len(year_ticks)
            except Exception as exc:
                msg = f"Failed to write Parquet ticks to {target_path}: {exc}"
                logger.exception("parquet_ticks_write_failed", path=str(target_path))
                raise ParquetStorageError(msg) from exc

        logger.info(
            "parquet_ticks_written",
            symbol=symbol.upper(),
            count=total_written,
        )
        return total_written

    @override
    def read_ticks(
        self,
        symbol: str,
        *,
        start_time_utc: datetime | None = None,
        end_time_utc: datetime | None = None,
        limit: int | None = None,
    ) -> list[TickRecord]:
        """Read ticks for a symbol within optional time range.

        Args:
            symbol: Ticker symbol.
            start_time_utc: Optional starting UTC timestamp filter.
            end_time_utc: Optional ending UTC timestamp filter.
            limit: Optional maximum number of ticks to return.

        Returns:
            List of filtered TickRecord objects sorted ascending by timestamp.
        """
        sym_dir = self._config.market_dir / symbol.upper() / "tick"
        if not sym_dir.is_dir():
            return []

        start_norm = _to_utc(start_time_utc) if start_time_utc else None
        end_norm = _to_utc(end_time_utc) if end_time_utc else None

        partition_files = sorted(sym_dir.glob("*.parquet"))
        collected: list[TickRecord] = []

        for p_file in partition_files:
            if not p_file.stem.isdigit():
                continue
            year = int(p_file.stem)
            if start_norm and year < start_norm.year:
                continue
            if end_norm and year > end_norm.year:
                continue

            for tick in self._read_ticks_file(p_file):
                if start_norm and tick.timestamp_utc < start_norm:
                    continue
                if end_norm and tick.timestamp_utc > end_norm:
                    continue
                collected.append(tick)

        collected.sort(key=lambda t: t.timestamp_utc)
        if limit is not None and limit > 0:
            return collected[:limit]
        return collected

    @override
    def list_partitions(self) -> list[MarketSeriesPartition]:
        """List all discovered market series partitions.

        Returns:
            List of MarketSeriesPartition metadata descriptors.
        """
        partitions: list[MarketSeriesPartition] = []
        for file_path in self._config.market_dir.glob("*/*/*.parquet"):
            if ".tmp_" in file_path.name or not file_path.stem.isdigit():
                continue

            try:
                symbol = file_path.parent.parent.name
                timeframe = file_path.parent.name
                year = int(file_path.stem)
                size = file_path.stat().st_size

                table = pq.read_table(file_path, columns=["timestamp_utc"])
                num_rows = table.num_rows
                if num_rows == 0:
                    continue

                ts_col = table.column("timestamp_utc")
                min_ts = _to_utc(ts_col[0].as_py())
                max_ts = _to_utc(ts_col[-1].as_py())

                partitions.append(
                    MarketSeriesPartition(
                        symbol=symbol,
                        timeframe=timeframe,
                        year=year,
                        file_path=file_path,
                        record_count=num_rows,
                        size_bytes=size,
                        min_timestamp_utc=min_ts,
                        max_timestamp_utc=max_ts,
                    )
                )
            except (OSError, pa.ArrowException, ValueError) as exc:
                logger.warning(
                    "partition_read_metadata_failed",
                    path=str(file_path),
                    error=str(exc),
                )

        partitions.sort(key=lambda p: (p.symbol, p.timeframe, p.year))
        return partitions

    @override
    def delete_partition(self, symbol: str, timeframe: str, year: int) -> bool:
        """Delete a single year partition for symbol and timeframe.

        Args:
            symbol: Ticker symbol.
            timeframe: Timeframe or 'tick'.
            year: Calendar year partition.

        Returns:
            True if partition was deleted, False if it did not exist.
        """
        target_path = self._get_partition_path(symbol, timeframe, year)
        if target_path.is_file():
            target_path.unlink()
            logger.info(
                "parquet_partition_deleted",
                symbol=symbol.upper(),
                timeframe=timeframe,
                year=year,
            )
            return True
        return False


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.parquet",
    provides=frozenset({PARQUET_STORE_SERVICE}),
    requires=frozenset(),
    optional=frozenset(),
    description=(
        "Partitioned columnar market data time-series store with Zstandard compression."
    ),
)


class ParquetFeature:
    """Wire Parquet market data store into kernel composition lifecycle."""

    def __init__(self, config: ParquetConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional Parquet store configuration.
        """
        self._config = config or ParquetConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Register Parquet store service into runtime context.

        Args:
            context: Kernel feature context.
        """
        service = ParquetStoreServiceImpl(self._config)
        context.provide(PARQUET_STORE_SERVICE, service)
        logger.info(
            "persistence_parquet_feature_started",
            market_dir=str(self._config.market_dir),
        )


def feature() -> ParquetFeature:
    """Return a zero-argument factory instance of ParquetFeature."""
    return ParquetFeature()
