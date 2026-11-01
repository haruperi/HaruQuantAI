"""Tests for FitnessTarget state helper (PM-001)."""

from __future__ import annotations

import pytest
from app.workspace.portfolio_master.fitness_target import (
    FitnessTarget,
    TargetFieldState,
)


class TestFitnessTarget:
    """Test suite for PM-001 FitnessTarget."""

    def test_target_state(self) -> None:
        """Assert equal types enable target and different types disable and reset."""
        state1 = FitnessTarget.apply(value_type=7, approximate_type=7, target=12.5)
        assert state1 == TargetFieldState(enabled=True, target=12.5)

        state2 = FitnessTarget.apply(value_type=8, approximate_type=7, target=12.5)
        assert state2 == TargetFieldState(enabled=False, target=0.0)

        # Re-enabling returns fresh state
        state3 = FitnessTarget.apply(value_type=7, approximate_type=7, target=4.0)
        assert state3 == TargetFieldState(enabled=True, target=4.0)

    def test_type_errors(self) -> None:
        """Assert boolean and non-int/float arguments raise exact TypeErrors."""
        with pytest.raises(
            TypeError,
            match=r"^value_type and approximate_type must be integers$",
        ):
            FitnessTarget.apply(value_type=True, approximate_type=7, target=12.5)  # type: ignore[arg-type]

        with pytest.raises(
            TypeError,
            match=r"^value_type and approximate_type must be integers$",
        ):
            FitnessTarget.apply(value_type=7, approximate_type=False, target=12.5)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match=r"^target must be a float$"):
            FitnessTarget.apply(value_type=7, approximate_type=7, target=1)  # type: ignore[arg-type]
