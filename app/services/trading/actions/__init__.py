"""Canonical public Trading action API."""

from app.services.trading.actions.controls import (
    clear_kill_switch,
    pause_strategy,
    resume_strategy,
    sync_positions,
    trigger_kill_switch,
)
from app.services.trading.actions.dependencies import TradingDependencies
from app.services.trading.actions.emergency import (
    cancel_all_orders,
    close_all_positions,
)
from app.services.trading.actions.orders import cancel_order, modify_order, submit_order
from app.services.trading.actions.positions import (
    close_position,
    modify_position,
    reduce_exposure,
)
from app.services.trading.actions.rebalance import execute_portfolio_rebalance
from app.services.trading.actions.runtime import run_live_evaluation_cycle

__all__ = [
    "TradingDependencies",
    "cancel_all_orders",
    "cancel_order",
    "clear_kill_switch",
    "close_all_positions",
    "close_position",
    "execute_portfolio_rebalance",
    "modify_order",
    "modify_position",
    "pause_strategy",
    "reduce_exposure",
    "resume_strategy",
    "run_live_evaluation_cycle",
    "submit_order",
    "sync_positions",
    "trigger_kill_switch",
]
