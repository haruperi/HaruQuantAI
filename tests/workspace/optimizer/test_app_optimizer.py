"""Tests for AppOptimizerService and workspace state transitions."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.app_optimizer import AppOptimizerService
from app.workspace.optimizer.settings_optimization import (
    OptimizableParameterSpec,
    OptimizationSettingsSnapshot,
)


class TestAppOptimizerService:
    """Test suite verifying AppOptimizerService state management and golden fixture."""

    def test_golden_fixture_start_simple_mode(self) -> None:
        """Verify golden fixture: starting SIMPLE mode over a 6-combination grid yields COMPLETED with 6 evaluations."""
        service = AppOptimizerService()
        p1 = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=10,
            enabled=True,
            start=10,
            stop=30,
            step=10,
        )  # 3 values: 10, 20, 30
        p2 = OptimizableParameterSpec(
            name="Shift",
            param_type="INT",
            original_value=1,
            enabled=True,
            start=1,
            stop=2,
            step=1,
        )  # 2 values: 1, 2
        # Total combinations: 3 * 2 = 6

        settings = OptimizationSettingsSnapshot(
            strategy_id="Strat_01",
            optimization_type="SIMPLE",
            parameters=(p1, p2),
        )

        service.save_settings("proj_1", settings)
        start_resp = service.start("proj_1")
        final_state = start_resp.data

        assert final_state.status == "COMPLETED"
        assert final_state.evaluations_completed == 6
        assert final_state.evaluations_total == 6
        assert final_state.progress_pct == 100.0
        assert final_state.best_fitness > 0.0

    def test_lifecycle_pause_resume_stop(self) -> None:
        """Verify pause, resume, and stop state transitions and guards."""
        service = AppOptimizerService()
        initial_state = service.get_state("proj_2").data
        assert initial_state.status == "IDLE"

        # Cannot pause IDLE
        with pytest.raises(DomainError) as exc_pause:
            service.pause("proj_2")
        assert exc_pause.value.code == "OPTIMIZER_CANNOT_PAUSE"

        # Stop from IDLE
        stop_resp = service.stop("proj_2")
        assert stop_resp.data.status == "STOPPED"

    def test_pause_and_resume_flow(self) -> None:
        """Verify pausing and resuming a running optimizer state."""
        service = AppOptimizerService()
        p = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=10,
            enabled=True,
            start=10,
            stop=20,
            step=5,
        )
        settings = OptimizationSettingsSnapshot(strategy_id="Strat_P", parameters=(p,))
        service.save_settings("proj_pause", settings)

        # Force state to RUNNING to test pause and resume
        service._states["proj_pause"] = service._states["proj_pause"].__class__(
            project_id="proj_pause",
            settings=settings,
            status="RUNNING",
            progress_pct=50.0,
            evaluations_completed=1,
            evaluations_total=3,
            best_fitness=100.0,
            active_result_tab="OptimizationProfile",
        )

        paused = service.pause("proj_pause").data
        assert paused.status == "PAUSED"

        # Cannot resume if not paused
        resumed = service.resume("proj_pause").data
        assert resumed.status == "RUNNING"

        with pytest.raises(DomainError) as exc_res:
            service.resume("proj_pause")
        assert exc_res.value.code == "OPTIMIZER_CANNOT_RESUME"

    def test_start_failure_transitions_to_failed(self) -> None:
        """Verify that starting with invalid settings raises DomainError and marks state FAILED."""
        service = AppOptimizerService()
        # Missing strategy_id
        invalid_settings = OptimizationSettingsSnapshot(strategy_id=None)
        service.save_settings("proj_3", invalid_settings)

        with pytest.raises(DomainError):
            service.start("proj_3")

        state = service.get_state("proj_3").data
        assert state.status == "FAILED"
