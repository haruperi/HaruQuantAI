"""Weekly High price strategy block (HighW).

Description:
    Returns Weekly High price at the specified historical weekly shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-HIGH-W: Historical Weekly High price retrieval.
Python API Usage:
    from app.extend.blocks.price.high_w import HighW, high_w
    price = high_w(chart, shift=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.price._common import MTFPrice, resolve_chart_field

logger = get_logger(__name__)

high_w_spec = BlockSpec(
    id="price.high_w",
    version="1.0.0",
    name="Weekly High (HighW)",
    description="Returns Weekly High price at specified historical weekly shift",
    category="price",
    tags=("price", "mtf", "weekly", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical weekly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Weekly High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(high_w_spec)
def high_w(chart: Any, shift: int = 0) -> float:
    """Get Weekly High price at historical weekly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical weekly bar offset (default 0).

    Returns:
        Weekly High price as float, or NaN.
    """
    logger.debug("FR-PRICE-HIGH-W: HighW(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.weekly_high(shift)
    return resolve_chart_field(chart, "weekly_high", shift)


# Direct donor class alias matching SQ.Blocks.Price.HighW
HighW = high_w

__all__ = ["HighW", "high_w", "high_w_spec"]
