"""Session High price strategy block."""

from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.price._common import SessionPrice

logger = get_logger(__name__)

session_high_spec = BlockSpec(
    id="price.session_high",
    version="1.0.0",
    name="Session High",
    description="Returns Session High price for defined session window at shift",
    category="price",
    tags=("price", "session", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "SessionPrice or BarData container"),
        InputPort("start_hours", PortType.NUMBER, "Start hour 0..23", default=8),
        InputPort("start_minutes", PortType.NUMBER, "Start min 0..59", default=30),
        InputPort("end_hours", PortType.NUMBER, "Session end hour 0..23", default=15),
        InputPort("end_minutes", PortType.NUMBER, "Session end min 0..59", default=15),
        InputPort("shift", PortType.NUMBER, "Historical session shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Session High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(session_high_spec)
def session_high(
    chart: Any,
    start_hours: int = 8,
    start_minutes: int = 30,
    *,
    end_hours: int = 15,
    end_minutes: int = 15,
    shift: int = 0,
) -> float:
    """Get Session High price at specified session shift.

    Args:
        chart: SessionPrice or BarData context.
        start_hours: Session start hour (default 8).
        start_minutes: Session start minute (default 30).
        end_hours: Session end hour (default 15).
        end_minutes: Session end minute (default 15).
        shift: Historical session offset (default 0).

    Returns:
        Session High price as float, or NaN.
    """
    if isinstance(chart, SessionPrice):
        return chart.high(shift)

    if chart is not None and hasattr(chart, "prices") and hasattr(chart, "timestamps"):
        sp = SessionPrice(
            timestamps=chart.timestamps,
            open_data=chart.open,
            high_data=chart.high,
            low_data=chart.low,
            close_data=chart.close,
            start_hour=start_hours,
            start_minute=start_minutes,
            end_hour=end_hours,
            end_minute=end_minutes,
        )
        return sp.high(shift)

    return float("nan")


__all__ = ["session_high", "session_high_spec"]
