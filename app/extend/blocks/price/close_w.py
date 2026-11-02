"""Weekly Close price strategy block (CloseW).

Description:
    Returns Weekly Close price at the specified historical weekly shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-CLOSE-W: Historical Weekly Close price retrieval.
Python API Usage:
    from app.extend.blocks.price.close_w import CloseW, close_w
    price = close_w(chart, shift=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.price._common import MTFPrice, resolve_chart_field

logger = get_logger(__name__)

close_w_spec = BlockSpec(
    id="price.close_w",
    version="1.0.0",
    name="Weekly Close (CloseW)",
    description="Returns Weekly Close price at specified historical weekly shift",
    category="price",
    tags=("price", "mtf", "weekly", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical weekly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Weekly Close price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(close_w_spec)
def close_w(chart: Any, shift: int = 0) -> float:
    """Get Weekly Close price at historical weekly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical weekly bar offset (default 0).

    Returns:
        Weekly Close price as float, or NaN.
    """
    logger.debug("FR-PRICE-CLOSE-W: CloseW(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.weekly_close(shift)
    return resolve_chart_field(chart, "weekly_close", shift)


# Direct donor class alias matching SQ.Blocks.Price.CloseW
CloseW = close_w

__all__ = ["CloseW", "close_w", "close_w_spec"]
