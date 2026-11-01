"""Unit tests for ResultsEquityChartService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_equity_chart import (
    EquityCurvePoint,
    ResultsEquityChartService,
)


def _create_chart_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="ChartStrategy",
        trades=(
            {
                "ticket": 1,
                "profit_loss": 500.0,
                "mae": 100.0,
                "type": "BUY",
                "open_time_ms": 1_000_000,
                "close_time_ms": 1_100_000,
                "sample_type": "IS",
            },
            {
                "ticket": 2,
                "profit_loss": -200.0,
                "mae": 250.0,
                "type": "SELL",
                "open_time_ms": 1_200_000,
                "close_time_ms": 1_300_000,
                "sample_type": "IS",
            },
            {
                "ticket": 3,
                "profit_loss": 300.0,
                "mae": 50.0,
                "type": "BUY",
                "open_time_ms": 1_400_000,
                "close_time_ms": 1_500_000,
                "sample_type": "OOS",
            },
        ),
        strategy_payload={"initial_capital": 10000.0},
    )


class TestResultsEquityChartService:
    """Test suite for ResultsEquityChartService."""

    def test_equity_chart_projection_both_directions(self) -> None:
        """Verify equity projection with IS/OOS sample boundary and drawdowns."""
        service = ResultsEquityChartService()
        run_res = _create_chart_result("Strat_01")
        service.register_in_memory_result(run_res)

        resp = service.get_projection("p1", "Results", "Strat_01", direction="BOTH")
        proj = resp.data
        assert proj.result_key == "Main"
        assert proj.initial_capital == 10000.0
        assert len(proj.points) == 4  # 1 anchor + 3 trades

        anchor = proj.points[0]
        assert anchor.index == 0
        assert anchor.balance == 10000.0
        assert anchor.drawdown_money == 0.0

        p1 = proj.points[1]
        assert p1.balance == 10500.0
        assert p1.drawdown_money == 0.0

        p2 = proj.points[2]
        assert p2.balance == 10300.0
        assert p2.drawdown_money == -200.0
        assert p2.open_equity == 10050.0  # 10300 - 250

        p3 = proj.points[3]
        assert p3.balance == 10600.0
        assert p3.drawdown_money == 0.0
        assert p3.sample_type == "OOS"

        assert len(proj.sample_boundaries) == 1
        assert proj.sample_boundaries[0] == ("OOS", 3)

        d = proj.to_dict()
        assert len(d["points"]) == 4

    def test_equity_chart_filtering_direction(self) -> None:
        """Verify filtering for LONG and SHORT trades only."""
        service = ResultsEquityChartService()
        run_res = _create_chart_result("Strat_01")
        service.register_in_memory_result(run_res)

        long_resp = service.get_projection(
            "p1", "Results", "Strat_01", direction="LONG"
        )
        assert len(long_resp.data.points) == 3  # anchor + 2 BUY trades

        short_resp = service.get_projection(
            "p1", "Results", "Strat_01", direction="SHORT"
        )
        assert len(short_resp.data.points) == 2  # anchor + 1 SELL trade

    def test_equity_chart_not_found(self) -> None:
        """Verify DomainError when strategy is not found."""
        service = ResultsEquityChartService()
        with pytest.raises(DomainError) as exc_info:
            service.get_projection("p1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"

    def test_equity_curve_point_to_dict(self) -> None:
        """Verify EquityCurvePoint serialization."""
        pt = EquityCurvePoint(
            index=1,
            timestamp_ms=1000,
            balance=10500.0,
            open_equity=10400.0,
            drawdown_money=-100.0,
            drawdown_pct=-0.95,
            sample_type="IS",
        )
        d = pt.to_dict()
        assert d["index"] == 1
        assert d["drawdown_money"] == -100.0
