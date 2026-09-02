"""Internal SQLite persistence for Service-Level Broker Resolver feature."""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("data/database/haruquantai.db")

BROKER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS broker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    desc VARCHAR(250),
    active BOOLEAN NOT NULL,
    timezone VARCHAR(100)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_platform ON broker(platform);
CREATE INDEX IF NOT EXISTS idx_broker_active ON broker(active);
"""

DEFAULT_FALLBACK_BROKER: dict[str, Any] = {
    "id": 1,
    "name": "MetaTrader 5",
    "platform": "mt5",
    "desc": "MetaTrader 5 Direct Terminal Gateway",
    "active": True,
    "timezone": "UTC+3",
}

DEFAULT_BROKER_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "name": "MetaTrader 5",
        "platform": "mt5",
        "desc": "MetaTrader 5 Direct Terminal Gateway",
        "active": 1,
        "timezone": "UTC+3",
    },
    {
        "name": "cTrader",
        "platform": "ctrader",
        "desc": "Spotware cTrader Open API Gateway",
        "active": 0,
        "timezone": "UTC",
    },
    {
        "name": "Binance",
        "platform": "binance",
        "desc": "Binance Spot & Futures Gateway",
        "active": 0,
        "timezone": "UTC",
    },
    {
        "name": "Dukascopy",
        "platform": "dukascopy",
        "desc": "Dukascopy Historical Feed Gateway",
        "active": 0,
        "timezone": "UTC",
    },
    {
        "name": "Yahoo",
        "platform": "yahoo",
        "desc": "Yahoo Finance Public Bar Gateway",
        "active": 0,
        "timezone": "UTC",
    },
)


def _resolve_db_path(db_path: Path | str | None = None) -> Path:
    """Resolve target database path to an absolute path.

    Args:
        db_path: Optional custom database path.

    Returns:
        Resolved absolute Path.
    """
    target = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    return target.resolve()


def init_broker_table(db_path: Path | str | None = None) -> None:
    """Ensure the broker table and indexes exist in the target database.

    Args:
        db_path: Optional custom database path.
    """
    path = _resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        conn.executescript(BROKER_TABLE_SQL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM broker;")
        if cursor.fetchone()[0] == 0:
            for brk in DEFAULT_BROKER_SEEDS:
                cursor.execute(
                    """
                    INSERT INTO broker (name, platform, desc, active, timezone)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        brk["name"],
                        brk["platform"],
                        brk["desc"],
                        brk["active"],
                        brk["timezone"],
                    ),
                )
        else:
            # Deduplicate any duplicate platform entries if needed
            cursor.execute(
                """
                DELETE FROM broker WHERE id NOT IN (
                    SELECT MIN(id) FROM broker GROUP BY platform
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


def get_active_broker_record(db_path: Path | str | None = None) -> dict[str, Any]:
    """Retrieve active broker configuration dictionary from database or runtime settings.

    Args:
        db_path: Optional custom database path.

    Returns:
        Dictionary with id, name, platform, desc, active, and timezone.
    """
    path = _resolve_db_path(db_path)
    init_broker_table(path)

    configured_platform: str | None = None
    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        # 1. Check if settings table exists and has a configured runtime_broker
        try:
            cursor.execute(
                "SELECT value FROM settings WHERE key = 'broker.runtime_broker' LIMIT 1;"
            )
            row = cursor.fetchone()
            if row is not None and row[0]:
                configured_platform = str(row[0]).strip().lower()
        except sqlite3.OperationalError:
            configured_platform = None

        # 2. If runtime setting specifies a platform, attempt exact match
        if configured_platform:
            cursor.execute(
                """
                SELECT id, name, platform, desc, active, timezone
                FROM broker
                WHERE LOWER(platform) = ? OR LOWER(name) = ?
                LIMIT 1;
                """,
                (configured_platform, configured_platform),
            )
            row = cursor.fetchone()
            if row is not None:
                return {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "platform": str(row[2]) if row[2] is not None else "",
                    "desc": str(row[3]) if row[3] is not None else "",
                    "active": bool(row[4]),
                    "timezone": str(row[5]) if row[5] is not None else "UTC",
                }

        # 3. Otherwise find the first broker with active = 1
        cursor.execute(
            """
            SELECT id, name, platform, desc, active, timezone
            FROM broker
            WHERE active = 1
            ORDER BY id ASC
            LIMIT 1;
            """
        )
        row = cursor.fetchone()
        if row is not None:
            return {
                "id": int(row[0]),
                "name": str(row[1]),
                "platform": str(row[2]) if row[2] is not None else "",
                "desc": str(row[3]) if row[3] is not None else "",
                "active": bool(row[4]),
                "timezone": str(row[5]) if row[5] is not None else "UTC",
            }

        # 4. Fallback to any first broker in table
        cursor.execute(
            """
            SELECT id, name, platform, desc, active, timezone
            FROM broker
            ORDER BY id ASC
            LIMIT 1;
            """
        )
        row = cursor.fetchone()
        if row is not None:
            return {
                "id": int(row[0]),
                "name": str(row[1]),
                "platform": str(row[2]) if row[2] is not None else "",
                "desc": str(row[3]) if row[3] is not None else "",
                "active": bool(row[4]),
                "timezone": str(row[5]) if row[5] is not None else "UTC",
            }

        return dict(DEFAULT_FALLBACK_BROKER)
    finally:
        conn.close()


def list_broker_records(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """List all registered broker records in the database.

    Args:
        db_path: Optional custom database path.

    Returns:
        List of broker configuration dictionaries.
    """
    path = _resolve_db_path(db_path)
    init_broker_table(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, platform, desc, active, timezone
            FROM broker
            ORDER BY id ASC;
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id": int(r[0]),
                "name": str(r[1]),
                "platform": str(r[2]) if r[2] is not None else "",
                "desc": str(r[3]) if r[3] is not None else "",
                "active": bool(r[4]),
                "timezone": str(r[5]) if r[5] is not None else "UTC",
            }
            for r in rows
        ]
    finally:
        conn.close()


def set_active_broker_record(
    platform_or_name: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Set the active broker in the database and synchronize runtime setting.

    Args:
        platform_or_name: Target broker platform identifier (e.g. 'mt5') or name.
        db_path: Optional custom database path.

    Returns:
        Updated broker module configuration dictionary.

    Raises:
        ValueError: If the specified broker does not exist.
    """
    path = _resolve_db_path(db_path)
    init_broker_table(path)

    target_key = platform_or_name.strip().lower()
    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")

        cursor.execute(
            """
            SELECT id, name, platform, desc, timezone
            FROM broker
            WHERE LOWER(platform) = ? OR LOWER(name) = ?
            LIMIT 1;
            """,
            (target_key, target_key),
        )
        row = cursor.fetchone()
        if row is None:
            msg = f"Broker '{platform_or_name}' not found in database."
            raise ValueError(msg)

        broker_id = int(row[0])
        name = str(row[1])
        platform = str(row[2]) if row[2] is not None else ""
        desc = str(row[3]) if row[3] is not None else ""
        timezone = str(row[4]) if row[4] is not None else "UTC"

        # Deactivate all other brokers and activate the target
        cursor.execute("UPDATE broker SET active = 0 WHERE id != ?;", (broker_id,))
        cursor.execute("UPDATE broker SET active = 1 WHERE id = ?;", (broker_id,))

        # Synchronize settings table if present
        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute(
                """
                UPDATE settings SET value = ?
                WHERE key = 'broker.runtime_broker';
                """,
                (platform,),
            )

        conn.commit()

        return {
            "id": broker_id,
            "name": name,
            "platform": platform,
            "desc": desc,
            "active": True,
            "timezone": timezone,
        }
    finally:
        conn.close()


def register_broker_record(
    name: str,
    platform: str | None = None,
    desc: str | None = None,
    active: bool = False,
    timezone: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Register or insert a new broker record into the broker table.

    Args:
        name: Name of the broker.
        platform: Platform code (e.g. 'mt5', 'ctrader').
        desc: Human-readable description.
        active: Whether this broker is active.
        timezone: Operating timezone.
        db_path: Optional custom database path.

    Returns:
        Created broker dictionary with ID.
    """
    path = _resolve_db_path(db_path)
    init_broker_table(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        if active:
            cursor.execute("UPDATE broker SET active = 0;")

        cursor.execute(
            """
            INSERT INTO broker (name, platform, desc, active, timezone)
            VALUES (?, ?, ?, ?, ?);
            """,
            (name, platform, desc, 1 if active else 0, timezone or "UTC"),
        )
        new_id = cursor.lastrowid

        if active and platform:
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute(
                    """
                    UPDATE settings SET value = ?
                    WHERE key = 'broker.runtime_broker';
                    """,
                    (platform,),
                )

        conn.commit()

        return {
            "id": new_id,
            "name": name,
            "platform": platform or "",
            "desc": desc or "",
            "active": active,
            "timezone": timezone or "UTC",
        }
    finally:
        conn.close()
