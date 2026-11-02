"""Consolidated facade for strategy control and account state blocks.

Description:
    Provides an object-oriented and namespace-bound API facade over discrete
    StrategyQuant-faithful strategy control building blocks for account info,
    open position queries, closed trade history, and pending order inspection.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-FACADE: Unified object interface for all strategy
      control queries.
Python API Usage:
    from app.extend.blocks.strategy_control import StrategyControl
    ctrl = StrategyControl(runtime)
    balance = await ctrl.account_balance()
    pos = await ctrl.market_position(scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.strategy_control.account_balance import (
    account_balance,
)
from app.extend.blocks.strategy_control.account_equity import (
    account_equity,
)
from app.extend.blocks.strategy_control.bars_since_order_closed import (
    bars_since_order_closed,
)
from app.extend.blocks.strategy_control.bars_since_order_open import (
    bars_since_order_open,
)
from app.extend.blocks.strategy_control.closed_pl_in_money import (
    closed_pl_in_money,
)
from app.extend.blocks.strategy_control.closed_pl_in_pips import (
    closed_pl_in_pips,
)
from app.extend.blocks.strategy_control.last_order_was import (
    last_order_was,
)
from app.extend.blocks.strategy_control.last_order_was_not import (
    last_order_was_not,
)
from app.extend.blocks.strategy_control.market_position import (
    market_position,
)
from app.extend.blocks.strategy_control.market_position_is_flat import (
    market_position_is_flat,
)
from app.extend.blocks.strategy_control.market_position_is_long import (
    market_position_is_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_long import (
    market_position_is_not_long,
)
from app.extend.blocks.strategy_control.market_position_is_not_short import (
    market_position_is_not_short,
)
from app.extend.blocks.strategy_control.market_position_is_short import (
    market_position_is_short,
)
from app.extend.blocks.strategy_control.market_position_size import (
    market_position_size,
)
from app.extend.blocks.strategy_control.market_positions_count import (
    market_positions_count,
)
from app.extend.blocks.strategy_control.no_trade_recently_closed import (
    no_trade_recently_closed,
)
from app.extend.blocks.strategy_control.open_pl_in_money import (
    open_pl_in_money,
)
from app.extend.blocks.strategy_control.open_pl_in_pips import (
    open_pl_in_pips,
)
from app.extend.blocks.strategy_control.order_open_price import (
    order_open_price,
)
from app.extend.blocks.strategy_control.order_pt import (
    order_pt,
)
from app.extend.blocks.strategy_control.order_sl import (
    order_sl,
)
from app.extend.blocks.strategy_control.pending_order_doesnt_exist import (
    pending_order_doesnt_exist,
)
from app.extend.blocks.strategy_control.pending_order_exists import (
    pending_order_exists,
)
from app.extend.blocks.strategy_control.trade_recently_closed import (
    trade_recently_closed,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)


class StrategyControl:
    """Consolidated facade for strategy control and account state blocks."""

    def __init__(self, context: TradingRuntime | None = None) -> None:
        """Initialize StrategyControl facade with an optional default context."""
        self._context = context
        logger.debug(
            "FR-STRATEGY-CONTROL-FACADE: Initialized StrategyControl with context=%s",
            context,
        )

    def _resolve_context(self, context: TradingRuntime | None) -> TradingRuntime:
        ctx = context if context is not None else self._context
        if ctx is None:
            raise ValueError(
                "A TradingRuntime context must be provided at init or call."
            )
        return ctx

    async def account_balance(self, *, context: TradingRuntime | None = None) -> float:
        """Return account balance in account currency."""
        ctx = self._resolve_context(context)
        return await account_balance(ctx)

    async def account_equity(self, *, context: TradingRuntime | None = None) -> float:
        """Return account equity in account currency."""
        ctx = self._resolve_context(context)
        return await account_equity(ctx)

    async def bars_since_order_closed(
        self,
        scope: TradeFilter,
        bar_times: Sequence[datetime],
        *,
        as_of: datetime,
        context: TradingRuntime | None = None,
    ) -> int:
        """Count chart bar starts since latest matching completion, or -1 if absent."""
        ctx = self._resolve_context(context)
        return await bars_since_order_closed(ctx, scope, bar_times, as_of=as_of)

    async def bars_since_order_open(
        self,
        scope: TradeFilter,
        bar_times: Sequence[datetime],
        *,
        as_of: datetime,
        context: TradingRuntime | None = None,
    ) -> int:
        """Count bar starts since first matching entry; return -1 when absent."""
        ctx = self._resolve_context(context)
        return await bars_since_order_open(ctx, scope, bar_times, as_of=as_of)

    async def closed_pl_in_money(
        self,
        scope: TradeFilter,
        *,
        trades_ago: int = 0,
        as_of: datetime | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Return net P/L for the selected completed trade, or zero when absent."""
        ctx = self._resolve_context(context)
        return await closed_pl_in_money(ctx, scope, trades_ago=trades_ago, as_of=as_of)

    async def closed_pl_in_pips(
        self,
        scope: TradeFilter,
        *,
        trades_ago: int = 0,
        as_of: datetime | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Return directional weighted price change in pips, or zero when absent."""
        ctx = self._resolve_context(context)
        return await closed_pl_in_pips(ctx, scope, trades_ago=trades_ago, as_of=as_of)

    async def last_order_was(
        self,
        scope: TradeFilter,
        direction: int,
        *,
        as_of: datetime | None = None,
        context: TradingRuntime | None = None,
    ) -> bool:
        """Test last completed entry direction; pending cancellations are excluded."""
        ctx = self._resolve_context(context)
        return await last_order_was(ctx, scope, direction, as_of=as_of)

    async def last_order_was_not(
        self,
        scope: TradeFilter,
        direction: int,
        *,
        as_of: datetime | None = None,
        context: TradingRuntime | None = None,
    ) -> bool:
        """Test opposite last entry direction; false when no completed trade exists."""
        ctx = self._resolve_context(context)
        return await last_order_was_not(ctx, scope, direction, as_of=as_of)

    async def market_position(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> int:
        """Return first matching direction: 1 long, -1 short, or 0 flat."""
        ctx = self._resolve_context(context)
        return await market_position(ctx, scope)

    async def market_position_is_flat(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether no matching market position exists."""
        ctx = self._resolve_context(context)
        return await market_position_is_flat(ctx, scope)

    async def market_position_is_long(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether any matching position is long, including hedged accounts."""
        ctx = self._resolve_context(context)
        return await market_position_is_long(ctx, scope)

    async def market_position_is_not_long(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether no matching long position exists."""
        ctx = self._resolve_context(context)
        return await market_position_is_not_long(ctx, scope)

    async def market_position_is_not_short(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether no matching short position exists."""
        ctx = self._resolve_context(context)
        return await market_position_is_not_short(ctx, scope)

    async def market_position_is_short(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether any matching position is short, including hedged accounts."""
        ctx = self._resolve_context(context)
        return await market_position_is_short(ctx, scope)

    async def market_position_size(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> float:
        """Sum matching position volumes without netting opposing directions."""
        ctx = self._resolve_context(context)
        return await market_position_size(ctx, scope)

    async def market_positions_count(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> int:
        """Count matching market positions, excluding pending orders."""
        ctx = self._resolve_context(context)
        return await market_positions_count(ctx, scope)

    async def no_trade_recently_closed(
        self,
        scope: TradeFilter,
        *,
        as_of: datetime,
        bar_start: datetime | None = None,
        check_this_bar: bool = True,
        check_this_minute: bool = True,
        context: TradingRuntime | None = None,
    ) -> bool:
        """Return the complement of the stable recent-completion predicate."""
        ctx = self._resolve_context(context)
        return await no_trade_recently_closed(
            ctx,
            scope,
            as_of=as_of,
            bar_start=bar_start,
            check_this_bar=check_this_bar,
            check_this_minute=check_this_minute,
        )

    async def open_pl_in_money(
        self,
        scope: TradeFilter,
        *,
        prices: Mapping[str, float] | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Sum net open P/L, optionally valuing at explicit strategy decision prices."""
        ctx = self._resolve_context(context)
        return await open_pl_in_money(ctx, scope, prices=prices)

    async def open_pl_in_pips(
        self,
        scope: TradeFilter,
        *,
        prices: Mapping[str, float] | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Sum directional pip changes per position, without volume weighting."""
        ctx = self._resolve_context(context)
        return await open_pl_in_pips(ctx, scope, prices=prices)

    async def order_open_price(
        self,
        scope: TradeFilter,
        *,
        pending: bool | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Return the first matching live entry price, or -1 when absent."""
        ctx = self._resolve_context(context)
        return await order_open_price(ctx, scope, pending=pending)

    async def order_pt(
        self,
        scope: TradeFilter,
        *,
        pending: bool | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Return the first matching live profit target, or -1 when absent."""
        ctx = self._resolve_context(context)
        return await order_pt(ctx, scope, pending=pending)

    async def order_sl(
        self,
        scope: TradeFilter,
        *,
        pending: bool | None = None,
        context: TradingRuntime | None = None,
    ) -> float:
        """Return the first matching live stop loss, or -1 when absent."""
        ctx = self._resolve_context(context)
        return await order_sl(ctx, scope, pending=pending)

    async def pending_order_doesnt_exist(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether no matching pending order exists."""
        ctx = self._resolve_context(context)
        return await pending_order_doesnt_exist(ctx, scope)

    async def pending_order_exists(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> bool:
        """Return whether any matching pending order exists."""
        ctx = self._resolve_context(context)
        return await pending_order_exists(ctx, scope)

    async def trade_recently_closed(
        self,
        scope: TradeFilter,
        *,
        as_of: datetime,
        bar_start: datetime | None = None,
        check_this_bar: bool = True,
        check_this_minute: bool = True,
        context: TradingRuntime | None = None,
    ) -> bool:
        """Test a recent completion without consuming the matching event."""
        ctx = self._resolve_context(context)
        return await trade_recently_closed(
            ctx,
            scope,
            as_of=as_of,
            bar_start=bar_start,
            check_this_bar=check_this_bar,
            check_this_minute=check_this_minute,
        )


__all__ = ["StrategyControl"]
