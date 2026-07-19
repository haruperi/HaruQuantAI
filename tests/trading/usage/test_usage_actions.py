"""Runnable usage examples for the canonical Trading action API."""

# ruff: noqa: ARG005

from dataclasses import replace
from decimal import Decimal

import pytest
from app.services.trading.actions import (
    TradingDependencies,
    cancel_all_orders,
    cancel_order,
    clear_kill_switch,
    close_all_positions,
    close_position,
    execute_portfolio_rebalance,
    modify_order,
    modify_position,
    pause_strategy,
    reduce_exposure,
    resume_strategy,
    run_live_evaluation_cycle,
    submit_order,
    sync_positions,
    trigger_kill_switch,
)
from tests.trading.unit.actions.test_controls import authority, projection, switch
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
    execution_store,
    policy,
    request,
)
from tests.trading.unit.actions.test_emergency import emergency_dependencies
from tests.trading.unit.actions.test_rebalance import (
    rebalance_dependencies,
    rebalance_request,
)
from tests.trading.unit.actions.test_runtime import evaluation_dependencies, evidence


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def test_usage_dependencies_trading_dependencies() -> None:
    """Compose every Trading authority explicitly at the application boundary."""
    assert isinstance(dependencies(), TradingDependencies)


@pytest.mark.anyio
async def test_usage_orders_submit_order() -> None:
    """Submit one complete Risk-approved Simulation order."""
    assert (await submit_order(request(), dependencies())).status == "sent"


@pytest.mark.anyio
async def test_usage_orders_modify_order() -> None:
    """Modify one addressed, versioned order."""
    item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    assert (
        await modify_order(item, dependencies(store=execution_store()))
    ).status == "sent"


@pytest.mark.anyio
async def test_usage_orders_cancel_order() -> None:
    """Cancel one addressed pending order."""
    item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    assert (
        await cancel_order(item, dependencies(store=execution_store()))
    ).status == "sent"


def _position_request(action: str, **updates: object):
    """Build an addressed position request for action examples."""
    return request(
        action=action,
        position_id="position-001",
        target_broker_position_id="position-001",
        **updates,
    )


@pytest.mark.anyio
async def test_usage_positions_close_position() -> None:
    """Close part of one exact position."""
    assert (
        await close_position(
            _position_request("close_position", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    ).status == "sent"


@pytest.mark.anyio
async def test_usage_positions_modify_position() -> None:
    """Modify one Risk-authorized stop field."""
    item = _position_request(
        "modify_position",
        order_type="LIMIT",
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0000"),
    )
    deps = dependencies(
        store=execution_store(),
        action_policy=policy("modify_position", mutable_fields="stop_loss"),
    )
    assert (await modify_position(item, deps)).status == "sent"


@pytest.mark.anyio
async def test_usage_positions_reduce_exposure() -> None:
    """Reduce exposure by the exact approved quantity."""
    assert (
        await reduce_exposure(
            _position_request("reduce_exposure", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    ).status == "sent"


@pytest.mark.anyio
async def test_usage_controls_pause_strategy() -> None:
    """Pause only Trading admission for one strategy."""
    deps = dependencies(action_policy=policy("pause_strategy"))
    assert (
        await pause_strategy(request(action="pause_strategy"), deps)
    ).status == "success"


@pytest.mark.anyio
async def test_usage_controls_resume_strategy() -> None:
    """Resume after inactive switches and matching route truth."""
    store = MemoryStore()
    store.projection = projection()
    deps = dependencies(store=store, action_policy=policy("resume_strategy"))
    deps = replace(
        deps,
        kill_switch_state_source=lambda item: (switch("global"),),
        reconciliation_source=lambda item: authority(),
    )
    assert (
        await resume_strategy(request(action="resume_strategy"), deps)
    ).status == "success"


@pytest.mark.anyio
async def test_usage_controls_sync_positions() -> None:
    """Persist read-only authority comparison evidence."""
    deps = replace(dependencies(), reconciliation_source=lambda item: authority())
    assert (
        await sync_positions(request(action="sync_positions"), deps)
    ).status == "success"


@pytest.mark.anyio
async def test_usage_controls_trigger_kill_switch() -> None:
    """Send an explicitly scoped activation to the Risk transition port."""

    async def transition(command, verdict):
        """Return the Risk-owned active state for the example."""
        return switch("global", "active")

    deps = dependencies(action_policy=policy("trigger_kill_switch"))
    deps = replace(deps, kill_switch_transition=transition)
    item = request(
        action="trigger_kill_switch",
        scope_level="global",
        control_reason="operator request",
    )
    assert (await trigger_kill_switch(item, deps)).status == "success"


@pytest.mark.anyio
async def test_usage_controls_clear_kill_switch() -> None:
    """Send Risk-authorized clearance when no parent is active."""

    async def transition(command, verdict):
        """Return the Risk-owned inactive state for the example."""
        return switch("global")

    deps = dependencies(action_policy=policy("clear_kill_switch"))
    deps = replace(deps, kill_switch_transition=transition)
    item = request(
        action="clear_kill_switch",
        scope_level="global",
        control_reason="operator reviewed",
    )
    assert (await clear_kill_switch(item, deps)).status == "success"


@pytest.mark.anyio
async def test_usage_emergency_cancel_all() -> None:
    """Cancel eligible orders and retain skipped results."""
    deps = emergency_dependencies("cancel_all_orders")
    assert (
        await cancel_all_orders(request(action="cancel_all_orders"), deps)
    ).status == "partial"


@pytest.mark.anyio
async def test_usage_emergency_close_all() -> None:
    """Close every current position through ordinary gates."""
    deps = emergency_dependencies("close_all_positions")
    assert (
        await close_all_positions(request(action="close_all_positions"), deps)
    ).status == "success"


@pytest.mark.anyio
async def test_usage_rebalance_execute_portfolio_rebalance() -> None:
    """Execute an exact authorized reduce-only portfolio plan."""
    item = rebalance_request()
    assert (
        await execute_portfolio_rebalance(item, rebalance_dependencies(item))
    ).status == "success"


@pytest.mark.anyio
async def test_usage_runtime_run_live_evaluation_cycle() -> None:
    """End a neutral public-domain evaluation cycle without mutation."""
    deps, _calls = evaluation_dependencies(None)
    assert (await run_live_evaluation_cycle(deps, evidence())).status == "success"
