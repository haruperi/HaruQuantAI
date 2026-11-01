"""Tests for ResultsOptimizationProfileService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.results_optimization_profile import (
    OptimizationRunRow,
    ResultsOptimizationProfileService,
)


class TestResultsOptimizationProfileService:
    """Test suite verifying optimization profile grids, views, and CSV export."""

    def test_golden_fixture_grid_and_csv(self) -> None:
        """Verify golden fixture: 4 runs over p1 (10, 20) and p2 (1, 2) project 2x2 z_matrix and 5-line CSV."""
        service = ResultsOptimizationProfileService()
        runs = [
            OptimizationRunRow(
                run_index=1,
                parameters={"p1": 10.0, "p2": 1.0},
                metrics={"NetProfit": 100.0},
                passed=True,
            ),
            OptimizationRunRow(
                run_index=2,
                parameters={"p1": 20.0, "p2": 1.0},
                metrics={"NetProfit": 150.0},
                passed=True,
            ),
            OptimizationRunRow(
                run_index=3,
                parameters={"p1": 10.0, "p2": 2.0},
                metrics={"NetProfit": 120.0},
                passed=True,
            ),
            OptimizationRunRow(
                run_index=4,
                parameters={"p1": 20.0, "p2": 2.0},
                metrics={"NetProfit": 180.0},
                passed=True,
            ),
        ]
        service.set_mock_runs("Strat_01", runs)

        resp = service.get_chart_grid(
            "Strat_01", param_x="p1", param_y="p2", metric="NetProfit"
        )
        assert resp.request_id == "req_Strat_01_chart_grid"
        grid_data = resp.data
        assert grid_data.x_values == (10.0, 20.0)
        assert grid_data.y_values == (1.0, 2.0)
        # y=1.0: x=10 -> 100.0, x=20 -> 150.0
        # y=2.0: x=10 -> 120.0, x=20 -> 180.0
        assert grid_data.z_matrix == ((100.0, 150.0), (120.0, 180.0))

        csv_text = service.export_csv("Strat_01")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 5  # header + 4 rows
        assert "run_index,p1,p2,NetProfit,passed" in lines[0]

    def test_view_management(self) -> None:
        """Verify view CRUD actions and default view protection."""
        service = ResultsOptimizationProfileService()
        views = service.list_views()
        assert len(views) == 1

        new_view = service.add_view("Custom View", param_x="Period", param_y="StopLoss")
        assert len(service.list_views()) == 2

        updated = service.update_view(new_view["id"], name="Updated View")
        assert updated["name"] == "Updated View"

        with pytest.raises(DomainError) as exc_protected:
            service.remove_view("default")
        assert exc_protected.value.code == "OPTIMIZER_DEFAULT_VIEW_PROTECTED"

        removed = service.remove_view(new_view["id"])
        assert removed is True
        assert len(service.list_views()) == 1

    def test_results_table_and_params(self) -> None:
        """Verify get_available_params, get_results_table, and 1D chart grid."""
        service = ResultsOptimizationProfileService()
        with pytest.raises(DomainError, match="store"):
            service.get_available_params("Empty")
        service.set_mock_runs("Empty", [])
        assert service.get_available_params("Empty") == ()

        runs = [
            OptimizationRunRow(
                run_index=1,
                parameters={"p1": 10.0},
                metrics={"NetProfit": 100.0},
                passed=True,
            ),
            OptimizationRunRow(
                run_index=2,
                parameters={"p1": 20.0},
                metrics={"NetProfit": 150.0},
                passed=True,
            ),
        ]
        service.set_mock_runs("Strat_1D", runs)

        params = service.get_available_params("Strat_1D")
        assert params == ("p1",)

        table_resp = service.get_results_table("Strat_1D")
        assert len(table_resp.data) == 2

        grid_resp = service.get_chart_grid("Strat_1D", param_x="p1", param_y=None)
        assert grid_resp.data.x_values == (10.0, 20.0)
        assert grid_resp.data.y_values == ()
        assert grid_resp.data.z_matrix == ((100.0, 150.0),)

        empty_csv = service.export_csv("Empty")
        assert empty_csv == "run_index,passed\n"
