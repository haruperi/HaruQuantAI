"""WinLossPLByWeekdayChart trade analysis chart snippet.

Description:
    Computes separate profit and loss totals by day of week.
    Matches StrategyQuant SQ.TradeAnalysis.WinLossPLByWeekdayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-win-loss-pl-weekday:
      Computes separate profit and loss totals by day of week.

Python API Usage:
    from app.extend.trade_analysis.win_loss_pl_by_weekday_chart import (
        WinLossPLByWeekdayChart,
    )
    chart = WinLossPLByWeekdayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart WinLossPLByWeekdayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class WinLossPLByWeekdayChart(TradeAnalysisChart):
    """Win/Loss P/L by Weekday chart matching StrategyQuant WinLossPLByWeekdayChart."""

    name: str = "Win/Loss P/L by Weekday"
    chart_id: str = "WinLossPLByWeekdayChart"
    dimension: DimensionType = "WEEKDAY"
    metric: MetricType = "WIN_LOSS_PL"
    source_ref: str = "WinLossPLByWeekdayChart.java"
