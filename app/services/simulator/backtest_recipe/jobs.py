"""Bounded background execution for canonical backtest runs.

A canonical run over a year of bars takes far longer than the API's 30-second
endpoint deadline, so a run cannot be served inside one request. This registry
executes each run on a worker thread with its own event loop, records ordered
progress events, and holds the terminal outcome for later retrieval.

The registry is deliberately in-process and bounded: it is run scratch state,
not durable evidence. Simulation remains the owner of the durable journal,
result, and artifacts that the run itself produces.
"""

from __future__ import annotations

import asyncio
import threading
from collections import OrderedDict, deque
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from app.services.simulator.backtest_recipe.evidence import (
    BacktestRunEvidence,
    CompletionSink,
)
from app.services.simulator.backtest_recipe.pipeline import (
    BacktestRunConfig,
    run_strategy_backtest,
    utc_now,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

type JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]

_TERMINAL: frozenset[str] = frozenset({"succeeded", "failed", "cancelled"})
_DEFAULT_MAX_JOBS = 32
_DEFAULT_MAX_EVENTS = 500


class BacktestCancelledError(Exception):
    """Raised inside a run when the operator cancels it."""


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One ordered progress record emitted by a running job."""

    sequence: int
    at: datetime
    stage: str
    detail: str


@dataclass
class BacktestJob:
    """Mutable state for one submitted backtest run."""

    job_id: str
    principal_id: str
    config: BacktestRunConfig
    status: JobStatus = "queued"
    submitted_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stage: str | None = None
    events: deque[ProgressEvent] = field(
        default_factory=lambda: deque(maxlen=_DEFAULT_MAX_EVENTS)
    )
    result: dict[str, Any] | None = None
    error: str | None = None
    _sequence: int = 0
    cancel_requested: threading.Event = field(default_factory=threading.Event)
    _updated: threading.Condition = field(default_factory=threading.Condition)

    @property
    def terminal(self) -> bool:
        """Whether the job has reached a terminal status.

        Returns:
            True once the job succeeded, failed, or was cancelled.
        """
        return self.status in _TERMINAL

    def snapshot(self) -> dict[str, Any]:
        """Return a bounded read-only projection of current job state.

        Returns:
            Serializable job state including the terminal outcome when present.
        """
        with self._updated:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "stage": self.stage,
                "submitted_at": self.submitted_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "symbol": self.config.symbol,
                "timeframe": self.config.timeframe,
                "strategy_id": self.config.strategy_id,
                "events": tuple(
                    {
                        "sequence": event.sequence,
                        "at": event.at,
                        "stage": event.stage,
                        "detail": event.detail,
                    }
                    for event in self.events
                ),
                "result": self.result,
                "error": self.error,
            }

    def record(self, stage: str, detail: str) -> None:
        """Append one ordered progress event and wake any waiters.

        Args:
            stage: Current pipeline stage name.
            detail: Human-readable stage detail.
        """
        with self._updated:
            self._sequence += 1
            self.stage = stage
            self.events.append(
                ProgressEvent(
                    sequence=self._sequence,
                    at=utc_now(),
                    stage=stage,
                    detail=detail,
                )
            )
            self._updated.notify_all()

    def transition(self, status: JobStatus, **values: object) -> None:
        """Apply one status transition and wake any waiters.

        Args:
            status: New job status.
            **values: Additional job fields to set.
        """
        with self._updated:
            self.status = status
            for name, value in values.items():
                setattr(self, name, value)
            self._updated.notify_all()

    def request_cancel(self) -> bool:
        """Request cooperative cancellation of this job.

        Returns:
            True when cancellation was requested, False when already terminal.
        """
        with self._updated:
            if self.terminal:
                return False
            if self.status == "queued":
                self.status = "cancelled"
                self.finished_at = utc_now()
                self.error = "cancelled before execution started"
                self._updated.notify_all()
                self.cancel_requested.set()
                return True
        self.cancel_requested.set()
        return True

    def wait_for_change(self, after: int, timeout: float) -> bool:
        """Block until a newer event exists, the job ends, or timeout elapses.

        Args:
            after: Highest sequence number the caller has already observed.
            timeout: Maximum seconds to wait.

        Returns:
            True when new state is available, False on timeout.
        """
        with self._updated:
            if self._sequence > after or self.terminal:
                return True
            return self._updated.wait_for(
                lambda: self._sequence > after or self.terminal, timeout=timeout
            )

    def events_after(self, after: int) -> tuple[ProgressEvent, ...]:
        """Return ordered events newer than a caller cursor.

        Args:
            after: Highest sequence number already observed.

        Returns:
            Ordered progress events with a greater sequence number.
        """
        with self._updated:
            return tuple(event for event in self.events if event.sequence > after)


class BacktestJobRegistry:
    """Bounded in-process registry executing backtest runs off the event loop."""

    def __init__(
        self,
        *,
        facts_loader: Callable[[BacktestRunConfig], Any],
        runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
        max_jobs: int = _DEFAULT_MAX_JOBS,
        completion_sink: CompletionSink | None = None,
    ) -> None:
        """Build one registry bound to a provider-facts loader.

        Args:
            facts_loader: Callable returning verified provider facts for a run.
            runtime_context: Factory for the runtime context a run needs. A job
                executes on its own thread, so any ContextVar established for
                the submitting request's task is invisible to it and must be
                re-entered here.
            max_jobs: Maximum retained jobs before the oldest terminal job is
                evicted.
            completion_sink: Optional callable receiving the complete terminal
                evidence of each successful run exactly once, before registry
                eviction can discard it.
        """
        self._facts_loader = facts_loader
        self._runtime_context = runtime_context
        self._max_jobs = max_jobs
        self._completion_sink = completion_sink
        self._jobs: OrderedDict[str, BacktestJob] = OrderedDict()
        self._lock = threading.Lock()

    def submit(self, config: BacktestRunConfig, *, principal_id: str) -> BacktestJob:
        """Validate and start one backtest run on a worker thread.

        Args:
            config: Operator-chosen run configuration.
            principal_id: Authenticated principal owning the run.

        Returns:
            The registered job in its initial state.

        Raises:
            ValueError: If the configuration is invalid.
        """
        config.validate()
        job = BacktestJob(
            job_id=generate_id("btr"), principal_id=principal_id, config=config
        )
        with self._lock:
            self._evict_locked()
            self._jobs[job.job_id] = job
        thread = threading.Thread(
            target=self._execute,
            args=(job,),
            name=f"backtest-{job.job_id}",
            daemon=True,
        )
        thread.start()
        return job

    def get(self, job_id: str, *, principal_id: str) -> BacktestJob | None:
        """Return one job owned by the requesting principal.

        Args:
            job_id: Registered job identifier.
            principal_id: Authenticated principal.

        Returns:
            The job, or None when unknown or owned by another principal.
        """
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None or job.principal_id != principal_id:
            return None
        return job

    def list_jobs(self, *, principal_id: str) -> tuple[BacktestJob, ...]:
        """Return the principal's jobs, newest first.

        Args:
            principal_id: Authenticated principal.

        Returns:
            Retained jobs owned by the principal.
        """
        with self._lock:
            jobs = tuple(self._jobs.values())
        return tuple(
            sorted(
                (job for job in jobs if job.principal_id == principal_id),
                key=lambda job: job.submitted_at,
                reverse=True,
            )
        )

    def _evict_locked(self) -> None:
        """Evict the oldest terminal jobs while the registry is over its bound."""
        while len(self._jobs) >= self._max_jobs:
            for job_id, job in self._jobs.items():
                if job.terminal:
                    del self._jobs[job_id]
                    break
            else:
                # Nothing terminal to reclaim; drop the oldest entry outright.
                self._jobs.popitem(last=False)

    def _sink_for(self, job: BacktestJob) -> CompletionSink | None:
        """Bind job identity onto the completion sink for attribution.

        The evidence projection built inside the pipeline carries no job or
        principal identity because the pipeline only sees the run config, so
        downstream durable catalogues could not attribute terminal evidence
        to its owning job and principal without this enrichment.

        Args:
            job: Registered job whose evidence the sink will receive.

        Returns:
            A sink enriching the evidence projection with ``job_id`` and
            ``principal_id``, or None when no sink is configured.
        """
        if self._completion_sink is None:
            return None
        base_sink = self._completion_sink

        def sink_with_job_identity(evidence: BacktestRunEvidence) -> None:
            enriched_projection = {
                **evidence.projection,
                "job_id": job.job_id,
                "principal_id": job.principal_id,
            }
            base_sink(
                BacktestRunEvidence(
                    projection=enriched_projection,
                    simulation_result=evidence.simulation_result,
                    performance_report=evidence.performance_report,
                )
            )

        return sink_with_job_identity

    def _execute(self, job: BacktestJob) -> None:
        """Run one job to completion on its own event loop.

        Args:
            job: Registered job to execute.
        """
        if job.cancel_requested.is_set():
            return
        job.transition("running", started_at=utc_now())

        def progress(stage: str, detail: str) -> None:
            """Record progress and honour a cancellation request.

            Args:
                stage: Current pipeline stage name.
                detail: Human-readable stage detail.

            Raises:
                BacktestCancelledError: If cancellation has been requested.
            """
            if job.cancel_requested.is_set():
                raise BacktestCancelledError
            job.record(stage, detail)

        try:
            context = (
                self._runtime_context() if self._runtime_context else nullcontext()
            )
            with context:
                facts = self._facts_loader(job.config)
                result = asyncio.run(
                    run_strategy_backtest(
                        job.config,
                        facts=facts,
                        progress=progress,
                        completion_sink=self._sink_for(job),
                    )
                )
        except BacktestCancelledError:
            job.transition(
                "cancelled",
                finished_at=utc_now(),
                error="cancelled by operator",
            )
        except Exception as error:  # noqa: BLE001 - terminal job outcome.
            logger.warning("Backtest job %s failed: %s", job.job_id, error)
            job.transition(
                "failed",
                finished_at=utc_now(),
                error=str(error) or type(error).__name__,
            )
        else:
            job.transition("succeeded", finished_at=utc_now(), result=result)

    def stream(
        self, job: BacktestJob, *, after: int = 0, heartbeat_seconds: float = 15.0
    ) -> Iterator[dict[str, Any]]:
        """Yield ordered progress frames until the job reaches a terminal state.

        Args:
            job: Registered job to observe.
            after: Highest sequence number the caller already observed.
            heartbeat_seconds: Idle interval after which a heartbeat is emitted.

        Yields:
            Progress, heartbeat, and one terminal frame.
        """
        cursor = after
        while True:
            for event in job.events_after(cursor):
                cursor = event.sequence
                yield {
                    "kind": "progress",
                    "sequence": event.sequence,
                    "at": event.at,
                    "stage": event.stage,
                    "detail": event.detail,
                }
            if job.terminal:
                yield {"kind": "terminal", "sequence": cursor, **job.snapshot()}
                return
            if not job.wait_for_change(cursor, heartbeat_seconds):
                yield {"kind": "heartbeat", "sequence": cursor, "at": utc_now()}


__all__ = (
    "BacktestCancelledError",
    "BacktestJob",
    "BacktestJobRegistry",
    "JobStatus",
    "ProgressEvent",
)
