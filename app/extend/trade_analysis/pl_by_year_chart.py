"""PLbyYearChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss by calendar year.
    Matches StrategyQuant SQ.TradeAnalysis.PLbyYearChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-year:
      Aggregates realized trade profit/loss by calendar year.

Python API Usage:
    from app.extend.trade_analysis.pl_by_year_chart import (
        PLbyYearChart,
    )
    chart = PLbyYearChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyYearChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyYearChart(TradeAnalysisChart):
    """Profit/Loss by Year chart matching StrategyQuant PLbyYearChart."""

    name: str = "Profit/Loss by Year"
    chart_id: str = "PLbyYearChart"
    dimension: DimensionType = "YEAR"
    metric: MetricType = "PL"
    source_ref: str = "PLbyYearChart.java"
