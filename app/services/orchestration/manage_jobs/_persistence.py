"""Feature-local SQLite operations for durable job and attempt state."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
import uuid

from app.contracts.orchestration.jobs import (
    ControlIntent,
    DomainOutcome,
    EffectReconciliation,
    JobAttempt,
    JobRecord,
    JobSemanticRecord,
    JobSubmission,
)

if TYPE_CHECKING:
    from app.contracts.common.models import JobState


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class JobStore:
    """Transactional store for jobs, semantic projections, attempts, and effects."""

    def __init__(self, database_path: str) -> None:
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE NOT NULL,
                state TEXT NOT NULL,
                version INTEGER NOT NULL,
                progress TEXT NOT NULL,
                message TEXT NOT NULL,
                progress_sequence INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_semantics (
                job_id TEXT PRIMARY KEY,
                request_fingerprint TEXT NOT NULL,
                input_ref TEXT NOT NULL,
                owner_operation TEXT NOT NULL,
                parent_job_id TEXT,
                root_job_id TEXT NOT NULL,
                depth INTEGER NOT NULL,
                max_depth INTEGER NOT NULL,
                supports_pause INTEGER NOT NULL,
                domain_outcome TEXT NOT NULL,
                desired_control TEXT NOT NULL,
                acknowledged_control TEXT NOT NULL,
                waiting_for_human INTEGER NOT NULL,
                enqueue_intent INTEGER NOT NULL,
                current_attempt_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_attempts (
                attempt_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                attempt_no INTEGER NOT NULL,
                fence INTEGER NOT NULL,
                predecessor_attempt_id TEXT,
                UNIQUE(job_id, attempt_no)
            );
            CREATE TABLE IF NOT EXISTS job_effects (
                idempotency_key TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                receipt_ref TEXT
            );
            """
        )
        self._connection.commit()

    def submit(self, job_id: str, idempotency_key: str) -> JobRecord:
        """Insert a minimal legacy job or return the existing record."""
        now = _now()
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO jobs VALUES (?, ?, 'QUEUED', 1, '0', '', 0, ?, ?)",
                (job_id, idempotency_key, now, now),
            )
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if row is None:
            raise RuntimeError("job insertion did not produce a record")
        return self._record(row)

    def submit_job(self, submission: JobSubmission) -> JobSemanticRecord:
        """Atomically persist job identity, attempt 1, and enqueue intent."""
        existing = self._connection.execute(
            "SELECT job_id FROM jobs WHERE idempotency_key = ?",
            (submission.idempotency_key,),
        ).fetchone()
        if existing is not None:
            record = self.get_semantics(str(existing[0]))
            if record.request_fingerprint != submission.request_fingerprint:
                raise ValueError("JOB_IDEMPOTENCY_CONFLICT")
            return record
        parent_depth = -1
        root_job_id = submission.root_job_id or submission.job_id
        if submission.parent_job_id is not None:
            parent = self.get_semantics(submission.parent_job_id)
            parent_depth = parent.depth
            root_job_id = parent.root_job_id
            if submission.job_id in {parent.job_id, parent.root_job_id}:
                raise ValueError("JOB_ANCESTRY_CYCLE")
        depth = parent_depth + 1
        if submission.max_depth < 0 or depth > submission.max_depth:
            raise ValueError("JOB_ANCESTRY_LIMIT")
        attempt_id = f"attempt-{uuid.uuid4().hex}"
        now = _now()
        with self._connection:
            self._connection.execute(
                "INSERT INTO jobs VALUES (?, ?, 'QUEUED', 1, '0', '', 0, ?, ?)",
                (submission.job_id, submission.idempotency_key, now, now),
            )
            self._connection.execute(
                "INSERT INTO job_attempts VALUES (?, ?, 1, 1, NULL)",
                (attempt_id, submission.job_id),
            )
            self._connection.execute(
                "INSERT INTO job_semantics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)",
                (
                    submission.job_id,
                    submission.request_fingerprint,
                    submission.input_ref,
                    submission.owner_operation,
                    submission.parent_job_id,
                    root_job_id,
                    depth,
                    submission.max_depth,
                    int(submission.supports_pause),
                    DomainOutcome.UNKNOWN.value,
                    ControlIntent.NONE.value,
                    ControlIntent.NONE.value,
                    attempt_id,
                ),
            )
        return self.get_semantics(submission.job_id)

    def get(self, job_id: str) -> JobRecord:
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._record(row)

    def get_semantics(self, job_id: str) -> JobSemanticRecord:
        row = self._connection.execute(
            "SELECT * FROM job_semantics WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise KeyError(job_id)
        attempt_row = self._connection.execute(
            "SELECT * FROM job_attempts WHERE attempt_id = ?", (row[14],)
        ).fetchone()
        if attempt_row is None:
            raise RuntimeError("current job attempt is missing")
        attempt = JobAttempt(
            str(attempt_row[0]), str(attempt_row[1]), int(attempt_row[2]),
            int(attempt_row[3]), None if attempt_row[4] is None else str(attempt_row[4]),
        )
        return JobSemanticRecord(
            job_id=str(row[0]), request_fingerprint=str(row[1]), input_ref=str(row[2]),
            owner_operation=str(row[3]), parent_job_id=None if row[4] is None else str(row[4]),
            root_job_id=str(row[5]), depth=int(row[6]), supports_pause=bool(row[8]),
            domain_outcome=DomainOutcome(str(row[9])), desired_control=ControlIntent(str(row[10])),
            acknowledged_control=ControlIntent(str(row[11]),), waiting_for_human=bool(row[12]),
            enqueue_intent=bool(row[13]), current_attempt=attempt,
        )

    def update_semantics(
        self,
        job_id: str,
        *,
        domain_outcome: DomainOutcome | None = None,
        desired_control: ControlIntent | None = None,
        acknowledged_control: ControlIntent | None = None,
        waiting_for_human: bool | None = None,
    ) -> JobSemanticRecord:
        current = self.get_semantics(job_id)
        with self._connection:
            self._connection.execute(
                "UPDATE job_semantics SET domain_outcome = ?, desired_control = ?, acknowledged_control = ?, waiting_for_human = ? WHERE job_id = ?",
                (
                    (domain_outcome or current.domain_outcome).value,
                    (desired_control or current.desired_control).value,
                    (acknowledged_control or current.acknowledged_control).value,
                    int(current.waiting_for_human if waiting_for_human is None else waiting_for_human),
                    job_id,
                ),
            )
        return self.get_semantics(job_id)

    def retry(self, job_id: str) -> JobSemanticRecord:
        job = self.get(job_id)
        if job.state not in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise ValueError("JOB_RETRY_REQUIRES_TERMINAL")
        current = self.get_semantics(job_id)
        next_no = current.current_attempt.attempt_no + 1
        attempt_id = f"attempt-{uuid.uuid4().hex}"
        with self._connection:
            self._connection.execute(
                "INSERT INTO job_attempts VALUES (?, ?, ?, ?, ?)",
                (attempt_id, job_id, next_no, current.current_attempt.fence + 1, current.current_attempt.attempt_id),
            )
            self._connection.execute(
                "UPDATE job_semantics SET current_attempt_id = ?, domain_outcome = ?, desired_control = ?, acknowledged_control = ?, waiting_for_human = 0, enqueue_intent = 1 WHERE job_id = ?",
                (attempt_id, DomainOutcome.UNKNOWN.value, ControlIntent.NONE.value, ControlIntent.NONE.value, job_id),
            )
            self._connection.execute(
                "UPDATE jobs SET state='QUEUED', version=version+1, progress='0', message='', updated_at=? WHERE job_id=?",
                (_now(), job_id),
            )
        return self.get_semantics(job_id)

    def reconcile_effect(self, item: EffectReconciliation) -> EffectReconciliation:
        row = self._connection.execute(
            "SELECT status, receipt_ref FROM job_effects WHERE idempotency_key = ?",
            (item.idempotency_key,),
        ).fetchone()
        if row is not None:
            existing = EffectReconciliation(item.idempotency_key, str(row[0]), None if row[1] is None else str(row[1]))
            if existing != item:
                raise ValueError("JOB_EFFECT_RECONCILIATION_CONFLICT")
            return existing
        with self._connection:
            self._connection.execute(
                "INSERT INTO job_effects VALUES (?, ?, ?)",
                (item.idempotency_key, item.status, item.receipt_ref),
            )
        return item

    def update(
        self,
        job_id: str,
        *,
        expected_version: int,
        state: str | None = None,
        progress: str | None = None,
        message: str | None = None,
    ) -> tuple[JobRecord, int]:
        current = self.get(job_id)
        now = _now()
        next_state = state or current.state
        next_progress = progress if progress is not None else current.progress
        next_message = message if message is not None else current.message
        increment_sequence = 1 if progress is not None else 0
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE jobs SET state = ?, version = version + 1, progress = ?, message = ?, progress_sequence = progress_sequence + ?, updated_at = ? WHERE job_id = ? AND version = ?",
                (next_state, next_progress, next_message, increment_sequence, now, job_id, expected_version),
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
        self._connection.close()

    @staticmethod
    def _record(row: tuple[object, ...]) -> JobRecord:
        return JobRecord(
            job_id=str(row[0]), idempotency_key=str(row[1]), state=cast("JobState", str(row[2])),
            version=int(str(row[3])), progress=str(row[4]), message=str(row[5]),
            created_at=str(row[7]), updated_at=str(row[8]),
        )
