"""Open P/L in money strategy block.

Description:
    Sums net open profit/loss across matching positions in account currency,
    optionally valuing at explicit strategy decision prices.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-OPEN-PL-IN-MONEY: Open positions net profit calculation.
Python API Usage:
    from app.extend.blocks.strategy_control.open_pl_in_money import (
        OpenPLInMoney,
        open_pl_in_money,
    )
    pl = await open_pl_in_money(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from collections.abc import Mapping

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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.blocks.strategy_control._common import valuation
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

open_pl_in_money_spec = BlockSpec(
    id="strategy_control.open_pl_in_money",
    name="Open Pl In Money",
    description=(
        "Sum net open P/L, optionally valuing at explicit strategy decision prices."
    ),
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("prices", PortType.ANY, required=False, default=None),
    ),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(open_pl_in_money_spec)
async def open_pl_in_money(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    prices: Mapping[str, float] | None = None,
) -> float:
    """Sum net open P/L, optionally valuing at explicit strategy decision prices.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        prices: Optional symbol-to-price mapping for custom mark valuation.

    Returns:
        Total net open profit/loss in money as float.
    """
    logger.debug("FR-STRATEGY-CONTROL-OPEN-PL-IN-MONEY: Evaluating open_pl_in_money")
    total = 0.0
    for position in await matching_positions(context, scope):
        gross = position.profit
        if prices is not None:
            gross = float(
                await context.account.OrderProfitCheck(
                    position.symbol,
                    position.position_type,
                    position.volume,
                    position.price_open,
                    valuation(position, prices),
                )
            )
        total += gross + position.swap + position.commission
    return total


# Exact StrategyQuant donor snippet class alias
OpenPLInMoney = open_pl_in_money

__all__ = [
    "OpenPLInMoney",
    "open_pl_in_money",
    "open_pl_in_money_spec",
]
