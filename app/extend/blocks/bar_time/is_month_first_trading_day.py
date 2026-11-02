"""Is Month First Trading Day condition strategy block.

Description:
    Evaluates whether bar falls on the first trading day of the month,
    with configurable weekend exclusion, matching StrategyQuant
    IsMonthFirstTradingDay snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful IsMonthFirstTradingDay block.
Key Capabilities:
    - FR-bar-time-predicate: Test if bar date is first trading day of month.
Python API Usage:
    from app.extend.blocks.bar_time.is_month_first_trading_day import (
        is_month_first_trading_day,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import (
    DateTime,
    _log_cond,
    resolve_bar_count,
    resolve_time_ms,
)
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

is_month_first_trading_day_spec = BlockSpec(
    id="condition.is_month_first_trading_day",
    version="1.0.0",
    name="Is Month First Trading Day",
    description="Evaluate whether bar falls on first trading day of the month",
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
            "True if on first trading day of month",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


def _is_first_calendar_trading_day(cur_ms: int, *, include_weekends: bool) -> bool:
    """Check if current timestamp matches the first calendar trading day."""
    first_date = DateTime.set_day_of_month(cur_ms, 1)
    if not include_weekends:
        dow = DateTime.get_day_of_week(first_date)
        if dow == DateTime.SATURDAY:
            first_date = DateTime.add_days(first_date, 2)
        elif dow == DateTime.SUNDAY:
            first_date = DateTime.add_days(first_date, 1)
    return DateTime.get_day(cur_ms) == DateTime.get_day(first_date)


def _has_prior_trading_bar(
    source: Any,
    shift: int,
    cur_ym: tuple[int, int],
    cur_day: int,
    *,
    include_weekends: bool,
) -> bool:
    """Check if earlier bars in the current month already occurred."""
    n = resolve_bar_count(source)
    if n <= 1:
        return False
    curr_idx = n - 1 - shift
    for prev_idx in range(curr_idx - 1, -1, -1):
        prev_ms = resolve_time_ms(source, n - 1 - prev_idx)
        if prev_ms == -1:
            continue
        if (DateTime.get_year(prev_ms), DateTime.get_month(prev_ms)) != cur_ym:
            continue
        if not include_weekends and DateTime.get_day_of_week(prev_ms) in (
            DateTime.SATURDAY,
            DateTime.SUNDAY,
        ):
            continue
        if DateTime.get_day(prev_ms) != cur_day:
            return True
    return False


@block(is_month_first_trading_day_spec)
def is_month_first_trading_day(
    source: Any, shift: int = 0, *, include_weekends: bool = False
) -> bool:
    """Evaluate whether bar falls on first trading day of the month."""
    if hasattr(source, "is_month_first_trading_day") and callable(
        source.is_month_first_trading_day
    ):
        return bool(
            source.is_month_first_trading_day(shift, include_weekends=include_weekends)
        )
    cur_ms = resolve_time_ms(source, shift)
    if cur_ms == -1:
        return False
    if not include_weekends and DateTime.get_day_of_week(cur_ms) in (
        DateTime.SATURDAY,
        DateTime.SUNDAY,
    ):
        return _log_cond("is_month_first_trading_day", shift, False)
    cur_ym = (DateTime.get_year(cur_ms), DateTime.get_month(cur_ms))
    cur_day = DateTime.get_day(cur_ms)
    if _has_prior_trading_bar(
        source, shift, cur_ym, cur_day, include_weekends=include_weekends
    ):
        return _log_cond("is_month_first_trading_day", shift, False)
    res = _is_first_calendar_trading_day(cur_ms, include_weekends=include_weekends)
    return _log_cond("is_month_first_trading_day", shift, res)
