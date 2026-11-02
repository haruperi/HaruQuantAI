"""WinLossPLByMonthChart trade analysis chart snippet.

Description:
    Computes separate profit and loss totals by calendar month.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossPLByMonthChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-pl-month:
      Computes separate profit and loss totals by calendar month.

Python API Usage:
    from app.extend.trade_analysis.win_loss_pl_by_month_chart import (
        WinLossPLByMonthChart,
    )
    chart = WinLossPLByMonthChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossPLByMonthChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossPLByMonthChart(TradeAnalysisChart):
    """Win/Loss P/L by Month chart matching StrategyQuant WinLossPLByMonthChart."""

    name: str = "Win/Loss P/L by Month"
    chart_id: str = "WinLossPLByMonthChart"
    dimension: DimensionType = "MONTH"
    metric: MetricType = "WIN_LOSS_PL"
    source_ref: str = "WinLossPLByMonthChart.java"
