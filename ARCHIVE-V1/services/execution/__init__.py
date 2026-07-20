"""Execution service tool exports.

Purpose:
    Expose deterministic, agent-facing execution tools from focused execution
    modules without placing implementation logic in this package initializer.

Classes and functions:
    Broker connectivity tools: Functions. Broker/account/symbol/quote/session
        checks from broker_connectivity.py.
    Execution readiness tools: Functions. Order, environment, sizing, pricing,
        cost, slippage, and plan checks from readiness_tools.py.
    Paper trading tools: Functions. Paper strategy/order/fill/report requests
        from paper_trading_tools.py.
    Live execution tools: Functions. Fail-closed live execution requests from
        live_execution_tools.py.
    Kill switch tools: Functions. Fail-closed safety-control requests from
        kill_switch_tools.py.
"""

from __future__ import annotations

from app.services.utils.standard import standardize_domain_exports

# broker_connectivity.py tools
from .broker_connectivity import (
    check_broker_connection,
    check_free_margin,
    check_lot_step,
    check_market_open,
    check_max_lot,
    check_min_lot,
    check_stop_distance,
    get_account_info,
    get_broker_time,
    get_current_bid_ask,
    get_current_spread,
    get_symbol_info,
    get_trade_permissions,
)

# kill_switch_tools.py tools
from .kill_switch_tools import (
    cancel_all_orders,
    check_kill_switch_conditions,
    clear_kill_switch_after_approval,
    close_all_positions,
    disable_new_orders,
    record_kill_switch_event,
    require_reenable_approval,
    trigger_global_kill_switch,
    trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
)

# live_execution_tools.py tools
from .live_execution_tools import (
    build_live_execution_report,
    cancel_live_order,
    close_live_position,
    modify_live_order,
    pause_live_strategy,
    reconcile_broker_state,
    reduce_live_exposure,
    resume_live_strategy,
    submit_live_order,
    sync_live_positions,
)

# paper_trading_tools.py tools
from .paper_trading_tools import (
    build_paper_trading_report,
    calculate_paper_slippage,
    close_paper_position,
    compare_paper_vs_backtest,
    modify_paper_order,
    record_paper_fill,
    start_paper_strategy,
    stop_paper_strategy,
    submit_paper_order,
)

# readiness_tools.py tools
from .readiness_tools import (
    build_execution_plan,
    estimate_slippage,
    estimate_transaction_cost,
    run_execution_readiness_check,
    validate_broker_symbol_mapping,
    validate_execution_environment,
    validate_order_price,
    validate_order_request,
    validate_order_size,
    validate_stop_loss_take_profit,
    validate_strategy_runtime_config,
)
from .trading import Trade, TradeResult

__all__ = [
    "build_execution_plan",
    "build_live_execution_report",
    "build_paper_trading_report",
    "calculate_paper_slippage",
    "cancel_all_orders",
    "cancel_live_order",
    "check_broker_connection",
    "check_free_margin",
    "check_kill_switch_conditions",
    "check_lot_step",
    "check_market_open",
    "check_max_lot",
    "check_min_lot",
    "check_stop_distance",
    "clear_kill_switch_after_approval",
    "close_all_positions",
    "close_live_position",
    "close_paper_position",
    "compare_paper_vs_backtest",
    "disable_new_orders",
    "estimate_slippage",
    "estimate_transaction_cost",
    "get_account_info",
    "get_broker_time",
    "get_current_bid_ask",
    "get_current_spread",
    "get_symbol_info",
    "get_trade_permissions",
    "modify_live_order",
    "modify_paper_order",
    "pause_live_strategy",
    "reconcile_broker_state",
    "record_kill_switch_event",
    "record_paper_fill",
    "reduce_live_exposure",
    "require_reenable_approval",
    "resume_live_strategy",
    "run_execution_readiness_check",
    "start_paper_strategy",
    "stop_paper_strategy",
    "submit_live_order",
    "submit_paper_order",
    "sync_live_positions",
    "trigger_global_kill_switch",
    "trigger_strategy_kill_switch",
    "trigger_symbol_kill_switch",
    "validate_broker_symbol_mapping",
    "validate_execution_environment",
    "validate_order_price",
    "validate_order_request",
    "validate_order_size",
    "validate_stop_loss_take_profit",
    "validate_strategy_runtime_config",
]


standardize_domain_exports(globals(), __all__, tool_category="execution")
