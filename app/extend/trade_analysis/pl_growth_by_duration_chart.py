"""PLGrowthByDurationChart trade analysis chart snippet.

Description:
    Visualizes cumulative profit/loss growth by trade duration.
    Matches StrategyQuant SQ.TradeAnalysis.PLGrowthByDurationChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-growth-duration:
      Visualizes cumulative profit/loss growth by trade duration.

Python API Usage:
    from app.extend.trade_analysis.pl_growth_by_duration_chart import (
        PLGrowthByDurationChart,
    )
    chart = PLGrowthByDurationChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLGrowthByDurationChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLGrowthByDurationChart(TradeAnalysisChart):
    """P/L Growth by Duration chart matching StrategyQuant."""

    name: str = "P/L Growth by Trade Duration"
    chart_id: str = "PLGrowthByDurationChart"
    dimension: DimensionType = "DURATION"
    metric: MetricType = "PL"
    source_ref: str = "PLGrowthByDurationChart.java"
