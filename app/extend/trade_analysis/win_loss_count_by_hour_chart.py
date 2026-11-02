"""WinLossCountByHourChart trade analysis chart snippet.

Description:
    Computes winning and losing trade counts by hour of day.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossCountByHourChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-count-hour:
      Computes winning and losing trade counts by hour of day.

Python API Usage:
    from app.extend.trade_analysis.win_loss_count_by_hour_chart import (
        WinLossCountByHourChart,
    )
    chart = WinLossCountByHourChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossCountByHourChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossCountByHourChart(TradeAnalysisChart):
    """Win/Loss Count by Hour chart matching StrategyQuant WinLossCountByHourChart."""

    name: str = "Win/Loss Count by Hour"
    chart_id: str = "WinLossCountByHourChart"
    dimension: DimensionType = "HOUR"
    metric: MetricType = "WIN_LOSS_COUNT"
    source_ref: str = "WinLossCountByHourChart.java"
