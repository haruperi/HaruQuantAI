"""Daily Close price strategy block (CloseD).

Description:
    Returns Daily Close price at the specified historical daily shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-CLOSE-D: Historical Daily Close price retrieval.
Python API Usage:
    from app.extend.blocks.price.close_d import CloseD, close_d
    price = close_d(chart, shift=0)
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

close_d_spec = BlockSpec(
    id="price.close_d",
    version="1.0.0",
    name="Daily Close (CloseD)",
    description="Returns Daily Close price at specified historical daily shift",
    category="price",
    tags=("price", "mtf", "daily", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical daily bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Daily Close price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(close_d_spec)
def close_d(chart: Any, shift: int = 0) -> float:
    """Get Daily Close price at historical daily shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical daily bar offset (default 0).

    Returns:
        Daily Close price as float, or NaN.
    """
    logger.debug("FR-PRICE-CLOSE-D: CloseD(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.daily_close(shift)
    return resolve_chart_field(chart, "daily_close", shift)


# Direct donor class alias matching SQ.Blocks.Price.CloseD
CloseD = close_d

__all__ = ["CloseD", "close_d", "close_d_spec"]
