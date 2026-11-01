"""Unit tests for ResultsExploreService."""

from __future__ import annotations

from app.core.lib.errors import JSONValue
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_explore import ResultsExploreService


class TestResultsExploreService:
    """Test suite for ResultsExploreService."""

    def test_explore_golden_fixture_sample_breakdown(self) -> None:
        """Verify 10 IS trades (+400) and 5 OOS trades (+200) yields 15 total trades."""
        service = ResultsExploreService()
        is_trades: list[dict[str, JSONValue]] = [
            {"profit_loss": 40.0, "sample_type": "InSample"} for _ in range(10)
        ]
        oos_trades: list[dict[str, JSONValue]] = [
            {"profit_loss": 40.0, "sample_type": "OutOfSample"} for _ in range(5)
        ]
        sample = RunResult(
            result_id="res_exp",
            databank_id="Results",
            strategy_id="Strat_Exp",
            strategy_name="Strat_Exp",
            trades=tuple(is_trades + oos_trades),
            parameters={"RSI_Period": 14},
        )
        service.register_in_memory_result(sample)

        resp = service.get_info("proj_1", "Results", "Strat_Exp")
        info = resp.data
        assert info.total_trades == 15
        assert info.net_profit == 600.0
        assert info.parameters == {"RSI_Period": 14}

        breakdown = info.sample_breakdown
        assert breakdown["InSample"]["net_profit"] == 400.0
        assert breakdown["InSample"]["total_trades"] == 10.0
        assert breakdown["OutOfSample"]["net_profit"] == 200.0
        assert breakdown["OutOfSample"]["total_trades"] == 5.0
        assert breakdown["FullSample"]["net_profit"] == 600.0

        d = info.to_dict()
        assert d["total_trades"] == 15
