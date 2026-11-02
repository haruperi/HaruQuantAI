"""Daily Low price strategy block (LowD).

Description:
    Returns Daily Low price at the specified historical daily shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-LOW-D: Historical Daily Low price retrieval.
Python API Usage:
    from app.extend.blocks.price.low_d import LowD, low_d
    price = low_d(chart, shift=0)
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

low_d_spec = BlockSpec(
    id="price.low_d",
    version="1.0.0",
    name="Daily Low (LowD)",
    description="Returns Daily Low price at specified historical daily shift",
    category="price",
    tags=("price", "mtf", "daily", "low"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical daily bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Daily Low price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(low_d_spec)
def low_d(chart: Any, shift: int = 0) -> float:
    """Get Daily Low price at historical daily shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical daily bar offset (default 0).

    Returns:
        Daily Low price as float, or NaN.
    """
    logger.debug("FR-PRICE-LOW-D: LowD(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.daily_low(shift)
    return resolve_chart_field(chart, "daily_low", shift)


# Direct donor class alias matching SQ.Blocks.Price.LowD
LowD = low_d

__all__ = ["LowD", "low_d", "low_d_spec"]
