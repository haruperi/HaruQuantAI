"""Analytics domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed analytics failure-code union from the ratified v1 operation rules.
type AnalyticsFailureCode = Literal[
    "ANALYTICS_VALIDATION_FAILED",
    "DATABANK_NOT_FOUND",
    "DATABANK_NAME_CONFLICT",
    "DATABANK_VERSION_CONFLICT",
    "DATABANK_CAPACITY_EXCEEDED",
    "RESULT_NOT_FOUND",
    "QUERY_INVALID",
    "QUERY_TOO_EXPENSIVE",
    "FORMULA_INVALID",
    "METRIC_NOT_FOUND",
    "COMPARISON_INCOMPATIBLE",
    "PANEL_INCOMPATIBLE",
    "CAPABILITY_UNAVAILABLE",
]


class AnalyticsFailure(WireModel):
    """Structured failure envelope shared by every analytics capability."""

    request_id: Uuid7
    code: AnalyticsFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "AnalyticsFailure": AnalyticsFailure,
}
