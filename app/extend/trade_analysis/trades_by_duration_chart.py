"""TradesByDurationChart trade analysis chart snippet.

Description:
    Counts executed trades grouped by duration bucket.
    Matches StrategyQuant SQ.TradeAnalysis.TradesByDurationChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-duration:
      Counts executed trades grouped by duration bucket.

Python API Usage:
    from app.extend.trade_analysis.trades_by_duration_chart import (
        TradesByDurationChart,
    )
    chart = TradesByDurationChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByDurationChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByDurationChart(TradeAnalysisChart):
    """Trades by Duration chart matching StrategyQuant TradesByDurationChart."""

    name: str = "Trades by Duration"
    chart_id: str = "TradesByDurationChart"
    dimension: DimensionType = "DURATION"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByDurationChart.java"
