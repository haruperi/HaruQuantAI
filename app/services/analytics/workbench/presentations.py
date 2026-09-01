"""Owner-evidence presentation builders for workbench sections (FEAT-ANLT-11).

Every builder here projects owner evidence — the report's presentation
series, the report's distribution metrics, or the canonical Simulation
closed-trade ledger — into finite JSON-safe rows. Builders never
recalculate report metrics and never invent values: when the underlying
evidence is absent the builder returns ``None`` and the caller emits an
explicitly unavailable section. Derived rows carry only counts, sums,
owner values, and timestamp arithmetic; no ratios such as win rate or
profit factor are computed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, cast

from app.composition.logging import get_logger
from app.services.analytics.contracts.evidence import to_report_json_safe

if TYPE_CHECKING:
    from app.services.analytics.contracts.models import PerformanceReport

logger = get_logger(__name__)

#: VAMI base index mandated by the classical VAMI definition.
_VAMI_BASE = Decimal(1000)

#: Supported period-table dimensions mirroring the gateway query enums.
_PERIOD_DIMENSIONS = frozenset(
    {"year", "quarter", "month", "week", "day", "day_of_week", "hour"}
)

#: Metric keys consulted for owner-supplied anchors and statistics.
_STARTING_EQUITY_KEY = "starting_equity"
_DISTRIBUTION_SECTION = "distribution"

#: Fence multiplier of the classical Tukey outlier rule applied to the
#: owner-supplied quartiles of the net trade PnL distribution.
_OUTLIER_FENCE_IQR = Decimal("1.5")


def _as_decimal(value: object) -> Decimal | None:
    """Read one owner value as a finite Decimal.

    Args:
        value: Decimal, str, int, or float evidence value.

    Returns:
        Finite Decimal, or None when the value is absent or unreadable.
    """
    if value is None:
        return None
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation, ValueError, TypeError:
        return None
    return parsed if parsed.is_finite() else None


def _as_timestamp(value: object) -> datetime | None:
    """Read one owner timestamp as a datetime.

    Args:
        value: datetime or ISO-8601 text.

    Returns:
        Parsed datetime, or None when unreadable.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _presentation_series(
    report: PerformanceReport, key: str
) -> list[dict[str, object]] | None:
    """Read one report-owned presentation series.

    Args:
        report: Validated source report.
        key: Presentation series key.

    Returns:
        Presentation rows, or None when the series is absent or empty.
    """
    presentation = report.precision_metadata.get("presentation_series")
    if not isinstance(presentation, Mapping):
        return None
    points = presentation.get(key)
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes, bytearray)):
        return None
    rows = [dict(point) for point in cast("Sequence[Mapping[str, object]]", points)]
    return rows or None


def _starting_equity(report: PerformanceReport) -> Decimal | None:
    """Read the owner-reported starting equity anchor.

    Args:
        report: Validated source report.

    Returns:
        Starting equity Decimal, or None when the metric is undefined.
    """
    for section in report.sections:
        for metric in section.metrics:
            if (
                metric.metric_key == _STARTING_EQUITY_KEY
                and metric.status == "calculated"
            ):
                return _as_decimal(metric.value)
    return None


def _equity_ordinates(
    report: PerformanceReport,
) -> list[tuple[datetime, Decimal]] | None:
    """Read the ordered (timestamp, equity) ordinates of the equity curve.

    Args:
        report: Validated source report.

    Returns:
        Ordered pairs, or None when the curve is absent.
    """
    points = _presentation_series(report, "equity_curve")
    if points is None:
        return None
    ordinates: list[tuple[datetime, Decimal]] = []
    for point in points:
        timestamp = _as_timestamp(point.get("timestamp"))
        equity = _as_decimal(point.get("equity"))
        if timestamp is None or equity is None:
            continue
        ordinates.append((timestamp, equity))
    return ordinates or None


def _ordered_trades(
    simulation_result: Mapping[str, object],
) -> list[dict[str, object]] | None:
    """Read the canonical closed-trade ledger in owner exit order.

    Args:
        simulation_result: Canonical Simulation result mapping.

    Returns:
        Trade rows sorted by (exit time, ticket), or None when absent.
    """

    def _sort_key(trade: Mapping[str, object]) -> tuple[datetime, str]:
        exit_time = _as_timestamp(trade.get("exit_time"))
        return (
            exit_time if exit_time is not None else datetime.max.replace(tzinfo=UTC),
            str(trade.get("ticket", "")),
        )

    ledger = simulation_result.get("closed_trades")
    if not isinstance(ledger, Sequence) or isinstance(ledger, (str, bytes, bytearray)):
        return None
    trades = [dict(trade) for trade in cast("Sequence[Mapping[str, object]]", ledger)]
    if not trades:
        return None
    trades.sort(key=_sort_key)
    return trades


def _net_pnl(trade: Mapping[str, object]) -> Decimal | None:
    """Read one trade's net PnL (profit plus commission plus swap).

    Args:
        trade: Closed-trade row.

    Returns:
        Net PnL Decimal, or None when unreadable.
    """
    profit = _as_decimal(trade.get("profit"))
    commission = _as_decimal(trade.get("commission"))
    swap = _as_decimal(trade.get("swap"))
    if profit is None:
        return None
    return profit + (commission or Decimal(0)) + (swap or Decimal(0))


def _json_rows(rows: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], ...]:
    """Convert finished rows to JSON-safe mappings.

    Args:
        rows: Presentation rows with owner-native values.

    Returns:
        JSON-safe row tuple.
    """
    return tuple(
        cast(
            "dict[str, object]",
            to_report_json_safe(dict(row)),
        )
        for row in rows
    )


def build_drawdown_curve(report: PerformanceReport) -> tuple[dict[str, object], ...]:
    """Read the report-owned drawdown presentation series.

    Args:
        report: Validated source report.

    Returns:
        JSON-safe drawdown rows, or an empty tuple when absent.
    """
    rows = _presentation_series(report, "drawdown_curve")
    return _json_rows(rows) if rows is not None else ()


def build_monthly_returns(report: PerformanceReport) -> tuple[dict[str, object], ...]:
    """Read the report-owned monthly-returns presentation table.

    Args:
        report: Validated source report.

    Returns:
        JSON-safe monthly rows, or an empty tuple when absent.
    """
    rows = _presentation_series(report, "monthly_returns")
    return _json_rows(rows) if rows is not None else ()


def build_returns_series(report: PerformanceReport) -> tuple[dict[str, object], ...]:
    """Derive per-point closed-trade returns from the equity curve.

    Each return is the fractional equity change between consecutive curve
    points, seeded with the owner-reported starting equity when defined.

    Args:
        report: Validated source report.

    Returns:
        JSON-safe return rows, or an empty tuple when evidence is absent.
    """
    ordinates = _equity_ordinates(report)
    if ordinates is None:
        return ()
    anchor = _starting_equity(report)
    rows: list[dict[str, object]] = []
    previous = anchor
    for timestamp, equity in ordinates:
        if previous is None or previous == 0:
            previous = equity
            continue
        rows.append(
            {
                "timestamp": timestamp,
                "return": (equity - previous) / previous,
                "equity": equity,
            }
        )
        previous = equity
    logger.debug("Built workbench returns series of %d rows", len(rows))
    return _json_rows(rows)


def build_vami_series(report: PerformanceReport) -> tuple[dict[str, object], ...]:
    """Derive the VAMI index series from the equity curve.

    The index is rebased to 1000 at the owner-reported starting equity,
    or at the first curve point when no anchor metric is defined.

    Args:
        report: Validated source report.

    Returns:
        JSON-safe VAMI rows, or an empty tuple when evidence is absent.
    """
    ordinates = _equity_ordinates(report)
    if ordinates is None:
        return ()
    base = _starting_equity(report) or ordinates[0][1]
    if base == 0:
        return ()
    rows = [
        {"timestamp": timestamp, "vami": _VAMI_BASE * equity / base}
        for timestamp, equity in ordinates
    ]
    logger.debug("Built workbench VAMI series of %d rows", len(rows))
    return _json_rows(rows)


_PERIOD_KEY_FORMATS: Mapping[str, str] = {
    "month": "%Y-%m",
    "week": "%G-W%V",
    "day": "%Y-%m-%d",
    "day_of_week": "%A",
    "hour": "%Y-%m-%dT%H",
}


def _period_key(timestamp: datetime, dimension: str) -> str:
    """Derive one period bucket key from an owner timestamp.

    Args:
        timestamp: Owner trade timestamp.
        dimension: Supported period dimension.

    Returns:
        Stable bucket key for the requested dimension.
    """
    if dimension == "year":
        return f"{timestamp.year:04d}"
    if dimension == "quarter":
        return f"{timestamp.year:04d}-Q{(timestamp.month - 1) // 3 + 1}"
    return timestamp.strftime(_PERIOD_KEY_FORMATS[dimension])


def _matches_context(trade: Mapping[str, object], context: str) -> bool:
    """Check one trade against the requested long/short context.

    Args:
        trade: Closed-trade row.
        context: ``all``, ``long`` (BUY), or ``short`` (SELL).

    Returns:
        True when the trade belongs to the requested context.
    """
    if context == "long":
        return str(trade.get("type")) == "BUY"
    if context == "short":
        return str(trade.get("type")) == "SELL"
    return True


def build_period_tables(
    simulation_result: Mapping[str, object],
    *,
    dimension: str = "month",
    context: str = "all",
) -> tuple[dict[str, object], ...]:
    """Aggregate the closed-trade ledger by one period dimension.

    Rows carry owner-safe aggregates only: trade counts, net PnL sums,
    and total holding seconds. No derived ratios are computed.

    Args:
        simulation_result: Canonical Simulation result mapping.
        dimension: One of year, quarter, month, week, day, day_of_week,
            hour.
        context: ``all``, ``long`` (BUY), or ``short`` (SELL).

    Returns:
        JSON-safe period rows, or an empty tuple when evidence is absent.
    """
    if dimension not in _PERIOD_DIMENSIONS:
        return ()
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    counts: dict[str, int] = {}
    nets: dict[str, Decimal] = {}
    held_totals: dict[str, int] = {}
    for trade in trades:
        if not _matches_context(trade, context):
            continue
        exit_time = _as_timestamp(trade.get("exit_time"))
        if exit_time is None:
            continue
        key = _period_key(exit_time, dimension)
        net = _net_pnl(trade) or Decimal(0)
        entry = _as_timestamp(trade.get("entry_time"))
        held = int((exit_time - entry).total_seconds()) if entry is not None else 0
        counts[key] = counts.get(key, 0) + 1
        nets[key] = nets.get(key, Decimal(0)) + net
        held_totals[key] = held_totals.get(key, 0) + held
    rows = [
        {
            "period": key,
            "trade_count": counts[key],
            "net_pnl": nets[key],
            "held_seconds": held_totals[key],
        }
        for key in sorted(counts)
    ]
    logger.debug(
        "Built workbench period table rows: dimension=%s context=%s count=%d",
        dimension,
        context,
        len(rows),
    )
    return _json_rows(rows)


def build_trade_calendar(
    simulation_result: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """Aggregate net PnL and trade counts per calendar exit day.

    Args:
        simulation_result: Canonical Simulation result mapping.

    Returns:
        JSON-safe calendar rows, or an empty tuple when evidence is absent.
    """
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    day_counts: dict[str, int] = {}
    day_nets: dict[str, Decimal] = {}
    for trade in trades:
        exit_time = _as_timestamp(trade.get("exit_time"))
        if exit_time is None:
            continue
        day = exit_time.strftime("%Y-%m-%d")
        day_counts[day] = day_counts.get(day, 0) + 1
        day_nets[day] = day_nets.get(day, Decimal(0)) + (_net_pnl(trade) or Decimal(0))
    rows = [
        {"date": day, "trade_count": day_counts[day], "net_pnl": day_nets[day]}
        for day in sorted(day_counts)
    ]
    logger.debug("Built workbench trade calendar rows: %d", len(rows))
    return _json_rows(rows)


def build_streaks(
    simulation_result: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """Derive the running win/loss streak counter per closed trade.

    Flat (zero-PnL) trades reset the streak counter.

    Args:
        simulation_result: Canonical Simulation result mapping.

    Returns:
        JSON-safe streak rows, or an empty tuple when evidence is absent.
    """
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    rows: list[dict[str, object]] = []
    streak = 0
    for trade in trades:
        net = _net_pnl(trade) or Decimal(0)
        if net > 0:
            streak = streak + 1 if streak > 0 else 1
            outcome = "win"
        elif net < 0:
            streak = streak - 1 if streak < 0 else -1
            outcome = "loss"
        else:
            streak = 0
            outcome = "flat"
        rows.append(
            {
                "ticket": trade.get("ticket"),
                "exit_time": trade.get("exit_time"),
                "outcome": outcome,
                "streak": streak,
            }
        )
    logger.debug("Built workbench streak rows: %d", len(rows))
    return _json_rows(rows)


def _distribution_metric(
    report: PerformanceReport, metric_key: str
) -> tuple[str, object] | None:
    """Read one calculated distribution metric with its unit.

    Args:
        report: Validated source report.
        metric_key: Owner metric key to read.

    Returns:
        (unit, value) pair, or None when the metric is not calculated.
    """
    for section in report.sections:
        if section.section_key != _DISTRIBUTION_SECTION:
            continue
        for metric in section.metrics:
            if metric.metric_key == metric_key and metric.status == "calculated":
                return metric.unit, metric.value
    return None


def build_histogram(report: PerformanceReport) -> tuple[dict[str, object], ...]:
    """Project the owner-calculated net-PnL histogram into bin rows.

    Args:
        report: Validated source report.

    Returns:
        JSON-safe bin rows, or an empty tuple when evidence is absent.
    """
    found = _distribution_metric(report, "histogram")
    if found is None:
        return ()
    _unit, value = found
    if not isinstance(value, Mapping):
        return ()
    edges = value.get("edges")
    counts = value.get("counts")
    if not isinstance(edges, Sequence) or not isinstance(counts, Sequence):
        return ()
    edges_list = [edge for edge in edges if edge is not None]
    rows = [
        {
            "edge_left": edges_list[index],
            "edge_right": edges_list[index + 1],
            "count": counts[index],
        }
        for index in range(min(len(edges_list) - 1, len(counts)))
    ]
    logger.debug("Built workbench histogram rows: %d", len(rows))
    return _json_rows(rows)


def build_outliers(
    simulation_result: Mapping[str, object], report: PerformanceReport
) -> tuple[dict[str, object], ...]:
    """List net-PnL trades outside the owner-reported Tukey fences.

    The quartiles come from the owner-calculated distribution percentiles;
    only fence membership of owner trade values is derived here.

    Args:
        simulation_result: Canonical Simulation result mapping.
        report: Validated source report.

    Returns:
        JSON-safe outlier rows, or an empty tuple when evidence is absent.
    """
    found = _distribution_metric(report, "percentiles")
    if found is None:
        return ()
    _unit, value = found
    if not isinstance(value, Mapping):
        return ()
    q1 = _as_decimal(value.get("p25"))
    q3 = _as_decimal(value.get("p75"))
    if q1 is None or q3 is None:
        return ()
    spread = q3 - q1
    low = q1 - _OUTLIER_FENCE_IQR * spread
    high = q3 + _OUTLIER_FENCE_IQR * spread
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    rows: list[dict[str, object]] = []
    for trade in trades:
        net = _net_pnl(trade)
        if net is None:
            continue
        if net < low:
            rows.append({"ticket": trade.get("ticket"), "net_pnl": net, "bound": "low"})
        elif net > high:
            rows.append(
                {"ticket": trade.get("ticket"), "net_pnl": net, "bound": "high"}
            )
    logger.debug("Built workbench outlier rows: %d", len(rows))
    return _json_rows(rows)


def build_excursions(
    simulation_result: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """List per-trade owner-reported MAE/MFE excursions.

    Args:
        simulation_result: Canonical Simulation result mapping.

    Returns:
        JSON-safe excursion rows, or an empty tuple when evidence is absent.
    """
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    rows = [
        {
            "ticket": trade.get("ticket"),
            "mae": trade.get("mae"),
            "mfe": trade.get("mfe"),
        }
        for trade in trades
        if trade.get("mae") is not None or trade.get("mfe") is not None
    ]
    logger.debug("Built workbench excursion rows: %d", len(rows))
    return _json_rows(rows)


def build_duration(
    simulation_result: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """List per-trade holding durations from owner timestamps.

    Args:
        simulation_result: Canonical Simulation result mapping.

    Returns:
        JSON-safe duration rows, or an empty tuple when evidence is absent.
    """
    trades = _ordered_trades(simulation_result)
    if trades is None:
        return ()
    rows: list[dict[str, object]] = []
    for trade in trades:
        entry = _as_timestamp(trade.get("entry_time"))
        exit_time = _as_timestamp(trade.get("exit_time"))
        if entry is None or exit_time is None:
            continue
        rows.append(
            {
                "ticket": trade.get("ticket"),
                "entry_time": entry,
                "exit_time": exit_time,
                "duration_seconds": int((exit_time - entry).total_seconds()),
            }
        )
    logger.debug("Built workbench duration rows: %d", len(rows))
    return _json_rows(rows)


__all__ = (
    "build_drawdown_curve",
    "build_duration",
    "build_excursions",
    "build_histogram",
    "build_monthly_returns",
    "build_outliers",
    "build_period_tables",
    "build_returns_series",
    "build_streaks",
    "build_trade_calendar",
    "build_vami_series",
)
