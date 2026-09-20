"""Durable job and attempt lifecycle management feature module.

Purpose:
    Provides durable job tracking, attempt accounting, progress checkpointing,
    and orphan recovery with an atomic 9-state compare-and-swap (CAS) state
    machine backed by SQLite WAL persistence.

Key capabilities:
    * Strict 9-state compare-and-swap lifecycle (queued through terminal states).
    * Execution attempt tracking with retry limit enforcement.
    * Checkpoint persistence with stage and percentage progress tracking.
    * Orphan job recovery on startup for interrupted executions.
    * Append-only event journaling for lifecycle auditability.

Python API usage:
    jobs = ctx.require(WORKSPACE_JOBS)
    receipt = jobs.create_job(definition)
    jobs.transition_state(receipt.job_id, JobState.RUNNING)
    jobs.update_progress(receipt.job_id, JobProgress(percent=50.0))

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

from app.contracts.workspace import (
    WORKSPACE_JOBS,
    WORKSPACE_PERSISTENCE,
    InvalidJobTransitionError,
    JobAttempt,
    JobDefinition,
    JobEvent,
    JobNotFoundError,
    JobProgress,
    JobReceipt,
    JobState,
    WorkspacePersistenceService,
)
from app.contracts.workspace import (
    JobService as IJobService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# Strict 9-state compare-and-swap state machine rules
VALID_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.QUEUED: {
        JobState.RUNNING,
        JobState.CANCELLING,
        JobState.CANCELLED,
        JobState.INTERRUPTED,
    },
    JobState.RUNNING: {
        JobState.PAUSING,
        JobState.CANCELLING,
        JobState.SUCCEEDED,
        JobState.FAILED,
        JobState.INTERRUPTED,
    },
    JobState.PAUSING: {
        JobState.PAUSED,
        JobState.CANCELLING,
        JobState.INTERRUPTED,
        JobState.FAILED,
    },
    JobState.PAUSED: {
        JobState.QUEUED,
        JobState.RUNNING,
        JobState.CANCELLING,
        JobState.CANCELLED,
        JobState.INTERRUPTED,
    },
    JobState.CANCELLING: {
        JobState.CANCELLED,
        JobState.INTERRUPTED,
        JobState.FAILED,
    },
    JobState.CANCELLED: set(),
    JobState.SUCCEEDED: set(),
    JobState.FAILED: set(),
    JobState.INTERRUPTED: {JobState.QUEUED},
}

TERMINAL_STATES = {
    JobState.SUCCEEDED,
    JobState.FAILED,
    JobState.CANCELLED,
    JobState.INTERRUPTED,
}


@dataclass(frozen=True, slots=True)
class JobConfig:
    """Runtime configuration for durable job management."""

    heartbeat_timeout_s: float = 30.0
    max_attempts_per_job: int = 3

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if self.heartbeat_timeout_s <= 0:
            raise ValueError("heartbeat_timeout_s must be greater than 0")
        if self.max_attempts_per_job < 1:
            raise ValueError("max_attempts_per_job must be at least 1")


class JobService(IJobService):
    """Production implementation of durable job management backed by SQLite WAL."""

    def __init__(
        self,
        config: JobConfig,
        persistence: WorkspacePersistenceService,
    ) -> None:
        """Initialize job service with configured persistence.

        Args:
            config: Job configuration.
            persistence: Persistence service boundary.
        """
        self._config = config
        self._persistence = persistence

    @override
    def create_job(self, definition: JobDefinition) -> JobReceipt:
        """Register a new job in the durable ledger with queued state.

        Args:
            definition: Immutable job specification.

        Returns:
            Initial JobReceipt.
        """
        now = datetime.now(UTC).isoformat()
        payload_json = json.dumps(definition.payload)
        event_id = str(uuid.uuid4())
        event_details = json.dumps({"action": "created"})

        self._persistence.insert_job(
            job_id=definition.job_id,
            group_id=definition.group_id,
            operation=definition.operation,
            state=JobState.QUEUED.value,
            priority=definition.priority,
            resource_class=definition.resource_class,
            config_hash=definition.config_hash,
            payload_json=payload_json,
            created_at_utc=now,
            event_id=event_id,
            event_details_json=event_details,
        )

        logger.info("job_created")
        return JobReceipt(
            job_id=definition.job_id,
            state=JobState.QUEUED,
            progress_percent=0.0,
            message="Job created",
            updated_at_utc=datetime.fromisoformat(now),
        )

    @override
    def get_job(self, job_id: str) -> JobDefinition | None:
        """Retrieve the immutable job definition by ID.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobDefinition or None if not found.
        """
        row = self._persistence.get_job_record(job_id)
        if not row:
            return None

        return JobDefinition(
            job_id=str(row[0]),
            group_id=str(row[1]),
            operation=str(row[2]),
            priority=int(row[4]),
            resource_class=str(row[5]),
            config_hash=str(row[6]),
            payload=json.loads(str(row[7])),
            created_at_utc=datetime.fromisoformat(str(row[11])),
        )

    @override
    def get_receipt(self, job_id: str) -> JobReceipt | None:
        """Retrieve the latest receipt and progress snapshot for a job.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobReceipt or None if not found.
        """
        row = self._persistence.get_job_record(job_id)
        if not row:
            return None

        updated_str = str(row[13] or row[12] or row[11])
        return JobReceipt(
            job_id=str(row[0]),
            state=JobState(str(row[3])),
            progress_percent=float(row[8]),
            message=str(row[9]),
            updated_at_utc=datetime.fromisoformat(updated_str),
        )

    @override
    def transition_state(
        self,
        job_id: str,
        from_state: JobState | None,
        to_state: JobState,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Perform a compare-and-swap state transition and record an audit event.

        Args:
            job_id: Target job ID.
            from_state: Expected current state (or None to bypass CAS guard).
            to_state: Target destination state.
            details: Optional transition metadata.

        Returns:
            True if transition succeeded; False if CAS state mismatched.

        Raises:
            JobNotFoundError: If target job does not exist.
            InvalidJobTransitionError: If state machine transition is disallowed.
        """
        row = self._persistence.get_job_record(job_id)
        if not row:
            raise JobNotFoundError(f"Job '{job_id}' not found")

        current_state = JobState(str(row[3]))

        # CAS check
        if from_state is not None and current_state != from_state:
            logger.debug("job_cas_mismatch")
            return False

        # State machine transition check
        allowed = VALID_TRANSITIONS.get(current_state, set())
        if to_state not in allowed:
            msg = (
                f"Cannot transition job '{job_id}' from "
                f"'{current_state.value}' to '{to_state.value}'"
            )
            raise InvalidJobTransitionError(msg)

        now = datetime.now(UTC).isoformat()
        event_id = str(uuid.uuid4())
        attempt_id = (details or {}).get("attempt_id")
        event_details = json.dumps(details or {})
        terminal_reason = (
            str((details or {}).get("reason", to_state.value))
            if to_state in TERMINAL_STATES
            else None
        )

        expected = from_state.value if from_state is not None else current_state.value
        success = self._persistence.transition_job_state_cas(
            job_id=job_id,
            expected_state=expected,
            new_state=to_state.value,
            updated_at_utc=now,
            event_id=event_id,
            event_details_json=event_details,
            attempt_id=attempt_id,
            terminal_reason=terminal_reason,
        )
        if not success:
            logger.debug("job_cas_mismatch")
            return False

        logger.info("job_state_transitioned")
        return True

    @override
    def record_progress(self, progress: JobProgress) -> None:
        """Update job progression percentage, message, and checkpoint.

        Args:
            progress: Progress details emitted by worker.
        """
        checkpoint_json = (
            json.dumps(progress.checkpoint) if progress.checkpoint is not None else None
        )
        now = datetime.now(UTC).isoformat()

        self._persistence.update_job_progress(
            job_id=progress.job_id,
            progress_percent=progress.progress_percent,
            progress_message=progress.message,
            checkpoint_json=checkpoint_json,
        )

        if progress.attempt_id:
            if checkpoint_json is not None:
                self._persistence.update_attempt_checkpoint(
                    attempt_id=progress.attempt_id,
                    heartbeat_at_utc=now,
                    checkpoint_json=checkpoint_json,
                )
            else:
                self._persistence.update_attempt_heartbeat(
                    attempt_id=progress.attempt_id,
                    heartbeat_at_utc=now,
                )

        event_id = str(uuid.uuid4())
        self._persistence.record_job_event(
            event_id=event_id,
            job_id=progress.job_id,
            attempt_id=progress.attempt_id,
            from_state=JobState.RUNNING.value,
            to_state=JobState.RUNNING.value,
            details_json=json.dumps(
                {
                    "progress_percent": progress.progress_percent,
                    "message": progress.message,
                }
            ),
            created_at_utc=now,
        )

    @override
    def create_attempt(self, job_id: str, worker_id: str) -> JobAttempt:
        """Record the start of a worker execution attempt.

        Args:
            job_id: Target job ID.
            worker_id: Assigned worker identity.

        Returns:
            Created JobAttempt instance.

        Raises:
            JobNotFoundError: If target job does not exist.
        """
        if not self._persistence.get_job_record(job_id):
            raise JobNotFoundError(f"Job '{job_id}' not found")

        existing = self._persistence.get_job_attempts(job_id)
        seq = len(existing) + 1
        attempt_id = f"{job_id}-att-{seq}"
        now = datetime.now(UTC).isoformat()

        self._persistence.create_job_attempt(
            attempt_id=attempt_id,
            job_id=job_id,
            worker_id=worker_id,
            sequence=seq,
            state=JobState.RUNNING.value,
            created_at_utc=now,
        )

        return JobAttempt(
            attempt_id=attempt_id,
            job_id=job_id,
            worker_id=worker_id,
            sequence=seq,
            state=JobState.RUNNING,
            heartbeat_at_utc=datetime.fromisoformat(now),
            checkpoint=None,
            created_at_utc=datetime.fromisoformat(now),
            completed_at_utc=None,
        )

    @override
    def update_heartbeat(self, attempt_id: str) -> None:
        """Refresh the liveness heartbeat timestamp on an attempt.

        Args:
            attempt_id: Active attempt ID.
        """
        now = datetime.now(UTC).isoformat()
        self._persistence.update_attempt_heartbeat(attempt_id, now)

    @override
    def list_attempts(self, job_id: str) -> tuple[JobAttempt, ...]:
        """Return all historical attempts for a job.

        Args:
            job_id: Target job ID.

        Returns:
            Ordered tuple of JobAttempt records.
        """
        rows = self._persistence.get_job_attempts(job_id)
        return tuple(
            JobAttempt(
                attempt_id=str(r[0]),
                job_id=str(r[1]),
                worker_id=str(r[2]),
                sequence=int(r[3]),
                state=JobState(str(r[4])),
                heartbeat_at_utc=datetime.fromisoformat(str(r[5])) if r[5] else None,
                checkpoint=json.loads(str(r[6])) if r[6] else None,
                created_at_utc=datetime.fromisoformat(str(r[7])),
                completed_at_utc=datetime.fromisoformat(str(r[8])) if r[8] else None,
            )
            for r in rows
        )

    @override
    def list_events(self, job_id: str) -> tuple[JobEvent, ...]:
        """Return all audit events associated with a job.

        Args:
            job_id: Target job ID.

        Returns:
            Ordered tuple of JobEvent records.
        """
        rows = self._persistence.get_job_events(job_id)
        return tuple(
            JobEvent(
                event_id=str(r[0]),
                job_id=str(r[1]),
                attempt_id=str(r[2]) if r[2] else None,
                from_state=JobState(str(r[3])) if r[3] else None,
                to_state=JobState(str(r[4])),
                details=json.loads(str(r[5])),
                created_at_utc=datetime.fromisoformat(str(r[6])),
            )
            for r in rows
        )

    @override
    def recover_orphans(self, interrupted_reason: str = "Coordinator restart") -> int:
        """Mark all uncompleted attempts from previous runs as interrupted.

        Args:
            interrupted_reason: Audit note for the recovery action.

        Returns:
            Number of recovered orphan jobs.
        """
        now = datetime.now(UTC).isoformat()
        count = self._persistence.recover_orphaned_jobs(
            running_states=(JobState.RUNNING.value, JobState.PAUSING.value),
            interrupted_state=JobState.INTERRUPTED.value,
            interrupted_reason=interrupted_reason,
            now_utc=now,
        )
        logger.info("orphan_jobs_recovered")
        return count


SPEC = FeatureSpec(
    name="workspace.jobs",
    provides=frozenset({WORKSPACE_JOBS}),
    requires=frozenset({WORKSPACE_PERSISTENCE}),
    optional=frozenset(),
    description="Durable job and attempt lifecycle management.",
)


class JobFeature:
    """Lifecycle-managed feature for durable job states and CAS transitions.

    Mounts JobService, binds persistence facilities, and publishes WORKSPACE_JOBS
    capability into the runtime composition.
    """

    def __init__(self, config: JobConfig | None = None) -> None:
        """Initialize job lifecycle feature with execution and retry config.

        Args:
            config: Job configuration specifying maximum retries and timeouts.
                If None, default JobConfig is used.
        """
        self._config = config or JobConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start job service, bind persistence, and publish WORKSPACE_JOBS.

        Args:
            context: Runtime feature context used for dependency resolution and
                capability provision.
        """
        persistence = context.require(WORKSPACE_PERSISTENCE)
        service = JobService(self._config, persistence)
        context.provide(WORKSPACE_JOBS, service)
        logger.info("workspace_jobs_started")


def feature() -> JobFeature:
    """Construct an unmounted JobFeature instance for runtime bootstrapping.

    Returns:
        Configured JobFeature instance ready for composition registration.
    """
    return JobFeature()


__all__ = [
    "SPEC",
    "JobConfig",
    "JobFeature",
    "JobService",
    "feature",
]
