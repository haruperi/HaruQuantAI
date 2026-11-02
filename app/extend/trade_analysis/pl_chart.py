"""PLChart trade analysis chart snippet.

Description:
    Visualizes sequential cumulative profit/loss trade by trade.
    Matches StrategyQuant SQ.TradeAnalysis.PLChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-sequence:
      Visualizes sequential cumulative profit/loss trade by trade.

Python API Usage:
    from app.extend.trade_analysis.pl_chart import (
        PLChart,
    )
    chart = PLChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLChart(TradeAnalysisChart):
    """Cumulative Profit/Loss chart matching StrategyQuant PLChart."""

    name: str = "Cumulative Profit/Loss"
    chart_id: str = "PLChart"
    dimension: DimensionType = "SEQUENCE"
    metric: MetricType = "PL"
    source_ref: str = "PLChart.java"
