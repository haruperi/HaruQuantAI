"""AW Shared Default overview template snippet (Stats/Overview cohort).

Description:
    Implements AWSharedDefault overview template snippet matching StrategyQuant
    donor Overview/AWSharedDefault.java.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: AW Shared Default template.

Key Capabilities:
    - FR-stats-overview-aw-shared-default: AW Shared Default metrics configuration.

Python API Usage:
    from app.extend.stats.overview.aw_shared_default import AWSharedDefault

    template = AWSharedDefault()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template AWSharedDefault
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.base import STANDARD_METRIC_COLUMNS, OverviewTemplate

logger = get_logger(__name__)


class AWSharedDefault(OverviewTemplate):
    """AW Shared Default overview statistics template."""

    def __init__(self) -> None:
        """Initialize AW Shared Default overview template."""
        self.template_id = "AWSharedDefault"
        self.name = "AW Shared Default"
        self.screenshot_name = "sqdefault_screenshot.jpg"
        self.html_template_name = "awshareddefault_template.htm"
        self.use_pct = False
        self.include_portfolio_comparison = False
        self.use_open_dd = False
        self.metric_column_ids = STANDARD_METRIC_COLUMNS
        self.source_ref = "Overview/AWSharedDefault.java"
        logger.info(
            "FR-stats-overview-aw-shared-default: initialized template_id=%s",
            self.template_id,
        )
