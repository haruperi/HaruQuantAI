"""Trade Analysis chart descriptors and evaluation catalog.

Description:
    Implements 27 concrete trade analysis chart definitions across temporal,
    duration, direction, sequence, and exit reason dimensions, computing P/L,
    trade counts, and win/loss distributions over executed trades matching
    donor SQ.TradeAnalysis snippets.

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
from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.extend.trade_analysis.base import (
    CLOSE_TYPES,
    DAYS_OF_MONTH,
    DIRECTIONS,
    DURATION_1H_SEC,
    DURATION_4H_SEC,
    DURATION_5M_SEC,
    DURATION_15M_SEC,
    DURATION_24H_SEC,
    DURATION_BUCKETS,
    HOURS,
    MONTHS,
    WEEKDAYS,
    DimensionType,
    MetricType,
    TradeAnalysisChart,
    TradeAnalysisChartDescriptor,
    TradeAnalysisPanePayload,
)
from app.extend.trade_analysis.long_short_profit_loss_chart import (
    LongShortProfitLossChart,
)
from app.extend.trade_analysis.long_short_trades_chart import LongShortTradesChart
from app.extend.trade_analysis.pl_by_day_chart import PLbyDayChart
from app.extend.trade_analysis.pl_by_hour_chart import PLbyHourChart
from app.extend.trade_analysis.pl_by_month_chart import PLbyMonthChart
from app.extend.trade_analysis.pl_by_trade_duration_chart import (
    PLbyTradeDurationChart,
)
from app.extend.trade_analysis.pl_by_weekday_chart import PLbyWeekdayChart
from app.extend.trade_analysis.pl_by_year_chart import PLbyYearChart
from app.extend.trade_analysis.pl_chart import PLChart
from app.extend.trade_analysis.pl_growth_by_duration_chart import (
    PLGrowthByDurationChart,
)
from app.extend.trade_analysis.pl_long_chart import PLLongChart
from app.extend.trade_analysis.pl_short_chart import PLShortChart
from app.extend.trade_analysis.trades_by_close_type_chart import (
    TradesByCloseTypeChart,
)
from app.extend.trade_analysis.trades_by_day_chart import TradesByDayChart
from app.extend.trade_analysis.trades_by_duration_chart import (
    TradesByDurationChart,
)
from app.extend.trade_analysis.trades_by_hour_chart import TradesByHourChart
from app.extend.trade_analysis.trades_by_month_chart import TradesByMonthChart
from app.extend.trade_analysis.trades_by_weekday_chart import TradesByWeekdayChart
from app.extend.trade_analysis.trades_by_year_chart import TradesByYearChart
from app.extend.trade_analysis.win_loss_count_by_day_chart import (
    WinLossCountByDayChart,
)
from app.extend.trade_analysis.win_loss_count_by_hour_chart import (
    WinLossCountByHourChart,
)
from app.extend.trade_analysis.win_loss_count_by_month_chart import (
    WinLossCountByMonthChart,
)
from app.extend.trade_analysis.win_loss_count_by_weekday_chart import (
    WinLossCountByWeekdayChart,
)
from app.extend.trade_analysis.win_loss_pl_by_day_chart import WinLossPLByDayChart
from app.extend.trade_analysis.win_loss_pl_by_hour_chart import WinLossPLByHourChart
from app.extend.trade_analysis.win_loss_pl_by_month_chart import (
    WinLossPLByMonthChart,
)
from app.extend.trade_analysis.win_loss_pl_by_weekday_chart import (
    WinLossPLByWeekdayChart,
)
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)

CHART_CLASSES: tuple[type[TradeAnalysisChart], ...] = (
    LongShortProfitLossChart,
    LongShortTradesChart,
    PLChart,
    PLGrowthByDurationChart,
    PLLongChart,
    PLShortChart,
    PLbyDayChart,
    PLbyHourChart,
    PLbyMonthChart,
    PLbyTradeDurationChart,
    PLbyWeekdayChart,
    PLbyYearChart,
    TradesByCloseTypeChart,
    TradesByDayChart,
    TradesByDurationChart,
    TradesByHourChart,
    TradesByMonthChart,
    TradesByWeekdayChart,
    TradesByYearChart,
    WinLossCountByDayChart,
    WinLossCountByHourChart,
    WinLossCountByMonthChart,
    WinLossCountByWeekdayChart,
    WinLossPLByDayChart,
    WinLossPLByHourChart,
    WinLossPLByMonthChart,
    WinLossPLByWeekdayChart,
)

_INSTANCES: dict[str, TradeAnalysisChart] = {
    cls().chart_id: cls() for cls in CHART_CLASSES
}


class TradeAnalysisCatalog:
    """Catalog of all 27 Trade Analysis chart descriptors and evaluators."""

    DESCRIPTORS: ClassVar[dict[str, TradeAnalysisChartDescriptor]] = {
        chart_id: instance.descriptor() for chart_id, instance in _INSTANCES.items()
    }

    @classmethod
    def get_chart(cls, chart_id: str) -> TradeAnalysisChart:
        """Look up or instantiate a chart by ID."""
        chart = _INSTANCES.get(chart_id)
        if chart is None:
            logger.debug(
                "FR-trade-analysis-catalog: unknown chart %s, fallback to PLChart",
                chart_id,
            )
            return PLChart(
                name=chart_id,
                chart_id=chart_id,
                source_ref=f"{chart_id}.java",
            )
        return chart

    @classmethod
    def list_charts(cls) -> list[TradeAnalysisChartDescriptor]:
        """Return all 27 chart descriptors."""
        return list(cls.DESCRIPTORS.values())

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
        chart = cls.get_chart(chart_id)
        return chart.evaluate(trades)


__all__ = [
    "CLOSE_TYPES",
    "DAYS_OF_MONTH",
    "DIRECTIONS",
    "DURATION_1H_SEC",
    "DURATION_4H_SEC",
    "DURATION_5M_SEC",
    "DURATION_15M_SEC",
    "DURATION_24H_SEC",
    "DURATION_BUCKETS",
    "HOURS",
    "MONTHS",
    "WEEKDAYS",
    "DimensionType",
    "LongShortProfitLossChart",
    "LongShortTradesChart",
    "MetricType",
    "PLChart",
    "PLGrowthByDurationChart",
    "PLLongChart",
    "PLShortChart",
    "PLbyDayChart",
    "PLbyHourChart",
    "PLbyMonthChart",
    "PLbyTradeDurationChart",
    "PLbyWeekdayChart",
    "PLbyYearChart",
    "TradeAnalysisCatalog",
    "TradeAnalysisChart",
    "TradeAnalysisChartDescriptor",
    "TradeAnalysisPanePayload",
    "TradesByCloseTypeChart",
    "TradesByDayChart",
    "TradesByDurationChart",
    "TradesByHourChart",
    "TradesByMonthChart",
    "TradesByWeekdayChart",
    "TradesByYearChart",
    "WinLossCountByDayChart",
    "WinLossCountByHourChart",
    "WinLossCountByMonthChart",
    "WinLossCountByWeekdayChart",
    "WinLossPLByDayChart",
    "WinLossPLByHourChart",
    "WinLossPLByMonthChart",
    "WinLossPLByWeekdayChart",
]
