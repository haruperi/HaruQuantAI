"""Session Close price strategy block."""

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

session_close_spec = BlockSpec(
    id="price.session_close",
    version="1.0.0",
    name="Session Close",
    description="Returns Session Close price for defined session window at shift",
    category="price",
    tags=("price", "session", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "SessionPrice or BarData container"),
        InputPort("end_hours", PortType.NUMBER, "Session end hour 0..23", default=15),
        InputPort("end_minutes", PortType.NUMBER, "Session end min 0..59", default=15),
        InputPort("shift", PortType.NUMBER, "Historical session shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Session Close price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(session_close_spec)
def session_close(
    chart: Any,
    end_hours: int = 15,
    end_minutes: int = 15,
    shift: int = 0,
) -> float:
    """Get Session Close price at specified session shift.

    Args:
        chart: SessionPrice or BarData context.
        end_hours: Session end hour (default 15).
        end_minutes: Session end minute (default 15).
        shift: Historical session offset (default 0).

    Returns:
        Session Close price as float, or NaN.
    """
    if isinstance(chart, SessionPrice):
        return chart.close(shift)

    if chart is not None and hasattr(chart, "prices") and hasattr(chart, "timestamps"):
        sp = SessionPrice(
            timestamps=chart.timestamps,
            open_data=chart.open,
            high_data=chart.high,
            low_data=chart.low,
            close_data=chart.close,
            end_hour=end_hours,
            end_minute=end_minutes,
        )
        return sp.close(shift)

    return float("nan")


__all__ = ["session_close", "session_close_spec"]
