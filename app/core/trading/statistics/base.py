"""Contract for custom strategy databank and backtest performance metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class BaseMetric(ABC):
    """Contract for custom strategy performance columns."""

    name: str = "BaseMetric"
    category: str = "Metrics"

    @abstractmethod
    def compute(
        self, trades: Sequence[dict[str, Any]], initial_capital: float = 10000.0
    ) -> float:
        """Compute a scalar metric from executed trades."""


__all__ = ["BaseMetric"]
