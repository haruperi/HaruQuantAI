"""Heiken Ashi Close price strategy block.

Description:
    Returns smoothed Heiken Ashi Close price at the specified historical shift,
    evaluating against BarPrice containers or OHLC arrays.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-HEIKEN-ASHI-CLOSE: Smoothed Heiken Ashi Close price retrieval.
Python API Usage:
    from app.extend.blocks.price.heiken_ashi_close import (
        HeikenAshiClose,
        heiken_ashi_close,
    )
    price = heiken_ashi_close(chart, shift=0)
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
from app.extend.blocks.price._common import (
    compute_heiken_ashi,
    resolve_shift_value,
)

logger = get_logger(__name__)

heiken_ashi_close_spec = BlockSpec(
    id="price.heiken_ashi_close",
    version="1.0.0",
    name="Heiken Ashi Close",
    description="Returns smoothed Heiken Ashi Close price at specified shift",
    category="price",
    tags=("price", "heiken_ashi", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart price container or BarData"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Heiken Ashi Close price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(heiken_ashi_close_spec)
def heiken_ashi_close(chart: Any, shift: int = 0) -> float:
    """Get Heiken Ashi Close price at historical shift.

    Args:
        chart: Chart price container, BarPrice, or BarData.
        shift: Historical bar offset (default 0).

    Returns:
        Heiken Ashi Close price as float, or NaN.
    """
    logger.debug("FR-PRICE-HEIKEN-ASHI-CLOSE: HeikenAshiClose(shift=%d)", shift)
    res = compute_heiken_ashi(chart)
    if res is None:
        return float("nan")
    _, _, _, ha_close = res
    return resolve_shift_value(ha_close, shift)


# Direct donor class alias matching SQ.Blocks.Price.HeikenAshiClose
HeikenAshiClose = heiken_ashi_close

__all__ = ["HeikenAshiClose", "heiken_ashi_close", "heiken_ashi_close_spec"]
