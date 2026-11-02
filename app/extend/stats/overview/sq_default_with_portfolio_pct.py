"""SQ Default with Portfolio Pct overview template snippet (Stats/Overview cohort).

Description:
    Implements SQDefaultWithPortfolioPct overview template snippet matching
    donor Overview/SQDefaultWithPortfolioPct.java, extending SQDefaultPct.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: SQ Default with Portfolio Pct template.

Key Capabilities:
    - FR-stats-overview-sq-default-portfolio-pct: Portfolio comparison with pct metrics.

Python API Usage:
    from app.extend.stats.overview.sq_default_with_portfolio_pct import (
        SQDefaultWithPortfolioPct,
    )

    template = SQDefaultWithPortfolioPct()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template SQDefaultWithPortfolioPct
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.overview.sq_default_pct import SQDefaultPct

logger = get_logger(__name__)


class SQDefaultWithPortfolioPct(SQDefaultPct):
    """SQ Default with Portfolio (%) overview statistics template."""

    def __init__(self) -> None:
        """Initialize SQ Default with Portfolio Pct overview template."""
        super().__init__()
        self.template_id = "SQDefaultWithPortfolioPct"
        self.name = "SQ Default with Portfolio (%)"
        self.screenshot_name = "sqdefault_screenshot_portfolio.jpg"
        self.html_template_name = "sqdefault_template.htm"
        self.use_pct = True
        self.include_portfolio_comparison = True
        self.use_open_dd = False
        self.source_ref = "Overview/SQDefaultWithPortfolioPct.java"
        logger.info(
            "FR-stats-overview-sq-default-portfolio-pct: initialized template_id=%s",
            self.template_id,
        )
