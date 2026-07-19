"""Focused redacted operational evidence for Trading runtime behavior."""

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import TradingError, redact_trading_payload
from app.services.trading.contracts.models import TRADING_CONTRACT_VERSION, JsonValue
from app.utils import is_sensitive_key, logger, to_json_safe

type OperationalEventType = Literal[
    "HEALTH_CHANGED",
    "DEPENDENCY_UNAVAILABLE",
    "EVIDENCE_STALE",
    "WORKFLOW_TIMEOUT",
    "LATENCY_OBSERVED",
    "COST_OBSERVED",
    "INCIDENT_RECORDED",
    "EVENT_DELIVERY_FAILED",
]
type OperationalSeverity = Literal["info", "warning", "error", "critical"]


class OperationalEvent(BaseModel):
    """Immutable Trading-owned operational evidence contract version 1."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    contract_version: Literal["v1"] = TRADING_CONTRACT_VERSION
    schema_id: Literal["trading.operational_event.v1"] = "trading.operational_event.v1"
    event_id: str
    event_type: OperationalEventType
    severity: OperationalSeverity
    occurred_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    facts: Mapping[str, JsonValue]
    source_refs: Mapping[str, str]
    redaction_applied: Literal[True] = True

    @field_validator("event_id", "request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required operational-event identifiers.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating OperationalEvent identifier")
        if not value or value != value.strip():
            raise ValueError("operational event identifiers must be non-empty")
        return value

    @field_validator("causation_id")
    @classmethod
    def _validate_causation(cls, value: str | None) -> str | None:
        """Validate optional event causation identity.

        Args:
            value: Optional causation identity.

        Returns:
            Validated optional identity.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating OperationalEvent causation identity")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("causation_id must be non-empty when supplied")
        return value

    @field_validator("occurred_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the operational-event UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If the timestamp is naive or non-UTC.
        """
        logger.debug("Validating OperationalEvent UTC timestamp")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("operational event time must be aware UTC")
        return value

    @field_validator("facts", mode="before")
    @classmethod
    def _redact_facts(cls, value: Mapping[str, object]) -> Mapping[str, JsonValue]:
        """Redact and freeze operational facts.

        Args:
            value: Candidate event facts.

        Returns:
            Redacted immutable JSON-safe facts.

        Raises:
            TypeError: If redaction does not return a mapping.
        """
        logger.debug("Redacting OperationalEvent facts")
        safe = to_json_safe(value)
        if not isinstance(safe, dict):
            raise TypeError("operational event facts must be a mapping")
        redacted = redact_trading_payload(safe)
        if not isinstance(redacted, dict):
            raise TypeError("operational event facts must be a mapping")
        return MappingProxyType(redacted)

    @field_validator("source_refs", mode="after")
    @classmethod
    def _freeze_source_refs(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze event source references.

        Args:
            value: Candidate source references.

        Returns:
            Immutable validated references.

        Raises:
            ValueError: If a source reference is blank or untrimmed.
        """
        logger.debug("Freezing OperationalEvent source references")
        if any(
            not key or key != key.strip() or not item or item != item.strip()
            for key, item in value.items()
        ):
            raise ValueError("operational event source references must be non-empty")
        if any(is_sensitive_key(key) for key in value):
            raise ValueError("operational event source references contain secrets")
        return MappingProxyType(dict(value))

    @model_validator(mode="after")
    def _validate_severity(self) -> Self:
        """Validate error-event severity.

        Returns:
            Validated event.

        Raises:
            ValueError: If an incident is represented below warning severity.
        """
        logger.debug("Validating OperationalEvent severity")
        incident_types = {"INCIDENT_RECORDED", "EVENT_DELIVERY_FAILED"}
        if self.event_type in incident_types and self.severity == "info":
            raise ValueError("incident events cannot have info severity")
        return self


def _delivery_failure_event(event: OperationalEvent) -> OperationalEvent:
    """Build redacted evidence for one failed event delivery.

    Args:
        event: Original event whose sink rejected delivery.

    Returns:
        Deterministic incident event sharing the original trace.
    """
    logger.warning("Building Trading event-delivery failure evidence")
    return OperationalEvent(
        event_id=f"{event.event_id}.delivery-failed",
        event_type="EVENT_DELIVERY_FAILED",
        severity="error",
        occurred_at=event.occurred_at,
        request_id=event.request_id,
        workflow_id=event.workflow_id,
        correlation_id=event.correlation_id,
        causation_id=event.event_id,
        facts={"failed_event_type": event.event_type},
        source_refs={"failed_event_id": event.event_id},
    )


def emit_runtime_event(
    event: OperationalEvent,
    sink: Callable[[OperationalEvent], None],
) -> None:
    """Publish one redacted runtime event through an injected sink.

    Args:
        event: Validated Trading operational evidence.
        sink: Composition-owned synchronous publication boundary.

    Raises:
        TradingError: If the sink rejects the event. A best-effort incident is
            offered to the same sink before the failure crosses the boundary.
    """
    logger.info("Publishing Trading runtime event %s", event.event_id)
    try:
        sink(event)
    except Exception as error:
        incident = _delivery_failure_event(event)
        try:
            sink(incident)
        except Exception as incident_error:
            logger.exception("Trading runtime event incident delivery also failed")
            raise TradingError(
                "SERVICE_UNAVAILABLE",
                "Trading runtime event and incident delivery failed",
                trace_context={
                    "event_id": event.event_id,
                    "incident_type": "EVENT_DELIVERY_FAILED",
                },
            ) from incident_error
        raise TradingError(
            "SERVICE_UNAVAILABLE",
            "Trading runtime event delivery failed",
            trace_context={
                "event_id": event.event_id,
                "incident_type": "EVENT_DELIVERY_FAILED",
            },
        ) from error


__all__ = ["OperationalEvent", "emit_runtime_event"]
