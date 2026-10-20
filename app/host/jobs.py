# ruff: noqa: INP001
"""Multiprocessing background job coordinator, cancellation context, and recovery.

Description:
    Coordinates CPU-bound and long-running background workloads for the HaruQuantAI
    host platform using an OS multiprocessing worker pool (ProcessPoolExecutor) to
    bypass Python's Global Interpreter Lock (GIL). Works with app/host/resources.py
    to size worker concurrency via workers = max(1, cpu_cores - 2), provision
    isolated per-job scratch directories, and enforce the active Memory Watchdog
    (15% RAM floor). Provides picklable cross-process JobContext cancellation tokens,
    persists job lifecycle events via HostPersistence, and reconciles orphan RUNNING
    jobs on startup by marking them INTERRUPTED.

Purpose:
    FEAT-HOST-JOBS: Host multiprocessing job pool, cooperative cancellation,
    memory-pressure gating, and startup orphan job reconciliation.

Key Capabilities:
    - FR-HOST-JOBS-POOL-LIFECYCLE: Manage ProcessPoolExecutor (ensure_pool -> INFO).
    - FR-HOST-JOBS-SUBMISSION: Submit and track jobs (submit_job -> INFO, ERROR).
    - FR-HOST-JOBS-WATCHDOG-GATE: 15% RAM admission gate (check_admission -> WARNING).
    - FR-HOST-JOBS-CANCELLATION: Cooperative JobContext tokens (cancel_job -> INFO).
    - FR-HOST-JOBS-RECONCILIATION: Recover orphan jobs (reconcile_orphan_jobs -> INFO).
    - FR-HOST-JOBS-PERSISTENCE: Persist job records and events (get_job -> DEBUG).

Python API Usage:
    ```python
    from app.host.jobs import JobManager, run_sample_compute_task

    manager = JobManager()
    record = manager.submit_job(run_sample_compute_task, 5_000, owner="researcher")
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
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
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


def _log(level: str, fr_id: str, msg: str, **extra: Any) -> None:
    """Emit structured FR log record with fr_id context."""
    getattr(logger, level)("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


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


def _row_to_record(r: Mapping[str, Any]) -> JobRecord:
    """Convert a persisted host_jobs row dictionary into a JobRecord."""
    own = str(r.get("owner", "default"))
    knd, st = str(r.get("kind", "compute")), str(r.get("status", ""))
    prg, msg = float(r.get("progress", 0.0)), str(r.get("message", ""))
    att, sub = int(r.get("attempt_id", 1)), str(r.get("submitted_at_utc", ""))
    sta, fin = r.get("started_at_utc"), r.get("finished_at_utc")
    return JobRecord(
        str(r["job_id"]),
        own,
        knd,
        st,
        prg,
        msg,
        att,
        sub,
        sta,
        fin,
        r.get("error_message"),
    )


class JobContext:
    """Picklable cooperative cancellation, pause, and progress context for jobs."""

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
        _log("info", CANCELLATION_FR, f"cancellation signaled for job {self.job_id}")

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
            msg = f"job {self.job_id} observed cancellation token and is terminating"
            _log("info", CANCELLATION_FR, msg, job_id=self.job_id)
            raise JobCancelledError(f"Job '{self.job_id}' was cancelled.")

    def wait_if_paused(
        self, *, poll_interval: float = 0.02, timeout: float | None = None
    ) -> None:
        """Block cooperatively while the job is paused, checking cancellation."""
        start = time.monotonic()
        while self.is_paused():
            self.raise_if_cancelled()
            if timeout is not None and (time.monotonic() - start) >= timeout:
                break
            time.sleep(max(0.005, poll_interval))
        self.raise_if_cancelled()

    def check_memory_guard(self, *, policy: str = "reject") -> MemoryWatchdogStatus:
        """Check system RAM headroom from inside a running task."""
        status = check_memory_headroom(self.min_available_ram_pct, policy=policy)
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
            self._progress_marker.write_text(json.dumps(payload), encoding="utf-8")
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
        return first.name in (
            "ctx",
            "context",
            "job_context",
        ) or "JobContext" in str(first.annotation)
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
        *,
        max_workers: int | None = None,
        resource_mgr: ResourceManager | None = None,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        memory_policy: str = "reject",
        use_process_pool: bool = True,
        cleanup_scratch_on_exit: bool = True,
        reconcile_on_startup: bool = False,
    ) -> None:
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
        det = f"workers={self._max_workers}, policy={self._memory_policy}"
        _log("info", POOL_LIFECYCLE_FR, f"initialized JobManager ({det})")
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
                cls = (
                    ProcessPoolExecutor
                    if self._use_process_pool
                    else ThreadPoolExecutor
                )
                self._pool = cls(max_workers=self._max_workers)
                msg = f"started {cls.__name__} with {self._max_workers} workers"
                _log("info", POOL_LIFECYCLE_FR, msg, max_workers=self._max_workers)
            return self._pool

    def ensure_io_pool(self) -> ThreadPoolExecutor:
        """Lazily create and return the dedicated I/O thread pool executor."""
        with self._lock:
            if self._io_pool is None:
                w = min(4, self._max_workers)
                self._io_pool = ThreadPoolExecutor(max_workers=w)
                _log("info", POOL_LIFECYCLE_FR, f"started I/O pool with {w} workers")
            return self._io_pool

    def _save_job(self, job_id: str, **fields: Any) -> int:
        """Persist or upsert a job record via HostPersistence."""
        return HostPersistence.update_record(
            "host_jobs", pk_values={"job_id": job_id}, updates=fields, upsert=True
        )

    def _update_job(self, job_id: str, updates: Mapping[str, Any]) -> bool:
        """Update an existing job record via HostPersistence."""
        return (
            HostPersistence.update_record(
                "host_jobs", pk_values={"job_id": job_id}, updates=updates
            )
            > 0
        )

    def _record_event(
        self,
        job_id: str,
        from_state: str | None,
        to_state: str,
        details: Mapping[str, Any],
        created_at_utc: str | None = None,
    ) -> str:
        """Insert a job state transition event via HostPersistence."""
        data = {
            "event_id": f"evt-{uuid.uuid4().hex[:12]}",
            "job_id": job_id,
            "attempt_id": None,
            "from_state": from_state,
            "to_state": to_state,
            "details_json": json.dumps(dict(details)),
            "created_at_utc": created_at_utc or datetime.now(UTC).isoformat(),
        }
        return str(HostPersistence.create_record("host_job_events", data))

    def reconcile_orphan_jobs(self) -> list[str]:
        """Mark orphan jobs left in RUNNING state as INTERRUPTED on system boot."""
        reconciled_ids: list[str] = []
        try:
            all_jobs = HostPersistence.read_records("host_jobs", limit=1_000)
        except Exception as exc:  # noqa: BLE001
            msg = f"could not query host_jobs during startup reconciliation: {exc}"
            _log("warning", RECONCILIATION_FR, msg, error=str(exc))
            return reconciled_ids

        now_iso = datetime.now(UTC).isoformat()
        for row in all_jobs:
            if str(row.get("status", "")).upper() == JobState.RUNNING:
                jid = str(row["job_id"])
                err_msg = "Orphan job left in RUNNING state marked INTERRUPTED on boot"
                upd = {
                    "status": str(JobState.INTERRUPTED),
                    "finished_at_utc": now_iso,
                    "message": "Interrupted by host restart",
                    "error_message": err_msg,
                }
                self._update_job(jid, upd)
                self._record_event(
                    jid,
                    str(JobState.RUNNING),
                    str(JobState.INTERRUPTED),
                    {"reason": "startup_orphan_recovery"},
                    now_iso,
                )
                self._resource_mgr.cleanup_scratch(jid)
                reconciled_ids.append(jid)
                msg = f"reconciled orphan RUNNING job {jid} -> INTERRUPTED"
                _log("warning", RECONCILIATION_FR, msg, job_id=jid)

        cnt = len(reconciled_ids)
        _log("info", RECONCILIATION_FR, f"orphan job reconciliation complete ({cnt})")
        return reconciled_ids

    def check_admission(
        self, *, on_memory_pressure: str | None = None
    ) -> MemoryWatchdogStatus:
        """Evaluate the 15% available RAM watchdog before starting a task."""
        pol = (
            on_memory_pressure.strip().lower()
            if on_memory_pressure is not None
            else self._memory_policy
        )
        st = self._resource_mgr.check_memory_headroom(policy=pol)
        if st.is_pressured:
            det = f"avail={st.available_pct:.1f}%, action={st.recommended_action}"
            _log("warning", WATCHDOG_GATE_FR, f"memory watchdog triggered ({det})")
        return st

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
        """Submit a task to the multiprocessing worker pool with watchdog gating."""
        jid = job_id or f"job-{uuid.uuid4().hex[:10]}"
        sub_at = datetime.now(UTC).isoformat()
        eff_pol = (
            on_memory_pressure.strip().lower()
            if on_memory_pressure is not None
            else self._memory_policy
        )

        st = self.check_admission(on_memory_pressure=eff_pol)
        if st.is_pressured and st.recommended_action == "REJECT":
            err_text = (
                f"Task rejected by Memory Watchdog: available RAM "
                f"({st.available_pct:.1f}%) is below {st.threshold_pct:.1f}% minimum."
            )
            r_msg = "Rejected by Memory Watchdog (<15% available RAM)"
            kw = {"submitted_at_utc": sub_at, "finished_at_utc": sub_at}
            self._save_job(
                jid,
                owner=owner,
                kind=kind,
                status=str(JobState.FAILED),
                rejected=1,
                message=r_msg,
                error_message=err_text,
                **kw,
            )
            det = {
                "reason": "memory_watchdog_reject",
                "available_pct": st.available_pct,
            }
            self._record_event(jid, None, str(JobState.FAILED), det, sub_at)
            raise MemoryPressureError(err_text)

        s_dir = self._resource_mgr.allocate_scratch(jid)
        ctx = JobContext(
            job_id=jid,
            scratch_dir=s_dir,
            min_available_ram_pct=self._min_available_ram_pct,
            cancel_event=threading.Event(),
            pause_event=threading.Event(),
        )
        done_evt = threading.Event()
        p_ctx = (
            pass_context
            if pass_context is not None
            else _callable_accepts_job_context(fn)
        )
        d1 = (jid, fn, args, kwargs, p_ctx, ctx)
        d2 = (owner, kind, sub_at, done_evt, executor_kind)
        deferred = _DeferredSubmission(*d1, *d2)

        if st.is_pressured and st.recommended_action == "PAUSE":
            ctx.set_paused(True)
            p_msg = "Paused by Memory Watchdog (<15% available RAM)"
            a1 = (jid, owner, kind, str(JobState.PAUSED), 0.0, p_msg, 1, sub_at)
            paused_rec = JobRecord(*a1, scratch_dir=str(s_dir))
            self._save_job(
                jid,
                owner=owner,
                kind=kind,
                status=str(JobState.PAUSED),
                accepted=1,
                message=p_msg,
                submitted_at_utc=sub_at,
            )
            det = {"reason": "memory_watchdog_pause", "available_pct": st.available_pct}
            self._record_event(
                jid, str(JobState.QUEUED), str(JobState.PAUSED), det, sub_at
            )
            with self._lock:
                self._jobs[jid] = paused_rec
                self._contexts[jid] = ctx
                self._done_events[jid] = done_evt
                self._paused_queue[jid] = deferred
            _log("warning", WATCHDOG_GATE_FR, f"job {jid} queued in PAUSED state")
            return paused_rec

        return self._dispatch_to_pool(deferred)

    def _dispatch_to_pool(self, sub: _DeferredSubmission) -> JobRecord:
        """Dispatch an admitted job to the worker pool executor."""
        jid, owner, kind, ctx = sub.job_id, sub.owner, sub.kind, sub.context
        started_at = datetime.now(UTC).isoformat()
        a1 = (jid, owner, kind, str(JobState.RUNNING), 0.0, "Running", 1)
        running_rec = JobRecord(
            *a1,
            sub.submitted_at_utc,
            started_at_utc=started_at,
            scratch_dir=str(ctx.scratch_dir),
        )
        self._save_job(
            jid,
            owner=owner,
            kind=kind,
            status=str(JobState.RUNNING),
            accepted=1,
            message="Running",
            submitted_at_utc=sub.submitted_at_utc,
            started_at_utc=started_at,
        )
        self._record_event(
            jid,
            str(JobState.QUEUED),
            str(JobState.RUNNING),
            {"owner": owner, "kind": kind},
            started_at,
        )
        pool: ProcessPoolExecutor | ThreadPoolExecutor = (
            self.ensure_io_pool()
            if sub.executor_kind == "thread"
            else self.ensure_pool()
        )
        with self._lock:
            self._jobs[jid] = running_rec
            self._contexts[jid] = ctx
            self._done_events[jid] = sub.done_event
            fut = pool.submit(
                _execute_worker_task,
                sub.fn,
                ctx,
                sub.pass_context,
                sub.args,
                sub.kwargs,
            )
            self._futures[jid] = fut

        fut.add_done_callback(functools.partial(self._on_future_done, jid))
        _log("info", SUBMISSION_FR, f"submitted job {jid} ({owner}/{kind})", job_id=jid)
        return running_rec

    @staticmethod
    def _extract_future_outcome(
        job_id: str, future: Future[tuple[int, Any]], ctx: JobContext | None
    ) -> tuple[int, Any]:
        """Extract worker PID and result or raise JobCancelledError."""
        if future.cancelled() or (ctx is not None and ctx.is_cancelled()):
            raise JobCancelledError(f"Job '{job_id}' cancelled.")
        return future.result()

    def _on_future_done(self, job_id: str, future: Future[tuple[int, Any]]) -> None:
        """Handle completion, failure, or cancellation of a worker pool future."""
        fin_at = datetime.now(UTC).isoformat()
        with self._lock:
            cur = self._jobs.get(job_id)
            ctx = self._contexts.get(job_id)
            done_evt = self._done_events.get(job_id)

        base = cur or JobRecord(
            job_id, "default", "compute", str(JobState.RUNNING), 0.0, "", 1, fin_at
        )
        pid, res, err_s = None, None, None
        prg = base.progress
        try:
            pid, res = self._extract_future_outcome(job_id, future, ctx)
            st_v, prg, msg_v = str(JobState.COMPLETED), 100.0, "Completed"
            det: dict[str, Any] = {"worker_pid": pid}
            _log("info", SUBMISSION_FR, f"job {job_id} completed on PID {pid}")
        except JobCancelledError as exc:
            st_v, msg_v, err_s = str(JobState.CANCELLED), "Cancelled by user", str(exc)
            det = {"reason": err_s}
            _log("info", CANCELLATION_FR, f"job {job_id} transitioned to CANCELLED")
        except Exception as exc:  # noqa: BLE001
            st_v, msg_v, err_s = str(JobState.FAILED), "Failed", str(exc)
            det = {"error": err_s}
            _log("exception", SUBMISSION_FR, f"job {job_id} failed during execution")

        final_rec = replace(
            base,
            status=st_v,
            progress=prg,
            message=msg_v,
            finished_at_utc=fin_at,
            error_message=err_s,
            result=res,
            worker_pid=pid,
        )
        upd: dict[str, Any] = {
            "status": st_v,
            "progress": prg,
            "message": msg_v,
            "finished_at_utc": fin_at,
            "error_message": err_s,
        }
        self._update_job(job_id, upd)
        self._record_event(job_id, str(JobState.RUNNING), final_rec.status, det, fin_at)
        if self._cleanup_scratch_on_exit:
            self._resource_mgr.cleanup_scratch(job_id)
        with self._lock:
            self._jobs[job_id] = final_rec
        if done_evt is not None:
            done_evt.set()

    def cancel_job(self, job_id: str) -> bool:
        """Signal cooperative cancellation for a queued, paused, or running job."""
        with self._lock:
            ctx, fut = self._contexts.get(job_id), self._futures.get(job_id)
            deferred = self._paused_queue.pop(job_id, None)
            current, done_evt = self._jobs.get(job_id), self._done_events.get(job_id)

        if ctx is None and current is None:
            return False
        if ctx is not None:
            ctx.cancel()
            ctx.set_paused(False)
        if fut is not None:
            fut.cancel()

        if deferred is not None:
            now_iso = datetime.now(UTC).isoformat()
            err = "Cancelled by user while paused"
            a1 = (job_id, deferred.owner, deferred.kind, str(JobState.CANCELLED), 0.0)
            a2 = ("Cancelled while paused", 1, deferred.submitted_at_utc)
            c_rec = JobRecord(
                *a1,
                *a2,
                finished_at_utc=now_iso,
                error_message=err,
                scratch_dir=str(deferred.context.scratch_dir),
            )
            upd = {
                "status": str(JobState.CANCELLED),
                "message": c_rec.message,
                "finished_at_utc": now_iso,
                "error_message": err,
            }
            self._update_job(job_id, upd)
            self._record_event(
                job_id,
                str(JobState.PAUSED),
                str(JobState.CANCELLED),
                {"reason": "user_cancelled_paused_job"},
                now_iso,
            )
            if self._cleanup_scratch_on_exit:
                self._resource_mgr.cleanup_scratch(job_id)
            with self._lock:
                self._jobs[job_id] = c_rec
            if done_evt is not None:
                done_evt.set()

        _log("info", CANCELLATION_FR, f"requested cancellation for job {job_id}")
        return True

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job cooperatively."""
        with self._lock:
            ctx, curr = self._contexts.get(job_id), self._jobs.get(job_id)
        if ctx is None or curr is None or curr.status != str(JobState.RUNNING):
            return False
        ctx.set_paused(True)
        with self._lock:
            self._jobs[job_id] = replace(
                curr, status=str(JobState.PAUSED), message="Paused"
            )
        self._update_job(job_id, {"status": str(JobState.PAUSED), "message": "Paused"})
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job when RAM headroom permits."""
        with self._lock:
            deferred = self._paused_queue.pop(job_id, None)
            ctx, curr = self._contexts.get(job_id), self._jobs.get(job_id)

        if deferred is not None:
            deferred.context.set_paused(False)
            self._dispatch_to_pool(deferred)
            return True

        if ctx is not None and curr is not None and curr.status == str(JobState.PAUSED):
            ctx.set_paused(False)
            with self._lock:
                self._jobs[job_id] = replace(
                    curr, status=str(JobState.RUNNING), message="Running"
                )
            self._update_job(
                job_id, {"status": str(JobState.RUNNING), "message": "Running"}
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
        if self._resource_mgr.check_memory_headroom(policy="pause").is_pressured:
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

    def wait_for_job(self, job_id: str, *, timeout: float = 10.0) -> JobRecord:
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
            mem_rec, ctx = self._jobs.get(job_id), self._contexts.get(job_id)

        if (
            mem_rec is not None
            and ctx is not None
            and mem_rec.status == str(JobState.RUNNING)
        ):
            prog = ctx.read_progress()
            if prog is not None:
                pct, msg = prog
                mem_rec = replace(mem_rec, progress=pct, message=msg or mem_rec.message)

        if mem_rec is not None:
            msg = f"retrieved in-memory job {job_id} (status={mem_rec.status})"
            _log("debug", PERSISTENCE_FR, msg, job_id=job_id)
            return mem_rec

        rows = HostPersistence.read_records(
            "host_jobs", pk_values={"job_id": job_id}, limit=1
        )
        if not rows:
            return None
        row = rows[0]
        msg = f"retrieved persisted job {job_id} (status={row.get('status')})"
        _log("debug", PERSISTENCE_FR, msg, job_id=job_id)
        return _row_to_record(row)

    def list_jobs(
        self, *, status: str | None = None, limit: int = 100
    ) -> list[JobRecord]:
        """List persisted jobs from host_jobs table."""
        where = {"status": status} if status else None
        rows = HostPersistence.read_records("host_jobs", where=where, limit=limit)
        msg = f"listed {len(rows)} persisted jobs (status={status})"
        _log("debug", PERSISTENCE_FR, msg, count=len(rows))
        return [_row_to_record(r) for r in rows]

    def get_job_events(self, job_id: str) -> list[dict[str, Any]]:
        """Retrieve state transition events for a job from host_job_events."""
        return HostPersistence.read_records(
            "host_job_events", where={"job_id": job_id}, order_by="created_at_utc ASC"
        )

    def shutdown(self, *, wait: bool = True, cancel_futures: bool = False) -> None:
        """Shut down the worker pool executor and stop background watchdogs."""
        self._resource_mgr.watchdog.stop()
        if cancel_futures:
            active_states = {
                str(JobState.QUEUED),
                str(JobState.RUNNING),
                str(JobState.PAUSED),
            }
            with self._lock:
                active_ids = [
                    jid
                    for jid, rec in self._jobs.items()
                    if rec.status in active_states
                ]
            for jid in active_ids:
                self.cancel_job(jid)
        with self._lock:
            pool, self._pool = self._pool, None
            io_pool, self._io_pool = self._io_pool, None
        if pool is not None:
            pool.shutdown(wait=wait, cancel_futures=cancel_futures)
            _log("info", POOL_LIFECYCLE_FR, "shut down worker pool executor")
        if io_pool is not None:
            io_pool.shutdown(wait=wait, cancel_futures=cancel_futures)
            _log("info", POOL_LIFECYCLE_FR, "shut down I/O worker pool executor")


def run_sample_compute_task(
    ctx: JobContext, iterations: int = 5_000, step_sleep_seconds: float = 0.0
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
    mgr = JobManager(max_workers=2)
    try:
        mgr.reconcile_orphan_jobs()
        submitted = mgr.submit_job(
            run_sample_compute_task, 2_500, owner="cli-demo", kind="compute"
        )
        mgr.wait_for_job(submitted.job_id, timeout=15.0)
    finally:
        mgr.shutdown()


if __name__ == "__main__":
    main()
