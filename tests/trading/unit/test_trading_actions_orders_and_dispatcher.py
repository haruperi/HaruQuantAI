"""Unit tests for Trading order actions and routing dispatcher."""

from __future__ import annotations

from app.services.trading.actions.orders import (
    cancel_order,
    modify_order,
    submit_order,
)
from app.services.trading.routing.dispatcher import (
    _classify_authority_response_value,
)


def test_trading_actions_orders_exports() -> None:
    """Verify order action exports exist."""
    assert submit_order is not None
    assert modify_order is not None
    assert cancel_order is not None


def test_trading_routing_dispatcher_classification() -> None:
    """Verify classification helper for authority responses."""
    capability = {
        "malformed_response_policy": "unknown_outcome",
        "mutation_retry_policy": "reconcile_before_retry",
    }
    raw = {
        "receipt_id": "r-1",
        "intent_id": "i-1",
        "client_order_id": "co-1",
        "route": "sim",
        "authority": "broker-1",
        "request_id": "req-a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
        "correlation_id": "cor-a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
        "authority_timestamp": "2026-08-17T10:00:00Z",
        "received_at": "2026-08-17T10:00:00Z",
        "requested_quantity": "1.0",
        "status": "FILLED",
    }
    cls = _classify_authority_response_value(raw, capability=capability)
    assert cls is not None
