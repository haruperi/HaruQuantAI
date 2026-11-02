"""Daily Open price strategy block (OpenD).

Description:
    Returns Daily Open price at the specified historical daily shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-OPEN-D: Historical Daily Open price retrieval.
Python API Usage:
    from app.extend.blocks.price.open_d import OpenD, open_d
    price = open_d(chart, shift=0)
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

open_d_spec = BlockSpec(
    id="price.open_d",
    version="1.0.0",
    name="Daily Open (OpenD)",
    description="Returns Daily Open price at specified historical daily shift",
    category="price",
    tags=("price", "mtf", "daily", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical daily bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Daily Open price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_d_spec)
def open_d(chart: Any, shift: int = 0) -> float:
    """Get Daily Open price at historical daily shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical daily bar offset (default 0).

    Returns:
        Daily Open price as float, or NaN.
    """
    logger.debug("FR-PRICE-OPEN-D: OpenD(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.daily_open(shift)
    return resolve_chart_field(chart, "daily_open", shift)


# Direct donor class alias matching SQ.Blocks.Price.OpenD
OpenD = open_d

__all__ = ["OpenD", "open_d", "open_d_spec"]
