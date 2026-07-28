"""Unit tests for Trading operational-event evidence and publication."""

# ruff: noqa: INP001
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.trading.contracts import ExecutionReceipt
from app.services.trading.monitoring import (
    OperationalEvent,
    build_broker_state_unknown_event,
    emit_runtime_event,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


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
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        facts={"state": "degraded", "api_key": "secret-value"},
        source_refs={"session": "session-001"},
    )


def test_event_has_trace_and_severity() -> None:
    """Preserve required trace/severity while redacting sensitive facts."""
    logger.debug("Testing OperationalEvent trace and redaction")
    event = _event()
    assert event.severity == "warning"
    assert event.workflow_id == WORKFLOW_ID
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

    result = emit_runtime_event(_event(), flaky_sink)
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "SERVICE_UNAVAILABLE"
    assert delivered[-1].event_type == "EVENT_DELIVERY_FAILED"


def _unknown_receipt() -> ExecutionReceipt:
    """Build one canonical retry-locked unknown-outcome receipt.

    Returns:
        Valid Trading execution receipt.
    """
    return ExecutionReceipt(
        receipt_id="receipt-unknown-001",
        intent_id="intent-001",
        client_order_id="client-order-001",
        route="sim",
        authority="simulator",
        status="unknown_outcome",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )


def test_unknown_broker_state_event_is_critical_and_traceable() -> None:
    """Build deterministic critical evidence from exact retry-lock sources."""
    first = build_broker_state_unknown_event(
        _unknown_receipt(),
        incident_id="incident-001",
        unresolved_scope=("order:order-001",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    second = build_broker_state_unknown_event(
        _unknown_receipt(),
        incident_id="incident-001",
        unresolved_scope=("order:order-001",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )

    assert first.status == "success"
    assert second.status == "success"
    assert first.data == second.data
    assert first.data is not None
    event = first.data
    assert event.event_type == "BROKER_STATE_UNKNOWN"
    assert event.severity == "critical"
    assert event.facts == {
        "retry_locked": True,
        "unresolved_scope": "order:order-001",
    }
    assert event.source_refs == {
        "receipt_id": "receipt-unknown-001",
        "incident_id": "incident-001",
    }


def test_unknown_broker_state_event_rejects_non_unknown_receipt() -> None:
    """Reject source evidence that does not prove a retry lock."""
    receipt = _unknown_receipt().model_copy(
        update={
            "status": "rejected",
            "retry_safe": True,
            "reconciliation_required": False,
        }
    )

    result = build_broker_state_unknown_event(
        receipt,
        incident_id="incident-001",
        unresolved_scope=("order:order-001",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "VALIDATION_FAILED"
