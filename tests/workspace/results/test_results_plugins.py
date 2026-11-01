"""Unit tests for ResultsPluginsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_plugins import (
    ResultsPluginDescriptor,
    ResultsPluginsService,
)


def _create_plugins_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="SampleStrategy",
        metrics={"net_profit": 500.0, "profit_factor": 2.0},
        trades=({"ticket": 1, "profit_loss": 500.0},),
        parameters={"constituent_strategy_ids": ["s1", "s2"]},
        strategy_payload={
            "symbol": "EURUSD",
            "timeframe": "H1",
            "candles": [{"time": 1000, "close": 1.1}],
        },
    )


class TestResultsPluginsService:
    """Test suite for ResultsPluginsService."""

    def test_golden_fixture_create_and_query(self) -> None:
        """Verify creating custom plugin and querying result keys."""
        service = ResultsPluginsService()
        run_res = _create_plugins_result("Strat_01")
        service.register_in_memory_result(run_res, "Results")

        # Create custom plugin
        resp = service.create_plugin(
            "OrderHeatmap", "Order Heatmap", "<div/>", "console.log('init')"
        )
        assert resp.data.plugin_id == "OrderHeatmap"
        assert resp.data.title == "Order Heatmap"
        assert not resp.data.is_builtin

        # Query result keys
        keys = service.get_strategy_result_keys("p1", "Results", "Strat_01")
        assert keys == ("Main", "Portfolio")

    def test_builtin_plugins_immutable(self) -> None:
        """Verify built-in plugins cannot be renamed or deleted."""
        service = ResultsPluginsService()
        with pytest.raises(DomainError) as exc_info:
            service.rename_plugin("Overview", "NewOverview")
        assert exc_info.value.code == "RESULTS_BUILTIN_PLUGIN_IMMUTABLE"

        with pytest.raises(DomainError) as exc_info:
            service.delete_plugin("Overview")
        assert exc_info.value.code == "RESULTS_BUILTIN_PLUGIN_IMMUTABLE"

    def test_read_only_accessors(self) -> None:
        """Verify read-only data accessors for stats, orders, settings, and candles."""
        service = ResultsPluginsService()
        run_res = _create_plugins_result("Strat_01")
        service.register_in_memory_result(run_res, "Results")

        stats = service.get_stats("p1", "Results", "Strat_01")
        assert stats["net_profit"] == 500.0

        orders = service.get_orders("p1", "Results", "Strat_01")
        assert len(orders) == 1

        settings = service.get_settings("p1", "Results", "Strat_01")
        assert settings["symbol"] == "EURUSD"

        candles = service.get_candles("p1", "Results", "Strat_01", "EURUSD", "H1")
        assert len(candles) == 1

        symbols = service.list_data_symbols()
        assert "EURUSD" in symbols

        strats = service.list_databank_strategies("p1", "Results")
        assert strats == ["Strat_01"]

    def test_descriptor_to_dict(self) -> None:
        """Verify ResultsPluginDescriptor to_dict."""
        desc = ResultsPluginDescriptor(
            plugin_id="p1",
            title="P1",
            source_html="<html/>",
            source_js="js",
            is_builtin=False,
        )
        d = desc.to_dict()
        assert d["plugin_id"] == "p1"
        assert d["title"] == "P1"
