"""WinLossPLByHourChart trade analysis chart snippet.

Description:
    Computes separate profit and loss totals by hour of day.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossPLByHourChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-pl-hour:
      Computes separate profit and loss totals by hour of day.

Python API Usage:
    from app.extend.trade_analysis.win_loss_pl_by_hour_chart import (
        WinLossPLByHourChart,
    )
    chart = WinLossPLByHourChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossPLByHourChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossPLByHourChart(TradeAnalysisChart):
    """Win/Loss P/L by Hour chart matching StrategyQuant WinLossPLByHourChart."""

    name: str = "Win/Loss P/L by Hour"
    chart_id: str = "WinLossPLByHourChart"
    dimension: DimensionType = "HOUR"
    metric: MetricType = "WIN_LOSS_PL"
    source_ref: str = "WinLossPLByHourChart.java"
