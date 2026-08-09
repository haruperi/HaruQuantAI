"""Optimization stress-calibration provider adapter."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.research.stress_evidence.contracts import (
    parse_stress_scenario_evidence,
)


class _StressCalibrationProvider:
    """Private provider implementing Optimization's structural port."""

    def __init__(self, evidence: Mapping[str, object]) -> None:
        self._evidence = parse_stress_scenario_evidence(evidence)

    def stress_profile_calibration(
        self, *, strategy_ref: str, market_data_ref: str
    ) -> Mapping[str, object]:
        """Return evidence with consumer trace references."""
        return {
            **self._evidence,
            "strategy_ref": strategy_ref,
            "market_data_ref": market_data_ref,
        }


def build_stress_calibration_provider(evidence: Mapping[str, object]) -> object:
    """Build an opaque Optimization-compatible stress provider.

    Args:
        evidence: Validated Research stress evidence.

    Returns:
        Opaque provider implementing the calibration method.
    """
    return _StressCalibrationProvider(evidence)


__all__ = ("build_stress_calibration_provider",)
