"""Historical market dataset storage repository for host persistence subsystem.

Description:
    Provides transactional CRUD operations against `datamgr_datasets`, tracking
    dataset metadata, timeframe configurations, and bar aggregates.

Purpose:
    FEAT-HOST-PERSISTENCE: Historical dataset metadata and partition CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-DATASETS: Metadata CRUD and bar aggregates.
      Associated: `DatasetStore.save()`, `DatasetStore.get_by_id()`,
        `DatasetStore.sum_bars()`, `DatasetStore.count()`
      Logging: DEBUG reads; INFO writes.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    datasets = db.datasets.list_datasets(limit=50)
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.engine import (
    _require_columns,
    _validate_columns,
)

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class DatasetStore:
    """Authoritative host persistence operations for datamgr_datasets."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def sum_bars(self) -> int:
        """Return the sum of stored dataset bar counts."""
        logger.debug(
            "DatasetStore.sum_bars storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(bars), 0) FROM datamgr_datasets"
            ).fetchone()
        logger.debug(
            "Dataset bar sum read", extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"}
        )
        return int(row[0])

    def save(self, record: dict[str, Any], *, update_columns: tuple[str, ...]) -> str:
        """Insert a complete row or update caller-selected columns on conflict."""
        logger.debug(
            "DatasetStore.save storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        columns = [
            "id",
            "source",
            "symbol",
            "underlying",
            "instrument",
            "timeframe",
            "broker",
            "broker_name",
            "timezone",
            "category",
            "date_from",
            "date_to",
            "bars",
            "created_at",
            "updated_at",
            "path",
            "data_kind",
            "quality_score",
            "lineage_json",
            "schema_version",
        ]
        _validate_columns(record, frozenset(columns))
        _require_columns(record, tuple(columns))
        _validate_columns(dict.fromkeys(update_columns), frozenset(columns) - {"id"})
        values = [record[col] for col in columns]
        dataset_id = str(record["id"])
        updates = ", ".join(f"{col} = excluded.{col}" for col in update_columns)
        action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT INTO datamgr_datasets ({', '.join(columns)}) "  # noqa: S608 - fixed column allowlist and placeholders
            f"VALUES ({placeholders}) ON CONFLICT(id) {action}"
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
        logger.info(
            "Saved dataset in datamgr_datasets: %s",
            dataset_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        return dataset_id

    def get_by_id(self, dataset_id: str) -> dict[str, Any] | None:
        """Retrieve dataset record by primary ID."""
        logger.debug(
            "DatasetStore.get_by_id storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "SELECT * FROM datamgr_datasets WHERE id = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (dataset_id,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def list_datasets(
        self,
        source: str | None = None,
        symbol: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List datasets matching optional source and symbol filters."""
        logger.debug(
            "DatasetStore.list_datasets storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        if source and symbol:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE source = ? "
                "AND symbol = ? ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [source, symbol, limit, offset]
        elif source:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE source = ? "
                "ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [source, limit, offset]
        elif symbol:
            sql = (
                "SELECT * FROM datamgr_datasets WHERE symbol = ? "
                "ORDER BY symbol ASC, timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [symbol, limit, offset]
        else:
            sql = (
                "SELECT * FROM datamgr_datasets ORDER BY symbol ASC, "
                "timeframe ASC LIMIT ? OFFSET ?;"
            )
            params = [limit, offset]

        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def delete(self, dataset_id: str) -> bool:
        """Delete dataset record by ID."""
        logger.debug(
            "DatasetStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "DELETE FROM datamgr_datasets WHERE id = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='source_datasets';"
            )
            if cur.fetchone():
                cur.execute(
                    "DELETE FROM source_partitions WHERE dataset_id = ?;",
                    (dataset_id,),
                )
                cur.execute(
                    "DELETE FROM source_datasets WHERE id = ?;",
                    (dataset_id,),
                )
            cur.execute(sql, (dataset_id,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted dataset %s (success=%s)",
            dataset_id,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        return success

    def count(self) -> int:
        """Return total dataset records count."""
        logger.debug(
            "DatasetStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-DATASETS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_datasets;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0
