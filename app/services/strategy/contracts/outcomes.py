"""Internal Strategy result helpers and the public mutation result contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, NoReturn, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

from app.composition.logging import get_logger
from app.services.strategy.contracts.references import (  # noqa: TC001
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    unwrap_strategy_response,
)

type StandardResponse[T] = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.strategy.contracts._base import JsonValue

T = TypeVar("T")
U = TypeVar("U")


class StrategyMutationResult(BaseModel):
    """Deterministic result of an immutable Strategy mutation."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.mutation_result.v1"] = "strategy.mutation_result.v1"
    mutation_id: str
    mutation_type: Literal["REGISTER_VERSION", "UPDATE_PARAMETERS"]
    status: Literal["ACCEPTED", "IDEMPOTENT", "REJECTED"]
    strategy_id: str
    strategy_version: str
    validated_ref: ValidatedStrategyRef | None = None
    validated_config: ValidatedStrategyConfig | None = None
    record_ref: str | None = None
    record_hash: str | None = None
    reason_codes: tuple[str, ...] = ()
    request_id: str
    correlation_id: str
    workflow_id: str
    completed_at: datetime
    audit_event_ref: str | None = None
    publication_pending: bool = False

    @model_validator(mode="after")
    def _validate_mutation(self) -> StrategyMutationResult:
        """Validate accepted, idempotent, and rejected result shapes.

        Returns:
            The validated immutable mutation result.

        Raises:
            ValueError: If the status and embedded payloads conflict.
        """
        logger.debug("Validating Strategy mutation result")
        payloads = int(self.validated_ref is not None) + int(
            self.validated_config is not None
        )
        if self.status == "REJECTED" and payloads:
            raise ValueError("rejected mutations cannot expose validated payloads")
        if self.status != "REJECTED" and payloads != 1:
            raise ValueError("accepted mutations require exactly one validated payload")
        return self


def success(data: T) -> T:
    """Return raw data from an internal Strategy operation.

    Args:
        data: Internal operation result value.

    Returns:
        The raw operation result value.
    """
    logger.debug("Returning successful raw Strategy result")
    return data


def failure(
    code: str,
    message: str,
    *,
    details: Mapping[str, JsonValue] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> NoReturn:
    """Raise a known safe Strategy failure for the outer response boundary.

    Raises:
        StrategyOperationError: Always, with the approved code and safe details.
    """
    logger.info("Raising Strategy failure with code %s", code)
    raise StrategyOperationError(
        code,
        message,
        details,
        request_id=request_id,
        correlation_id=correlation_id,
    )


def propagate_failure(outcome: StandardResponse[U]) -> NoReturn:
    """Propagate a nested StandardResponse failure without wrapping it.

    Raises:
        StrategyOperationError: If the response is an error response.
        ValueError: If the response is successful.
    """
    logger.debug("Propagating nested Strategy response failure")
    unwrap_strategy_response(outcome, operation="nested_strategy_operation")
    raise ValueError("only error responses can be propagated")


__all__ = ["StrategyMutationResult"]
