"""Hardware Diagnostics, Process Pool Allocation, and Job Admission Manager.

Description:
    This module provides point-in-time hardware resource diagnostics, background
    process pool allocation, resource-bounded compute job admission, and cooperative
    task cancellation. It exists to guarantee bounded CPU and memory consumption,
    prevent out-of-memory crashes, enforce capacity limits across components, and
    ensure orderly cancellation during shutdown. Externally, it participates in
    three key workflows: (1) `BootstrapCoordinator` calls `diagnostics()` during
    `_services()` to sample system RAM and CPU topology, builds a `JobManager` sized
    to host capacity, and creates a `ProcessPoolExecutor` via `create_pool()`; (2)
    `Composition` injects scoped `JobAccess` capability facades into workspaces and
    plugins, allowing quantitative modules to offload background compute tasks; and
    (3) Component uninstallation and host shutdown invoke `JobManager.close()` to
    guarantee that background jobs terminate cooperatively within bounded timeframes.
    Internally, `diagnostics()` queries `psutil`; `create_pool()` constructs worker
    pools bounded for platform safety; and `JobManager` validates `Budget` constraints,
    tracks worker/memory reservations, executes asynchronous tasks with timeout
    supervision, and manages job state transitions.

Purpose:
    FEAT-HOST-JOBS: Hardware Diagnostics, Process Pool, and Job Admission Manager.
    Provides hardware resource inspection, multiprocessing pool management,
    budget-guarded task admission, and cooperative job cancellation.

Key Capabilities:
    - FR-HOST-JOBS-HARDWARE-DIAGNOSTICS: System Metrics Sampling
      Associated: `diagnostics()`
      Logging: Emits info log when hardware diagnostics (CPU, RAM, OS, Python)
      are collected.
    - FR-HOST-JOBS-POOL-ALLOCATION: Bounded Process Pool Allocation
      Associated: `create_pool()`
      Logging: Emits info log with allocated worker counts upon process pool
      creation.
    - FR-HOST-JOBS-BUDGET-ADMISSION: Resource-Guarded Task Admission
      Associated: `JobManager.submit()`, `Budget.validate()`
      Logging: Emits info log detailing task ID, owner, worker budget, memory
      reservation, and timeout on task submission.
    - FR-HOST-JOBS-EXECUTION-LIFECYCLE: Execution & State Transitions
      Associated: `JobManager._run()`, `JobManager._finished()`
      Logging: Emits debug log on job start and info/warning/exception logs on
      success, timeout, failure, or cancellation.
    - FR-HOST-JOBS-COOPERATIVE-CANCELLATION: Owner-Scoped Task Cancellation
      Associated: `JobManager.cancel()`, `JobManager.close()`
      Logging: Emits info log when job cancellation is requested and when
      owner-scoped job queues are closed.

Python API Usage:
    ```python
    from app.host.jobs import Budget, JobManager, diagnostics

    # 1. Inspect hardware resources
    hw = diagnostics()
    cpu_count, mem_bytes = hw["cpu_count"], hw["memory_available_bytes"]

    # 2. Instantiate job manager with capacity limits
    manager = JobManager(workers=cpu_count, memory_bytes=mem_bytes // 2)


    # 3. Submit cooperative async task under explicit budget
    async def sample_work() -> None:
        pass


    budget = Budget(workers=1, memory_bytes=1024 * 1024 * 100, timeout_seconds=10.0)
    job = manager.submit("workspace.analysis", budget, sample_work)

    # 4. Await or close manager
    await manager.close("workspace.analysis")
    ```

CLI Usage:
    Worker counts and process pool sizing are configured via CLI entrypoint
    flags:
    ```bash
    # Launch host with explicit worker process count
    uv run python -m app.main --workers 4

    # Run host jobs test suite
    uv run pytest tests/host/test_jobs.py
    ```
"""

from __future__ import annotations

import asyncio
import math
import os
import platform
from collections.abc import Awaitable, Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from typing import Any, Literal
from uuid import uuid4

import psutil

from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_JOBS = 4096
SHUTDOWN_SECONDS = 5.0


def diagnostics() -> dict[str, Any]:
    """Collect a point-in-time CPU, memory, OS, and Python snapshot.

    Queries psutil and platform synchronously, then logs collection without host
    identifiers. Hardware-query failures propagate; results are not a resource
    reservation.

    Returns:
        Mapping with CPU count, total/available RAM in bytes, OS name, and Python
        version.
    """
    memory = psutil.virtual_memory()
    logger.info("Hardware diagnostics collected")
    return {
        "cpu_count": os.cpu_count() or 1,
        "memory_total_bytes": memory.total,
        "memory_available_bytes": memory.available,
        "system": platform.system(),
        "python_version": platform.python_version(),
    }


def create_pool(workers: int) -> ProcessPoolExecutor:
    """Construct an executor whose workers start when work is submitted.

    The configured HostSettings bounds explicit counts for Windows compatibility.
    This helper neither submits tasks nor loads quantitative providers.

    Args:
        workers: Explicit process count; zero selects CPU count minus one, bounded to
            1..61.

    Returns:
        A ProcessPoolExecutor owned and shut down by the caller.

    Raises:
        ValueError: The executor rejects a nonpositive explicit worker count.
    """
    count = workers or min(61, max(1, (os.cpu_count() or 1) - 1))
    logger.info("Compute pool allocated with %s workers", count)
    return ProcessPoolExecutor(max_workers=count)


@dataclass(frozen=True)
class Budget:
    """Logical CPU/memory reservation and finite cooperative deadline."""

    workers: int
    memory_bytes: int
    timeout_seconds: float

    def validate(self) -> None:
        """Reject nonpositive, unbounded or nonintegral resource requests."""
        if (
            type(self.workers) is not int
            or type(self.memory_bytes) is not int
            or self.workers < 1
            or self.memory_bytes < 1
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("Invalid job budget")


@dataclass(frozen=True)
class Job:
    """Immutable job state without exception text or task-input diagnostics."""

    id: str
    owner: str
    budget: Budget
    state: Literal["queued", "running", "succeeded", "failed", "cancelled", "timed_out"]


class JobManager:
    """One event-loop admission authority shared by all scoped owner capabilities."""

    def __init__(self, workers: int, memory_bytes: int) -> None:
        Budget(workers, memory_bytes, 1).validate()
        self.capacity = (workers, memory_bytes)
        self.reserved = (0, 0)
        self.records: dict[str, Job] = {}
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.closed = False

    def submit(
        self, owner: str, budget: Budget, operation: Callable[[], Awaitable[None]]
    ) -> Job:
        """Reserve capacity before starting an explicitly supplied local task body.

        Raises:
            ValueError: Invalid budget, owner, capacity or admission lifecycle.
        """
        budget.validate()
        if not owner or self.closed or len(self.records) >= MAX_JOBS:
            raise ValueError("Job admission unavailable")
        workers = self.reserved[0] + budget.workers
        memory = self.reserved[1] + budget.memory_bytes
        if workers > self.capacity[0] or memory > self.capacity[1]:
            raise ValueError("Insufficient host resources")
        loop = asyncio.get_running_loop()
        job = Job(uuid4().hex, owner, budget, "queued")
        self.reserved = (workers, memory)
        self.records[job.id] = job
        self.tasks[job.id] = loop.create_task(self._run(job, operation))
        self.tasks[job.id].add_done_callback(lambda _task: self._finished(job))
        logger.info(
            "Host job submitted: id=%s, owner=%s, budget=(workers=%d, "
            "mem=%dMB, timeout=%.1fs)",
            job.id,
            owner,
            budget.workers,
            budget.memory_bytes // (1024 * 1024),
            budget.timeout_seconds,
        )
        return job

    def _finished(self, job: Job) -> None:
        """Release reservations even for cancellation before a queued task starts."""
        self.tasks.pop(job.id, None)
        self.reserved = (
            self.reserved[0] - job.budget.workers,
            self.reserved[1] - job.budget.memory_bytes,
        )
        if self.records[job.id].state in {"queued", "running"}:
            self.records[job.id] = replace(job, state="cancelled")

    async def _run(self, job: Job, operation: Callable[[], Awaitable[None]]) -> None:
        """Run one trusted cooperative body and record only attributed safe outcomes."""
        self.records[job.id] = replace(job, state="running")
        logger.debug("Host job started: id=%s, owner=%s", job.id, job.owner)
        try:
            async with asyncio.timeout(job.budget.timeout_seconds):
                await operation()
        except TimeoutError:
            self.records[job.id] = replace(job, state="timed_out")
            logger.warning(
                "Host job timed out: id=%s, owner=%s (timeout=%.1fs)",
                job.id,
                job.owner,
                job.budget.timeout_seconds,
            )
        except asyncio.CancelledError:
            self.records[job.id] = replace(job, state="cancelled")
            logger.info("Host job cancelled: id=%s, owner=%s", job.id, job.owner)
            raise
        except Exception:
            self.records[job.id] = replace(job, state="failed")
            logger.exception("Host job failed: id=%s, owner=%s", job.id, job.owner)
        else:
            self.records[job.id] = replace(job, state="succeeded")
            logger.info("Host job succeeded: id=%s, owner=%s", job.id, job.owner)

    def status(self, owner: str, job_id: str) -> Job:
        """Read only the caller's job, without granting peer execution authority."""
        job = self.records[job_id]
        if job.owner != owner:
            raise PermissionError("Job access denied")
        return job

    def cancel(self, owner: str, job_id: str) -> None:
        """Request cooperative cancellation of an owned job."""
        self.status(owner, job_id)
        logger.info("Host job cancel requested: id=%s, owner=%s", job_id, owner)
        task = self.tasks.get(job_id)
        if task is not None:
            task.cancel()

    async def close(self, owner: str | None = None) -> None:
        """Cancel owned/all jobs and report bodies that fail to stop within the bound.

        Reservations are retained until a task actually finishes. This is not OS
        process containment for an uncooperative extension.
        """
        if owner is None:
            self.closed = True
        pending = [
            task
            for key, task in self.tasks.items()
            if owner is None or self.records[key].owner == owner
        ]
        for task in pending:
            task.cancel()
        if pending:
            _, unfinished = await asyncio.wait(pending, timeout=SHUTDOWN_SECONDS)
            if unfinished:
                raise TimeoutError("Owner jobs did not stop")
        logger.info("JobManager closed: owner=%s", owner)
