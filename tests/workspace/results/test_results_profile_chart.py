"""Unit tests for ResultsProfileChartService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_profile_chart import (
    ResultsProfileChartService,
    TradeProfilePath,
)


def _create_profile_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="ProfileStrategy",
        trades=(
            {
                "ticket": 1,
                "type": "BUY",
                "profit_loss": 100.0,
                "mae": 20.0,
                "mfe": 150.0,
            },
            {
                "ticket": 2,
                "type": "SELL",
                "profit_loss": -50.0,
                "mae": 60.0,
                "mfe": 10.0,
            },
            {
                "ticket": 3,
                "type": "BUY",
                "profit_loss": 80.0,
                "path": [0.0, -10.0, 50.0, 80.0],
            },
        ),
    )


class TestResultsProfileChartService:
    """Test suite for ResultsProfileChartService."""

    def test_get_paths_projection(self) -> None:
        """Verify excursion paths and quantile calculations."""
        service = ResultsProfileChartService()
        run_res = _create_profile_result("Strat_01")
        service.register_in_memory_result(run_res)

        resp = service.get_paths("p1", "Results", "Strat_01", unit="MONEY")
        payload = resp.data
        assert payload.result_key == "Main"
        assert payload.unit == "MONEY"
        assert len(payload.paths) == 3

        p1 = payload.paths[0]
        assert p1.ticket == 1
        assert p1.is_winner is True
        assert p1.points == (0.0, -20.0, 150.0, 100.0)

        p2 = payload.paths[1]
        assert p2.ticket == 2
        assert p2.is_winner is False
        assert p2.points == (0.0, -60.0, 10.0, -50.0)

        p3 = payload.paths[2]
        assert p3.ticket == 3
        assert p3.points == (0.0, -10.0, 50.0, 80.0)

        # Envelopes
        assert len(payload.mean_path) == 4
        assert len(payload.quantile_25) == 4
        assert len(payload.quantile_75) == 4

        d = payload.to_dict()
        assert len(d["paths"]) == 3
        assert len(d["mean_path"]) == 4

    def test_profile_chart_strategy_not_found(self) -> None:
        """Verify DomainError when strategy is not found."""
        service = ResultsProfileChartService()
        with pytest.raises(DomainError) as exc_info:
            service.get_paths("p1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"

    def test_profile_empty_trades(self) -> None:
        """Verify empty trades produce empty paths and envelopes."""
        service = ResultsProfileChartService()
        run_res = RunResult(
            result_id="res_empty",
            databank_id="Results",
            strategy_id="EmptyStrat",
            strategy_name="Empty",
            trades=(),
        )
        service.register_in_memory_result(run_res)

        resp = service.get_paths("p1", "Results", "EmptyStrat")
        assert len(resp.data.paths) == 0
        assert len(resp.data.mean_path) == 0

    def test_trade_profile_path_to_dict(self) -> None:
        """Verify TradeProfilePath to_dict."""
        path = TradeProfilePath(
            ticket=5, direction="BUY", is_winner=True, points=(0.0, 10.0, 20.0)
        )
        d = path.to_dict()
        assert d["ticket"] == 5
        assert d["points"] == [0.0, 10.0, 20.0]
