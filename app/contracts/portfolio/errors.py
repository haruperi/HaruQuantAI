"""Portfolio domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed portfolio failure-code union from the ratified v1 operation rules;
# the ten codes are shared by every portfolio capability.
type PortfolioFailureCode = Literal[
    "PORTFOLIO_VALIDATION_FAILED",
    "PORTFOLIO_ADMISSION_REJECTED",
    "PORTFOLIO_VERSION_CONFLICT",
    "CORRELATION_POLICY_INVALID",
    "CURRENCY_RATE_MISSING",
    "EXPOSURE_LIMIT_BREACHED",
    "SEARCH_INFEASIBLE",
    "PORTFOLIO_NOT_FOUND",
    "PORTFOLIO_METHOD_UNSUPPORTED",
    "CAPABILITY_UNAVAILABLE",
]


class PortfolioFailure(WireModel):
    """Structured failure envelope shared by every portfolio capability."""

    request_id: Uuid7
    code: PortfolioFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "PortfolioFailure": PortfolioFailure,
}
