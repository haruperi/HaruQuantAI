"""Coordination of Simulation Workbench catalogue resources (FEAT-API-27).

The registry owns transitions only: batch lifecycle, run completion with
report attachment ordering, cancellation, failed-only retry, annotation,
and archiving. Authorization happens at the route boundary before any
registry call; persistence stays in the ``persistence`` package.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import cast

from app.services.api.widgets.simulator.persistence import (
    annotate_simulation_result_record,
    archive_simulation_result_record,
    cancel_simulation_batch_item_records,
    create_simulation_result_record,
    read_simulation_batch_items,
    read_simulation_batch_record,
    read_simulation_result_record,
    retry_simulation_batch_item_record,
    transition_simulation_result_completion,
    update_simulation_batch_record,
)
from app.utils import format_utc_timestamp, get_logger

logger = get_logger(__name__)


class SimulationWorkbenchConflictError(Exception):
    """Raised when a guarded transition disagrees with stored state."""

    def __init__(self, code: str) -> None:
        """Initialize with the stable conflict code."""
        super().__init__(code)
        self.code = code


class SimulationWorkbenchRegistry:
    """Coordinates guarded catalogue transitions for one deployment."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        attach_report: Callable[[str, str], None] | None = None,
    ) -> None:
        """Build one registry with an injectable clock and report attacher.

        Args:
            clock: UTC clock used for transition timestamps; real time when
                absent.
            attach_report: Callable receiving ``(run_id, report_json)``
                that attaches the immutable Analytics report artifact
                before a run may complete.
        """
        self._clock = clock or (lambda: datetime.now(UTC))
        self._attach_report = attach_report

    def _now(self) -> str:
        """Return the current clock reading as a canonical UTC string."""
        return format_utc_timestamp(self._clock())

    def register_run(self, values: Mapping[str, object], *, request_id: str) -> bool:
        """Register one catalogue run row identity-idempotently.

        Args:
            values: Exact result-row column values.
            request_id: Canonical operation request identifier.

        Returns:
            True when a new row was created.
        """
        return create_simulation_result_record(values, request_id=request_id) == 1

    def complete_run(
        self,
        run_id: str,
        principal_id: str,
        *,
        request_id: str,
        report_json: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        """Complete one queued or running run after attaching its report.

        The immutable Analytics report artifact is attached before the
        status transition; an attachment failure leaves the run uncompleted.

        Args:
            run_id: Canonical run identity.
            principal_id: Authenticated principal.
            request_id: Canonical operation request identifier.
            report_json: Serialized Analytics report to attach when present.
            evidence: Immutable evidence references to record
                (``result_ref``, ``report_id``, ``report_ref``,
                ``artifact_manifest_ref``, ``quality_status``).

        Returns:
            The updated catalogue row.

        Raises:
            SimulationWorkbenchConflictError: ``SIMULATION_RUN_NOT_ACTIVE``
                when the run is unknown, foreign, or already terminal.
        """
        timestamp = self._now()
        if report_json is not None:
            if self._attach_report is None:
                raise SimulationWorkbenchConflictError(
                    "SIMULATION_WORKBENCH_STORE_UNAVAILABLE"
                )
            self._attach_report(run_id, report_json)
        rows = read_simulation_result_record(
            run_id, principal_id, request_id=request_id
        )
        if not rows:
            raise SimulationWorkbenchConflictError("SIMULATION_RUN_NOT_ACTIVE")
        current = rows[0]
        merged = {
            **current,
            **{k: v for k, v in (evidence or {}).items() if v is not None},
        }
        changed = transition_simulation_result_completion(
            run_id,
            principal_id,
            completed_at=str(merged.get("completed_at") or timestamp),
            updated_at=timestamp,
            result_ref=cast("str | None", merged.get("result_ref")),
            report_id=cast("str | None", merged.get("report_id")),
            report_ref=cast("str | None", merged.get("report_ref")),
            artifact_manifest_ref=cast(
                "str | None", merged.get("artifact_manifest_ref")
            ),
            quality_status=cast("str | None", merged.get("quality_status")),
            request_id=request_id,
        )
        if changed == 0:
            raise SimulationWorkbenchConflictError("SIMULATION_RUN_NOT_ACTIVE")
        rows = read_simulation_result_record(
            run_id, principal_id, request_id=request_id
        )
        logger.info("Completed Simulation workbench run %s", run_id)
        return rows[0]

    def cancel_batch(
        self, batch_id: str, principal_id: str, *, request_id: str
    ) -> Mapping[str, object]:
        """Cancel every non-terminal item of one owned batch exactly once.

        Args:
            batch_id: Canonical batch identity.
            principal_id: Authenticated principal.
            request_id: Canonical operation request identifier.

        Returns:
            Mapping with the batch identity and cancelled item count.

        Raises:
            SimulationWorkbenchConflictError: ``SIMULATION_BATCH_NOT_FOUND``
                when the batch is unknown or foreign.
        """
        if not read_simulation_batch_record(
            batch_id, principal_id, request_id=request_id
        ):
            raise SimulationWorkbenchConflictError("SIMULATION_BATCH_NOT_FOUND")
        timestamp = self._now()
        cancelled = cancel_simulation_batch_item_records(
            batch_id,
            reason="cancelled by operator",
            updated_at=timestamp,
            request_id=request_id,
        )
        update_simulation_batch_record(
            batch_id,
            principal_id,
            status="cancelled",
            completed_count=0,
            failed_count=0,
            cancelled_count=cancelled,
            finished_at=timestamp,
            updated_at=timestamp,
            request_id=request_id,
        )
        logger.info(
            "Cancelled Simulation workbench batch %s (items %d)",
            batch_id,
            cancelled,
        )
        return {"batch_id": batch_id, "cancelled_items": cancelled}

    def retry_failed_batch_items(
        self,
        batch_id: str,
        principal_id: str,
        *,
        request_id: str,
        resubmit: Callable[[Mapping[str, object]], str],
    ) -> Mapping[str, object]:
        """Retry only the failed items of one owned batch.

        Args:
            batch_id: Canonical batch identity.
            principal_id: Authenticated principal.
            request_id: Canonical operation request identifier.
            resubmit: Callable receiving one failed item row and returning
                the new job identity.

        Returns:
            Mapping with the batch identity and retried item count.

        Raises:
            SimulationWorkbenchConflictError: ``SIMULATION_BATCH_NOT_FOUND``
                when the batch is unknown or foreign.
        """
        if not read_simulation_batch_record(
            batch_id, principal_id, request_id=request_id
        ):
            raise SimulationWorkbenchConflictError("SIMULATION_BATCH_NOT_FOUND")
        items = read_simulation_batch_items(
            batch_id, principal_id, request_id=request_id
        )
        failed = tuple(item for item in items if item["status"] == "failed")
        timestamp = self._now()
        for item in failed:
            job_id = resubmit(item)
            retry_simulation_batch_item_record(
                batch_id,
                int(str(item["position"])),
                job_id=job_id,
                updated_at=timestamp,
                request_id=request_id,
            )
        counts = self._item_counts(batch_id, principal_id, request_id=request_id)
        if failed:
            update_simulation_batch_record(
                batch_id,
                principal_id,
                status="running",
                completed_count=counts["completed"],
                failed_count=counts["failed"],
                cancelled_count=counts["cancelled"],
                finished_at=None,
                updated_at=timestamp,
                request_id=request_id,
            )
        logger.info(
            "Retried Simulation workbench batch %s failed items (count %d)",
            batch_id,
            len(failed),
        )
        return {"batch_id": batch_id, "retried_items": len(failed)}

    def _item_counts(
        self, batch_id: str, principal_id: str, *, request_id: str
    ) -> dict[str, int]:
        """Count one owned batch's items by terminal status.

        Returns:
            Item counts keyed by terminal status.
        """
        items = read_simulation_batch_items(
            batch_id, principal_id, request_id=request_id
        )
        return {
            status: sum(1 for item in items if item["status"] == status)
            for status in ("completed", "failed", "cancelled")
        }

    def annotate_run(
        self,
        run_id: str,
        principal_id: str,
        annotations: Mapping[str, object],
        *,
        request_id: str,
    ) -> int:
        """Apply mutable principal-owned annotations to one run.

        Args:
            run_id: Canonical run identity.
            principal_id: Authenticated principal.
            annotations: Bounded annotation columns and values.
            request_id: Canonical operation request identifier.

        Returns:
            Affected row count.
        """
        rows = read_simulation_result_record(
            run_id, principal_id, request_id=request_id
        )
        if not rows:
            return 0
        current = rows[0]
        tags = current.get("tags")
        tag_values = json.loads(tags) if isinstance(tags, str) else []
        supplied_tags = annotations.get("tags")
        if isinstance(supplied_tags, str):
            tag_values = json.loads(supplied_tags)
        elif isinstance(supplied_tags, (list, tuple)):
            tag_values = list(supplied_tags)
        changed = annotate_simulation_result_record(
            run_id,
            principal_id,
            name=cast(
                "str | None",
                annotations.get("name", current.get("name")),
            ),
            alias=cast(
                "str | None",
                annotations.get("alias", current.get("alias")),
            ),
            description=cast(
                "str | None",
                annotations.get("description", current.get("description")),
            ),
            tags=json.dumps(tag_values),
            run_reason=cast(
                "str | None",
                annotations.get("run_reason", current.get("run_reason")),
            ),
            updated_at=self._now(),
            request_id=request_id,
        )
        logger.info("Annotated Simulation workbench run %s (rows %s)", run_id, changed)
        return changed

    def archive_run(self, run_id: str, principal_id: str, *, request_id: str) -> int:
        """Archive one run's catalogue metadata without deleting evidence.

        Args:
            run_id: Canonical run identity.
            principal_id: Authenticated principal.
            request_id: Canonical operation request identifier.

        Returns:
            Affected row count.
        """
        changed = archive_simulation_result_record(
            run_id,
            principal_id,
            updated_at=self._now(),
            request_id=request_id,
        )
        logger.info("Archived Simulation workbench run %s (rows %s)", run_id, changed)
        return changed


def build_simulation_workbench_registry(
    *,
    clock: Callable[[], datetime] | None = None,
    attach_report: Callable[[str, str], None] | None = None,
) -> object:
    """Build the production registry with its default dependencies.

    Args:
        clock: Optional injected UTC clock.
        attach_report: Optional report-attachment callable.

    Returns:
        Opaque registry consumed by the gateway orchestration.
    """
    logger.info("Building Simulation workbench registry")
    return SimulationWorkbenchRegistry(clock=clock, attach_report=attach_report)


def execute_workbench_registry_operation(
    registry: object, operation: str, *args: object, **kwargs: object
) -> object:
    """Execute one allowlisted registry operation behind the boundary.

    Args:
        registry: Registry instance.
        operation: Allowlisted operation name.
        *args: Positional operation arguments.
        **kwargs: Keyword operation arguments.

    Returns:
        Exact operation result.

    Raises:
        TypeError: If the handle is not a registry.
        ValueError: If the operation is not allowlisted.
    """
    if not isinstance(registry, SimulationWorkbenchRegistry):
        raise TypeError("registry must be a SimulationWorkbenchRegistry")
    allowed = {
        "annotate_run",
        "archive_run",
        "cancel_batch",
        "complete_run",
        "register_run",
        "retry_failed_batch_items",
    }
    if operation not in allowed:
        raise ValueError("unsupported Simulation workbench registry operation")
    return getattr(registry, operation)(*args, **kwargs)


__all__ = (
    "SimulationWorkbenchConflictError",
    "SimulationWorkbenchRegistry",
    "build_simulation_workbench_registry",
    "execute_workbench_registry_operation",
)
