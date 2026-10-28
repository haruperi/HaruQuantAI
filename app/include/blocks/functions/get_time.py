"""Get time integer encoding temporal expression strategy block."""

from __future__ import annotations

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.functions._common import (
    TIME_HOUR_MULTIPLIER,
    TIME_MINUTE_MULTIPLIER,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

get_time_spec = BlockSpec(
    id="function.get_time",
    version="1.0.0",
    name="Get Time",
    description="Encodes hour, minute, and second into integer HHMMSS",
    category="functions",
    tags=("temporal", "time", "clock"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("hour", PortType.NUMBER, "Hour number 0..23", default=0),
        InputPort("minute", PortType.NUMBER, "Minute number 0..59", default=0),
        InputPort("second", PortType.NUMBER, "Second number 0..59", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Encoded HHMMSS integer"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(get_time_spec)
def get_time(hour: int = 0, minute: int = 0, second: int = 0) -> int:
    """Encode time as integer HHMMSS.

    Args:
        hour: Hour number 0..23.
        minute: Minute number 0..59.
        second: Second number 0..59.

    Returns:
        Integer encoded as HHMMSS.
    """
    res = hour * TIME_HOUR_MULTIPLIER + minute * TIME_MINUTE_MULTIPLIER + second
    logger.debug(
        "FR-SERVICES-FUNCTION-TEMPORAL: get_time(%02d:%02d:%02d) = %d",
        hour,
        minute,
        second,
        res,
    )
    return res


__all__ = ["get_time", "get_time_spec"]
