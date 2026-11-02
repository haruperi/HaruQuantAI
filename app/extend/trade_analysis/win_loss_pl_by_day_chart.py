"""WinLossPLByDayChart trade analysis chart snippet.

Description:
    Computes separate profit and loss totals by day of month.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossPLByDayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-pl-day:
      Computes separate profit and loss totals by day of month.

Python API Usage:
    from app.extend.trade_analysis.win_loss_pl_by_day_chart import (
        WinLossPLByDayChart,
    )
    chart = WinLossPLByDayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossPLByDayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossPLByDayChart(TradeAnalysisChart):
    """Win/Loss P/L by Day chart matching StrategyQuant WinLossPLByDayChart."""

    name: str = "Win/Loss P/L by Day"
    chart_id: str = "WinLossPLByDayChart"
    dimension: DimensionType = "DAY"
    metric: MetricType = "WIN_LOSS_PL"
    source_ref: str = "WinLossPLByDayChart.java"
