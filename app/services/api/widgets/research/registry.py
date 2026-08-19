"""Principal-scoped experiment, run, and batch lifecycle for the workbench.

A complete Research pass takes far longer than an endpoint deadline, so a run
is a job: submission returns an identity immediately, execution happens on a
worker thread, and progress is observed by polling or by consuming the ordered
event stream. This mirrors the canonical Simulator job pattern rather than
inventing a second protocol.

The registry stores run identities, ordered events, and terminal reports for
the life of the process. It stores no browser state and makes no scientific
decision — the report it retains is the one Research authored.
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final, Literal, Protocol, cast

from app.services.api.widgets.research.projections import (
    hydrate_report,
    project_report,
)
from app.utils import generate_id, get_logger, utc_now

logger = get_logger(__name__)

type JsonValue = Any
type RunStatus = Literal["queued", "running", "completed", "failed", "cancelled"]

#: Retained runs per principal. Older terminal runs are evicted first.
_MAX_RUNS_PER_PRINCIPAL: Final[int] = 200
#: Retained ordered events per run.
_MAX_EVENTS_PER_RUN: Final[int] = 512
#: Seconds a stream waits before emitting a heartbeat frame.
_HEARTBEAT_SECONDS: Final[float] = 15.0


@dataclass(slots=True)
class ResearchExperiment:
    """One durable-in-process research question and its run ledger."""

    experiment_id: str
    principal_id: str
    name: str
    hypothesis: str
    notes: str | None
    tags: tuple[str, ...]
    created_at: datetime

    def summary(
        self, *, run_count: int, latest: Mapping[str, JsonValue] | None
    ) -> Mapping[str, JsonValue]:
        """Project one experiment summary.

        Args:
            run_count: Number of retained runs for this experiment.
            latest: Most recent run summary, or ``None``.

        Returns:
            JSON-safe experiment summary.
        """
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "notes": self.notes,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat(),
            "run_count": run_count,
            "latest_run": latest,
        }


@dataclass(slots=True)
class ResearchRun:
    """One background Research run and everything observed about it."""

    run_id: str
    experiment_id: str
    principal_id: str
    hypothesis: str
    symbol: str
    timeframe: str
    preset: str
    selected_stages: tuple[str, ...]
    reason: str | None
    force_rerun: bool
    batch_id: str | None
    request_material: Mapping[str, JsonValue]
    created_at: datetime
    status: RunStatus = "queued"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    report: object | None = None
    dataset: Mapping[str, JsonValue] | None = None
    effective_configuration: Mapping[str, JsonValue] | None = None
    artifacts: tuple[Mapping[str, JsonValue], ...] = ()
    error: Mapping[str, JsonValue] | None = None
    events: list[Mapping[str, JsonValue]] = field(default_factory=list)
    cancel_requested: bool = False


class _ResearchRunStore(Protocol):
    """Narrow durable-store contract consumed by the workbench registry."""

    @property
    def persist_research_experiment(self) -> Callable[..., None]:
        """Return the experiment writer."""
        ...

    @property
    def load_research_experiments(
        self,
    ) -> Callable[..., Sequence[Mapping[str, JsonValue]]]:
        """Return the experiment reader."""
        ...

    @property
    def persist_research_run(self) -> Callable[..., None]:
        """Return the run writer."""
        ...

    @property
    def load_research_runs(
        self,
    ) -> Callable[..., Sequence[Mapping[str, JsonValue]]]:
        """Return the run reader."""
        ...

    @property
    def persist_research_run_batch(self) -> Callable[..., None]:
        """Return the batch writer."""
        ...

    @property
    def load_research_run_batches(
        self,
    ) -> Callable[..., Sequence[Mapping[str, JsonValue]]]:
        """Return the batch reader."""
        ...


class ResearchWorkbenchRegistry:
    """Thread-safe in-process store for experiments, runs, and batches."""

    def __init__(
        self,
        *,
        executor: Callable[[ResearchRun, Callable[..., None]], Mapping[str, JsonValue]],
        runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
        store: _ResearchRunStore | None = None,
    ) -> None:
        """Create one workbench registry.

        Args:
            executor: Callable performing one run and returning its result
                material. It receives the run record and a progress emitter.
            runtime_context: Factory for the runtime context a background run
                must re-enter, since it executes outside any request task.
            store: Optional durable Research ledger. ``None`` retains only
                process-local state.
        """
        self._executor = executor
        self._runtime_context = runtime_context
        self._store = store
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._experiments: dict[str, ResearchExperiment] = {}
        self._runs: dict[str, ResearchRun] = {}
        self._batches: dict[str, dict[str, JsonValue]] = {}
        self._hydrated: set[str] = set()

    # -- experiments ------------------------------------------------------

    def create_experiment(
        self,
        *,
        principal_id: str,
        name: str,
        hypothesis: str,
        notes: str | None,
        tags: Sequence[str],
    ) -> ResearchExperiment:
        """Create and retain one experiment for the calling principal.

        Args:
            principal_id: Authenticated principal identity.
            name: Human-readable experiment name.
            hypothesis: Explicit hypothesis under test.
            notes: Optional free-form notes.
            tags: Bounded tag list.

        Returns:
            The created experiment.
        """
        experiment = ResearchExperiment(
            experiment_id=generate_id("rxp"),
            principal_id=principal_id,
            name=name,
            hypothesis=hypothesis,
            notes=notes,
            tags=tuple(tags),
            created_at=utc_now(),
        )
        with self._lock:
            self._experiments[experiment.experiment_id] = experiment
        self._persist_experiment(experiment)
        logger.info("Created Research experiment %s", experiment.experiment_id)
        return experiment

    def get_experiment(
        self, experiment_id: str, *, principal_id: str
    ) -> ResearchExperiment | None:
        """Return one owned experiment.

        Args:
            experiment_id: Experiment identity.
            principal_id: Authenticated principal identity.

        Returns:
            The experiment, or ``None`` when unknown or owned by another
            principal.
        """
        self._hydrate(principal_id)
        with self._lock:
            experiment = self._experiments.get(experiment_id)
        if experiment is None or experiment.principal_id != principal_id:
            return None
        return experiment

    def list_experiments(self, *, principal_id: str) -> tuple[ResearchExperiment, ...]:
        """Return every experiment owned by one principal, newest first.

        Args:
            principal_id: Authenticated principal identity.

        Returns:
            Owned experiments ordered by creation time descending.
        """
        self._hydrate(principal_id)
        with self._lock:
            owned = [
                experiment
                for experiment in self._experiments.values()
                if experiment.principal_id == principal_id
            ]
        return tuple(sorted(owned, key=lambda item: item.created_at, reverse=True))

    # -- runs -------------------------------------------------------------

    def submit_run(
        self,
        *,
        principal_id: str,
        experiment_id: str,
        hypothesis: str,
        symbol: str,
        timeframe: str,
        preset: str,
        selected_stages: Sequence[str],
        reason: str | None,
        force_rerun: bool,
        request_material: Mapping[str, JsonValue],
        batch_id: str | None = None,
    ) -> ResearchRun:
        """Queue one background Research run and start its worker.

        Args:
            principal_id: Authenticated principal identity.
            experiment_id: Owning experiment identity.
            hypothesis: Explicit hypothesis recorded on the run.
            symbol: Instrument the run analyzes.
            timeframe: Canonical timeframe key.
            preset: Server-owned preset identifier.
            selected_stages: Dependency-complete Research stage selection.
            reason: Optional operator-supplied run reason.
            force_rerun: Whether the caller explicitly forced a fresh run.
            request_material: JSON-safe request evidence retained for audit.
            batch_id: Owning automation batch, when the run came from one.

        Returns:
            The queued run record.
        """
        run = ResearchRun(
            run_id=generate_id("rrn"),
            experiment_id=experiment_id,
            principal_id=principal_id,
            hypothesis=hypothesis,
            symbol=symbol,
            timeframe=timeframe,
            preset=preset,
            selected_stages=tuple(selected_stages),
            reason=reason,
            force_rerun=force_rerun,
            batch_id=batch_id,
            request_material=dict(request_material),
            created_at=utc_now(),
        )
        with self._lock:
            self._runs[run.run_id] = run
            self._evict_runs(principal_id)
        self._emit(run, kind="progress", stage="queued", message="Run queued")
        self._persist_run(run)
        thread = threading.Thread(
            target=self._execute,
            args=(run,),
            name=f"research-run-{run.run_id}",
            daemon=True,
        )
        thread.start()
        logger.info("Queued Research run %s", run.run_id)
        return run

    def get_run(self, run_id: str, *, principal_id: str) -> ResearchRun | None:
        """Return one owned run.

        Args:
            run_id: Run identity.
            principal_id: Authenticated principal identity.

        Returns:
            The run, or ``None`` when unknown or owned by another principal.
        """
        self._hydrate(principal_id)
        with self._lock:
            run = self._runs.get(run_id)
        if run is None or run.principal_id != principal_id:
            return None
        return run

    def list_runs(
        self,
        *,
        principal_id: str,
        experiment_id: str | None = None,
        batch_id: str | None = None,
    ) -> tuple[ResearchRun, ...]:
        """Return owned runs, newest first.

        Failed, cancelled, and inconclusive runs are retained deliberately —
        a research ledger that shows only successes is not a ledger.

        Args:
            principal_id: Authenticated principal identity.
            experiment_id: Optional experiment filter.
            batch_id: Optional automation batch filter.

        Returns:
            Owned runs ordered by creation time descending.
        """
        self._hydrate(principal_id)
        with self._lock:
            owned = [
                run
                for run in self._runs.values()
                if run.principal_id == principal_id
                and (experiment_id is None or run.experiment_id == experiment_id)
                and (batch_id is None or run.batch_id == batch_id)
            ]
        return tuple(sorted(owned, key=lambda item: item.created_at, reverse=True))

    def cancel_run(self, run_id: str, *, principal_id: str) -> ResearchRun | None:
        """Request cooperative cancellation of one owned run.

        A queued run never starts. A running stage sequence is not interrupted
        mid-computation; the run is marked cancelled as soon as the in-flight
        Research call returns, and its result is discarded.

        Args:
            run_id: Run identity.
            principal_id: Authenticated principal identity.

        Returns:
            The run after the cancellation request, or ``None`` when unknown.
        """
        run = self.get_run(run_id, principal_id=principal_id)
        if run is None:
            return None
        with self._lock:
            if run.status in {"completed", "failed", "cancelled"}:
                return run
            run.cancel_requested = True
            if run.status == "queued":
                run.status = "cancelled"
                run.completed_at = utc_now()
        if run.status == "cancelled":
            self._emit(run, kind="terminal", stage="cancelled", message="Run cancelled")
        else:
            self._emit(
                run,
                kind="progress",
                stage="cancelling",
                message="Cancellation requested",
            )
        self._persist_run(run)
        return run

    def stream_events(
        self, run_id: str, *, principal_id: str, after: int = 0
    ) -> Iterator[Mapping[str, JsonValue]] | None:
        """Yield ordered run events, blocking until each becomes available.

        Args:
            run_id: Run identity.
            principal_id: Authenticated principal identity.
            after: Last sequence already delivered to the caller.

        Returns:
            Blocking iterator of ordered events, or ``None`` when the run is
            unknown or owned by another principal.
        """
        run = self.get_run(run_id, principal_id=principal_id)
        if run is None:
            return None

        def _iterate() -> Iterator[Mapping[str, JsonValue]]:
            """Yield ordered frames until the run reaches a terminal event.

            Yields:
                Ordered progress, heartbeat, and terminal frames.
            """
            cursor = after
            while True:
                with self._condition:
                    while len(run.events) <= cursor:
                        terminal = run.status in {"completed", "failed", "cancelled"}
                        if terminal and len(run.events) <= cursor:
                            delivered = self._condition.wait(_HEARTBEAT_SECONDS)
                            if not delivered and len(run.events) <= cursor:
                                yield {"kind": "heartbeat", "sequence": cursor}
                                return
                            continue
                        if not self._condition.wait(_HEARTBEAT_SECONDS):
                            yield {"kind": "heartbeat", "sequence": cursor}
                    event = run.events[cursor]
                cursor += 1
                yield event
                if str(event.get("kind")) == "terminal":
                    return

        return _iterate()

    # -- batches ----------------------------------------------------------

    def create_batch(
        self,
        *,
        principal_id: str,
        experiment_id: str,
        symbols: Sequence[str],
        trigger: str,
        reason: str | None,
        request_material: Mapping[str, JsonValue],
    ) -> Mapping[str, JsonValue]:
        """Create one automation batch record.

        Args:
            principal_id: Authenticated principal identity.
            experiment_id: Owning experiment identity.
            symbols: Requested symbol universe.
            trigger: Batch trigger kind.
            reason: Optional operator-supplied reason.
            request_material: JSON-safe request evidence retained for audit.

        Returns:
            The created batch record.
        """
        batch: dict[str, JsonValue] = {
            "batch_id": generate_id("rbt"),
            "principal_id": principal_id,
            "experiment_id": experiment_id,
            "symbols": [str(symbol) for symbol in symbols],
            "trigger": trigger,
            "reason": reason,
            "created_at": utc_now().isoformat(),
            "request": dict(request_material),
            "rejections": [],
        }
        with self._lock:
            self._batches[str(batch["batch_id"])] = batch
        self._persist_batch(batch)
        return batch

    def record_batch_rejection(
        self, batch_id: str, *, symbol: str, code: str, detail: str
    ) -> None:
        """Record one symbol the gateway refused to queue.

        Args:
            batch_id: Owning batch identity.
            symbol: Rejected symbol.
            code: Symbolic rejection code.
            detail: Bounded rejection detail.
        """
        with self._lock:
            batch = self._batches.get(batch_id)
            if batch is None:
                return
            rejections = list(batch.get("rejections") or [])
            rejections.append({"symbol": symbol, "code": code, "detail": detail})
            batch["rejections"] = rejections
        self._persist_batch(batch)

    def get_batch(
        self, batch_id: str, *, principal_id: str
    ) -> Mapping[str, JsonValue] | None:
        """Return one owned automation batch.

        Args:
            batch_id: Batch identity.
            principal_id: Authenticated principal identity.

        Returns:
            The batch record, or ``None`` when unknown or owned by another
            principal.
        """
        self._hydrate(principal_id)
        with self._lock:
            batch = self._batches.get(batch_id)
        if batch is None or batch.get("principal_id") != principal_id:
            return None
        return batch

    def list_batches(self, *, principal_id: str) -> tuple[Mapping[str, JsonValue], ...]:
        """Return every batch owned by one principal, newest first.

        Args:
            principal_id: Authenticated principal identity.

        Returns:
            Owned batch records ordered by creation time descending.
        """
        self._hydrate(principal_id)
        with self._lock:
            owned = [
                batch
                for batch in self._batches.values()
                if batch.get("principal_id") == principal_id
            ]
        return tuple(
            sorted(owned, key=lambda item: str(item.get("created_at")), reverse=True)
        )

    # -- internals --------------------------------------------------------

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        """Parse one persisted ISO-8601 timestamp.

        Args:
            value: Persisted timestamp text.

        Returns:
            Parsed timestamp.
        """
        return datetime.fromisoformat(str(value))

    def _hydrate(self, principal_id: str) -> None:
        """Load one principal's durable ledger at most once successfully.

        Args:
            principal_id: Authenticated principal identity.
        """
        if self._store is None:
            return
        with self._lock:
            if principal_id in self._hydrated:
                return
            try:
                request_id = generate_id("req")
                experiments = self._store.load_research_experiments(
                    principal_id=principal_id, request_id=request_id
                )
                runs = self._store.load_research_runs(
                    principal_id=principal_id, request_id=request_id
                )
                batches = self._store.load_research_run_batches(
                    principal_id=principal_id, request_id=request_id
                )
                for row in experiments:
                    experiment = ResearchExperiment(
                        experiment_id=str(row["experiment_id"]),
                        principal_id=str(row["principal_id"]),
                        name=str(row["name"]),
                        hypothesis=str(row["hypothesis"]),
                        notes=str(row["notes"])
                        if row.get("notes") is not None
                        else None,
                        tags=tuple(str(tag) for tag in row.get("tags") or ()),
                        created_at=self._parse_datetime(row["created_at"]),
                    )
                    self._experiments.setdefault(experiment.experiment_id, experiment)
                for row in runs:
                    stored_report = row.get("report")
                    report = (
                        hydrate_report(stored_report)
                        if isinstance(stored_report, Mapping)
                        else None
                    )
                    run = ResearchRun(
                        run_id=str(row["run_id"]),
                        experiment_id=str(row["experiment_id"]),
                        principal_id=str(row["principal_id"]),
                        hypothesis=str(row["hypothesis"]),
                        symbol=str(row["symbol"]),
                        timeframe=str(row["timeframe"]),
                        preset=str(row["preset"]),
                        selected_stages=tuple(
                            str(stage) for stage in row.get("selected_stages") or ()
                        ),
                        reason=str(row["reason"])
                        if row.get("reason") is not None
                        else None,
                        force_rerun=bool(row.get("force_rerun", False)),
                        batch_id=str(row["batch_id"])
                        if row.get("batch_id") is not None
                        else None,
                        request_material=dict(row.get("request") or {}),
                        created_at=self._parse_datetime(row["created_at"]),
                        status=cast("RunStatus", str(row["status"])),
                        started_at=(
                            self._parse_datetime(row["started_at"])
                            if row.get("started_at") is not None
                            else None
                        ),
                        completed_at=(
                            self._parse_datetime(row["completed_at"])
                            if row.get("completed_at") is not None
                            else None
                        ),
                        report=report,
                        dataset=row.get("dataset"),
                        effective_configuration=row.get("effective_configuration"),
                        artifacts=tuple(row.get("artifacts") or ()),
                        error=row.get("error"),
                    )
                    self._runs.setdefault(run.run_id, run)
                for row in batches:
                    self._batches.setdefault(str(row["batch_id"]), dict(row))
                self._hydrated.add(principal_id)
                self._evict_runs(principal_id)
            except Exception as error:  # noqa: BLE001 - optional store must not break reads
                logger.warning(
                    "Unable to hydrate Research ledger for principal: %s",
                    type(error).__name__,
                )

    def _persist_experiment(self, experiment: ResearchExperiment) -> None:
        """Persist one experiment without invalidating the in-memory result."""
        if self._store is None:
            return
        try:
            self._store.persist_research_experiment(
                experiment_id=experiment.experiment_id,
                principal_id=experiment.principal_id,
                name=experiment.name,
                hypothesis=experiment.hypothesis,
                notes=experiment.notes,
                tags=experiment.tags,
                created_at=experiment.created_at.isoformat(),
                request_id=generate_id("req"),
            )
        except Exception as error:  # noqa: BLE001 - evidence remains valid without store
            logger.warning(
                "Unable to persist Research experiment: %s", type(error).__name__
            )

    def _persist_run(self, run: ResearchRun) -> None:
        """Persist one run state without invalidating its evidence."""
        if self._store is None:
            return
        try:
            self._store.persist_research_run(
                run_id=run.run_id,
                experiment_id=run.experiment_id,
                principal_id=run.principal_id,
                batch_id=run.batch_id,
                status=run.status,
                hypothesis=run.hypothesis,
                symbol=run.symbol,
                timeframe=run.timeframe,
                preset=run.preset,
                selected_stages=run.selected_stages,
                reason=run.reason,
                force_rerun=run.force_rerun,
                request_material=run.request_material,
                report=project_report(run.report) if run.report is not None else None,
                dataset=run.dataset,
                effective_configuration=run.effective_configuration,
                artifacts=run.artifacts,
                error=run.error,
                created_at=run.created_at.isoformat(),
                started_at=run.started_at.isoformat() if run.started_at else None,
                completed_at=(
                    run.completed_at.isoformat() if run.completed_at else None
                ),
                request_id=generate_id("req"),
            )
        except Exception as error:  # noqa: BLE001 - evidence remains valid without store
            logger.warning("Unable to persist Research run: %s", type(error).__name__)

    def _persist_batch(self, batch: Mapping[str, JsonValue]) -> None:
        """Persist one batch state without invalidating the in-memory result."""
        if self._store is None:
            return
        try:
            self._store.persist_research_run_batch(
                batch_id=str(batch["batch_id"]),
                experiment_id=str(batch["experiment_id"]),
                principal_id=str(batch["principal_id"]),
                symbols=tuple(str(item) for item in batch.get("symbols") or ()),
                trigger=str(batch["trigger"]),
                reason=str(batch["reason"])
                if batch.get("reason") is not None
                else None,
                request_material=dict(batch.get("request") or {}),
                rejections=tuple(batch.get("rejections") or ()),
                created_at=str(batch["created_at"]),
                request_id=generate_id("req"),
            )
        except Exception as error:  # noqa: BLE001 - evidence remains valid without store
            logger.warning("Unable to persist Research batch: %s", type(error).__name__)

    @staticmethod
    def _cancel_requested(run: ResearchRun) -> bool:
        """Read one run's cancellation flag at the moment of the call.

        The flag is set from a request thread while the worker thread runs, so
        it must be read fresh rather than remembered from an earlier check.

        Args:
            run: Run record.

        Returns:
            Whether cancellation has been requested.
        """
        return bool(run.cancel_requested)

    def _evict_runs(self, principal_id: str) -> None:
        """Drop the oldest terminal runs once a principal exceeds retention.

        Args:
            principal_id: Authenticated principal identity.
        """
        owned = sorted(
            (run for run in self._runs.values() if run.principal_id == principal_id),
            key=lambda item: item.created_at,
        )
        excess = len(owned) - _MAX_RUNS_PER_PRINCIPAL
        for run in owned:
            if excess <= 0:
                return
            if run.status in {"completed", "failed", "cancelled"}:
                self._runs.pop(run.run_id, None)
                excess -= 1

    def _emit(
        self,
        run: ResearchRun,
        *,
        kind: str,
        stage: str,
        message: str,
        detail: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Append one ordered run event and wake every stream waiter.

        Args:
            run: Run the event belongs to.
            kind: ``progress``, ``terminal``, or ``heartbeat``.
            stage: Stage or lifecycle phase the event describes.
            message: Human-readable progress message.
            detail: Optional bounded structured detail.
        """
        with self._condition:
            sequence = len(run.events)
            if sequence >= _MAX_EVENTS_PER_RUN:
                # Retain the terminal frame even when a run is unusually chatty.
                if kind != "terminal":
                    return
                run.events = list(deque(run.events, maxlen=_MAX_EVENTS_PER_RUN - 1))
                sequence = len(run.events)
            run.events.append(
                {
                    "kind": kind,
                    "sequence": sequence,
                    "run_id": run.run_id,
                    "stage": stage,
                    "status": run.status,
                    "message": message,
                    "detail": dict(detail or {}),
                    "timestamp": utc_now().isoformat(),
                }
            )
            self._condition.notify_all()

    def _execute(self, run: ResearchRun) -> None:
        """Run one Research pass on a worker thread.

        Args:
            run: Queued run record.
        """
        with self._lock:
            if self._cancel_requested(run):
                return
            run.status = "running"
            run.started_at = utc_now()
        self._persist_run(run)
        self._emit(run, kind="progress", stage="starting", message="Run started")

        def emit(stage: str, message: str, **detail: JsonValue) -> None:
            """Publish one ordered progress event from the executor.

            Args:
                stage: Stage the executor is entering or leaving.
                message: Human-readable progress message.
                **detail: Bounded structured detail.
            """
            self._emit(
                run, kind="progress", stage=stage, message=message, detail=detail
            )

        context = self._runtime_context() if self._runtime_context else nullcontext()
        try:
            with context:
                result = self._executor(run, emit)
        except Exception as error:
            logger.exception("Research run %s failed", run.run_id)
            with self._lock:
                run.status = "failed"
                run.completed_at = utc_now()
                run.error = {
                    "code": type(error).__name__,
                    "message": str(error)[:500],
                }
            self._emit(run, kind="terminal", stage="failed", message="Run failed")
            self._persist_run(run)
            return

        with self._lock:
            if self._cancel_requested(run):
                run.status = "cancelled"
                run.completed_at = utc_now()
            else:
                run.report = result.get("report")
                run.dataset = result.get("dataset")
                run.effective_configuration = result.get("effective_configuration")
                run.artifacts = tuple(result.get("artifacts") or ())
                run.error = result.get("error")
                run.status = "failed" if run.error is not None else "completed"
                run.completed_at = utc_now()
        self._emit(
            run,
            kind="terminal",
            stage=run.status,
            message=f"Run {run.status}",
        )
        self._persist_run(run)


__all__ = (
    "ResearchExperiment",
    "ResearchRun",
    "ResearchWorkbenchRegistry",
    "RunStatus",
)
