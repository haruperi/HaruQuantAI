"""Tests for the centralized BaseMetric extension interface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import pytest
from app.core.trading.statistics.base import BaseMetric
from app.include.metrics.base import BaseMetric as OldBaseMetric


def test_metric_interface_identity_and_abstractness() -> None:
    """Verify BaseMetric identity, abstractness, and default parameter behavior."""
    assert BaseMetric is OldBaseMetric
    assert BaseMetric.name == "BaseMetric"
    assert BaseMetric.category == "Metrics"

    with pytest.raises(TypeError):
        BaseMetric()  # type: ignore[abstract]

    class ConcreteMetric(BaseMetric):
        @override
        def compute(
            self,
            trades: Sequence[dict[str, Any]],
            initial_capital: float = 10000.0,
        ) -> float:
            return initial_capital

    metric = ConcreteMetric()
    assert metric.compute([]) == 10000.0
    assert metric.compute([], initial_capital=25000.0) == 25000.0
