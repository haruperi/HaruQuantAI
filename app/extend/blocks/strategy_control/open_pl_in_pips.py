"""Open P/L in pips strategy block.

Description:
    Sums directional pip changes across matching open positions, without
    volume weighting.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-OPEN-PL-IN-PIPS: Open positions pip change calculation.
Python API Usage:
    from app.extend.blocks.strategy_control.open_pl_in_pips import (
        OpenPLInPips,
        open_pl_in_pips,
    )
    pips = await open_pl_in_pips(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from collections.abc import Mapping

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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.blocks.strategy_control._common import valuation
from app.extend.functions.order_functions import (
    TradeFilter,
    pip_size,
)

logger = get_logger(__name__)

open_pl_in_pips_spec = BlockSpec(
    id="strategy_control.open_pl_in_pips",
    name="Open Pl In Pips",
    description=("Sum directional pip changes per position, without volume weighting."),
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


@block(open_pl_in_pips_spec)
async def open_pl_in_pips(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    prices: Mapping[str, float] | None = None,
) -> float:
    """Sum directional pip changes per position, without volume weighting.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        prices: Optional symbol-to-price mapping for custom mark valuation.

    Returns:
        Summed directional pip change across matching positions.
    """
    logger.debug("FR-STRATEGY-CONTROL-OPEN-PL-IN-PIPS: Evaluating open_pl_in_pips")
    total = 0.0
    for position in await matching_positions(context, scope):
        spec = await context.symbol.SymbolInfo(position.symbol)
        size = pip_size(spec.price.pip_size, spec.price.tick_size)
        direction = 1 if position.position_type == 0 else -1
        total += direction * (valuation(position, prices) - position.price_open) / size
    return float(total)


# Exact StrategyQuant donor snippet class alias
OpenPLInPips = open_pl_in_pips

__all__ = [
    "OpenPLInPips",
    "open_pl_in_pips",
    "open_pl_in_pips_spec",
]
