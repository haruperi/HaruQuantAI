"""Typed public outcomes for every Strategy operation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.strategy.contracts.references import (  # noqa: TC001
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.utils import is_sensitive_key, logger

_MAX_TEXT_LENGTH = 512
T = TypeVar("T")
U = TypeVar("U")


class StrategyError(BaseModel):
    """Stable redacted Strategy failure contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.error.v1"] = "strategy.error.v1"
    code: str
    message: str
    details: Mapping[str, str]
    request_id: str | None = None
    correlation_id: str | None = None

    @field_validator("code", "message")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate required error text.

        Args:
            value: Error text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or oversized.
        """
        logger.debug("Validating Strategy error text")
        value = value.strip()
        if not value or len(value) > _MAX_TEXT_LENGTH:
            raise ValueError("error text must contain 1..512 characters")
        return value

    @field_validator("details", mode="after")
    @classmethod
    def _freeze_safe_details(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Reject sensitive detail keys and freeze safe details.

        Args:
            value: Structured error details.

        Returns:
            Immutable safe details.

        Raises:
            ValueError: If a sensitive detail key is present.
        """
        logger.debug("Validating Strategy error details")
        if any(is_sensitive_key(key) for key in value):
            raise ValueError("Strategy error details cannot contain sensitive keys")
        return MappingProxyType(dict(value))

    @field_serializer("details", when_used="json")
    def _serialize_safe_details(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable safe error details.

        Args:
            value: Immutable safe details.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy error details")
        return dict(value)


class StrategyOutcome[T](BaseModel):
    """Exclusive success-data or error result."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)
    status: Literal["success", "error"]
    data: T | None = None
    error: StrategyError | None = None

    @model_validator(mode="after")
    def _validate_exclusive(self) -> StrategyOutcome[T]:
        """Validate exclusive outcome branches.

        Returns:
            The validated outcome.

        Raises:
            ValueError: If data/error does not match status.
        """
        logger.debug("Validating Strategy outcome exclusivity")
        if self.status == "success" and (self.data is None or self.error is not None):
            raise ValueError("success outcomes require only data")
        if self.status == "error" and (self.error is None or self.data is not None):
            raise ValueError("error outcomes require only error")
        return self


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
            The validated mutation result.

        Raises:
            ValueError: If the result branch is inconsistent.
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


def success(data: T) -> StrategyOutcome[T]:
    """Create a successful Strategy outcome.

    Args:
        data: Successful public result.

    Returns:
        A success outcome.
    """
    logger.debug("Creating successful Strategy outcome")
    return StrategyOutcome[T](status="success", data=data)


def failure(
    code: str,
    message: str,
    *,
    details: dict[str, str] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> StrategyOutcome[T]:
    """Create a redacted failed Strategy outcome.

    Args:
        code: Stable error code.
        message: Safe bounded message.
        details: Safe structured details.
        request_id: Optional request trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        An error outcome.
    """
    logger.info("Creating failed Strategy outcome with code %s", code)
    return StrategyOutcome[T](
        status="error",
        error=StrategyError(
            code=code,
            message=message,
            details=details or {},
            request_id=request_id,
            correlation_id=correlation_id,
        ),
    )


def propagate_failure(outcome: StrategyOutcome[U]) -> StrategyOutcome[T]:
    """Retype an existing error outcome without exposing raw failures.

    Args:
        outcome: Existing error outcome from an upstream Strategy feature.

    Returns:
        The same public error under the caller's result type.

    Raises:
        ValueError: If supplied a success outcome.
    """
    logger.debug("Propagating typed Strategy feature failure")
    if outcome.error is None:
        raise ValueError("only error outcomes can be propagated")
    return StrategyOutcome[T](status="error", error=outcome.error)


__all__ = ["StrategyError", "StrategyMutationResult", "StrategyOutcome"]
