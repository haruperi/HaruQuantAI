"""Base class for StrategyQuant Overview statistics templates (Stats/Overview cohort).

Description:
    Defines the abstract base class OverviewTemplate for StrategyQuant
    Overview statistics templates, encapsulating metadata and row rendering logic.

Purpose:
    FEAT-EXTEND-STATS-OVERVIEW: Strategy Overview templates base class.

Key Capabilities:
    - FR-stats-overview-base: Base template contract and metric row generation.

Python API Usage:
    from app.extend.stats.base import OverviewTemplate

    class CustomOverview(OverviewTemplate):
        ...

CLI Usage:
    python -m app.cli extend stats overview --list
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from app.core.host.logging import get_logger
from app.extend.columns.base import StrategyStatsSnapshot
from app.extend.columns.databanks import DatabankColumnEvaluator
from app.workspace.results.results_overview import OverviewMetricRow

if TYPE_CHECKING:
    from app.extend.stats.overview_templates import OverviewStatsTemplate

logger = get_logger(__name__)

STANDARD_METRIC_COLUMNS: tuple[str, ...] = (
    "NetProfit",
    "ProfitFactor",
    "ReturnDDRatio",
    "Drawdown",
    "NumberOfTrades",
    "WinningPct",
    "AvgTrade",
    "SharpeRatio",
    "MaxProfit",
    "MaxLoss",
)


class OverviewTemplate(ABC):
    """Abstract base class for all StrategyQuant Overview statistic templates."""

    template_id: str
    name: str
    screenshot_name: str
    html_template_name: str
    use_pct: bool
    include_portfolio_comparison: bool
    use_open_dd: bool
    metric_column_ids: tuple[str, ...]
    source_ref: str

    def render_rows(
        self, stats: StrategyStatsSnapshot
    ) -> tuple[OverviewMetricRow, ...]:
        """Render OverviewMetricRow sequence for this template across All/Long/Short."""
        logger.info(
            "FR-stats-overview-base: rendering template=%s with %d metrics",
            self.template_id,
            len(self.metric_column_ids),
        )

        rows: list[OverviewMetricRow] = []
        for col_id in self.metric_column_ids:
            all_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="Both"
            )
            long_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="BUY"
            )
            short_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="SELL"
            )
            unit = "%" if self.use_pct and "Pct" in col_id else "$"

            rows.append(
                OverviewMetricRow(
                    metric_id=col_id,
                    label=col_id,
                    all_trades=all_val,
                    long_trades=long_val,
                    short_trades=short_val,
                    unit=unit,
                )
            )

        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        """Convert template descriptor to dictionary representation."""
        return {
            "template_id": self.template_id,
            "label": self.name,
            "screenshot_name": self.screenshot_name,
            "html_template_name": self.html_template_name,
            "use_pct": self.use_pct,
            "include_portfolio_comparison": self.include_portfolio_comparison,
            "use_open_dd": self.use_open_dd,
            "metric_column_ids": list(self.metric_column_ids),
            "source_ref": self.source_ref,
        }

    def to_template_descriptor(self) -> OverviewStatsTemplate:
        """Create legacy OverviewStatsTemplate descriptor."""
        from app.extend.stats.overview_templates import OverviewStatsTemplate

        return OverviewStatsTemplate(
            template_id=self.template_id,
            label=self.name,
            use_pct=self.use_pct,
            include_portfolio_comparison=self.include_portfolio_comparison,
            use_open_dd=self.use_open_dd,
            metric_column_ids=self.metric_column_ids,
            source_ref=self.source_ref,
        )
