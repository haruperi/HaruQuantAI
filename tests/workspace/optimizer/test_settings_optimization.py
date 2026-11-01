"""Tests for SettingsOptimizationService and parameter models."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.settings_optimization import (
    OptimizableParameterSpec,
    OptimizationSettingsSnapshot,
    SettingsOptimizationService,
)


class TestSettingsOptimizationService:
    """Test suite for parameter step counts and combinatorial evaluations."""

    def test_count_parameter_steps_enabled(self) -> None:
        """Verify step counts for enabled integer and float parameters."""
        p1 = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=14,
            enabled=True,
            start=10.0,
            stop=20.0,
            step=5.0,
        )
        assert SettingsOptimizationService.count_parameter_steps(p1) == 3

        p2 = OptimizableParameterSpec(
            name="Multiplier",
            param_type="FLOAT",
            original_value=2.0,
            enabled=True,
            start=1.0,
            stop=4.0,
            step=1.0,
        )
        assert SettingsOptimizationService.count_parameter_steps(p2) == 4

    def test_count_parameter_steps_disabled(self) -> None:
        """Verify disabled parameter returns 1 step."""
        p = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=14,
            enabled=False,
            start=10.0,
            stop=50.0,
            step=5.0,
        )
        assert SettingsOptimizationService.count_parameter_steps(p) == 1

    def test_count_parameter_steps_bool(self) -> None:
        """Verify boolean parameter returns 2 steps."""
        p = OptimizableParameterSpec(
            name="UseFilter",
            param_type="BOOL",
            original_value=True,
            enabled=True,
        )
        assert SettingsOptimizationService.count_parameter_steps(p) == 2

    def test_count_parameter_steps_invalid_range(self) -> None:
        """Verify DomainError code OPTIMIZER_INVALID_PARAM_RANGE on invalid step or stop < start."""
        p_invalid_step = OptimizableParameterSpec(
            name="P1",
            param_type="INT",
            original_value=10,
            enabled=True,
            start=10.0,
            stop=20.0,
            step=0.0,
        )
        with pytest.raises(DomainError) as exc_step:
            SettingsOptimizationService.count_parameter_steps(p_invalid_step)
        assert exc_step.value.code == "OPTIMIZER_INVALID_PARAM_RANGE"

        p_stop_lt_start = OptimizableParameterSpec(
            name="P2",
            param_type="INT",
            original_value=10,
            enabled=True,
            start=20.0,
            stop=10.0,
            step=2.0,
        )
        with pytest.raises(DomainError) as exc_range:
            SettingsOptimizationService.count_parameter_steps(p_stop_lt_start)
        assert exc_range.value.code == "OPTIMIZER_INVALID_PARAM_RANGE"

    def test_golden_fixture_get_number_of_tests(self) -> None:
        """Verify golden fixture: 2 enabled parameters (3 x 4) in SIMPLE mode yield 12 tests."""
        p1 = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=14,
            enabled=True,
            start=10.0,
            stop=20.0,
            step=5.0,
        )
        p2 = OptimizableParameterSpec(
            name="Mult",
            param_type="FLOAT",
            original_value=2.0,
            enabled=True,
            start=1.0,
            stop=4.0,
            step=1.0,
        )
        settings = OptimizationSettingsSnapshot(
            strategy_id="Strat_01",
            optimization_type="SIMPLE",
            max_tests=1000,
            period_type="percent",
            parameters=(p1, p2),
        )
        result = SettingsOptimizationService.get_number_of_tests(settings)
        assert result["total_combinations"] == 12
        assert result["evaluations_total"] == 12
        assert result["max_tests_label"] == "1.000"
        assert result["param1_label"] == "Out of Sample %"
        assert result["param2_label"] == "Walk Forward runs"

    def test_get_number_of_tests_empty_parameters(self) -> None:
        """Verify empty parameters yield 0 combinations."""
        settings = OptimizationSettingsSnapshot(parameters=())
        result = SettingsOptimizationService.get_number_of_tests(settings)
        assert result["total_combinations"] == 0

    def test_get_number_of_tests_walk_forward_and_matrix(self) -> None:
        """Verify walk-forward window and matrix multipliers."""
        p1 = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=10,
            start=10,
            stop=20,
            step=10,
        )  # 2 values
        # Walk forward: param1 from 20 to 40 step 10 -> 3 windows
        wf_settings = OptimizationSettingsSnapshot(
            optimization_type="WALK_FORWARD",
            param1_start=20,
            param1_stop=40,
            param1_step=10,
            parameters=(p1,),
        )
        res_wf = SettingsOptimizationService.get_number_of_tests(wf_settings)
        assert res_wf["total_combinations"] == 2 * 3

        # Matrix: param1 from 20 to 40 step 10 -> 3; param2 from 5 to 15 step 5 -> 3; windows = 9
        matrix_settings = OptimizationSettingsSnapshot(
            optimization_type="WALK_FORWARD_MATRIX",
            param1_start=20,
            param1_stop=40,
            param1_step=10,
            param2_start=5,
            param2_stop=15,
            param2_step=5,
            parameters=(p1,),
        )
        res_matrix = SettingsOptimizationService.get_number_of_tests(matrix_settings)
        assert res_matrix["total_combinations"] == 2 * 9

    def test_max_tests_cap(self) -> None:
        """Verify max tests cap when combinations exceed limit."""
        p1 = OptimizableParameterSpec(
            name="Period",
            param_type="INT",
            original_value=10,
            start=1,
            stop=100,
            step=1,
        )  # 100 values
        settings = OptimizationSettingsSnapshot(
            optimization_type="SIMPLE",
            max_tests=50,
            parameters=(p1,),
        )
        res = SettingsOptimizationService.get_number_of_tests(settings)
        assert res["total_combinations"] == 50
