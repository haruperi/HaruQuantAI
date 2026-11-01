"""Tests for ResultsWalkForwardService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.results_walk_forward import (
    ResultsWalkForwardService,
    WalkForwardResultsProjection,
    WFWindowResult,
)


class TestResultsWalkForwardService:
    """Test suite verifying walk-forward projection, matrix cells, and parameter application."""

    def test_golden_fixture_apply_latest_window_parameters(self) -> None:
        """Verify golden fixture: applying latest window parameters writes windows[-1].best_params."""
        service = ResultsWalkForwardService()
        w1 = WFWindowResult(
            window_index=1,
            is_start="2020-01-01",
            is_end="2020-12-31",
            oos_start="2021-01-01",
            oos_end="2021-03-31",
            best_params={"Period": 14, "Multiplier": 2.0},
            is_net_profit=500.0,
            oos_net_profit=120.0,
            passed=True,
        )
        w2 = WFWindowResult(
            window_index=2,
            is_start="2020-04-01",
            is_end="2021-03-31",
            oos_start="2021-04-01",
            oos_end="2021-06-30",
            best_params={"Period": 18, "Multiplier": 2.5},
            is_net_profit=600.0,
            oos_net_profit=150.0,
            passed=True,
        )
        w3 = WFWindowResult(
            window_index=3,
            is_start="2020-07-01",
            is_end="2021-06-30",
            oos_start="2021-07-01",
            oos_end="2021-09-30",
            best_params={"Period": 22, "Multiplier": 3.0},
            is_net_profit=750.0,
            oos_net_profit=180.0,
            passed=True,
        )
        proj = WalkForwardResultsProjection(
            strategy_id="Strat_01",
            is_matrix=False,
            selected_runs_count=3,
            selected_oos_pct=25,
            stitched_oos_equity=(
                (1, 10000.0),
                (2, 10120.0),
                (3, 10270.0),
                (4, 10450.0),
            ),
            baseline_equity=((1, 10000.0), (4, 10300.0)),
            windows=(w1, w2, w3),
            matrix_cells=(),
            robustness_passed=3,
            robustness_total=3,
            overall_passed=True,
        )
        service.set_projection("Strat_01", proj)

        resp = service.apply_latest_window_parameters("proj_1", "Results", "Strat_01")
        assert resp.request_id == "req_Strat_01_apply_wf_params"
        assert resp.data == {"Period": 22, "Multiplier": 3.0}

    def test_apply_without_windows_raises(self) -> None:
        """Verify DomainError code OPTIMIZER_NO_WF_WINDOWS when strategy has no windows."""
        service = ResultsWalkForwardService()
        with pytest.raises(DomainError) as exc_info:
            service.apply_latest_window_parameters("proj_1", "Results", "Strat_Unknown")
        assert exc_info.value.code == "OPTIMIZER_NO_WF_WINDOWS"

    def test_export_wf_csv(self) -> None:
        """Verify CSV export of walk forward windows."""
        service = ResultsWalkForwardService()
        w1 = WFWindowResult(
            window_index=1,
            is_start="2020-01-01",
            is_end="2020-12-31",
            oos_start="2021-01-01",
            oos_end="2021-03-31",
            best_params={"Period": 14},
            is_net_profit=500.0,
            oos_net_profit=120.0,
            passed=True,
        )
        proj = WalkForwardResultsProjection(
            strategy_id="Strat_01",
            is_matrix=False,
            selected_runs_count=1,
            selected_oos_pct=25,
            stitched_oos_equity=(),
            baseline_equity=(),
            windows=(w1,),
            matrix_cells=(),
            robustness_passed=1,
            robustness_total=1,
            overall_passed=True,
        )
        service.set_projection("Strat_01", proj)

        csv_text = service.export_wf_csv("Strat_01")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "window_index,is_start,is_end" in lines[0]

    def test_view_management_and_conditions(self) -> None:
        """Verify view CRUD, conditions, and empty projection."""
        service = ResultsWalkForwardService()
        assert len(service.list_views()) == 1

        v = service.add_view("Matrix View", show_matrix=True)
        assert len(service.list_views()) == 2

        up = service.update_view(v["id"], name="Updated WF View")
        assert up["name"] == "Updated WF View"

        with pytest.raises(DomainError) as exc_prot:
            service.remove_view("default")
        assert exc_prot.value.code == "OPTIMIZER_DEFAULT_VIEW_PROTECTED"

        service.remove_view(v["id"])
        assert len(service.list_views()) == 1

        conditions = service.get_conditions()
        assert len(conditions) == 2

        empty_proj = service.get_projection("Unknown").data
        assert empty_proj.strategy_id == "Unknown"
        assert len(empty_proj.windows) == 0

        empty_csv = service.export_wf_csv("Unknown")
        assert "window_index,is_start" in empty_csv
