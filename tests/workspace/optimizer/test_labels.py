"""Tests for OptimizationLabels helper."""

import pytest
from app.workspace.optimizer.labels import OptimizationLabels


class TestOptimizationLabels:
    """Test suite verifying OptimizationLabels mapping and validation rules."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (100, "100"),
            (500, "500"),
            (1000, "1.000"),
            (3000, "3.000"),
            (7500, "7.500"),
            (10000, "10.000"),
            (15000, "15.000"),
            (50000, "50.000"),
            (100000, "100.000"),
            (200000, "200.000"),
            (500000, "500.000"),
            (1000000, "1.000.000"),
            (10000000, "10.000.000"),
            (100000000, "100.000.000"),
            (1000000000, "1.000.000.000"),
            (1000000001, "Exhaustive (all combinations)"),
            (42, 42),
        ],
    )
    def test_max_tests(self, value: int, expected: str | int) -> None:
        """Verify all 16 mapped max test values plus unmapped integer 42."""
        assert OptimizationLabels.max_tests(value) == expected

    @pytest.mark.parametrize(
        "invalid_value",
        [True, False, 100.0, "1000", None, [1000]],
    )
    def test_max_tests_type_error(self, invalid_value: object) -> None:
        """Verify TypeError when value is not an integer."""
        with pytest.raises(TypeError, match="value must be an integer"):
            OptimizationLabels.max_tests(invalid_value)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("param", "period_type", "expected"),
        [
            (1, "percent", "Out of Sample %"),
            (1, "days", "In Sample days"),
            (1, "bars", "In Sample bars"),
            (2, "percent", "Walk Forward runs"),
            (2, "days", "Out of Sample days"),
            (2, "bars", "Out of Sample bars"),
            (0, "percent", "Walk Forward runs"),
            (0, "days", "Out of Sample days"),
            (0, "bars", "Out of Sample bars"),
            (1, "unknown", None),
            (2, "unknown", None),
        ],
    )
    def test_period_parameter(
        self, param: int, period_type: str, expected: str | None
    ) -> None:
        """Verify period parameter string mapping for params 1, 2, 0 and unknown."""
        assert OptimizationLabels.period_parameter(param, period_type) == expected

    def test_period_parameter_type_errors(self) -> None:
        """Verify exact type error messages for invalid parameter or period_type."""
        with pytest.raises(TypeError, match="parameter must be an integer"):
            OptimizationLabels.period_parameter(True, "percent")  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="period_type must be a string"):
            OptimizationLabels.period_parameter(1, None)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="period_type must be a string"):
            OptimizationLabels.period_parameter(1, 123)  # type: ignore[arg-type]
