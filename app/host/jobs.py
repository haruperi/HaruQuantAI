# ruff: noqa: INP001
"""Multiprocessing background job coordinator, cancellation context, and recovery.

Description:
    Coordinates CPU-bound and long-running background workloads for the
    HaruQuantAI host platform using an OS multiprocessing worker pool
    (concurrent.futures.ProcessPoolExecutor) to bypass Python's Global
    Interpreter Lock (GIL). Works hand-in-hand with app/host/resources.py to
    size worker concurrency via workers = max(1, cpu_cores - 2), provision
    isolated per-job scratch directories, and enforce the active Memory Watchdog
    that rejects or pauses tasks when available system RAM drops below 15%.
    Provides picklable cross-process JobContext cancellation tokens for
    safe termination at cooperative checkpoints, persists job lifecycle transitions and
    events via app/host/persistence/ without importing sqlite3, and reconciles
    orphan jobs left in RUNNING state on startup by marking them INTERRUPTED.

Purpose:
    FEAT-HOST-JOBS: Host multiprocessing job pool, cooperative cancellation,
    memory-pressure gating, and startup orphan job reconciliation.

Key Capabilities:
    - FR-HOST-JOBS-POOL-LIFECYCLE: Manage ProcessPoolExecutor lifecycle sized by
      workers = max(1, cpu_cores - 2).
      Associated: `JobManager.__init__()`, `JobManager.ensure_pool()`,
      `JobManager.shutdown()`
      Logging: INFO on process pool initialization and graceful shutdown.
    - FR-HOST-JOBS-SUBMISSION: Submit, execute, and track jobs across QUEUED,
      RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED, and INTERRUPTED states.
      Associated: `JobManager.submit_job()`, `JobManager.wait_for_job()`,
      `JobRecord`, `JobState`
      Logging: INFO on job submission and completion; ERROR on task failure.
    - FR-HOST-JOBS-WATCHDOG-GATE: Gate task admission and execution using the
      15% available RAM watchdog, rejecting or pausing tasks on memory pressure.
      Associated: `JobManager.check_admission()`, `JobManager.resume_paused_jobs()`,
      `JobContext.check_memory_guard()`, `MemoryPressureError`
      Logging: WARNING when jobs are paused or rejected due to RAM < 15%.
    - FR-HOST-JOBS-CANCELLATION: Cooperative cancellation and progress reporting
      across worker processes via JobContext tokens.
      Associated: `JobContext`, `JobCancelledError`, `JobManager.cancel_job()`
      Logging: INFO when cancellation is signaled and when a job terminates early.
    - FR-HOST-JOBS-RECONCILIATION: Mark orphan jobs left in RUNNING state as
      INTERRUPTED on system startup.
      Associated: `JobManager.reconcile_orphan_jobs()`
      Logging: INFO on reconciliation scan; WARNING for each RUNNING job marked
      INTERRUPTED.
    - FR-HOST-JOBS-PERSISTENCE: Persist job records and state transition events
      through app/host/persistence/ with zero sqlite3 imports.
      Associated: `JobManager.get_job()`, `JobManager.list_jobs()`
      Logging: DEBUG on job persistence writes and queries.

Python API Usage:
    ```python
    from app.host.jobs import JobContext, JobManager, run_sample_compute_task

    manager = JobManager()
    reconciled = manager.reconcile_orphan_jobs()
    record = manager.submit_job(
        run_sample_compute_task,
        5_000,
        owner="researcher",
        kind="backtest",
    )
    completed = manager.wait_for_job(record.job_id, timeout=10.0)
    manager.shutdown()
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.jobs
    ```
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.host.persistence.read import (
    get_host_job,
    get_host_job_events,
    list_host_jobs,
)
from app.host.persistence.update import (
    record_host_job_event,
    save_host_job,
    update_host_job,
)
from app.host.resources import (
    MIN_AVAILABLE_RAM_PCT,
    MemoryWatchdogStatus,
    ResourceManager,
    calculate_worker_allocation,
    check_memory_headroom,
    probe_cpu,
)

__all__ = [
    "JobCancelledError",
    "JobContext",
    "JobManager",
    "JobRecord",
    "JobState",
    "MemoryPressureError",
]

logger = get_logger(__name__)

POOL_LIFECYCLE_FR = "FR-HOST-JOBS-POOL-LIFECYCLE"
SUBMISSION_FR = "FR-HOST-JOBS-SUBMISSION"
WATCHDOG_GATE_FR = "FR-HOST-JOBS-WATCHDOG-GATE"
CANCELLATION_FR = "FR-HOST-JOBS-CANCELLATION"
RECONCILIATION_FR = "FR-HOST-JOBS-RECONCILIATION"
PERSISTENCE_FR = "FR-HOST-JOBS-PERSISTENCE"

CANCEL_MARKER_FILE = ".job_cancel"
PAUSE_MARKER_FILE = ".job_pause"
PROGRESS_MARKER_FILE = ".job_progress.json"


class JobState(StrEnum):
    """Canonical lifecycle states for host background jobs."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"


class JobCancelledError(InterruptedError):
    """Raised when a job cooperatively terminates due to a cancellation signal."""


class MemoryPressureError(MemoryError):
    """Raised when available system RAM drops below the 15% watchdog threshold."""


@dataclass(frozen=True)
class JobRecord:
    """Immutable snapshot of a managed background job."""

    job_id: str
    owner: str
    kind: str
    status: str
    progress: float
    message: str
    attempt_id: int
    submitted_at_utc: str
    started_at_utc: str | None = None
    finished_at_utc: str | None = None
    error_message: str | None = None
    result: Any = None
    worker_pid: int | None = None
    scratch_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize JobRecord to a plain dictionary."""
        return asdict(self)


class JobContext:
    """Picklable cooperative cancellation, pause, and progress context for jobs.

    Supports both in-process threading events and cross-process filesystem marker
    synchronization inside the job's isolated scratch sandbox so tasks running in
    a ProcessPoolExecutor on Windows ('spawn') observe cancellation and pause
    signals immediately without unpicklable lock objects.
    """

    def __init__(
        self,
        job_id: str,
        scratch_dir: Path | str,
        *,
        attempt_id: int = 1,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        cancel_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
    ) -> None:
        """Initialize JobContext with job identity and isolated scratch directory."""
        self.job_id: str = job_id
        self.attempt_id: int = attempt_id
        self.scratch_dir: Path = Path(scratch_dir).resolve()
        self.min_available_ram_pct: float = float(min_available_ram_pct)
        self._cancel_event: threading.Event | None = cancel_event
        self._pause_event: threading.Event | None = pause_event

    @override
    def __getstate__(self) -> dict[str, Any]:
        """Strip unpicklable threading primitives when sent to ProcessPoolExecutor."""
        return {
            "job_id": self.job_id,
            "attempt_id": self.attempt_id,
            "scratch_dir": str(self.scratch_dir),
            "min_available_ram_pct": self.min_available_ram_pct,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore JobContext inside a child worker process."""
        self.job_id = str(state["job_id"])
        self.attempt_id = int(state.get("attempt_id", 1))
        self.scratch_dir = Path(str(state["scratch_dir"])).resolve()
        self.min_available_ram_pct = float(
            state.get("min_available_ram_pct", MIN_AVAILABLE_RAM_PCT)
        )
        self._cancel_event = None
        self._pause_event = None

    @property
    def _cancel_marker(self) -> Path:
        return self.scratch_dir / CANCEL_MARKER_FILE

    @property
    def _pause_marker(self) -> Path:
        return self.scratch_dir / PAUSE_MARKER_FILE

    @property
    def _progress_marker(self) -> Path:
        return self.scratch_dir / PROGRESS_MARKER_FILE

    def cancel(self) -> None:
        """Signal cooperative cancellation for this job across threads and processes."""
        if self._cancel_event is not None:
            self._cancel_event.set()
        try:
            self.scratch_dir.mkdir(parents=True, exist_ok=True)
            self._cancel_marker.write_text("cancelled", encoding="utf-8")
        except OSError:
            pass
        logger.info(
            "%s: cancellation token signaled for job %s",
            CANCELLATION_FR,
            self.job_id,
            extra={"fr_id": CANCELLATION_FR, "job_id": self.job_id},
        )

    def set_paused(self, paused: bool) -> None:
        """Set or clear the cooperative pause signal for this job."""
        if self._pause_event is not None:
            if paused:
                self._pause_event.set()
            else:
                self._pause_event.clear()
        try:
            if paused:
                self.scratch_dir.mkdir(parents=True, exist_ok=True)
                self._pause_marker.write_text("paused", encoding="utf-8")
            else:
                self._pause_marker.unlink(missing_ok=True)
        except OSError:
            pass

    def is_cancelled(self) -> bool:
        """Return True if cooperative cancellation has been requested."""
        if self._cancel_event is not None and self._cancel_event.is_set():
            return True
        return self._cancel_marker.exists()

    def is_paused(self) -> bool:
        """Return True if the job is currently paused."""
        if self._pause_event is not None and self._pause_event.is_set():
            return True
        return self._pause_marker.exists()

    def raise_if_cancelled(self) -> None:
        """Raise JobCancelledError immediately if cancellation was signaled."""
        if self.is_cancelled():
            logger.info(
                "%s: job %s observed cancellation token and is terminating safely",
                CANCELLATION_FR,
                self.job_id,
                extra={"fr_id": CANCELLATION_FR, "job_id": self.job_id},
            )
            raise JobCancelledError(f"Job '{self.job_id}' was cancelled.")

    def wait_if_paused(
        self,
        *,
        poll_interval: float = 0.02,
        timeout: float | None = None,
    ) -> None:
        """Block cooperatively while the job is paused, checking cancellation."""
        start = time.monotonic()
        while self.is_paused():
            self.raise_if_cancelled()
            if timeout is not None and (time.monotonic() - start) >= timeout:
                break
            time.sleep(max(0.005, poll_interval))
        self.raise_if_cancelled()

    def check_memory_guard(
        self,
        *,
        policy: str = "reject",
    ) -> MemoryWatchdogStatus:
        """Check system RAM headroom from inside a running task."""
        status = check_memory_headroom(
            self.min_available_ram_pct,
            policy=policy,
        )
        if status.is_pressured and status.recommended_action == "REJECT":
            raise MemoryPressureError(
                f"Available RAM ({status.available_pct:.1f}%) dropped below "
                f"{status.threshold_pct:.1f}% threshold for job '{self.job_id}'."
            )
        if status.is_pressured and status.recommended_action == "PAUSE":
            self.set_paused(True)
        return status

    def report_progress(self, progress: float, message: str = "") -> None:
        """Record task progress percentage (0..100) and status message."""
        self.raise_if_cancelled()
        clamped = round(max(0.0, min(100.0, float(progress))), 2)
        payload = {"progress": clamped, "message": message}
        try:
            self.scratch_dir.mkdir(parents=True, exist_ok=True)
            self._progress_marker.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
        except OSError:
            pass

    def read_progress(self) -> tuple[float, str] | None:
        """Read latest progress reported by worker process if available."""
        try:
            if self._progress_marker.exists():
                raw = json.loads(self._progress_marker.read_text(encoding="utf-8"))
                return float(raw.get("progress", 0.0)), str(raw.get("message", ""))
        except OSError, ValueError, TypeError:
            pass
        return None


def _execute_worker_task(
    fn: Callable[..., Any],
    context: JobContext,
    pass_context: bool,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[int, Any]:
    """Top-level picklable entrypoint executed inside ProcessPoolExecutor workers."""
    context.raise_if_cancelled()
    context.wait_if_paused()
    worker_pid = os.getpid()
    result = fn(context, *args, **kwargs) if pass_context else fn(*args, **kwargs)
    context.raise_if_cancelled()
    return worker_pid, result


def _callable_accepts_job_context(fn: Callable[..., Any]) -> bool:
    """Determine if target callable expects a JobContext as its first parameter."""
    try:
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        if not params:
            return False
        first = params[0]
        if first.name in ("ctx", "context", "job_context"):
            return True
        ann = str(first.annotation)
        return "JobContext" in ann
    except ValueError, TypeError:
        return False


@dataclass
class _DeferredSubmission:
    """Holds a paused job waiting for system RAM headroom to recover."""

    job_id: str
    fn: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    pass_context: bool
    context: JobContext
    owner: str
    kind: str
    submitted_at_utc: str
    done_event: threading.Event = field(default_factory=threading.Event)
    executor_kind: str | None = None


class JobManager:
    """Multiprocessing job coordinator with memory watchdog and orphan recovery."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        max_workers: int | None = None,
        resource_mgr: ResourceManager | None = None,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        memory_policy: str = "reject",
        use_process_pool: bool = True,
        cleanup_scratch_on_exit: bool = True,
        reconcile_on_startup: bool = False,
    ) -> None:
        """Initialize JobManager with ProcessPoolExecutor and ResourceManager.

        Args:
            db_path: Optional SQLite database path for job persistence.
            max_workers: Optional worker limit override. If None, uses
                workers = max(1, cpu_cores - 2).
            resource_mgr: Optional ResourceManager instance.
            min_available_ram_pct: Minimum available system RAM percentage
                before watchdog triggers (default: 15.0%).
            memory_policy: Default watchdog enforcement policy ('reject' or 'pause').
            use_process_pool: If True (default), uses ProcessPoolExecutor to
                bypass the GIL; if False, uses ThreadPoolExecutor.
            cleanup_scratch_on_exit: If True, removes per-job scratch directory
                when the job finishes.
            reconcile_on_startup: If True, immediately marks orphan RUNNING jobs
                as INTERRUPTED on initialization.
        """
        self._db_path = db_path
        self._min_available_ram_pct = float(min_available_ram_pct)
        self._memory_policy = memory_policy.strip().lower()
        self._use_process_pool = use_process_pool
        self._cleanup_scratch_on_exit = cleanup_scratch_on_exit

        self._resource_mgr = resource_mgr or ResourceManager(
            min_available_ram_pct=self._min_available_ram_pct,
            watchdog_policy=self._memory_policy,
        )
        self._max_workers = (
            max(1, max_workers)
            if max_workers is not None
            else calculate_worker_allocation(probe_cpu().logical_cores)
        )

        self._lock = threading.Lock()
        self._pool: ProcessPoolExecutor | ThreadPoolExecutor | None = None
        self._io_pool: ThreadPoolExecutor | None = None
        self._jobs: dict[str, JobRecord] = {}
        self._contexts: dict[str, JobContext] = {}
        self._futures: dict[str, Future[tuple[int, Any]]] = {}
        self._done_events: dict[str, threading.Event] = {}
        self._paused_queue: dict[str, _DeferredSubmission] = {}

        self._resource_mgr.watchdog.register_callbacks(
            on_pressure=self._on_memory_pressure,
            on_recovery=self._on_memory_recovery,
        )

        logger.info(
            "%s: initialized JobManager (max_workers=%d, process_pool=%s, "
            "ram_threshold=%.1f%%, policy=%s)",
            POOL_LIFECYCLE_FR,
            self._max_workers,
            self._use_process_pool,
            self._min_available_ram_pct,
            self._memory_policy,
            extra={
                "fr_id": POOL_LIFECYCLE_FR,
                "max_workers": self._max_workers,
                "use_process_pool": self._use_process_pool,
            },
        )

        if reconcile_on_startup:
            self.reconcile_orphan_jobs()

    @property
    def max_workers(self) -> int:
        """Return configured worker concurrency limit."""
        return self._max_workers

    @property
    def resource_manager(self) -> ResourceManager:
        """Return associated ResourceManager custodian."""
        return self._resource_mgr

    def ensure_pool(self) -> ProcessPoolExecutor | ThreadPoolExecutor:
        """Lazily create and return the active worker pool executor."""
        with self._lock:
            if self._pool is None:
                if self._use_process_pool:
                    self._pool = ProcessPoolExecutor(max_workers=self._max_workers)
                else:
                    self._pool = ThreadPoolExecutor(max_workers=self._max_workers)
                logger.info(
                    "%s: started %s with %d workers",
                    POOL_LIFECYCLE_FR,
                    type(self._pool).__name__,
                    self._max_workers,
                    extra={
                        "fr_id": POOL_LIFECYCLE_FR,
                        "pool_type": type(self._pool).__name__,
                        "max_workers": self._max_workers,
                    },
                )
            return self._pool

    def ensure_io_pool(self) -> ThreadPoolExecutor:
        """Lazily create and return the dedicated I/O thread pool executor."""
        with self._lock:
            if self._io_pool is None:
                workers = min(4, self._max_workers)
                self._io_pool = ThreadPoolExecutor(max_workers=workers)
                logger.info(
                    "%s: started I/O ThreadPoolExecutor with %d workers",
                    POOL_LIFECYCLE_FR,
                    workers,
                    extra={
                        "fr_id": POOL_LIFECYCLE_FR,
                        "pool_type": "ThreadPoolExecutor",
                        "max_workers": workers,
                    },
                )
            return self._io_pool

    def reconcile_orphan_jobs(self) -> list[str]:
        """Mark orphan jobs left in RUNNING state as INTERRUPTED on system boot.

        Returns:
            List of job_ids transitioned from RUNNING to INTERRUPTED.
        """
        reconciled_ids: list[str] = []
        try:
            all_jobs = list_host_jobs(conn=self._db_path, limit=1_000)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s: could not query host_jobs during startup reconciliation: %s",
                RECONCILIATION_FR,
                exc,
                extra={"fr_id": RECONCILIATION_FR, "error": str(exc)},
            )
            return reconciled_ids

        now_iso = datetime.now(UTC).isoformat()
        for row in all_jobs:
            raw_status = str(row.get("status", "")).upper()
            if raw_status == JobState.RUNNING:
                jid = str(row["job_id"])
                err_msg = "Orphan job left in RUNNING state marked INTERRUPTED on boot"
                update_host_job(
                    jid,
                    {
                        "status": str(JobState.INTERRUPTED),
                        "finished_at_utc": now_iso,
                        "message": "Interrupted by host restart",
                        "error_message": err_msg,
                    },
                    conn=self._db_path,
                )
                record_host_job_event(
                    event_id=f"evt-{uuid.uuid4().hex[:12]}",
                    job_id=jid,
                    from_state=str(JobState.RUNNING),
                    to_state=str(JobState.INTERRUPTED),
                    details_json=json.dumps({"reason": "startup_orphan_recovery"}),
                    created_at_utc=now_iso,
                    conn=self._db_path,
                )
                self._resource_mgr.cleanup_scratch(jid)
                reconciled_ids.append(jid)
                logger.warning(
                    "%s: reconciled orphan RUNNING job %s -> INTERRUPTED",
                    RECONCILIATION_FR,
                    jid,
                    extra={
                        "fr_id": RECONCILIATION_FR,
                        "job_id": jid,
                        "to_state": str(JobState.INTERRUPTED),
                    },
                )

        logger.info(
            "%s: startup orphan job reconciliation complete (reconciled=%d)",
            RECONCILIATION_FR,
            len(reconciled_ids),
            extra={
                "fr_id": RECONCILIATION_FR,
                "reconciled_count": len(reconciled_ids),
            },
        )
        return reconciled_ids

    def check_admission(
        self,
        *,
        on_memory_pressure: str | None = None,
    ) -> MemoryWatchdogStatus:
        """Evaluate the 15% available RAM watchdog before starting a task."""
        policy = (
            on_memory_pressure.strip().lower()
            if on_memory_pressure is not None
            else self._memory_policy
        )
        status = self._resource_mgr.check_memory_headroom(policy=policy)
        if status.is_pressured:
            logger.warning(
                "%s: memory watchdog triggered during job admission "
                "(available=%.1f%% < %.1f%%, action=%s)",
                WATCHDOG_GATE_FR,
                status.available_pct,
                status.threshold_pct,
                status.recommended_action,
                extra={
                    "fr_id": WATCHDOG_GATE_FR,
                    "available_pct": status.available_pct,
                    "action": status.recommended_action,
                },
            )
        return status

    def submit_job(
        self,
        fn: Callable[..., Any],
        *args: Any,
        job_id: str | None = None,
        owner: str = "default",
        kind: str = "compute",
        pass_context: bool | None = None,
        on_memory_pressure: str | None = None,
        executor_kind: str | None = None,
        **kwargs: Any,
    ) -> JobRecord:
        """Submit a task to the multiprocessing worker pool with watchdog gating.

        Args:
            fn: Top-level picklable callable to execute.
            *args: Positional arguments forwarded to fn.
            job_id: Optional explicit job identifier.
            owner: Submitting component or user identifier.
            kind: Job classification (e.g., 'compute', 'backtest', 'ingest').
            pass_context: Whether to pass JobContext as the first argument to fn.
                If None, auto-detected from fn's signature.
            on_memory_pressure: Watchdog policy override ('reject' or 'pause').
            executor_kind: Optional executor selection ('process' or 'thread').
            **kwargs: Keyword arguments forwarded to fn.

        Returns:
            JobRecord representing the submitted (or paused) job.

        Raises:
            MemoryPressureError: If available system RAM is below 15% and policy
                is 'reject'.
        """
        jid = job_id or f"job-{uuid.uuid4().hex[:10]}"
        submitted_at = datetime.now(UTC).isoformat()
        effective_policy = (
            on_memory_pressure.strip().lower()
            if on_memory_pressure is not None
            else self._memory_policy
        )

        watchdog_status = self.check_admission(on_memory_pressure=effective_policy)
        if (
            watchdog_status.is_pressured
            and watchdog_status.recommended_action == "REJECT"
        ):
            err_text = (
                f"Task rejected by Memory Watchdog: available RAM "
                f"({watchdog_status.available_pct:.1f}%) is below "
                f"{watchdog_status.threshold_pct:.1f}% minimum."
            )
            save_host_job(
                jid,
                owner=owner,
                kind=kind,
                status=str(JobState.FAILED),
                rejected=1,
                message="Rejected by Memory Watchdog (<15% available RAM)",
                submitted_at_utc=submitted_at,
                finished_at_utc=submitted_at,
                error_message=err_text,
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=jid,
                from_state=None,
                to_state=str(JobState.FAILED),
                details_json=json.dumps(
                    {
                        "reason": "memory_watchdog_reject",
                        "available_pct": watchdog_status.available_pct,
                    }
                ),
                created_at_utc=submitted_at,
                conn=self._db_path,
            )
            raise MemoryPressureError(err_text)

        scratch_dir = self._resource_mgr.allocate_scratch(jid)
        cancel_evt = threading.Event()
        pause_evt = threading.Event()
        ctx = JobContext(
            job_id=jid,
            scratch_dir=scratch_dir,
            min_available_ram_pct=self._min_available_ram_pct,
            cancel_event=cancel_evt,
            pause_event=pause_evt,
        )
        done_evt = threading.Event()
        effective_pass_ctx = (
            pass_context
            if pass_context is not None
            else _callable_accepts_job_context(fn)
        )

        if (
            watchdog_status.is_pressured
            and watchdog_status.recommended_action == "PAUSE"
        ):
            ctx.set_paused(True)
            paused_rec = JobRecord(
                job_id=jid,
                owner=owner,
                kind=kind,
                status=str(JobState.PAUSED),
                progress=0.0,
                message="Paused by Memory Watchdog (<15% available RAM)",
                attempt_id=1,
                submitted_at_utc=submitted_at,
                scratch_dir=str(scratch_dir),
            )
            save_host_job(
                jid,
                owner=owner,
                kind=kind,
                status=str(JobState.PAUSED),
                accepted=1,
                message=paused_rec.message,
                submitted_at_utc=submitted_at,
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=jid,
                from_state=str(JobState.QUEUED),
                to_state=str(JobState.PAUSED),
                details_json=json.dumps(
                    {
                        "reason": "memory_watchdog_pause",
                        "available_pct": watchdog_status.available_pct,
                    }
                ),
                created_at_utc=submitted_at,
                conn=self._db_path,
            )
            with self._lock:
                self._jobs[jid] = paused_rec
                self._contexts[jid] = ctx
                self._done_events[jid] = done_evt
                self._paused_queue[jid] = _DeferredSubmission(
                    job_id=jid,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    pass_context=effective_pass_ctx,
                    context=ctx,
                    owner=owner,
                    kind=kind,
                    submitted_at_utc=submitted_at,
                    done_event=done_evt,
                    executor_kind=executor_kind,
                )
            logger.warning(
                "%s: job %s queued in PAUSED state due to low RAM (%.1f%%)",
                WATCHDOG_GATE_FR,
                jid,
                watchdog_status.available_pct,
                extra={"fr_id": WATCHDOG_GATE_FR, "job_id": jid},
            )
            return paused_rec

        return self._dispatch_to_pool(
            jid=jid,
            fn=fn,
            args=args,
            kwargs=kwargs,
            pass_context=effective_pass_ctx,
            ctx=ctx,
            owner=owner,
            kind=kind,
            submitted_at=submitted_at,
            done_evt=done_evt,
            executor_kind=executor_kind,
        )

    def _dispatch_to_pool(
        self,
        *,
        jid: str,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        pass_context: bool,
        ctx: JobContext,
        owner: str,
        kind: str,
        submitted_at: str,
        done_evt: threading.Event,
        executor_kind: str | None = None,
    ) -> JobRecord:
        """Dispatch an admitted job to the worker pool executor."""
        started_at = datetime.now(UTC).isoformat()
        running_rec = JobRecord(
            job_id=jid,
            owner=owner,
            kind=kind,
            status=str(JobState.RUNNING),
            progress=0.0,
            message="Running",
            attempt_id=1,
            submitted_at_utc=submitted_at,
            started_at_utc=started_at,
            scratch_dir=str(ctx.scratch_dir),
        )

        save_host_job(
            jid,
            owner=owner,
            kind=kind,
            status=str(JobState.RUNNING),
            accepted=1,
            message="Running",
            submitted_at_utc=submitted_at,
            started_at_utc=started_at,
            conn=self._db_path,
        )
        record_host_job_event(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            job_id=jid,
            from_state=str(JobState.QUEUED),
            to_state=str(JobState.RUNNING),
            details_json=json.dumps({"owner": owner, "kind": kind}),
            created_at_utc=started_at,
            conn=self._db_path,
        )

        if executor_kind == "thread":
            pool: ProcessPoolExecutor | ThreadPoolExecutor = self.ensure_io_pool()
        else:
            pool = self.ensure_pool()

        with self._lock:
            self._jobs[jid] = running_rec
            self._contexts[jid] = ctx
            self._done_events[jid] = done_evt
            future = pool.submit(
                _execute_worker_task,
                fn,
                ctx,
                pass_context,
                args,
                kwargs,
            )
            self._futures[jid] = future

        future.add_done_callback(functools.partial(self._on_future_done, jid))

        logger.info(
            "%s: submitted job %s (owner=%s, kind=%s)",
            SUBMISSION_FR,
            jid,
            owner,
            kind,
            extra={"fr_id": SUBMISSION_FR, "job_id": jid, "kind": kind},
        )
        return running_rec

    @staticmethod
    def _extract_future_outcome(
        job_id: str,
        future: Future[tuple[int, Any]],
        ctx: JobContext | None,
    ) -> tuple[int, Any]:
        """Extract worker PID and result or raise JobCancelledError."""
        if future.cancelled() or (ctx is not None and ctx.is_cancelled()):
            raise JobCancelledError(f"Job '{job_id}' cancelled.")
        return future.result()

    def _on_future_done(
        self,
        job_id: str,
        future: Future[tuple[int, Any]],
    ) -> None:
        """Handle completion, failure, or cancellation of a worker pool future."""
        finished_at = datetime.now(UTC).isoformat()
        with self._lock:
            current = self._jobs.get(job_id)
            ctx = self._contexts.get(job_id)
            done_evt = self._done_events.get(job_id)

        owner = current.owner if current else "default"
        kind = current.kind if current else "compute"
        submitted_at = current.submitted_at_utc if current else finished_at
        started_at = current.started_at_utc if current else finished_at
        scratch_str = current.scratch_dir if current else None

        try:
            worker_pid, result = self._extract_future_outcome(job_id, future, ctx)
            final_rec = JobRecord(
                job_id=job_id,
                owner=owner,
                kind=kind,
                status=str(JobState.COMPLETED),
                progress=100.0,
                message="Completed",
                attempt_id=1,
                submitted_at_utc=submitted_at,
                started_at_utc=started_at,
                finished_at_utc=finished_at,
                result=result,
                worker_pid=worker_pid,
                scratch_dir=scratch_str,
            )
            update_host_job(
                job_id,
                {
                    "status": str(JobState.COMPLETED),
                    "progress": 100.0,
                    "message": "Completed",
                    "finished_at_utc": finished_at,
                },
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                from_state=str(JobState.RUNNING),
                to_state=str(JobState.COMPLETED),
                details_json=json.dumps({"worker_pid": worker_pid}),
                created_at_utc=finished_at,
                conn=self._db_path,
            )
            logger.info(
                "%s: job %s completed on worker PID %s",
                SUBMISSION_FR,
                job_id,
                worker_pid,
                extra={
                    "fr_id": SUBMISSION_FR,
                    "job_id": job_id,
                    "worker_pid": worker_pid,
                },
            )
        except JobCancelledError as exc:
            final_rec = JobRecord(
                job_id=job_id,
                owner=owner,
                kind=kind,
                status=str(JobState.CANCELLED),
                progress=current.progress if current else 0.0,
                message="Cancelled by user",
                attempt_id=1,
                submitted_at_utc=submitted_at,
                started_at_utc=started_at,
                finished_at_utc=finished_at,
                error_message=str(exc),
                scratch_dir=scratch_str,
            )
            update_host_job(
                job_id,
                {
                    "status": str(JobState.CANCELLED),
                    "message": "Cancelled by user",
                    "finished_at_utc": finished_at,
                    "error_message": str(exc),
                },
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                from_state=str(JobState.RUNNING),
                to_state=str(JobState.CANCELLED),
                details_json=json.dumps({"reason": str(exc)}),
                created_at_utc=finished_at,
                conn=self._db_path,
            )
            logger.info(
                "%s: job %s transitioned to CANCELLED",
                CANCELLATION_FR,
                job_id,
                extra={"fr_id": CANCELLATION_FR, "job_id": job_id},
            )
        except Exception as exc:
            final_rec = JobRecord(
                job_id=job_id,
                owner=owner,
                kind=kind,
                status=str(JobState.FAILED),
                progress=current.progress if current else 0.0,
                message="Failed",
                attempt_id=1,
                submitted_at_utc=submitted_at,
                started_at_utc=started_at,
                finished_at_utc=finished_at,
                error_message=str(exc),
                scratch_dir=scratch_str,
            )
            update_host_job(
                job_id,
                {
                    "status": str(JobState.FAILED),
                    "message": "Failed",
                    "finished_at_utc": finished_at,
                    "error_message": str(exc),
                },
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                from_state=str(JobState.RUNNING),
                to_state=str(JobState.FAILED),
                details_json=json.dumps({"error": str(exc)}),
                created_at_utc=finished_at,
                conn=self._db_path,
            )
            logger.exception(
                "%s: job %s failed during execution",
                SUBMISSION_FR,
                job_id,
                extra={"fr_id": SUBMISSION_FR, "job_id": job_id, "error": str(exc)},
            )

        if self._cleanup_scratch_on_exit:
            self._resource_mgr.cleanup_scratch(job_id)

        with self._lock:
            self._jobs[job_id] = final_rec

        if done_evt is not None:
            done_evt.set()

    def cancel_job(self, job_id: str) -> bool:
        """Signal cooperative cancellation for a queued, paused, or running job."""
        with self._lock:
            ctx = self._contexts.get(job_id)
            fut = self._futures.get(job_id)
            deferred = self._paused_queue.pop(job_id, None)
            current = self._jobs.get(job_id)
            done_evt = self._done_events.get(job_id)

        if ctx is None and current is None:
            return False

        if ctx is not None:
            ctx.cancel()
            ctx.set_paused(False)

        if fut is not None:
            fut.cancel()

        if deferred is not None:
            now_iso = datetime.now(UTC).isoformat()
            cancelled_rec = JobRecord(
                job_id=job_id,
                owner=deferred.owner,
                kind=deferred.kind,
                status=str(JobState.CANCELLED),
                progress=0.0,
                message="Cancelled while paused",
                attempt_id=1,
                submitted_at_utc=deferred.submitted_at_utc,
                finished_at_utc=now_iso,
                error_message="Cancelled by user while paused",
                scratch_dir=str(deferred.context.scratch_dir),
            )
            update_host_job(
                job_id,
                {
                    "status": str(JobState.CANCELLED),
                    "message": "Cancelled while paused",
                    "finished_at_utc": now_iso,
                    "error_message": "Cancelled by user while paused",
                },
                conn=self._db_path,
            )
            record_host_job_event(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                from_state=str(JobState.PAUSED),
                to_state=str(JobState.CANCELLED),
                details_json=json.dumps({"reason": "user_cancelled_paused_job"}),
                created_at_utc=now_iso,
                conn=self._db_path,
            )
            if self._cleanup_scratch_on_exit:
                self._resource_mgr.cleanup_scratch(job_id)
            with self._lock:
                self._jobs[job_id] = cancelled_rec
            if done_evt is not None:
                done_evt.set()

        logger.info(
            "%s: requested cancellation for job %s",
            CANCELLATION_FR,
            job_id,
            extra={"fr_id": CANCELLATION_FR, "job_id": job_id},
        )
        return True

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job cooperatively."""
        with self._lock:
            ctx = self._contexts.get(job_id)
            curr = self._jobs.get(job_id)
        if ctx is None or curr is None or curr.status != str(JobState.RUNNING):
            return False

        ctx.set_paused(True)
        paused_rec = JobRecord(
            job_id=curr.job_id,
            owner=curr.owner,
            kind=curr.kind,
            status=str(JobState.PAUSED),
            progress=curr.progress,
            message="Paused",
            attempt_id=curr.attempt_id,
            submitted_at_utc=curr.submitted_at_utc,
            started_at_utc=curr.started_at_utc,
            scratch_dir=curr.scratch_dir,
        )
        with self._lock:
            self._jobs[job_id] = paused_rec
        update_host_job(
            job_id,
            {"status": str(JobState.PAUSED), "message": "Paused"},
            conn=self._db_path,
        )
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job when RAM headroom permits."""
        with self._lock:
            deferred = self._paused_queue.pop(job_id, None)
            ctx = self._contexts.get(job_id)
            curr = self._jobs.get(job_id)

        if deferred is not None:
            deferred.context.set_paused(False)
            self._dispatch_to_pool(
                jid=deferred.job_id,
                fn=deferred.fn,
                args=deferred.args,
                kwargs=deferred.kwargs,
                pass_context=deferred.pass_context,
                ctx=deferred.context,
                owner=deferred.owner,
                kind=deferred.kind,
                submitted_at=deferred.submitted_at_utc,
                done_evt=deferred.done_event,
                executor_kind=deferred.executor_kind,
            )
            return True

        if ctx is not None and curr is not None and curr.status == str(JobState.PAUSED):
            ctx.set_paused(False)
            resumed_rec = JobRecord(
                job_id=curr.job_id,
                owner=curr.owner,
                kind=curr.kind,
                status=str(JobState.RUNNING),
                progress=curr.progress,
                message="Running",
                attempt_id=curr.attempt_id,
                submitted_at_utc=curr.submitted_at_utc,
                started_at_utc=curr.started_at_utc,
                scratch_dir=curr.scratch_dir,
            )
            with self._lock:
                self._jobs[job_id] = resumed_rec
            update_host_job(
                job_id,
                {"status": str(JobState.RUNNING), "message": "Running"},
                conn=self._db_path,
            )
            return True

        return False

    def _resume_all_paused(self) -> list[str]:
        """Dispatch or unpause all currently paused jobs."""
        with self._lock:
            paused_ids = [
                jid
                for jid, rec in self._jobs.items()
                if rec.status == str(JobState.PAUSED)
            ]

        return [jid for jid in paused_ids if self.resume_job(jid)]

    def resume_paused_jobs(self) -> list[str]:
        """Resume all paused jobs if available system RAM is >= 15%."""
        with self._lock:
            candidates = [
                jid
                for jid, rec in self._jobs.items()
                if rec.status == str(JobState.PAUSED)
            ]
        status = self._resource_mgr.check_memory_headroom(policy="pause")
        if status.is_pressured:
            return []

        resumed: list[str] = []
        for jid in candidates:
            if self.resume_job(jid):
                resumed.append(jid)
            else:
                curr = self.get_job(jid)
                if curr is not None and curr.status in (
                    str(JobState.RUNNING),
                    str(JobState.COMPLETED),
                ):
                    resumed.append(jid)
        return resumed

    def _on_memory_pressure(self, status: MemoryWatchdogStatus) -> None:
        """Callback invoked when MemoryWatchdog detects available RAM < 15%."""
        with self._lock:
            running_ids = [
                jid
                for jid, rec in self._jobs.items()
                if rec.status == str(JobState.RUNNING)
            ]
        for jid in running_ids:
            if status.recommended_action == "PAUSE":
                self.pause_job(jid)
            else:
                self.cancel_job(jid)

    def _on_memory_recovery(self, _status: MemoryWatchdogStatus) -> None:
        """Callback invoked when MemoryWatchdog observes RAM recovery >= 15%."""
        self._resume_all_paused()

    def wait_for_job(
        self,
        job_id: str,
        *,
        timeout: float = 10.0,
    ) -> JobRecord:
        """Wait for a submitted job to reach a terminal state and return its record."""
        with self._lock:
            done_evt = self._done_events.get(job_id)

        if done_evt is not None:
            done_evt.wait(timeout=timeout)

        rec = self.get_job(job_id)
        if rec is None:
            raise KeyError(f"Job '{job_id}' not found.")
        return rec

    def get_job(self, job_id: str) -> JobRecord | None:
        """Retrieve current JobRecord from memory or persistence store."""
        with self._lock:
            mem_rec = self._jobs.get(job_id)
            ctx = self._contexts.get(job_id)

        if (
            mem_rec is not None
            and ctx is not None
            and mem_rec.status == str(JobState.RUNNING)
        ):
            prog = ctx.read_progress()
            if prog is not None:
                pct, msg = prog
                mem_rec = JobRecord(
                    job_id=mem_rec.job_id,
                    owner=mem_rec.owner,
                    kind=mem_rec.kind,
                    status=mem_rec.status,
                    progress=pct,
                    message=msg or mem_rec.message,
                    attempt_id=mem_rec.attempt_id,
                    submitted_at_utc=mem_rec.submitted_at_utc,
                    started_at_utc=mem_rec.started_at_utc,
                    scratch_dir=mem_rec.scratch_dir,
                )

        if mem_rec is not None:
            logger.debug(
                "%s: retrieved in-memory job %s (status=%s)",
                PERSISTENCE_FR,
                job_id,
                mem_rec.status,
                extra={"fr_id": PERSISTENCE_FR, "job_id": job_id},
            )
            return mem_rec

        row = get_host_job(job_id, conn=self._db_path)
        if row is None:
            return None

        logger.debug(
            "%s: retrieved persisted job %s (status=%s)",
            PERSISTENCE_FR,
            job_id,
            row.get("status"),
            extra={"fr_id": PERSISTENCE_FR, "job_id": job_id},
        )
        return JobRecord(
            job_id=str(row["job_id"]),
            owner=str(row.get("owner", "default")),
            kind=str(row.get("kind", "compute")),
            status=str(row.get("status", "")),
            progress=float(row.get("progress", 0.0)),
            message=str(row.get("message", "")),
            attempt_id=int(row.get("attempt_id", 1)),
            submitted_at_utc=str(row.get("submitted_at_utc", "")),
            started_at_utc=row.get("started_at_utc"),
            finished_at_utc=row.get("finished_at_utc"),
            error_message=row.get("error_message"),
        )

    def list_jobs(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[JobRecord]:
        """List persisted jobs from host_jobs table."""
        rows = list_host_jobs(conn=self._db_path, status=status, limit=limit)
        logger.debug(
            "%s: listed %d persisted jobs (status=%s)",
            PERSISTENCE_FR,
            len(rows),
            status,
            extra={"fr_id": PERSISTENCE_FR, "count": len(rows)},
        )
        return [
            JobRecord(
                job_id=str(r["job_id"]),
                owner=str(r.get("owner", "default")),
                kind=str(r.get("kind", "compute")),
                status=str(r.get("status", "")),
                progress=float(r.get("progress", 0.0)),
                message=str(r.get("message", "")),
                attempt_id=int(r.get("attempt_id", 1)),
                submitted_at_utc=str(r.get("submitted_at_utc", "")),
                started_at_utc=r.get("started_at_utc"),
                finished_at_utc=r.get("finished_at_utc"),
                error_message=r.get("error_message"),
            )
            for r in rows
        ]

    def get_job_events(self, job_id: str) -> list[dict[str, Any]]:
        """Retrieve state transition events for a job from host_job_events."""
        return get_host_job_events(job_id, conn=self._db_path)

    def shutdown(self, *, wait: bool = True, cancel_futures: bool = False) -> None:
        """Shut down the worker pool executor and stop background watchdogs."""
        self._resource_mgr.watchdog.stop()
        if cancel_futures:
            with self._lock:
                active_ids = [
                    jid
                    for jid, record in self._jobs.items()
                    if record.status
                    in {
                        str(JobState.QUEUED),
                        str(JobState.RUNNING),
                        str(JobState.PAUSED),
                    }
                ]
            for jid in active_ids:
                self.cancel_job(jid)
        with self._lock:
            pool = self._pool
            self._pool = None
            io_pool = self._io_pool
            self._io_pool = None
        if pool is not None:
            pool.shutdown(wait=wait, cancel_futures=cancel_futures)
            logger.info(
                "%s: shut down worker pool executor",
                POOL_LIFECYCLE_FR,
                extra={"fr_id": POOL_LIFECYCLE_FR},
            )
        if io_pool is not None:
            io_pool.shutdown(wait=wait, cancel_futures=cancel_futures)
            logger.info(
                "%s: shut down I/O worker pool executor",
                POOL_LIFECYCLE_FR,
                extra={"fr_id": POOL_LIFECYCLE_FR},
            )


def run_sample_compute_task(
    ctx: JobContext,
    iterations: int = 5_000,
    step_sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    """Top-level picklable task demonstrating multiprocessing and JobContext."""
    total = max(1, iterations)
    acc = 0.0
    check_step = max(1, total // 10)
    for idx in range(1, total + 1):
        if idx % check_step == 0:
            ctx.raise_if_cancelled()
            ctx.wait_if_paused()
            ctx.report_progress((idx / total) * 100.0, f"Step {idx}/{total}")
            if step_sleep_seconds > 0.0:
                time.sleep(step_sleep_seconds)
        acc += (idx * 0.5) / (idx + 1.0)
    return {
        "job_id": ctx.job_id,
        "worker_pid": os.getpid(),
        "iterations": total,
        "checksum": round(acc, 4),
    }


def main() -> None:
    """Demonstrate multiprocessing JobManager, JobContext, and orphan reconciliation."""
    print("=== 1. Startup Orphan Job Reconciliation ===")
    mgr = JobManager(max_workers=2)
    try:
        reconciled = mgr.reconcile_orphan_jobs()
        print(f"Reconciled orphan RUNNING jobs: {len(reconciled)}")

        print("=== 2. Multiprocessing Task Submission (ProcessPoolExecutor) ===")
        submitted = mgr.submit_job(
            run_sample_compute_task,
            2_500,
            owner="cli-demo",
            kind="compute",
        )
        completed = mgr.wait_for_job(submitted.job_id, timeout=15.0)
        print(
            f"Job {completed.job_id} finished with status={completed.status} "
            f"on worker_pid={completed.worker_pid} (host_pid={os.getpid()})",
        )
    finally:
        mgr.shutdown()


if __name__ == "__main__":
    main()
