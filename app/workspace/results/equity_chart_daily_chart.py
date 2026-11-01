"""Daily P&L bar subchart series generator service.

Description:
    Implements EquityChartDailyChartService aggregating closed trade net
    profits by UTC calendar day and tracking cumulative balance progression.

Purpose:
    FEAT-RESULTS-DAILY-CHART: Daily periodic P&L bar subchart series.

Key Capabilities:
    - FR-results-daily-aggregation: Group trade outcomes by UTC calendar day.

Python API Usage:
    from app.workspace.results.equity_chart_daily_chart import (
        EquityChartDailyChartService,
    )
    service = EquityChartDailyChartService()
    series = service.build_series(10000.0, trades)

CLI Usage:
    python -m app.cli results daily-chart --strategy-id Strat_01
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.workspace.results.app_results import to_float, to_int

logger = get_logger(__name__)

DAY_MS = 86_400_000


@dataclass(frozen=True, slots=True)
class DailyPlPoint:
    """Aggregated daily profit/loss and cumulative balance point."""

    day_epoch_ms: int
    net_pl: float
    cumulative_balance: float
    trade_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert daily point to dictionary representation."""
        return {
            "day_epoch_ms": self.day_epoch_ms,
            "net_pl": self.net_pl,
            "cumulative_balance": self.cumulative_balance,
            "trade_count": self.trade_count,
        }


class EquityChartDailyChartService:
    """Daily P&L subchart series generator service."""

    @classmethod
    def build_series(
        cls,
        initial_capital: float,
        trades: Sequence[dict[str, Any]],
    ) -> tuple[DailyPlPoint, ...]:
        """Group trades by calendar day and produce sorted DailyPlPoint series."""
        day_trades: dict[int, list[float]] = {}
        for t in trades:
            ts = to_int(
                t.get(
                    "close_time_ms",
                    t.get("close_time", t.get("timestamp_ms", 0)),
                )
            )
            day_floor = (ts // DAY_MS) * DAY_MS
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            day_trades.setdefault(day_floor, []).append(pl)

        sorted_days = sorted(day_trades.keys())
        cumulative_balance = initial_capital
        points: list[DailyPlPoint] = []

        for d in sorted_days:
            pls = day_trades[d]
            net_pl = sum(pls)
            cumulative_balance += net_pl
            points.append(
                DailyPlPoint(
                    day_epoch_ms=d,
                    net_pl=round(net_pl, 2),
                    cumulative_balance=round(cumulative_balance, 2),
                    trade_count=len(pls),
                )
            )

        logger.info(
            "FR-results-daily-aggregation: aggregated %d days from %d trades",
            len(points),
            len(trades),
        )
        return tuple(points)
