"""Injected-store port for durable Agentic workflow state.

Agentic declares the persistence operations it needs and never implements a
database writer. An approved composition root supplies the concrete store, so
Agentic owns no connection, credential, or SQL execution path — matching the
Portfolio and Risk precedents.

The in-memory reference store below is a deterministic development and
evidence double. It proves idempotency, expected-version conflict detection,
and checkpoint ordering, but it is explicitly **not** durable: crash safety is
a property of the concrete store a composition root injects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.utils import get_logger

if TYPE_CHECKING:
    from app.agentic.contracts import WorkflowCheckpoint
    from app.agentic.orchestration.models import WorkflowRun

logger = get_logger(__name__)


@runtime_checkable
class AgenticWorkflowStore(Protocol):
    """Atomic persistence operations required by Agentic orchestration."""

    def reserve_run(self, run: WorkflowRun) -> WorkflowRun:
        """Reserve one run against its idempotency key.

        A repeated key returns the originally reserved run rather than
        creating a second run.

        Args:
            run: Candidate initial run state.

        Returns:
            The reserved run, which may be a previously stored run.
        """
        ...

    def load_run(self, run_id: str) -> WorkflowRun | None:
        """Load one run by identity.

        Args:
            run_id: Stable run identity.

        Returns:
            The stored run, or None when absent.
        """
        ...

    def save_run(self, run: WorkflowRun, expected_revision: int) -> WorkflowRun:
        """Atomically save one run under an expected-version guard.

        Args:
            run: Run state to commit.
            expected_revision: Revision the caller observed.

        Returns:
            The committed run carrying its incremented revision.
        """
        ...

    def append_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Append one immutable checkpoint.

        Args:
            checkpoint: Committed workflow checkpoint.
        """
        ...

    def list_checkpoints(self, task_id: str) -> tuple[WorkflowCheckpoint, ...]:
        """List every checkpoint for one task in commit order.

        Args:
            task_id: Owning task identity.

        Returns:
            Ordered committed checkpoints.
        """
        ...


class _InMemoryWorkflowStore:
    """Deterministic non-durable reference implementation of the store port."""

    def __init__(self) -> None:
        """Initialise empty run, idempotency, and checkpoint state."""
        self._runs: dict[str, WorkflowRun] = {}
        self._by_idempotency: dict[str, str] = {}
        self._checkpoints: list[WorkflowCheckpoint] = []

    def reserve_run(self, run: WorkflowRun) -> WorkflowRun:
        """Reserve one run against its idempotency key.

        Args:
            run: Candidate initial run state.

        Returns:
            The reserved run, which may be a previously stored run.
        """
        existing_id = self._by_idempotency.get(run.idempotency_key)
        if existing_id is not None:
            logger.info(
                "Returning the original run for idempotency key reuse on task %s",
                run.task_id,
            )
            return self._runs[existing_id]
        self._by_idempotency[run.idempotency_key] = run.run_id
        self._runs[run.run_id] = run
        return run

    def load_run(self, run_id: str) -> WorkflowRun | None:
        """Load one run by identity.

        Args:
            run_id: Stable run identity.

        Returns:
            The stored run, or None when absent.
        """
        return self._runs.get(run_id)

    def save_run(self, run: WorkflowRun, expected_revision: int) -> WorkflowRun:
        """Atomically save one run under an expected-version guard.

        Args:
            run: Run state to commit.
            expected_revision: Revision the caller observed.

        Returns:
            The committed run carrying its incremented revision.

        Raises:
            ValueError: If the run is absent or the revision guard failed.
        """
        stored = self._runs.get(run.run_id)
        if stored is None:
            message = f"unknown Agentic run: {run.run_id}"
            raise ValueError(message)
        if stored.revision != expected_revision:
            message = (
                f"concurrent modification of run {run.run_id}: expected revision "
                f"{expected_revision}, stored {stored.revision}"
            )
            raise ValueError(message)
        committed = run.model_copy(update={"revision": stored.revision + 1})
        self._runs[run.run_id] = committed
        return committed

    def append_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Append one immutable checkpoint.

        Args:
            checkpoint: Committed workflow checkpoint.
        """
        self._checkpoints.append(checkpoint)

    def list_checkpoints(self, task_id: str) -> tuple[WorkflowCheckpoint, ...]:
        """List every checkpoint for one task in commit order.

        Args:
            task_id: Owning task identity.

        Returns:
            Ordered committed checkpoints.
        """
        return tuple(
            checkpoint
            for checkpoint in self._checkpoints
            if checkpoint.task_id == task_id
        )


def build_in_memory_workflow_store() -> AgenticWorkflowStore:
    """Build the deterministic non-durable reference workflow store.

    Returns:
        A store satisfying the `AgenticWorkflowStore` port.
    """
    logger.debug("Building the in-memory Agentic workflow store")
    return _InMemoryWorkflowStore()
