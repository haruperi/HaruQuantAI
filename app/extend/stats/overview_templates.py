"""Overview statistics templates and row renderers (Stats/Overview cohort).

Description:
    Implements OverviewStatsCatalog and registers all 7 donor Overview
    templates (AWSharedDefault, DefaultOpenDD, SQDefault, SQDefaultPct,
    SQDefaultWithPortfolio, SQDefaultWithPortfolioPct, TSOverview),
    rendering structured OverviewMetricRow projections.

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
from app.extend.columns.databanks import DatabankColumnEvaluator
from app.workspace.results.results_overview import OverviewMetricRow

logger = get_logger(__name__)

STANDARD_METRIC_COLUMNS = (
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


# Register all 7 donor Overview templates
OVERVIEW_TEMPLATES: dict[str, OverviewStatsTemplate] = {
    "AWSharedDefault": OverviewStatsTemplate(
        template_id="AWSharedDefault",
        label="AW Shared Default",
        use_pct=False,
        include_portfolio_comparison=False,
        use_open_dd=False,
        metric_column_ids=STANDARD_METRIC_COLUMNS,
        source_ref="Overview/AWSharedDefault.java",
    ),
    "DefaultOpenDD": OverviewStatsTemplate(
        template_id="DefaultOpenDD",
        label="Default Open Drawdown",
        use_pct=False,
        include_portfolio_comparison=False,
        use_open_dd=True,
        metric_column_ids=(
            "NetProfit",
            "ProfitFactor",
            "ReturnOpenDDRatio",
            "OpenDrawdown",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "SharpeRatio",
        ),
        source_ref="Overview/DefaultOpenDD.java",
    ),
    "SQDefault": OverviewStatsTemplate(
        template_id="SQDefault",
        label="StrategyQuant Default",
        use_pct=False,
        include_portfolio_comparison=False,
        use_open_dd=False,
        metric_column_ids=STANDARD_METRIC_COLUMNS,
        source_ref="Overview/SQDefault.java",
    ),
    "SQDefaultPct": OverviewStatsTemplate(
        template_id="SQDefaultPct",
        label="StrategyQuant Default (%)",
        use_pct=True,
        include_portfolio_comparison=False,
        use_open_dd=False,
        metric_column_ids=(
            "NetProfitInPct",
            "ProfitFactor",
            "ReturnDDRatio",
            "DrawdownPct",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "SharpeRatio",
        ),
        source_ref="Overview/SQDefaultPct.java",
    ),
    "SQDefaultWithPortfolio": OverviewStatsTemplate(
        template_id="SQDefaultWithPortfolio",
        label="SQ Default with Portfolio",
        use_pct=False,
        include_portfolio_comparison=True,
        use_open_dd=False,
        metric_column_ids=STANDARD_METRIC_COLUMNS,
        source_ref="Overview/SQDefaultWithPortfolio.java",
    ),
    "SQDefaultWithPortfolioPct": OverviewStatsTemplate(
        template_id="SQDefaultWithPortfolioPct",
        label="SQ Default with Portfolio (%)",
        use_pct=True,
        include_portfolio_comparison=True,
        use_open_dd=False,
        metric_column_ids=(
            "NetProfitInPct",
            "ProfitFactor",
            "ReturnDDRatio",
            "DrawdownPct",
            "NumberOfTrades",
            "WinningPct",
            "AvgTrade",
            "SharpeRatio",
        ),
        source_ref="Overview/SQDefaultWithPortfolioPct.java",
    ),
    "TSOverview": OverviewStatsTemplate(
        template_id="TSOverview",
        label="TradeStation Overview",
        use_pct=False,
        include_portfolio_comparison=False,
        use_open_dd=False,
        metric_column_ids=(
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
        ),
        source_ref="Overview/TSOverview.java",
    ),
}


class OverviewStatsCatalog:
    """Catalog of Overview templates providing template lookup and row rendering."""

    @classmethod
    def list_templates(cls) -> tuple[OverviewStatsTemplate, ...]:
        """List all 7 registered Overview templates."""
        return tuple(OVERVIEW_TEMPLATES.values())

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
    def render_rows(
        cls, template_id: str, stats: StrategyStatsSnapshot
    ) -> tuple[OverviewMetricRow, ...]:
        """Render OverviewMetricRow sequence for template across All/Long/Short."""
        tmpl = cls.get(template_id)
        logger.info(
            "FR-stats-overview-templates: rendering template=%s with %d metrics",
            template_id,
            len(tmpl.metric_column_ids),
        )

        rows: list[OverviewMetricRow] = []
        for col_id in tmpl.metric_column_ids:
            all_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="Both"
            )
            long_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="BUY"
            )
            short_val = DatabankColumnEvaluator.evaluate(
                col_id, stats, sample_type="FullSample", direction="SELL"
            )
            unit = "%" if tmpl.use_pct and "Pct" in col_id else "$"

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
