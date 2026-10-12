"""Data Manager operational audit logs storage repository.

Description:
    Provides transactional CRUD operations against `datamgr_logs`, persisting
    structured operational logs, audit records, and error telemetry.

Purpose:
    FEAT-HOST-PERSISTENCE: Data Manager operational audit log CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-LOGS: Data Manager operational audit log CRUD.
      Associated: `LogStore.create()`, `LogStore.list_logs()`, `LogStore.clear()`,
        `LogStore.count()`
      Logging: DEBUG reads; INFO writes and clears.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    db.logs.create({"level": "INFO", "message": "Initialized"})
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class LogStore:
    """Authoritative host persistence operations for datamgr_logs."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new log record and return its generated ID."""
        logger.debug(
            "LogStore.create storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-LOGS"},
        )
        record_copy = dict(record)
        details = record_copy.get("details", {})
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        elif isinstance(details, str):
            details_str = details
        else:
            details_str = "{}"

        columns = ["timestamp_utc", "action", "message", "symbol", "details"]
        values = [
            record_copy.get("timestamp_utc", datetime.now(UTC).isoformat()),
            str(record_copy.get("action", "")).upper(),
            str(record_copy.get("message", "")),
            str(record_copy["symbol"]).upper() if record_copy.get("symbol") else None,
            details_str,
        ]
        placeholders = ", ".join(["?"] * len(columns))
        sql = (
            f"INSERT INTO datamgr_logs ({', '.join(columns)}) "  # noqa: S608
            f"VALUES ({placeholders});"
        )
        with self._db.transaction() as conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid or 0

    def list_logs(
        self,
        symbol: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List log records ordered newest first with optional filters."""
        logger.debug(
            "LogStore.list_logs storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-LOGS"},
        )
        query = "SELECT * FROM datamgr_logs WHERE 1=1"
        params: list[Any] = []
        if symbol:
            query += " AND UPPER(symbol) = UPPER(?)"
            params.append(symbol.strip())
        if action:
            query += " AND UPPER(action) = UPPER(?)"
            params.append(action.strip())
        query += " ORDER BY id DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(query, params).fetchall()
            results: list[dict[str, Any]] = []
            for r in rows:
                item: dict[str, Any] = dict(r)
                details_raw = item.get("details")
                if isinstance(details_raw, str):
                    fallback_details: dict[str, Any] = {}
                    try:
                        loaded = json.loads(details_raw)
                        item["details"] = (
                            loaded if isinstance(loaded, dict) else fallback_details
                        )
                    except json.JSONDecodeError, ValueError:
                        item["details"] = fallback_details
                results.append(item)
            return results

    def clear(self, symbol: str | None = None) -> int:
        """Delete log records, optionally filtered by symbol. Return deleted count."""
        logger.info(
            "LogStore.clear storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-LOGS"},
        )
        query = "DELETE FROM datamgr_logs"
        params: list[Any] = []
        if symbol:
            query += " WHERE UPPER(symbol) = UPPER(?)"
            params.append(symbol.strip())
        query += ";"
        with self._db.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount or 0

    def count(self, symbol: str | None = None) -> int:
        """Return count of log records."""
        logger.debug(
            "LogStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-LOGS"},
        )
        query = "SELECT COUNT(*) FROM datamgr_logs"
        params: list[Any] = []
        if symbol:
            query += " WHERE UPPER(symbol) = UPPER(?)"
            params.append(symbol.strip())
        query += ";"
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(query, params).fetchone()
            return int(row[0]) if row else 0
