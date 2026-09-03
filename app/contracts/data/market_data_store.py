"""Contracts and protocols for the Partitioned Parquet Market Data Store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    import duckdb
    import polars as pl
    import pyarrow as pa


@dataclass(frozen=True)
class IngestionReceipt:
    """Receipt returned after atomically committing a market data batch."""

    part_paths: list[str]
    dataset: Literal["ticks", "bars"]
    source: str
    symbol: str
    timeframe: str
    minimum_datetime: datetime
    maximum_datetime: datetime
    row_count: int
    schema_version: int
    checksums: list[str]
    committed_at: datetime


class CatalogPartRecord(BaseModel):
    """Manifest record metadata for an immutable Parquet part file."""

    model_config = ConfigDict(frozen=True)

    file_path: str
    dataset: Literal["ticks", "bars"]
    source: str
    symbol: str
    timeframe: str
    minimum_datetime: datetime
    maximum_datetime: datetime
    row_count: int
    schema_version: int
    checksum: str
    created_at: datetime


class ScanRangeQuery(BaseModel):
    """Specification for querying a historical range."""

    model_config = ConfigDict(frozen=True)

    source: str
    symbol: str
    start: datetime
    end: datetime
    timeframe: str = "M1"
    columns: list[str] | None = None
    restore_prices: bool = True
    tick_size: Decimal | float = 0.00001


@runtime_checkable
class MarketDataStoreCapability(Protocol):
    """Capability protocol for the canonical partitioned Parquet market data store."""

    def append_ticks(
        self,
        table_or_df: pa.Table | pl.DataFrame | object,
        *,
        source: str,
        symbol: str,
        tick_size: Decimal | float = 0.00001,
    ) -> IngestionReceipt:
        """Append an immutable batch of ticks into the partitioned Parquet dataset.

        Args:
            table_or_df: PyArrow Table or Polars DataFrame containing tick records.
            source: Origin broker or provider (e.g. 'mt5-pepperstone', 'dukascopy').
            symbol: Instrument ticker symbol (e.g. 'EURUSD').
            tick_size: Instrument tick size for fixed-point integer conversion.

        Returns:
            IngestionReceipt summarizing committed parts and row counts.
        """
        ...

    def append_bars(
        self,
        table_or_df: pa.Table | pl.DataFrame | object,
        *,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        tick_size: Decimal | float = 0.00001,
    ) -> IngestionReceipt:
        """Append an immutable batch of M1 bars into the partitioned Parquet dataset.

        Args:
            table_or_df: PyArrow Table or Polars DataFrame containing bar records.
            source: Origin broker or provider.
            symbol: Instrument ticker symbol.
            timeframe: Bar timeframe code (default 'M1').
            tick_size: Instrument tick size for fixed-point integer conversion.

        Returns:
            IngestionReceipt summarizing committed parts and row counts.
        """
        ...

    def scan_ticks(
        self,
        query: ScanRangeQuery,
    ) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over partitioned tick data with pushdowns.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for deferred execution.
        """
        ...

    def scan_bars(
        self,
        query: ScanRangeQuery,
    ) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over partitioned bar data with pushdowns.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for deferred execution.
        """
        ...

    def query_sql(
        self,
        sql: str,
    ) -> duckdb.DuckDBPyRelation:
        """Execute analytical SQL query over Parquet files using DuckDB.

        Args:
            sql: SQL statement referencing 'ticks' or 'bars' views/tables.

        Returns:
            DuckDBPyRelation with query results.
        """
        ...

    def get_latest_timestamp(
        self,
        *,
        dataset: Literal["ticks", "bars"],
        source: str,
        symbol: str,
        timeframe: str = "M1",
    ) -> datetime | None:
        """Query the manifest catalog for the latest verified timestamp.

        Args:
            dataset: 'ticks' or 'bars'.
            source: Origin data source identifier.
            symbol: Instrument symbol.
            timeframe: Bar timeframe (ignored for ticks).

        Returns:
            Latest timestamp if recorded, otherwise None.
        """
        ...
