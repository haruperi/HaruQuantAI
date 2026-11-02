"""WinLossCountByWeekdayChart trade analysis chart snippet.

Description:
    Computes winning and losing trade counts by day of week.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossCountByWeekdayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-count-weekday:
      Computes winning and losing trade counts by day of week.

Python API Usage:
    from app.extend.trade_analysis.win_loss_count_by_weekday_chart import (
        WinLossCountByWeekdayChart,
    )
    chart = WinLossCountByWeekdayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossCountByWeekdayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossCountByWeekdayChart(TradeAnalysisChart):
    """Win/Loss Count by Weekday chart matching StrategyQuant."""

    name: str = "Win/Loss Count by Weekday"
    chart_id: str = "WinLossCountByWeekdayChart"
    dimension: DimensionType = "WEEKDAY"
    metric: MetricType = "WIN_LOSS_COUNT"
    source_ref: str = "WinLossCountByWeekdayChart.java"
