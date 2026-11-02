"""Monthly Open price strategy block (OpenM).

Description:
    Returns Monthly Open price at the specified historical monthly shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-OPEN-M: Historical Monthly Open price retrieval.
Python API Usage:
    from app.extend.blocks.price.open_m import OpenM, open_m
    price = open_m(chart, shift=0)
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

open_m_spec = BlockSpec(
    id="price.open_m",
    version="1.0.0",
    name="Monthly Open (OpenM)",
    description="Returns Monthly Open price at specified historical monthly shift",
    category="price",
    tags=("price", "mtf", "monthly", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical monthly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Monthly Open price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_m_spec)
def open_m(chart: Any, shift: int = 0) -> float:
    """Get Monthly Open price at historical monthly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical monthly bar offset (default 0).

    Returns:
        Monthly Open price as float, or NaN.
    """
    logger.debug("FR-PRICE-OPEN-M: OpenM(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.monthly_open(shift)
    return resolve_chart_field(chart, "monthly_open", shift)


# Direct donor class alias matching SQ.Blocks.Price.OpenM
OpenM = open_m

__all__ = ["OpenM", "open_m", "open_m_spec"]
