"""Session Low price strategy block.

Description:
    Returns Session Low price for defined session window at shift,
    evaluating against SessionPrice or BarData containers.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-SESSION-LOW: Defined window Session Low price retrieval.
Python API Usage:
    from app.extend.blocks.price.session_low import (
        SessionLow,
        session_low,
    )
    price = session_low(chart, start_hours=8, end_hours=15, shift=0)
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
from app.extend.blocks.price._common import SessionPrice

logger = get_logger(__name__)

session_low_spec = BlockSpec(
    id="price.session_low",
    version="1.0.0",
    name="Session Low",
    description="Returns Session Low price for defined session window at shift",
    category="price",
    tags=("price", "session", "low"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "SessionPrice or BarData container"),
        InputPort("start_hours", PortType.NUMBER, "Start hour 0..23", default=8),
        InputPort("start_minutes", PortType.NUMBER, "Start min 0..59", default=30),
        InputPort("end_hours", PortType.NUMBER, "End hour 0..23", default=15),
        InputPort("end_minutes", PortType.NUMBER, "End min 0..59", default=15),
        InputPort("shift", PortType.NUMBER, "Historical session shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Session Low price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(session_low_spec)
def session_low(
    chart: Any,
    start_hours: int = 8,
    start_minutes: int = 30,
    *,
    end_hours: int = 15,
    end_minutes: int = 15,
    shift: int = 0,
) -> float:
    """Get Session Low price at specified session shift.

    Args:
        chart: SessionPrice or BarData context.
        start_hours: Session start hour (default 8).
        start_minutes: Session start minute (default 30).
        end_hours: Session end hour (default 15).
        end_minutes: Session end minute (default 15).
        shift: Historical session offset (default 0).

    Returns:
        Session Low price as float, or NaN.
    """
    logger.debug(
        "FR-PRICE-SESSION-LOW: SessionLow(start=%02d:%02d, end=%02d:%02d, shift=%d)",
        start_hours,
        start_minutes,
        end_hours,
        end_minutes,
        shift,
    )
    if isinstance(chart, SessionPrice):
        return chart.low(shift)

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
        return sp.low(shift)

    return float("nan")


# Direct donor class alias matching SQ.Blocks.Price.SessionLow
SessionLow = session_low

__all__ = ["SessionLow", "session_low", "session_low_spec"]
