"""Unit tests for Trading operational-event evidence and publication."""

# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.trading.contracts import TradingError
from app.services.trading.monitoring import OperationalEvent, emit_runtime_event
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _event() -> OperationalEvent:
    """Build one valid operational event fixture.

    Returns:
        Valid operational evidence.
    """
    logger.debug("Building operational event test fixture")
    return OperationalEvent(
        event_id="event-001",
        event_type="HEALTH_CHANGED",
        severity="warning",
        occurred_at=NOW,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        facts={"state": "degraded", "api_key": "secret-value"},
        source_refs={"session": "session-001"},
    )


def test_event_has_trace_and_severity() -> None:
    """Preserve required trace/severity while redacting sensitive facts."""
    logger.debug("Testing OperationalEvent trace and redaction")
    event = _event()
    assert event.severity == "warning"
    assert event.workflow_id == "workflow-001"
    assert event.facts["api_key"] != "secret-value"


def test_event_rejects_sensitive_source_reference() -> None:
    """Operational source references cannot claim redaction while carrying secrets."""
    event = _event()
    with pytest.raises(ValueError, match="source references contain secrets"):
        OperationalEvent.model_validate(
            {
                "contract_version": event.contract_version,
                "schema_id": event.schema_id,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "occurred_at": event.occurred_at,
                "request_id": event.request_id,
                "workflow_id": event.workflow_id,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "facts": dict(event.facts),
                "source_refs": {"access_token": "t"},
                "redaction_applied": True,
            }
        )


def test_event_delivery_failure_is_incident() -> None:
    """Expose sink failure after offering a delivery incident."""
    logger.debug("Testing OperationalEvent delivery failure incident")
    delivered: list[OperationalEvent] = []

    def flaky_sink(event: OperationalEvent) -> None:
        """Reject the first event and retain the resulting incident.

        Args:
            event: Event offered for publication.
        """
        logger.debug("Invoking flaky operational-event sink")
        if not delivered:
            delivered.append(event)
            raise OSError("sink unavailable")
        delivered.append(event)

    with pytest.raises(TradingError, match="SERVICE_UNAVAILABLE"):
        emit_runtime_event(_event(), flaky_sink)
    assert delivered[-1].event_type == "EVENT_DELIVERY_FAILED"
