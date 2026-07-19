"""Unit tests for explicit gated Trading bulk actions."""

# ruff: noqa: INP001

from dataclasses import replace
from decimal import Decimal

import pytest
from app.services.trading.actions import cancel_all_orders, close_all_positions
from app.services.trading.actions.emergency import _validated_child
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.state import TradingProjection
from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    dependencies,
    policy,
    request,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


async def unknown_dispatch(intent: OrderIntent) -> ExecutionReceipt:
    """Return one uncertain authority outcome for preservation tests."""
    return ExecutionReceipt(
        receipt_id="receipt-unknown",
        intent_id=intent.source_intent_id,
        client_order_id=intent.client_order_id,
        route=intent.route,
        authority="simulation",
        status="unknown_outcome",
        requested_quantity=intent.approved_volume,
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id=intent.request_id,
        correlation_id=intent.correlation_id,
    )


def emergency_dependencies(action: str):
    """Build bulk dependencies with broker targets sourced from Trading state."""
    store = MemoryStore()
    store.projection = TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=1,
        orders={
            "order-001": {"symbol": "EURUSD", "broker_order_id": "order-001"},
            "order-filled": {
                "symbol": "EURUSD",
                "broker_order_id": "order-filled",
            },
        },
        positions={
            "position-001": {
                "symbol": "EURUSD",
                "broker_position_id": "position-001",
            }
        },
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    return dependencies(store=store, action_policy=policy(action, max_children="5"))


def test_derived_child_is_revalidated_before_dispatch() -> None:
    """An invalid derived cancellation fails before any authority callback."""
    with pytest.raises(TradingError, match="INVALID_REQUEST"):
        _validated_child(
            request(action="cancel_all_orders"),
            {
                "action": "cancel_order",
                "order_type": "LIMIT",
                "price": None,
                "target_broker_order_id": None,
            },
        )


@pytest.mark.anyio
async def test_cancel_all_preserves_uncertain_results() -> None:
    """Bulk cancel reports uncertainty and skips already-filled work."""
    deps = emergency_dependencies("cancel_all_orders")
    deps = replace(deps, simulation_dispatch=unknown_dispatch)
    outcome = await cancel_all_orders(request(action="cancel_all_orders"), deps)
    assert outcome.status == "partial"
    assert outcome.data["results"][0]["status"] == "unknown_outcome"
    assert outcome.data["skipped"] == [{"order_id": "order-filled", "state": "FILLED"}]


@pytest.mark.anyio
async def test_close_all_reports_partial_completion() -> None:
    """Bulk close returns every child authority result."""
    deps = emergency_dependencies("close_all_positions")
    outcome = await close_all_positions(request(action="close_all_positions"), deps)
    assert outcome.status == "success"
    assert len(outcome.data["results"]) == 1


@pytest.mark.anyio
async def test_bulk_ceiling_blocks_before_children() -> None:
    """Risk max_children is enforced before any bulk mutation."""
    deps = dependencies(action_policy=policy("cancel_all_orders", max_children="0"))
    with pytest.raises(TradingError, match="PERMISSION_DENIED"):
        await cancel_all_orders(request(action="cancel_all_orders"), deps)
