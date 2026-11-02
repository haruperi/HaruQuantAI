"""Bar Open price strategy block.

Description:
    Returns bar Open price at the specified historical shift, evaluating
    against BarPrice containers, series, or raw price arrays.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-OPEN: Historical bar Open price retrieval.
Python API Usage:
    from app.extend.blocks.price.open import Open, bar_open
    price = bar_open(chart, shift=0)
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

open_spec = BlockSpec(
    id="price.open",
    version="1.0.0",
    name="Open",
    description="Returns bar Open price at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Open price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_spec)
def bar_open(chart: Any, shift: int = 0) -> float:
    """Get bar Open price at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        Open price as float, or NaN.
    """
    logger.debug("FR-PRICE-OPEN: Open(shift=%d)", shift)
    return resolve_chart_field(chart, "open", shift)


open_price = bar_open
# Direct donor class alias matching SQ.Blocks.Price.Open
Open = bar_open

__all__ = ["Open", "bar_open", "open_price", "open_spec"]
