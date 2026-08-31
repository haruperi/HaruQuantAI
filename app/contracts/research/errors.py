"""Research domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed research failure-code union from the ratified v1 operation rules.
type ResearchFailureCode = Literal[
    "RESEARCH_VALIDATION_FAILED",
    "RESEARCH_NOT_FOUND",
    "RESEARCH_STATE_CONFLICT",
    "RESEARCH_BUDGET_EXCEEDED",
    "RESEARCH_METHOD_INCOMPATIBLE",
    "RESEARCH_PREVIEW_MISMATCH",
    "PARAMETER_DOMAIN_INVALID",
    "AI_PROPOSAL_INVALID",
    "CAPABILITY_UNAVAILABLE",
]


class ResearchFailure(WireModel):
    """Structured failure envelope shared by every research capability."""

    request_id: Uuid7
    code: ResearchFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "ResearchFailure": ResearchFailure,
}
