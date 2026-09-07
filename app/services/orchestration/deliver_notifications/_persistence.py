"""Feature-local SQLite operations for notification receipts."""

from __future__ import annotations

import sqlite3
from typing import Literal, cast

from app.contracts.orchestration.models import NotificationReceipt

type _NotificationStatus = Literal[
    "PENDING",
    "DELIVERED",
    "FAILED",
    "UNKNOWN",
    "SUPPRESSED_RATE_LIMIT",
    "DISABLED",
]


class NotificationStore:
    """Transactional receipt and rate-limit store."""

    def __init__(self, database_path: str) -> None:
        """Open the configured SQLite store.

        Args:
            database_path: SQLite database filename or ``:memory:``.
        """
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS notification_receipts (
            delivery_id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            status TEXT NOT NULL,
            rendered_hash TEXT NOT NULL,
            sent_at TEXT,
            error TEXT,
            created_at TEXT NOT NULL
            )"""
        )
        self._connection.commit()

    def get(self, delivery_id: str) -> NotificationReceipt | None:
        """Return the existing receipt for an idempotency identity.

        Args:
            delivery_id: Logical delivery identity.

        Returns:
            Existing receipt, or None.
        """
        row = self._connection.execute(
            """SELECT receipt_id, delivery_id, channel_id, status, rendered_hash,
            sent_at, error FROM notification_receipts WHERE delivery_id = ?""",
            (delivery_id,),
        ).fetchone()
        return None if row is None else self._receipt(row)

    def save(self, receipt: NotificationReceipt, created_at: str) -> None:
        """Insert or replace one durable receipt.

        Args:
            receipt: Receipt to persist.
            created_at: Stable timestamp used for rate accounting.
        """
        with self._connection:
            self._connection.execute(
                """INSERT OR REPLACE INTO notification_receipts
                (delivery_id, receipt_id, channel_id, status, rendered_hash,
                 sent_at, error, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    receipt.delivery_id,
                    receipt.receipt_id,
                    receipt.channel_id,
                    receipt.status,
                    receipt.rendered_hash,
                    receipt.sent_at,
                    receipt.error,
                    created_at,
                ),
            )

    def count_attempts(self, channel_id: str, since: str) -> int:
        """Count delivery attempts in a channel window.

        Args:
            channel_id: Channel identity.
            since: Inclusive UTC lower bound.

        Returns:
            Number of external delivery attempts.
        """
        row = self._connection.execute(
            """SELECT COUNT(*) FROM notification_receipts
            WHERE channel_id = ? AND created_at >= ?
            AND status IN ('PENDING', 'DELIVERED', 'FAILED', 'UNKNOWN')""",
            (channel_id, since),
        ).fetchone()
        return int(row[0]) if row is not None else 0

    @staticmethod
    def _receipt(row: tuple[object, ...]) -> NotificationReceipt:
        """Convert one row into a public receipt.

        Args:
            row: Selected receipt row.

        Returns:
            Parsed notification receipt.
        """
        return NotificationReceipt(
            receipt_id=str(row[0]),
            delivery_id=str(row[1]),
            channel_id=str(row[2]),
            status=cast("_NotificationStatus", str(row[3])),
            rendered_hash=str(row[4]),
            sent_at=None if row[5] is None else str(row[5]),
            error=None if row[6] is None else str(row[6]),
        )

    def close(self) -> None:
        """Close the database handle."""
        self._connection.close()
