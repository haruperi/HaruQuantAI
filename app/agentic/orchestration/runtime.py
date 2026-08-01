"""Durable Agentic workflow store over Data-owned runtime records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.contracts import WorkflowCheckpoint
from app.agentic.orchestration.models import WorkflowRun
from app.services.data import (
    build_agentic_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.utils import canonical_digest


def _encode(value: object) -> str:
    """Encode one validated Agentic model as JSON.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Agentic workflow state must be a validated model")
    return value.model_dump_json()


def _key(value: str) -> str:
    """Derive one storage-safe identifier.

    Returns:
        Bounded key.
    """
    return f"record-{canonical_digest(value)}"


class DurableWorkflowStore:
    """Data-backed implementation of the Agentic workflow-store port."""

    def __init__(self) -> None:
        """Build the lazy Data runtime handle."""
        self._store = build_agentic_runtime_store(
            {
                "checkpoint": (_encode, WorkflowCheckpoint.model_validate_json),
                "workflow-run": (_encode, WorkflowRun.model_validate_json),
            }
        )

    def reserve_run(self, run: WorkflowRun) -> WorkflowRun:
        """Atomically reserve a run and its idempotency identity.

        Returns:
            Newly reserved or previously stored run.
        """
        existing = cast(
            "WorkflowRun | None",
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="workflow-idempotency",
                key=_key(run.idempotency_key),
            ),
        )
        if existing is not None:
            return existing
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="workflow-idempotency",
            state_key=_key(run.idempotency_key),
            state_kind="workflow-run",
            state_value=run,
            expected_revision=0,
            event_collection="workflow-runs",
            event_key=_key(run.run_id),
            event_partition="runs",
            event_sequence=int(canonical_digest(run.run_id)[:15], 16) + 1,
            event_kind="workflow-run",
            event_value=run,
        )
        if committed:
            return run
        return cast(
            "WorkflowRun",
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="workflow-idempotency",
                key=_key(run.idempotency_key),
            ),
        )

    def load_run(self, run_id: str) -> WorkflowRun | None:
        """Load one run by identity.

        Returns:
            Stored run or ``None``.
        """
        return cast(
            "WorkflowRun | None",
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="workflow-runs",
                key=_key(run_id),
            ),
        )

    def save_run(self, run: WorkflowRun, expected_revision: int) -> WorkflowRun:
        """Commit one run under its owner revision guard.

        Returns:
            Committed run with incremented revision.

        Raises:
            ValueError: If the stored revision conflicts.
        """
        committed = run.model_copy(update={"revision": expected_revision + 1})
        execute_runtime_store_operation(
            self._store,
            "compare_and_swap",
            collection="workflow-runs",
            key=_key(run.run_id),
            kind="workflow-run",
            value=committed,
            expected_revision=expected_revision + 1,
        )
        return committed

    def append_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Append one immutable checkpoint."""
        execute_runtime_store_operation(
            self._store,
            "append",
            collection="workflow-checkpoints",
            key=_key(checkpoint.checkpoint_id),
            partition=_key(checkpoint.task_id),
            sequence=checkpoint.sequence + 1,
            kind="checkpoint",
            value=checkpoint,
        )

    def list_checkpoints(self, task_id: str) -> tuple[WorkflowCheckpoint, ...]:
        """List one task's checkpoints in commit order.

        Returns:
            Ordered checkpoints.
        """
        return cast(
            "tuple[WorkflowCheckpoint, ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="workflow-checkpoints",
                partition=_key(task_id),
                limit=1_000,
            ),
        )


__all__ = ("DurableWorkflowStore",)
