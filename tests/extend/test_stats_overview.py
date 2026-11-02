"""Unit tests for Overview statistics templates (Stats/Overview cohort)."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.extend.columns.base import StrategyStatsSnapshot
from app.extend.stats import (
    OVERVIEW_SNIPPET_CLASSES,
    OVERVIEW_SNIPPETS,
    OVERVIEW_TEMPLATES,
    AWSharedDefault,
    DefaultOpenDD,
    OverviewStatsCatalog,
    OverviewStatsTemplate,
    OverviewTemplate,
    SQDefault,
    SQDefaultPct,
    SQDefaultWithPortfolio,
    SQDefaultWithPortfolioPct,
    TSOverview,
)


class TestOverviewStatsCatalog:
    """Test suite for Overview templates catalog and row rendering."""

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
        assert set(OVERVIEW_SNIPPET_CLASSES.keys()) == expected_keys
        assert set(OVERVIEW_SNIPPETS.keys()) == expected_keys

        templates_list = OverviewStatsCatalog.list_templates()
        assert len(templates_list) == 7

        snippets_list = OverviewStatsCatalog.list_snippets()
        assert len(snippets_list) == 7

    def test_get_template_and_not_found(self) -> None:
        """Verify get template returns valid descriptor or raises DomainError."""
        tmpl = OverviewStatsCatalog.get("SQDefault")
        assert tmpl.template_id == "SQDefault"
        assert tmpl.use_pct is False

        with pytest.raises(DomainError) as exc_info:
            OverviewStatsCatalog.get("UnknownTemplate")
        assert exc_info.value.code == "STATS_TEMPLATE_NOT_FOUND"

    def test_get_snippet_and_not_found(self) -> None:
        """Verify get snippet returns valid instance or raises DomainError."""
        snippet = OverviewStatsCatalog.get_snippet("SQDefault")
        assert snippet.template_id == "SQDefault"
        assert isinstance(snippet, SQDefault)

        with pytest.raises(DomainError) as exc_info:
            OverviewStatsCatalog.get_snippet("NonExistentSnippet")
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
        assert d["metric_column_ids"] == ["NetProfit"]


class TestOverviewSnippets:
    """Test suite for individual Overview snippet classes and inheritance."""

    def test_aw_shared_default_metadata(self) -> None:
        """Verify AWSharedDefault attributes and descriptor conversion."""
        snippet = AWSharedDefault()
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "AWSharedDefault"
        assert snippet.name == "AW Shared Default"
        assert snippet.screenshot_name == "sqdefault_screenshot.jpg"
        assert snippet.html_template_name == "awshareddefault_template.htm"
        assert snippet.use_pct is False
        assert snippet.include_portfolio_comparison is False
        assert snippet.use_open_dd is False
        assert snippet.source_ref == "Overview/AWSharedDefault.java"

        desc = snippet.to_template_descriptor()
        assert desc.template_id == "AWSharedDefault"
        assert desc.label == "AW Shared Default"

        data = snippet.to_dict()
        assert data["template_id"] == "AWSharedDefault"
        assert data["label"] == "AW Shared Default"
        assert data["source_ref"] == "Overview/AWSharedDefault.java"

    def test_default_open_dd_metadata(self) -> None:
        """Verify DefaultOpenDD attributes."""
        snippet = DefaultOpenDD()
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "DefaultOpenDD"
        assert snippet.name == "Default Open Drawdown"
        assert snippet.use_open_dd is True
        assert "OpenDrawdown" in snippet.metric_column_ids
        assert "ReturnOpenDDRatio" in snippet.metric_column_ids

    def test_sq_default_metadata(self) -> None:
        """Verify SQDefault attributes."""
        snippet = SQDefault()
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "SQDefault"
        assert snippet.name == "StrategyQuant Default"
        assert snippet.screenshot_name == "sqdefault_screenshot.jpg"
        assert snippet.html_template_name == "sqdefault_template.htm"
        assert snippet.use_pct is False

    def test_sq_default_pct_metadata(self) -> None:
        """Verify SQDefaultPct attributes."""
        snippet = SQDefaultPct()
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "SQDefaultPct"
        assert snippet.name == "StrategyQuant Default (%)"
        assert snippet.use_pct is True
        assert "NetProfitInPct" in snippet.metric_column_ids
        assert "DrawdownPct" in snippet.metric_column_ids

    def test_sq_default_with_portfolio_inheritance(self) -> None:
        """Verify SQDefaultWithPortfolio inherits from SQDefault."""
        snippet = SQDefaultWithPortfolio()
        assert isinstance(snippet, SQDefault)
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "SQDefaultWithPortfolio"
        assert snippet.name == "SQ Default with Portfolio"
        assert snippet.screenshot_name == "sqdefault_screenshot_portfolio.jpg"
        assert snippet.include_portfolio_comparison is True
        assert snippet.use_pct is False

    def test_sq_default_with_portfolio_pct_inheritance(self) -> None:
        """Verify SQDefaultWithPortfolioPct inherits from SQDefaultPct."""
        snippet = SQDefaultWithPortfolioPct()
        assert isinstance(snippet, SQDefaultPct)
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "SQDefaultWithPortfolioPct"
        assert snippet.name == "SQ Default with Portfolio (%)"
        assert snippet.screenshot_name == "sqdefault_screenshot_portfolio.jpg"
        assert snippet.include_portfolio_comparison is True
        assert snippet.use_pct is True

    def test_ts_overview_metadata(self) -> None:
        """Verify TSOverview attributes and column ids."""
        snippet = TSOverview()
        assert isinstance(snippet, OverviewTemplate)
        assert snippet.template_id == "TSOverview"
        assert snippet.name == "TradeStation Overview"
        assert snippet.screenshot_name == "ts_screenshot.jpg"
        assert snippet.html_template_name == "ts_template.htm"
        assert "GrossProfit" in snippet.metric_column_ids
        assert "GrossLoss" in snippet.metric_column_ids
        assert "WinLossRatio" in snippet.metric_column_ids

    def test_snippet_render_rows_pct_unit(self) -> None:
        """Verify render_rows assigns '%' unit to Pct metrics in use_pct template."""
        snippet = SQDefaultPct()
        snapshot = StrategyStatsSnapshot(
            trades=(
                {"ticket": 1, "type": "BUY", "profit_loss": 500.0},
                {"ticket": 2, "type": "SELL", "profit_loss": -200.0},
            ),
            initial_deposit=10000.0,
            strategy_name="PctStrat",
        )
        rows = snippet.render_rows(snapshot)
        pct_row = next(r for r in rows if r.metric_id == "NetProfitInPct")
        assert pct_row.unit == "%"
        assert pct_row.all_trades == 3.0
