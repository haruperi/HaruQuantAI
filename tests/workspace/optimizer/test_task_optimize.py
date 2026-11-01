"""Tests for TaskOptimizeVerifier and TaskOptimizeRunner."""

from pathlib import Path
from typing import Any

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.settings_optimization import (
    OptimizableParameterSpec,
    OptimizationSettingsSnapshot,
)
from app.workspace.optimizer.task_optimize import (
    TaskOptimizeRunner,
    TaskOptimizeVerifier,
)
from tests.workspace.home.test_execution_acceptance import context, project
from tests.workspace.home.test_execution_acceptance import execution as execution  # noqa: PLC0414


class TestTaskOptimize:
    """Test suite verifying optimization verification guards and execution runner."""

    def test_verifier_missing_strategy(self) -> None:
        """Verify OPTIMIZER_STRATEGY_REQUIRED when strategy_id is None."""
        settings = OptimizationSettingsSnapshot(strategy_id=None)
        with pytest.raises(DomainError) as exc_info:
            TaskOptimizeVerifier.verify(settings)
        assert exc_info.value.code == "OPTIMIZER_STRATEGY_REQUIRED"

    def test_verifier_no_enabled_parameters(self) -> None:
        """Verify OPTIMIZER_NO_ENABLED_PARAMETERS when no parameter is enabled with >1 step."""
        p_disabled = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=14,
            enabled=False,
            start=10,
            stop=20,
            step=5,
        )
        settings = OptimizationSettingsSnapshot(
            strategy_id="Strat_01", parameters=(p_disabled,)
        )
        with pytest.raises(DomainError) as exc_info:
            TaskOptimizeVerifier.verify(settings)
        assert exc_info.value.code == "OPTIMIZER_NO_ENABLED_PARAMETERS"

    def test_verifier_invalid_wf_grid(self) -> None:
        """Verify OPTIMIZER_INVALID_WF_GRID on inverted WF bounds."""
        p_enabled = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=14,
            enabled=True,
            start=10,
            stop=20,
            step=5,
        )
        wf_invalid = OptimizationSettingsSnapshot(
            strategy_id="Strat_01",
            optimization_type="WALK_FORWARD",
            param1_start=40,
            param1_stop=20,
            parameters=(p_enabled,),
        )
        with pytest.raises(DomainError) as exc_info:
            TaskOptimizeVerifier.verify(wf_invalid)
        assert exc_info.value.code == "OPTIMIZER_INVALID_WF_GRID"

        matrix_invalid = OptimizationSettingsSnapshot(
            strategy_id="Strat_01",
            optimization_type="WALK_FORWARD_MATRIX",
            param1_start=20,
            param1_stop=40,
            param2_start=30,
            param2_stop=10,
            parameters=(p_enabled,),
        )
        with pytest.raises(DomainError) as exc_matrix:
            TaskOptimizeVerifier.verify(matrix_invalid)
        assert exc_matrix.value.code == "OPTIMIZER_INVALID_WF_GRID"

    def test_golden_fixture_task_runner(self, execution: Any, tmp_path: Path) -> None:
        """Grid variants use actual bar PnL, selecting threshold 10 over 11/12."""
        parameter = OptimizableParameterSpec(
            name="threshold",
            param_type="FLOAT",
            original_value=10,
            start=10,
            stop=12,
            step=1,
        )
        settings = OptimizationSettingsSnapshot(
            strategy_id="known", optimization_type="SIMPLE", parameters=(parameter,)
        )
        executor, _, _ = execution
        snapshot = executor.prepare(
            project(
                "GRID",
                parameter_ranges=[
                    {"name": "threshold", "start": 10, "end": 12, "step": 1}
                ],
            ),
            "task",
            1,
        )
        summary = TaskOptimizeRunner.execute(
            "project",
            settings,
            execution=executor,
            snapshot=snapshot,
            context=context(tmp_path, "optimizer-compat"),
        )
        assert summary.evaluations_completed == 3
        assert summary.best_parameters == {"threshold": 10.0}
        assert summary.best_fitness == 0
        assert len(summary.stored_strategy_ids) == 3
