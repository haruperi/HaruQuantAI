"""Grid compute management and coordinator integration service.

Description:
    Provides compute cluster orchestration, worker registration, heartbeat tracking,
    and job lifecycle aggregation for AppGridControl. Interacts with the core
    RemoteComputeCoordinator to compile live queue snapshots matching donor contracts.

Purpose:
    FEAT-GRID-CONTROL: Cluster management and distributed execution state aggregation.

Key Capabilities:
    - FR-GRID-SERVICE-COORDINATION: Manage worker nodes, heartbeats, and jobs.
    - FR-GRID-SERVICE-SNAPSHOT: Aggregate active, queued, and finished job states.

Python API Usage:
    from app.workspace.grid_control.service import GridControlService
    service = GridControlService()
    snapshot = service.get_grid_data()

CLI Usage:
    uv run python -m app.workspace.grid_control.service
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any

from app.core.grid.contracts import (
    GridTopologyInfo,
    RemoteJobResult,
    RemoteJobSpec,
    RemoteWorkerNode,
)
from app.core.grid.executor import RemoteComputeCoordinator
from app.core.host.logging import get_logger
from app.workspace.grid_control.models import (
    FinishedJobSnapshot,
    GridDataPayload,
    RunningJobSnapshot,
    WaitingJobSnapshot,
)

__all__ = ["GridControlService"]

_logger = get_logger(__name__)


class GridControlService:
    """Service managing compute cluster workers, jobs, and wire snapshots."""

    def __init__(
        self,
        coordinator: RemoteComputeCoordinator | None = None,
        *,
        max_finished_jobs: int = 150,
    ) -> None:
        """Initialize GridControlService with optional shared coordinator."""
        self.coordinator = coordinator or RemoteComputeCoordinator()
        self.max_finished_jobs = max_finished_jobs
        self._create_times: dict[str, int] = {}
        self._start_times: dict[str, int] = {}
        self._job_progress: dict[str, int] = {}
        self._finished_jobs: deque[FinishedJobSnapshot] = deque(
            maxlen=max_finished_jobs
        )

        # Register completion listener on the coordinator
        self.coordinator.add_job_finished_listener(self._on_job_completed)
        _logger.info(
            "Initialized GridControlService with max_finished_jobs=%d",
            max_finished_jobs,
        )

    def _now_ms(self, now_utc: datetime | None = None) -> int:
        dt = now_utc or datetime.now(UTC)
        return int(dt.timestamp() * 1000)

    def register_worker(self, node: RemoteWorkerNode) -> None:
        """Register or update a remote worker node."""
        _logger.info(
            "FR-GRID-SERVICE-COORDINATION: Registering worker %s at %s",
            node.worker_id,
            node.ip,
        )
        self.coordinator.register_worker(node)

    def heartbeat(
        self,
        worker_id: str,
        timestamp_utc: datetime | None = None,
        running_threads: int = 0,
        cpu_usage_pct: int = 0,
        used_memory_mb: float = 0.0,
    ) -> None:
        """Process worker heartbeat to update metrics and health."""
        _logger.debug(
            "FR-GRID-SERVICE-COORDINATION: Heartbeat from worker %s: "
            "cpu=%d%%, threads=%d",
            worker_id,
            cpu_usage_pct,
            running_threads,
        )
        self.coordinator.heartbeat(
            worker_id,
            timestamp_utc=timestamp_utc,
            running_threads=running_threads,
            cpu_usage_pct=cpu_usage_pct,
            used_memory_mb=used_memory_mb,
        )

    def get_topology(self, now_utc: datetime | None = None) -> GridTopologyInfo:
        """Query active cluster topology."""
        _logger.debug("FR-GRID-SERVICE-COORDINATION: Querying grid topology")
        return self.coordinator.get_topology(now_utc)

    def submit_job(self, spec: RemoteJobSpec, now_utc: datetime | None = None) -> Any:
        """Submit a compute job to the coordinator and track timestamps."""
        now_ms = self._now_ms(now_utc)
        self._create_times[spec.job_id] = now_ms
        self._job_progress[spec.job_id] = 0

        _logger.info(
            "FR-GRID-SERVICE-COORDINATION: Submitting job %s (group=%s)",
            spec.job_id,
            spec.job_group_id,
        )
        result = self.coordinator.submit(spec, now_utc=now_utc)

        # If worker assigned immediately or running locally, record start time
        is_active = (
            spec.job_id in self.coordinator.assigned_jobs
            or self.coordinator.is_local_mode
        )
        if is_active:
            self._start_times[spec.job_id] = now_ms

        return result

    def update_job_progress(self, job_id: str, progress: int) -> None:
        """Update execution progress percentage for an active job."""
        _logger.debug(
            "FR-GRID-SERVICE-COORDINATION: Updating progress for job %s: %d%%",
            job_id,
            progress,
        )
        self._job_progress[job_id] = max(-1, min(100, progress))

    def _on_job_completed(
        self, job_group_id: str, job_id: str, result: RemoteJobResult
    ) -> None:
        """Internal callback invoked when a job finishes in the coordinator."""
        now_ms = int(datetime.now(UTC).timestamp() * 1000)
        create_time = self._create_times.get(job_id, now_ms)
        start_time = self._start_times.get(job_id, create_time)
        duration = max(0, result.duration_ms or (now_ms - start_time))
        duration_with_wait = max(duration, now_ms - create_time)

        snapshot = FinishedJobSnapshot(
            job_id=job_id,
            job_group_id=job_group_id,
            create_time_ms=create_time,
            duration_ms=duration,
            duration_with_wait_ms=duration_with_wait,
            start_time_ms=start_time,
            finish_time_ms=now_ms,
            success=result.success,
            message=result.error_message,
        )
        self._finished_jobs.appendleft(snapshot)
        _logger.info(
            "FR-GRID-SERVICE-COORDINATION: Job %s completed: success=%s, duration=%dms",
            job_id,
            result.success,
            duration,
        )

    def record_finished_job(self, snapshot: FinishedJobSnapshot) -> None:
        """Manually record a finished job snapshot."""
        _logger.debug(
            "FR-GRID-SERVICE-COORDINATION: Recording finished job snapshot: %s",
            snapshot.job_id,
        )
        self._finished_jobs.appendleft(snapshot)

    def get_grid_data(self, now_utc: datetime | None = None) -> GridDataPayload:
        """Compile live snapshot across running, waiting, and finished jobs."""
        now_ms = self._now_ms(now_utc)
        running: list[RunningJobSnapshot] = []
        waiting: list[WaitingJobSnapshot] = []

        finished_ids = {job.job_id for job in self._finished_jobs}

        for job_id, spec in self.coordinator.job_specs.items():
            if job_id in finished_ids:
                continue

            create_time = self._create_times.get(job_id, now_ms)
            start_time = self._start_times.get(job_id, create_time)
            is_assigned = (
                job_id in self.coordinator.assigned_jobs
                or self.coordinator.is_local_mode
            )

            if is_assigned:
                duration = max(0, now_ms - start_time)
                duration_with_wait = max(0, now_ms - create_time)
                progress = self._job_progress.get(job_id, 0)
                running.append(
                    RunningJobSnapshot(
                        job_id=job_id,
                        job_group_id=spec.job_group_id,
                        create_time_ms=create_time,
                        progress=progress,
                        duration_ms=duration,
                        duration_with_wait_ms=duration_with_wait,
                        start_time_ms=start_time,
                        waiting=False,
                    )
                )
            else:
                waiting.append(
                    WaitingJobSnapshot(
                        job_id=job_id,
                        job_group_id=spec.job_group_id,
                        create_time_ms=create_time,
                    )
                )

        _logger.info(
            "FR-GRID-SERVICE-SNAPSHOT: Generated grid data payload: "
            "%d running, %d waiting, %d finished",
            len(running),
            len(waiting),
            len(self._finished_jobs),
        )

        return GridDataPayload(
            running=tuple(running),
            waiting=tuple(waiting),
            finished=tuple(self._finished_jobs),
        )
