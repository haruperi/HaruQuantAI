"""Unit tests for route-aware Trading order actions."""

# ruff: noqa: INP001

import pytest
from app.services.trading.actions import cancel_order, modify_order, submit_order
from app.services.trading.contracts import TradingError, TradingRoute
from tests.trading.unit.actions.test_dependencies import (
    dependencies,
    execution_store,
    request,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


@pytest.mark.anyio
async def test_submit_order_route_parity() -> None:
    """Simulation dispatches while a Broker route without a session fails closed."""
    outcome = await submit_order(request(), dependencies())
    assert outcome.status == "sent"
    live = request(route=TradingRoute.LIVE, provider_id="mt5")
    with pytest.raises(TradingError, match="SERVICE_UNAVAILABLE"):
        await submit_order(live, dependencies())


@pytest.mark.anyio
async def test_modify_order_rejects_stale_version() -> None:
    """Order modification requires explicit optimistic version evidence."""
    item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=None,
    )
    with pytest.raises(TradingError, match="VERSION_CONFLICT"):
        await modify_order(item, dependencies())


@pytest.mark.anyio
async def test_cancel_order_is_idempotent() -> None:
    """Repeated cancellation cannot cause a second authority mutation."""
    store = execution_store()
    deps = dependencies(store=store)
    item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    first = await cancel_order(item, deps)
    assert first.status == "sent"
    with pytest.raises(TradingError, match="VERSION_CONFLICT"):
        await cancel_order(item, deps)
    assert len(store.events) == 1


@pytest.mark.anyio
async def test_order_verbs_reject_mismatched_actions() -> None:
    """Each order verb accepts only its exact canonical action."""
    with pytest.raises(TradingError, match="INVALID_REQUEST"):
        await cancel_order(request(), dependencies())
