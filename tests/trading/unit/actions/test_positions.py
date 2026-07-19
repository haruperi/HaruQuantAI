"""Unit tests for route-aware Trading position actions."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.trading.actions import (
    close_position,
    modify_position,
    reduce_exposure,
)
from app.services.trading.contracts import TradingError
from tests.trading.unit.actions.test_dependencies import (
    dependencies,
    execution_store,
    policy,
    request,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def position_request(action: str, **updates: object):
    """Build one addressed position mutation request."""
    values = {
        "action": action,
        "position_id": "position-001",
        "target_broker_position_id": "position-001",
        **updates,
    }
    return request(**values)


def position_dependencies(*, action_policy=None):
    """Build dependencies with exact Trading-state position identity."""
    return dependencies(store=execution_store(), action_policy=action_policy)


@pytest.mark.anyio
async def test_partial_close_preserves_position_identity() -> None:
    """A partial close dispatches against the exact addressed position."""
    outcome = await close_position(
        position_request("close_position", quantity=Decimal(1)), position_dependencies()
    )
    assert outcome.status == "sent"


@pytest.mark.anyio
async def test_modify_position_rejects_unapproved_field() -> None:
    """Stop changes outside Risk mutable_fields authority are rejected."""
    item = position_request(
        "modify_position",
        order_type="LIMIT",
        stop_loss=Decimal("1.0000"),
        price=Decimal("1.1000"),
    )
    deps = position_dependencies(
        action_policy=policy("modify_position", mutable_fields="take_profit")
    )
    with pytest.raises(TradingError, match="SCOPE_MISMATCH"):
        await modify_position(item, deps)


@pytest.mark.anyio
async def test_modify_position_accepts_approved_stop_scope() -> None:
    """A declared stop-loss mutation follows the ordinary dispatch path."""
    item = position_request(
        "modify_position",
        order_type="LIMIT",
        stop_loss=Decimal("1.0000"),
        price=Decimal("1.1000"),
    )
    deps = position_dependencies(
        action_policy=policy("modify_position", mutable_fields="stop_loss")
    )
    assert (await modify_position(item, deps)).status == "sent"


@pytest.mark.anyio
async def test_reduce_exposure_cannot_increase() -> None:
    """A reduction larger than current exposure is rejected before dispatch."""
    item = position_request("reduce_exposure", quantity=Decimal(3))
    with pytest.raises(TradingError, match="VALIDATION_FAILED"):
        await reduce_exposure(item, position_dependencies())


@pytest.mark.anyio
async def test_reduce_exposure_executes_exact_approved_quantity() -> None:
    """An in-bounds exact Risk-approved reduction dispatches once."""
    item = position_request("reduce_exposure", quantity=Decimal("0.50"))
    assert (await reduce_exposure(item, position_dependencies())).status == "sent"
