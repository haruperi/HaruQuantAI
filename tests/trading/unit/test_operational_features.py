"""Unit evidence for protective orders and trade ownership."""

from decimal import Decimal

import pytest
from app.services.trading import (
    assign_trade_ownership,
    build_protective_order_plan,
    build_trade_ownership,
    create_protective_order_plan,
    create_trade_ownership_registry,
    detect_orphaned_trade,
    parse_protective_order_plan,
    parse_trade_ownership,
    resize_protective_orders,
    verify_protective_order_coverage,
)
from app.services.trading.contracts import TradingError


def test_protection_is_versioned_covered_and_residual_bounded() -> None:
    """Protection transport and residual resizing remain fail closed."""
    plan = create_protective_order_plan(
        plan_id="protect-001",
        position_id="position-001",
        order_id="order-001",
        risk_decision_id="risk-001",
        quantity=Decimal(2),
        stop_price=Decimal(9),
        target_price=Decimal(12),
        oco_group_id="oco-001",
        source_sequence=1,
    )
    assert parse_protective_order_plan(build_protective_order_plan(plan)) == plan
    evidence = verify_protective_order_coverage(
        plan,
        open_quantity=Decimal(2),
        stop_acknowledged=True,
        target_acknowledged=True,
    )
    assert evidence["status"] == "PROTECTED"
    assert resize_protective_orders(
        plan, residual_quantity=Decimal(1), source_sequence=2
    ).quantity == Decimal(1)


def test_ownership_transport_and_orphan_detection() -> None:
    """Exact active ownership prevents false orphan classification."""
    mapping = build_trade_ownership(
        ownership_id="ownership-001",
        owner_type="player",
        owner_id="player-001",
        account_id="account-001",
        position_id="position-001",
        trade_plan_id="plan-001",
        strategy_version="v1",
        session_id="session-001",
        source_sequence=1,
    )
    ownership = parse_trade_ownership(mapping)
    registry = create_trade_ownership_registry()
    assert detect_orphaned_trade(registry, "position-001")
    assign_trade_ownership(registry, ownership)
    assert not detect_orphaned_trade(registry, "position-001")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"plan_id": ""}, "identifiers"),
        ({"quantity": Decimal(0)}, "numeric"),
        ({"target_price": Decimal(9)}, "must differ"),
    ],
)
def test_protection_rejects_invalid_contracts(
    changes: dict[str, object], message: str
) -> None:
    """Malformed protection evidence fails closed."""
    values: dict[str, object] = {
        "plan_id": "protect-001",
        "position_id": "position-001",
        "order_id": "order-001",
        "risk_decision_id": "risk-001",
        "quantity": Decimal(2),
        "stop_price": Decimal(9),
        "target_price": Decimal(12),
        "oco_group_id": "oco-001",
        "source_sequence": 1,
    }
    with pytest.raises(ValueError, match=message):
        create_protective_order_plan(**{**values, **changes})


def test_protection_operations_reject_unknown_or_exposure_increasing_state() -> None:
    """Protection cannot be fabricated or enlarged by a resize."""
    with pytest.raises(TradingError):
        verify_protective_order_coverage(
            object(),
            open_quantity=Decimal(1),
            stop_acknowledged=True,
            target_acknowledged=True,
        )
    plan = create_protective_order_plan(
        plan_id="protect-001",
        position_id="position-001",
        order_id="order-001",
        risk_decision_id="risk-001",
        quantity=Decimal(2),
        stop_price=Decimal(9),
        target_price=Decimal(12),
        oco_group_id="oco-001",
        source_sequence=1,
    )
    assert (
        verify_protective_order_coverage(
            plan,
            open_quantity=Decimal(1),
            stop_acknowledged=False,
            target_acknowledged=True,
        )["status"]
        == "UNKNOWN"
    )
    with pytest.raises(TradingError):
        resize_protective_orders(plan, residual_quantity=Decimal(3), source_sequence=2)
    with pytest.raises(TradingError):
        resize_protective_orders(plan, residual_quantity=Decimal(1), source_sequence=1)
    with pytest.raises(TradingError):
        build_protective_order_plan(object())
