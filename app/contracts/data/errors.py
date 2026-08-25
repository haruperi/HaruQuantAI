"""Data domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed data failure-code union from the ratified v1 operation rules.
type DataFailureCode = Literal[
    "DATA_VALIDATION_FAILED",
    "DATA_NOT_FOUND",
    "DATA_VERSION_CONFLICT",
    "DATA_CONNECTION_UNSUPPORTED",
    "DATA_TIMEFRAME_UNSUPPORTED",
    "DATA_PRECISION_UNAVAILABLE",
    "DATA_COVERAGE_INCOMPLETE",
    "DATA_ALIGNMENT_INCOMPATIBLE",
    "DATA_FEED_UNAVAILABLE",
    "DATA_QUANTDATA_INVALID",
    "CAPABILITY_UNAVAILABLE",
]


class DataFailure(WireModel):
    """Structured failure envelope for every data capability."""

    request_id: Uuid7
    code: DataFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "DataFailure": DataFailure,
}
