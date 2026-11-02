"""Closed P/L in money strategy block.

Description:
    Returns the net realized profit/loss in account currency for the selected
    completed trade, or zero when no completed trade is found.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-CLOSED-PL-IN-MONEY: Closed trade realized P/L in money.
Python API Usage:
    from app.extend.blocks.strategy_control.closed_pl_in_money import (
        ClosedPLInMoney,
        closed_pl_in_money,
    )
    pl = await closed_pl_in_money(context, scope, trades_ago=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from datetime import datetime

from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.strategy_control.history import last_trade
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

closed_pl_in_money_spec = BlockSpec(
    id="strategy_control.closed_pl_in_money",
    name="Closed Pl In Money",
    description=(
        "Return net P/L for the selected completed trade, or zero when absent."
    ),
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("as_of", PortType.ANY, required=False, default=None),
    ),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(closed_pl_in_money_spec)
async def closed_pl_in_money(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    trades_ago: int = 0,
    as_of: datetime | None = None,
) -> float:
    """Return net P/L for the selected completed trade, or zero when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        trades_ago: 0 for most recent completed trade, 1 for second most recent.
        as_of: Optional cutoff timestamp.

    Returns:
        Net realized profit/loss in account currency, or 0.0.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-CLOSED-PL-IN-MONEY: closed_pl_in_money trades_ago=%d",
        trades_ago,
    )
    trade = await last_trade(context, scope, trades_ago, as_of)
    return trade.net_profit if trade is not None else 0.0


# Exact StrategyQuant donor snippet class alias
ClosedPLInMoney = closed_pl_in_money

__all__ = [
    "ClosedPLInMoney",
    "closed_pl_in_money",
    "closed_pl_in_money_spec",
]
