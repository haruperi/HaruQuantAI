"""WinLossCountByDayChart trade analysis chart snippet.

Description:
    Computes winning and losing trade counts by day of month.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossCountByDayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-count-day:
      Computes winning and losing trade counts by day of month.

Python API Usage:
    from app.extend.trade_analysis.win_loss_count_by_day_chart import (
        WinLossCountByDayChart,
    )
    chart = WinLossCountByDayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossCountByDayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossCountByDayChart(TradeAnalysisChart):
    """Win/Loss Count by Day chart matching StrategyQuant WinLossCountByDayChart."""

    name: str = "Win/Loss Count by Day"
    chart_id: str = "WinLossCountByDayChart"
    dimension: DimensionType = "DAY"
    metric: MetricType = "WIN_LOSS_COUNT"
    source_ref: str = "WinLossCountByDayChart.java"
