"""SQ Default overview template snippet (Stats/Overview cohort).

Description:
    Implements SQDefault overview template snippet matching StrategyQuant
    donor Overview/SQDefault.java.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: SQ Default template.

Key Capabilities:
    - FR-stats-overview-sq-default: SQ Default metrics configuration.

Python API Usage:
    from app.extend.stats.overview.sq_default import SQDefault

    template = SQDefault()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template SQDefault
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.base import STANDARD_METRIC_COLUMNS, OverviewTemplate

logger = get_logger(__name__)


class SQDefault(OverviewTemplate):
    """StrategyQuant Default overview statistics template."""

    def __init__(self) -> None:
        """Initialize SQ Default overview template."""
        self.template_id = "SQDefault"
        self.name = "StrategyQuant Default"
        self.screenshot_name = "sqdefault_screenshot.jpg"
        self.html_template_name = "sqdefault_template.htm"
        self.use_pct = False
        self.include_portfolio_comparison = False
        self.use_open_dd = False
        self.metric_column_ids = STANDARD_METRIC_COLUMNS
        self.source_ref = "Overview/SQDefault.java"
        logger.info(
            "FR-stats-overview-sq-default: initialized template_id=%s",
            self.template_id,
        )
