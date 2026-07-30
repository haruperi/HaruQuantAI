"""Integration evidence for governed order and position modifications."""

from decimal import Decimal

import pytest
from app.services.trading import modify_order, modify_position

from tests.trading.conftest import (
    action_policy,
    execution_store,
    trading_dependencies,
    trading_request,
)


@pytest.mark.anyio
async def test_modifications_use_current_state_and_fresh_authority() -> None:
    """Order and position modifications each dispatch exactly once."""
    order_store = execution_store()
    order = await modify_order(
        trading_request(
            action="modify_order",
            order_id="order-001",
            target_broker_order_id="order-001",
            expected_version=1,
        ),
        trading_dependencies(store=order_store),
    )
    assert order.status == "success"
    assert order.data is not None
    assert order.data.requested_quantity == Decimal("1.00")
    assert [event.event_type for event in order_store.events] == [
        "send_attempted",
        "receipt_recorded",
    ]

    position_store = execution_store()
    position = await modify_position(
        trading_request(
            action="modify_position",
            order_type="LIMIT",
            position_id="position-001",
            target_broker_position_id="position-001",
            expected_version=1,
            price=Decimal("1.1000"),
            stop_loss=Decimal("1.0000"),
        ),
        trading_dependencies(
            store=position_store,
            action_policy=action_policy(
                "modify_position",
                mutable_fields="stop_loss",
            ),
        ),
    )
    assert position.status == "success"
    assert position.data is not None
    assert [event.event_type for event in position_store.events] == [
        "send_attempted",
        "receipt_recorded",
    ]
