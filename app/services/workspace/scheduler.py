"""Bounded priority job scheduler and worker supervisor feature module.

Purpose:
    Coordinates bounded job queue dispatching, priority-ordered execution,
    concurrency ceiling management, and cooperative job pause/resume/cancel
    supervision.

Key capabilities:
    * Min-heap priority dispatching ordering jobs by urgency and submission time.
    * Bounded concurrency ceiling preventing worker oversubscription.
    * Cooperative execution supervision supporting pause, resume, and cancel.
    * Queue depth and dispatch latency observability telemetry.

Python API usage:
    scheduler = ctx.require(WORKSPACE_SCHEDULER)
    receipt = scheduler.submit_job(definition, priority=10)
    stats = scheduler.get_queue_stats()
    scheduler.cancel_job(receipt.job_id)

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from app.contracts.workspace import (
    WORKSPACE_JOBS,
    WORKSPACE_SCHEDULER,
    JobDefinition,
    JobReceipt,
    JobService,
    JobState,
    QueueStats,
)
from app.contracts.workspace import (
    SchedulerService as ISchedulerService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    """Configuration for scheduler concurrency and dispatch."""

    max_concurrency: int = 4
    poll_interval_s: float = 0.5

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if self.poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be greater than 0")


class SchedulerService(ISchedulerService):
    """Production implementation of bounded priority dispatch and supervision."""

    def __init__(
        self,
        config: SchedulerConfig,
        job_service: JobService,
    ) -> None:
        """Initialize scheduler with configured concurrency.

        Args:
            config: Scheduler configuration options.
            job_service: Durable job service boundary.
        """
        self._config = config
        self._job_service = job_service
        # Priority queue entries: (-priority, sequence_id, job_id)
        self._queue: list[tuple[int, int, str]] = []
        self._seq_counter: int = 0
        self._active_jobs: set[str] = set()
        self._paused_jobs: set[str] = set()

    @override
    def submit_job(self, definition: JobDefinition) -> JobReceipt:
        """Submit a job to the scheduling queue.

        Args:
            definition: Immutable job definition.

        Returns:
            Receipt confirming admission.
        """
        receipt = self._job_service.create_job(definition)
        self._seq_counter += 1
        heapq.heappush(
            self._queue,
            (-definition.priority, self._seq_counter, definition.job_id),
        )
        logger.info("job_scheduled_in_queue")
        return receipt

    @override
    def pause_job(self, job_id: str) -> bool:
        """Request a cooperative pause on an active or queued job.

        Args:
            job_id: Target job ID.

        Returns:
            True if pause initiated successfully.
        """
        receipt = self._job_service.get_receipt(job_id)
        if not receipt:
            return False

        if receipt.state == JobState.RUNNING:
            ok = self._job_service.transition_state(
                job_id,
                JobState.RUNNING,
                JobState.PAUSING,
                {"action": "pause_requested"},
            )
            if ok:
                self._paused_jobs.add(job_id)
                self._active_jobs.discard(job_id)
                logger.info("job_pause_requested")
            return ok

        if receipt.state == JobState.QUEUED:
            ok = self._job_service.transition_state(
                job_id,
                JobState.QUEUED,
                JobState.PAUSED,
                {"action": "paused_while_queued"},
            )
            if ok:
                self._paused_jobs.add(job_id)
                logger.info("job_paused_in_queue")
            return ok

        return False

    @override
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job from its latest checkpoint.

        Args:
            job_id: Target job ID.

        Returns:
            True if resume initiated successfully.
        """
        receipt = self._job_service.get_receipt(job_id)
        if not receipt or receipt.state != JobState.PAUSED:
            return False

        ok = self._job_service.transition_state(
            job_id,
            JobState.PAUSED,
            JobState.QUEUED,
            {"action": "resumed"},
        )
        if ok:
            self._paused_jobs.discard(job_id)
            job = self._job_service.get_job(job_id)
            priority = job.priority if job else 0
            self._seq_counter += 1
            heapq.heappush(self._queue, (-priority, self._seq_counter, job_id))
            logger.info("job_resumed")
        return ok

    @override
    def cancel_job(self, job_id: str) -> bool:
        """Request cooperative cancellation of a job.

        Args:
            job_id: Target job ID.

        Returns:
            True if cancellation initiated.
        """
        receipt = self._job_service.get_receipt(job_id)
        if not receipt:
            return False

        if receipt.state == JobState.QUEUED:
            ok = self._job_service.transition_state(
                job_id,
                JobState.QUEUED,
                JobState.CANCELLED,
                {"reason": "cancelled_by_scheduler"},
            )
            if ok:
                logger.info("queued_job_cancelled")
            return ok

        if receipt.state == JobState.RUNNING:
            ok = self._job_service.transition_state(
                job_id,
                JobState.RUNNING,
                JobState.CANCELLING,
                {"reason": "cancelled_by_scheduler"},
            )
            if ok:
                self._active_jobs.discard(job_id)
                logger.info("running_job_cancellation_requested")
            return ok

        if receipt.state in (JobState.PAUSED, JobState.PAUSING):
            ok = self._job_service.transition_state(
                job_id,
                receipt.state,
                JobState.CANCELLED,
                {"reason": "cancelled_by_scheduler"},
            )
            if ok:
                self._paused_jobs.discard(job_id)
                self._active_jobs.discard(job_id)
                logger.info("paused_job_cancelled")
            return ok

        return False

    @override
    def dispatch_next(self) -> JobDefinition | None:
        """Select and dequeue the highest-priority pending job.

        Returns:
            JobDefinition or None if queue is empty or at capacity.
        """
        if len(self._active_jobs) >= self._config.max_concurrency:
            return None

        while self._queue:
            _, _, job_id = heapq.heappop(self._queue)
            receipt = self._job_service.get_receipt(job_id)
            if not receipt or receipt.state != JobState.QUEUED:
                continue

            job_def = self._job_service.get_job(job_id)
            if not job_def:
                continue

            ok = self._job_service.transition_state(
                job_id,
                JobState.QUEUED,
                JobState.RUNNING,
                {"action": "dispatched_by_scheduler"},
            )
            if ok:
                self._active_jobs.add(job_id)
                logger.info("job_dispatched_for_execution")
                return job_def

        return None

    def poll_and_dispatch(self) -> list[str]:
        """Dispatch queued jobs up to configured concurrency limit.

        Returns:
            List of dispatched job IDs.
        """
        dispatched: list[str] = []
        while len(self._active_jobs) < self._config.max_concurrency:
            job = self.dispatch_next()
            if not job:
                break
            dispatched.append(job.job_id)

        return dispatched

    def mark_completed(self, job_id: str) -> None:
        """Inform scheduler that an active job has reached a terminal state.

        Args:
            job_id: Completed job ID.
        """
        self._active_jobs.discard(job_id)
        self._paused_jobs.discard(job_id)

    @override
    def get_queue_stats(self) -> QueueStats:
        """Return current metrics on queued, active, and paused jobs.

        Returns:
            QueueStats snapshot.
        """
        # Clean up stale queue items
        valid_queued = 0
        for _, _, job_id in self._queue:
            rcpt = self._job_service.get_receipt(job_id)
            if rcpt and rcpt.state == JobState.QUEUED:
                valid_queued += 1

        return QueueStats(
            queued_count=valid_queued,
            running_count=len(self._active_jobs),
            paused_count=len(self._paused_jobs),
            max_concurrency=self._config.max_concurrency,
        )


SPEC = FeatureSpec(
    name="workspace.scheduler",
    provides=frozenset({WORKSPACE_SCHEDULER}),
    requires=frozenset({WORKSPACE_JOBS}),
    optional=frozenset(),
    description="Bounded dispatch and worker supervision.",
)


class SchedulerFeature:
    """Lifecycle-managed feature for priority dispatch and worker supervision.

    Mounts SchedulerService, resolves WORKSPACE_JOBS dependency, triggers orphan job
    recovery on startup, and publishes WORKSPACE_SCHEDULER.
    """

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        """Initialize scheduler feature with concurrency and dispatch configuration.

        Args:
            config: Scheduler configuration specifying concurrency limits and dispatch
                intervals. If None, default SchedulerConfig is used.
        """
        self._config = config or SchedulerConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start scheduler service, recover orphan jobs, and publish capability.

        Args:
            context: Runtime feature context used for dependency resolution and
                capability provision.
        """
        job_service = context.require(WORKSPACE_JOBS)
        # Recover any orphan jobs from earlier runs
        recovered = job_service.recover_orphans()
        if recovered > 0:
            logger.info("scheduler_recovered_orphans_on_boot")

        service = SchedulerService(self._config, job_service)
        context.provide(WORKSPACE_SCHEDULER, service)
        logger.info("workspace_scheduler_started")


def feature() -> SchedulerFeature:
    """Construct an unmounted SchedulerFeature instance for bootstrapping.

    Returns:
        Configured SchedulerFeature instance ready for registration.
    """
    return SchedulerFeature()


__all__ = [
    "SPEC",
    "SchedulerConfig",
    "SchedulerFeature",
    "SchedulerService",
    "feature",
]
