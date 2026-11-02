"""Default with OpenDD overview template snippet (Stats/Overview cohort).

Description:
    Implements DefaultOpenDD overview template snippet matching StrategyQuant
    donor Overview/DefaultOpenDD.java with open drawdown metrics.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: Default with OpenDD template.

Key Capabilities:
    - FR-stats-overview-default-open-dd: Default with OpenDD metrics configuration.

Python API Usage:
    from app.extend.stats.overview.default_open_dd import DefaultOpenDD

    template = DefaultOpenDD()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template DefaultOpenDD
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.base import OverviewTemplate

logger = get_logger(__name__)


class DefaultOpenDD(OverviewTemplate):
    """Default with Open Drawdown overview statistics template."""

    def __init__(self) -> None:
        """Initialize Default with OpenDD overview template."""
        self.template_id = "DefaultOpenDD"
        self.name = "Default Open Drawdown"
        self.screenshot_name = "sqdefault_screenshot.jpg"
        self.html_template_name = "sqdefault_template.htm"
        self.use_pct = False
        self.include_portfolio_comparison = False
        self.use_open_dd = True
        self.metric_column_ids = (
            "NetProfit",
            "ProfitFactor",
            "ReturnOpenDDRatio",
            "OpenDrawdown",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "SharpeRatio",
        )
        self.source_ref = "Overview/DefaultOpenDD.java"
        logger.info(
            "FR-stats-overview-default-open-dd: initialized template_id=%s",
            self.template_id,
        )
