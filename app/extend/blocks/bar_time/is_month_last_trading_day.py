"""Is Month Last Trading Day condition strategy block.

Description:
    Evaluates whether bar falls on the last trading day of the month,
    with configurable weekend exclusion, matching StrategyQuant
    IsMonthLastTradingDay snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful IsMonthLastTradingDay block.
Key Capabilities:
    - FR-bar-time-predicate: Test if bar date is last trading day of month.
Python API Usage:
    from app.extend.blocks.bar_time.is_month_last_trading_day import (
        is_month_last_trading_day,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.bar_time._common import (
    DateTime,
    _log_cond,
    resolve_time_ms,
)

is_month_last_trading_day_spec = BlockSpec(
    id="condition.is_month_last_trading_day",
    version="1.0.0",
    name="Is Month Last Trading Day",
    description="Evaluate whether bar falls on last trading day of the month",
    category="bar_time",
    tags=("condition", "trading_day", "calendar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
        InputPort(
            "include_weekends",
            PortType.BOOLEAN,
            "Whether to consider weekend days",
            default=False,
        ),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if on last trading day of month",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_month_last_trading_day_spec)
def is_month_last_trading_day(
    source: Any, shift: int = 0, *, include_weekends: bool = False
) -> bool:
    """Evaluate whether bar falls on last trading day of the month."""
    if hasattr(source, "is_month_last_trading_day") and callable(
        source.is_month_last_trading_day
    ):
        return bool(
            source.is_month_last_trading_day(shift, include_weekends=include_weekends)
        )
    ms = resolve_time_ms(source, shift)
    if ms == -1:
        return False
    last_date = DateTime.set_day_of_month(ms, DateTime.get_days_in_month(ms))
    if not include_weekends:
        dow = DateTime.get_day_of_week(last_date)
        if dow == DateTime.SATURDAY:
            last_date = DateTime.add_days(last_date, -1)
        elif dow == DateTime.SUNDAY:
            last_date = DateTime.add_days(last_date, -2)
    res = DateTime.get_day(ms) == DateTime.get_day(last_date)
    return _log_cond("is_month_last_trading_day", shift, res)
