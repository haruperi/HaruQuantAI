"""Get date integer encoding temporal expression strategy block."""

from __future__ import annotations

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.functions._common import (
    DATE_MONTH_MULTIPLIER,
    DATE_YEAR_MULTIPLIER,
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

get_date_spec = BlockSpec(
    id="function.get_date",
    version="1.0.0",
    name="Get Date",
    description="Encodes calendar year, month, and day into integer YYYYMMDD",
    category="functions",
    tags=("temporal", "date", "calendar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "year", PortType.NUMBER, "Full calendar year (e.g. 2024)", default=2016
        ),
        InputPort("month", PortType.NUMBER, "Month number 1..12", default=1),
        InputPort("day", PortType.NUMBER, "Day number 1..31", default=1),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Encoded YYYYMMDD integer"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(get_date_spec)
def get_date(year: int = 2016, month: int = 1, day: int = 1) -> int:
    """Encode date as integer YYYYMMDD.

    Args:
        year: Full calendar year (e.g. 2024).
        month: Month number 1..12.
        day: Day number 1..31.

    Returns:
        Integer encoded as YYYYMMDD.
    """
    res = year * DATE_YEAR_MULTIPLIER + month * DATE_MONTH_MULTIPLIER + day
    logger.debug(
        "FR-SERVICES-FUNCTION-TEMPORAL: get_date(%04d-%02d-%02d) = %d",
        year,
        month,
        day,
        res,
    )
    return res


__all__ = ["get_date", "get_date_spec"]
