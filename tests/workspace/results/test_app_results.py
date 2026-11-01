"""Unit tests for AppResultsService and selection projection."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.app_results import AppResultsService


def _create_sample_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name=f"Name_{strategy_id}",
        metrics={"net_profit": 500.0, "symbol": "EURUSD", "timeframe": "H1"},
        strategy_payload={
            "symbol": "EURUSD",
            "timeframe": "H1",
            "data_items": [
                {
                    "result_key": "Main",
                    "label": "Main",
                    "symbol": "EURUSD",
                    "timeframe": "H1",
                },
                {
                    "result_key": "Additional_1",
                    "label": "Additional_1",
                    "symbol": "GBPUSD",
                    "timeframe": "H1",
                },
            ],
        },
    )


class TestAppResultsService:
    """Test suite for AppResultsService."""

    def test_get_data_items_golden_fixture(self) -> None:
        """Verify golden fixture projection for Strat_01."""
        service = AppResultsService()
        sample = _create_sample_result("Strat_01")
        service.register_in_memory_result("Results", sample)

        resp = service.get_data_items("proj_1", "Results", "Strat_01")
        state = resp.data
        assert state.strategy_id == "Strat_01"
        assert state.active_result_key == "Main"
        assert state.active_tab_id == "overview"
        assert len(state.data_items) == 2
        assert state.data_items[0].result_key == "Main"
        assert state.data_items[0].symbol == "EURUSD"
        assert state.data_items[1].result_key == "Additional_1"
        assert state.data_items[1].symbol == "GBPUSD"

        # Check serialization helper
        d = state.to_dict()
        assert d["strategy_id"] == "Strat_01"
        assert len(d["data_items"]) == 2

    def test_get_data_items_missing_strategy(self) -> None:
        """Verify DomainError(RESULTS_STRATEGY_NOT_FOUND) when strategy missing."""
        service = AppResultsService()
        with pytest.raises(DomainError) as exc_info:
            service.get_data_items("proj_1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"

    def test_ordering_with_portfolio_and_subkeys(self) -> None:
        """Verify deterministic ordering: Main first, Portfolio second, others sorted."""
        service = AppResultsService()
        sample = RunResult(
            result_id="res_port",
            databank_id="Results",
            strategy_id="Strat_Port",
            strategy_name="PortfolioStrat",
            strategy_payload={
                "data_items": [
                    {"result_key": "Z_Sub"},
                    {"result_key": "Portfolio", "is_portfolio": True},
                    {"result_key": "A_Sub"},
                    {"result_key": "Main"},
                ]
            },
        )
        service.register_in_memory_result("Results", sample)

        resp = service.get_data_items("proj_1", "Results", "Strat_Port")
        keys = tuple(item.result_key for item in resp.data.data_items)
        assert keys == ("Main", "Portfolio", "A_Sub", "Z_Sub")
