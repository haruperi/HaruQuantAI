"""Broker execution profiles and stock configurations storage repository.

Description:
    Provides transactional CRUD operations against `datamgr_brokers` and
    `datamgr_broker_stocks`, managing broker profiles, server timezone offsets,
    and associated symbol mappings.

Purpose:
    FEAT-HOST-PERSISTENCE: Broker profile and stock configuration persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-BROKERS: Broker profile and stock configuration persistence.
      Associated: `BrokerStore.list_profiles()`, `BrokerStore.get_profile()`,
        `BrokerStore.get_profile_by_name()`, `BrokerStore.create_profile()`,
        `BrokerStore.update_profile()`, `BrokerStore.delete_profile()`,
        `BrokerStore.list_stocks()`, `BrokerStore.replace_stocks()`,
        `BrokerStore.get_counts()`, `BrokerStore.ensure_defaults()`
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
        with self._db.connection(query_only=True) as conn:
            exists: sqlite3.Row | None = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='datamgr_broker'"
            ).fetchone()
            if not exists:
                return []
            rows = conn.execute(
                "SELECT * FROM datamgr_broker ORDER BY id ASC"
            ).fetchall()
        logger.debug(
            "Broker rows read",
            extra={"count": len(rows), "fr_id": "FR-HOST-PERSISTENCE-BROKERS"},
        )
        return [dict(row) for row in rows]

    def get_profile(self, broker_id: int) -> dict[str, Any] | None:
        """Fetch a single broker profile by ID."""
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM datamgr_broker WHERE id = ?", (broker_id,)
            ).fetchone()
        logger.debug(
            "Broker profile read by id",
            extra={
                "broker_id": broker_id,
                "found": row is not None,
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return dict(row) if row else None

    def get_profile_by_name(self, name: str) -> dict[str, Any] | None:
        """Fetch a single broker profile by name (case-insensitive)."""
        clean = name.strip()
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM datamgr_broker WHERE LOWER(name) = LOWER(?)",
                (clean,),
            ).fetchone()
        logger.debug(
            "Broker profile read by name",
            extra={
                "broker_name": name,
                "found": row is not None,
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return dict(row) if row else None

    def create_profile(self, data: dict[str, Any]) -> int:
        """Create a new broker profile record."""
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValidationError("Broker profile name must not be empty")
        now_str = datetime.now(UTC).isoformat()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO datamgr_broker (
                    name, is_system, description, server_timezone,
                    postfix, enabled, mt_use, stockpicker_use,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    int(bool(data.get("is_system", 0))),
                    str(data.get("description", "")),
                    str(data.get("server_timezone", "UTC")),
                    str(data.get("postfix", "")),
                    int(bool(data.get("enabled", 1))),
                    int(bool(data.get("mt_use", 0))),
                    int(bool(data.get("stockpicker_use", 0))),
                    str(data.get("created_at_utc") or now_str),
                    str(data.get("updated_at_utc") or now_str),
                ),
            )
            broker_id = cursor.lastrowid or 0
        logger.info(
            "Broker profile created",
            extra={
                "broker_id": broker_id,
                "broker_name": name,
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return broker_id

    def update_profile(self, broker_id: int, data: dict[str, Any]) -> bool:
        """Update an existing broker profile."""
        now_str = datetime.now(UTC).isoformat()
        with self._db.transaction() as conn:
            existing = conn.execute(
                "SELECT is_system FROM datamgr_broker WHERE id = ?", (broker_id,)
            ).fetchone()
            if not existing:
                raise PersistenceError(f"Broker profile ID {broker_id} does not exist")
            if bool(existing["is_system"]):
                raise PersistenceError("System broker profile cannot be modified")

            name = str(data.get("name", "")).strip()
            if not name:
                raise ValidationError("Broker profile name must not be empty")

            conn.execute(
                """
                UPDATE datamgr_broker
                SET name = ?, description = ?, server_timezone = ?,
                    postfix = ?, enabled = ?, mt_use = ?, stockpicker_use = ?,
                    updated_at_utc = ?
                WHERE id = ?
                """,
                (
                    name,
                    str(data.get("description", "")),
                    str(data.get("server_timezone", "UTC")),
                    str(data.get("postfix", "")),
                    int(bool(data.get("enabled", 1))),
                    int(bool(data.get("mt_use", 0))),
                    int(bool(data.get("stockpicker_use", 0))),
                    str(data.get("updated_at_utc") or now_str),
                    broker_id,
                ),
            )
        logger.info(
            "Broker profile updated",
            extra={
                "broker_id": broker_id,
                "broker_name": name,
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return True

    def delete_profile(self, broker_id: int) -> bool:
        """Delete a broker profile after validating dependency invariants."""
        with self._db.transaction() as conn:
            existing = conn.execute(
                "SELECT is_system, name FROM datamgr_broker WHERE id = ?", (broker_id,)
            ).fetchone()
            if not existing:
                return False
            if bool(existing["is_system"]):
                raise PersistenceError("Cannot delete system broker profile")

            # Check instrument dependencies
            inst_count_row = conn.execute(
                "SELECT COUNT(*) FROM datamgr_instruments WHERE broker_id = ?",
                (broker_id,),
            ).fetchone()
            if inst_count_row and inst_count_row[0] > 0:
                raise PersistenceError(
                    f"Cannot delete broker profile '{existing['name']}' because "
                    f"{inst_count_row[0]} instruments reference it"
                )

            # Check session dependencies
            sess_cols = {
                col[1]
                for col in conn.execute(
                    "PRAGMA table_info(datamgr_sessions)"
                ).fetchall()
            }
            if "broker_id" in sess_cols:
                sess_count_row = conn.execute(
                    "SELECT COUNT(*) FROM datamgr_sessions WHERE broker_id = ?",
                    (broker_id,),
                ).fetchone()
                if sess_count_row and sess_count_row[0] > 0:
                    raise PersistenceError(
                        f"Broker profile '{existing['name']}' is used by "
                        f"{sess_count_row[0]} session(s)"
                    )

            # Remove associated stocks and profile
            conn.execute(
                "DELETE FROM datamgr_broker_stock WHERE broker_id = ?", (broker_id,)
            )
            conn.execute("DELETE FROM datamgr_broker WHERE id = ?", (broker_id,))
        logger.info(
            "Broker profile deleted",
            extra={
                "broker_id": broker_id,
                "broker_name": existing["name"],
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return True

    def list_stocks(self, broker_id: int) -> list[str]:
        """Fetch stock tickers associated with a broker profile."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT ticker FROM datamgr_broker_stock WHERE broker_id = ? "
                "ORDER BY id ASC",
                (broker_id,),
            ).fetchall()
        logger.debug(
            "Broker stocks read",
            extra={
                "broker_id": broker_id,
                "count": len(rows),
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )
        return [str(row[0]) for row in rows]

    def replace_stocks(self, broker_id: int, tickers: list[str]) -> None:
        """Replace all stock tickers for a broker profile."""
        with self._db.transaction() as conn:
            existing = conn.execute(
                "SELECT is_system, stockpicker_use FROM datamgr_broker WHERE id = ?",
                (broker_id,),
            ).fetchone()
            if not existing:
                raise PersistenceError(f"Broker profile ID {broker_id} does not exist")
            if bool(existing["is_system"]):
                raise PersistenceError("Cannot modify stocks for system broker profile")
            if not bool(existing["stockpicker_use"]):
                raise PersistenceError(
                    "Broker profile is not configured for stockpicker use"
                )

            conn.execute(
                "DELETE FROM datamgr_broker_stock WHERE broker_id = ?", (broker_id,)
            )
            clean_tickers = sorted({t.strip() for t in tickers if t.strip()})
            for ticker in clean_tickers:
                conn.execute(
                    "INSERT INTO datamgr_broker_stock (broker_id, ticker) "
                    "VALUES (?, ?)",
                    (broker_id, ticker),
                )
        logger.info(
            "Broker stocks updated",
            extra={
                "broker_id": broker_id,
                "count": len(clean_tickers),
                "fr_id": "FR-HOST-PERSISTENCE-BROKERS",
            },
        )

    def get_counts(self, broker_id: int) -> dict[str, int]:
        """Compute customized stocks, instruments, and sessions counts."""
        with self._db.connection(query_only=True) as conn:
            stocks_row = conn.execute(
                "SELECT COUNT(*) FROM datamgr_broker_stock WHERE broker_id = ?",
                (broker_id,),
            ).fetchone()
            inst_row = conn.execute(
                "SELECT COUNT(*) FROM datamgr_instruments WHERE broker_id = ?",
                (broker_id,),
            ).fetchone()
            sess_cols = {
                col[1]
                for col in conn.execute(
                    "PRAGMA table_info(datamgr_sessions)"
                ).fetchall()
            }
            sess_count = 0
            if "broker_id" in sess_cols:
                sess_row = conn.execute(
                    "SELECT COUNT(*) FROM datamgr_sessions WHERE broker_id = ?",
                    (broker_id,),
                ).fetchone()
                sess_count = int(sess_row[0]) if sess_row else 0

        return {
            "customized_stocks": int(stocks_row[0]) if stocks_row else 0,
            "customized_instruments": int(inst_row[0]) if inst_row else 0,
            "customized_sessions": sess_count,
        }

    def ensure_defaults(self) -> None:
        """Seed the 11 authoritative StrategyQuant X default system broker profiles."""
        system_defaults: list[dict[str, Any]] = [
            {
                "id": 1,
                "name": "[[XTB]]",
                "is_system": 1,
                "description": "XTB broker",
                "stockpicker_use": 1,
                "mt_use": 0,
                "server_timezone": "UTC",
                "postfix": "",
            },
            {
                "id": 2,
                "name": "[[RoboForex]]",
                "is_system": 1,
                "description": "RoboForex",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EET",
                "postfix": "_roboforex",
            },
            {
                "id": 3,
                "name": "[[Dukascopy]]",
                "is_system": 1,
                "description": "Dukascopy",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_dukascopy",
            },
            {
                "id": 4,
                "name": "[[Darwinex]]",
                "is_system": 1,
                "description": "Darwinex CFDs",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_darwinex",
            },
            {
                "id": 5,
                "name": "[[ICMarkets]]",
                "is_system": 1,
                "description": "ICMarkets",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_icmarkets",
            },
            {
                "id": 6,
                "name": "[[Pepperstone]]",
                "is_system": 1,
                "description": "Pepperstone",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_pepperstone",
            },
            {
                "id": 7,
                "name": "[[OANDA]]",
                "is_system": 1,
                "description": "OANDA",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_oanda",
            },
            {
                "id": 8,
                "name": "[[FTMO]]",
                "is_system": 1,
                "description": "FTMO",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_ftmo",
            },
            {
                "id": 9,
                "name": "[[The5ers]]",
                "is_system": 1,
                "description": "The5ers",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "Asia/Jerusalem",
                "postfix": "_the5ers",
            },
            {
                "id": 10,
                "name": "[[Monevis]]",
                "is_system": 1,
                "description": "Monevis",
                "stockpicker_use": 0,
                "mt_use": 1,
                "server_timezone": "EETUS",
                "postfix": "_monevis",
            },
            {
                "id": 11,
                "name": "[[Darwinex Zero]]",
                "is_system": 1,
                "description": "Darwinex Zero",
                "stockpicker_use": 1,
                "mt_use": 0,
                "server_timezone": "UTC",
                "postfix": "",
            },
        ]
        with self._db.transaction() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='datamgr_broker'"
            ).fetchone()
            if not exists:
                return
            now_str = datetime.now(UTC).isoformat()
            for item in system_defaults:
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
