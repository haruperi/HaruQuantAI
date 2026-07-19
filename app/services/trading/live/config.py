"""Immutable fail-closed Trading live/paper runtime configuration."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Annotated, Literal, Self

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.trading.contracts import TradingError
from app.services.trading.contracts.models import JsonValue
from app.services.trading.routing.capabilities import BROKER_OPERATION_TIMEOUT_SECONDS
from app.utils import is_sensitive_key, logger


def _positive_decimal(value: object) -> Decimal:
    """Parse one exact positive runtime duration.

    Args:
        value: Candidate JSON-safe integer or Decimal string.

    Returns:
        Exact positive Decimal duration.

    Raises:
        TypeError: If the value is not an exact supported type.
        ValueError: If the value is a float, non-finite, or non-positive.
    """
    logger.debug("Validating Trading runtime duration")
    if isinstance(value, bool | float) or not isinstance(value, int | str | Decimal):
        raise TypeError("runtime duration must be an exact Decimal value")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("runtime duration is invalid") from error
    if not result.is_finite() or result <= 0:
        raise ValueError("runtime duration must be finite and positive")
    return result


type _PositiveDecimal = Annotated[Decimal, BeforeValidator(_positive_decimal)]


def _positive_int(value: object) -> int:
    """Parse one exact positive runtime integer.

    Args:
        value: Candidate integer value.

    Returns:
        Exact positive integer.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is not positive.
    """
    logger.debug("Validating Trading positive runtime integer")
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("runtime integer must be an exact int")
    if value <= 0:
        raise ValueError("runtime integer must be positive")
    return value


type _PositiveInt = Annotated[int, BeforeValidator(_positive_int)]


def _staleness_bounds(value: object) -> Mapping[str, Decimal]:
    """Parse required positive per-evidence freshness bounds.

    Args:
        value: Candidate evidence-class mapping.

    Returns:
        Immutable exact freshness bounds.

    Raises:
        TypeError: If the value is not a mapping.
        ValueError: If keys or values are invalid.
    """
    logger.debug("Validating Trading per-evidence staleness bounds")
    if not isinstance(value, Mapping):
        raise TypeError("MAX_STALENESS_SECONDS must be a mapping")
    required = {"route_snapshot", "risk_decision", "kill_switch"}
    if set(value) != required:
        raise ValueError("MAX_STALENESS_SECONDS requires exact evidence classes")
    parsed = {key: _positive_decimal(item) for key, item in value.items()}
    return MappingProxyType(parsed)


class _LiveRuntimeConfig(BaseModel):
    """Private validated live/paper runtime settings."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    runtime_profile: Literal["paper", "live"] = Field(
        validation_alias=AliasChoices("RUNTIME_PROFILE", "runtime_profile")
    )
    execution_route: Literal["paper", "live"] = Field(
        validation_alias=AliasChoices("EXECUTION_ROUTE", "execution_route")
    )
    allow_live_mutations: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "ALLOW_LIVE_MUTATIONS",
            "allow_live_mutations",
        ),
    )
    live_workflow_timeout_seconds: _PositiveDecimal = Field(
        validation_alias=AliasChoices(
            "LIVE_WORKFLOW_TIMEOUT_SECONDS",
            "live_workflow_timeout_seconds",
        )
    )
    shutdown_budget_seconds: _PositiveDecimal = Field(
        validation_alias=AliasChoices(
            "SHUTDOWN_BUDGET_SECONDS",
            "shutdown_budget_seconds",
        )
    )
    idempotency_retention_seconds: _PositiveInt = Field(
        validation_alias=AliasChoices(
            "IDEMPOTENCY_RETENTION_SECONDS",
            "idempotency_retention_seconds",
        )
    )
    concurrency_lock_timeout_seconds: _PositiveDecimal = Field(
        validation_alias=AliasChoices(
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS",
            "concurrency_lock_timeout_seconds",
        )
    )
    max_staleness_seconds: Mapping[str, Decimal] = Field(
        validation_alias=AliasChoices(
            "MAX_STALENESS_SECONDS",
            "max_staleness_seconds",
        )
    )
    broker_operation_timeout_seconds: _PositiveDecimal = Field(
        default=BROKER_OPERATION_TIMEOUT_SECONDS,
        validation_alias=AliasChoices(
            "BROKER_OPERATION_TIMEOUT_SECONDS",
            "broker_operation_timeout_seconds",
        ),
    )
    data_authority_id: str = Field(
        validation_alias=AliasChoices("DATA_AUTHORITY_ID", "data_authority_id")
    )

    @field_validator("max_staleness_seconds", mode="before")
    @classmethod
    def _validate_staleness_bounds(cls, value: object) -> Mapping[str, Decimal]:
        """Validate required per-evidence freshness policy.

        Args:
            value: Candidate policy mapping.

        Returns:
            Immutable exact bounds.
        """
        logger.debug("Validating LiveSession freshness policy")
        return _staleness_bounds(value)

    @model_validator(mode="after")
    def _validate_compatibility(self) -> Self:
        """Validate exact runtime-profile/route compatibility.

        Returns:
            Validated immutable settings.

        Raises:
            ValueError: If profile/route or authority evidence conflicts.
        """
        logger.debug("Validating Trading live runtime compatibility")
        if self.runtime_profile != self.execution_route:
            raise ValueError("runtime profile and execution route are incompatible")
        if not self.data_authority_id or self.data_authority_id.strip() != (
            self.data_authority_id
        ):
            raise ValueError("data authority identity is required")
        return self


def _validate_live_config(config: Mapping[str, JsonValue]) -> _LiveRuntimeConfig:
    """Validate runtime config without accepting secret material.

    Args:
        config: JSON-safe caller configuration.

    Returns:
        Immutable validated runtime settings.

    Raises:
        TradingError: If config is sensitive, incomplete, or incompatible.
    """
    logger.info("Validating Trading live/paper configuration")
    if any(is_sensitive_key(key) for key in config):
        raise TradingError(
            "CONFIGURATION_INVALID",
            "Trading runtime configuration cannot carry secret material",
        )
    try:
        return _LiveRuntimeConfig.model_validate(dict(config))
    except (TypeError, ValueError) as error:
        raise TradingError(
            "CONFIGURATION_INVALID",
            "Trading runtime configuration is invalid",
        ) from error


__all__: tuple[str, ...] = ()
