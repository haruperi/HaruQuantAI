"""Trading session storage repository for host persistence subsystem.

Description:
    Provides transactional CRUD operations against `datamgr_sessions`, managing
    market schedules, session hours, and holiday calendars.

Purpose:
    FEAT-HOST-PERSISTENCE: Trading session schedules and calendars.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SESSIONS: Trading-session row CRUD.
      Associated: `SessionStore.upsert()`, `SessionStore.get_by_name()`,
        `SessionStore.delete()`, `SessionStore.count()`
      Logging: DEBUG reads; INFO write results.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    db.sessions.upsert({"name": "FOREX", "broker_id": 1, "tz": "UTC"})
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


class SessionStore:
    """Authoritative host persistence operations for datamgr_sessions."""

    _columns = frozenset(
        {
            "broker_id",
            "description",
            "timezone",
            "windows_json",
            "holidays_json",
            "is_default",
        }
    )

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize with parent DatabaseManager."""
        self._db = db

    def create(self, record: dict[str, Any]) -> int:
        """Insert a new session definition and return its generated ID."""
        logger.debug(
            "SessionStore.create storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        record_copy = dict(record)
        record_copy.setdefault("broker_id", -1)
        columns = (
            "name",
            "broker_id",
            "description",
            "timezone",
            "windows_json",
            "holidays_json",
            "is_default",
        )
        _validate_columns(record_copy, self._columns | {"name"})
        _require_columns(record_copy, columns)
        values = [record_copy[col] for col in columns]
        sql = (
            "INSERT INTO datamgr_sessions ("
            "name, broker_id, description, timezone, "
            "windows_json, holidays_json, is_default"
            ") VALUES (?, ?, ?, ?, ?, ?, ?);"
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            last_id = cur.lastrowid or 0
        logger.info(
            "Created session in datamgr_sessions: %s (id=%d)",
            record_copy.get("name"),
            last_id,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return last_id

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrieve session record by name."""
        logger.debug(
            "SessionStore.get_by_name storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT * FROM datamgr_sessions WHERE name = ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            row = cur.fetchone()
            if row is not None:
                return dict(row)
        return None

    def upsert(self, record: Mapping[str, Any], *, only_if_absent: bool = False) -> int:
        """Atomically insert or update a session and return its existing/new ID."""
        logger.debug(
            "SessionStore.upsert storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        record_copy = dict(record)
        record_copy.setdefault("broker_id", -1)
        columns = tuple(record_copy)
        _validate_columns(record_copy, self._columns | {"name"})
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(
            f"{col} = excluded.{col}" for col in columns if col != "name"
        )
        action = (
            "DO NOTHING"
            if only_if_absent or not updates
            else f"DO UPDATE SET {updates}"
        )
        sql = (
            f"INSERT INTO datamgr_sessions ({', '.join(columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders}) ON CONFLICT(name) {action}"
        )
        with self._db.transaction() as conn:
            conn.execute(sql, tuple(record_copy.values()))
            row = conn.execute(
                "SELECT id FROM datamgr_sessions WHERE name = ?", (record_copy["name"],)
            ).fetchone()
            session_id = int(row["id"])
        logger.info(
            "Session upsert completed",
            extra={"session_id": session_id, "fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return session_id

    def list_sessions(self, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        """List sessions in ascending name order."""
        logger.debug(
            "SessionStore.list_sessions storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT * FROM datamgr_sessions ORDER BY name ASC LIMIT ? OFFSET ?;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def list_by_broker(
        self, broker_id: int, limit: int = 1000, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List sessions filtered by broker profile ID."""
        logger.debug(
            "SessionStore.list_by_broker storage operation",
            extra={"broker_id": broker_id, "fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = (
            "SELECT * FROM datamgr_sessions WHERE broker_id = ? "
            "ORDER BY name ASC LIMIT ? OFFSET ?;"
        )
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (broker_id, limit, offset))
            return [dict(r) for r in cur.fetchall()]

    def update(self, name: str, updates: dict[str, Any]) -> bool:
        """Update fields for a session by name."""
        logger.debug(
            "SessionStore.update storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        if not updates:
            return True
        updates_copy = dict(updates)
        updates_copy.pop("id", None)
        updates_copy.pop("name", None)
        _validate_columns(updates_copy, self._columns)
        set_clause = ", ".join(f"{k} = ?" for k in updates_copy)
        sql = f"UPDATE datamgr_sessions SET {set_clause} WHERE name = ?;"  # noqa: S608
        params = [*list(updates_copy.values()), name]
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            success = cur.rowcount > 0
        logger.info(
            "Updated session %s (success=%s)",
            name,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return success

    def delete(self, name: str) -> bool:
        """Delete session definition by name."""
        logger.debug(
            "SessionStore.delete storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "DELETE FROM datamgr_sessions WHERE name = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            success = cur.rowcount > 0
        logger.info(
            "Deleted session %s (success=%s)",
            name,
            success,
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        return success

    def delete_many(self, names: list[str]) -> int:
        """Batch delete session definitions by names."""
        logger.debug(
            "SessionStore.delete_many storage operation",
            extra={"names_count": len(names), "fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        if not names:
            return 0
        placeholders = ", ".join("?" for _ in names)
        sql = f"DELETE FROM datamgr_sessions WHERE name IN ({placeholders});"  # noqa: S608
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(names))
            deleted_count = cur.rowcount or 0
        logger.info(
            "Batch deleted %d session(s)",
            deleted_count,
            extra={
                "deleted_count": deleted_count,
                "fr_id": "FR-HOST-PERSISTENCE-SESSIONS",
            },
        )
        return deleted_count

    def count(self) -> int:
        """Return total session definitions count."""
        logger.debug(
            "SessionStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-SESSIONS"},
        )
        sql = "SELECT COUNT(*) FROM datamgr_sessions;"
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row else 0
