"""WinLossCountByMonthChart trade analysis chart snippet.

Description:
    Computes winning and losing trade counts by calendar month.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossCountByMonthChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-count-month:
      Computes winning and losing trade counts by calendar month.

Python API Usage:
    from app.extend.trade_analysis.win_loss_count_by_month_chart import (
        WinLossCountByMonthChart,
    )
    chart = WinLossCountByMonthChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossCountByMonthChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossCountByMonthChart(TradeAnalysisChart):
    """Win/Loss Count by Month chart matching StrategyQuant WinLossCountByMonthChart."""

    name: str = "Win/Loss Count by Month"
    chart_id: str = "WinLossCountByMonthChart"
    dimension: DimensionType = "MONTH"
    metric: MetricType = "WIN_LOSS_COUNT"
    source_ref: str = "WinLossCountByMonthChart.java"
