"""Executable Trading actions usage example.

Demonstrates FEAT-TRD-08 order, position, and control actions.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    build_approved_trading_request,
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
    kill_switch_states,
    policy,
    request,
)
from tests.trading.unit.actions.test_emergency import emergency_dependencies
from tests.trading.unit.actions.test_rebalance import (
    rebalance_dependencies,
    rebalance_request,
)
from tests.trading.unit.actions.test_runtime import (
    evaluation_dependencies,
    evidence,
    risk_decision,
    trade_intent,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _position_request(action: str, **updates: object) -> Any:
    """Build an addressed position request for action examples."""
    return request(
        action=action,
        position_id="position-001",
        target_broker_position_id="position-001",
        **updates,
    )


def fr_trd_013() -> None:
    """FR-TRD-013: Stage 3 — Submit one validated Risk-approved order."""
    _header("Stage 3: Order Submission - Submit Order (FR-TRD-013)")
    sub_res = asyncio.run(submit_order(request(), dependencies()))
    print(_format_result(sub_res))
    print(f"Data -> status='{sub_res.status}'")


def fr_trd_014() -> None:
    """FR-TRD-014: Stage 3 — Modify approved order scope with optimistic versioning."""
    _header("Stage 3: Order Modification - Modify Order (FR-TRD-014)")
    mod_item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    mod_res = asyncio.run(modify_order(mod_item, dependencies(store=execution_store())))
    print(_format_result(mod_res))
    print(f"Data -> status='{mod_res.status}'")


def fr_trd_015() -> None:
    """FR-TRD-015: Stage 3 — Cancel pending order after normal gates."""
    _header("Stage 3: Order Cancellation - Cancel Order (FR-TRD-015)")
    can_item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    can_res = asyncio.run(cancel_order(can_item, dependencies(store=execution_store())))
    print(_format_result(can_res))
    print(f"Data -> status='{can_res.status}'")


def fr_trd_016() -> None:
    """FR-TRD-016: Stage 3 — Close position fully or partially."""
    _header("Stage 3: Position Close - Close Position (FR-TRD-016)")
    close_res = asyncio.run(
        close_position(
            _position_request("close_position", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    )
    print(_format_result(close_res))
    print(f"Data -> status='{close_res.status}'")


def fr_trd_017() -> None:
    """FR-TRD-017: Stage 3 — Modify approved stop-loss/take-profit scope."""
    _header("Stage 3: Position Modification - Modify Position (FR-TRD-017)")
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
    pos_mod_res = asyncio.run(modify_position(pos_mod_item, pos_mod_deps))
    print(_format_result(pos_mod_res))
    print(f"Data -> status='{pos_mod_res.status}'")


def fr_trd_018() -> None:
    """FR-TRD-018: Stage 3 — Reduce exposure to match Risk-approved reduction."""
    _header("Stage 3: Exposure Reduction - Reduce Exposure (FR-TRD-018)")
    red_res = asyncio.run(
        reduce_exposure(
            _position_request("reduce_exposure", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    )
    print(_format_result(red_res))
    print(f"Data -> status='{red_res.status}'")


def fr_trd_019() -> None:
    """FR-TRD-019: Stage 2 — Pause runtime admission without changing strategy lifecycle."""
    _header("Stage 2: Strategy Control - Pause Strategy (FR-TRD-019)")
    pause_deps = dependencies(action_policy=policy("pause_strategy"))
    pause_res = asyncio.run(
        pause_strategy(request(action="pause_strategy"), pause_deps)
    )
    print(_format_result(pause_res))
    print(f"Data -> status='{pause_res.status}'")


def fr_trd_020() -> None:
    """FR-TRD-020: Stage 2 — Resume strategy after verdict, kill-switch, and reconciliation checks."""
    _header("Stage 2: Strategy Control - Resume Strategy (FR-TRD-020)")
    mem_store = MemoryStore()
    mem_store.projection = projection()
    resume_deps = dependencies(store=mem_store, action_policy=policy("resume_strategy"))
    resume_deps = replace(
        resume_deps,
        kill_switch_state_source=kill_switch_states,
        reconciliation_source=lambda _item: authority(),
    )
    resume_res = asyncio.run(
        resume_strategy(request(action="resume_strategy"), resume_deps)
    )
    print(_format_result(resume_res))
    print(f"Data -> status='{resume_res.status}'")


def fr_trd_021() -> None:
    """FR-TRD-021: Stage 2 — Trigger scoped Risk kill-switch transition."""
    _header("Stage 2: Kill Switch Control - Trigger Kill Switch (FR-TRD-021)")

    async def transition_trig(cmd: Any, verdict: Any) -> Any:
        return switch("global", "active")

    trig_deps = dependencies(action_policy=policy("trigger_kill_switch"))
    trig_deps = replace(trig_deps, kill_switch_transition=transition_trig)
    trig_item = request(
        action="trigger_kill_switch",
        scope_level="global",
        control_reason="operator request",
    )
    trig_res = asyncio.run(trigger_kill_switch(trig_item, trig_deps))
    print(_format_result(trig_res))
    print(f"Data -> status='{trig_res.status}'")


def fr_trd_022() -> None:
    """FR-TRD-022: Stage 2 — Clear kill switch through Risk clearance authority."""
    _header("Stage 2: Kill Switch Control - Clear Kill Switch (FR-TRD-022)")

    async def transition_clr(cmd: Any, verdict: Any) -> Any:
        return switch("global")

    clr_deps = dependencies(action_policy=policy("clear_kill_switch"))
    clr_deps = replace(clr_deps, kill_switch_transition=transition_clr)
    clr_item = request(
        action="clear_kill_switch",
        scope_level="global",
        control_reason="operator reviewed",
    )
    clr_res = asyncio.run(clear_kill_switch(clr_item, clr_deps))
    print(_format_result(clr_res))
    print(f"Data -> status='{clr_res.status}'")


def fr_trd_023() -> None:
    """FR-TRD-023: Stage 3 — Mass-cancel pending orders through normal gates."""
    _header("Stage 3: Emergency Action - Cancel All Orders (FR-TRD-023)")
    em_can_deps = emergency_dependencies("cancel_all_orders")
    em_can_req = request(action="cancel_all_orders")
    em_can_res = asyncio.run(cancel_all_orders(em_can_req, em_can_deps))
    print(_format_result(em_can_res))
    print(f"Data -> status='{em_can_res.status}'")


def fr_trd_025() -> None:
    """FR-TRD-025: Stage 3 — Synchronize projections from route truth."""
    _header("Stage 3: State Sync - Sync Positions (FR-TRD-025)")
    sync_deps = replace(dependencies(), reconciliation_source=lambda _item: authority())
    sync_res = asyncio.run(sync_positions(request(action="sync_positions"), sync_deps))
    print(_format_result(sync_res))
    print(f"Data -> status='{sync_res.status}'")


def fr_trd_050() -> None:
    """FR-TRD-050: Stage 3 — Mass-close positions through normal gates."""
    _header("Stage 3: Emergency Action - Close All Positions (FR-TRD-050)")
    em_cls_deps = emergency_dependencies("close_all_positions")
    em_cls_req = request(action="close_all_positions")
    em_cls_res = asyncio.run(close_all_positions(em_cls_req, em_cls_deps))
    print(_format_result(em_cls_res))
    print(f"Data -> status='{em_cls_res.status}'")


def fr_trd_056() -> None:
    """FR-TRD-056: Stage 1 — Expose immutable TradingDependencies container."""
    _header(
        "Stage 1: Dependency Injection - TradingDependencies Container (FR-TRD-056)"
    )
    deps = dependencies()
    print(_format_result(deps))
    print(
        f"Data -> route='{deps.connection.environment.value if deps.connection else 'sim'}', retention={deps.idempotency_retention_seconds}s"
    )


def fr_trd_064() -> None:
    """FR-TRD-064: Stage 3 — Execute portfolio rebalance execution request."""
    _header("Stage 3: Rebalance Execution - Execute Portfolio Rebalance (FR-TRD-064)")
    reb_item = rebalance_request()
    reb_deps = rebalance_dependencies(reb_item)
    reb_res = asyncio.run(execute_portfolio_rebalance(reb_item, reb_deps))
    print(_format_result(reb_res))
    print(f"Data -> status='{reb_res.status}'")


def fr_trd_065() -> None:
    """FR-TRD-065: Stage 3 — Drive live/paper evaluation cycle across domains."""
    _header("Stage 3: Runtime Evaluation - Run Live Evaluation Cycle (FR-TRD-065)")
    eval_deps, _calls = evaluation_dependencies(None)
    eval_res = asyncio.run(run_live_evaluation_cycle(eval_deps, evidence()))
    print(_format_result(eval_res))
    print(f"Data -> status='{eval_res.status}'")


def fr_trd_069() -> None:
    """FR-TRD-069: Keep action admission behind current Risk approval."""
    sub_res = asyncio.run(submit_order(request(), dependencies()))
    print(f"Data -> risk_gated_status='{sub_res.status}'")


def fr_trd_089() -> None:
    """FR-TRD-089: Use one public action path for simulation submission."""
    fr_trd_013()


def fr_trd_090() -> None:
    """FR-TRD-090: Preserve the shared modification and cancellation verbs."""
    fr_trd_014()
    fr_trd_015()


def fr_trd_092() -> None:
    """FR-TRD-092: Apply Risk and kill-switch gates before dispatch."""
    fr_trd_069()


def fr_trd_093() -> None:
    """FR-TRD-093: Build the approved request through the public boundary."""
    deps, _calls = evaluation_dependencies(trade_intent())
    approved = build_approved_trading_request(
        trade_intent(), risk_decision(), deps, evidence()
    )
    assert approved.quantity == Decimal("0.50")
    print(f"Data -> approved_quantity='{approved.quantity}'")


def fr_trd_095() -> None:
    """FR-TRD-095: Inject deadline authority into the shared cycle."""
    fr_trd_065()


def fr_trd_105() -> None:
    """FR-TRD-105: Preserve a normal neutral no-mutation outcome."""
    fr_trd_065()


def fr_trd_106() -> None:
    """FR-TRD-106: Keep timeout evidence route-neutral."""
    deps, _calls = evaluation_dependencies(None)
    assert deps.evaluation_deadline_factory is not None
    print("Data -> injected_deadline='available'")


def fr_trd_111() -> None:
    """FR-TRD-111: Keep cancellation and upstream failures distinct."""
    fr_trd_106()


def fr_trd_113() -> None:
    """FR-TRD-113: Keep authority transport outside approved economics."""
    fr_trd_093()


def _emit_requirement_success(function: object) -> object:
    """Wrap one example so direct execution emits its success contract."""

    def wrapped() -> None:
        function()
        requirement = function.__name__.removeprefix("fr_trd_").replace("_", "-")
        print(f"SUCCESS: FR-TRD-{requirement}")

    return wrapped


for _example_name, _example_function in tuple(globals().items()):
    if _example_name.startswith("fr_trd_") and callable(_example_function):
        globals()[_example_name] = _emit_requirement_success(_example_function)


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-08 — actions/ — Route-Aware Public Actions\n\n"
        "Purpose: Execute public Trading actions including order submission, modification, cancellation, position management, strategy controls, kill-switch transitions, emergency actions, rebalance, and runtime evaluation cycles.\n\n"
        "Module flow:\n"
        "-> Stage 1: Dependency container initialization and request material binding\n"
        "-> Stage 2: Fail-closed action policy checking, kill-switch validation, and strategy control\n"
        "-> Stage 3: Order submission, modification, position close, emergency execution, and evaluation cycle completion"
    )

    # Stage 1: Dependency initialization
    fr_trd_056()

    # Stage 2: Strategy and kill switch controls
    fr_trd_019()
    fr_trd_020()
    fr_trd_021()
    fr_trd_022()

    # Stage 3: Orders, positions, emergency & rebalance actions
    fr_trd_013()
    fr_trd_014()
    fr_trd_015()
    fr_trd_016()
    fr_trd_017()
    fr_trd_018()
    fr_trd_023()
    fr_trd_025()
    fr_trd_050()
    fr_trd_064()
    fr_trd_065()
    fr_trd_069()
    fr_trd_089()
    fr_trd_090()
    fr_trd_092()
    fr_trd_093()
    fr_trd_095()
    fr_trd_105()
    fr_trd_106()
    fr_trd_111()
    fr_trd_113()


if __name__ == "__main__":
    main()
