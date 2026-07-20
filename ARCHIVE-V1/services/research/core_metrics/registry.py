"""Registry for Edge Core Metric calculators.

Purpose:
    Registry for Edge Core Metric calculators.

Classes:
    MetricRegistry: Represent MetricRegistry data or behavior.

Functions:
    None.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .base import MetricCalculator


@dataclass
class MetricRegistry:
    """Small registry keyed by metric family."""

    _calculators: dict[str, MetricCalculator] = field(default_factory=dict)

    def register(self, calculator: MetricCalculator) -> None:
        """Run register processing."""
        self._calculators[calculator.family] = calculator

    def get(self, family: str) -> MetricCalculator:
        """Run get processing."""
        return self._calculators[family]

    def all(self) -> list[MetricCalculator]:
        """Run all processing."""
        return [self._calculators[key] for key in sorted(self._calculators)]

    def families(self) -> list[str]:
        """Run families processing."""
        return sorted(self._calculators)

    @classmethod
    def from_calculators(
        cls, calculators: Iterable[MetricCalculator]
    ) -> MetricRegistry:
        """Run from calculators processing."""
        registry = cls()
        for calculator in calculators:
            registry.register(calculator)
        return registry
