"""Standalone bounded usage for critical operational alert delivery."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import (
    CriticalAlertDeliveryResult,
    CriticalAlertTrigger,
    CriticalOperationalAlert,
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
    deliver_critical_alert,
)
from app.services.risk import create_kill_switch_state
from app.services.trading import (
    build_broker_state_unknown_event,
    create_execution_receipt,
)
from app.utils import AuthContext

# Private type-only aliases; Risk exposes functions, not contract classes.
KillSwitchState = object

NOW = datetime(2026, 7, 24, 9, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _context() -> AuthContext:
    """Build one authenticated operator context.

    Returns:
        Valid shared authentication context.
    """
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-example",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment="simulation",
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )


def _active_state() -> KillSwitchState:
    """Build one active authoritative Risk state.

    Returns:
        Canonical active global state.
    """
    return create_kill_switch_state(
        state_id="global-state-example",
        scope_level="global",
        scope={},
        state="active",
        reason="operator safety stop",
        version=2,
        updated_at=NOW,
    )


def fr_api_064() -> CriticalOperationalAlert:
    """FR-API-064: Represent one of the two approved critical triggers, its
    deterministic authoritative-source binding, fixed-template bounded redacted
    content, and one delivery attempt/result without carrying secrets or provider
    objects.

    Returns:
        One bounded critical operational alert.
    """
    alert = build_kill_switch_activation_alert(_active_state(), _context())
    assert alert.trigger is CriticalAlertTrigger.RISK_KILL_SWITCH_ACTIVATED
    return CriticalOperationalAlert.model_validate(alert.model_dump())


def fr_api_065() -> CriticalOperationalAlert:
    """FR-API-065: Accept only an active Risk KillSwitchState v1 plus
    authenticated trace context and derive risk.kill_switch_activated with identity
    bound to state ID/version; inactive or unknown state never creates an alert.

    Returns:
        Deterministic active-state alert.
    """
    first = build_kill_switch_activation_alert(_active_state(), _context())
    second = build_kill_switch_activation_alert(_active_state(), _context())
    assert first.alert_id == second.alert_id
    return first


def fr_api_066() -> CriticalOperationalAlert:
    """FR-API-066: Accept only a critical Trading BROKER_STATE_UNKNOWN
    OperationalEvent v1 with retry_locked=true and receipt/incident references, and
    derive trading.broker_state_unknown with identity bound to the event ID.

    Returns:
        Deterministic alert bound to Trading retry-lock evidence.
    """
    receipt = create_execution_receipt(
        receipt_id="receipt-unknown-example",
        intent_id="intent-example",
        client_order_id="client-order-example",
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
        incident_id="incident-unknown-example",
        unresolved_scope=("order:order-example",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    assert event.status == "success"
    assert event.data is not None
    alert = build_unknown_broker_state_alert(event.data)
    assert alert.trigger is CriticalAlertTrigger.TRADING_BROKER_STATE_UNKNOWN
    return alert


def fr_api_067() -> CriticalAlertDeliveryResult:
    """FR-API-067: Submit the alert exactly once to an injected sink using
    alert_id as the idempotency key and return a delivered/failed
    CriticalAlertDeliveryResult.

    Returns:
        Structured successful delivery evidence.
    """
    alert = fr_api_065()
    attempts: list[str] = []

    def sink(value: CriticalOperationalAlert, *, idempotency_key: str) -> None:
        """Record one secret-safe demonstration delivery."""
        assert value == alert
        attempts.append(idempotency_key)

    result = deliver_critical_alert(alert, sink)
    assert attempts == [alert.alert_id]
    return CriticalAlertDeliveryResult.model_validate(result.model_dump())


def main() -> None:
    """Run every alert feature requirement demonstration."""
    alert = fr_api_064()
    fr_api_065()
    fr_api_066()
    delivery = fr_api_067()
    print(
        {
            "trigger": alert.trigger.value,
            "delivery_status": delivery.status,
            "attempts": 1,
        }
    )


if __name__ == "__main__":
    main()
