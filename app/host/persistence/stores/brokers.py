"""Broker execution profiles and stock configurations storage repository.

Description:
    Provides transactional CRUD operations against `datamgr_brokers` and
    `datamgr_broker_stocks`, managing broker profiles, server timezone offsets,
    and associated symbol mappings. Default profiles belong to BrokerService in
    the workspace.

Purpose:
    FEAT-HOST-PERSISTENCE: Broker profile and stock configuration persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-BROKERS: Broker profile and stock configuration persistence.
      Associated: `BrokerStore.list_profiles()`, `BrokerStore.get_profile()`,
        `BrokerStore.get_profile_by_name()`, `BrokerStore.create_profile()`,
        `BrokerStore.update_profile()`, `BrokerStore.delete_profile()`,
        `BrokerStore.list_stocks()`, `BrokerStore.replace_stocks()`,
        `BrokerStore.get_counts()`, `BrokerStore.count()`,
        `BrokerStore.seed_defaults()`
      Logging: DEBUG reads; INFO writes and lifecycle events.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    profiles = db.brokers.list_profiles()
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.errors import PersistenceError, ValidationError

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class BrokerStore:
    """Manage authoritative broker profiles and constituent stock persistence."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize BrokerStore with DatabaseManager."""
        self._db = db

    def list_profiles(self) -> list[dict[str, Any]]:
        """Return all broker rows ordered by id ascending."""
        logger.debug(
            "BrokerStore.list_profiles storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        sql = """
            SELECT id, name, is_system, description, server_timezone,
                   postfix, enabled, mt_use, stockpicker_use,
                   created_at_utc, updated_at_utc
            FROM datamgr_broker
            ORDER BY id ASC;
        """
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def count(self) -> int:
        """Return the number of stored broker profiles."""
        logger.debug(
            "BrokerStore.count storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM datamgr_broker;")
            return int(cur.fetchone()[0])

    def get_profile(self, broker_id: int) -> dict[str, Any] | None:
        """Return a single broker profile by ID, or None if not found."""
        logger.debug(
            "BrokerStore.get_profile storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        sql = """
            SELECT id, name, is_system, description, server_timezone,
                   postfix, enabled, mt_use, stockpicker_use,
                   created_at_utc, updated_at_utc
            FROM datamgr_broker
            WHERE id = ?;
        """
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (broker_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_profile_by_name(self, name: str) -> dict[str, Any] | None:
        """Return a single broker profile by name (case-insensitive), or None."""
        logger.debug(
            "BrokerStore.get_profile_by_name storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        sql = """
            SELECT id, name, is_system, description, server_timezone,
                   postfix, enabled, mt_use, stockpicker_use,
                   created_at_utc, updated_at_utc
            FROM datamgr_broker
            WHERE UPPER(name) = UPPER(?);
        """
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            row = cur.fetchone()
            return dict(row) if row else None

    def create_profile(self, profile: dict[str, Any]) -> int:
        """Insert a new broker profile record. Returns the new broker id."""
        logger.debug(
            "BrokerStore.create_profile storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        if not profile.get("name") or not str(profile["name"]).strip():
            raise ValidationError("Broker name must not be empty.")
        now = datetime.now(UTC).isoformat()
        sql = """
            INSERT INTO datamgr_broker (
                name, is_system, description, server_timezone, postfix,
                enabled, mt_use, stockpicker_use, created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            str(profile["name"]).strip(),
            int(bool(profile.get("is_system", False))),
            str(profile.get("description", "")),
            str(profile.get("server_timezone", "UTC")),
            str(profile.get("postfix", "")),
            int(bool(profile.get("enabled", True))),
            int(bool(profile.get("mt_use", True))),
            int(bool(profile.get("stockpicker_use", False))),
            now,
            now,
        )
        with self._db.transaction() as conn:
            try:
                cur = conn.cursor()
                cur.execute(sql, params)
                new_id = cur.lastrowid
                if new_id is None:
                    raise PersistenceError("Insert failed to return row id.")
            except sqlite3.IntegrityError as exc:
                raise PersistenceError(
                    f"Broker name '{profile['name']}' already exists."
                ) from exc
        logger.info(
            "Broker profile created",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS", "broker_id": new_id},
        )
        return new_id

    @staticmethod
    def _to_int_bool(val: object) -> int:
        """Convert a boolean or integer-like value to 0 or 1."""
        return int(bool(val))

    def update_profile(self, broker_id: int, updates: dict[str, Any]) -> bool:
        """Update an existing non-system broker profile.

        Raises:
            ValidationError: If broker name is empty.
            PersistenceError: If profile is a system broker or update fails.
        """
        logger.debug(
            "BrokerStore.update_profile storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        now = datetime.now(UTC).isoformat()
        allowed_fields: dict[str, Callable[[Any], Any]] = {
            "name": str,
            "description": str,
            "server_timezone": str,
            "postfix": str,
            "enabled": self._to_int_bool,
            "mt_use": self._to_int_bool,
            "stockpicker_use": self._to_int_bool,
        }
        set_clauses: list[str] = []
        params: list[Any] = []
        for key, val in updates.items():
            if key in allowed_fields:
                if key == "name" and (val is None or not str(val).strip()):
                    raise ValidationError("Broker name must not be empty.")
                converter = allowed_fields[key]
                converted = converter(val) if val is not None else val
                set_clauses.append(f"{key} = ?")
                params.append(converted)
        if not set_clauses:
            return False
        set_clauses.append("updated_at_utc = ?")
        params.append(now)
        params.append(broker_id)
        sql = f"UPDATE datamgr_broker SET {', '.join(set_clauses)} WHERE id = ?;"  # noqa: S608
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_system, name FROM datamgr_broker WHERE id = ?;",
                (broker_id,),
            )
            existing = cur.fetchone()
            if not existing:
                return False
            if bool(existing["is_system"]):
                raise PersistenceError(
                    f"Cannot modify system broker profile '{existing['name']}' "
                    f"(id={broker_id})."
                )
            try:
                cur.execute(sql, params)
                updated = cur.rowcount > 0
            except sqlite3.IntegrityError as exc:
                raise PersistenceError(
                    f"Broker update failed: name conflict on id={broker_id}."
                ) from exc
        logger.info(
            "Broker profile updated",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS", "broker_id": broker_id},
        )
        return updated

    def delete_profile(self, broker_id: int) -> bool:
        """Delete a non-system broker profile and cascade to datamgr_broker_stock."""
        logger.debug(
            "BrokerStore.delete_profile storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_system, name FROM datamgr_broker WHERE id = ?;", (broker_id,)
            )
            row = cur.fetchone()
            if not row:
                return False
            if bool(row["is_system"]):
                raise PersistenceError(
                    f"Cannot delete system broker profile '{row['name']}' "
                    f"(id={broker_id})."
                )
            cur.execute(
                "SELECT COUNT(*) FROM datamgr_instruments WHERE broker_id = ?;",
                (broker_id,),
            )
            inst_count = cur.fetchone()[0]
            if inst_count > 0:
                raise PersistenceError(
                    f"Cannot delete broker profile '{row['name']}' because "
                    f"{inst_count} instruments reference it"
                )
            sess_table = cur.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='datamgr_sessions';"
            ).fetchone()
            if sess_table:
                sess_cols = {
                    r["name"]
                    for r in cur.execute(
                        "PRAGMA table_info(datamgr_sessions);"
                    ).fetchall()
                }
                if "broker_id" in sess_cols:
                    cur.execute(
                        "SELECT COUNT(*) FROM datamgr_sessions WHERE broker_id = ?;",
                        (broker_id,),
                    )
                    sess_count = cur.fetchone()[0]
                    if sess_count > 0:
                        raise PersistenceError(
                            f"Cannot delete broker profile '{row['name']}' because "
                            f"{sess_count} sessions reference it"
                        )
            cur.execute(
                "DELETE FROM datamgr_broker_stock WHERE broker_id = ?;", (broker_id,)
            )
            cur.execute("DELETE FROM datamgr_broker WHERE id = ?;", (broker_id,))
            deleted = cur.rowcount > 0
        logger.info(
            "Broker profile deleted",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS", "broker_id": broker_id},
        )
        return deleted

    def list_stocks(self, broker_id: int) -> list[str]:
        """Return list of uppercase tickers associated with a broker."""
        logger.debug(
            "BrokerStore.list_stocks storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        sql = """
            SELECT ticker FROM datamgr_broker_stock
            WHERE broker_id = ?
            ORDER BY ticker ASC;
        """
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(sql, (broker_id,))
            return [r[0] for r in cur.fetchall()]

    def replace_stocks(self, broker_id: int, tickers: list[str]) -> int:
        """Replace the constituent stocks list for a broker in an atomic transaction."""
        logger.debug(
            "BrokerStore.replace_stocks storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        unique_tickers = sorted({t.strip().upper() for t in tickers if t.strip()})
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_system, stockpicker_use FROM datamgr_broker WHERE id = ?;",
                (broker_id,),
            )
            existing = cur.fetchone()
            if not existing:
                raise PersistenceError(f"Broker profile ID {broker_id} does not exist")
            if bool(existing["is_system"]):
                raise PersistenceError("Cannot modify stocks for system broker profile")
            if not bool(existing["stockpicker_use"]):
                raise PersistenceError(
                    "Broker profile is not configured for stockpicker use"
                )
            cur.execute(
                "DELETE FROM datamgr_broker_stock WHERE broker_id = ?;", (broker_id,)
            )
            if unique_tickers:
                insert_sql = (
                    "INSERT INTO datamgr_broker_stock (broker_id, ticker) "
                    "VALUES (?, ?);"
                )
                cur.executemany(insert_sql, [(broker_id, t) for t in unique_tickers])
        logger.info(
            "Broker constituent stocks replaced",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
                "broker_id": broker_id,
                "count": len(unique_tickers),
            },
        )
        return len(unique_tickers)

    def get_counts(self, broker_id: int) -> dict[str, int]:
        """Return counts of dependent records (stocks, instruments, sessions)."""
        logger.debug(
            "BrokerStore.get_counts storage operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM datamgr_broker_stock WHERE broker_id = ?;",
                (broker_id,),
            )
            stock_row = cur.fetchone()
            cur.execute(
                "SELECT COUNT(*) FROM datamgr_instruments WHERE broker_id = ?;",
                (broker_id,),
            )
            inst_row = cur.fetchone()
            sess_count = 0
            sess_table = cur.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='datamgr_sessions';"
            ).fetchone()
            if sess_table:
                sess_cols = {
                    r["name"]
                    for r in cur.execute(
                        "PRAGMA table_info(datamgr_sessions);"
                    ).fetchall()
                }
                if "broker_id" in sess_cols:
                    cur.execute(
                        "SELECT COUNT(*) FROM datamgr_sessions WHERE broker_id = ?;",
                        (broker_id,),
                    )
                    sess_count = int(cur.fetchone()[0])

        return {
            "customized_stocks": int(stock_row[0]) if stock_row else 0,
            "customized_instruments": int(inst_row[0]) if inst_row else 0,
            "customized_sessions": sess_count,
        }

    def seed_defaults(self, defaults: list[dict[str, Any]]) -> None:
        """Seed default system broker profiles from caller-provided definitions."""
        with self._db.transaction() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='datamgr_broker'"
            ).fetchone()
            if not exists:
                return
            now_str = datetime.now(UTC).isoformat()
            for item in defaults:
                row = conn.execute(
                    "SELECT id, name FROM datamgr_broker WHERE id = ? OR name = ?",
                    (item["id"], item["name"]),
                ).fetchone()
                if not row:
                    conn.execute(
                        """
                        INSERT INTO datamgr_broker (
                            id, name, is_system, description, server_timezone,
                            postfix, enabled, mt_use, stockpicker_use,
                            created_at_utc, updated_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                        """,
                        (
                            item["id"],
                            item["name"],
                            item["is_system"],
                            item["description"],
                            item["server_timezone"],
                            item["postfix"],
                            item["mt_use"],
                            item["stockpicker_use"],
                            now_str,
                            now_str,
                        ),
                    )
                elif row[1] != item["name"] and item["is_system"]:
                    conn.execute(
                        "UPDATE datamgr_broker SET name = ?, updated_at_utc = ? "
                        "WHERE id = ?",
                        (item["name"], now_str, item["id"]),
                    )

        logger.info(
            "System broker profile defaults ensured",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
