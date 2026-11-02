"""Closed P/L in pips strategy block.

Description:
    Returns the directional price change in pips for the selected completed
    trade, or zero when no completed trade is found.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-CLOSED-PL-IN-PIPS: Closed trade realized P/L in pips.
Python API Usage:
    from app.extend.blocks.strategy_control.closed_pl_in_pips import (
        ClosedPLInPips,
        closed_pl_in_pips,
    )
    pips = await closed_pl_in_pips(context, scope, trades_ago=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from datetime import datetime

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.strategy_control.history import last_trade
from app.extend.functions.order_functions import (
    TradeFilter,
    pip_size,
)

logger = get_logger(__name__)

closed_pl_in_pips_spec = BlockSpec(
    id="strategy_control.closed_pl_in_pips",
    name="Closed Pl In Pips",
    description=(
        "Return directional weighted price change in pips, or zero when absent."
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


@block(closed_pl_in_pips_spec)
async def closed_pl_in_pips(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    trades_ago: int = 0,
    as_of: datetime | None = None,
) -> float:
    """Return directional weighted price change in pips, or zero when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        trades_ago: 0 for most recent completed trade, 1 for second most recent.
        as_of: Optional cutoff timestamp.

    Returns:
        Directional price change in pips as float, or 0.0.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-CLOSED-PL-IN-PIPS: closed_pl_in_pips trades_ago=%d",
        trades_ago,
    )
    trade = await last_trade(context, scope, trades_ago, as_of)
    if trade is None:
        return 0.0
    spec = await context.symbol.SymbolInfo(trade.symbol)
    size = pip_size(spec.price.pip_size, spec.price.tick_size)
    return float(trade.direction * (trade.price_close - trade.price_open) / size)


# Exact StrategyQuant donor snippet class alias
ClosedPLInPips = closed_pl_in_pips

__all__ = [
    "ClosedPLInPips",
    "closed_pl_in_pips",
    "closed_pl_in_pips_spec",
]
