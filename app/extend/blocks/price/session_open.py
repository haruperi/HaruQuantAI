"""Session Open price strategy block."""

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
from app.extend.blocks.price._common import SessionPrice

logger = get_logger(__name__)

session_open_spec = BlockSpec(
    id="price.session_open",
    version="1.0.0",
    name="Session Open",
    description="Returns Session Open price for defined session window at shift",
    category="price",
    tags=("price", "session", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "SessionPrice or BarData container"),
        InputPort("start_hours", PortType.NUMBER, "Start hour 0..23", default=8),
        InputPort("start_minutes", PortType.NUMBER, "Start min 0..59", default=30),
        InputPort("shift", PortType.NUMBER, "Historical session shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Session Open price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(session_open_spec)
def session_open(
    chart: Any,
    start_hours: int = 8,
    start_minutes: int = 30,
    shift: int = 0,
) -> float:
    """Get Session Open price at specified session shift.

    Args:
        chart: SessionPrice or BarData context.
        start_hours: Session start hour (default 8).
        start_minutes: Session start minute (default 30).
        shift: Historical session offset (default 0).

    Returns:
        Session Open price as float, or NaN.
    """
    if isinstance(chart, SessionPrice):
        return chart.open(shift)

    if chart is not None and hasattr(chart, "prices") and hasattr(chart, "timestamps"):
        sp = SessionPrice(
            timestamps=chart.timestamps,
            open_data=chart.open,
            high_data=chart.high,
            low_data=chart.low,
            close_data=chart.close,
            start_hour=start_hours,
            start_minute=start_minutes,
        )
        return sp.open(shift)

    return float("nan")


__all__ = ["session_open", "session_open_spec"]
