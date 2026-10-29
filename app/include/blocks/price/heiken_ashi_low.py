"""Heiken Ashi Low price strategy block."""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.price._common import (
    compute_heiken_ashi,
    resolve_shift_value,
)

logger = get_logger(__name__)

heiken_ashi_low_spec = BlockSpec(
    id="price.heiken_ashi_low",
    version="1.0.0",
    name="Heiken Ashi Low",
    description="Returns smoothed Heiken Ashi Low price at specified shift",
    category="price",
    tags=("price", "heiken_ashi", "low"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart price container or BarData"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Heiken Ashi Low price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(heiken_ashi_low_spec)
def heiken_ashi_low(chart: Any, shift: int = 0) -> float:
    """Get Heiken Ashi Low price at historical shift.

    Args:
        chart: Chart price container, BarPrice, or BarData.
        shift: Historical bar offset (default 0).

    Returns:
        Heiken Ashi Low price as float, or NaN.
    """
    res = compute_heiken_ashi(chart)
    if res is None:
        return float("nan")
    _, _, ha_low, _ = res
    return resolve_shift_value(ha_low, shift)


__all__ = ["heiken_ashi_low", "heiken_ashi_low_spec"]
