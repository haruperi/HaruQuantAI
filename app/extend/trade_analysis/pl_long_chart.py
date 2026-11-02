"""PLLongChart trade analysis chart snippet.

Description:
    Visualizes sequential profit/loss exclusively for long trades.
    Matches StrategyQuant SQ.TradeAnalysis.PLLongChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-long:
      Visualizes sequential profit/loss exclusively for long trades.

Python API Usage:
    from app.extend.trade_analysis.pl_long_chart import (
        PLLongChart,
    )
    chart = PLLongChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLLongChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLLongChart(TradeAnalysisChart):
    """Long Trade Profit/Loss chart matching StrategyQuant PLLongChart."""

    name: str = "Long Trade Profit/Loss"
    chart_id: str = "PLLongChart"
    dimension: DimensionType = "SEQUENCE"
    metric: MetricType = "PL"
    source_ref: str = "PLLongChart.java"
