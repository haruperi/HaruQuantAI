"""Portfolio Master fitness target field state helper.

Description:
    Computes enabled status and target value for fitness ranking criteria
    based on approximate type matching.
Purpose:
    FEAT-PORTFOLIO-MASTER: Configure portfolio fitness target field state.
Key Capabilities:
    - FR-master-target-state: Determine target field active state and reset.
Python API Usage:
    from app.workspace.portfolio_master.fitness_target import (
        FitnessTarget,
        TargetFieldState,
    )
    state = FitnessTarget.apply(
        value_type=2,
        approximate_type=2,
        target=12.5,
    )
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_master/test_fitness_target.py
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TargetFieldState:
    """Target field visibility and value state for a ranking criterion."""

    enabled: bool
    target: float


class FitnessTarget:
    """Helper evaluating dynamic criterion target field active state."""

    @staticmethod
    def apply(
        *,
        value_type: int,
        approximate_type: int,
        target: float,
    ) -> TargetFieldState:
        """Evaluate target field state for a ranking criterion.

        Args:
            value_type: Exact integer value type of the criterion.
            approximate_type: Exact integer value type indicating target approximation.
            target: Floating-point target value.

        Returns:
            TargetFieldState with enabled flag and target value (reset to 0.0
            if disabled).

        Raises:
            TypeError: If value_type or approximate_type are not exact ints,
                or if target is not a float.
        """
        if type(value_type) is not int or type(approximate_type) is not int:
            raise TypeError("value_type and approximate_type must be integers")
        if type(target) is not float:
            raise TypeError("target must be a float")

        if value_type == approximate_type:
            logger.debug(
                "Target field enabled: value_type %d matches approximate_type %d",
                value_type,
                approximate_type,
            )
            return TargetFieldState(enabled=True, target=target)

        logger.debug(
            "Target field disabled: value_type %d differs from approximate_type %d",
            value_type,
            approximate_type,
        )
        return TargetFieldState(enabled=False, target=0.0)
