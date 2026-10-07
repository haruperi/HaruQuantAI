"""Hardware diagnostics, process pool allocation, and job admission coordinator.

Description:
    Provides point-in-time hardware resource diagnostics, background worker pool
    allocation, resource-bounded compute job admission, deduplicated scheduling,
    hierarchical parent-child tracking, checkpointed cooperative task cancellation,
    timeout supervision, durable SQLite state persistence, restart reconciliation,
    real-time event publication, and FastAPI REST transport routes for the
    HaruQuantAI platform host. It exists to guarantee bounded CPU and memory
    consumption, prevent out-of-memory crashes, enforce capacity limits across
    workspaces and plugins, and ensure orderly cooperative cancellation during
    component uninstallation or host shutdown.

    Externally, it participates in four key workflows: (1) `BootstrapCoordinator`
    calls `diagnostics()` during initialization to sample system RAM and CPU
    topology, builds a `JobManager` sized to host capacity, and creates a
    `ProcessPoolExecutor` via `create_pool()`; (2) `Composition` injects scoped
    `JobAccess` capability facades into workspaces and plugins, allowing quantitative
    modules (genetic algorithms, parameter optimization, Monte Carlo retesting) to
    offload compute tasks; (3) the host web shell interacts via `create_jobs_router()`
    to submit tasks, query job records, monitor capacity, and request cooperative
    cancellation; and (4) on process boot, `JobStore.reconcile_on_startup()`
    reconciles orphaned or in-flight jobs to `INTERRUPTED` without fabricating false
    success or hanging indefinitely.

    Internally, `diagnostics()` queries `psutil`; `create_pool()` constructs worker
    pools bounded for platform safety; `JobStore` persists job states and budgets to
    SQLite (`host_jobs` table); `JobContext` coordinates cooperative cancellation and
    incremental progress reporting; and `JobManager` validates `Budget` constraints,
    tracks worker/memory reservations, executes asynchronous tasks with timeout
    supervision, and broadcasts `jobs.changed` updates to the central `EventBus`.

Purpose:
    FEAT-HOST-JOBS: Hardware Diagnostics, Process Pool, and Job Admission Manager.
    Provides hardware resource inspection, worker pool management, budget-guarded
    task admission, deduplication, restart reconciliation, and cooperative cancellation.

Key Capabilities:
    - FR-HOST-JOBS-HARDWARE-DIAGNOSTICS: System Metrics Sampling
      Associated: `[diagnostics()]`
      Logging: Emits INFO log when hardware diagnostics (CPU, RAM, OS, Python)
      are collected.
    - FR-HOST-JOBS-POOL-ALLOCATION: Bounded Process Pool Allocation
      Associated: `[create_pool()]`
      Logging: Emits INFO log with allocated worker counts upon process pool creation.
    - FR-HOST-JOBS-BUDGET-ADMISSION: Resource-Guarded Task Admission
      Associated: `[JobManager.submit()]`, `[Budget.validate()]`
      Logging: Emits INFO log detailing task ID, owner, worker budget, memory
      reservation, and timeout on task submission.
    - FR-HOST-JOBS-EXECUTION-LIFECYCLE: Execution & State Transitions
      Associated: `[JobManager._run()]`, `[JobManager._finished()]`
      Logging: Emits info/warning/error logs on lifecycle transitions; failures
      include job identity and safe code locations, omitting exception secrets.
    - FR-HOST-JOBS-COOPERATIVE-CANCELLATION: Owner-Scoped Task Cancellation
      Associated: `[JobManager.cancel()]`, `[JobManager.close()]`,
      `[JobContext.check_cancellation()]`
      Logging: Emits INFO log when job cancellation is requested and when
      owner-scoped job queues are closed.
    - FR-HOST-JOBS-DEDUPLICATION: Active Duplicate Submission Prevention
      Associated: `[JobManager.submit()]`
      Logging: Emits INFO when dedup key is registered or released; WARNING when
      duplicate submission is rejected.
    - FR-HOST-JOBS-RESTART-RECONCILIATION: Startup Orphaned Job Reconciliation
      Associated: `[JobStore.reconcile_on_startup()]`
      Logging: Emits INFO when orphaned or active jobs from previous runs are
      reconciled to INTERRUPTED state.
    - FR-HOST-JOBS-EVENT-BROADCAST: Real-time Event Publication
      Associated: `[JobManager._publish_job_event()]`
      Logging: Emits DEBUG when job lifecycle updates and progress reports are
      broadcast to the EventBus.
    - FR-HOST-JOBS-REST-API: FastAPI HTTP and Management Router
      Associated: `[create_jobs_router()]`
      Logging: Emits DEBUG when jobs router is constructed and endpoints are invoked.

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
    Inspect diagnostics, capacity, and active jobs via the CLI entrypoint:
    ```bash
    uv run python -m app.host.jobs --diagnostics
    uv run python -m app.host.jobs --capacity
    uv run python -m app.host.jobs --list
    ```
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import platform
import secrets
import sqlite3
import sys
import threading
from collections.abc import Callable, Generator
from concurrent.futures import Executor, Future, ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, TypeVar, override

import psutil
from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse

if TYPE_CHECKING:
    from multiprocessing.context import BaseContext

    from app.host.transport import EventBus

__all__ = [
    "BYTES_PER_GIB",
    "DEFAULT_CLOSE_TIMEOUT_SECONDS",
    "DEFAULT_DATABASE_PATH",
    "Budget",
    "BudgetExceededError",
    "CapacityExceededError",
    "CapacityStatus",
    "DuplicateJobError",
    "HardwareDiagnostics",
    "JobAccess",
    "JobCancelledError",
    "JobContext",
    "JobError",
    "JobManager",
    "JobManagerClosedError",
    "JobNotFoundError",
    "JobProgress",
    "JobRecord",
    "JobRouterService",
    "JobStatus",
    "JobStore",
    "JobTimeoutError",
    "SubmitJobRequest",
    "create_jobs_router",
    "create_pool",
    "diagnostics",
    "main",
]

logger = get_logger(__name__)

T = TypeVar("T")

BYTES_PER_GIB: float = 1024.0**3
DEFAULT_CLOSE_TIMEOUT_SECONDS: float = 5.0
DEFAULT_DATABASE_PATH: Path = Path("data/database/haruquantai.db")


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class JobError(Exception):
    """Base exception for all job execution, budget, and coordination errors."""


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


class DuplicateJobError(JobError):
    """Raised when submitting a job with a dedup_key matching an active task."""


class JobCancelledError(JobError):
    """Raised when an operation is cancelled cooperatively during execution."""


# ==============================================================================
# Domain Enums & Models
# ==============================================================================


class JobStatus(StrEnum):
    """Enumeration of possible job lifecycle states.

    Values match frontend UI contract (ui/app/host/types.ts).
    """

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CANCELLATION_REQUESTED = "cancellation_requested"
    INTERRUPTED = "interrupted"

    # Aliases for legacy/alternative naming
    SUBMITTED = "queued"
    SUCCEEDED = "completed"


class HardwareDiagnostics(BaseModel):
    """Snapshot of point-in-time host hardware and runtime topology."""

    cpu_count_logical: int
    cpu_count_physical: int
    total_ram_bytes: int
    available_ram_bytes: int
    total_ram_gb: float
    available_ram_gb: float
    os_platform: str
    python_version: str


@dataclass(frozen=True)
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


class JobProgress(BaseModel):
    """Incremental progress metrics reported by an active task."""

    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    accepted: int = Field(default=0, ge=0)
    rejected: int = Field(default=0, ge=0)
    message: str = Field(default="")


class JobRecord(BaseModel):
    """Immutable auditing record of a submitted compute task."""

    job_id: str
    owner: str
    kind: str = "compute"
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    accepted: int = 0
    rejected: int = 0
    message: str = ""
    attempt_id: int = 1
    max_retries: int = 0
    retry_count: int = 0
    dedup_key: str | None = None
    parent_job_id: str | None = None
    child_job_ids: list[str] = Field(default_factory=list)
    budget: Budget = Field(default_factory=Budget)
    submitted_at_utc: str
    started_at_utc: str | None = None
    finished_at_utc: str | None = None
    error_message: str | None = None
    error_location: str | None = None


class CapacityStatus(BaseModel):
    """Snapshot of current capacity and active reservations."""

    max_workers: int
    reserved_workers: int
    available_workers: int
    max_memory_bytes: int
    reserved_memory_bytes: int
    available_memory_bytes: int
    active_jobs_count: int
    is_closed: bool


class SubmitJobRequest(BaseModel):
    """REST API payload specification for task submission."""

    owner: str = "default"
    kind: str = "compute"
    workers: int = Field(default=1, ge=1)
    memory_bytes: int = Field(default=0, ge=0)
    timeout_seconds: float | None = Field(default=None, gt=0.0)
    dedup_key: str | None = None
    parent_job_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# Hardware Diagnostics & Pool Allocation
# ==============================================================================


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


# ==============================================================================
# Job Context (Cooperative Cancellation & Progress)
# ==============================================================================


class JobContext:
    """Scoped execution context coordinating cancellation and progress reporting."""

    def __init__(
        self,
        job_id: str,
        attempt_id: int = 1,
        manager: JobManager | None = None,
    ) -> None:
        """Initialize JobContext for an active task.

        Args:
            job_id: Task identifier string.
            attempt_id: Monotonic attempt count for this execution.
            manager: Central JobManager instance for progress reporting.
        """
        self.job_id: str = job_id
        self.attempt_id: int = attempt_id
        self._manager: JobManager | None = manager
        self._cancellation_requested = threading.Event()

    @override
    def __getstate__(self) -> dict[str, Any]:
        """Exclude unpickleable manager reference during process IPC."""
        state = self.__dict__.copy()
        state["_manager"] = None
        return state

    @property
    def is_cancellation_requested(self) -> bool:
        """Return True if cooperative cancellation was requested."""
        return self._cancellation_requested.is_set()

    def request_cancellation(self) -> None:
        """Signal cooperative cancellation to this task."""
        self._cancellation_requested.set()

    def check_cancellation(self) -> None:
        """Raise JobCancelledError if cancellation was requested.

        Raises:
            JobCancelledError: If cancellation was signaled.
        """
        if self.is_cancellation_requested:
            logger.info(
                "Task %s acknowledged cooperative cancellation checkpoint",
                self.job_id,
                extra={
                    "job_id": self.job_id,
                    "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
                },
            )
            raise JobCancelledError(f"Job '{self.job_id}' was cancelled cooperatively.")

    def report_progress(
        self,
        progress: float,
        *,
        accepted: int = 0,
        rejected: int = 0,
        message: str = "",
    ) -> None:
        """Report incremental progress back to the JobManager and EventBus.

        Args:
            progress: Completion percentage (0.0 to 100.0).
            accepted: Accepted items metric count.
            rejected: Rejected items metric count.
            message: Informational status message.
        """
        if self._manager is not None:
            self._manager.report_progress(
                self.job_id,
                progress=progress,
                accepted=accepted,
                rejected=rejected,
                message=message,
            )


# ==============================================================================
# SQLite Durability & Startup Reconciliation
# ==============================================================================


class JobStore:
    """Authoritative SQLite persistence manager for job records.

    Provides transactional, parameterized CRUD operations against the `host_jobs`
    table and startup reconciliation for interrupted jobs.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        busy_timeout: float = 5.0,
    ) -> None:
        """Initialize JobStore with a database path.

        Args:
            db_path: Optional path to SQLite file or ':memory:'. Defaults to
                'data/database/haruquantai.db'.
            busy_timeout: Lock timeout in seconds.
        """
        self._is_memory = str(db_path) == ":memory:"
        self._db_path = (
            Path(db_path).resolve()
            if db_path and not self._is_memory
            else (None if self._is_memory else DEFAULT_DATABASE_PATH.resolve())
        )
        self._busy_timeout = busy_timeout
        self._lock = threading.Lock()
        self._mem_conn: sqlite3.Connection | None = (
            sqlite3.connect(":memory:", check_same_thread=False)
            if self._is_memory
            else None
        )
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row

    @property
    def db_path(self) -> Path | str:
        """Return the resolved database path or ':memory:'."""
        return ":memory:" if self._is_memory else (self._db_path or "")

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        """Context manager providing thread-safe SQLite connection."""
        with self._lock:
            if self._is_memory and self._mem_conn:
                yield self._mem_conn
            else:
                if self._db_path is None:
                    raise RuntimeError("Database path cannot be None for persistent db")
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(
                    self._db_path,
                    timeout=self._busy_timeout,
                    autocommit=True,
                )
                conn.row_factory = sqlite3.Row
                try:
                    conn.execute(
                        f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)}"
                    )
                    conn.execute("PRAGMA foreign_keys = ON")
                    yield conn
                finally:
                    conn.close()

    def initialize(self) -> None:
        """Ensure host_jobs schema and indexes exist."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_jobs (
                    job_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0.0,
                    accepted INTEGER NOT NULL DEFAULT 0,
                    rejected INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL DEFAULT '',
                    attempt_id INTEGER NOT NULL DEFAULT 1,
                    max_retries INTEGER NOT NULL DEFAULT 0,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    dedup_key TEXT,
                    parent_job_id TEXT,
                    child_job_ids_json TEXT NOT NULL DEFAULT '[]',
                    budget_json TEXT NOT NULL,
                    submitted_at_utc TEXT NOT NULL,
                    started_at_utc TEXT,
                    finished_at_utc TEXT,
                    error_message TEXT,
                    error_location TEXT
                );
                """
            )
            # Ensure backward-compatibility if legacy table exists
            table_info = conn.execute("PRAGMA table_info(host_jobs);").fetchall()
            cols = {r["name"] for r in table_info}
            required_cols = {
                "owner": "TEXT NOT NULL DEFAULT 'default'",
                "kind": "TEXT NOT NULL DEFAULT 'compute'",
                "progress": "REAL NOT NULL DEFAULT 0.0",
                "accepted": "INTEGER NOT NULL DEFAULT 0",
                "rejected": "INTEGER NOT NULL DEFAULT 0",
                "message": "TEXT NOT NULL DEFAULT ''",
                "attempt_id": "INTEGER NOT NULL DEFAULT 1",
                "max_retries": "INTEGER NOT NULL DEFAULT 0",
                "retry_count": "INTEGER NOT NULL DEFAULT 0",
                "dedup_key": "TEXT",
                "parent_job_id": "TEXT",
                "child_job_ids_json": "TEXT NOT NULL DEFAULT '[]'",
                "budget_json": "TEXT NOT NULL DEFAULT '{}'",
                "submitted_at_utc": "TEXT NOT NULL DEFAULT ''",
                "error_message": "TEXT",
                "error_location": "TEXT",
            }
            for col_name, col_def in required_cols.items():
                if col_name not in cols:
                    conn.execute(
                        f"ALTER TABLE host_jobs ADD COLUMN {col_name} {col_def};"
                    )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_owner ON host_jobs(owner);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_status ON host_jobs(status);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_jobs_dedup "
                "ON host_jobs(dedup_key);"
            )

    def upsert_job(self, record: JobRecord) -> None:
        """Insert or replace a job record.

        Args:
            record: JobRecord model instance to persist.
        """
        self.initialize()
        budget_dict = (
            asdict(record.budget)
            if is_dataclass(record.budget)
            else record.budget.__dict__
        )
        budget_json = json.dumps(budget_dict)
        child_json = json.dumps(record.child_job_ids)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO host_jobs (
                    job_id, owner, kind, status, progress, accepted, rejected,
                    message, attempt_id, max_retries, retry_count, dedup_key,
                    parent_job_id, child_job_ids_json, budget_json, submitted_at_utc,
                    started_at_utc, finished_at_utc, error_message, error_location
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                );
                """,
                (
                    record.job_id,
                    record.owner,
                    record.kind,
                    str(record.status),
                    record.progress,
                    record.accepted,
                    record.rejected,
                    record.message,
                    record.attempt_id,
                    record.max_retries,
                    record.retry_count,
                    record.dedup_key,
                    record.parent_job_id,
                    child_json,
                    budget_json,
                    record.submitted_at_utc,
                    record.started_at_utc,
                    record.finished_at_utc,
                    record.error_message,
                    record.error_location,
                ),
            )

    def get_job(self, job_id: str) -> JobRecord | None:
        """Query job record by job_id.

        Args:
            job_id: Task identifier string.

        Returns:
            JobRecord instance if found, None otherwise.
        """
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM host_jobs WHERE job_id = ?;", (job_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_record(row)

    def list_jobs(
        self,
        owner: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[JobRecord]:
        """List job records matching optional filters.

        Args:
            owner: Filter by owner identifier.
            status: Filter by job lifecycle status.
            limit: Maximum records to return.

        Returns:
            List of matching JobRecord instances.
        """
        self.initialize()
        params: list[Any] = []
        if owner is not None and status is not None:
            query = (
                "SELECT * FROM host_jobs WHERE owner = ? AND status = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [owner, str(status), limit]
        elif owner is not None:
            query = (
                "SELECT * FROM host_jobs WHERE owner = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [owner, limit]
        elif status is not None:
            query = (
                "SELECT * FROM host_jobs WHERE status = ? "
                "ORDER BY submitted_at_utc DESC LIMIT ?;"
            )
            params = [str(status), limit]
        else:
            query = "SELECT * FROM host_jobs ORDER BY submitted_at_utc DESC LIMIT ?;"
            params = [limit]

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def reconcile_on_startup(self) -> int:
        """Reconcile uncompleted jobs from previous runs to INTERRUPTED state.

        Returns:
            Count of reconciled jobs.
        """
        self.initialize()
        now_utc = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE host_jobs
                SET status = 'interrupted',
                    finished_at_utc = ?,
                    error_message = ?
                WHERE status IN ('queued', 'running', 'cancellation_requested');
                """,
                (now_utc, "Host restarted while job was in-flight."),
            )
            count = cursor.rowcount

        if count > 0:
            logger.info(
                "Startup reconciliation: marked %d orphaned jobs as INTERRUPTED",
                count,
                extra={
                    "reconciled_count": count,
                    "requirement": "FR-HOST-JOBS-RESTART-RECONCILIATION",
                },
            )
        return count

    def _row_to_record(self, row: sqlite3.Row) -> JobRecord:
        """Convert SQLite row to typed JobRecord model."""
        budget_data = json.loads(row["budget_json"])
        child_ids = json.loads(row["child_job_ids_json"])
        return JobRecord(
            job_id=row["job_id"],
            owner=row["owner"],
            kind=row["kind"],
            status=JobStatus(row["status"]),
            progress=float(row["progress"]),
            accepted=int(row["accepted"]),
            rejected=int(row["rejected"]),
            message=row["message"],
            attempt_id=int(row["attempt_id"]),
            max_retries=int(row["max_retries"]),
            retry_count=int(row["retry_count"]),
            dedup_key=row["dedup_key"],
            parent_job_id=row["parent_job_id"],
            child_job_ids=child_ids,
            budget=Budget(**budget_data),
            submitted_at_utc=row["submitted_at_utc"],
            started_at_utc=row["started_at_utc"],
            finished_at_utc=row["finished_at_utc"],
            error_message=row["error_message"],
            error_location=row["error_location"],
        )


# ==============================================================================
# Central JobManager Coordinator
# ==============================================================================


class JobManager:
    """Resource-aware compute job admission, ledger, and lifecycle supervisor.

    Guarantees bounded CPU worker and memory reservations, executes tasks with
    timeout supervision, handles state transitions, coordinates cooperative
    cancellation, persists records to SQLite, and broadcasts real-time events.
    """

    def __init__(
        self,
        pool: Executor | None = None,
        *,
        max_workers: int | None = None,
        max_memory_bytes: int | None = None,
        db_path: Path | str | None = None,
        event_bus: EventBus | None = None,
        auto_reconcile: bool = True,
    ) -> None:
        """Initialize JobManager with worker pool and capacity limits.

        Args:
            pool: Optional external Executor (e.g. ProcessPoolExecutor or
                ThreadPoolExecutor). If None, allocates a new process pool.
            max_workers: Maximum worker slots permitted simultaneously.
            max_memory_bytes: Maximum memory reservation permitted in bytes.
            db_path: Optional SQLite storage path or ':memory:'.
            event_bus: Optional central EventBus for real-time broadcasts.
            auto_reconcile: If True, reconciles orphaned jobs on initialization.
        """
        system_cpus = os.cpu_count() or 1
        self._max_workers: int = max(1, max_workers or system_cpus)

        system_ram = psutil.virtual_memory().total
        self._max_memory_bytes: int = (
            max(1, max_memory_bytes) if max_memory_bytes is not None else system_ram
        )

        self._pool: Executor = pool or create_pool(max_workers=self._max_workers)
        self._owns_pool: bool = pool is None

        self._store = JobStore(db_path=db_path)
        self._store.initialize()

        self._event_bus = event_bus
        self._handlers: dict[str, Callable[..., Any]] = {}

        self._lock = threading.Lock()
        self._reserved_workers: int = 0
        self._reserved_memory_bytes: int = 0
        self._jobs: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._future_to_job: dict[Future[Any], str] = {}
        self._contexts: dict[str, JobContext] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._owner_jobs: dict[str, set[str]] = {}
        self._active_dedup_keys: dict[str, str] = {}
        self._closed: bool = False

        if auto_reconcile:
            self._store.reconcile_on_startup()

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

    @property
    def store(self) -> JobStore:
        """Return underlying JobStore instance."""
        return self._store

    def register_handler(self, kind: str, handler: Callable[..., Any]) -> None:
        """Register a named callable task handler for REST submission.

        Args:
            kind: Unique job classification slug.
            handler: Callable target function.
        """
        with self._lock:
            self._handlers[kind] = handler

    def get_handler(self, kind: str) -> Callable[..., Any] | None:
        """Return registered task handler for the given job kind if registered."""
        with self._lock:
            return self._handlers.get(kind)

    def get_job_id_for_future(self, future: Future[Any]) -> str | None:
        """Return job ID associated with an active future if available."""
        with self._lock:
            return self._future_to_job.get(future)

    def capacity_status(self) -> CapacityStatus:
        """Return a snapshot of current capacity and active reservations.

        Returns:
            CapacityStatus model instance.
        """
        with self._lock:
            return CapacityStatus(
                max_workers=self._max_workers,
                reserved_workers=self._reserved_workers,
                available_workers=max(0, self._max_workers - self._reserved_workers),
                max_memory_bytes=self._max_memory_bytes,
                reserved_memory_bytes=self._reserved_memory_bytes,
                available_memory_bytes=max(
                    0, self._max_memory_bytes - self._reserved_memory_bytes
                ),
                active_jobs_count=len(self._futures),
                is_closed=self._closed,
            )

    def submit(
        self,
        owner: str,
        fn: Callable[..., T],
        *args: Any,
        budget: Budget | None = None,
        kind: str = "compute",
        dedup_key: str | None = None,
        parent_job_id: str | None = None,
        pass_context: bool = False,
        **kwargs: Any,
    ) -> Future[T]:
        """Admit and execute an asynchronous task within declared resource budgets.

        Args:
            owner: Component, workspace, or session ID submitting the task.
            fn: Callable target function to execute in the worker pool.
            *args: Positional arguments passed to target callable.
            budget: Resource allocation constraints. If None, uses default 1-worker.
            kind: Descriptive classification slug for logging and auditing.
            dedup_key: Optional uniqueness key preventing duplicate concurrent tasks.
            parent_job_id: Optional parent job ID to establish hierarchy.
            pass_context: If True, passes JobContext as 'context' kwarg to fn.
            **kwargs: Keyword arguments passed to target callable.

        Returns:
            Future instance representing pending or executing task.

        Raises:
            JobManagerClosedError: If JobManager has already been closed.
            BudgetExceededError: If requested budget exceeds ceiling limits.
            CapacityExceededError: If current available capacity cannot admit task.
            DuplicateJobError: If active job with identical dedup_key is running.
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

            # Deduplication check
            if dedup_key is not None:
                if dedup_key in self._active_dedup_keys:
                    active_id = self._active_dedup_keys[dedup_key]
                    logger.warning(
                        "Rejected duplicate job submission for key '%s'; "
                        "active job: %s",
                        dedup_key,
                        active_id,
                        extra={
                            "dedup_key": dedup_key,
                            "active_job_id": active_id,
                            "requirement": "FR-HOST-JOBS-DEDUPLICATION",
                        },
                    )
                    raise DuplicateJobError(
                        f"Job with dedup_key '{dedup_key}' is active: {active_id}"
                    )
                self._active_dedup_keys[dedup_key] = job_id
                logger.info(
                    "Registered dedup_key '%s' for job %s",
                    dedup_key,
                    job_id,
                    extra={
                        "dedup_key": dedup_key,
                        "job_id": job_id,
                        "requirement": "FR-HOST-JOBS-DEDUPLICATION",
                    },
                )

            # Capacity check
            if (
                self._reserved_workers + task_budget.workers > self._max_workers
                or self._reserved_memory_bytes + task_budget.memory_bytes
                > self._max_memory_bytes
            ):
                if dedup_key is not None:
                    self._active_dedup_keys.pop(dedup_key, None)
                raise CapacityExceededError(
                    f"Insufficient capacity: requested {task_budget.workers} workers "
                    f"and {task_budget.memory_bytes} bytes, but only "
                    f"{self._max_workers - self._reserved_workers} workers and "
                    f"{self._max_memory_bytes - self._reserved_memory_bytes} bytes "
                    f"available"
                )

            self._reserved_workers += task_budget.workers
            self._reserved_memory_bytes += task_budget.memory_bytes

            context = JobContext(job_id=job_id, manager=self)
            self._contexts[job_id] = context

            record = JobRecord(
                job_id=job_id,
                owner=owner,
                kind=kind,
                budget=task_budget,
                status=JobStatus.QUEUED,
                dedup_key=dedup_key,
                parent_job_id=parent_job_id,
                submitted_at_utc=now_utc,
            )
            self._jobs[job_id] = record
            self._owner_jobs.setdefault(owner, set()).add(job_id)

            # Establish parent-child link if parent exists
            if parent_job_id and parent_job_id in self._jobs:
                parent_rec = self._jobs[parent_job_id]
                new_children = [*parent_rec.child_job_ids, job_id]
                self._jobs[parent_job_id] = parent_rec.model_copy(
                    update={"child_job_ids": new_children}
                )
                self._store.upsert_job(self._jobs[parent_job_id])

        self._store.upsert_job(record)
        self._publish_job_event(record)

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

        call_kwargs = dict(kwargs)
        if pass_context:
            call_kwargs["context"] = context

        self._run(job_id)
        future = self._pool.submit(fn, *args, **call_kwargs)

        with self._lock:
            self._futures[job_id] = future
            self._future_to_job[future] = job_id

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
                updated = current.model_copy(
                    update={
                        "status": JobStatus.RUNNING,
                        "started_at_utc": now_utc,
                    }
                )
                self._jobs[job_id] = updated
                self._store.upsert_job(updated)
                self._publish_job_event(updated)

        logger.info(
            "Job %s transitioned to RUNNING",
            job_id,
            extra={
                "job_id": job_id,
                "requirement": "FR-HOST-JOBS-EXECUTION-LIFECYCLE",
            },
        )

    def report_progress(
        self,
        job_id: str,
        *,
        progress: float,
        accepted: int = 0,
        rejected: int = 0,
        message: str = "",
    ) -> None:
        """Update job progress and publish telemetry update.

        Args:
            job_id: Task identifier string.
            progress: Completion percentage (0.0 to 100.0).
            accepted: Accepted items metric count.
            rejected: Rejected items metric count.
            message: Informational progress string.
        """
        clamped_progress = max(0.0, min(100.0, progress))
        with self._lock:
            if job_id in self._jobs:
                current = self._jobs[job_id]
                updated = current.model_copy(
                    update={
                        "progress": clamped_progress,
                        "accepted": accepted,
                        "rejected": rejected,
                        "message": message,
                    }
                )
                self._jobs[job_id] = updated
                self._store.upsert_job(updated)
                self._publish_job_event(updated)

    def _handle_timeout(self, job_id: str, timeout_seconds: float) -> None:
        """Handle execution timeout by cooperatively cancelling future."""
        with self._lock:
            future = self._futures.get(job_id)
            context = self._contexts.get(job_id)

        if context is not None:
            context.request_cancellation()

        cancelled = False
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
            cancelled = future.cancel()

        if not cancelled:
            with self._lock:
                record = self._jobs.get(job_id)
                if record is not None and record.status in (
                    JobStatus.QUEUED,
                    JobStatus.RUNNING,
                    JobStatus.CANCELLATION_REQUESTED,
                ):
                    updated = record.model_copy(
                        update={
                            "status": JobStatus.CANCELLED,
                            "error_message": "JobTimeoutError",
                        }
                    )
                    self._jobs[job_id] = updated
                    self._store.upsert_job(updated)
                    self._publish_job_event(updated)

    def _finished(self, job_id: str, future: Future[Any]) -> None:
        """Handle task termination, release reservations, and update state.

        Args:
            job_id: Task identifier string.
            future: Completed or cancelled Future instance.
        """
        now_utc = datetime.now(UTC).isoformat()
        safe_location: str | None = None
        error_msg: str | None = None
        new_status: JobStatus

        with self._lock:
            timer = self._timers.pop(job_id, None)
            if timer is not None:
                timer.cancel()

            self._futures.pop(job_id, None)
            self._contexts.pop(job_id, None)
            record = self._jobs.get(job_id)

            if record is not None:
                self._reserved_workers = max(
                    0, self._reserved_workers - record.budget.workers
                )
                self._reserved_memory_bytes = max(
                    0, self._reserved_memory_bytes - record.budget.memory_bytes
                )
                if record.dedup_key is not None:
                    self._active_dedup_keys.pop(record.dedup_key, None)
                    logger.info(
                        "Released dedup_key '%s' for completed job %s",
                        record.dedup_key,
                        job_id,
                        extra={
                            "dedup_key": record.dedup_key,
                            "job_id": job_id,
                            "requirement": "FR-HOST-JOBS-DEDUPLICATION",
                        },
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
            exc = future.exception()
            if isinstance(exc, JobCancelledError):
                new_status = JobStatus.CANCELLED
                logger.info(
                    "Job %s was cancelled cooperatively",
                    job_id,
                    extra={
                        "job_id": job_id,
                        "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
                    },
                )
            else:
                new_status = JobStatus.FAILED
                error_msg = exc.__class__.__name__ if exc else "ExecutionError"
                tb = exc.__traceback__ if exc else None
                while tb and tb.tb_next:
                    tb = tb.tb_next
                if tb:
                    code = tb.tb_frame.f_code
                    safe_location = (
                        f"{Path(code.co_filename).name}:{tb.tb_lineno}:{code.co_name}"
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
                updated = record.model_copy(
                    update={
                        "status": new_status,
                        "progress": 100.0
                        if new_status == JobStatus.COMPLETED
                        else record.progress,
                        "finished_at_utc": now_utc,
                        "error_message": error_msg,
                        "error_location": safe_location,
                    }
                )
                self._jobs[job_id] = updated
                self._store.upsert_job(updated)
                self._publish_job_event(updated)

    def cancel(self, job_id: str) -> bool:
        """Request cooperative cancellation of an active or pending task.

        Args:
            job_id: Task identifier string.

        Returns:
            True if cancellation was successfully initiated, False otherwise.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return False

            if record.status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.INTERRUPTED,
            ):
                return False

            future = self._futures.get(job_id)
            context = self._contexts.get(job_id)

            if context is not None:
                context.request_cancellation()

            if record.status == JobStatus.RUNNING:
                updated = record.model_copy(
                    update={"status": JobStatus.CANCELLATION_REQUESTED}
                )
                self._jobs[job_id] = updated
                self._store.upsert_job(updated)
                self._publish_job_event(updated)

        cancelled = False
        if future is not None:
            cancelled = future.cancel()

        logger.info(
            "Cancellation requested for job %s (future_cancelled: %s)",
            job_id,
            cancelled,
            extra={
                "job_id": job_id,
                "cancelled": cancelled,
                "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
            },
        )
        return True

    def _close_owner(self, owner: str) -> None:
        """Cancel jobs belonging to a specific owner scope."""
        with self._lock:
            job_ids = list(self._owner_jobs.pop(owner, set()))
            futures_to_cancel = [
                self._futures.get(jid) for jid in job_ids if jid in self._futures
            ]
            contexts_to_cancel = [
                self._contexts.get(jid) for jid in job_ids if jid in self._contexts
            ]

        for ctx in contexts_to_cancel:
            if ctx is not None:
                ctx.request_cancellation()

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

    def _close_global(self, timeout: float) -> None:
        """Cancel all running jobs and cleanly terminate the worker pool."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            all_futures = list(self._futures.values())
            all_timers = list(self._timers.values())
            all_contexts = list(self._contexts.values())

        for ctx in all_contexts:
            ctx.request_cancellation()

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
            self._active_dedup_keys.clear()

        logger.info(
            "JobManager closed; pool shut down within %.2f second limit",
            timeout,
            extra={
                "timeout": timeout,
                "requirement": "FR-HOST-JOBS-COOPERATIVE-CANCELLATION",
            },
        )

    def close(
        self,
        owner: str | None = None,
        timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS,
    ) -> None:
        """Cooperatively cancel jobs and release worker pools.

        Args:
            owner: If specified, cancels only jobs belonging to this owner.
                If None, cancels all jobs and shuts down the worker pool.
            timeout: Maximum wait time in seconds for worker pool cleanup.
        """
        if owner is not None:
            self._close_owner(owner)
        else:
            self._close_global(timeout)

    def get_job(self, job_id: str) -> JobRecord:
        """Retrieve audit record for task by ID.

        Args:
            job_id: Task identifier string.

        Returns:
            JobRecord model instance.

        Raises:
            JobNotFoundError: If job_id is not recorded.
        """
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]

        stored = self._store.get_job(job_id)
        if stored is not None:
            return stored

        raise JobNotFoundError(f"Job '{job_id}' not found")

    def list_jobs(
        self,
        owner: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[JobRecord]:
        """List job records matching optional query filters.

        Args:
            owner: Filter by owner identifier.
            status: Filter by lifecycle state.
            limit: Maximum count of records to return.

        Returns:
            List of matching JobRecord instances.
        """
        return self._store.list_jobs(owner=owner, status=status, limit=limit)

    def _publish_job_event(self, record: JobRecord) -> None:
        """Broadcast job state changes to the EventBus."""
        if self._event_bus is None:
            return

        payload = {
            "job_id": record.job_id,
            "owner": record.owner,
            "kind": record.kind,
            "status": str(record.status),
            "progress": record.progress,
            "accepted": record.accepted,
            "rejected": record.rejected,
            "message": record.message,
            "started_at_utc": record.started_at_utc,
            "finished_at_utc": record.finished_at_utc,
        }
        self._event_bus.publish(
            channel="jobs", event_type="jobs.changed", payload=payload
        )
        logger.debug(
            "FR-HOST-JOBS-EVENT-BROADCAST: Published jobs.changed for %s",
            record.job_id,
            extra={
                "job_id": record.job_id,
                "status": str(record.status),
                "requirement": "FR-HOST-JOBS-EVENT-BROADCAST",
            },
        )


# ==============================================================================
# Scoped JobAccess Facade
# ==============================================================================


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
        dedup_key: str | None = None,
        parent_job_id: str | None = None,
        pass_context: bool = False,
        **kwargs: Any,
    ) -> Future[T]:
        """Submit a background compute task bound to this owner scope.

        Args:
            fn: Callable target function to execute in worker pool.
            *args: Positional arguments for target callable.
            budget: Declared resource budget constraints.
            kind: Descriptive classification slug.
            dedup_key: Optional uniqueness key.
            parent_job_id: Optional parent job ID.
            pass_context: If True, passes JobContext to fn.
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
            dedup_key=dedup_key,
            parent_job_id=parent_job_id,
            pass_context=pass_context,
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

    def get_job(self, job_id: str) -> JobRecord:
        """Retrieve job record by task ID.

        Args:
            job_id: Task identifier string.

        Returns:
            JobRecord model instance.
        """
        return self._manager.get_job(job_id)

    def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[JobRecord]:
        """List jobs belonging exclusively to this owner scope.

        Args:
            status: Optional lifecycle status filter.
            limit: Maximum count of records.

        Returns:
            List of matching JobRecord instances.
        """
        return self._manager.list_jobs(owner=self._owner, status=status, limit=limit)

    def close(self, timeout: float = DEFAULT_CLOSE_TIMEOUT_SECONDS) -> None:
        """Cancel all pending and executing tasks owned by this scope.

        Args:
            timeout: Maximum wait time in seconds.
        """
        self._manager.close(owner=self._owner, timeout=timeout)


# ==============================================================================
# REST API Router & Service
# ==============================================================================


def _default_api_task(
    payload: dict[str, Any], context: JobContext | None = None
) -> dict[str, Any]:
    """Default lightweight worker task executed for REST submissions."""
    if context is not None:
        context.report_progress(50.0, message="Executing workload")
        context.check_cancellation()
        context.report_progress(100.0, message="Workload complete")
    return {"status": "success", "echo": payload}


class JobRouterService:
    """Service encapsulating HTTP endpoint handlers for local jobs."""

    def __init__(self, manager: JobManager) -> None:
        """Initialize service with central JobManager."""
        self._manager = manager

    def list_jobs(
        self,
        request: Request,
        owner: Annotated[str | None, Query()] = None,
        status_filter: Annotated[JobStatus | None, Query(alias="status")] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 50,
    ) -> Response:
        """Query recent job records."""
        req_id = request.headers.get("x-request-id")
        jobs = self._manager.list_jobs(owner=owner, status=status_filter, limit=limit)
        resp = StandardResponse.success(
            data=[j.model_dump() for j in jobs],
            message="Jobs retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_capacity(self, request: Request) -> Response:
        """Query host worker capacity and active reservation metrics."""
        req_id = request.headers.get("x-request-id")
        cap = self._manager.capacity_status()
        resp = StandardResponse.success(
            data=cap.model_dump(),
            message="Capacity status retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def submit_job(
        self,
        request: Request,
        body: SubmitJobRequest,
    ) -> Response:
        """Submit a new background compute task."""
        req_id = request.headers.get("x-request-id")
        budget = Budget(
            workers=body.workers,
            memory_bytes=body.memory_bytes,
            timeout_seconds=body.timeout_seconds,
        )

        handler = self._manager.get_handler(body.kind) or _default_api_task

        try:
            future = self._manager.submit(
                body.owner,
                handler,
                body.payload,
                budget=budget,
                kind=body.kind,
                dedup_key=body.dedup_key,
                parent_job_id=body.parent_job_id,
                pass_context=True,
            )
        except CapacityExceededError as exc:
            err = StandardError(code="CAPACITY_EXCEEDED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=StandardResponse.failure(
                    message="Job rejected due to capacity limits.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except DuplicateJobError as exc:
            err = StandardError(code="DUPLICATE_JOB", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=StandardResponse.failure(
                    message="Job rejected due to active duplicate.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except BudgetExceededError as exc:
            err = StandardError(code="BUDGET_EXCEEDED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content=StandardResponse.failure(
                    message="Job budget exceeds maximum allowable limits.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except JobManagerClosedError as exc:
            err = StandardError(code="MANAGER_CLOSED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=StandardResponse.failure(
                    message="Job manager is closed.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        job_id = self._manager.get_job_id_for_future(future)
        job_record = self._manager.get_job(job_id) if job_id else None
        data = job_record.model_dump() if job_record else {"status": "submitted"}
        resp = StandardResponse.success(
            data=data,
            message="Job admitted successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=resp.to_dict())

    def get_job(self, request: Request, job_id: str) -> Response:
        """Query status and metrics for a specific job."""
        req_id = request.headers.get("x-request-id")
        try:
            rec = self._manager.get_job(job_id)
        except JobNotFoundError:
            err = StandardError(code="NOT_FOUND", message=f"Job '{job_id}' not found.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=StandardResponse.failure(
                    message="Job record not found.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        resp = StandardResponse.success(
            data=rec.model_dump(),
            message="Job record retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def cancel_job(self, request: Request, job_id: str) -> Response:
        """Cancel a pending or running job."""
        req_id = request.headers.get("x-request-id")
        try:
            self._manager.get_job(job_id)
        except JobNotFoundError:
            err = StandardError(code="NOT_FOUND", message=f"Job '{job_id}' not found.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=StandardResponse.failure(
                    message="Job record not found.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        self._manager.cancel(job_id)
        updated_rec = self._manager.get_job(job_id)
        resp = StandardResponse.success(
            data=updated_rec.model_dump(),
            message="Job cancellation requested.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_jobs_router(manager: JobManager) -> APIRouter:
    """Create and return a FastAPI APIRouter exposing jobs management endpoints.

    Args:
        manager: Central JobManager instance.

    Returns:
        Configured FastAPI APIRouter instance.
    """
    service = JobRouterService(manager)
    router = APIRouter(prefix="/jobs", tags=["jobs"])

    router.add_api_route(
        "",
        service.list_jobs,
        methods=["GET"],
        summary="List jobs",
    )
    router.add_api_route(
        "/capacity",
        service.get_capacity,
        methods=["GET"],
        summary="Get capacity status",
    )
    router.add_api_route(
        "",
        service.submit_job,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary="Submit job",
    )
    router.add_api_route(
        "/{job_id}",
        service.get_job,
        methods=["GET"],
        summary="Get job by ID",
    )
    router.add_api_route(
        "/{job_id}/cancel",
        service.cancel_job,
        methods=["POST"],
        summary="Cancel job",
    )

    logger.debug(
        "FR-HOST-JOBS-REST-API: Constructed jobs router with prefix /jobs",
        extra={"prefix": "/jobs", "requirement": "FR-HOST-JOBS-REST-API"},
    )
    return router


# ==============================================================================
# CLI Entrypoint
# ==============================================================================


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for inspecting hardware, capacity, and job records."""
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Local Jobs and Coordinator CLI"
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Sample and display host hardware diagnostics",
    )
    parser.add_argument(
        "--capacity",
        action="store_true",
        help="Sample and display host capacity limits",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List persisted jobs in SQLite storage",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Run startup reconciliation and print interrupted job count",
    )
    parser.add_argument(
        "--owner",
        type=str,
        default=None,
        help="Filter jobs by owner identifier",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Optional path to SQLite database file or ':memory:'",
    )

    args = parser.parse_args(argv)

    if args.diagnostics:
        diag = diagnostics()
        sys.stdout.write(f"{diag.model_dump_json(indent=2)}\n")
        return 0

    if args.reconcile:
        store = JobStore(db_path=args.db_path)
        count = store.reconcile_on_startup()
        sys.stdout.write(f"Reconciled {count} orphaned jobs to INTERRUPTED\n")
        return 0

    if args.capacity:
        diag = diagnostics()
        cap = CapacityStatus(
            max_workers=diag.cpu_count_logical,
            reserved_workers=0,
            available_workers=diag.cpu_count_logical,
            max_memory_bytes=diag.total_ram_bytes,
            reserved_memory_bytes=0,
            available_memory_bytes=diag.total_ram_bytes,
            active_jobs_count=0,
            is_closed=False,
        )
        sys.stdout.write(f"{cap.model_dump_json(indent=2)}\n")
        return 0

    if args.list:
        store = JobStore(db_path=args.db_path)
        jobs = store.list_jobs(owner=args.owner)
        sys.stdout.write(f"{json.dumps([j.model_dump() for j in jobs], indent=2)}\n")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
