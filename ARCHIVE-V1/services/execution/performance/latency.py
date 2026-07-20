"""Latency budget monitoring helpers.

Classes and functions:
    LatencySample: Class. Provides LatencySample behavior for execution workflows.
    LatencyAlert: Class. Provides LatencyAlert behavior for execution workflows.
    LatencyBudgetMonitor: Class. Provides LatencyBudgetMonitor behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatencySample:
    """Represent LatencySample behavior in execution service workflows."""

    operation: str
    latency_ms: int


@dataclass(frozen=True)
class LatencyAlert:
    """Represent LatencyAlert behavior in execution service workflows."""

    operation: str
    threshold_ms: int
    observed_latency_ms: int


class LatencyBudgetMonitor:
    """Raise alerts when observed latency exceeds a configured budget."""

    def __init__(self, *, threshold_ms: int) -> None:
        self._threshold_ms = threshold_ms

    def evaluate(self, sample: LatencySample) -> LatencyAlert | None:
        """Perform the evaluate execution service operation."""
        if sample.latency_ms <= self._threshold_ms:
            return None
        return LatencyAlert(
            operation=sample.operation,
            threshold_ms=self._threshold_ms,
            observed_latency_ms=sample.latency_ms,
        )

    def evaluate_many(
        self, samples: tuple[LatencySample, ...]
    ) -> tuple[LatencyAlert, ...]:
        """Perform the evaluate_many execution service operation."""
        return tuple(
            alert for sample in samples if (alert := self.evaluate(sample)) is not None
        )
