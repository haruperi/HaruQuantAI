"""Trade Analysis chart descriptors and evaluation catalog.

Description:
    Implements 27 concrete trade analysis chart definitions across temporal,
    duration, direction, and exit reason dimensions, computing P/L, trade counts,
    and win/loss distributions over executed trades.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-catalog: Catalog and evaluate 27 trade analysis charts
      across hours, weekdays, months, durations, directions, and close types.

Python API Usage:
    from app.extend.trade_analysis.charts import TradeAnalysisCatalog
    payload = TradeAnalysisCatalog.evaluate("PLbyHourChart", trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyHourChart
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal

from app.core.host.logging import get_logger
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)

DimensionType = Literal[
    "HOUR",
    "WEEKDAY",
    "DAY",
    "MONTH",
    "YEAR",
    "DURATION",
    "CLOSE_TYPE",
    "DIRECTION",
    "SEQUENCE",
]

MetricType = Literal["PL", "TRADE_COUNT", "WIN_LOSS_COUNT", "WIN_LOSS_PL"]

HOURS = [f"{h:02d}:00" for h in range(24)]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
DAYS_OF_MONTH = [str(d) for d in range(1, 32)]
DURATION_BUCKETS = ["<5m", "5-15m", "15-60m", "1-4h", "4-24h", ">24h"]
CLOSE_TYPES = [
    "SL",
    "PT",
    "Signal",
    "TrailingStop",
    "ExitAfterBars",
    "EndOfDay",
    "Other",
]
DIRECTIONS = ["Long", "Short"]


@dataclass(frozen=True, slots=True)
class TradeAnalysisChartDescriptor:
    """Descriptor defining dimensions and metrics for a trade analysis chart."""

    chart_id: str
    title: str
    dimension: DimensionType
    metric: MetricType
    source_ref: str


@dataclass(frozen=True, slots=True)
class TradeAnalysisPanePayload:
    """Aggregated chart categories and data series payload."""

    chart_id: str
    title: str
    dimension: str
    metric: str
    categories: tuple[str, ...]
    series: dict[str, tuple[float, ...]]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "chart_id": self.chart_id,
            "title": self.title,
            "dimension": self.dimension,
            "metric": self.metric,
            "categories": list(self.categories),
            "series": {k: list(v) for k, v in self.series.items()},
        }


DURATION_5M_SEC = 300
DURATION_15M_SEC = 900
DURATION_1H_SEC = 3600
DURATION_4H_SEC = 14400
DURATION_24H_SEC = 86400


class TradeAnalysisCatalog:
    """Catalog of all 27 Trade Analysis chart descriptors and evaluators."""

    DESCRIPTORS: ClassVar[dict[str, TradeAnalysisChartDescriptor]] = {
        "LongShortProfitLossChart": TradeAnalysisChartDescriptor(
            "LongShortProfitLossChart",
            "Profit/Loss by Direction",
            "DIRECTION",
            "PL",
            "LongShortProfitLossChart.java",
        ),
        "LongShortTradesChart": TradeAnalysisChartDescriptor(
            "LongShortTradesChart",
            "Trade Count by Direction",
            "DIRECTION",
            "TRADE_COUNT",
            "LongShortTradesChart.java",
        ),
        "PLChart": TradeAnalysisChartDescriptor(
            "PLChart", "Cumulative Profit/Loss", "SEQUENCE", "PL", "PLChart.java"
        ),
        "PLGrowthByDurationChart": TradeAnalysisChartDescriptor(
            "PLGrowthByDurationChart",
            "P/L Growth by Trade Duration",
            "DURATION",
            "PL",
            "PLGrowthByDurationChart.java",
        ),
        "PLLongChart": TradeAnalysisChartDescriptor(
            "PLLongChart",
            "Long Trade Profit/Loss",
            "SEQUENCE",
            "PL",
            "PLLongChart.java",
        ),
        "PLShortChart": TradeAnalysisChartDescriptor(
            "PLShortChart",
            "Short Trade Profit/Loss",
            "SEQUENCE",
            "PL",
            "PLShortChart.java",
        ),
        "PLbyDayChart": TradeAnalysisChartDescriptor(
            "PLbyDayChart",
            "Profit/Loss by Day of Month",
            "DAY",
            "PL",
            "PLbyDayChart.java",
        ),
        "PLbyHourChart": TradeAnalysisChartDescriptor(
            "PLbyHourChart", "Profit/Loss by Hour", "HOUR", "PL", "PLbyHourChart.java"
        ),
        "PLbyMonthChart": TradeAnalysisChartDescriptor(
            "PLbyMonthChart",
            "Profit/Loss by Month",
            "MONTH",
            "PL",
            "PLbyMonthChart.java",
        ),
        "PLbyTradeDurationChart": TradeAnalysisChartDescriptor(
            "PLbyTradeDurationChart",
            "Profit/Loss by Duration",
            "DURATION",
            "PL",
            "PLbyTradeDurationChart.java",
        ),
        "PLbyWeekdayChart": TradeAnalysisChartDescriptor(
            "PLbyWeekdayChart",
            "Profit/Loss by Weekday",
            "WEEKDAY",
            "PL",
            "PLbyWeekdayChart.java",
        ),
        "PLbyYearChart": TradeAnalysisChartDescriptor(
            "PLbyYearChart", "Profit/Loss by Year", "YEAR", "PL", "PLbyYearChart.java"
        ),
        "TradesByCloseTypeChart": TradeAnalysisChartDescriptor(
            "TradesByCloseTypeChart",
            "Trades by Close Type",
            "CLOSE_TYPE",
            "TRADE_COUNT",
            "TradesByCloseTypeChart.java",
        ),
        "TradesByDayChart": TradeAnalysisChartDescriptor(
            "TradesByDayChart",
            "Trades by Day of Month",
            "DAY",
            "TRADE_COUNT",
            "TradesByDayChart.java",
        ),
        "TradesByDurationChart": TradeAnalysisChartDescriptor(
            "TradesByDurationChart",
            "Trades by Duration",
            "DURATION",
            "TRADE_COUNT",
            "TradesByDurationChart.java",
        ),
        "TradesByHourChart": TradeAnalysisChartDescriptor(
            "TradesByHourChart",
            "Trades by Hour",
            "HOUR",
            "TRADE_COUNT",
            "TradesByHourChart.java",
        ),
        "TradesByMonthChart": TradeAnalysisChartDescriptor(
            "TradesByMonthChart",
            "Trades by Month",
            "MONTH",
            "TRADE_COUNT",
            "TradesByMonthChart.java",
        ),
        "TradesByWeekdayChart": TradeAnalysisChartDescriptor(
            "TradesByWeekdayChart",
            "Trades by Weekday",
            "WEEKDAY",
            "TRADE_COUNT",
            "TradesByWeekdayChart.java",
        ),
        "TradesByYearChart": TradeAnalysisChartDescriptor(
            "TradesByYearChart",
            "Trades by Year",
            "YEAR",
            "TRADE_COUNT",
            "TradesByYearChart.java",
        ),
        "WinLossCountByDayChart": TradeAnalysisChartDescriptor(
            "WinLossCountByDayChart",
            "Win/Loss Count by Day",
            "DAY",
            "WIN_LOSS_COUNT",
            "WinLossCountByDayChart.java",
        ),
        "WinLossCountByHourChart": TradeAnalysisChartDescriptor(
            "WinLossCountByHourChart",
            "Win/Loss Count by Hour",
            "HOUR",
            "WIN_LOSS_COUNT",
            "WinLossCountByHourChart.java",
        ),
        "WinLossCountByMonthChart": TradeAnalysisChartDescriptor(
            "WinLossCountByMonthChart",
            "Win/Loss Count by Month",
            "MONTH",
            "WIN_LOSS_COUNT",
            "WinLossCountByMonthChart.java",
        ),
        "WinLossCountByWeekdayChart": TradeAnalysisChartDescriptor(
            "WinLossCountByWeekdayChart",
            "Win/Loss Count by Weekday",
            "WEEKDAY",
            "WIN_LOSS_COUNT",
            "WinLossCountByWeekdayChart.java",
        ),
        "WinLossPLByDayChart": TradeAnalysisChartDescriptor(
            "WinLossPLByDayChart",
            "Win/Loss P/L by Day",
            "DAY",
            "WIN_LOSS_PL",
            "WinLossPLByDayChart.java",
        ),
        "WinLossPLByHourChart": TradeAnalysisChartDescriptor(
            "WinLossPLByHourChart",
            "Win/Loss P/L by Hour",
            "HOUR",
            "WIN_LOSS_PL",
            "WinLossPLByHourChart.java",
        ),
        "WinLossPLByMonthChart": TradeAnalysisChartDescriptor(
            "WinLossPLByMonthChart",
            "Win/Loss P/L by Month",
            "MONTH",
            "WIN_LOSS_PL",
            "WinLossPLByMonthChart.java",
        ),
        "WinLossPLByWeekdayChart": TradeAnalysisChartDescriptor(
            "WinLossPLByWeekdayChart",
            "Win/Loss P/L by Weekday",
            "WEEKDAY",
            "WIN_LOSS_PL",
            "WinLossPLByWeekdayChart.java",
        ),
    }

    @staticmethod
    def _get_duration_bucket(duration_sec: float) -> str:
        if duration_sec < DURATION_5M_SEC:
            return "<5m"
        if duration_sec < DURATION_15M_SEC:
            return "5-15m"
        if duration_sec < DURATION_1H_SEC:
            return "15-60m"
        if duration_sec < DURATION_4H_SEC:
            return "1-4h"
        if duration_sec < DURATION_24H_SEC:
            return "4-24h"
        return ">24h"

    @classmethod
    def _resolve_categories(
        cls,
        dimension: DimensionType,
        trades: Sequence[WhatIfRecord | Any],
    ) -> list[str]:
        """Resolve categorical x-axis labels."""
        dimension_map: dict[str, Sequence[str]] = {
            "HOUR": HOURS,
            "WEEKDAY": WEEKDAYS,
            "MONTH": MONTHS,
            "DAY": DAYS_OF_MONTH,
            "DURATION": DURATION_BUCKETS,
            "CLOSE_TYPE": CLOSE_TYPES,
            "DIRECTION": DIRECTIONS,
        }
        if dimension in dimension_map:
            return list(dimension_map[dimension])
        if dimension == "YEAR":
            return sorted(
                {
                    str(datetime.fromtimestamp(t.time_open_msc / 1000, tz=UTC).year)
                    for t in trades
                    if hasattr(t, "time_open_msc") and t.time_open_msc > 0
                }
            ) or ["2024", "2025"]
        return [f"#{i + 1}" for i in range(len(trades))] or ["#1"]

    @classmethod
    def _calculate_win_loss_count(
        cls,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
        dimension: DimensionType,
    ) -> dict[str, tuple[float, ...]]:
        win_counts = [0.0] * num_cats
        loss_counts = [0.0] * num_cats
        for t in trades:
            if getattr(t, "kind", "trade") != "trade":
                continue
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = cat_indices.get(cls._resolve_category(t, dimension))
            if idx is not None:
                if p >= 0:
                    win_counts[idx] += 1.0
                else:
                    loss_counts[idx] += 1.0
        return {"Wins": tuple(win_counts), "Losses": tuple(loss_counts)}

    @classmethod
    def _calculate_win_loss_pl(
        cls,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
        dimension: DimensionType,
    ) -> dict[str, tuple[float, ...]]:
        win_pl = [0.0] * num_cats
        loss_pl = [0.0] * num_cats
        for t in trades:
            if getattr(t, "kind", "trade") != "trade":
                continue
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = cat_indices.get(cls._resolve_category(t, dimension))
            if idx is not None:
                if p >= 0:
                    win_pl[idx] = round(win_pl[idx] + p, 2)
                else:
                    loss_pl[idx] = round(loss_pl[idx] + p, 2)
        return {"Profit": tuple(win_pl), "Loss": tuple(loss_pl)}

    @classmethod
    def _calculate_trade_count(
        cls,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
        dimension: DimensionType,
    ) -> dict[str, tuple[float, ...]]:
        counts = [0.0] * num_cats
        for t in trades:
            idx = cat_indices.get(cls._resolve_category(t, dimension))
            if idx is not None:
                counts[idx] += 1.0
        return {"Trades": tuple(counts)}

    @classmethod
    def _calculate_pl(
        cls,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
        dimension: DimensionType,
    ) -> dict[str, tuple[float, ...]]:
        pl_values = [0.0] * num_cats
        for i, t in enumerate(trades):
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = (
                i
                if dimension == "SEQUENCE" and i < num_cats
                else cat_indices.get(cls._resolve_category(t, dimension))
            )
            if idx is not None:
                pl_values[idx] = round(pl_values[idx] + p, 2)
        return {"NetProfit": tuple(pl_values)}

    @classmethod
    def _calculate_series(
        cls,
        descriptor: TradeAnalysisChartDescriptor,
        trades: Sequence[WhatIfRecord | Any],
        categories: list[str],
    ) -> dict[str, tuple[float, ...]]:
        """Compute series data values for the chart."""
        cat_indices = {cat: i for i, cat in enumerate(categories)}
        num_cats = len(categories)

        if descriptor.metric == "WIN_LOSS_COUNT":
            return cls._calculate_win_loss_count(
                trades, cat_indices, num_cats, descriptor.dimension
            )
        if descriptor.metric == "WIN_LOSS_PL":
            return cls._calculate_win_loss_pl(
                trades, cat_indices, num_cats, descriptor.dimension
            )
        if descriptor.metric == "TRADE_COUNT":
            return cls._calculate_trade_count(
                trades, cat_indices, num_cats, descriptor.dimension
            )
        return cls._calculate_pl(trades, cat_indices, num_cats, descriptor.dimension)

    @classmethod
    def evaluate(
        cls,
        chart_id: str,
        trades: Sequence[WhatIfRecord | Any],
    ) -> TradeAnalysisPanePayload:
        """Evaluate trade analysis chart on trade records sequence.

        Args:
            chart_id: One of the 27 registered chart IDs.
            trades: Sequence of trades to evaluate.

        Returns:
            TradeAnalysisPanePayload with categories and series.
        """
        descriptor = cls.DESCRIPTORS.get(chart_id)
        if descriptor is None:
            descriptor = TradeAnalysisChartDescriptor(
                chart_id, chart_id, "SEQUENCE", "PL", f"{chart_id}.java"
            )

        categories = cls._resolve_categories(descriptor.dimension, trades)
        series = cls._calculate_series(descriptor, trades, categories)

        logger.debug(
            "FR-trade-analysis-catalog: evaluated chart %s (%d categories)",
            chart_id,
            len(categories),
        )

        return TradeAnalysisPanePayload(
            chart_id=descriptor.chart_id,
            title=descriptor.title,
            dimension=descriptor.dimension,
            metric=descriptor.metric,
            categories=tuple(categories),
            series=series,
        )

    @classmethod
    def _resolve_category(cls, trade: Any, dimension: DimensionType) -> str:
        open_msc = getattr(trade, "time_open_msc", 0)
        close_msc = getattr(trade, "time_close_msc", open_msc)
        dt = (
            datetime.fromtimestamp(open_msc / 1000, tz=UTC)
            if open_msc > 0
            else datetime.now(tz=UTC)
        )

        mapping: dict[DimensionType, str] = {
            "HOUR": f"{dt.hour:02d}:00",
            "WEEKDAY": WEEKDAYS[dt.weekday()],
            "MONTH": MONTHS[dt.month - 1],
            "DAY": str(dt.day),
            "YEAR": str(dt.year),
            "DURATION": cls._get_duration_bucket(
                max(0.0, (close_msc - open_msc) / 1000.0)
            ),
            "CLOSE_TYPE": str(getattr(trade, "close_reason", "Signal") or "Signal"),
            "DIRECTION": "Long" if getattr(trade, "direction", 1) == 1 else "Short",
        }
        return mapping.get(dimension, "#1")
