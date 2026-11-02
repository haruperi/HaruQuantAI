"""LongShortTradesChart trade analysis chart snippet.

Description:
    Computes trade count distribution between long and short trades.
    Matches StrategyQuant SQ.TradeAnalysis.LongShortTradesChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-long-short-trades:
      Computes trade count distribution between long and short trades.

Python API Usage:
    from app.extend.trade_analysis.long_short_trades_chart import (
        LongShortTradesChart,
    )
    chart = LongShortTradesChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart LongShortTradesChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class LongShortTradesChart(TradeAnalysisChart):
    """Long vs Short trades chart matching StrategyQuant LongShortTradesChart."""

    name: str = "Long vs Short trades"
    chart_id: str = "LongShortTradesChart"
    dimension: DimensionType = "DIRECTION"
    metric: MetricType = "TRADE_COUNT"
    source_ref: str = "LongShortTradesChart.java"
