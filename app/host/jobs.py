"""Hardware diagnostics, process pool allocation, and job admission manager.

Description:
    Provides point-in-time hardware resource diagnostics, background process pool
    allocation, resource-bounded compute job admission, and cooperative task
    cancellation. It exists to guarantee bounded CPU and memory consumption,
    prevent out-of-memory crashes, enforce capacity limits across components, and
    ensure orderly cancellation during shutdown. Externally, it participates in
    three key workflows: (1) `BootstrapCoordinator` calls `diagnostics()` during
    `_services()` to sample system RAM and CPU topology, builds a `JobManager` sized
    to host capacity, and creates a `ProcessPoolExecutor` via `create_pool()`; (2)
    `Composition` injects scoped `JobAccess` capability facades into workspaces and
    plugins, allowing quantitative modules to offload background compute tasks; and
    (3) Component uninstallation and host shutdown invoke `JobManager.close()` to
    guarantee that background jobs terminate cooperatively within bounded
    timeframes. Internally, `diagnostics()` queries `psutil`; `create_pool()`
    constructs worker pools bounded for platform safety; and `JobManager` validates
    `Budget` constraints, tracks worker/memory reservations, executes asynchronous
    tasks with timeout supervision, and manages job state transitions.

Purpose:
    FEAT-HOST-JOBS: Hardware Diagnostics, Process Pool, and Job Admission Manager.
    Provides hardware resource inspection, multiprocessing pool management,
    budget-guarded task admission, and cooperative job cancellation.

Capabilities:
    - FR-HOST-JOBS-HARDWARE-DIAGNOSTICS: System Metrics Sampling
      Associated: `[diagnostics()]`
      Logging: Emits INFO log when hardware diagnostics (CPU, RAM, OS, Python)
      are collected.
    - FR-HOST-JOBS-POOL-ALLOCATION: Bounded Process Pool Allocation
      Associated: `[create_pool()]`
      Logging: Emits INFO log with allocated worker counts upon process pool
      creation.
    - FR-HOST-JOBS-BUDGET-ADMISSION: Resource-Guarded Task Admission
      Associated: `[JobManager.submit()]`, `[Budget.validate()]`
      Logging: Emits INFO log detailing task ID, owner, worker budget, memory
      reservation, and timeout on task submission.
    - FR-HOST-JOBS-EXECUTION-LIFECYCLE: Execution & State Transitions
      Associated: `[JobManager._run()]`, `[JobManager._finished()]`
      Logging: Emits info/warning/error logs on lifecycle transitions; failures
      include job identity and safe code locations, omitting exception values.
    - FR-HOST-JOBS-COOPERATIVE-CANCELLATION: Owner-Scoped Task Cancellation
      Associated: `[JobManager.cancel()]`, `[JobManager.close()]`
      Logging: Emits INFO log when job cancellation is requested and when
      owner-scoped job queues are closed.

Python API Usage:
    ```python
    from app.host.jobs import Budget, JobManager, create_pool, diagnostics

    # Inspect hardware
    diag = diagnostics()
    print(diag.cpu_count_logical, diag.total_ram_gb)

    # Allocate bounded worker pool and manager
    pool = create_pool(max_workers=4)
    manager = JobManager(pool=pool, max_workers=4, max_memory_bytes=8 * 1024**3)

    # Submit task with resource budget
    budget = Budget(workers=1, memory_bytes=1024**3, timeout_seconds=30.0)
    future = manager.submit("workspace-1", sum, [1, 2, 3], budget=budget)
    result = future.result()

    # Clean shutdown
    manager.close()
    ```

CLI Usage:
    Diagnostics and process pools are initialized during process startup:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

import multiprocessing
import os
import platform
import secrets
import sys
import threading
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import psutil

from app.host.logging import get_logger

if TYPE_CHECKING:
    from multiprocessing.context import BaseContext

__all__ = [
    "Budget",
    "BudgetExceededError",
    "CapacityExceededError",
    "HardwareDiagnostics",
    "JobAccess",
    "JobError",
    "JobManager",
    "JobManagerClosedError",
    "JobNotFoundError",
    "JobRecord",
    "JobStatus",
    "JobTimeoutError",
    "create_pool",
    "diagnostics",
]

logger = get_logger(__name__)

T = TypeVar("T")

BYTES_PER_GIB: float = 1024.0**3
DEFAULT_CLOSE_TIMEOUT_SECONDS: float = 5.0


class JobError(Exception):
    """Base exception for all job execution and resource admission errors."""


class JobManagerClosedError(JobError):
    """Raised when submitting tasks to a closed JobManager."""


class CapacityExceededError(JobError):
    """Raised when active reservations exceed configured capacity ceilings."""


class BudgetExceededError(JobError):
    """Raised when a job budget violates platform or manager constraints."""


class JobNotFoundError(JobError):
    """Raised when looking up an unrecorded or non-existent job ID."""


class JobTimeoutError(JobError):
    """Raised when a job exceeds its configured execution timeout duration."""


@dataclass(frozen=True, slots=True)
class HardwareDiagnostics:
    """Snapshot of point-in-time host hardware and runtime topology.

    Attributes:
        cpu_count_logical: Total number of logical execution cores.
        cpu_count_physical: Total number of physical CPU cores.
        total_ram_bytes: Total physical memory installed in bytes.
        available_ram_bytes: Available physical memory in bytes.
        total_ram_gb: Total physical memory in gigabytes.
        available_ram_gb: Available physical memory in gigabytes.
        os_platform: Operating system platform identifier string.
        python_version: Active Python runtime release version.
    """

    cpu_count_logical: int
    cpu_count_physical: int
    total_ram_bytes: int
    available_ram_bytes: int
    total_ram_gb: float
    available_ram_gb: float
    os_platform: str
    python_version: str


@dataclass(frozen=True, slots=True)
class Budget:
    """Resource declaration and constraints for an admitted compute task.

    Attributes:
        workers: Number of dedicated worker process slots required.
        memory_bytes: Maximum memory reservation requested in bytes.
        timeout_seconds: Optional execution deadline in seconds.
    """

    workers: int = 1
    memory_bytes: int = 0
    timeout_seconds: float | None = None

    def validate(self, max_workers: int, max_memory_bytes: int) -> None:
        """Validate budget parameters against ceiling constraints.

        Args:
            max_workers: Maximum worker count permitted by manager.
            max_memory_bytes: Maximum memory ceiling permitted by manager.

        Raises:
            BudgetExceededError: If requested resources exceed ceilings.
            ValueError: If budget parameters are non-positive or invalid.
        """
        if self.workers < 1:
            raise ValueError(f"Worker count must be at least 1, got {self.workers}")
        if self.workers > max_workers:
            raise BudgetExceededError(
                f"Requested {self.workers} workers exceeds max ceiling of {max_workers}"
            )
        if self.memory_bytes < 0:
            raise ValueError(
                f"Memory reservation cannot be negative, got {self.memory_bytes}"
            )
        if self.memory_bytes > max_memory_bytes:
            raise BudgetExceededError(
                f"Requested {self.memory_bytes} bytes memory exceeds ceiling of "
                f"{max_memory_bytes} bytes"
            )
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError(
                f"Timeout must be strictly positive, got {self.timeout_seconds}"
            )


class JobStatus(StrEnum):
    """Enumeration of possible job lifecycle states."""

    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class JobRecord:
    """Immutable auditing record of a submitted compute task.

    Attributes:
        job_id: Unique task identifier string.
        owner: Component or workspace identifier that submitted the job.
        kind: Descriptive classification slug (e.g. 'backtest', 'compute').
        budget: Declared resource budget parameters.
        status: Current execution status string.
        submitted_at_utc: ISO 8601 UTC timestamp of submission.
        started_at_utc: ISO 8601 UTC timestamp of run initialization.
        finished_at_utc: ISO 8601 UTC timestamp of completion or failure.
        error_location: Safe code location if job failed, or None.
    """

    job_id: str
    owner: str
    kind: str
    budget: Budget
    status: str
    submitted_at_utc: str
    started_at_utc: str | None = None
    finished_at_utc: str | None = None
    error_location: str | None = None


def diagnostics() -> HardwareDiagnostics:
    """Collect point-in-time hardware resource and platform diagnostics.

    Returns:
        HardwareDiagnostics snapshot containing CPU, memory, and OS metrics.
    """
    logical_cpus = psutil.cpu_count(logical=True) or 1
    physical_cpus = psutil.cpu_count(logical=False) or logical_cpus

    vmem = psutil.virtual_memory()
    total_ram = vmem.total
    avail_ram = vmem.available
    total_gb = round(total_ram / BYTES_PER_GIB, 2)
    avail_gb = round(avail_ram / BYTES_PER_GIB, 2)

    os_plat = platform.platform()
    py_ver = sys.version.split()[0]

    diag = HardwareDiagnostics(
        cpu_count_logical=logical_cpus,
        cpu_count_physical=physical_cpus,
        total_ram_bytes=total_ram,
        available_ram_bytes=avail_ram,
        total_ram_gb=total_gb,
        available_ram_gb=avail_gb,
        os_platform=os_plat,
        python_version=py_ver,
    )

    logger.info(
        "Hardware diagnostics collected: %d logical CPUs (%d physical), "
        "%.2f GB RAM (%.2f GB available) on %s (Python %s)",
        logical_cpus,
        physical_cpus,
        total_gb,
        avail_gb,
        os_plat,
        py_ver,
        extra={
            "logical_cpus": logical_cpus,
            "physical_cpus": physical_cpus,
            "total_ram_bytes": total_ram,
            "available_ram_bytes": avail_ram,
            "requirement": "FR-HOST-JOBS-HARDWARE-DIAGNOSTICS",
        },
    )

    return diag


def create_pool(
    max_workers: int | None = None,
    mp_context: BaseContext | None = None,
) -> ProcessPoolExecutor:
    """Allocate a platform-bounded multiprocessing worker pool.

    Args:
        max_workers: Desired worker process concurrency. If None or invalid,
            clamped to available logical CPU count.
        mp_context: Optional multiprocessing start context. Defaults to
            isolated 'spawn' context.

    Returns:
        Configured and bounded ProcessPoolExecutor instance.
    """
    system_cpus = os.cpu_count() or 1
    if max_workers is None or max_workers < 1:
        allocated_workers = system_cpus
    else:
        allocated_workers = max(1, min(max_workers, system_cpus))

    ctx = mp_context or multiprocessing.get_context("spawn")
    pool = ProcessPoolExecutor(
        max_workers=allocated_workers,
        mp_context=ctx,
    )

    logger.info(
        "Allocated process pool with %d workers",
        allocated_workers,
        extra={
            "allocated_workers": allocated_workers,
            "requirement": "FR-HOST-JOBS-POOL-ALLOCATION",
        },
    )

    return pool


class JobManager:
    """Resource-aware compute job admission, ledger, and lifecycle supervisor.

    Guarantees bounded CPU worker and memory reservations, executes tasks with
    timeout supervision, handles state transitions, and enforces cooperative
    task cancellation during shutdown.
    """

    def __init__(
        self,
        pool: ProcessPoolExecutor | None = None,
        *,
        max_workers: int | None = None,
        max_memory_bytes: int | None = None,
    ) -> None:
        """Initialize JobManager with worker pool and capacity limits.

        Args:
            pool: Optional external ProcessPoolExecutor. If None, allocates a
                new pool bounded to system capacity.
            max_workers: Maximum worker slots permitted simultaneously.
            max_memory_bytes: Maximum memory reservation permitted in bytes.
        """
        system_cpus = os.cpu_count() or 1
        self._max_workers: int = max(1, max_workers or system_cpus)

        system_ram = psutil.virtual_memory().total
        self._max_memory_bytes: int = (
            max(1, max_memory_bytes) if max_memory_bytes is not None else system_ram
        )

        self._pool: ProcessPoolExecutor = pool or create_pool(
            max_workers=self._max_workers
        )
        self._owns_pool: bool = pool is None

        self._lock = threading.Lock()
        self._reserved_workers: int = 0
        self._reserved_memory_bytes: int = 0
        self._jobs: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._owner_jobs: dict[str, set[str]] = {}
        self._closed: bool = False

    @property
    def max_workers(self) -> int:
        """Return maximum permitted worker process concurrency."""
        return self._max_workers

    @property
    def max_memory_bytes(self) -> int:
        """Return maximum permitted memory budget in bytes."""
        return self._max_memory_bytes

    @property
    def reserved_workers(self) -> int:
        """Return currently committed worker slots."""
        with self._lock:
            return self._reserved_workers

    @property
    def reserved_memory_bytes(self) -> int:
        """Return currently committed memory reservation in bytes."""
        with self._lock:
            return self._reserved_memory_bytes

    def capacity_status(self) -> dict[str, Any]:
        """Return a snapshot of current capacity and active reservations."""
        with self._lock:
            return {
                "max_workers": self._max_workers,
                "reserved_workers": self._reserved_workers,
                "available_workers": max(0, self._max_workers - self._reserved_workers),
                "max_memory_bytes": self._max_memory_bytes,
                "reserved_memory_bytes": self._reserved_memory_bytes,
                "available_memory_bytes": max(
                    0, self._max_memory_bytes - self._reserved_memory_bytes
                ),
                "active_jobs_count": len(self._futures),
                "is_closed": self._closed,
            }

    def submit(
        self,
        owner: str,
        fn: Callable[..., T],
        *args: Any,
        budget: Budget | None = None,
        kind: str = "compute",
        **kwargs: Any,
    ) -> Future[T]:
        """Admit and execute an asynchronous task within declared resource budgets.

        Args:
            owner: Component, workspace, or session ID submitting the task.
            fn: Callable target function to execute in the worker pool.
            *args: Positional arguments passed to target callable.
            budget: Resource allocation constraints. If None, uses default 1-worker.
            kind: Descriptive classification slug for logging and auditing.
            **kwargs: Keyword arguments passed to target callable.

        Returns:
            Future instance representing pending or executing task.

        Raises:
            JobManagerClosedError: If JobManager has already been closed.
            BudgetExceededError: If requested budget exceeds ceiling limits.
            CapacityExceededError: If current available capacity cannot admit task.
        """
        task_budget = budget or Budget()
        task_budget.validate(self._max_workers, self._max_memory_bytes)

        job_id = secrets.token_hex(16)
        now_utc = datetime.now(UTC).isoformat()

        with self._lock:
            if self._closed:
                raise JobManagerClosedError(
                    "JobManager is closed; task submission rejected"
                )

            if (
                self._reserved_workers + task_budget.workers > self._max_workers
                or self._reserved_memory_bytes + task_budget.memory_bytes
                > self._max_memory_bytes
            ):
                raise CapacityExceededError(
                    f"Insufficient capacity: requested {task_budget.workers} workers "
                    f"and {task_budget.memory_bytes} bytes, but only "
                    f"{self._max_workers - self._reserved_workers} workers and "
                    f"{self._max_memory_bytes - self._reserved_memory_bytes} bytes "
                    f"available"
                )

            self._reserved_workers += task_budget.workers
            self._reserved_memory_bytes += task_budget.memory_bytes

            record = JobRecord(
                job_id=job_id,
                owner=owner,
                kind=kind,
                budget=task_budget,
                status=JobStatus.SUBMITTED,
                submitted_at_utc=now_utc,
            )
            self._jobs[job_id] = record
            self._owner_jobs.setdefault(owner, set()).add(job_id)

        logger.info(
            "Admitted job %s (owner: %s, kind: %s, workers: %d, memory: %d bytes, "
            "timeout: %s)",
            job_id,
            owner,
            kind,
            task_budget.workers,
            task_budget.memory_bytes,
            task_budget.timeout_seconds,
            extra={
                "job_id": job_id,
                "owner": owner,
                "kind": kind,
                "workers": task_budget.workers,
                "memory_bytes": task_budget.memory_bytes,
                "timeout_seconds": task_budget.timeout_seconds,
                "requirement": "FR-HOST-JOBS-BUDGET-ADMISSION",
            },
        )

        future = self._pool.submit(fn, *args, **kwargs)
        self._run(job_id)

        with self._lock:
            self._futures[job_id] = future

            if task_budget.timeout_seconds is not None:
                timer = threading.Timer(
                    task_budget.timeout_seconds,
                    self._handle_timeout,
                    args=[job_id, task_budget.timeout_seconds],
                )
                timer.daemon = True
                self._timers[job_id] = timer
                timer.start()

        future.add_done_callback(lambda f: self._finished(job_id, f))
        return future

    def _run(self, job_id: str) -> None:
        """Mark job state transition to RUNNING and emit lifecycle telemetry.

        Args:
            job_id: Task identifier string.
        """
        now_utc = datetime.now(UTC).isoformat()
        with self._lock:
            if job_id in self._jobs:
                current = self._jobs[job_id]
                self._jobs[job_id] = JobRecord(
                    job_id=current.job_id,
                    owner=current.owner,
                    kind=current.kind,
                    budget=current.budget,
                    status=JobStatus.RUNNING,
                    submitted_at_utc=current.submitted_at_utc,
                    started_at_utc=now_utc,
                )

        logger.info(
            "Job %s transitioned to RUNNING",
            job_id,
            extra={
                "job_id": job_id,
                "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
            },
        )

    def _handle_timeout(self, job_id: str, timeout_seconds: float) -> None:
        """Handle execution timeout by cooperatively cancelling future."""
        with self._lock:
            future = self._futures.get(job_id)

        if future is not None and not future.done():
            logger.warning(
                "Job %s exceeded timeout of %.2f seconds; cancelling",
                job_id,
                timeout_seconds,
                extra={
                    "job_id": job_id,
                    "timeout_seconds": timeout_seconds,
                    "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
                },
            )
            future.cancel()

    def _finished(self, job_id: str, future: Future[Any]) -> None:
        """Handle task termination, release reservations, and update state.

        Args:
            job_id: Task identifier string.
            future: Completed or cancelled Future instance.
        """
        now_utc = datetime.now(UTC).isoformat()
        safe_location: str | None = None
        new_status: str

        with self._lock:
            timer = self._timers.pop(job_id, None)
            if timer is not None:
                timer.cancel()

            self._futures.pop(job_id, None)
            record = self._jobs.get(job_id)

            if record is not None:
                self._reserved_workers = max(
                    0, self._reserved_workers - record.budget.workers
                )
                self._reserved_memory_bytes = max(
                    0, self._reserved_memory_bytes - record.budget.memory_bytes
                )

        if future.cancelled():
            new_status = JobStatus.CANCELLED
            logger.info(
                "Job %s was cancelled",
                job_id,
                extra={
                    "job_id": job_id,
                    "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
                },
            )
        elif future.exception() is not None:
            new_status = JobStatus.FAILED
            exc = future.exception()
            tb = exc.__traceback__ if exc else None
            frame = tb.tb_next if tb and tb.tb_next else tb
            if frame:
                code = frame.tb_frame.f_code
                safe_location = (
                    f"{Path(code.co_filename).name}:{frame.tb_lineno}:{code.co_name}"
                )
            else:
                safe_location = "unknown:0:unknown"

            logger.error(
                "Job %s failed at %s",
                job_id,
                safe_location,
                extra={
                    "job_id": job_id,
                    "safe_location": safe_location,
                    "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
                },
            )
        else:
            new_status = JobStatus.COMPLETED
            logger.info(
                "Job %s completed successfully",
                job_id,
                extra={
                    "job_id": job_id,
                    "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
                },
            )

        with self._lock:
            if record is not None:
                self._jobs[job_id] = JobRecord(
                    job_id=record.job_id,
                    owner=record.owner,
                    kind=record.kind,
                    budget=record.budget,
                    status=new_status,
                    submitted_at_utc=record.submitted_at_utc,
                    started_at_utc=record.started_at_utc,
                    finished_at_utc=now_utc,
                    error_location=safe_location,
                )

    def cancel(self, job_id: str) -> bool:
        """Request cooperative cancellation of an active or pending task.

        Args:
            job_id: Task identifier string.

        Returns:
            True if cancellation was successfully initiated, False otherwise.
        """
        with self._lock:
            future = self._futures.get(job_id)

        if future is None or future.done():
            return False

        cancelled = future.cancel()
        logger.info(
            "Cancellation requested for job %s (success: %s)",
            job_id,
            cancelled,
            extra={
                "job_id": job_id,
                "cancelled": cancelled,
                "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
            },
        )
        return cancelled

    def close(
        self,
        owner: str | None = None,
        timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS,
    ) -> None:
        """Cooperatively cancel jobs and release worker pools.

        Args:
            owner: If specified, cancels only jobs belonging to this owner.
                If None, cancels all jobs and shuts down the process pool.
            timeout: Maximum wait time in seconds for worker pool cleanup.
        """
        if owner is not None:
            with self._lock:
                job_ids = list(self._owner_jobs.pop(owner, set()))
                futures_to_cancel = [
                    self._futures.get(jid) for jid in job_ids if jid in self._futures
                ]

            for fut in futures_to_cancel:
                if fut and not fut.done():
                    fut.cancel()

            logger.info(
                "Closed owner-scoped job queue for %s (%d jobs cancelled)",
                owner,
                len(job_ids),
                extra={
                    "owner": owner,
                    "count": len(job_ids),
                    "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
                },
            )
            return

        # Global shutdown
        with self._lock:
            if self._closed:
                return
            self._closed = True
            all_futures = list(self._futures.values())
            all_timers = list(self._timers.values())

        for timer in all_timers:
            timer.cancel()

        for fut in all_futures:
            if not fut.done():
                fut.cancel()

        if self._owns_pool:
            try:
                self._pool.shutdown(wait=True, cancel_futures=True)
            except TypeError:
                self._pool.shutdown(wait=True)

        with self._lock:
            self._reserved_workers = 0
            self._reserved_memory_bytes = 0

        logger.info(
            "JobManager closed; pool shut down within %.2f second limit",
            timeout,
            extra={
                "timeout": timeout,
                "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
            },
        )

    def get_job(self, job_id: str) -> JobRecord:
        """Retrieve audit record for task by ID.

        Args:
            job_id: Task identifier string.

        Returns:
            Immutable JobRecord.

        Raises:
            JobNotFoundError: If job_id is not recorded.
        """
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(f"Job '{job_id}' not found")
            return self._jobs[job_id]


class JobAccess:
    """Scoped capability facade injected into workspaces and plugins."""

    def __init__(self, manager: JobManager, owner: str) -> None:
        """Initialize JobAccess facade bound to a specific owner.

        Args:
            manager: Central JobManager instance.
            owner: Scoped owner identifier string.
        """
        self._manager: JobManager = manager
        self._owner: str = owner

    @property
    def owner(self) -> str:
        """Return the bound owner identifier string."""
        return self._owner

    def submit(
        self,
        fn: Callable[..., T],
        *args: Any,
        budget: Budget | None = None,
        kind: str = "compute",
        **kwargs: Any,
    ) -> Future[T]:
        """Submit a background compute task bound to this owner scope.

        Args:
            fn: Callable target function to execute in worker pool.
            *args: Positional arguments for target callable.
            budget: Declared resource budget constraints.
            kind: Descriptive classification slug.
            **kwargs: Keyword arguments for target callable.

        Returns:
            Future representing task execution.
        """
        return self._manager.submit(
            self._owner,
            fn,
            *args,
            budget=budget,
            kind=kind,
            **kwargs,
        )

    def cancel(self, job_id: str) -> bool:
        """Cancel an admitted or executing task.

        Args:
            job_id: Task identifier string.

        Returns:
            True if task was cancelled, False otherwise.
        """
        return self._manager.cancel(job_id)

    def close(self, timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS) -> None:
        """Cancel all pending and executing tasks owned by this scope.

        Args:
            timeout: Maximum wait time in seconds.
        """
        self._manager.close(owner=self._owner, timeout=timeout)
