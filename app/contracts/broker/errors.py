"""Broker domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed broker failure-code union from the ratified v1 operation rules; the
# nine codes are shared by every broker capability.
type BrokerFailureCode = Literal[
    "BROKER_VALIDATION_FAILED",
    "BROKER_PROFILE_UNSUPPORTED",
    "BROKER_ENVIRONMENT_MISMATCH",
    "BROKER_SESSION_NOT_READY",
    "BROKER_OPERATION_REJECTED",
    "BROKER_OUTCOME_UNKNOWN",
    "BROKER_PAGINATION_INVALID",
    "CREDENTIALS_MISSING",
    "CAPABILITY_UNAVAILABLE",
]


class BrokerFailure(WireModel):
    """Structured failure envelope shared by every broker capability."""

    request_id: Uuid7
    code: BrokerFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "BrokerFailure": BrokerFailure,
}
