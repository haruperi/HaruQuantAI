"""PLbyTradeDurationChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss across duration buckets.
    Matches StrategyQuant SQ.TradeAnalysis.PLbyTradeDurationChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-duration:
      Aggregates realized trade profit/loss across duration buckets.

Python API Usage:
    from app.extend.trade_analysis.pl_by_trade_duration_chart import (
        PLbyTradeDurationChart,
    )
    chart = PLbyTradeDurationChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyTradeDurationChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyTradeDurationChart(TradeAnalysisChart):
    """Profit/Loss by Duration chart matching StrategyQuant PLbyTradeDurationChart."""

    name: str = "Profit/Loss by Duration"
    chart_id: str = "PLbyTradeDurationChart"
    dimension: DimensionType = "DURATION"
    metric: MetricType = "PL"
    source_ref: str = "PLbyTradeDurationChart.java"
