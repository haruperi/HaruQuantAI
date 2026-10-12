"""Authoritative instrument storage repository for host persistence subsystem.

Description:
    Provides transactional CRUD operations against `datamgr_instruments`, managing
    symbol metadata, broker mappings, tick parameters, and lot sizes.

Purpose:
    FEAT-HOST-PERSISTENCE: Authoritative instrument metadata CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-INSTRUMENTS: Instrument row CRUD.
      Associated: `InstrumentStore.create()`, `InstrumentStore.get_by_symbol()`,
        `InstrumentStore.update()`, `InstrumentStore.delete()`,
        `InstrumentStore.count()`
      Logging: DEBUG reads; INFO writes without payload values.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    db.instruments.create({"symbol": "EURUSD", "broker_id": 1})
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.engine import (
    _require_columns,
    _validate_columns,
)

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class InstrumentStore:
    """Authoritative host persistence operations for datamgr_instruments."""

    _columns = frozenset(
        {
            "connection",
            "broker_id",
            "description",
            "tick_size",
            "tick_step",
            "tick_value_in_money",
            "point_value",
            "decimals",
            "default_spread",
            "default_slippage",
            "min_volume",
            "max_volume",
            "lot_step",
            "margin_rate",
            "swap_long",
            "swap_short",
            "swap_3day_day",
            "commissions",
            "data_type",
            "alias",
            "exchange",
            "country",
            "sector",
            "min_distance",
            "order_size_multiplier",
            "order_size_step",
            "cot",
            "created_at_utc",
            "updated_at_utc",
        }
    )

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new instrument record and return its generated ID."""
        logger.debug(
            "InstrumentStore.create storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        record_copy = dict(record)
        record_copy.setdefault("min_distance", 0.0)
        record_copy.setdefault("order_size_multiplier", 1.0)
        record_copy.setdefault("order_size_step", 0.0)
        record_copy.setdefault("cot", None)

        columns = [
            "symbol",
            "connection",
            "broker_id",
            "description",
            "tick_size",
            "tick_step",
            "tick_value_in_money",
            "point_value",
            "decimals",
            "default_spread",
            "default_slippage",
            "min_volume",
            "max_volume",
            "lot_step",
            "margin_rate",
            "swap_long",
            "swap_short",
            "swap_3day_day",
            "commissions",
            "data_type",
            "alias",
            "exchange",
            "country",
            "sector",
            "min_distance",
            "order_size_multiplier",
            "order_size_step",
            "cot",
            "created_at_utc",
            "updated_at_utc",
        ]
        _validate_columns(record_copy, self._columns | {"symbol"})
        _require_columns(record_copy, tuple(columns))
        values = [record_copy[col] for col in columns]
        placeholders = ", ".join("?" for _ in columns)
        cols_str = ", ".join(columns)
        sql = f"INSERT INTO datamgr_instruments ({cols_str}) VALUES ({placeholders});"  # noqa: S608
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            last_id = cur.lastrowid or 0
        logger.info(
            "Created instrument in datamgr_instruments: %s (id=%d)",
            record["symbol"],
            last_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return last_id

    def get_by_symbol(self, symbol: str) -> dict[str, Any] | None:
        """Retrieve instrument record by symbol name."""
        logger.debug(
            "InstrumentStore.get_by_symbol storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "SELECT * FROM datamgr_instruments WHERE symbol = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (symbol,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def insert_if_absent(self, record: Mapping[str, Any]) -> bool:
        """Insert supplied instrument fields without replacing an existing symbol."""
        logger.debug(
            "InstrumentStore.insert_if_absent storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        columns = tuple(record)
        _validate_columns(record, self._columns | {"symbol"})
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT OR IGNORE INTO datamgr_instruments ({', '.join(columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders})"
        )
        with self._db.transaction() as conn:
            inserted = conn.execute(sql, tuple(record.values())).rowcount > 0
        logger.info(
            "Instrument insert-if-absent completed",
            extra={"inserted": inserted, "fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return inserted

    def list_instruments(
        self,
        connection: str | None = None,
        data_type: str | None = None,
        *,
        broker_id: int | None = None,
        search: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List instruments with optional connection, type, broker, or search."""
        logger.debug(
            "InstrumentStore.list_instruments storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        where_clauses: list[str] = []
        params: list[Any] = []
        if connection:
            where_clauses.append("connection = ?")
            params.append(connection)
        if data_type:
            where_clauses.append("data_type = ?")
            params.append(data_type)
        if broker_id is not None:
            where_clauses.append("broker_id = ?")
            params.append(broker_id)
        if search:
            where_clauses.append("(symbol LIKE ? OR description LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern])

        where_sql = f"WHERE {' AND '.join(where_clauses)} " if where_clauses else ""
        sql = (
            f"SELECT * FROM datamgr_instruments {where_sql}"  # noqa: S608
            "ORDER BY symbol ASC LIMIT ? OFFSET ?;"
        )
        params.extend([limit, offset])

        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update(self, symbol: str, updates: dict[str, Any]) -> bool:
        """Update fields for a symbol in datamgr_instruments."""
        logger.debug(
            "InstrumentStore.update storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy.pop("id", None)
        updates_copy.pop("symbol", None)
        _validate_columns(updates_copy, self._columns)
        if not updates_copy:
            return True
        set_clause = ", ".join(f"{k} = ?" for k in updates_copy)
        sql = f"UPDATE datamgr_instruments SET {set_clause} WHERE symbol = ?;"  # noqa: S608
        params = [*list(updates_copy.values()), symbol]
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            success = cur.rowcount > 0
        logger.info(
            "Updated instrument %s (success=%s)",
            symbol,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return success

    def delete(self, symbol: str) -> bool:
        """Delete an instrument record by symbol."""
        logger.debug(
            "InstrumentStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "DELETE FROM datamgr_instruments WHERE symbol = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (symbol,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted instrument %s (success=%s)",
            symbol,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return success

    def delete_many(self, symbols: list[str]) -> int:
        """Delete multiple instruments by symbol."""
        if not symbols:
            return 0
        logger.debug(
            "InstrumentStore.delete_many storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS", "count": len(symbols)},
        )
        placeholders = ", ".join("?" for _ in symbols)
        sql = f"DELETE FROM datamgr_instruments WHERE symbol IN ({placeholders});"  # noqa: S608
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(symbols))
            deleted_count = cur.rowcount
        logger.info(
            "Deleted %d instruments",
            deleted_count,
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        return deleted_count

    def count(self) -> int:
        """Return total instrument count."""
        logger.debug(
            "InstrumentStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-INSTRUMENTS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_instruments;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0
