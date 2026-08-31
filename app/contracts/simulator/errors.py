"""Simulator domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed simulator failure-code union from the ratified v1 operation rules;
# the nine codes are shared by every simulator capability.
type SimulatorFailureCode = Literal[
    "SIM_VALIDATION_FAILED",
    "SIM_ENGINE_PROFILE_REQUIRED",
    "SIM_SEGMENT_INVALID",
    "SIM_ORDER_REJECTED",
    "SIM_RECONCILIATION_FAILED",
    "SIM_COST_UNRECONCILED",
    "CHECKPOINT_INCOMPATIBLE",
    "SIM_DISTRIBUTION_INCOMPATIBLE",
    "CAPABILITY_UNAVAILABLE",
]


class SimulatorFailure(WireModel):
    """Structured failure envelope for every simulator capability."""

    request_id: Uuid7
    code: SimulatorFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "SimulatorFailure": SimulatorFailure,
}
