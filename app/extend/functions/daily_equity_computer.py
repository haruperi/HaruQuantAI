"""Daily equity curve computation (matching donor DailyEquityComputer.java).

Description:
    Computes daily aggregated cumulative equity from chronological closed order
    streams, tracking profit accumulation across day intervals and forward-filling
    untraded days, conforming to StrategyQuant DailyEquityComputer.

Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions.

Key Capabilities:
    - FR-FUNCTIONS-DAILY-EQUITY: Calculate daily cumulative equity curve.

Python API Usage:
    from app.extend.functions.daily_equity_computer import DailyEquityComputer
    daily_equity = DailyEquityComputer.compute_daily_equity(orders, result_pl_type=0)

CLI Usage:
    uv run pytest tests/extend/test_functions.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.core.host.logging import get_logger
from app.extend.functions.comparator_by_profit import (
    PL_TYPE_MONEY,
    _extract_pl,
)

logger = get_logger(__name__)

_DAY_MS: int = 86_400_000
_EXTRA_DAYS_BUFFER: int = 3


def _is_filled(order: Any) -> bool:
    """Return True if order is filled and valid for equity computation."""
    if hasattr(order, "is_filled_order"):
        return bool(order.is_filled_order())
    if hasattr(order, "isFilledOrder"):
        return bool(order.isFilledOrder())
    return not getattr(order, "is_canceled", False)


def _get_close_time_ms(order: Any) -> int:
    """Extract order close timestamp in epoch milliseconds."""
    val = getattr(
        order,
        "close_time_ms",
        getattr(order, "CloseTime", getattr(order, "close_time", 0)),
    )
    return int(val)


def _get_order_pl(order: Any, pl_type: int) -> float:
    """Extract order profit by PL type."""
    fn = getattr(order, "get_pl_by_type", getattr(order, "getPLByType", None))
    if callable(fn):
        return float(fn(pl_type))
    return _extract_pl(order, pl_type)


def _get_date_in_ms(timestamp_ms: int) -> int:
    """Truncate timestamp to UTC start of day in milliseconds."""
    return timestamp_ms - (timestamp_ms % _DAY_MS)


def _find_time_bounds(
    order_list: Sequence[Any],
) -> tuple[int, int] | None:
    """Find first and last close time among filled orders in sequence."""
    last_order_time: int = -9223372036854775808
    first_order_time: int = 9223372036854775807
    has_filled: bool = False

    for o in order_list:
        if not _is_filled(o):
            continue
        c_time = _get_close_time_ms(o)
        has_filled = True
        last_order_time = max(last_order_time, c_time)
        first_order_time = min(first_order_time, c_time)

    if not has_filled:
        return None
    return first_order_time, last_order_time


def _fill_gap(
    equity_per_day: list[float],
    equity_index: int,
    array_time: int,
    order_time: int,
) -> tuple[int, int] | None:
    """Forward fill daily equity across untraded calendar days."""
    last_day_equity = equity_per_day[equity_index]
    while array_time < order_time:
        equity_index += 1
        if equity_index >= len(equity_per_day):
            logger.error(
                "FR-FUNCTIONS-DAILY-EQUITY: index overflow: %d >= %d",
                equity_index,
                len(equity_per_day),
            )
            return None
        equity_per_day[equity_index] = last_day_equity
        array_time += _DAY_MS
    return equity_index, array_time


class DailyEquityComputer:
    """Computes daily cumulative equity series from trading orders."""

    @classmethod
    def compute_daily_equity(
        cls,
        order_list: Sequence[Any],
        result_pl_type: int = PL_TYPE_MONEY,
    ) -> list[float]:
        """Compute cumulative equity per calendar day from closed orders.

        Args:
            order_list: Sequence of closed order records.
            result_pl_type: 0 for Money, 1 for Pips, 2 for Percent.

        Returns:
            List of daily cumulative equity values, or empty list on error.
        """
        logger.info(
            "FR-FUNCTIONS-DAILY-EQUITY: computing daily equity for %d orders",
            len(order_list),
        )
        if not order_list:
            return []

        bounds = _find_time_bounds(order_list)
        if bounds is None:
            return []
        first_order_time, last_order_time = bounds

        array_size = _EXTRA_DAYS_BUFFER + int(
            (last_order_time - first_order_time) // _DAY_MS
        )
        equity_per_day: list[float] = [0.0] * array_size

        array_time = _get_date_in_ms(first_order_time)
        total_pl: float = 0.0
        equity_index: int = 0

        for idx, order in enumerate(order_list):
            if not _is_filled(order):
                continue

            total_pl += _get_order_pl(order, result_pl_type)
            order_time = _get_date_in_ms(_get_close_time_ms(order))

            if order_time == array_time:
                equity_per_day[equity_index] = total_pl
            elif order_time < array_time:
                logger.error("FR-FUNCTIONS-DAILY-EQUITY: out-of-order trade at %d", idx)
                return []
            else:
                res = _fill_gap(equity_per_day, equity_index, array_time, order_time)
                if res is None:
                    return []
                equity_index, array_time = res
                equity_per_day[equity_index] = total_pl

        if equity_index < len(equity_per_day):
            last_day_equity = equity_per_day[equity_index]
            for i in range(equity_index + 1, len(equity_per_day)):
                equity_per_day[i] = last_day_equity

        return equity_per_day
