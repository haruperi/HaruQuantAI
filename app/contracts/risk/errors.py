"""Risk domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed risk failure-code union from the ratified v1 operation rules; the
# codes are shared by every risk capability. NO_TRADE outcomes and kill
# switch blocks are typed decision outcomes, not failures, so they never
# appear here.
type RiskFailureCode = Literal[
    "RISK_VALIDATION_FAILED",
    "RISK_PROFILE_INVALID",
    "RISK_EVIDENCE_STALE",
    "RISK_EVIDENCE_MISSING",
    "RISK_APPROVAL_REQUIRED",
    "RISK_TOKEN_INVALID",
    "RISK_RESERVATION_CONFLICT",
    "KILL_SWITCH_ACTIVE",
    "RISK_SCOPE_UNKNOWN",
    "RISK_NOT_FOUND",
    "CAPABILITY_UNAVAILABLE",
]


class RiskFailure(WireModel):
    """Structured failure envelope shared by every risk capability."""

    request_id: Uuid7
    code: RiskFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "RiskFailure": RiskFailure,
}
