"""Optimization settings and combinatorial test count calculation service.

Description:
    Provides SettingsOptimizationService and configuration snapshots for strategy
    parameter sweeping, combinatorial test calculations, and label integration.

Purpose:
    FEAT-SETTINGS-OPTIMIZATION: Strategy parameter sweep configuration and calculation.

Key Capabilities:
    - FR-settings-param-steps: Calculate test steps per parameter.
    - FR-settings-total-tests: Compute Cartesian test combinations.

Python API Usage:
    from app.workspace.optimizer.settings_optimization import (
        OptimizableParameterSpec,
        OptimizationSettingsSnapshot,
        SettingsOptimizationService,
    )
    param = OptimizableParameterSpec(
        name="Period", param_type="INT", original_value=14, start=10, stop=20, step=5
    )
    steps = SettingsOptimizationService.count_parameter_steps(param)  # 3

CLI Usage:
    python -m app.cli optimizer count-tests --strategy-id Strat_01
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Final, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.optimizer.labels import OptimizationLabels

logger = get_logger(__name__)

EXHAUSTIVE_MAX_TESTS: Final[int] = 1000000001

ParameterType = Literal["INT", "FLOAT", "BOOL", "SHIFT", "PERIOD"]
OptimizationType = Literal[
    "SIMPLE",
    "GENETIC",
    "WALK_FORWARD",
    "WALK_FORWARD_MATRIX",
    "SYS_PARAM_PERMUTATION",
    "SEQUENTIAL",
]
PeriodType = Literal["percent", "days", "bars"]


@dataclass(frozen=True, slots=True)
class OptimizableParameterSpec:
    """Specification for an optimizable strategy parameter range."""

    name: str
    param_type: ParameterType
    original_value: float | int | bool
    enabled: bool = True
    start: float = 0.0
    stop: float = 0.0
    step: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary."""
        return {
            "name": self.name,
            "param_type": self.param_type,
            "original_value": self.original_value,
            "enabled": self.enabled,
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
        }


@dataclass(frozen=True, slots=True)
class OptimizationSettingsSnapshot:
    """Snapshot of workspace optimization configuration."""

    strategy_id: str | None = None
    optimization_type: OptimizationType = "SIMPLE"
    max_tests: int = 1000
    period_type: PeriodType = "percent"
    param1_start: int = 20
    param1_stop: int = 40
    param1_step: int = 10
    param2_start: int = 5
    param2_stop: int = 15
    param2_step: int = 5
    anchored: bool = False
    parameters: tuple[OptimizableParameterSpec, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings snapshot to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "optimization_type": self.optimization_type,
            "max_tests": self.max_tests,
            "period_type": self.period_type,
            "param1_start": self.param1_start,
            "param1_stop": self.param1_stop,
            "param1_step": self.param1_step,
            "param2_start": self.param2_start,
            "param2_stop": self.param2_stop,
            "param2_step": self.param2_step,
            "anchored": self.anchored,
            "parameters": [p.to_dict() for p in self.parameters],
        }


class SettingsOptimizationService:
    """Optimization configuration and combinatorial test calculation service."""

    @staticmethod
    def count_parameter_steps(param: OptimizableParameterSpec) -> int:
        """Calculate discrete test steps for a single parameter spec.

        Args:
            param: Parameter specification.

        Returns:
            Number of test steps.

        Raises:
            DomainError: Code OPTIMIZER_INVALID_PARAM_RANGE on invalid step/range.
        """
        if not param.enabled:
            return 1
        if param.param_type == "BOOL":
            return 2

        if param.step <= 0 or param.stop < param.start:
            logger.error(
                "Invalid parameter range for %s: start=%f, stop=%f, step=%f",
                param.name,
                param.start,
                param.stop,
                param.step,
            )
            raise DomainError(
                code="OPTIMIZER_INVALID_PARAM_RANGE",
                message=(
                    f"Invalid range for {param.name}: "
                    f"start={param.start}, stop={param.stop}, step={param.step}"
                ),
            )

        steps = math.floor((param.stop - param.start) / param.step + 1e-9) + 1
        logger.debug("Parameter %s has %d discrete steps", param.name, steps)
        return steps

    @classmethod
    def get_number_of_tests(
        cls, settings: OptimizationSettingsSnapshot
    ) -> dict[str, int | str]:
        """Compute combinatorial test evaluations and period labels.

        Args:
            settings: Optimization settings snapshot.

        Returns:
            Dictionary containing total combinations, evaluations count, and labels.
        """
        if not settings.parameters:
            raw_combos = 0
        else:
            raw_combos = math.prod(
                cls.count_parameter_steps(p) for p in settings.parameters
            )

        # Walk-forward window multiplier
        window_multiplier = 1
        if settings.optimization_type == "WALK_FORWARD":
            if (
                settings.param1_step > 0
                and settings.param1_stop >= settings.param1_start
            ):
                window_multiplier = (
                    math.floor(
                        (settings.param1_stop - settings.param1_start)
                        / settings.param1_step
                        + 1e-9
                    )
                    + 1
                )
        elif settings.optimization_type == "WALK_FORWARD_MATRIX":
            w1 = 1
            w2 = 1
            if (
                settings.param1_step > 0
                and settings.param1_stop >= settings.param1_start
            ):
                w1 = (
                    math.floor(
                        (settings.param1_stop - settings.param1_start)
                        / settings.param1_step
                        + 1e-9
                    )
                    + 1
                )
            if (
                settings.param2_step > 0
                and settings.param2_stop >= settings.param2_start
            ):
                w2 = (
                    math.floor(
                        (settings.param2_stop - settings.param2_start)
                        / settings.param2_step
                        + 1e-9
                    )
                    + 1
                )
            window_multiplier = w1 * w2

        # Cap per-window evaluations when not exhaustive
        per_window_evals = raw_combos
        if (
            settings.max_tests != EXHAUSTIVE_MAX_TESTS
            and per_window_evals > settings.max_tests
        ):
            per_window_evals = settings.max_tests

        total_combinations = per_window_evals * window_multiplier

        max_tests_label = OptimizationLabels.max_tests(settings.max_tests)
        param1_label = (
            OptimizationLabels.period_parameter(1, settings.period_type) or ""
        )
        param2_label = (
            OptimizationLabels.period_parameter(2, settings.period_type) or ""
        )

        logger.info(
            "Calculated %d combinations (raw: %d, windows: %d) with max_tests=%s",
            total_combinations,
            raw_combos,
            window_multiplier,
            max_tests_label,
        )

        return {
            "total_combinations": total_combinations,
            "evaluations_total": total_combinations,
            "max_tests_label": str(max_tests_label),
            "param1_label": param1_label,
            "param2_label": param2_label,
        }
