"""Focused redacted operational evidence for Trading runtime behavior."""

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger
from app.kernel.identity import validate_id
from app.kernel.redaction import is_sensitive_key, redact_text_value
from app.kernel.serialization import canonical_json, to_json_safe
from app.services.trading.contracts import (
    ExecutionReceipt,
    TradingError,
)
from app.services.trading.contracts.errors import _redact_trading_payload_value
from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    JsonValue,
    _validate_trace_id,
    _validation_field_name,
)
from app.services.trading.contracts.responses import success_trading_response

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

type OperationalEventType = Literal[
    "HEALTH_CHANGED",
    "DEPENDENCY_UNAVAILABLE",
    "EVIDENCE_STALE",
    "WORKFLOW_TIMEOUT",
    "LATENCY_OBSERVED",
    "COST_OBSERVED",
    "INCIDENT_RECORDED",
    "EVENT_DELIVERY_FAILED",
    "BROKER_STATE_UNKNOWN",
]
type OperationalSeverity = Literal["info", "warning", "error", "critical"]

_MAX_UNRESOLVED_SCOPE_ITEMS = 8
_MAX_UNRESOLVED_SCOPE_TEXT = 256


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

    @field_validator("event_id")
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

    @field_validator("request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_trace(cls, value: str, info: ValidationInfo) -> str:
        """Validate canonical operational-event trace identifiers.

        Args:
            value: Candidate trace identifier.
            info: Pydantic field metadata.

        Returns:
            Validated prefixed UUID4 identifier.

        Raises:
            ValueError: If the identifier is invalid.
        """
        prefixes = {
            "request_id": "req",
            "workflow_id": "wf",
            "correlation_id": "cor",
        }
        field_name = _validation_field_name(info)
        return _validate_trace_id(value, prefixes[field_name], field_name)

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
        if value is None:
            return None
        return _validate_trace_id(value, "cau", "causation_id")

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
        redacted = _redact_trading_payload_value(safe)
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
        if any(
            redact_text_value(item).redacted_paths
            or redact_text_value(item).truncated_paths
            for item in value.values()
        ):
            raise ValueError(
                "operational event source references contain unsafe material"
            )
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
        if self.event_type == "BROKER_STATE_UNKNOWN" and self.severity != "critical":
            raise ValueError("unknown broker state must be critical")
        return self


def _validate_unknown_event_source(
    receipt: ExecutionReceipt,
    *,
    incident_id: str,
    unresolved_scope: Sequence[str],
    occurred_at: datetime,
    workflow_id: str,
) -> tuple[str, str, str, tuple[str, ...], str]:
    """Validate one retry-locked event source and its bounded facts.

    Args:
        receipt: Authoritative unknown-outcome execution receipt.
        incident_id: Persisted Trading incident identity.
        unresolved_scope: Ordered unresolved reconciliation identities.
        occurred_at: Persisted transition occurrence time.
        workflow_id: Originating canonical workflow trace.

    Returns:
        Canonical traces, ordered scope, and bounded textual scope.

    Raises:
        ValueError: If source, time, or bounded facts are incompatible.
        Exception: If trace identities are incompatible.
    """
    if receipt.status != "unknown_outcome" or not receipt.reconciliation_required:
        raise ValueError("receipt is not a retry-locked unknown outcome")
    if (
        not incident_id
        or incident_id != incident_id.strip()
        or occurred_at.tzinfo is None
        or occurred_at.utcoffset() != timedelta(0)
    ):
        raise ValueError("incident identity or occurrence time is invalid")
    request_id = validate_id(receipt.request_id, expected_prefix="req")
    checked_workflow_id = validate_id(workflow_id, expected_prefix="wf")
    correlation_id = validate_id(
        receipt.correlation_id,
        expected_prefix="cor",
    )
    checked_scope = tuple(unresolved_scope)
    if (
        not checked_scope
        or len(checked_scope) > _MAX_UNRESOLVED_SCOPE_ITEMS
        or checked_scope != tuple(sorted(set(checked_scope)))
        or any(not item or item != item.strip() for item in checked_scope)
    ):
        raise ValueError("unresolved scope is invalid or unbounded")
    scope_text = ",".join(checked_scope)
    if len(scope_text) > _MAX_UNRESOLVED_SCOPE_TEXT:
        raise ValueError("unresolved scope text is unbounded")
    return (
        request_id,
        checked_workflow_id,
        correlation_id,
        checked_scope,
        scope_text,
    )


def _build_broker_state_unknown_event_value(
    receipt: ExecutionReceipt,
    *,
    incident_id: str,
    unresolved_scope: Sequence[str],
    occurred_at: datetime,
    workflow_id: str,
) -> OperationalEvent:
    """Build one critical event from a persisted retry-locked outcome.

    Args:
        receipt: Authoritative unknown-outcome execution receipt.
        incident_id: Persisted Trading incident identity.
        unresolved_scope: Ordered unresolved reconciliation identities.
        occurred_at: Persisted transition occurrence time.
        workflow_id: Originating canonical workflow trace.

    Returns:
        Deterministic bounded critical operational event.

    Raises:
        TradingError: If source, trace, time, or bounded facts are incompatible.
    """
    logger.warning("Building critical unknown-broker-state event")
    try:
        (
            request_id,
            checked_workflow_id,
            correlation_id,
            checked_scope,
            scope_text,
        ) = _validate_unknown_event_source(
            receipt,
            incident_id=incident_id,
            unresolved_scope=unresolved_scope,
            occurred_at=occurred_at,
            workflow_id=workflow_id,
        )
        digest = sha256(
            canonical_json(
                {
                    "receipt_id": receipt.receipt_id,
                    "incident_id": incident_id,
                    "unresolved_scope": checked_scope,
                }
            ).encode("utf-8")
        ).hexdigest()
        return OperationalEvent(
            event_id=f"trd-broker-unknown-{digest}",
            event_type="BROKER_STATE_UNKNOWN",
            severity="critical",
            occurred_at=occurred_at,
            request_id=request_id,
            workflow_id=checked_workflow_id,
            correlation_id=correlation_id,
            causation_id=None,
            facts={
                "retry_locked": True,
                "unresolved_scope": scope_text,
            },
            source_refs={
                "receipt_id": receipt.receipt_id,
                "incident_id": incident_id,
            },
        )
    except (TypeError, ValueError, Exception) as error:
        raise TradingError(
            "VALIDATION_FAILED",
            "Unknown broker-state event source is invalid",
        ) from error


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
        causation_id=None,
        facts={"failed_event_type": event.event_type},
        source_refs={"failed_event_id": event.event_id},
    )


def _emit_runtime_event_value(
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


def build_broker_state_unknown_event(
    receipt: ExecutionReceipt,
    *,
    incident_id: str,
    unresolved_scope: Sequence[str],
    occurred_at: datetime,
    workflow_id: str,
) -> StandardResponse[OperationalEvent]:
    """Build unknown-outcome evidence in a standard response.

    Args:
        receipt: Authoritative unknown-outcome execution receipt.
        incident_id: Persisted Trading incident identity.
        unresolved_scope: Ordered unresolved reconciliation identities.
        occurred_at: Persisted transition occurrence time.
        workflow_id: Originating canonical workflow trace.

    Returns:
        Canonical response containing the operational event or a mapped error.
    """
    try:
        event = _build_broker_state_unknown_event_value(
            receipt,
            incident_id=incident_id,
            unresolved_scope=unresolved_scope,
            occurred_at=occurred_at,
            workflow_id=workflow_id,
        )
    except TradingError as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"incident_id": incident_id})
    return success_trading_response(
        event,
        risk_level="critical",
        legacy_status="unknown_outcome",
        extensions={"incident_id": incident_id},
    )


def emit_runtime_event(
    event: OperationalEvent,
    sink: Callable[[OperationalEvent], None],
) -> StandardResponse[None]:
    """Publish runtime evidence in a standard response.

    Args:
        event: Validated Trading operational evidence.
        sink: Composition-owned synchronous publication boundary.

    Returns:
        Successful empty response or a canonical mapped Trading error.
    """
    try:
        _emit_runtime_event_value(event, sink)
    except TradingError as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"event_id": event.event_id})
    return success_trading_response(
        None,
        risk_level="high",
        legacy_status="emitted",
        extensions={"event_id": event.event_id},
    )


__all__ = [
    "OperationalEvent",
    "build_broker_state_unknown_event",
    "emit_runtime_event",
]
