"""PLShortChart trade analysis chart snippet.

Description:
    Visualizes sequential profit/loss exclusively for short trades.
    Matches StrategyQuant SQ.TradeAnalysis.PLShortChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-short:
      Visualizes sequential profit/loss exclusively for short trades.

Python API Usage:
    from app.extend.trade_analysis.pl_short_chart import (
        PLShortChart,
    )
    chart = PLShortChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLShortChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLShortChart(TradeAnalysisChart):
    """Short Trade Profit/Loss chart matching StrategyQuant PLShortChart."""

    name: str = "Short Trade Profit/Loss"
    chart_id: str = "PLShortChart"
    dimension: DimensionType = "SEQUENCE"
    metric: MetricType = "PL"
    source_ref: str = "PLShortChart.java"
