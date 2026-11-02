"""Get date integer encoding temporal expression strategy block.

Description:
    Encodes calendar year, month, and day into integer YYYYMMDD with non-silent
    requirement logging, supporting both ISO (year, month, day) and StrategyQuant
    donor (day, month, year) positional call signatures.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library.
Key Capabilities:
    - FR-function-temporal: Calendar date integer encoding.
    - FR-function-logging: Non-silent requirement diagnostics.
Python API Usage:
    from app.extend.blocks.functions.get_date import get_date
    date_int = get_date(year=2024, month=10, day=28)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.functions._common import (
    DATE_MONTH_MULTIPLIER,
    DATE_YEAR_MULTIPLIER,
)

logger = get_logger(__name__)

MAX_CALENDAR_DAY: int = 31
MIN_CALENDAR_YEAR: int = 1900

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
def get_date(
    year: int = 2016,
    month: int = 1,
    day: int = 1,
    *,
    d: int | None = None,
    m: int | None = None,
    y: int | None = None,
) -> int:
    """Encode date as integer YYYYMMDD.

    Supports both (year, month, day) and StrategyQuant donor (day, month, year)
    positional conventions.

    Args:
        year: Full calendar year (or day if passed positionally in SQ donor order).
        month: Month number 1..12.
        day: Day number 1..31 (or year if passed positionally in SQ donor order).
        d: Explicit keyword day override.
        m: Explicit keyword month override.
        y: Explicit keyword year override.

    Returns:
        Integer encoded as YYYYMMDD.
    """
    eff_year = year if y is None else y
    eff_month = month if m is None else m
    eff_day = day if d is None else d

    # Disambiguate donor StrategyQuant positional order (day, month, year):
    if eff_year <= MAX_CALENDAR_DAY and eff_day >= MIN_CALENDAR_YEAR:
        eff_year, eff_day = eff_day, eff_year

    res = eff_year * DATE_YEAR_MULTIPLIER + eff_month * DATE_MONTH_MULTIPLIER + eff_day
    logger.debug(
        "FR-SERVICES-FUNCTION-TEMPORAL: get_date(%04d-%02d-%02d) = %d",
        eff_year,
        eff_month,
        eff_day,
        res,
    )
    return res


__all__ = ["get_date", "get_date_spec"]
