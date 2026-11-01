"""Tests for ResultsSysParamPermutationService."""

from app.workspace.optimizer.results_optimization_profile import OptimizationRunRow
from app.workspace.optimizer.results_sys_param_permutation import (
    ResultsSysParamPermutationService,
)


class TestResultsSysParamPermutationService:
    """Test suite verifying SPP statistics, percentiles, and table slicing."""

    def test_golden_fixture_spp_stats(self) -> None:
        """Verify golden fixture: 5 runs [100, 200, 300, 400, 500] yield median==300 and mean==300."""
        service = ResultsSysParamPermutationService()
        runs = [
            OptimizationRunRow(
                run_index=i,
                parameters={"Param": i},
                metrics={"NetProfit": val},
                passed=True,
            )
            for i, val in enumerate([100.0, 200.0, 300.0, 400.0, 500.0], start=1)
        ]
        service.set_runs("Strat_01", runs)

        resp = service.get_projection("Strat_01")
        proj = resp.data
        assert proj.total_permutations == 5
        assert proj.profitable_runs_pct == 100.0

        np_row = next(r for r in proj.summary_rows if r.metric_id == "NetProfit")
        assert np_row.median_value == 300.0
        assert np_row.mean_value == 300.0
        assert np_row.percentile_5 >= 100.0
        assert np_row.percentile_95 <= 500.0

    def test_get_table_pagination(self) -> None:
        """Verify get_table pagination offset and limit."""
        service = ResultsSysParamPermutationService()
        runs = [
            OptimizationRunRow(
                run_index=i,
                parameters={"Param": i},
                metrics={"NetProfit": float(i * 10)},
                passed=True,
            )
            for i in range(10)
        ]
        service.set_runs("Strat_01", runs)

        resp = service.get_table("Strat_01", offset=2, limit=3)
        assert len(resp.data) == 3
        assert resp.data[0].run_index == 2
        assert resp.data[-1].run_index == 4
