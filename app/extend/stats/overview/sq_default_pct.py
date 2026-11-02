"""SQ Default Pct overview template snippet (Stats/Overview cohort).

Description:
    Implements SQDefaultPct overview template snippet matching StrategyQuant
    donor Overview/SQDefaultPct.java with percentage-based performance.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: SQ Default Pct template.

Key Capabilities:
    - FR-stats-overview-sq-default-pct: SQ Default Pct metrics configuration.

Python API Usage:
    from app.extend.stats.overview.sq_default_pct import SQDefaultPct

    template = SQDefaultPct()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template SQDefaultPct
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.base import OverviewTemplate

logger = get_logger(__name__)


class SQDefaultPct(OverviewTemplate):
    """StrategyQuant Default (%) overview statistics template."""

    def __init__(self) -> None:
        """Initialize SQ Default Pct overview template."""
        self.template_id = "SQDefaultPct"
        self.name = "StrategyQuant Default (%)"
        self.screenshot_name = "sqdefault_screenshot.jpg"
        self.html_template_name = "sqdefault_template.htm"
        self.use_pct = True
        self.include_portfolio_comparison = False
        self.use_open_dd = False
        self.metric_column_ids = (
            "NetProfitInPct",
            "ProfitFactor",
            "ReturnDDRatio",
            "DrawdownPct",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "SharpeRatio",
        )
        self.source_ref = "Overview/SQDefaultPct.java"
        logger.info(
            "FR-stats-overview-sq-default-pct: initialized template_id=%s",
            self.template_id,
        )
