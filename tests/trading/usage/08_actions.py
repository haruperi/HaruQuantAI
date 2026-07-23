"""Executable Trading actions usage example.

Demonstrates order, position, and control actions.
"""

# ruff: noqa: PLR0915

import asyncio
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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


def _position_request(action: str, **updates: object):
    """Build an addressed position request for action examples."""
    return request(
        action=action,
        position_id="position-001",
        target_broker_position_id="position-001",
        **updates,
    )


async def _async_example() -> None:
    """Run Trading actions sequentially."""

    # 1. TradingDependencies
    deps = dependencies()
    print(f"Dependencies initialized: {isinstance(deps, TradingDependencies)}")

    # 2. Submit order
    sub_res = await submit_order(request(), deps)
    print(f"Submit order status: {sub_res.status}")

    # 3. Modify order
    mod_item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    mod_res = await modify_order(mod_item, dependencies(store=execution_store()))
    print(f"Modify order status: {mod_res.status}")

    # 4. Cancel order
    can_item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    can_res = await cancel_order(can_item, dependencies(store=execution_store()))
    print(f"Cancel order status: {can_res.status}")

    # 5. Position actions: close, modify, reduce
    close_res = await close_position(
        _position_request("close_position", quantity=Decimal("0.50")),
        dependencies(store=execution_store()),
    )
    print(f"Close position status: {close_res.status}")

    pos_mod_item = _position_request(
        "modify_position",
        order_type="LIMIT",
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0000"),
    )
    pos_mod_deps = dependencies(
        store=execution_store(),
        action_policy=policy("modify_position", mutable_fields="stop_loss"),
    )
    pos_mod_res = await modify_position(pos_mod_item, pos_mod_deps)
    print(f"Modify position status: {pos_mod_res.status}")

    red_res = await reduce_exposure(
        _position_request("reduce_exposure", quantity=Decimal("0.50")),
        dependencies(store=execution_store()),
    )
    print(f"Reduce exposure status: {red_res.status}")

    # 6. Strategy controls: pause, resume, sync
    pause_deps = dependencies(action_policy=policy("pause_strategy"))
    pause_res = await pause_strategy(request(action="pause_strategy"), pause_deps)
    print(f"Pause strategy status: {pause_res.status}")

    mem_store = MemoryStore()
    mem_store.projection = projection()
    resume_deps = dependencies(store=mem_store, action_policy=policy("resume_strategy"))
    resume_deps = replace(
        resume_deps,
        kill_switch_state_source=lambda _item: (switch("global"),),
        reconciliation_source=lambda _item: authority(),
    )
    resume_res = await resume_strategy(request(action="resume_strategy"), resume_deps)
    print(f"Resume strategy status: {resume_res.status}")

    sync_deps = replace(dependencies(), reconciliation_source=lambda _item: authority())
    sync_res = await sync_positions(request(action="sync_positions"), sync_deps)
    print(f"Sync positions status: {sync_res.status}")

    # 7. Kill switch controls: trigger, clear
    async def transition_trig(cmd, verdict):
        return switch("global", "active")

    trig_deps = dependencies(action_policy=policy("trigger_kill_switch"))
    trig_deps = replace(trig_deps, kill_switch_transition=transition_trig)
    trig_item = request(
        action="trigger_kill_switch",
        scope_level="global",
        control_reason="operator request",
    )
    trig_res = await trigger_kill_switch(trig_item, trig_deps)
    print(f"Trigger kill switch status: {trig_res.status}")

    async def transition_clr(cmd, verdict):
        return switch("global")

    clr_deps = dependencies(action_policy=policy("clear_kill_switch"))
    clr_deps = replace(clr_deps, kill_switch_transition=transition_clr)
    clr_item = request(
        action="clear_kill_switch",
        scope_level="global",
        control_reason="operator reviewed",
    )
    clr_res = await clear_kill_switch(clr_item, clr_deps)
    print(f"Clear kill switch status: {clr_res.status}")

    # 8. Emergency actions: cancel_all, close_all
    em_can_deps = emergency_dependencies("cancel_all_orders")
    em_can_req = request(action="cancel_all_orders")
    em_can_res = await cancel_all_orders(em_can_req, em_can_deps)
    print(f"Cancel all orders status: {em_can_res.status}")

    em_cls_deps = emergency_dependencies("close_all_positions")
    em_cls_req = request(action="close_all_positions")
    em_cls_res = await close_all_positions(em_cls_req, em_cls_deps)
    print(f"Close all positions status: {em_cls_res.status}")

    # 9. Portfolio rebalance
    reb_item = rebalance_request()
    reb_deps = rebalance_dependencies(reb_item)
    reb_res = await execute_portfolio_rebalance(reb_item, reb_deps)
    print(f"Execute portfolio rebalance status: {reb_res.status}")

    # 10. Live evaluation cycle
    eval_deps, _calls = evaluation_dependencies(None)
    eval_res = await run_live_evaluation_cycle(eval_deps, evidence())
    print(f"Live evaluation cycle status: {eval_res.status}")


def example_actions() -> None:
    """Demonstrate Trading action execution."""
    print("=" * 80)
    print("Trading Example 8: Public Actions and Execution Control")
    print("=" * 80)
    asyncio.run(_async_example())


def main() -> None:
    """Run Trading actions usage example."""
    example_actions()


if __name__ == "__main__":
    main()
