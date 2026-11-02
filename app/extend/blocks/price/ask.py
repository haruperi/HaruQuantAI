"""Ask price strategy block.

Description:
    Returns the current or historical Ask quote price for the specified symbol
    or chart container.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-ASK: Historical Ask quote price retrieval.
Python API Usage:
    from app.extend.blocks.price.ask import Ask, ask
    val = ask(chart, shift=0)
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
from app.extend.blocks.price._common import resolve_chart_field

logger = get_logger(__name__)

ask_spec = BlockSpec(
    id="price.ask",
    version="1.0.0",
    name="Ask",
    description="Returns Ask price at specified historical shift",
    category="price",
    tags=("price", "quote", "ask"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart or QuotePrice container"),
        InputPort("shift", PortType.NUMBER, "Historical offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Ask price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(ask_spec)
def ask(chart: Any, shift: int = 0) -> float:
    """Get Ask price at historical shift.

    Args:
        chart: QuotePrice, BarPrice, series, or array.
        shift: Historical offset (default 0).

    Returns:
        Ask price as float, or NaN.
    """
    logger.debug("FR-PRICE-ASK: Ask(shift=%d)", shift)
    return resolve_chart_field(chart, "ask", shift)


# Direct donor class alias matching SQ.Blocks.Price.Ask
Ask = ask

__all__ = ["Ask", "ask", "ask_spec"]
