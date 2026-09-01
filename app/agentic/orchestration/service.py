"""Durable submission, resumption, cancellation, and expiry of Agentic work.

Submission is idempotent and persists its initial checkpoint *before* any
execution, so a crash between submission and the first node cannot lose the
run. Terminal runs never resume under the same task identity.

Policy and context arrive through injected ports declared here in terms of
Agentic contracts, so orchestration can be implemented before the concrete
`permissions/` and `context_memory/` features without a circular import. No
runtime or provider object crosses those ports.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.contracts import build_workflow_checkpoint
from app.agentic.orchestration.models import (
    WorkflowRun,
    is_terminal_state,
    validate_transition,
)
from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.kernel.serialization import canonical_digest
from app.kernel.time import utc_now

if TYPE_CHECKING:
    from app.agentic.contracts import AgentTask
    from app.agentic.orchestration.models import WorkflowDefinition
    from app.agentic.orchestration.repository import AgenticWorkflowStore

logger = get_logger(__name__)


@runtime_checkable
class PolicyPort(Protocol):
    """Deterministic authorization decision for one governed task action."""

    def authorize_task(self, task: AgentTask, action: str) -> bool:
        """Authorize one governed task action.

        Args:
            task: Bounded governed task.
            action: Requested orchestration action.

        Returns:
            True when the action is authorized.
        """
        ...


@runtime_checkable
class ContextPort(Protocol):
    """Bounded eligible context assembly for one governed task."""

    def assemble_task_context(self, task: AgentTask) -> Mapping[str, str]:
        """Assemble bounded eligible context for one task.

        Args:
            task: Bounded governed task.

        Returns:
            Bounded eligible context.
        """
        ...


def _checkpoint_for(
    run: WorkflowRun,
    task: AgentTask,
    state: str,
) -> object:
    """Build the immutable checkpoint recording one committed transition.

    Args:
        run: Run being committed.
        task: Owning governed task.
        state: Durable state at this checkpoint.

    Returns:
        A validated immutable workflow checkpoint.
    """
    return build_workflow_checkpoint(
        {
            "checkpoint_id": derive_stable_id(
                "id",
                f"{run.run_id}:{run.sequence}:{state}",
            ),
            "task_id": run.task_id,
            "workflow_name": run.workflow_name,
            "workflow_version": run.workflow_version,
            "node_id": run.current_node,
            "sequence": run.sequence,
            "state": state,
            "expected_version": run.revision,
            "state_payload_hash": canonical_digest(
                {"run": run.run_id, "node": run.current_node, "state": state},
            ),
            "created_at": run.updated_at,
            "request_id": task.request_id,
            "workflow_id": task.workflow_id,
            "correlation_id": task.correlation_id,
            "causation_id": task.causation_id,
        },
    )


def submit_task(
    store: AgenticWorkflowStore,
    definition: WorkflowDefinition,
    task: AgentTask,
    policy: PolicyPort | None = None,
    context: ContextPort | None = None,
    at_time: datetime | None = None,
) -> WorkflowRun:
    """Submit one bounded governed task idempotently.

    Args:
        store: Injected durable workflow store.
        definition: Immutable bounded workflow declaration.
        task: Bounded governed task.
        policy: Optional injected authorization port.
        context: Optional injected context-assembly port.
        at_time: Optional submission time; current UTC when omitted.

    Returns:
        The reserved run. A repeated idempotency key returns the original run.

    Raises:
        ValueError: If the workflow does not match the task, the deadline has
            already passed, or policy denies submission.
    """
    now = at_time if at_time is not None else utc_now()
    logger.info(
        "Submitting Agentic task %s to workflow %s",
        task.task_id,
        definition.workflow_name,
    )
    if task.workflow_name != definition.workflow_name:
        message = (
            f"task declares workflow {task.workflow_name}, "
            f"definition is {definition.workflow_name}"
        )
        raise ValueError(message)
    if task.workflow_version != definition.version:
        message = (
            f"task declares version {task.workflow_version}, "
            f"definition is {definition.version}"
        )
        raise ValueError(message)
    if task.deadline_at <= now:
        message = "task deadline has already passed at submission"
        raise ValueError(message)
    if policy is not None and not policy.authorize_task(task, "submit_task"):
        message = f"policy denied submission of task {task.task_id}"
        raise ValueError(message)
    if context is not None:
        # Context is assembled at submission so an ineligible-evidence refusal
        # happens before any model call is budgeted.
        context.assemble_task_context(task)

    candidate = WorkflowRun(
        run_id=derive_stable_id("id", f"run:{task.idempotency_key}"),
        task_id=task.task_id,
        workflow_name=definition.workflow_name,
        workflow_version=definition.version,
        state="submitted",
        current_node=definition.entry_node,
        sequence=0,
        revision=0,
        attempts=0,
        idempotency_key=task.idempotency_key,
        created_at=now,
        updated_at=now,
        deadline_at=task.deadline_at,
        terminal_reason=None,
    )
    # The run identity is derived from the idempotency key, so probing before
    # reserving is what distinguishes a genuinely new run from a replay. Without
    # this probe a repeated submission would append a second initial checkpoint.
    already_present = store.load_run(candidate.run_id) is not None
    reserved = store.reserve_run(candidate)
    if not already_present:
        # Persist the initial checkpoint before any execution begins.
        store.append_checkpoint(_checkpoint_for(reserved, task, "submitted"))  # type: ignore[arg-type]
    return reserved


def _transition(
    store: AgenticWorkflowStore,
    run: WorkflowRun,
    task: AgentTask,
    target: str,
    terminal_reason: str | None,
    at_time: datetime | None,
) -> WorkflowRun:
    """Commit one validated durable transition and its checkpoint.

    Args:
        store: Injected durable workflow store.
        run: Current run state.
        task: Owning governed task.
        target: Proposed durable state.
        terminal_reason: Enumerated reason when the target is terminal.
        at_time: Optional transition time; current UTC when omitted.

    Returns:
        The committed run.
    """
    now = at_time if at_time is not None else utc_now()
    validate_transition(run.state, target)
    updated = run.model_copy(
        update={
            "state": target,
            "sequence": run.sequence + 1,
            "updated_at": now,
            "terminal_reason": terminal_reason,
        },
    )
    committed = store.save_run(updated, run.revision)
    store.append_checkpoint(_checkpoint_for(committed, task, target))  # type: ignore[arg-type]
    logger.info(
        "Agentic run %s transitioned %s -> %s",
        run.run_id,
        run.state,
        target,
    )
    return committed


def _load_live_run(store: AgenticWorkflowStore, run_id: str) -> WorkflowRun:
    """Load one non-terminal run.

    Args:
        store: Injected durable workflow store.
        run_id: Stable run identity.

    Returns:
        The stored non-terminal run.

    Raises:
        ValueError: If the run is unknown or already terminal.
    """
    run = store.load_run(run_id)
    if run is None:
        message = f"unknown Agentic run: {run_id}"
        raise ValueError(message)
    if is_terminal_state(run.state):
        message = (
            f"run {run_id} is terminal ({run.state}) and cannot resume "
            "under the same task identity"
        )
        raise ValueError(message)
    return run


def resume_task(
    store: AgenticWorkflowStore,
    run_id: str,
    task: AgentTask,
    at_time: datetime | None = None,
) -> WorkflowRun:
    """Resume one non-terminal run from its last committed checkpoint.

    Args:
        store: Injected durable workflow store.
        run_id: Stable run identity.
        task: Owning governed task.
        at_time: Optional resume time; current UTC when omitted.

    Returns:
        The committed running run.

    Raises:
        ValueError: If the run is terminal or its deadline has passed.
    """
    run = _load_live_run(store, run_id)
    now = at_time if at_time is not None else utc_now()
    if now >= run.deadline_at:
        message = f"run {run_id} has passed its deadline and must expire"
        raise ValueError(message)
    return _transition(store, run, task, "running", None, now)


def cancel_task(
    store: AgenticWorkflowStore,
    run_id: str,
    task: AgentTask,
    reason: str = "OPERATOR_CANCELLED",
    at_time: datetime | None = None,
) -> WorkflowRun:
    """Cancel one non-terminal run.

    Args:
        store: Injected durable workflow store.
        run_id: Stable run identity.
        task: Owning governed task.
        reason: Enumerated cancellation reason.
        at_time: Optional cancellation time; current UTC when omitted.

    Returns:
        The committed cancelled run.

    Raises:
        ValueError: If the run is unknown or already terminal.
    """
    run = _load_live_run(store, run_id)
    return _transition(store, run, task, "cancelled", reason, at_time)


def expire_task(
    store: AgenticWorkflowStore,
    run_id: str,
    task: AgentTask,
    at_time: datetime | None = None,
) -> WorkflowRun:
    """Expire one non-terminal run whose deadline has passed.

    Args:
        store: Injected durable workflow store.
        run_id: Stable run identity.
        task: Owning governed task.
        at_time: Optional evaluation time; current UTC when omitted.

    Returns:
        The committed expired run.

    Raises:
        ValueError: If the run is terminal or its deadline has not passed.
    """
    run = _load_live_run(store, run_id)
    now = at_time if at_time is not None else utc_now()
    if now < run.deadline_at:
        message = f"run {run_id} has not reached its deadline"
        raise ValueError(message)
    return _transition(store, run, task, "expired", "DEADLINE_EXCEEDED", now)
