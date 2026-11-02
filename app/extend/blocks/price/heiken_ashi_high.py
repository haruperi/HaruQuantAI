"""Heiken Ashi High price strategy block.

Description:
    Returns smoothed Heiken Ashi High price at the specified historical shift,
    evaluating against BarPrice containers or OHLC arrays.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-HEIKEN-ASHI-HIGH: Smoothed Heiken Ashi High price retrieval.
Python API Usage:
    from app.extend.blocks.price.heiken_ashi_high import (
        HeikenAshiHigh,
        heiken_ashi_high,
    )
    price = heiken_ashi_high(chart, shift=0)
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

heiken_ashi_high_spec = BlockSpec(
    id="price.heiken_ashi_high",
    version="1.0.0",
    name="Heiken Ashi High",
    description="Returns smoothed Heiken Ashi High price at specified shift",
    category="price",
    tags=("price", "heiken_ashi", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart price container or BarData"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Heiken Ashi High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(heiken_ashi_high_spec)
def heiken_ashi_high(chart: Any, shift: int = 0) -> float:
    """Get Heiken Ashi High price at historical shift.

    Args:
        chart: Chart price container, BarPrice, or BarData.
        shift: Historical bar offset (default 0).

    Returns:
        Heiken Ashi High price as float, or NaN.
    """
    logger.debug("FR-PRICE-HEIKEN-ASHI-HIGH: HeikenAshiHigh(shift=%d)", shift)
    res = compute_heiken_ashi(chart)
    if res is None:
        return float("nan")
    _, ha_high, _, _ = res
    return resolve_shift_value(ha_high, shift)


# Direct donor class alias matching SQ.Blocks.Price.HeikenAshiHigh
HeikenAshiHigh = heiken_ashi_high

__all__ = ["HeikenAshiHigh", "heiken_ashi_high", "heiken_ashi_high_spec"]
