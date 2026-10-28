"""Is Month First Trading Day condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import (
    DateTime,
    resolve_bar_count,
    resolve_time_ms,
)
from app.include.blocks.base import block
from app.include.blocks.metadata import (
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
        return False
    cur_ym = (DateTime.get_year(cur_ms), DateTime.get_month(cur_ms))
    cur_day = DateTime.get_day(cur_ms)
    n = resolve_bar_count(source)
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
            return False
    return True
