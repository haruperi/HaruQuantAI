"""TradesByWeekdayChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by day of week.
    Matches StrategyQuant SQ.TradeAnalysis.TradesByWeekdayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-weekday:
      Counts executed trades grouped by day of week.

Python API Usage:
    from app.extend.trade_analysis.trades_by_weekday_chart import (
        TradesByWeekdayChart,
    )
    chart = TradesByWeekdayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByWeekdayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByWeekdayChart(TradeAnalysisChart):
    """Trades by Weekday chart matching StrategyQuant TradesByWeekdayChart."""

    name: str = "Trades by Weekday"
    chart_id: str = "TradesByWeekdayChart"
    dimension: DimensionType = "WEEKDAY"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByWeekdayChart.java"
