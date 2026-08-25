"""Common typed capability failure record."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, WireModel


class CapabilityFailure(WireModel):
    """Explicit failed capability outcome."""

    outcome: Literal["FAILURE"] = "FAILURE"
    problem: ProblemDetails
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "CapabilityFailure": CapabilityFailure,
}
