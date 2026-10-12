"""Host background jobs and worker leases storage repository.

Description:
    Provides transactional storage operations for `host_jobs` and `host_leases`,
    managing job state transitions, progress tracking, process budgets, worker
    lease reservations, expiry pruning, and date normalization.

Purpose:
    FEAT-HOST-PERSISTENCE: Host job lifecycle and lease reservation CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-JOBS: Job row reads/writes and conditional field updates.
      Associated: `JobStore.get_job()`, `JobStore.upsert_job()`,
        `JobStore.update_statuses()`
      Logging: DEBUG reads; INFO writes and affected-row count.
    - FR-HOST-PERSISTENCE-LEASES: Atomic reservation row predicates and CRUD.
      Associated: `LeaseStore.acquire()`, `LeaseStore.renew()`,
        `LeaseStore.release()`, `LeaseStore.prune_expired()`
      Logging: DEBUG conditional results/reads; INFO deleted-row count.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager
    from app.host.persistence.stores.jobs import JobStore, LeaseStore

    db = DatabaseManager(":memory:")
    db.initialize()
    leases = LeaseStore(db)
    jobs = JobStore(db)
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.engine import (
    _BUSY_TIMEOUT_SECONDS,
    DatabaseManager,
    canonical_json,
)

logger = get_logger(__name__)


class LeaseStore:
    """Store reservations with atomic holder/expiry predicates supplied by callers."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get(self, lease_key: str) -> dict[str, Any] | None:
        """Read one reservation row without interpreting its lifecycle."""
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM host_leases WHERE lease_key = ?", (lease_key,)
            ).fetchone()
        logger.debug("Lease row read", extra={"fr_id": "FR-HOST-PERSISTENCE-LEASES"})
        return self._row_to_record(row) if row is not None else None

    def acquire(self, record: Mapping[str, Any], observed_at_utc: str) -> bool:
        """Conditionally insert/replace a row by its holder and expiration."""
        metadata = canonical_json(record["metadata"])
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO host_leases
                (lease_key, holder_id, scope, acquired_at_utc, expires_at_utc, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lease_key) DO UPDATE SET
                    holder_id = excluded.holder_id, scope = excluded.scope,
                    acquired_at_utc = excluded.acquired_at_utc,
                    expires_at_utc = excluded.expires_at_utc,
                    metadata = excluded.metadata
                WHERE host_leases.holder_id = excluded.holder_id
                   OR host_leases.expires_at_utc < ?""",
                (
                    record["lease_key"],
                    record["holder_id"],
                    record["scope"],
                    record["acquired_at_utc"],
                    record["expires_at_utc"],
                    metadata,
                    observed_at_utc,
                ),
            )
            changed = cursor.rowcount > 0
        logger.debug(
            "Conditional lease write completed",
            extra={"changed": changed, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return changed

    def renew(
        self,
        lease_key: str,
        holder_id: str,
        observed_at_utc: str,
        expires_at_utc: str,
    ) -> dict[str, Any] | None:
        """Update expiry and read the resulting row within one transaction."""
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE host_leases SET expires_at_utc = ? "
                "WHERE lease_key = ? AND holder_id = ? AND expires_at_utc >= ?",
                (expires_at_utc, lease_key, holder_id, observed_at_utc),
            )
            row = (
                conn.execute(
                    "SELECT * FROM host_leases WHERE lease_key = ?", (lease_key,)
                ).fetchone()
                if cursor.rowcount
                else None
            )
            record = self._row_to_record(row) if row is not None else None
        logger.debug(
            "Conditional lease renewal completed",
            extra={"changed": row is not None, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return record

    def release(self, lease_key: str, holder_id: str) -> bool:
        """Delete a row only when its key and holder match."""
        with self._db.transaction() as conn:
            changed = (
                conn.execute(
                    "DELETE FROM host_leases WHERE lease_key = ? AND holder_id = ?",
                    (lease_key, holder_id),
                ).rowcount
                > 0
            )
        logger.debug(
            "Conditional lease delete completed",
            extra={"changed": changed, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return changed

    def list_active(self, observed_at_utc: str) -> list[dict[str, Any]]:
        """Read rows after a caller-supplied expiration cutoff."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT * FROM host_leases WHERE expires_at_utc > ? "
                "ORDER BY expires_at_utc",
                (observed_at_utc,),
            ).fetchall()
        logger.debug("Lease rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-LEASES"})
        return [self._row_to_record(row) for row in rows]

    def prune_expired(self, observed_at_utc: str) -> int:
        """Delete rows at or before a caller-supplied expiration cutoff."""
        with self._db.transaction() as conn:
            count = conn.execute(
                "DELETE FROM host_leases WHERE expires_at_utc <= ?", (observed_at_utc,)
            ).rowcount
        logger.info(
            "Lease rows deleted",
            extra={"count": count, "fr_id": "FR-HOST-PERSISTENCE-LEASES"},
        )
        return count

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
        """Decode stored JSON without interpreting worker policy."""
        record = dict(row)
        record["metadata"] = json.loads(record["metadata"])
        return record


class JobStore:
    """Persist explicit job fields without interpreting job lifecycle or budgets."""

    _columns = (
        "job_id",
        "owner",
        "kind",
        "status",
        "progress",
        "accepted",
        "rejected",
        "message",
        "attempt_id",
        "max_retries",
        "retry_count",
        "dedup_key",
        "parent_job_id",
        "child_job_ids_json",
        "budget_json",
        "submitted_at_utc",
        "started_at_utc",
        "finished_at_utc",
        "error_message",
        "error_location",
    )

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = _BUSY_TIMEOUT_SECONDS,
        db: DatabaseManager | None = None,
    ) -> None:
        self._db = db or DatabaseManager(db_path, busy_timeout=busy_timeout)

    @property
    def db_path(self) -> Path | str:
        """Return the configured database location."""
        return ":memory:" if self._db.is_memory else self._db.database_path

    @property
    def db(self) -> DatabaseManager:
        """Return the manager used by this store."""
        return self._db

    def initialize(self) -> None:
        """Ensure the storage schema exists."""
        self._db.initialize()

    def upsert_job(self, record: Mapping[str, Any]) -> None:
        """Write one complete job storage record."""
        self.initialize()
        placeholders = ", ".join("?" for _ in self._columns)
        sql = (
            f"INSERT OR REPLACE INTO host_jobs ({', '.join(self._columns)}) "  # noqa: S608 - fixed columns/placeholders only
            f"VALUES ({placeholders})"
        )
        with self._db.transaction() as conn:
            conn.execute(sql, tuple(record[column] for column in self._columns))
        logger.info("Job row saved", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Read one job storage record by ID."""
        self.initialize()
        with self._db.connection(query_only=True) as conn:
            row = conn.execute(
                "SELECT * FROM host_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        logger.debug("Job row read", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})
        return dict(row) if row is not None else None

    def list_jobs(
        self,
        owner: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Read recent job rows with optional field filters."""
        self.initialize()
        filters = []
        parameters: list[Any] = []
        for column, value in (("owner", owner), ("status", status)):
            if value is not None:
                filters.append(f"{column} = ?")
                parameters.append(value)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        sql = f"SELECT * FROM host_jobs{where} ORDER BY submitted_at_utc DESC LIMIT ?"  # noqa: S608
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(sql, (*parameters, limit)).fetchall()
        logger.debug("Job rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-JOBS"})
        return [dict(row) for row in rows]

    def update_statuses(
        self,
        matching_statuses: tuple[str, ...],
        *,
        status: str,
        finished_at_utc: str,
        error_message: str,
    ) -> int:
        """Atomically update fields on rows matching caller-supplied statuses."""
        self.initialize()
        if not matching_statuses:
            return 0
        placeholders = ", ".join("?" for _ in matching_statuses)
        sql = (
            "UPDATE host_jobs SET status = ?, finished_at_utc = ?, error_message = ? "  # noqa: S608 - fixed columns/placeholders only
            f"WHERE status IN ({placeholders})"
        )
        with self._db.transaction() as conn:
            count = conn.execute(
                sql, (status, finished_at_utc, error_message, *matching_statuses)
            ).rowcount
        logger.info(
            "Job rows updated",
            extra={"count": count, "fr_id": "FR-HOST-PERSISTENCE-JOBS"},
        )
        return count
