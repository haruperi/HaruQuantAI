"""Finite equity-derived presentation series for canonical reports.

These helpers project the report-owned closed-trade equity curve into the
presentation shapes the report itself publishes (drawdown and monthly
returns). They derive presentation rows from owner evidence only; they
never recalculate report metrics, never fabricate points, and never
substitute zero for absent evidence.

Boundary assumption: the closed-trade equity curve is anchored at the
operator's initial balance before the first closed trade, so drawdown and
monthly returns seed their running peak and prior-month base from that
balance when it is supplied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.utils import get_logger

logger = get_logger(__name__)


def _as_decimal(value: object) -> Decimal:
    """Normalize one owner equity value to a finite Decimal.

    Args:
        value: Equity value as Decimal, str, int, or float.

    Returns:
        Finite Decimal representation.

    Raises:
        AnalyticsValidationError: If the value cannot be read finitely.
    """
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise AnalyticsValidationError(
            "presentation equity value is not decimal-safe"
        ) from error
    if not parsed.is_finite():
        raise AnalyticsValidationError("presentation equity value is not finite")
    return parsed


def _as_timestamp(value: object) -> datetime:
    """Normalize one owner timestamp to a UTC datetime.

    Args:
        value: Timestamp as datetime or ISO-8601 text.

    Returns:
        Parsed datetime.

    Raises:
        AnalyticsValidationError: If the timestamp cannot be parsed.
    """
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as error:
        raise AnalyticsValidationError(
            "presentation timestamp is not ISO-8601"
        ) from error


def _equity_ordinates(
    points: Sequence[Mapping[str, object]],
) -> list[tuple[datetime, Decimal]]:
    """Read the ordered (timestamp, equity) ordinates of an equity curve.

    Args:
        points: Owner presentation equity points in owner order.

    Returns:
        Ordered timestamp/equity pairs.

    Raises:
        AnalyticsValidationError: If a point lacks a usable ordinate.
    """
    ordinates: list[tuple[datetime, Decimal]] = []
    for point in points:
        if "equity" not in point or "timestamp" not in point:
            raise AnalyticsValidationError("presentation point is incomplete")
        timestamp = _as_timestamp(point["timestamp"])
        equity = _as_decimal(point["equity"])
        ordinates.append((timestamp, equity))
    return ordinates


def build_drawdown_series(
    points: Sequence[Mapping[str, object]],
    *,
    initial_balance: Decimal | None = None,
) -> tuple[dict[str, object], ...]:
    """Build the closed-trade drawdown presentation series.

    The running peak is seeded with the initial balance when supplied, so
    an early loss below the starting equity is visible as drawdown even
    before any new equity high exists.

    Args:
        points: Owner presentation equity points in owner order.
        initial_balance: Optional starting equity anchor.

    Returns:
        Rows of timestamp, equity, peak, and fractional drawdown.

    Raises:
        AnalyticsValidationError: If the equity evidence is unreadable.
    """
    ordinates = _equity_ordinates(points)
    if not ordinates:
        return ()
    peak = (
        _as_decimal(initial_balance) if initial_balance is not None else ordinates[0][1]
    )
    rows: list[dict[str, object]] = []
    for timestamp, equity in ordinates:
        peak = max(peak, equity)
        drawdown = Decimal(0) if peak == 0 else (equity - peak) / peak
        rows.append(
            {
                "timestamp": timestamp,
                "equity": equity,
                "peak": peak,
                "drawdown": drawdown,
            }
        )
    logger.debug("Built drawdown presentation series of %d rows", len(rows))
    return tuple(rows)


def build_monthly_return_rows(
    points: Sequence[Mapping[str, object]],
    *,
    initial_balance: Decimal | None = None,
) -> tuple[dict[str, object], ...]:
    """Build the calendar-monthly return presentation table.

    Each calendar month contributes its last observed equity; the month's
    return is measured against the previous month-end equity, seeded with
    the initial balance when supplied.

    Args:
        points: Owner presentation equity points in owner order.
        initial_balance: Optional starting equity anchor.

    Returns:
        Rows of month key, fractional return, ending equity, and points.

    Raises:
        AnalyticsValidationError: If the equity evidence is unreadable.
    """
    ordinates = _equity_ordinates(points)
    if not ordinates:
        return ()
    month_ends: dict[str, tuple[Decimal, int]] = {}
    for timestamp, equity in ordinates:
        # Owner order is exit-time order, so the last write per month key is
        # that month's ending equity.
        month_key = timestamp.strftime("%Y-%m")
        _ending, count = month_ends.get(month_key, (equity, 0))
        month_ends[month_key] = (equity, count + 1)
    previous = _as_decimal(initial_balance) if initial_balance is not None else None
    rows: list[dict[str, object]] = []
    for month_key in sorted(month_ends):
        ending, count = month_ends[month_key]
        base = previous if previous is not None and previous != 0 else ending
        monthly_return = Decimal(0) if base == 0 else (ending - base) / base
        rows.append(
            {
                "month": month_key,
                "return": monthly_return,
                "ending_equity": ending,
                "trade_points": count,
            }
        )
        previous = ending
    logger.debug("Built monthly return presentation rows: %d", len(rows))
    return tuple(rows)


__all__ = ("build_drawdown_series", "build_monthly_return_rows")
