"""Authoritative critical operational alert builder tests."""

from decimal import Decimal

import pytest
from app.services.api import (
    build_critical_alert_trigger,
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
    get_critical_alert_error_type,
)
from app.services.trading import (
    build_broker_state_unknown_event,
    create_execution_receipt,
    create_operational_event,
)

from tests.api.unit.test_alert_models import (
    CORRELATION_ID,
    NOW,
    REQUEST_ID,
    WORKFLOW_ID,
)
from tests.risk import _support as risk_support


def test_kill_switch_builder_is_deterministic_and_source_bound() -> None:
    """Verify active Risk state yields one deterministic redacted alert identity."""
    context = risk_support._auth(risk_support._config())
    state = risk_support._inactive_state().model_copy(
        update={"state": "active", "version": 2, "updated_at": NOW}
    )

    first = build_kill_switch_activation_alert(state, context)
    second = build_kill_switch_activation_alert(state, context)

    assert first == second
    assert first.trigger is build_critical_alert_trigger("RISK_KILL_SWITCH_ACTIVATED")
    assert first.source_id == state.state_id
    assert first.scope == {"scope_level": "global"}


def test_kill_switch_builder_rejects_non_active_state() -> None:
    """Verify inactive Risk state cannot fabricate an activation alert."""
    with pytest.raises(get_critical_alert_error_type(), match="ALERT_SOURCE_INVALID"):
        build_kill_switch_activation_alert(
            risk_support._inactive_state(),
            risk_support._auth(risk_support._config()),
        )


def test_unknown_broker_builder_rejects_non_authoritative_event() -> None:
    """Verify current non-unknown Trading events cannot trigger the closed alert."""
    event = create_operational_event(
        event_id="event-1",
        event_type="INCIDENT_RECORDED",
        severity="critical",
        occurred_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        facts={"retry_locked": True},
        source_refs={"receipt_id": "receipt-1", "incident_id": "incident-1"},
    )

    with pytest.raises(get_critical_alert_error_type(), match="ALERT_SOURCE_INVALID"):
        build_unknown_broker_state_alert(event)


def test_only_retry_locked_unknown_broker_event_builds_alert() -> None:
    """Verify exact Trading retry-lock evidence builds the closed API alert."""
    receipt = create_execution_receipt(
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
    event = build_broker_state_unknown_event(
        receipt,
        incident_id="incident-001",
        unresolved_scope=("order:order-001",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )

    assert event.status == "success"
    assert event.data is not None
    alert = build_unknown_broker_state_alert(event.data)

    assert alert.trigger is build_critical_alert_trigger("TRADING_BROKER_STATE_UNKNOWN")
    assert alert.source_id == event.data.event_id
    assert alert.scope == {
        "retry_locked": "true",
        "unresolved_scope": "order:order-001",
    }
