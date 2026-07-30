"""Critical alert integration across Risk truth and the API sink boundary."""

from decimal import Decimal

from app.services.api import (
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
    deliver_critical_alert,
)
from app.services.trading import (
    build_broker_state_unknown_event,
    create_execution_receipt,
)

from tests.api.unit.test_alert_models import (
    CORRELATION_ID,
    NOW,
    REQUEST_ID,
    WORKFLOW_ID,
)
from tests.risk import _support as risk_support


def test_delivery_failure_cannot_change_authoritative_state() -> None:
    """Verify failed channel delivery leaves canonical active Risk truth intact."""
    state = risk_support._inactive_state().model_copy(
        update={"state": "active", "version": 2}
    )
    alert = build_kill_switch_activation_alert(
        state,
        risk_support._auth(risk_support._config()),
    )
    attempts: list[str] = []

    def unavailable_sink(value: object, *, idempotency_key: str) -> None:
        """Record and reject one channel delivery."""
        del value
        attempts.append(idempotency_key)
        raise RuntimeError("test channel unavailable")

    result = deliver_critical_alert(alert, unavailable_sink)

    assert result.status == "failed"
    assert result.failure_code == "ALERT_DELIVERY_FAILED"
    assert attempts == [alert.alert_id]
    assert state.state == "active"
    assert state.version == 2


def test_unknown_broker_alert_preserves_retry_lock_truth() -> None:
    """Verify Trading retry-lock truth survives API alert sink failure."""
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
    attempts = 0

    def unavailable_sink(value: object, *, idempotency_key: str) -> None:
        """Reject exactly one API alert attempt."""
        nonlocal attempts
        del value, idempotency_key
        attempts += 1
        raise RuntimeError("test channel unavailable")

    result = deliver_critical_alert(alert, unavailable_sink)

    assert result.status == "failed"
    assert attempts == 1
    assert event.data.facts["retry_locked"] is True
