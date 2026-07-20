"""Trading action primitives package.

This package hosts the platform-independent shared trading action surface:
local validation, orders, positions, controls, and emergency actions. Every
action packages a :class:`~app.services.trading.contracts.TradingRequestEnvelope`
through local schema validation and, for ``route="live"``, an injected gate
pipeline seam that is wired by the future ``gates/pipeline.py`` unit. No file
in this package imports a provider broker SDK directly.
"""

from __future__ import annotations

from app.services.trading.actions._common import (
    LiveGatePipeline,
    TradingActionDependencies,
)
from app.services.trading.actions.controls import (
    pause_strategy,
    resume_strategy,
    shutdown,
    sync_positions,
    trigger_global_kill_switch,
    trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
)
from app.services.trading.actions.emergency import (
    cancel_all_orders,
    close_all_positions,
    flatten_account,
    flatten_strategy,
    flatten_symbol,
)
from app.services.trading.actions.orders import (
    buy,
    buy_limit,
    buy_stop,
    order_delete,
    order_modify,
    sell,
    sell_limit,
    sell_stop,
    submit_oco_group,
)
from app.services.trading.actions.positions import (
    position_close,
    position_modify,
    position_open,
    reduce_exposure,
)
from app.services.trading.actions.validation import (
    AccountMarginContext,
    ConversionRateEvidence,
    DailyRailState,
    DefenseInDepthRailLimits,
    LocateSnapshot,
    MarketSessionEvidence,
    OrderIntent,
    OrderSide,
    OrderType,
    OrderValidationContext,
    OrderValidationResult,
    SymbolTradingConstraints,
    validate_order_request,
)

__all__ = [
    "AccountMarginContext",
    "ConversionRateEvidence",
    "DailyRailState",
    "DefenseInDepthRailLimits",
    "LiveGatePipeline",
    "LocateSnapshot",
    "MarketSessionEvidence",
    "OrderIntent",
    "OrderSide",
    "OrderType",
    "OrderValidationContext",
    "OrderValidationResult",
    "SymbolTradingConstraints",
    "TradingActionDependencies",
    "buy",
    "buy_limit",
    "buy_stop",
    "cancel_all_orders",
    "close_all_positions",
    "flatten_account",
    "flatten_strategy",
    "flatten_symbol",
    "order_delete",
    "order_modify",
    "pause_strategy",
    "position_close",
    "position_modify",
    "position_open",
    "reduce_exposure",
    "resume_strategy",
    "sell",
    "sell_limit",
    "sell_stop",
    "shutdown",
    "submit_oco_group",
    "sync_positions",
    "trigger_global_kill_switch",
    "trigger_strategy_kill_switch",
    "trigger_symbol_kill_switch",
    "validate_order_request",
]
