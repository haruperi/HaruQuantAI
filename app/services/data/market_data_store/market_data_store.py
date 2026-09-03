"""Partitioned Parquet Market Data Store Service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, override

import polars as pl
import pyarrow as pa

from app.contracts.data.market_data_store import (
    IngestionReceipt,
    MarketDataStoreCapability,
    ScanRangeQuery,
)
from app.services.data.market_data_store.catalog import MarketDataCatalog
from app.services.data.market_data_store.config import MarketDataStoreConfig
from app.services.data.market_data_store.reader import MarketDataReader
from app.services.data.market_data_store.writer import MarketDataWriter

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal

    import duckdb


class MarketDataStoreService(MarketDataStoreCapability):
    """Canonical Historical Market Data Store implementation for HaruQuantAI."""

    def __init__(self, config: MarketDataStoreConfig | None = None) -> None:
        """Initialize the MarketDataStoreService.

        Args:
            config: Optional store configuration. Defaults to standard configuration.
        """
        self._config = config or MarketDataStoreConfig()
        self._catalog = MarketDataCatalog(self._config.manifest_database_path)
        self._writer = MarketDataWriter(self._config, catalog=self._catalog)
        self._reader = MarketDataReader(self._config)

    @property
    def config(self) -> MarketDataStoreConfig:
        """Return the current store configuration."""
        return self._config

    @property
    def catalog(self) -> MarketDataCatalog:
        """Return the manifest catalog instance."""
        return self._catalog

    @override
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
            source: Origin broker or provider (e.g. 'dukascopy').
            symbol: Instrument ticker symbol (e.g. 'EURUSD').
            tick_size: Instrument tick size for fixed-point integer conversion.

        Returns:
            IngestionReceipt summarizing committed parts and row counts.
        """
        table = self._coerce_to_pyarrow(table_or_df)
        return self._writer.append_ticks(
            table, source=source, symbol=symbol, tick_size=tick_size
        )

    @override
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
        table = self._coerce_to_pyarrow(table_or_df)
        return self._writer.append_bars(
            table,
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            tick_size=tick_size,
        )

    @override
    def scan_ticks(self, query: ScanRangeQuery) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over partitioned tick data with pushdowns.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for deferred execution.
        """
        return self._reader.scan_ticks(query)

    @override
    def scan_bars(self, query: ScanRangeQuery) -> pl.LazyFrame:
        """Open a Polars LazyFrame scan over partitioned bar data with pushdowns.

        Args:
            query: Range, partition, and projection query specification.

        Returns:
            Polars LazyFrame ready for deferred execution.
        """
        return self._reader.scan_bars(query)

    @override
    def query_sql(self, sql: str) -> duckdb.DuckDBPyRelation:
        """Execute analytical SQL query over Parquet files using DuckDB.

        Args:
            sql: SQL statement referencing 'ticks' or 'bars' views.

        Returns:
            DuckDBPyRelation with query results.
        """
        return self._reader.query_sql(sql)

    @override
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
        return self._catalog.get_latest_timestamp(
            dataset=dataset, source=source, symbol=symbol, timeframe=timeframe
        )

    def close(self) -> None:
        """Release open database connections and locks."""
        self._catalog.close()

    @staticmethod
    def _coerce_to_pyarrow(table_or_df: object) -> pa.Table:
        """Convert Polars DataFrame, Pandas DataFrame, or PyArrow Table to pa.Table."""
        if isinstance(table_or_df, pa.Table):
            return table_or_df
        if hasattr(table_or_df, "to_arrow"):
            return table_or_df.to_arrow()
        if hasattr(pa.Table, "from_pandas") and hasattr(table_or_df, "to_dict"):
            import pandas as pd

            if isinstance(table_or_df, pd.DataFrame):
                df = table_or_df
                if (
                    isinstance(df.index, pd.DatetimeIndex)
                    and "datetime" not in df.columns
                ):
                    df = df.reset_index().rename(columns={"index": "datetime"})
                return pa.Table.from_pandas(df, preserve_index=False)
        msg = f"Unsupported data type for market data ingestion: {type(table_or_df)}"
        raise TypeError(msg)
