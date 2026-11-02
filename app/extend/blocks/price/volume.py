"""Bar Volume price strategy block.

Description:
    Returns bar Volume at the specified historical shift, evaluating
    against BarPrice containers, series, or raw volume arrays.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-VOLUME: Historical bar Volume retrieval.
Python API Usage:
    from app.extend.blocks.price.volume import Volume, bar_volume
    vol = bar_volume(chart, shift=0)
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

volume_spec = BlockSpec(
    id="price.volume",
    version="1.0.0",
    name="Volume",
    description="Returns bar Volume at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "volume"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.SUB,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Volume at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(volume_spec)
def bar_volume(chart: Any, shift: int = 0) -> float:
    """Get bar Volume at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        Volume as float, or NaN.
    """
    logger.debug("FR-PRICE-VOLUME: Volume(shift=%d)", shift)
    return resolve_chart_field(chart, "volume", shift)


volume_price = bar_volume
# Direct donor class alias matching SQ.Blocks.Price.Volume
Volume = bar_volume

__all__ = ["Volume", "bar_volume", "volume_price", "volume_spec"]
