"""TradesByDayChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by day of month (1-31).
    Matches StrategyQuant SQ.TradeAnalysis.TradesByDayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-day:
      Counts executed trades grouped by day of month (1-31).

Python API Usage:
    from app.extend.trade_analysis.trades_by_day_chart import (
        TradesByDayChart,
    )
    chart = TradesByDayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByDayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByDayChart(TradeAnalysisChart):
    """Trades by Day of Month chart matching StrategyQuant TradesByDayChart."""

    name: str = "Trades by Day of Month"
    chart_id: str = "TradesByDayChart"
    dimension: DimensionType = "DAY"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByDayChart.java"
