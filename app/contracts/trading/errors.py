"""Trading domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed trading failure-code union from the ratified v1 operation rules.
type TradingFailureCode = Literal[
    "TRADING_VALIDATION_FAILED",
    "TRADING_MODE_MISMATCH",
    "TRADING_SESSION_NOT_ACTIVE",
    "TRADING_STATE_CONFLICT",
    "TRADING_AUTHORITY_MISMATCH",
    "TRADING_RISK_AUTHORITY_INVALID",
    "TRADING_IDEMPOTENCY_CONFLICT",
    "TRADING_PROTECTION_INVALID",
    "TRADING_QUERY_INVALID",
    "CAPABILITY_UNAVAILABLE",
]


class TradingFailure(WireModel):
    """Structured failure envelope for every trading capability."""

    request_id: Uuid7
    code: TradingFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "TradingFailure": TradingFailure,
}
