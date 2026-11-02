"""SQ Default with Portfolio overview template snippet (Stats/Overview cohort).

Description:
    Implements SQDefaultWithPortfolio overview template snippet matching StrategyQuant
    donor Overview/SQDefaultWithPortfolio.java, extending SQDefault.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: SQ Default with Portfolio template.

Key Capabilities:
    - FR-stats-overview-sq-default-portfolio: Portfolio comparison configuration.

Python API Usage:
    from app.extend.stats.overview.sq_default_with_portfolio import (
        SQDefaultWithPortfolio,
    )

    template = SQDefaultWithPortfolio()
    rows = template.render_rows(stats)

CLI Usage:
    python -m app.cli extend stats overview --template SQDefaultWithPortfolio
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.stats.overview.sq_default import SQDefault

logger = get_logger(__name__)


class SQDefaultWithPortfolio(SQDefault):
    """SQ Default with Portfolio overview statistics template."""

    def __init__(self) -> None:
        """Initialize SQ Default with Portfolio overview template."""
        super().__init__()
        self.template_id = "SQDefaultWithPortfolio"
        self.name = "SQ Default with Portfolio"
        self.screenshot_name = "sqdefault_screenshot_portfolio.jpg"
        self.html_template_name = "sqdefault_template.htm"
        self.use_pct = False
        self.include_portfolio_comparison = True
        self.use_open_dd = False
        self.source_ref = "Overview/SQDefaultWithPortfolio.java"
        logger.info(
            "FR-stats-overview-sq-default-portfolio: initialized template_id=%s",
            self.template_id,
        )
