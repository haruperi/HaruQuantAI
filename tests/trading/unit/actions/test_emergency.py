"""Unit tests for explicit gated Trading bulk actions."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.brokers import get_broker_error_code
from app.services.trading.actions import (
    cancel_all_orders,
    close_all_positions,
    emergency,
)
from app.services.trading.actions.emergency import _validated_child
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.reconciliation import AuthoritySnapshot
from app.services.trading.state import (
    TradingProjection,
    create_execution_position,
    create_execution_position_store,
    set_execution_position,
)
from app.utils import validate_id

from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    dependencies,
    policy,
    request,
)
from tests.trading.unit.routing.test_dispatcher import _ErrorAdapter


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
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    store.execution_positions = create_execution_position_store()
    set_execution_position(
        store.execution_positions,
        create_execution_position(
            position_id="position-001",
            account_id="account-001",
            symbol="EURUSD",
            broker_position_id="position-001",
            state="OPEN",
            quantity=Decimal("2.00"),
            average_entry_price=Decimal("1.10"),
            source_sequence=1,
            version=1,
        ),
    )
    deps = dependencies(store=store)

    def policy_for(item):
        """Build exact parent or child action-policy evidence."""
        selected = policy(
            item.action,
            **({"max_children": "5"} if item.action == action else {}),
        )
        return selected.model_copy(
            update={
                "request_id": item.request_id,
                "workflow_id": item.workflow_id,
                "correlation_id": item.correlation_id,
            }
        )

    return replace(
        deps,
        action_policy_source=policy_for,
        reconciliation_source=lambda item: AuthoritySnapshot(
            route=item.route,
            authority_id="simulation",
            account_id=item.account_id,
            source_id="simulation-read-port",
            account={},
            orders={},
            positions={},
            observed_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        ),
    )


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
    deps = replace(
        deps,
        broker_adapter=_ErrorAdapter(
            get_broker_error_code("BROKER_RATE_LIMITED"),
            broker="sim",
            environment="simulation",
        ),
    )
    outcome = await cancel_all_orders(request(action="cancel_all_orders"), deps)
    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "partial"
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
async def test_bulk_children_receive_distinct_canonical_request_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every cancel/close child receives its own canonical UUID4 trace."""
    generated_requests = [
        "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "req-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    ]
    generated_causes = [
        "cau-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "cau-dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    ]
    issued: list[str] = []

    def issue_request_id(prefix: str) -> str:
        """Return the next deterministic canonical test request ID."""
        if prefix == "req":
            value = generated_requests[len(issued)]
            issued.append(value)
            return value
        value = generated_causes[len(issued) - 1]
        return value

    monkeypatch.setattr(emergency, "generate_id", issue_request_id)
    await cancel_all_orders(
        request(action="cancel_all_orders"),
        emergency_dependencies("cancel_all_orders"),
    )
    await close_all_positions(
        request(action="close_all_positions"),
        emergency_dependencies("close_all_positions"),
    )

    checked = tuple(validate_id(value, expected_prefix="req") for value in issued)
    assert checked == tuple(generated_requests)


@pytest.mark.anyio
async def test_bulk_ceiling_blocks_before_children() -> None:
    """Risk max_children is enforced before any bulk mutation."""
    deps = dependencies(action_policy=policy("cancel_all_orders", max_children="0"))
    result = await cancel_all_orders(request(action="cancel_all_orders"), deps)
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "PERMISSION_DENIED"
