"""Polars Lazy Reader and DuckDB Analytical SQL Engines."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
import polars as pl

if TYPE_CHECKING:
    from app.contracts.data.market_data_store import ScanRangeQuery
    from app.services.data.market_data_store.config import MarketDataStoreConfig


class MarketDataReader:
    """High-speed partitioned Parquet reader with Polars and DuckDB."""

    def __init__(self, config: MarketDataStoreConfig) -> None:
        """Initialize the reader engine.

        Args:
            config: Store configuration parameters.
        """
        self._config = config
        self._root = Path(config.storage_root).resolve()
        self._ticks_root = self._root / "ticks"
        self._bars_root = self._root / "bars"

    def scan_ticks(self, query: ScanRangeQuery) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over the partitioned ticks dataset.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for evaluation or backtesting streaming.
        """
        glob_pattern = str(self._ticks_root / "**" / "*.parquet")

        if not any(self._ticks_root.glob("**/*.parquet")):
            return pl.DataFrame(
                schema={
                    "datetime": pl.Datetime("us", time_zone="UTC"),
                    "sequence": pl.UInt32,
                    "bid_ticks": pl.Int64,
                    "ask_ticks": pl.Int64,
                    "last_ticks": pl.Int64,
                    "volume": pl.UInt64,
                    "flags": pl.UInt16,
                    "source": pl.String,
                    "symbol": pl.String,
                    "year": pl.String,
                    "month": pl.String,
                }
            ).lazy()

        start_dt = (
            query.start if query.start.tzinfo else query.start.replace(tzinfo=UTC)
        )
        end_dt = query.end if query.end.tzinfo else query.end.replace(tzinfo=UTC)

        scan = pl.scan_parquet(
            glob_pattern,
            hive_partitioning=True,
        ).filter(
            (pl.col("source") == query.source)
            & (pl.col("symbol") == query.symbol)
            & (pl.col("datetime") >= start_dt)
            & (pl.col("datetime") < end_dt)
        )

        if query.restore_prices:
            tick_sz = float(query.tick_size)
            scan = scan.with_columns(
                [
                    (pl.col("bid_ticks").cast(pl.Float64) * tick_sz).alias("bid"),
                    (pl.col("ask_ticks").cast(pl.Float64) * tick_sz).alias("ask"),
                    (
                        pl.when(pl.col("last_ticks").is_not_null())
                        .then(pl.col("last_ticks").cast(pl.Float64) * tick_sz)
                        .otherwise(None)
                        .alias("last")
                    ),
                    (
                        (pl.col("ask_ticks") - pl.col("bid_ticks")).cast(pl.Float64)
                        * tick_sz
                    ).alias("spread"),
                ]
            )

        if query.columns:
            scan = scan.select(query.columns)

        return scan.sort("datetime", "sequence")

    def scan_bars(self, query: ScanRangeQuery) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over the partitioned bars dataset.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for evaluation.
        """
        glob_pattern = str(self._bars_root / "**" / "*.parquet")

        if not any(self._bars_root.glob("**/*.parquet")):
            return pl.DataFrame(
                schema={
                    "datetime": pl.Datetime("us", time_zone="UTC"),
                    "open_ticks": pl.Int64,
                    "high_ticks": pl.Int64,
                    "low_ticks": pl.Int64,
                    "close_ticks": pl.Int64,
                    "tick_volume": pl.UInt64,
                    "real_volume": pl.UInt64,
                    "source": pl.String,
                    "timeframe": pl.String,
                    "symbol": pl.String,
                    "year": pl.String,
                }
            ).lazy()

        start_dt = (
            query.start if query.start.tzinfo else query.start.replace(tzinfo=UTC)
        )
        end_dt = query.end if query.end.tzinfo else query.end.replace(tzinfo=UTC)

        scan = pl.scan_parquet(
            glob_pattern,
            hive_partitioning=True,
        ).filter(
            (pl.col("source") == query.source)
            & (pl.col("timeframe") == query.timeframe)
            & (pl.col("symbol") == query.symbol)
            & (pl.col("datetime") >= start_dt)
            & (pl.col("datetime") < end_dt)
        )

        if query.restore_prices:
            tick_sz = float(query.tick_size)
            scan = scan.with_columns(
                [
                    (pl.col("open_ticks").cast(pl.Float64) * tick_sz).alias("open"),
                    (pl.col("high_ticks").cast(pl.Float64) * tick_sz).alias("high"),
                    (pl.col("low_ticks").cast(pl.Float64) * tick_sz).alias("low"),
                    (pl.col("close_ticks").cast(pl.Float64) * tick_sz).alias("close"),
                ]
            )

        if query.columns:
            scan = scan.select(query.columns)

        return scan.sort("datetime")

    def query_sql(self, sql_query: str) -> duckdb.DuckDBPyRelation:
        """Execute analytical SQL query using DuckDB directly over Parquet files.

        Args:
            sql_query: Arbitrary SQL statement querying 'ticks' or 'bars'.

        Returns:
            DuckDBPyRelation with results.
        """
        con = duckdb.connect(":memory:")

        ticks_pattern = str(self._ticks_root / "**" / "*.parquet").replace("\\", "/")
        bars_pattern = str(self._bars_root / "**" / "*.parquet").replace("\\", "/")

        if any(self._ticks_root.glob("**/*.parquet")):
            sql_ticks = (
                f"CREATE VIEW ticks AS SELECT * FROM "  # noqa: S608
                f"read_parquet('{ticks_pattern}', hive_partitioning=true)"
            )
            con.execute(sql_ticks)

        if any(self._bars_root.glob("**/*.parquet")):
            sql_bars = (
                f"CREATE VIEW bars AS SELECT * FROM "  # noqa: S608
                f"read_parquet('{bars_pattern}', hive_partitioning=true)"
            )
            con.execute(sql_bars)

        return con.query(sql_query)
