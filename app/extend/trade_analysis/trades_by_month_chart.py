"""TradesByMonthChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by calendar month (Jan-Dec).
    Matches StrategyQuant SQ.TradeAnalysis.TradesByMonthChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-month:
      Counts executed trades grouped by calendar month (Jan-Dec).

Python API Usage:
    from app.extend.trade_analysis.trades_by_month_chart import (
        TradesByMonthChart,
    )
    chart = TradesByMonthChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByMonthChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByMonthChart(TradeAnalysisChart):
    """Trades by Month chart matching StrategyQuant TradesByMonthChart."""

    name: str = "Trades by Month"
    chart_id: str = "TradesByMonthChart"
    dimension: DimensionType = "MONTH"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByMonthChart.java"
