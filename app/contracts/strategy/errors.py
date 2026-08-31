"""Strategy domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed strategy failure-code union from the ratified v1 operation rules.
type StrategyFailureCode = Literal[
    "STRATEGY_VALIDATION_FAILED",
    "STRATEGY_AST_INVALID",
    "STRATEGY_BLOCK_UNAVAILABLE",
    "STRATEGY_TEMPLATE_INVALID",
    "STRATEGY_IMPORT_INVALID",
    "STRATEGY_PLUGIN_UNAVAILABLE",
    "STRATEGY_TARGET_UNSUPPORTED",
    "CODEGEN_FAILED",
    "COMPILE_FAILED",
    "CAPABILITY_UNAVAILABLE",
]


class StrategyFailure(WireModel):
    """Structured failure envelope for every strategy capability."""

    request_id: Uuid7
    code: StrategyFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "StrategyFailure": StrategyFailure,
}
