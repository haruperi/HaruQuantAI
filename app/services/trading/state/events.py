"""Versioned redacted events for Trading-owned execution state."""

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    JsonValue,
    TradingRoute,
    _contains_sensitive_key,
)
from app.utils import logger, to_json_safe

type TradingEventType = Literal[
    "send_attempted",
    "receipt_recorded",
    "fill_recorded",
    "reconciliation_transitioned",
    "incident_recorded",
]


class TradingEvent(BaseModel):
    """Immutable event carrying ordered execution and trace evidence.

    Attributes:
        event_id: Globally unique event identity.
        event_type: Finite Trading event category.
        aggregate_version: Projection version expected before this event.
        payload: Redacted event-specific facts.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.event.v1"] = "trading.event.v1"
    event_id: str
    event_type: TradingEventType
    event_version: Literal["v1"] = "v1"
    aggregate_version: int
    route: TradingRoute
    tenant_id: str
    authority_id: str
    occurred_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    payload: Mapping[str, JsonValue]
    redaction_applied: Literal[True] = True

    @field_validator(
        "event_id",
        "tenant_id",
        "authority_id",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required event text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating required TradingEvent text")
        if not value or value != value.strip():
            raise ValueError("TradingEvent text must be non-empty and trimmed")
        return value

    @field_validator("causation_id")
    @classmethod
    def _validate_causation(cls, value: str | None) -> str | None:
        """Validate optional event causation identity.

        Args:
            value: Candidate causation identity.

        Returns:
            Validated optional identity.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating TradingEvent causation identity")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("causation_id must be non-empty and trimmed")
        return value

    @field_validator("occurred_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate event UTC time.

        Args:
            value: Candidate event time.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating TradingEvent UTC time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("TradingEvent time must be timezone-aware UTC")
        return value

    @field_validator("payload", mode="before")
    @classmethod
    def _validate_payload(cls, value: Mapping[str, object]) -> Mapping[str, JsonValue]:
        """Validate and freeze redacted JSON-safe event facts.

        Args:
            value: Candidate event facts.

        Returns:
            Immutable JSON-safe facts.

        Raises:
            TypeError: If facts do not serialize to a mapping.
        """
        logger.debug("Validating TradingEvent payload")
        safe = to_json_safe(value)
        if not isinstance(safe, dict):
            raise TypeError("TradingEvent payload must be a mapping")
        return MappingProxyType(safe)

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        """Validate optimistic event version.

        Returns:
            Validated event.

        Raises:
            ValueError: If aggregate version is negative.
        """
        logger.debug("Validating TradingEvent aggregate version")
        if self.aggregate_version < 0:
            raise ValueError("aggregate_version must be non-negative")
        if _contains_sensitive_key(to_json_safe(self.payload)):
            raise ValueError("TradingEvent payload contains unredacted sensitive keys")
        return self


__all__ = ["TradingEvent"]
