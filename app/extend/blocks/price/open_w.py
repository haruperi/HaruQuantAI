"""Weekly Open price strategy block (OpenW).

Description:
    Returns Weekly Open price at the specified historical weekly shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-OPEN-W: Historical Weekly Open price retrieval.
Python API Usage:
    from app.extend.blocks.price.open_w import OpenW, open_w
    price = open_w(chart, shift=0)
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

open_w_spec = BlockSpec(
    id="price.open_w",
    version="1.0.0",
    name="Weekly Open (OpenW)",
    description="Returns Weekly Open price at specified historical weekly shift",
    category="price",
    tags=("price", "mtf", "weekly", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical weekly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Weekly Open price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_w_spec)
def open_w(chart: Any, shift: int = 0) -> float:
    """Get Weekly Open price at historical weekly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical weekly bar offset (default 0).

    Returns:
        Weekly Open price as float, or NaN.
    """
    logger.debug("FR-PRICE-OPEN-W: OpenW(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.weekly_open(shift)
    return resolve_chart_field(chart, "weekly_open", shift)


# Direct donor class alias matching SQ.Blocks.Price.OpenW
OpenW = open_w

__all__ = ["OpenW", "open_w", "open_w_spec"]
