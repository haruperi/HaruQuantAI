"""Strategy control and account state blocks package.

Description:
    Exports StrategyQuant-faithful strategy control blocks, exact donor class
    aliases, the unified StrategyControl facade, and history reconstruction
    helpers.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-EXPORTS: Public package exports for strategy control blocks.
Python API Usage:
    from app.extend.blocks.strategy_control import (
        AccountBalance,
        MarketPosition,
        StrategyControl,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.strategy_control._common import (
    position_value,
    valuation,
)
from app.extend.blocks.strategy_control.account_balance import (
    AccountBalance,
    account_balance,
)
from app.extend.blocks.strategy_control.account_equity import (
    AccountEquity,
    account_equity,
)
from app.extend.blocks.strategy_control.bars_since_order_closed import (
    BarsSinceOrderClosed,
    bars_since_order_closed,
)
from app.extend.blocks.strategy_control.bars_since_order_open import (
    BarsSinceOrderOpen,
    bars_since_order_open,
)
from app.extend.blocks.strategy_control.closed_pl_in_money import (
    ClosedPLInMoney,
    closed_pl_in_money,
)
from app.extend.blocks.strategy_control.closed_pl_in_pips import (
    ClosedPLInPips,
    closed_pl_in_pips,
)
from app.extend.blocks.strategy_control.facade import StrategyControl
from app.extend.blocks.strategy_control.history import (
    ClosedTrade,
    closed_trades,
    last_trade,
)
from app.extend.blocks.strategy_control.last_order_was import (
    LastOrderWas,
    last_order_was,
)
from app.extend.blocks.strategy_control.last_order_was_not import (
    LastOrderWasNot,
    last_order_was_not,
)
from app.extend.blocks.strategy_control.market_position import (
    MarketPosition,
    market_position,
)
from app.extend.blocks.strategy_control.market_position_is_flat import (
    MarketPositionIsFlat,
    market_position_is_flat,
)
from app.extend.blocks.strategy_control.market_position_is_long import (
    MarketPositionIsLong,
    market_position_is_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_long import (
    MarketPositionIsNotLong,
    market_position_is_not_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_short import (
    MarketPositionIsNotShort,
    market_position_is_not_short,
)
from app.extend.blocks.strategy_control.market_position_is_short import (
    MarketPositionIsShort,
    market_position_is_short,
)
from app.extend.blocks.strategy_control.market_position_size import (
    MarketPositionSize,
    market_position_size,
)
from app.extend.blocks.strategy_control.market_positions_count import (
    MarketPositionsCount,
    market_positions_count,
)
from app.extend.blocks.strategy_control.no_trade_recently_closed import (
    NoTradeRecentlyClosed,
    no_trade_recently_closed,
)
from app.extend.blocks.strategy_control.open_pl_in_money import (
    OpenPLInMoney,
    open_pl_in_money,
)
from app.extend.blocks.strategy_control.open_pl_in_pips import (
    OpenPLInPips,
    open_pl_in_pips,
)
from app.extend.blocks.strategy_control.order_open_price import (
    OrderOpenPrice,
    order_open_price,
)
from app.extend.blocks.strategy_control.order_pt import (
    OrderPT,
    order_pt,
)
from app.extend.blocks.strategy_control.order_sl import (
    OrderSL,
    order_sl,
)
from app.extend.blocks.strategy_control.pending_order_doesnt_exist import (
    PendingOrderDoesntExist,
    pending_order_doesnt_exist,
)
from app.extend.blocks.strategy_control.pending_order_exists import (
    PendingOrderExists,
    pending_order_exists,
)
from app.extend.blocks.strategy_control.trade_recently_closed import (
    TradeRecentlyClosed,
    trade_recently_closed,
)

__all__ = [
    "AccountBalance",
    "AccountEquity",
    "BarsSinceOrderClosed",
    "BarsSinceOrderOpen",
    "ClosedPLInMoney",
    "ClosedPLInPips",
    "ClosedTrade",
    "LastOrderWas",
    "LastOrderWasNot",
    "MarketPosition",
    "MarketPositionIsFlat",
    "MarketPositionIsLong",
    "MarketPositionIsNotLong",
    "MarketPositionIsNotShort",
    "MarketPositionIsShort",
    "MarketPositionSize",
    "MarketPositionsCount",
    "NoTradeRecentlyClosed",
    "OpenPLInMoney",
    "OpenPLInPips",
    "OrderOpenPrice",
    "OrderPT",
    "OrderSL",
    "PendingOrderDoesntExist",
    "PendingOrderExists",
    "StrategyControl",
    "TradeRecentlyClosed",
    "account_balance",
    "account_equity",
    "bars_since_order_closed",
    "bars_since_order_open",
    "closed_pl_in_money",
    "closed_pl_in_pips",
    "closed_trades",
    "last_order_was",
    "last_order_was_not",
    "last_trade",
    "market_position",
    "market_position_is_flat",
    "market_position_is_long",
    "market_position_is_not_long",
    "market_position_is_not_short",
    "market_position_is_short",
    "market_position_size",
    "market_positions_count",
    "no_trade_recently_closed",
    "open_pl_in_money",
    "open_pl_in_pips",
    "order_open_price",
    "order_pt",
    "order_sl",
    "pending_order_doesnt_exist",
    "pending_order_exists",
    "position_value",
    "trade_recently_closed",
    "valuation",
]
