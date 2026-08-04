"""Durable Agentic workflow store over Agentic-owned relational records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.contracts import WorkflowCheckpoint
from app.agentic.orchestration.models import WorkflowRun
from app.agentic.persistence import (
    create_agentic_persistence_store,
    create_workflow_checkpoint_record,
    create_workflow_run_reservation,
    read_workflow_checkpoint_records,
    read_workflow_idempotency_record,
    read_workflow_run_record,
    update_workflow_run_record,
)


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


class DurableWorkflowStore:
    """Data-backed implementation of the Agentic workflow-store port."""

    def __init__(self) -> None:
        """Build the relational persistence handle."""
        self._store = create_agentic_persistence_store(
            {
                "checkpoint": (_encode, WorkflowCheckpoint.model_validate_json),
                "workflow-run": (_encode, WorkflowRun.model_validate_json),
            }
        )

    def reserve_run(self, run: WorkflowRun) -> WorkflowRun:
        """Atomically reserve a run and its idempotency identity.

        Returns:
            Newly reserved or previously stored run.

        Raises:
            ValueError: If the run identity conflicts with stored state.
        """
        existing = cast(
            "WorkflowRun | None",
            read_workflow_idempotency_record(
                self._store,
                run.idempotency_key,
            ),
        )
        if existing is not None:
            return existing
        committed = create_workflow_run_reservation(
            self._store,
            idempotency_key=run.idempotency_key,
            run_key=run.run_id,
            sequence=run.sequence + 1,
            value=run,
        )
        if committed:
            return run
        existing = cast(
            "WorkflowRun | None",
            read_workflow_idempotency_record(self._store, run.idempotency_key),
        )
        if existing is None:
            raise ValueError("Agentic workflow identity conflicts with stored state")
        return existing

    def load_run(self, run_id: str) -> WorkflowRun | None:
        """Load one run by identity.

        Returns:
            Stored run or ``None``.
        """
        return cast(
            "WorkflowRun | None",
            read_workflow_run_record(
                self._store,
                run_id,
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
        update_workflow_run_record(
            self._store,
            key=run.run_id,
            value=committed,
            expected_revision=expected_revision,
        )
        return committed

    def append_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Append one immutable checkpoint."""
        create_workflow_checkpoint_record(
            self._store,
            key=checkpoint.checkpoint_id,
            partition=checkpoint.task_id,
            sequence=checkpoint.sequence + 1,
            value=checkpoint,
        )

    def list_checkpoints(self, task_id: str) -> tuple[WorkflowCheckpoint, ...]:
        """List one task's checkpoints in commit order.

        Returns:
            Ordered checkpoints.
        """
        return cast(
            "tuple[WorkflowCheckpoint, ...]",
            read_workflow_checkpoint_records(
                self._store,
                task_id,
                1_000,
            ),
        )


__all__ = ("DurableWorkflowStore",)
