"""Bounded canonical batch execution for the Simulation Workbench (FEAT-API-27).

A batch is nothing more than an ordered, durably-recorded set of canonical
runs executed against the shared Simulation job registry under a bounded
concurrency. The gateway owns the durable membership rows and the admission
bound; the Simulator owns every run, and the completion sink owns catalogue
retention of the results.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.kernel.time import format_utc_timestamp
from app.services.api.widgets.simulator.persistence import (
    create_simulation_batch_item_records,
    create_simulation_batch_record,
    read_simulation_batch_items,
    read_simulation_batch_record,
    transition_simulation_batch_item_record,
    update_simulation_batch_record,
)
from app.services.api.widgets.simulator.workbench_schemas import (
    MAX_BATCH_CONCURRENCY,
    MAX_BATCH_ITEMS,
)

logger = get_logger(__name__)

_TERMINAL_ITEM_STATUS: Mapping[str, str] = {
    "succeeded": "completed",
    "completed": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
}


def _item_status(snapshot: Mapping[str, object]) -> str | None:
    """Map one job snapshot status onto its durable item status.

    Args:
        snapshot: Compact Simulator job snapshot.

    Returns:
        Durable item status, or ``None`` while the job is still running.
    """
    return _TERMINAL_ITEM_STATUS.get(str(snapshot.get("status", "")))


def _run_identity(snapshot: Mapping[str, object]) -> str | None:
    """Return the canonical run identity a finished job produced.

    Args:
        snapshot: Compact Simulator job snapshot.

    Returns:
        Canonical run identity, or ``None`` when the job produced none.
    """
    result = snapshot.get("result")
    if not isinstance(result, Mapping):
        return None
    run_id = result.get("run_id")
    return str(run_id) if run_id else None


class BatchRunner:
    """Executes bounded batches of canonical runs for one deployment."""

    def __init__(
        self,
        run_source: Callable[..., object],
        *,
        clock: Callable[[], datetime] | None = None,
        poll_interval: float = 0.25,
        provenance: Callable[[str, Mapping[str, object]], None] | None = None,
        runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
    ) -> None:
        """Build one batch runner over a composed Simulator run dispatcher.

        Args:
            run_source: Simulator run dispatcher accepting ``submit`` and
                ``get`` operations.
            clock: UTC clock used for durable timestamps; real time when
                absent.
            poll_interval: Seconds between terminal-state polls of one item.
            provenance: Callable recording each submitted job's owning batch
                so its catalogue row records the batch it belongs to.
            runtime_context: Factory re-entering the composed persistence
                settings on a worker thread, since batch execution happens
                outside any request task.
        """
        self._run_source = run_source
        self._provenance = provenance
        self._runtime_context = runtime_context
        self._clock = clock or (lambda: datetime.now(UTC))
        self._poll_interval = poll_interval
        self._specs: dict[tuple[str, int], Mapping[str, object]] = {}
        self._lock = threading.Lock()

    def _enter_runtime(self) -> AbstractContextManager[Any]:
        """Enter the composed persistence settings for one worker thread.

        Returns:
            Context manager covering one background thread's writes.
        """
        if self._runtime_context is None:
            return nullcontext()
        return self._runtime_context()

    def _now(self) -> str:
        """Return the current clock reading as a canonical UTC string.

        Returns:
            Canonical UTC timestamp text.
        """
        return format_utc_timestamp(self._clock())

    def _record_item(
        self,
        batch_id: str,
        position: int,
        *,
        status: str,
        run_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Write one durable item transition.

        Args:
            batch_id: Owning batch identity.
            position: Ordered item position.
            status: Observed item status.
            run_id: Canonical run identity once the item produced one.
            error: Safe failure detail when the item failed.
        """
        transition_simulation_batch_item_record(
            batch_id,
            position,
            status=status,
            run_id=run_id,
            error=error,
            updated_at=self._now(),
            request_id=generate_id("req"),
        )

    def _submit(
        self, spec: Mapping[str, object], *, principal_id: str
    ) -> Mapping[str, object]:
        """Submit one batch item as a canonical run.

        Args:
            spec: One validated batch run specification.
            principal_id: Authenticated principal owning the run.

        Returns:
            Compact Simulator job snapshot for the submitted run.
        """
        from app.services.api.widgets.simulator.schemas import SimulatorRunRequest

        request = SimulatorRunRequest.model_validate(
            {
                "symbol": spec["symbol"],
                "timeframe": spec["timeframe"],
                "strategy_id": spec["strategy_id"],
                "start": spec["start"],
                "end": spec["end"],
                "parameters": dict(
                    cast("Mapping[str, str]", spec.get("parameters", {}))
                ),
            }
        )
        return cast(
            "Mapping[str, object]",
            self._run_source("submit", request, principal_id=principal_id),
        )

    def _watch(
        self,
        batch_id: str,
        position: int,
        job_id: str,
        *,
        principal_id: str,
        release: Callable[[], None],
    ) -> None:
        """Follow one submitted item to its terminal outcome.

        Args:
            batch_id: Owning batch identity.
            position: Ordered item position.
            job_id: Submitted Simulator job identity.
            principal_id: Authenticated principal.
            release: Callable releasing the concurrency permit exactly once.
        """
        waiter = threading.Event()
        with self._enter_runtime():
            try:
                while True:
                    snapshot = cast(
                        "Mapping[str, object] | None",
                        self._run_source("get", job_id, principal_id=principal_id),
                    )
                    if snapshot is None:
                        self._record_item(
                            batch_id,
                            position,
                            status="failed",
                            error="SIMULATION_BATCH_ITEM_LOST",
                        )
                        return
                    status = _item_status(snapshot)
                    if status is None:
                        waiter.wait(self._poll_interval)
                        continue
                    self._record_item(
                        batch_id,
                        position,
                        status=status,
                        run_id=_run_identity(snapshot),
                        error=cast("str | None", snapshot.get("error")),
                    )
                    return
            finally:
                release()
                self._sync(batch_id, principal_id)

    def _sync(self, batch_id: str, principal_id: str) -> None:
        """Recompute one batch's durable counts and terminal status.

        A cancelled batch is terminal by operator decision and is never
        re-opened by a straggling item.

        Args:
            batch_id: Owning batch identity.
            principal_id: Authenticated principal.
        """
        with self._lock:
            request_id = generate_id("req")
            rows = read_simulation_batch_record(
                batch_id, principal_id, request_id=request_id
            )
            if not rows or str(rows[0].get("status")) == "cancelled":
                return
            items = read_simulation_batch_items(
                batch_id, principal_id, request_id=request_id
            )
            counts = {
                status: sum(1 for item in items if item["status"] == status)
                for status in ("completed", "failed", "cancelled")
            }
            finished = sum(counts.values()) == len(items)
            terminal = "failed" if counts["failed"] else "completed"
            timestamp = self._now()
            update_simulation_batch_record(
                batch_id,
                principal_id,
                status=terminal if finished else "running",
                completed_count=counts["completed"],
                failed_count=counts["failed"],
                cancelled_count=counts["cancelled"],
                finished_at=timestamp if finished else None,
                updated_at=timestamp,
                request_id=request_id,
            )

    def _start_item(
        self,
        batch_id: str,
        position: int,
        spec: Mapping[str, object],
        *,
        principal_id: str,
        release: Callable[[], None],
    ) -> None:
        """Submit one item and start following it, or record its refusal.

        Args:
            batch_id: Owning batch identity.
            position: Ordered item position.
            spec: One validated batch run specification.
            principal_id: Authenticated principal.
            release: Callable releasing the concurrency permit exactly once.
        """
        try:
            snapshot = self._submit(spec, principal_id=principal_id)
        except Exception as error:  # noqa: BLE001 - refusal is the outcome.
            logger.warning(
                "Simulation batch %s item %d refused: %s",
                batch_id,
                position,
                type(error).__name__,
            )
            self._record_item(
                batch_id,
                position,
                status="failed",
                error="SIMULATION_BATCH_ITEM_REFUSED",
            )
            release()
            self._sync(batch_id, principal_id)
            return
        job_id = str(snapshot.get("job_id"))
        if self._provenance is not None:
            self._provenance(job_id, {"origin_kind": "batch", "batch_id": batch_id})
        self._record_item(batch_id, position, status="running")
        threading.Thread(
            target=self._watch,
            args=(batch_id, position, job_id),
            kwargs={"principal_id": principal_id, "release": release},
            name=f"batch-{batch_id}-{position}",
            daemon=True,
        ).start()

    def _dispatch_items(
        self,
        batch_id: str,
        items: Sequence[Mapping[str, object]],
        *,
        principal_id: str,
        concurrency: int,
    ) -> None:
        """Submit every item of one batch under its concurrency bound.

        Args:
            batch_id: Owning batch identity.
            items: Ordered batch run specifications.
            principal_id: Authenticated principal.
            concurrency: Maximum simultaneously running items.
        """
        permits = threading.Semaphore(concurrency)

        def run() -> None:
            """Acquire one permit per item and start each in order."""
            with self._enter_runtime():
                dispatch_each()

        def dispatch_each() -> None:
            """Submit every item in order under the acquired permits."""
            for position, spec in enumerate(items):
                permits.acquire()
                released = threading.Event()

                def release(event: threading.Event = released) -> None:
                    """Release this item's permit exactly once."""
                    if not event.is_set():
                        event.set()
                        permits.release()

                self._start_item(
                    batch_id,
                    position,
                    spec,
                    principal_id=principal_id,
                    release=release,
                )

        threading.Thread(target=run, name=f"batch-{batch_id}", daemon=True).start()

    def create_batch(
        self, payload: Mapping[str, object], *, principal_id: str, request_id: str
    ) -> Mapping[str, object]:
        """Record and start one bounded batch of canonical runs.

        Args:
            payload: Validated batch creation request as plain JSON values.
            principal_id: Authenticated principal owning the batch.
            request_id: Canonical operation request identifier.

        Returns:
            Accepted batch projection with its ordered item rows.

        Raises:
            ValueError: If the batch exceeds its admission bounds.
        """
        items = tuple(cast("Sequence[Mapping[str, object]]", payload.get("items", ())))
        if not items or len(items) > MAX_BATCH_ITEMS:
            raise ValueError("SIMULATION_BATCH_SIZE_INVALID")
        concurrency = int(str(payload.get("concurrency", 1)))
        if not 1 <= concurrency <= MAX_BATCH_CONCURRENCY:
            raise ValueError("SIMULATION_BATCH_CONCURRENCY_INVALID")
        batch_id = generate_id("rbt")
        timestamp = self._now()
        create_simulation_batch_record(
            {
                "batch_id": batch_id,
                "principal_id": principal_id,
                "status": "running",
                "concurrency": concurrency,
                "name": payload.get("name"),
                "total_count": len(items),
                "completed_count": 0,
                "failed_count": 0,
                "cancelled_count": 0,
                "finished_at": None,
                "created_at": timestamp,
                "updated_at": timestamp,
            },
            request_id=request_id,
        )
        create_simulation_batch_item_records(
            tuple(
                {
                    "batch_id": batch_id,
                    "position": position,
                    "run_id": None,
                    "job_id": None,
                    "status": "queued",
                    "error": None,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                for position in range(len(items))
            ),
            request_id=request_id,
        )
        for position, spec in enumerate(items):
            self._specs[(batch_id, position)] = spec
        self._dispatch_items(
            batch_id, items, principal_id=principal_id, concurrency=concurrency
        )
        return self.read_batch(batch_id, principal_id=principal_id)

    def read_batch(
        self, batch_id: str, *, principal_id: str, after: int = 0
    ) -> Mapping[str, object]:
        """Read one ordered batch frame from the durable rows.

        Args:
            batch_id: Owning batch identity.
            principal_id: Authenticated principal.
            after: Lowest item position to include.

        Returns:
            Batch row with its ordered item rows from ``after`` onward.
        """
        request_id = generate_id("req")
        rows = read_simulation_batch_record(
            batch_id, principal_id, request_id=request_id
        )
        items = read_simulation_batch_items(
            batch_id, principal_id, request_id=request_id
        )
        return {
            "batch": rows[0] if rows else None,
            "items": tuple(
                item for item in items if int(str(item["position"])) >= after
            ),
            "after": after,
        }

    def resubmit(self, item: Mapping[str, object], *, principal_id: str) -> str:
        """Resubmit one failed batch item under a new job identity.

        Args:
            item: Durable failed item row.
            principal_id: Authenticated principal.

        Returns:
            New Simulator job identity.

        Raises:
            ValueError: If this deployment holds no specification for the
                item, so the exact run can no longer be reproduced.
        """
        batch_id = str(item["batch_id"])
        position = int(str(item["position"]))
        spec = self._specs.get((batch_id, position))
        if spec is None:
            raise ValueError("SIMULATION_BATCH_ITEM_NOT_REPRODUCIBLE")
        snapshot = self._submit(spec, principal_id=principal_id)
        job_id = str(snapshot.get("job_id"))
        threading.Thread(
            target=self._watch,
            args=(batch_id, position, job_id),
            kwargs={"principal_id": principal_id, "release": lambda: None},
            name=f"batch-retry-{batch_id}-{position}",
            daemon=True,
        ).start()
        return job_id


def build_batch_runner(
    run_source: Callable[..., object],
    *,
    clock: Callable[[], datetime] | None = None,
    poll_interval: float = 0.25,
    provenance: Callable[[str, Mapping[str, object]], None] | None = None,
    runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
) -> Callable[..., object]:
    """Build the batch dispatcher executing canonical runs under a bound.

    Args:
        run_source: Composed Simulator run dispatcher accepting ``submit``
            and ``get`` operations.
        clock: UTC clock used for durable timestamps; real time when absent.
        poll_interval: Seconds between terminal-state polls of one item.
        provenance: Callable recording each submitted job's owning batch.
        runtime_context: Factory re-entering composed persistence settings on
            the batch worker threads.

    Returns:
        Callable dispatching ``create_batch``, ``stream_batch``, or
        ``resubmit``.
    """
    runner = BatchRunner(
        run_source,
        clock=clock,
        poll_interval=poll_interval,
        provenance=provenance,
        runtime_context=runtime_context,
    )

    def dispatch(operation: str, *args: object, **kwargs: object) -> object:
        """Execute one batch runner operation.

        Args:
            operation: ``create_batch``, ``stream_batch``, or ``resubmit``.
            *args: Positional operation arguments.
            **kwargs: Keyword operation arguments.

        Returns:
            Operation result.

        Raises:
            ValueError: If the operation is unsupported.
        """
        if operation == "create_batch":
            return runner.create_batch(
                cast("Mapping[str, object]", args[0]),
                principal_id=str(kwargs["principal_id"]),
                request_id=str(kwargs["request_id"]),
            )
        if operation == "stream_batch":
            return runner.read_batch(
                str(args[0]),
                principal_id=str(kwargs.get("principal_id", "")),
                after=int(str(kwargs.get("after", 0))),
            )
        if operation == "resubmit":
            return runner.resubmit(
                cast("Mapping[str, object]", args[0]),
                principal_id=str(kwargs["principal_id"]),
            )
        raise ValueError("unsupported Simulation batch operation")

    return dispatch


__all__ = ("BatchRunner", "build_batch_runner")
