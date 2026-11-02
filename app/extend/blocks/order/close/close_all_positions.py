"""Close All Positions strategy block.

Description:
    Closes all open positions matching the specified trade filter criteria
    (symbol, direction, magic number, comment), stopping at the first incomplete
    close, matching the StrategyQuant CloseAllPositions snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-ALL-POSITIONS: Close all matching positions under operation lock.
Python API Usage:
    from app.extend.blocks.order.close import close_all_positions
    results = await close_all_positions(runtime, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
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
    close_positions,
    matching_positions,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

close_all_positions_spec = BlockSpec(
    id="order.close_all_positions",
    name="Close All Positions",
    description="Close matching positions, stopping at the first incomplete close.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_all_positions_spec)
async def close_all_positions(
    context: TradingRuntime, scope: TradeFilter
) -> list[TradeResult]:
    """Close matching positions, stopping at the first incomplete close."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        logger.debug(
            "FR-ORDER-CLOSE-ALL-POSITIONS: Closing %d matching positions for scope=%s",
            len(positions),
            scope,
        )
        return await close_positions(context, positions)


__all__ = ["close_all_positions", "close_all_positions_spec"]
