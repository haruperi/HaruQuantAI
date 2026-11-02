"""TradeStation Overview template snippet (Stats/Overview cohort).

Description:
    Implements TSOverview overview template snippet matching StrategyQuant
    donor Overview/TSOverview.java with 28-metric TradeStation layout.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: TradeStation Overview template.

Key Capabilities:
    - FR-stats-overview-ts-overview: TS Overview metrics configuration.

Python API Usage:
    from app.extend.stats.overview.ts_overview import TSOverview

    template = TSOverview()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template TSOverview
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.base import OverviewTemplate

logger = get_logger(__name__)


class TSOverview(OverviewTemplate):
    """TradeStation Overview statistics template."""

    def __init__(self) -> None:
        """Initialize TradeStation Overview template."""
        self.template_id = "TSOverview"
        self.name = "TradeStation Overview"
        self.screenshot_name = "ts_screenshot.jpg"
        self.html_template_name = "ts_template.htm"
        self.use_pct = False
        self.include_portfolio_comparison = False
        self.use_open_dd = False
        self.metric_column_ids = (
            "NetProfit",
            "GrossProfit",
            "GrossLoss",
            "ProfitFactor",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "WinLossRatio",
            "MaxProfit",
            "MaxLoss",
        )
        self.source_ref = "Overview/TSOverview.java"
        logger.info(
            "FR-stats-overview-ts-overview: initialized template_id=%s",
            self.template_id,
        )
