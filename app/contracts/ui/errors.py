"""UI domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed UI failure-code union from the ratified v1 operation rules.
type UiFailureCode = Literal[
    "UI_VALIDATION_FAILED",
    "UI_INCOMPATIBLE_WIDGET",
    "UI_LAYOUT_INCOMPATIBLE",
    "UI_DRAFT_CONFLICT",
    "UI_CONFIRMATION_REQUIRED",
    "UI_UNAUTHORIZED",
    "UI_STATE_STALE",
    "CAPABILITY_UNAVAILABLE",
]


class UiFailure(WireModel):
    """Structured failure envelope shared by all sixteen UI ports."""

    outcome: Literal["FAILURE"] = "FAILURE"
    request_id: Uuid7
    code: UiFailureCode
    problem: ProblemDetails
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "UiFailure": UiFailure,
}
