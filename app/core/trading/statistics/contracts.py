"""Contracts and configuration models for strategy performance statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

type SplitType = Literal["NONE", "DATE", "RATIO"]


@dataclass(frozen=True, slots=True)
class SampleSplit:
    """In-Sample (IS) and Out-of-Sample (OOS) partitioning configuration."""

    split_type: SplitType = "NONE"
    split_date: datetime | None = None
    in_sample_ratio: float = 0.7


@dataclass(frozen=True, slots=True)
class MetricResults:
    """Strategy performance evaluation results partitioned by sample split."""

    all_trades: dict[str, float]
    in_sample: dict[str, float]
    out_of_sample: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert results to serializable dictionary."""
        return {
            "all_trades": dict(self.all_trades),
            "in_sample": dict(self.in_sample),
            "out_of_sample": dict(self.out_of_sample),
        }


__all__ = ["MetricResults", "SampleSplit", "SplitType"]
