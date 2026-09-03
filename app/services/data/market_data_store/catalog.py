"""DuckDB Manifest & Ingestion State Catalog."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import duckdb

from app.contracts.data.market_data_store import CatalogPartRecord


class MarketDataCatalog:
    """Embedded DuckDB Catalog tracking committed Parquet parts."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: str | Path | None = None) -> None:
        """Initialize the catalog connection.

        Args:
            database_path: Path to DuckDB database, or None for in-memory.
        """
        self._lock = threading.RLock()
        self._db_path = str(database_path) if database_path else ":memory:"
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn: duckdb.DuckDBPyConnection | None = duckdb.connect(
            database=self._db_path
        )
        self._init_schema()

    @property
    def _connection(self) -> duckdb.DuckDBPyConnection:
        """Return active DuckDB connection or raise if closed."""
        if self._conn is None:
            msg = "Catalog connection is closed"
            raise RuntimeError(msg)
        return self._conn

    def _init_schema(self) -> None:
        """Ensure manifest tables and indices exist."""
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ingestion_manifest (
                    file_path VARCHAR PRIMARY KEY,
                    dataset VARCHAR NOT NULL,
                    source VARCHAR NOT NULL,
                    symbol VARCHAR NOT NULL,
                    timeframe VARCHAR NOT NULL,
                    minimum_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                    maximum_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                    row_count BIGINT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    checksum VARCHAR NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_manifest_lookup
                ON ingestion_manifest(
                    dataset, source, symbol, timeframe, maximum_datetime
                );
                """
            )

    def register_part(self, record: CatalogPartRecord) -> None:
        """Atomically insert or update a committed Parquet part record.

        Args:
            record: Manifest metadata for the committed file.
        """
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO ingestion_manifest (
                    file_path, dataset, source, symbol, timeframe,
                    minimum_datetime, maximum_datetime, row_count,
                    schema_version, checksum, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    record.file_path,
                    record.dataset,
                    record.source,
                    record.symbol,
                    record.timeframe,
                    record.minimum_datetime,
                    record.maximum_datetime,
                    record.row_count,
                    record.schema_version,
                    record.checksum,
                    record.created_at,
                ],
            )

    def get_latest_timestamp(
        self,
        dataset: Literal["ticks", "bars"],
        source: str,
        symbol: str,
        timeframe: str = "M1",
    ) -> datetime | None:
        """Retrieve the latest verified timestamp for a series without scanning files.

        Args:
            dataset: 'ticks' or 'bars'.
            source: Broker/source identifier.
            symbol: Ticker symbol.
            timeframe: Timeframe code (ignored when dataset is 'ticks').

        Returns:
            Latest UTC datetime if any records exist, otherwise None.
        """
        with self._lock:
            if dataset == "ticks":
                res = self._connection.execute(
                    """
                    SELECT MAX(maximum_datetime)
                    FROM ingestion_manifest
                    WHERE dataset = 'ticks' AND source = ? AND symbol = ?
                    """,
                    [source, symbol],
                ).fetchone()
            else:
                res = self._connection.execute(
                    """
                    SELECT MAX(maximum_datetime)
                    FROM ingestion_manifest
                    WHERE dataset = ? AND source = ? AND symbol = ? AND timeframe = ?
                    """,
                    [dataset, source, symbol, timeframe],
                ).fetchone()

            if res and res[0] is not None:
                ts = res[0]
                if isinstance(ts, datetime):
                    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)
            return None

    def list_parts(
        self,
        dataset: Literal["ticks", "bars"],
        source: str,
        symbol: str,
        timeframe: str = "M1",
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CatalogPartRecord]:
        """List active Parquet parts overlapping an optional time range.

        Args:
            dataset: 'ticks' or 'bars'.
            source: Broker/source identifier.
            symbol: Ticker symbol.
            timeframe: Timeframe code (ignored when dataset is 'ticks').
            start: Optional range start.
            end: Optional range end.

        Returns:
            List of CatalogPartRecord items.
        """
        if dataset == "ticks":
            query = """
                SELECT file_path, dataset, source, symbol, timeframe,
                       minimum_datetime, maximum_datetime, row_count,
                       schema_version, checksum, created_at
                FROM ingestion_manifest
                WHERE dataset = 'ticks' AND source = ? AND symbol = ?
            """
            params: list[Any] = [source, symbol]
        else:
            query = """
                SELECT file_path, dataset, source, symbol, timeframe,
                       minimum_datetime, maximum_datetime, row_count,
                       schema_version, checksum, created_at
                FROM ingestion_manifest
                WHERE dataset = ? AND source = ? AND symbol = ? AND timeframe = ?
            """
            params = [dataset, source, symbol, timeframe]

        if start is not None:
            query += " AND maximum_datetime >= ?"
            params.append(start)
        if end is not None:
            query += " AND minimum_datetime < ?"
            params.append(end)

        query += " ORDER BY minimum_datetime ASC"

        with self._lock:
            rows = self._connection.execute(query, params).fetchall()

        records: list[CatalogPartRecord] = []
        for r in rows:
            min_dt = r[5] if r[5].tzinfo else r[5].replace(tzinfo=UTC)
            max_dt = r[6] if r[6].tzinfo else r[6].replace(tzinfo=UTC)
            created_at = r[10] if r[10].tzinfo else r[10].replace(tzinfo=UTC)
            records.append(
                CatalogPartRecord(
                    file_path=r[0],
                    dataset=r[1],
                    source=r[2],
                    symbol=r[3],
                    timeframe=r[4],
                    minimum_datetime=min_dt,
                    maximum_datetime=max_dt,
                    row_count=r[7],
                    schema_version=r[8],
                    checksum=r[9],
                    created_at=created_at,
                )
            )
        return records

    def get_summary(self) -> list[dict[str, Any]]:
        """Return aggregated summary counts across all stored datasets."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT dataset, source, symbol, timeframe,
                       COUNT(*) AS part_count,
                       SUM(row_count) AS total_rows,
                       MIN(minimum_datetime) AS earliest_dt,
                       MAX(maximum_datetime) AS latest_dt
                FROM ingestion_manifest
                GROUP BY dataset, source, symbol, timeframe
                ORDER BY dataset, source, symbol, timeframe
                """
            ).fetchall()

        return [
            {
                "dataset": r[0],
                "source": r[1],
                "symbol": r[2],
                "timeframe": r[3],
                "part_count": r[4],
                "total_rows": r[5],
                "earliest_datetime": r[6],
                "latest_datetime": r[7],
            }
            for r in rows
        ]

    def close(self) -> None:
        """Close the underlying DuckDB catalog connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
