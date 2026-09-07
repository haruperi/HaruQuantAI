"""Feature-local SQLite operations for durable job state."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from app.contracts.orchestration.jobs import JobRecord

if TYPE_CHECKING:
    from app.contracts.common.models import JobState


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class JobStore:
    """Transactional store for jobs and progress sequence numbers."""

    def __init__(self, database_path: str) -> None:
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            idempotency_key TEXT UNIQUE NOT NULL,
            state TEXT NOT NULL,
            version INTEGER NOT NULL,
            progress TEXT NOT NULL,
            message TEXT NOT NULL,
            progress_sequence INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
            )"""
        )
        self._connection.commit()

    def submit(self, job_id: str, idempotency_key: str) -> JobRecord:
        """Insert a job or return the existing idempotent record.

        Returns:
            Accepted job record.

        Raises:
            RuntimeError: If SQLite does not return the accepted record.
        """
        now = _now()
        with self._connection:
            self._connection.execute(
                """INSERT OR IGNORE INTO jobs
                VALUES (?, ?, 'QUEUED', 1, '0', '', 0, ?, ?)""",
                (job_id, idempotency_key, now, now),
            )
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if row is None:
            raise RuntimeError("job insertion did not produce a record")
        return self._record(row)

    def get(self, job_id: str) -> JobRecord:
        """Return one job or raise a stable lookup error.

        Raises:
            KeyError: If the job does not exist.
        """
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._record(row)

    def update(
        self,
        job_id: str,
        *,
        expected_version: int,
        state: str | None = None,
        progress: str | None = None,
        message: str | None = None,
    ) -> tuple[JobRecord, int]:
        """Apply one optimistic update.

        Returns:
            Updated record and its progress sequence.

        Raises:
            KeyError: If the job does not exist.
            ValueError: If expected_version no longer matches.
        """
        current = self.get(job_id)
        now = _now()
        next_state = state or current.state
        next_progress = progress if progress is not None else current.progress
        next_message = message if message is not None else current.message
        increment_sequence = 1 if progress is not None else 0
        with self._connection:
            cursor = self._connection.execute(
                """UPDATE jobs SET state = ?, version = version + 1, progress = ?,
                message = ?, progress_sequence = progress_sequence + ?, updated_at = ?
                WHERE job_id = ? AND version = ?""",
                (
                    next_state,
                    next_progress,
                    next_message,
                    increment_sequence,
                    now,
                    job_id,
                    expected_version,
                ),
            )
        if cursor.rowcount != 1:
            raise ValueError("JOB_VERSION_CONFLICT")
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._record(row), int(row[6])

    def close(self) -> None:
        """Close the database handle."""
        self._connection.close()

    @staticmethod
    def _record(row: tuple[object, ...]) -> JobRecord:
        """Convert one database row to its public record.

        Returns:
            Parsed job record.
        """
        return JobRecord(
            job_id=str(row[0]),
            idempotency_key=str(row[1]),
            state=cast("JobState", str(row[2])),
            version=int(str(row[3])),
            progress=str(row[4]),
            message=str(row[5]),
            created_at=str(row[7]),
            updated_at=str(row[8]),
        )
