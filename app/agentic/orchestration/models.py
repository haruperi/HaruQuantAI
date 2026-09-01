"""Durable workflow declarations and run state.

A workflow definition is immutable and bounded: its fan-out, rounds, retries,
and deadline are declared up front and are not model-overridable. A run records
the current durable position and carries an expected-version guard so a
concurrent writer cannot silently overwrite a committed transition.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.composition.logging import get_logger

logger = get_logger(__name__)

_MAX_SHORT_TEXT = 200
_MAX_NODES = 64

WorkflowState = Literal[
    "submitted",
    "running",
    "waiting_human",
    "succeeded",
    "refused",
    "failed",
    "cancelled",
    "expired",
]

# Terminal states may never resume under the same task identity
# (`FR-AGENTIC-012`).
TERMINAL_STATES: frozenset[str] = frozenset(
    {"succeeded", "refused", "failed", "cancelled", "expired"},
)

# Transitions permitted from each non-terminal state.
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "submitted": frozenset({"running", "cancelled", "expired", "refused", "failed"}),
    "running": frozenset(
        {
            "running",
            "waiting_human",
            "succeeded",
            "refused",
            "failed",
            "cancelled",
            "expired",
        },
    ),
    "waiting_human": frozenset(
        {"running", "cancelled", "expired", "refused", "failed"},
    ),
}


def _text(value: str, field: str) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > _MAX_SHORT_TEXT:
        message = f"{field} must not exceed {_MAX_SHORT_TEXT} characters"
        raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


class _OrchestrationModel(BaseModel):
    """Private strict immutable behaviour shared by orchestration contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class WorkflowDefinition(_OrchestrationModel):
    """One immutable bounded workflow declaration.

    Attributes:
        workflow_name: Registered workflow name.
        version: Exact workflow version.
        nodes: Ordered registered node identities.
        entry_node: Node the run begins at.
        limits_profile_id: Versioned limits profile bounding this workflow.
        max_fan_out: Maximum parallel branches from one node.
        max_rounds: Maximum bounded rebuttal rounds.
        max_retries: Maximum bounded transient retries per node.
        deadline_seconds: Maximum wall-clock lifetime of one run.
        permits_human_wait: Whether the workflow may pause for human input.
    """

    workflow_name: str
    version: str
    nodes: tuple[str, ...]
    entry_node: str
    limits_profile_id: str
    max_fan_out: int
    max_rounds: int
    max_retries: int
    deadline_seconds: int
    permits_human_wait: bool

    @field_validator("workflow_name", "version", "entry_node", "limits_profile_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded workflow reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "workflow reference")

    @field_validator("nodes")
    @classmethod
    def _validate_nodes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the declared node set.

        Args:
            value: Candidate node identities.

        Returns:
            Validated node identities.

        Raises:
            ValueError: If the set is empty, oversized, or duplicated.
        """
        if not value:
            message = "nodes is required"
            raise ValueError(message)
        if len(value) > _MAX_NODES:
            message = f"nodes must not exceed {_MAX_NODES} entries"
            raise ValueError(message)
        validated = tuple(_text(node, "node identity") for node in value)
        if len(set(validated)) != len(validated):
            message = "nodes must not repeat a node identity"
            raise ValueError(message)
        return validated

    @field_validator("max_fan_out", "max_rounds", "deadline_seconds")
    @classmethod
    def _validate_positive_bound(cls, value: int) -> int:
        """Validate one positive workflow bound.

        Args:
            value: Candidate bound.

        Returns:
            Validated bound.

        Raises:
            ValueError: If the bound is not positive.
        """
        if value <= 0:
            message = "workflow bound must be positive"
            raise ValueError(message)
        return value

    @field_validator("max_retries")
    @classmethod
    def _validate_retries(cls, value: int) -> int:
        """Validate the retry bound.

        Zero is legitimate: a workflow may specify that no failure is retried.

        Args:
            value: Candidate retry bound.

        Returns:
            Validated retry bound.

        Raises:
            ValueError: If the bound is negative.
        """
        if value < 0:
            message = "max_retries must be non-negative"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_entry_node(self) -> Self:
        """Validate that the entry node is a declared node.

        Returns:
            The validated definition.

        Raises:
            ValueError: If the entry node is not declared.
        """
        if self.entry_node not in self.nodes:
            message = f"entry_node {self.entry_node} is not a declared node"
            raise ValueError(message)
        return self


class WorkflowRun(_OrchestrationModel):
    """One durable position in a bounded Agentic workflow.

    Attributes:
        run_id: Stable run identity.
        task_id: Owning task identity.
        workflow_name: Registered workflow name.
        workflow_version: Exact workflow version.
        state: Current durable state.
        current_node: Node the run is positioned at.
        sequence: Monotonic committed transition count.
        revision: Optimistic-concurrency guard.
        attempts: Retries consumed at the current node.
        idempotency_key: Submission idempotency identity.
        created_at: UTC submission time.
        updated_at: UTC time of the last committed transition.
        deadline_at: UTC deadline after which the run expires.
        terminal_reason: Enumerated reason when the state is terminal.
    """

    run_id: str
    task_id: str
    workflow_name: str
    workflow_version: str
    state: WorkflowState
    current_node: str
    sequence: int
    revision: int
    attempts: int
    idempotency_key: str
    created_at: datetime
    updated_at: datetime
    deadline_at: datetime
    terminal_reason: str | None = None

    @field_validator(
        "run_id",
        "task_id",
        "workflow_name",
        "workflow_version",
        "current_node",
        "idempotency_key",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded run reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "workflow run reference")

    @field_validator("sequence", "revision", "attempts")
    @classmethod
    def _validate_counter(cls, value: int) -> int:
        """Validate one non-negative run counter.

        Args:
            value: Candidate counter.

        Returns:
            Validated counter.

        Raises:
            ValueError: If the counter is negative.
        """
        if value < 0:
            message = "workflow run counter must be non-negative"
            raise ValueError(message)
        return value

    @field_validator("created_at", "updated_at", "deadline_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate one run timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "workflow run timestamp")

    @field_validator("terminal_reason")
    @classmethod
    def _validate_terminal_reason(cls, value: str | None) -> str | None:
        """Validate the optional enumerated terminal reason.

        Args:
            value: Candidate reason code.

        Returns:
            Validated reason code, or None.
        """
        if value is None:
            return None
        return _text(value, "terminal_reason")

    @model_validator(mode="after")
    def _validate_terminal_agreement(self) -> Self:
        """Validate that terminal state and terminal reason agree.

        Returns:
            The validated run.

        Raises:
            ValueError: If a terminal state lacks a reason, or a live state
                carries one.
        """
        is_terminal = self.state in TERMINAL_STATES
        if is_terminal and self.terminal_reason is None:
            message = f"terminal state {self.state} requires a terminal_reason"
            raise ValueError(message)
        if not is_terminal and self.terminal_reason is not None:
            message = f"non-terminal state {self.state} must not carry a reason"
            raise ValueError(message)
        return self


def build_workflow_definition(fields: object) -> WorkflowDefinition:
    """Build one immutable bounded workflow declaration.

    Args:
        fields: Complete workflow-definition fields.

    Returns:
        A validated immutable workflow definition.
    """
    logger.debug("Building an Agentic workflow definition")
    return WorkflowDefinition.model_validate(fields)


def is_terminal_state(state: str) -> bool:
    """Report whether a workflow state is terminal.

    Args:
        state: Candidate workflow state.

    Returns:
        True when the state is terminal.
    """
    return state in TERMINAL_STATES


def validate_transition(current: str, target: str) -> str:
    """Validate one durable workflow state transition.

    Args:
        current: Current durable state.
        target: Proposed durable state.

    Returns:
        The validated target state.

    Raises:
        ValueError: If the current state is terminal or the transition is not
            permitted.
    """
    if current in TERMINAL_STATES:
        message = f"terminal state {current} cannot transition to {target}"
        raise ValueError(message)
    allowed = _ALLOWED_TRANSITIONS[current]
    if target not in allowed:
        message = f"transition {current} -> {target} is not permitted"
        raise ValueError(message)
    return target
