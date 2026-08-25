"""Orchestration domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed orchestration failure-code union shared by every ratified v1
# orchestration capability.
type OrchestrationFailureCode = Literal[
    "ORCHESTRATION_VALIDATION_FAILED",
    "PROJECT_NOT_FOUND",
    "PROJECT_VERSION_CONFLICT",
    "TASK_CONTRACT_INVALID",
    "GRAPH_CYCLE_UNBOUNDED",
    "TASK_STATE_CONFLICT",
    "LEASE_NOT_HELD",
    "FENCING_TOKEN_STALE",
    "CHECKPOINT_INCOMPATIBLE",
    "VARIABLE_RESOLUTION_FAILED",
    "EXECUTABLE_NOT_ALLOWLISTED",
    "NOTIFICATION_DISABLED",
    "NOTIFICATION_RATE_LIMITED",
    "CAPABILITY_UNAVAILABLE",
]


class OrchestrationFailure(WireModel):
    """Structured failure envelope for every orchestration capability."""

    request_id: Uuid7
    code: OrchestrationFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "OrchestrationFailure": OrchestrationFailure,
}
