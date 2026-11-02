"""Monthly Close price strategy block (CloseM).

Description:
    Returns Monthly Close price at the specified historical monthly shift,
    evaluating against MTFPrice or chart container contexts.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-CLOSE-M: Historical Monthly Close price retrieval.
Python API Usage:
    from app.extend.blocks.price.close_m import CloseM, close_m
    price = close_m(chart, shift=0)
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

close_m_spec = BlockSpec(
    id="price.close_m",
    version="1.0.0",
    name="Monthly Close (CloseM)",
    description="Returns Monthly Close price at specified historical monthly shift",
    category="price",
    tags=("price", "mtf", "monthly", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical monthly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Monthly Close price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(close_m_spec)
def close_m(chart: Any, shift: int = 0) -> float:
    """Get Monthly Close price at historical monthly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical monthly bar offset (default 0).

    Returns:
        Monthly Close price as float, or NaN.
    """
    logger.debug("FR-PRICE-CLOSE-M: CloseM(shift=%d)", shift)
    if isinstance(chart, MTFPrice):
        return chart.monthly_close(shift)
    return resolve_chart_field(chart, "monthly_close", shift)


# Direct donor class alias matching SQ.Blocks.Price.CloseM
CloseM = close_m

__all__ = ["CloseM", "close_m", "close_m_spec"]
