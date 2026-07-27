"""Coverage expansion tests for trading/actions/emergency.py."""

from unittest.mock import MagicMock

import pytest
from app.services.trading.actions.emergency import (
    _bind_child_authority,
    _max_children,
    cancel_all_orders,
    close_all_positions,
)
from app.services.trading.contracts import TradingError


def test_max_children_validation() -> None:
    """Verify _max_children policy limit checks."""
    request = MagicMock()
    deps = MagicMock()

    # Unavailable policy
    deps.action_policy_source.return_value = None
    with pytest.raises(TradingError) as exc_info:
        _max_children(request, deps)
    assert exc_info.value.code == "PERMISSION_DENIED"

    # Malformed limit
    verdict = MagicMock(
        allowed=True, expires_at=9999999999, scope={"max_children": "invalid"}
    )
    deps.clock.return_value = 100
    deps.action_policy_source.return_value = verdict
    with pytest.raises(TradingError) as exc_info:
        _max_children(request, deps)
    assert exc_info.value.code == "PERMISSION_DENIED"

    # Non-positive limit
    verdict.scope = {"max_children": "-5"}
    with pytest.raises(TradingError) as exc_info:
        _max_children(request, deps)
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_bind_child_authority_sim_and_failures() -> None:
    """Verify _bind_child_authority sim route bypass and failure paths."""
    child = MagicMock()
    child.route.value = "sim"
    deps = MagicMock()

    # sim route returns child unchanged
    assert _bind_child_authority(child, deps) is child

    # non-sim route without decision -> raises TradingError
    child.route.value = "live"
    deps.child_risk_decision_source.return_value = None
    with pytest.raises(TradingError) as exc_info:
        _bind_child_authority(child, deps)
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_bulk_cancellation_and_closure_edge_cases() -> None:
    """Verify cancel_all_orders and close_all_positions failure modes."""
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    from app.services.trading.contracts import TradingRequest

    now = datetime.now(UTC)
    request = TradingRequest(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        causation_id="cau-44444444-4444-4444-8444-444444444444",
        route="sim",
        action="cancel_all_orders",
        account_id="acc-1",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="LIMIT",
        quantity_unit="units",
        quantity=Decimal("1.0"),
        price=Decimal("1.1000"),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-1",
        canonical_material_version="v1",
        system_time=now,
        valid_until=now + timedelta(minutes=5),
    )
    deps = MagicMock()

    async def run_test() -> None:
        # Projection is None -> TradingError
        deps.account_state_source.return_value = MagicMock(orders=[])
        deps.action_policy_source.return_value = MagicMock(
            allowed=True, expires_at=9999999999, scope={"max_children": "10"}
        )
        deps.clock.return_value = 100
        deps.store.load_projection.return_value = None

        with pytest.raises(TradingError) as exc_info:
            await cancel_all_orders(request, deps)
        assert exc_info.value.code == "RECONCILIATION_REQUIRED"

        # Oversized orders exceeding limit -> GATE_BLOCKED
        deps.account_state_source.return_value = MagicMock(
            orders=[MagicMock(), MagicMock()]
        )
        deps.action_policy_source.return_value = MagicMock(
            allowed=True, expires_at=9999999999, scope={"max_children": "1"}
        )
        deps.store.load_projection.return_value = MagicMock(orders={})

        with pytest.raises(TradingError) as exc_info:
            await cancel_all_orders(request, deps)
        assert exc_info.value.code == "GATE_BLOCKED"

        # Close all positions oversized -> GATE_BLOCKED
        req_close = request.model_copy(update={"action": "close_all_positions"})
        deps.account_state_source.return_value = MagicMock(
            positions=[MagicMock(), MagicMock()]
        )

        with pytest.raises(TradingError) as exc_info:
            await close_all_positions(req_close, deps)
        assert exc_info.value.code == "GATE_BLOCKED"

        # Cancel orders loop with cancellable order
        from unittest.mock import AsyncMock, patch

        req_cancel = request.model_copy(update={"action": "cancel_all_orders"})
        ord_can = MagicMock(
            order_id="ord-can",
            state="ACCEPTED",
            symbol="EURUSD",
            side="BUY",
            quantity=Decimal("1.0"),
            price=Decimal("1.1"),
        )
        deps.account_state_source.return_value = MagicMock(orders=[ord_can])
        deps.action_policy_source.return_value = MagicMock(
            allowed=True, expires_at=9999999999, scope={"max_children": "10"}
        )
        deps.store.load_projection.return_value = MagicMock(
            version=1, orders={"ord-can": {"broker_order_id": "ord-can"}}
        )

        with patch(
            "app.services.trading.actions.emergency.cancel_order",
            new_callable=AsyncMock,
        ) as mock_cancel:
            mock_cancel.return_value = MagicMock(status="success", data={})
            env_can = await cancel_all_orders(req_cancel, deps)
            assert env_can.status == "success"

        # Close positions loop with open position
        pos_open = MagicMock(
            position_id="pos-open",
            symbol="EURUSD",
            side="LONG",
            quantity=Decimal("1.0"),
        )
        deps.account_state_source.return_value = MagicMock(positions=[pos_open])
        deps.store.load_projection.return_value = MagicMock(
            version=1, positions={"pos-open": {"broker_position_id": "pos-open"}}
        )

        with patch(
            "app.services.trading.actions.emergency.close_position",
            new_callable=AsyncMock,
        ) as mock_close:
            mock_close.return_value = MagicMock(status="success", data={})
            env_pos = await close_all_positions(req_close, deps)
            assert env_pos.status == "success"

    import asyncio

    asyncio.run(run_test())
