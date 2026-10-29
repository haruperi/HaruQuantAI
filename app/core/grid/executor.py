"""Remote compute coordinator, worker health tracking, and local fallback."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.core.grid.contracts import (
    GridTopologyInfo,
    RemoteJobResult,
    RemoteJobSpec,
    RemoteWorkerNode,
)

if TYPE_CHECKING:
    from app.core.jobs.manager import JobManager, JobRecord

__all__ = ["RemoteComputeCoordinator"]


class RemoteComputeCoordinator:
    """Coordinator managing cluster workers, dispatch, deduplication, and fallback."""

    def __init__(
        self,
        local_manager: JobManager | None = None,
        *,
        fallback_to_local: bool = True,
    ) -> None:
        """Initialize coordinator with optional local JobManager fallback."""
        self.local_manager = local_manager
        self.fallback_to_local = fallback_to_local
        self.workers: dict[str, RemoteWorkerNode] = {}
        self.assigned_jobs: dict[str, str] = {}
        self.job_specs: dict[str, RemoteJobSpec] = {}
        self.job_results: dict[str, RemoteJobResult] = {}
        self.job_retries: dict[str, int] = {}
        self.job_states: dict[str, str] = {}
        self.listeners: list[Callable[[str, str, RemoteJobResult], None]] = []
        self.is_local_mode: bool = False

    def add_job_finished_listener(
        self, callback: Callable[[str, str, RemoteJobResult], None]
    ) -> None:
        """Register a callback for terminal job completion events."""
        self.listeners.append(callback)

    def register_worker(self, node: RemoteWorkerNode) -> None:
        """Register or update a remote worker node."""
        self.workers[node.worker_id] = node

    def heartbeat(
        self,
        worker_id: str,
        timestamp_utc: datetime | None = None,
        running_threads: int = 0,
        cpu_usage_pct: int = 0,
        used_memory_mb: float = 0.0,
    ) -> None:
        """Process heartbeat from a worker, updating capability metrics and status."""
        worker = self.workers.get(worker_id)
        if worker is not None:
            worker.last_heartbeat_utc = timestamp_utc or datetime.now(UTC)
            worker.status = "HEALTHY"
            worker.running_threads = running_threads
            worker.cpu_usage_pct = cpu_usage_pct
            worker.used_memory_mb = used_memory_mb

    def get_topology(self, now_utc: datetime | None = None) -> GridTopologyInfo:
        """Compile active topology snapshot across healthy nodes."""
        now = now_utc or datetime.now(UTC)
        healthy = [w for w in self.workers.values() if w.is_healthy(now)]
        return GridTopologyInfo(
            nodes=list(self.workers.values()),
            running_threads=sum(w.running_threads for w in healthy),
            total_cores=sum(w.total_cores for w in healthy),
        )

    def _select_worker(
        self, now_utc: datetime | None = None
    ) -> RemoteWorkerNode | None:
        """Select healthy worker with the lowest thread load."""
        now = now_utc or datetime.now(UTC)
        healthy = [w for w in self.workers.values() if w.is_healthy(now)]
        if not healthy:
            return None
        return min(healthy, key=lambda w: w.running_threads)

    def submit(
        self, spec: RemoteJobSpec, now_utc: datetime | None = None
    ) -> JobRecord | str:
        """Dispatch job to a healthy remote worker or fall back to local JobManager."""
        self.job_specs[spec.job_id] = spec
        worker = self._select_worker(now_utc)

        if worker is None:
            if self.fallback_to_local and self.local_manager is not None:
                self.is_local_mode = True
                fn = spec.payload.get("fn", lambda: spec.payload)
                return self.local_manager.submit_job(
                    fn, job_id=spec.job_id, kind="compute"
                )
            self.job_states[spec.job_id] = "FAILED"
            result = RemoteJobResult(
                job_id=spec.job_id,
                job_group_id=spec.job_group_id,
                success=False,
                error_message=(
                    "No healthy remote worker available and local fallback disabled"
                ),
            )
            self.job_results[spec.job_id] = result
            return spec.job_id

        self.assigned_jobs[spec.job_id] = worker.worker_id
        self.job_states[spec.job_id] = "DISPATCHED"
        worker.running_threads += 1
        return spec.job_id

    def handle_result(self, result: RemoteJobResult) -> bool:
        """Record remote result with first-wins deduplication. Return False if dup."""
        current_state = self.job_states.get(result.job_id)
        if current_state in ("COMPLETED", "FAILED", "STOPPED"):
            # Deduplication: ignore late or duplicate completions from retry workers
            return False

        worker_id = self.assigned_jobs.get(result.job_id)
        if worker_id and worker_id in self.workers:
            self.workers[worker_id].running_threads = max(
                0, self.workers[worker_id].running_threads - 1
            )

        self.job_results[result.job_id] = result
        self.job_states[result.job_id] = (
            "STOPPED"
            if result.stopped
            else ("COMPLETED" if result.success else "FAILED")
        )

        for listener in list(self.listeners):
            listener(result.job_group_id, result.job_id, result)

        return True

    def check_watchdog(
        self, now_utc: datetime | None = None, max_retries: int = 2
    ) -> list[str]:
        """Detect timed-out workers, reassign in-flight jobs, or record failure."""
        now = now_utc or datetime.now(UTC)
        disconnected: list[str] = []

        for worker in self.workers.values():
            if (
                not worker.is_healthy(now, timeout_sec=10.0)
                and worker.status != "DISCONNECTED"
            ):
                worker.status = "DISCONNECTED"
                disconnected.append(worker.worker_id)

        # Reassign or fail jobs belonging to disconnected workers
        for job_id, worker_id in list(self.assigned_jobs.items()):
            if (
                worker_id in disconnected
                and self.job_states.get(job_id) == "DISPATCHED"
            ):
                retries = self.job_retries.get(job_id, 0)
                if retries < max_retries:
                    new_worker = self._select_worker(now)
                    if new_worker is not None:
                        self.assigned_jobs[job_id] = new_worker.worker_id
                        self.job_retries[job_id] = retries + 1
                        new_worker.running_threads += 1
                        continue

                # Max retries reached or no worker available
                self.job_states[job_id] = "FAILED"
                spec = self.job_specs.get(job_id)
                group_id = spec.job_group_id if spec else "default"
                result = RemoteJobResult(
                    job_id=job_id,
                    job_group_id=group_id,
                    worker_id=worker_id,
                    success=False,
                    error_message="Worker disconnected and max retries exceeded",
                )
                self.job_results[job_id] = result
                for listener in list(self.listeners):
                    listener(group_id, job_id, result)

        return disconnected

    def cancel(self, job_id: str) -> None:
        """Cancel an in-flight remote job and mark as STOPPED."""
        current = self.job_states.get(job_id)
        if current in ("COMPLETED", "FAILED", "STOPPED"):
            return

        worker_id = self.assigned_jobs.get(job_id)
        if worker_id and worker_id in self.workers:
            self.workers[worker_id].running_threads = max(
                0, self.workers[worker_id].running_threads - 1
            )

        self.job_states[job_id] = "STOPPED"
        spec = self.job_specs.get(job_id)
        group_id = spec.job_group_id if spec else "default"
        result = RemoteJobResult(
            job_id=job_id,
            job_group_id=group_id,
            worker_id=worker_id or "",
            success=False,
            stopped=True,
            error_message="Job execution cancelled",
        )
        self.job_results[job_id] = result
        for listener in list(self.listeners):
            listener(group_id, job_id, result)
