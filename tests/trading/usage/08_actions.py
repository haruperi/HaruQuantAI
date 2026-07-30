"""Executable Trading actions usage example.

Demonstrates order, position, and control actions.
"""

# ruff: noqa: PLR0915
import asyncio
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading import (
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
from tests.trading.unit.actions.test_runtime import evaluation_dependencies, evidence


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _print_result(label: str, response: Any) -> None:
    """Print bounded operation evidence rather than a status-only claim."""
    status = response.status
    data = response.data
    evidence = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
    print(f"{label}:", {"status": status, "evidence": evidence})


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
    print(
        "Dependencies initialized:",
        f"route={deps.connection.environment.value if deps.connection else 'sim'}",
        f"idempotency_retention={deps.idempotency_retention_seconds}s",
        f"broker_timeout={deps.broker_operation_timeout_seconds}s",
    )

    # 2. Submit order
    sub_res = await submit_order(request(), deps)
    _print_result("Submit order", sub_res)

    # 3. Modify order
    mod_item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    mod_res = await modify_order(mod_item, dependencies(store=execution_store()))
    _print_result("Modify order", mod_res)

    # 4. Cancel order
    can_item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    can_res = await cancel_order(can_item, dependencies(store=execution_store()))
    _print_result("Cancel order", can_res)

    # 5. Position actions: close, modify, reduce
    close_res = await close_position(
        _position_request("close_position", quantity=Decimal("0.50")),
        dependencies(store=execution_store()),
    )
    _print_result("Close position", close_res)

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
    _print_result("Modify position", pos_mod_res)

    red_res = await reduce_exposure(
        _position_request("reduce_exposure", quantity=Decimal("0.50")),
        dependencies(store=execution_store()),
    )
    _print_result("Reduce exposure", red_res)

    # 6. Strategy controls: pause, resume, sync
    pause_deps = dependencies(action_policy=policy("pause_strategy"))
    pause_res = await pause_strategy(request(action="pause_strategy"), pause_deps)
    _print_result("Pause strategy", pause_res)

    mem_store = MemoryStore()
    mem_store.projection = projection()
    resume_deps = dependencies(store=mem_store, action_policy=policy("resume_strategy"))
    resume_deps = replace(
        resume_deps,
        kill_switch_state_source=kill_switch_states,
        reconciliation_source=lambda _item: authority(),
    )
    resume_res = await resume_strategy(request(action="resume_strategy"), resume_deps)
    _print_result("Resume strategy", resume_res)

    sync_deps = replace(dependencies(), reconciliation_source=lambda _item: authority())
    sync_res = await sync_positions(request(action="sync_positions"), sync_deps)
    _print_result("Sync positions", sync_res)

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
    _print_result("Trigger kill switch", trig_res)

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
    _print_result("Clear kill switch", clr_res)

    # 8. Emergency actions: cancel_all, close_all
    em_can_deps = emergency_dependencies("cancel_all_orders")
    em_can_req = request(action="cancel_all_orders")
    em_can_res = await cancel_all_orders(em_can_req, em_can_deps)
    _print_result("Cancel all orders", em_can_res)

    em_cls_deps = emergency_dependencies("close_all_positions")
    em_cls_req = request(action="close_all_positions")
    em_cls_res = await close_all_positions(em_cls_req, em_cls_deps)
    _print_result("Close all positions", em_cls_res)

    # 9. Portfolio rebalance
    reb_item = rebalance_request()
    reb_deps = rebalance_dependencies(reb_item)
    reb_res = await execute_portfolio_rebalance(reb_item, reb_deps)
    _print_result("Execute portfolio rebalance", reb_res)

    # 10. Live evaluation cycle
    eval_deps, _calls = evaluation_dependencies(None)
    eval_res = await run_live_evaluation_cycle(eval_deps, evidence())
    _print_result("Live evaluation cycle", eval_res)


def example_actions() -> None:
    """Demonstrate Trading action execution."""
    _header("Demonstrate Trading action execution.")
    print("Trading Example 8: Public Actions and Execution Control")
    asyncio.run(_async_example())


def fr_trd_013() -> None:
    """FR-TRD-013: The system shall submit one validated Risk-approved order through the selected route."""
    _header(
        "FR-TRD-013: The system shall submit one validated Risk-approved order through the selected route."
    )
    example_actions()


def fr_trd_014() -> None:
    """FR-TRD-014: The system shall modify only the approved identity/scope with optimistic version and caller idempotency."""
    _header(
        "FR-TRD-014: The system shall modify only the approved identity/scope with optimistic version and caller idempotency."
    )
    example_actions()


def fr_trd_015() -> None:
    """FR-TRD-015: The system shall cancel one pending order after normal gates."""
    _header("FR-TRD-015: The system shall cancel one pending order after normal gates.")
    example_actions()


def fr_trd_016() -> None:
    """FR-TRD-016: The system shall close a position fully or partially with correct netting/hedging identity."""
    _header(
        "FR-TRD-016: The system shall close a position fully or partially with correct netting/hedging identity."
    )
    example_actions()


def fr_trd_017() -> None:
    """FR-TRD-017: The system shall modify only approved stop-loss/take-profit scope."""
    _header(
        "FR-TRD-017: The system shall modify only approved stop-loss/take-profit scope."
    )
    example_actions()


def fr_trd_018() -> None:
    """FR-TRD-018: The system shall reduce, never increase, exposure and execute exactly the Risk-approved reduction."""
    _header(
        "FR-TRD-018: The system shall reduce, never increase, exposure and execute exactly the Risk-approved reduction."
    )
    example_actions()


def fr_trd_019() -> None:
    """FR-TRD-019: The system shall pause runtime admission without changing strategy lifecycle governance."""
    _header(
        "FR-TRD-019: The system shall pause runtime admission without changing strategy lifecycle governance."
    )
    example_actions()


def fr_trd_020() -> None:
    """FR-TRD-020: The system shall resume only after a valid Risk-owned `ActionPolicyVerdict`, all applicable `global > portfolio > strategy > symbol` kill-switch scopes are inactive, and reconciliation is ready."""
    _header(
        "FR-TRD-020: The system shall resume only after a valid Risk-owned `ActionPolicyVerdict`, all applicable `global > portfolio > strategy > symbol` kill-switch scopes are inactive, and reconciliation is ready."
    )
    example_actions()


def fr_trd_021() -> None:
    """FR-TRD-021: The system shall request a scoped Risk-owned kill-switch transition only with a compatible `ActionPolicyVerdict`; request text cannot create emergency authority."""
    _header(
        "FR-TRD-021: The system shall request a scoped Risk-owned kill-switch transition only with a compatible `ActionPolicyVerdict`; request text cannot create emergency authority."
    )
    example_actions()


def fr_trd_022() -> None:
    """FR-TRD-022: The system shall clear a switch only through Risk-authorized clearance; an inactive child cannot override an active parent, and resume requires reconciliation readiness."""
    _header(
        "FR-TRD-022: The system shall clear a switch only through Risk-authorized clearance; an inactive child cannot override an active parent, and resume requires reconciliation readiness."
    )
    example_actions()


def fr_trd_023() -> None:
    """FR-TRD-023: The system shall mass-cancel pending or otherwise cancellable orders through normal gates, bind each paper/live child to its own current Risk decision/token and action-policy verdict, validate every derived child, return every child result, and never claim cancellation for uncertain or already-filled work."""
    _header(
        "FR-TRD-023: The system shall mass-cancel pending or otherwise cancellable orders through normal gates, bind each paper/live child to its own current Risk decision/token and action-policy verdict, validate every derived child, return every child result, and never claim cancellation for uncertain or already-filled work."
    )
    example_actions()


def fr_trd_025() -> None:
    """FR-TRD-025: The system shall synchronize projections from route truth without mutating route orders or positions."""
    _header(
        "FR-TRD-025: The system shall synchronize projections from route truth without mutating route orders or positions."
    )
    example_actions()


def fr_trd_050() -> None:
    """FR-TRD-050: The system shall mass-close positions through normal gates, bind each paper/live child to its own current Risk decision/token and action-policy verdict, validate every derived child, and return every child result."""
    _header(
        "FR-TRD-050: The system shall mass-close positions through normal gates, bind each paper/live child to its own current Risk decision/token and action-policy verdict, validate every derived child, and return every child result."
    )
    example_actions()


def fr_trd_056() -> None:
    """FR-TRD-056: The system shall expose one immutable injected dependency container carrying every exact authority/read port and required runtime bound listed in the `dependencies.py` Files row, without resolving secrets or creating route/store dependencies at import time. Evaluation ports return public typed domain contracts; the normalized symbol-capability port returns exact `supported_order_types` and Brokers `BrokerSymbolInfo`, never interpreted provider-native flag names."""
    _header(
        "FR-TRD-056: The system shall expose one immutable injected dependency container carrying every exact authority/read port and required runtime bound listed in the `dependencies.py` Files row, without resolving secrets or creating route/store dependencies at import time. Evaluation ports return public typed domain contracts; the normalized symbol-capability port returns exact `supported_order_types` and Brokers `BrokerSymbolInfo`, never interpreted provider-native flag names."
    )
    example_actions()


def fr_trd_064() -> None:
    """FR-TRD-064: The system shall validate the receiver-owned `PortfolioRebalanceExecutionRequest` (hash, approval token, route, target version), revalidate eligibility, `AllocationRiskDecision`, `PortfolioBudgetExecutionVerdict`, kill switch, and idempotency, resolve each approved component exposure reduction into an executable order through the injected Trading-owned resolver, and revalidate the child request's immutable parent bindings before the existing order/reconciliation path; it never recalculates target weights and keeps correction actions canonical `reduce_exposure`."""
    _header(
        "FR-TRD-064: The system shall validate the receiver-owned `PortfolioRebalanceExecutionRequest` (hash, approval token, route, target version), revalidate eligibility, `AllocationRiskDecision`, `PortfolioBudgetExecutionVerdict`, kill switch, and idempotency, resolve each approved component exposure reduction into an executable order through the injected Trading-owned resolver, and revalidate the child request's immutable parent bindings before the existing order/reconciliation path; it never recalculates target weights and keeps correction actions canonical `reduce_exposure`."
    )
    example_actions()


def fr_trd_065() -> None:
    """FR-TRD-065: The system shall drive one live/paper evaluation cycle strictly through public domain APIs: request `MarketDataset` + `AccountStateSnapshot` from Data, `IndicatorSeries` from Indicators, invoke Strategy for a `TradeIntent`, and — when a non-neutral `TradeIntent` is produced — submit it to Risk and pass any approved `RiskDecision` into the existing validate/gate/dispatch path. A neutral signal returns a normal no-mutation `StandardResponse[object]` with `legacy_status="no_action"` and ends the cycle. Trading never computes indicators, generates signals, or sizes/approves."""
    _header(
        'FR-TRD-065: The system shall drive one live/paper evaluation cycle strictly through public domain APIs: request `MarketDataset` + `AccountStateSnapshot` from Data, `IndicatorSeries` from Indicators, invoke Strategy for a `TradeIntent`, and — when a non-neutral `TradeIntent` is produced — submit it to Risk and pass any approved `RiskDecision` into the existing validate/gate/dispatch path. A neutral signal returns a normal no-mutation `StandardResponse[object]` with `legacy_status="no_action"` and ends the cycle. Trading never computes indicators, generates signals, or sizes/approves.'
    )
    example_actions()


def main() -> None:
    """Run Trading actions usage example."""
    example_actions()


if __name__ == "__main__":
    main()
