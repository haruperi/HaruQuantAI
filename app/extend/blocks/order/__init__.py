"""Order management building blocks, specifications, and execution facade.

Description:
    Exposes canonical strategy order execution building blocks matching StrategyQuant
    SQ.Blocks.Order donor classes (Close, Modify, Open), along with sizing, validity,
    ATM, and price level formula evaluators.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-ALL-PENDING: Cancel all matching pending orders.
    - FR-ORDER-CLOSE-ALL-POSITIONS: Close all matching open positions.
    - FR-ORDER-CLOSE-BEST: Close highest profit matching position.
    - FR-ORDER-CLOSE-PENDING: Cancel first matching pending order.
    - FR-ORDER-CLOSE-POSITION: Close first matching position with volume control.
    - FR-ORDER-CLOSE-WORST: Close lowest profit matching position.
    - FR-ORDER-SET-PROFIT-TARGET: Set or update order profit target.
    - FR-ORDER-SET-STOP-LOSS: Set or update order stop loss with tightening policy.
    - FR-ORDER-ENTER-AT-LIMIT: Open limit order with pending replacement.
    - FR-ORDER-ENTER-AT-MARKET: Open market order at current price.
    - FR-ORDER-ENTER-AT-STOP: Open stop order with pending replacement.
    - FR-ORDER-ENTER-REVERSE-AT-MARKET: Reverse position at market.
    - FR-ORDER-SIZING: Evaluate position sizing models.
    - FR-ORDER-FORMULAS: Evaluate price level formulas and offsets.
    - FR-ORDER-ATM: Partition trade volume across multi-bracket exits.
    - FR-ORDER-VALIDITY: Translate bar counts to timezone-aware expiration datetimes.
    - FR-ORDER-FACADE: Unified object interface for all order operations.
Python API Usage:
    from app.extend.blocks.order import Orders, enter_at_market, close_position
    orders = Orders(runtime)
    await orders.enter_at_market("EURUSD", 1, 0.1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.order._common import (
    cancel_orders,
    close_positions,
    matching_orders,
    matching_positions,
    net_profit,
    set_protection,
)
from app.extend.blocks.order.atm import (
    ATMBracket,
    ATMStrategy,
)
from app.extend.blocks.order.close import (
    close_all_pending_orders,
    close_all_pending_orders_spec,
    close_all_positions,
    close_all_positions_spec,
    close_best_position,
    close_best_position_spec,
    close_pending_order,
    close_pending_order_spec,
    close_position,
    close_position_spec,
    close_worst_position,
    close_worst_position_spec,
)
from app.extend.blocks.order.facade import Orders
from app.extend.blocks.order.formulas import (
    PriceFormulaMode,
    evaluate_price_level,
    price_offset_atr,
    price_offset_percent,
    price_offset_pips,
)
from app.extend.blocks.order.modify import (
    set_profit_target,
    set_profit_target_spec,
    set_stop_loss,
    set_stop_loss_spec,
)
from app.extend.blocks.order.open import (
    enter_at_limit,
    enter_at_limit_spec,
    enter_at_market,
    enter_at_market_spec,
    enter_at_stop,
    enter_at_stop_spec,
    enter_reverse_at_market,
    enter_reverse_at_market_spec,
    execute_entry,
)
from app.extend.blocks.order.runtime import (
    AccountSource,
    DealSource,
    OrderExecution,
    OrderSource,
    PositionSource,
    SymbolSource,
    TradingRuntime,
)
from app.extend.blocks.order.sizing import (
    SizingMethod,
    evaluate_sizing,
    fixed_lots,
    margin_percent,
    normalize_lots,
    risk_cash,
    risk_percent,
    volatility_risk,
)
from app.extend.blocks.order.types import (
    TradeFilter,
    aware_timestamp,
    bars_since,
    normalize_price,
    pip_size,
)
from app.extend.blocks.order.validity import (
    parse_timeframe_delta,
    schedule_bar_validity,
)

__all__ = [
    "ATMBracket",
    "ATMStrategy",
    "AccountSource",
    "DealSource",
    "OrderExecution",
    "OrderSource",
    "Orders",
    "PositionSource",
    "PriceFormulaMode",
    "SizingMethod",
    "SymbolSource",
    "TradeFilter",
    "TradingRuntime",
    "aware_timestamp",
    "bars_since",
    "cancel_orders",
    "close_all_pending_orders",
    "close_all_pending_orders_spec",
    "close_all_positions",
    "close_all_positions_spec",
    "close_best_position",
    "close_best_position_spec",
    "close_pending_order",
    "close_pending_order_spec",
    "close_position",
    "close_position_spec",
    "close_positions",
    "close_worst_position",
    "close_worst_position_spec",
    "enter_at_limit",
    "enter_at_limit_spec",
    "enter_at_market",
    "enter_at_market_spec",
    "enter_at_stop",
    "enter_at_stop_spec",
    "enter_reverse_at_market",
    "enter_reverse_at_market_spec",
    "evaluate_price_level",
    "evaluate_sizing",
    "execute_entry",
    "fixed_lots",
    "margin_percent",
    "matching_orders",
    "matching_positions",
    "net_profit",
    "normalize_lots",
    "normalize_price",
    "parse_timeframe_delta",
    "pip_size",
    "price_offset_atr",
    "price_offset_percent",
    "price_offset_pips",
    "risk_cash",
    "risk_percent",
    "schedule_bar_validity",
    "set_profit_target",
    "set_profit_target_spec",
    "set_protection",
    "set_stop_loss",
    "set_stop_loss_spec",
    "volatility_risk",
]
