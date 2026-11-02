"""TradesByYearChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by calendar year.
    Matches StrategyQuant SQ.TradeAnalysis.TradesByYearChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-year:
      Counts executed trades grouped by calendar year.

Python API Usage:
    from app.extend.trade_analysis.trades_by_year_chart import (
        TradesByYearChart,
    )
    chart = TradesByYearChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByYearChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByYearChart(TradeAnalysisChart):
    """Trades by Year chart matching StrategyQuant TradesByYearChart."""

    name: str = "Trades by Year"
    chart_id: str = "TradesByYearChart"
    dimension: DimensionType = "YEAR"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByYearChart.java"
