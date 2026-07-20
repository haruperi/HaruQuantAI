"""Base types for Edge Core Metric calculators.

Purpose:
    Base types for Edge Core Metric calculators.

Classes:
    MetricValue: Represent MetricValue data or behavior.
    MetricContext: Represent MetricContext data or behavior.
    MetricCalculator: Represent MetricCalculator data or behavior.

Functions:
    None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import pandas as pd
from app.services.research.data.models import (
    CanonicalOHLCVSSchema,
    DataQualityReportModel,
)


@dataclass(frozen=True)
class MetricValue:
    """Normalized metric output."""

    family: str
    key: str
    value: Any
    value_type: str = "number"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricContext:
    """Shared context for metric calculators."""

    symbol: str
    timeframe: str
    data: pd.DataFrame
    schema: CanonicalOHLCVSSchema
    report: DataQualityReportModel


class MetricCalculator(Protocol):
    """Metric family interface."""

    family: str

    def compute(self, context: MetricContext) -> list[MetricValue]:
        """Compute normalized metrics for one family."""
        ...
