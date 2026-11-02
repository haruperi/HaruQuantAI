"""Bar Close price strategy block.

Description:
    Returns bar Close price at the specified historical shift, evaluating
    against BarPrice containers, series, or raw price arrays.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-CLOSE: Historical bar Close price retrieval.
Python API Usage:
    from app.extend.blocks.price.close import Close, bar_close
    price = bar_close(chart, shift=0)
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
from app.extend.blocks.price._common import resolve_chart_field

logger = get_logger(__name__)

close_spec = BlockSpec(
    id="price.close",
    version="1.0.0",
    name="Close",
    description="Returns bar Close price at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Close price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(close_spec)
def bar_close(chart: Any, shift: int = 0) -> float:
    """Get bar Close price at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        Close price as float, or NaN.
    """
    logger.debug("FR-PRICE-CLOSE: Close(shift=%d)", shift)
    return resolve_chart_field(chart, "close", shift)


close_price = bar_close
# Direct donor class alias matching SQ.Blocks.Price.Close
Close = bar_close

__all__ = ["Close", "bar_close", "close_price", "close_spec"]
