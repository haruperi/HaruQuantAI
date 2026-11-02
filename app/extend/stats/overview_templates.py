"""Overview statistics templates and row renderers (Stats/Overview cohort).

Description:
    Implements OverviewStatsCatalog and registers all 7 donor Overview
    templates (AWSharedDefault, DefaultOpenDD, SQDefault, SQDefaultPct,
    SQDefaultWithPortfolio, SQDefaultWithPortfolioPct, TSOverview),
    rendering structured OverviewMetricRow projections via modular snippet classes.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: Strategy Overview templates catalog.

Key Capabilities:
    - FR-stats-overview-templates: Retrieve templates and render metrics rows.

Python API Usage:
    from app.extend.stats.overview_templates import OverviewStatsCatalog

    template = OverviewStatsCatalog.get("SQDefault")
    rows = OverviewStatsCatalog.render_rows("SQDefault", stats)

CLI Usage:
    python -m app.cli extend stats overview --list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.extend.columns.base import StrategyStatsSnapshot
from app.extend.stats.base import STANDARD_METRIC_COLUMNS, OverviewTemplate
from app.extend.stats.overview import (
    AWSharedDefault,
    DefaultOpenDD,
    SQDefault,
    SQDefaultPct,
    SQDefaultWithPortfolio,
    SQDefaultWithPortfolioPct,
    TSOverview,
)
from app.workspace.results.results_overview import OverviewMetricRow

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OverviewStatsTemplate:
    """Descriptor defining a template layout for strategy Overview metrics."""

    template_id: str
    label: str
    use_pct: bool
    include_portfolio_comparison: bool
    use_open_dd: bool
    metric_column_ids: tuple[str, ...]
    source_ref: str

    def to_dict(self) -> dict[str, Any]:
        """Convert template descriptor to dictionary."""
        return {
            "template_id": self.template_id,
            "label": self.label,
            "use_pct": self.use_pct,
            "include_portfolio_comparison": self.include_portfolio_comparison,
            "use_open_dd": self.use_open_dd,
            "metric_column_ids": list(self.metric_column_ids),
            "source_ref": self.source_ref,
        }


# Modular snippet class registry
OVERVIEW_SNIPPET_CLASSES: dict[str, type[OverviewTemplate]] = {
    "AWSharedDefault": AWSharedDefault,
    "DefaultOpenDD": DefaultOpenDD,
    "SQDefault": SQDefault,
    "SQDefaultPct": SQDefaultPct,
    "SQDefaultWithPortfolio": SQDefaultWithPortfolio,
    "SQDefaultWithPortfolioPct": SQDefaultWithPortfolioPct,
    "TSOverview": TSOverview,
}

# Concrete snippet instances
OVERVIEW_SNIPPETS: dict[str, OverviewTemplate] = {
    key: cls() for key, cls in OVERVIEW_SNIPPET_CLASSES.items()
}

# Register all 7 donor Overview template descriptors for backward compatibility
OVERVIEW_TEMPLATES: dict[str, OverviewStatsTemplate] = {
    key: snippet.to_template_descriptor() for key, snippet in OVERVIEW_SNIPPETS.items()
}


class OverviewStatsCatalog:
    """Catalog of Overview templates providing template lookup and row rendering."""

    @classmethod
    def list_templates(cls) -> tuple[OverviewStatsTemplate, ...]:
        """List all 7 registered Overview template descriptors."""
        return tuple(OVERVIEW_TEMPLATES.values())

    @classmethod
    def list_snippets(cls) -> tuple[OverviewTemplate, ...]:
        """List all 7 registered Overview snippet instances."""
        return tuple(OVERVIEW_SNIPPETS.values())

    @classmethod
    def get(cls, template_id: str) -> OverviewStatsTemplate:
        """Lookup template descriptor by ID."""
        if template_id not in OVERVIEW_TEMPLATES:
            raise DomainError(
                code="STATS_TEMPLATE_NOT_FOUND",
                message=f"Overview template '{template_id}' not found",
                details={"template_id": template_id},
            )
        return OVERVIEW_TEMPLATES[template_id]

    @classmethod
    def get_snippet(cls, template_id: str) -> OverviewTemplate:
        """Lookup snippet instance by ID."""
        if template_id not in OVERVIEW_SNIPPETS:
            raise DomainError(
                code="STATS_TEMPLATE_NOT_FOUND",
                message=f"Overview template '{template_id}' not found",
                details={"template_id": template_id},
            )
        return OVERVIEW_SNIPPETS[template_id]

    @classmethod
    def render_rows(
        cls, template_id: str, stats: StrategyStatsSnapshot
    ) -> tuple[OverviewMetricRow, ...]:
        """Render OverviewMetricRow sequence for template across All/Long/Short."""
        snippet = cls.get_snippet(template_id)
        logger.info(
            "FR-stats-overview-templates: rendering template=%s with %d metrics",
            template_id,
            len(snippet.metric_column_ids),
        )
        return snippet.render_rows(stats)


__all__ = [
    "OVERVIEW_SNIPPETS",
    "OVERVIEW_SNIPPET_CLASSES",
    "OVERVIEW_TEMPLATES",
    "STANDARD_METRIC_COLUMNS",
    "OverviewStatsCatalog",
    "OverviewStatsTemplate",
]
