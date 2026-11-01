"""Unit tests for OverviewStatsCatalog (Stats/Overview cohort)."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.extend.columns.base import StrategyStatsSnapshot
from app.extend.stats import (
    OVERVIEW_TEMPLATES,
    OverviewStatsCatalog,
    OverviewStatsTemplate,
)


class TestOverviewStatsCatalog:
    """Test suite for Overview templates and row rendering."""

    def test_registered_templates_count_and_keys(self) -> None:
        """Verify all 7 donor Overview templates are registered."""
        assert len(OVERVIEW_TEMPLATES) == 7
        expected_keys = {
            "AWSharedDefault",
            "DefaultOpenDD",
            "SQDefault",
            "SQDefaultPct",
            "SQDefaultWithPortfolio",
            "SQDefaultWithPortfolioPct",
            "TSOverview",
        }
        assert set(OVERVIEW_TEMPLATES.keys()) == expected_keys

        templates_list = OverviewStatsCatalog.list_templates()
        assert len(templates_list) == 7

    def test_get_template_and_not_found(self) -> None:
        """Verify get template returns valid descriptor or raises DomainError."""
        tmpl = OverviewStatsCatalog.get("SQDefault")
        assert tmpl.template_id == "SQDefault"
        assert tmpl.use_pct is False

        with pytest.raises(DomainError) as exc_info:
            OverviewStatsCatalog.get("UnknownTemplate")
        assert exc_info.value.code == "STATS_TEMPLATE_NOT_FOUND"

    def test_render_rows_all_long_short(self) -> None:
        """Verify rendering metric rows across directional subsets."""
        snapshot = StrategyStatsSnapshot(
            trades=(
                {"ticket": 1, "type": "BUY", "profit_loss": 300.0},
                {"ticket": 2, "type": "SELL", "profit_loss": -100.0},
            ),
            initial_deposit=10000.0,
            strategy_name="StatsStrat",
        )

        rows = OverviewStatsCatalog.render_rows("SQDefault", snapshot)
        assert len(rows) >= 8

        net_profit_row = next(r for r in rows if r.metric_id == "NetProfit")
        assert net_profit_row.all_trades == 200.0
        assert net_profit_row.long_trades == 300.0
        assert net_profit_row.short_trades == -100.0

    def test_template_to_dict(self) -> None:
        """Verify OverviewStatsTemplate to_dict."""
        tmpl = OverviewStatsTemplate(
            template_id="T1",
            label="Template 1",
            use_pct=True,
            include_portfolio_comparison=False,
            use_open_dd=False,
            metric_column_ids=("NetProfit",),
            source_ref="ref",
        )
        d = tmpl.to_dict()
        assert d["template_id"] == "T1"
        assert d["use_pct"] is True
