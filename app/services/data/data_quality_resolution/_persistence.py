"""SQLite persistence and publication locking for Data Quality Resolution."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PUBLICATION_LOCKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS publication_locks (
    series_key TEXT PRIMARY KEY,
    current_version INTEGER NOT NULL,
    lock_owner TEXT,
    acquired_at TEXT,
    lock_id TEXT
);
"""

QUALITY_FINDINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS quality_findings (
    finding_id TEXT PRIMARY KEY,
    data_version_id TEXT NOT NULL,
    rule_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    point TEXT,
    range_from TEXT,
    range_to TEXT,
    observed TEXT,
    expected TEXT,
    resolution_state TEXT NOT NULL,
    derived_version_id TEXT
);
"""

QUALITY_DECISIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS quality_decisions (
    decision_id TEXT PRIMARY KEY,
    finding_ids TEXT NOT NULL,
    action TEXT NOT NULL,
    policy_version INTEGER NOT NULL,
    derived_version_id TEXT,
    decided_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class PublicationLockReceipt:
    """Receipt for an exclusive publication lock."""

    series_key: str
    acquired_version: int
    lock_id: str
    acquired_at: str


def init_database(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Initialize SQLite database schema for data quality resolution.

    Args:
        db_path: Optional file path for SQLite database, or None for in-memory.

    Returns:
        Configured SQLite connection.
    """
    conn = (
        sqlite3.connect(str(db_path), check_same_thread=False)
        if db_path
        else sqlite3.connect(":memory:", check_same_thread=False)
    )
    with conn:
        conn.execute(PUBLICATION_LOCKS_TABLE_SQL)
        conn.execute(QUALITY_FINDINGS_TABLE_SQL)
        conn.execute(QUALITY_DECISIONS_TABLE_SQL)
    return conn


def data_lock_data_publication(
    db_conn: sqlite3.Connection,
    series_key: str,
    expected_version: int,
    lock_owner: str,
) -> tuple[bool, PublicationLockReceipt | None, str | None]:
    """Acquire an exclusive publication lock with optimistic version checking.

    Args:
        db_conn: SQLite database connection.
        series_key: Logical series identifier.
        expected_version: Expected current version for optimistic concurrency control.
        lock_owner: Identifier of the acquiring process/operation.

    Returns:
        Tuple of (success, lock_receipt, error_message).
    """
    now = datetime.now(tz=UTC).isoformat()
    lock_id = str(uuid.uuid7())

    with db_conn:
        cur = db_conn.cursor()
        cur.execute(
            """
            SELECT current_version, lock_owner FROM publication_locks
            WHERE series_key = ?
            """,
            (series_key,),
        )
        row = cur.fetchone()

        if row is None:
            if expected_version != 0:
                msg = (
                    f"Series {series_key} does not exist; "
                    f"expected version {expected_version}"
                )
                return False, None, msg
            cur.execute(
                """
                INSERT INTO publication_locks (
                    series_key, current_version, lock_owner, acquired_at, lock_id
                )
                VALUES (?, 1, ?, ?, ?)
                """,
                (series_key, lock_owner, now, lock_id),
            )
            return (
                True,
                PublicationLockReceipt(
                    series_key=series_key,
                    acquired_version=1,
                    lock_id=lock_id,
                    acquired_at=now,
                ),
                None,
            )

        current_ver, existing_owner = row[0], row[1]
        if current_ver != expected_version:
            msg = (
                f"Optimistic version conflict for series {series_key}: "
                f"expected {expected_version}, current {current_ver}"
            )
            return False, None, msg

        if existing_owner is not None and existing_owner != lock_owner:
            return False, None, f"Series {series_key} is locked by {existing_owner}"

        next_ver = current_ver + 1
        cur.execute(
            """
            UPDATE publication_locks
            SET current_version = ?, lock_owner = ?, acquired_at = ?, lock_id = ?
            WHERE series_key = ? AND current_version = ?
            """,
            (next_ver, lock_owner, now, lock_id, series_key, current_ver),
        )
        if cur.rowcount == 0:
            return False, None, "Concurrent modification conflict on lock acquisition"

        return (
            True,
            PublicationLockReceipt(
                series_key=series_key,
                acquired_version=next_ver,
                lock_id=lock_id,
                acquired_at=now,
            ),
            None,
        )
