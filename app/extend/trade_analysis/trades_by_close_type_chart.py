"""TradesByCloseTypeChart trade analysis chart snippet.

Description:
    Counts trades grouped by closing reason (SL, PT, Signal).
    Matches StrategyQuant SQ.TradeAnalysis.TradesByCloseTypeChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-trades-by-close-type:
      Counts trades grouped by closing reason (SL, PT, Signal).

Python API Usage:
    from app.extend.trade_analysis.trades_by_close_type_chart import (
        TradesByCloseTypeChart,
    )
    chart = TradesByCloseTypeChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart TradesByCloseTypeChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class TradesByCloseTypeChart(TradeAnalysisChart):
    """Trades by Close Type chart matching StrategyQuant TradesByCloseTypeChart."""

    name: str = "Trades by Close Type"
    chart_id: str = "TradesByCloseTypeChart"
    dimension: DimensionType = "CLOSE_TYPE"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "TradesByCloseTypeChart.java"
