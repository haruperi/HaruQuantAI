"""TradesByHourChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by hour of entry (0-23).
    Matches StrategyQuant SQ.TradeAnalysis.TradesByHourChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-hour:
      Counts executed trades grouped by hour of entry (0-23).

Python API Usage:
    from app.extend.trade_analysis.trades_by_hour_chart import (
        TradesByHourChart,
    )
    chart = TradesByHourChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByHourChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByHourChart(TradeAnalysisChart):
    """Trades by Hour chart matching StrategyQuant TradesByHourChart."""

    name: str = "Trades by Hour"
    chart_id: str = "TradesByHourChart"
    dimension: DimensionType = "HOUR"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByHourChart.java"
