"""Typed time-series split and walk-forward contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from itertools import pairwise

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.optimization.parameters import ParameterValue  # noqa: TC001
from app.services.optimization.scoring import CandidateScore  # noqa: TC001
from app.services.optimization.search import SearchRequest  # noqa: TC001
from app.utils import logger


class SplitMode(StrEnum):
    """Supported chronological walk-forward split modes."""

    ROLLING = "rolling"
    ANCHORED = "anchored"
    EXPANDING = "expanding"


class TimeSeriesSplit(BaseModel):
    """One half-open UTC training and test fold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fold_id: str
    train_start_index: int
    train_end_index: int
    test_start_index: int
    test_end_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    purge_bars: int
    embargo_bars: int
    leakage_prevented: bool

    @model_validator(mode="after")
    def _validate_split(self) -> TimeSeriesSplit:
        """Validate half-open chronological split relationships.

        Returns:
            Validated time-series split.

        Raises:
            ValueError: If indices, UTC boundaries, or gaps conflict.
        """
        logger.debug("Validating Optimization time-series split")
        if not (
            0
            <= self.train_start_index
            < self.train_end_index
            <= self.test_start_index
            < self.test_end_index
        ):
            raise ValueError("split indices must be ordered and non-overlapping")
        times = (self.train_start, self.train_end, self.test_start, self.test_end)
        offsets = tuple(value.utcoffset() for value in times)
        if any(value.tzinfo is None for value in times) or any(
            offset is None for offset in offsets
        ):
            raise ValueError("split boundaries must be timezone-aware")
        if any(
            offset is not None and offset.total_seconds() != 0 for offset in offsets
        ):
            raise ValueError("split boundaries must be UTC")
        if not self.train_start < self.train_end <= self.test_start < self.test_end:
            raise ValueError("split times must be ordered and non-overlapping")
        if self.purge_bars < 0 or self.embargo_bars < 0 or not self.leakage_prevented:
            raise ValueError("split leakage prevention evidence is invalid")
        return self


class WalkForwardRequest(BaseModel):
    """Bounded chronological walk-forward optimization request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    search: SearchRequest
    mode: SplitMode
    observation_times: tuple[datetime, ...]
    train_bars: int
    test_bars: int
    step_bars: int
    purge_bars: int = 0
    embargo_bars: int = 0
    average_trade_duration_bars: int | None = None
    minimum_fold_count: int = 3

    @model_validator(mode="after")
    def _validate_request(self) -> WalkForwardRequest:
        """Validate equally spaced UTC observations and window bounds.

        Returns:
            Validated walk-forward request.

        Raises:
            ValueError: If observations or window policy are invalid.
        """
        logger.debug("Validating Optimization walk-forward request")
        minimum_observation_count = 2
        if len(self.observation_times) < minimum_observation_count:
            raise ValueError("walk-forward requires at least two observations")
        offsets = tuple(value.utcoffset() for value in self.observation_times)
        if any(value.tzinfo is None for value in self.observation_times) or any(
            offset is None or offset.total_seconds() != 0 for offset in offsets
        ):
            raise ValueError("walk-forward observations must be UTC")
        deltas = tuple(right - left for left, right in pairwise(self.observation_times))
        if any(delta.total_seconds() <= 0 for delta in deltas) or len(set(deltas)) != 1:
            raise ValueError(
                "walk-forward observations must be unique and equally spaced"
            )
        if (
            min(
                self.train_bars, self.test_bars, self.step_bars, self.minimum_fold_count
            )
            <= 0
        ):
            raise ValueError("walk-forward sizes and minimum folds must be positive")
        if self.purge_bars < 0 or self.embargo_bars < 0:
            raise ValueError("purge and embargo cannot be negative")
        if self.purge_bars >= self.train_bars:
            raise ValueError("purge must leave a non-empty training window")
        if (
            self.average_trade_duration_bars is not None
            and self.average_trade_duration_bars <= 0
        ):
            raise ValueError("average trade duration must be positive")
        return self


class WalkForwardFoldResult(BaseModel):
    """Measured training selection and out-of-sample fold evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fold_id: str
    candidate_hash: str
    selected_parameters: Mapping[str, ParameterValue]
    train_score: CandidateScore
    out_of_sample_score: CandidateScore
    degradation: float | None

    @field_validator("degradation")
    @classmethod
    def _validate_degradation(cls, value: float | None) -> float | None:
        """Validate optional fold degradation.

        Args:
            value: Optional relative degradation.

        Returns:
            Finite degradation or None.

        Raises:
            ValueError: If the value is non-finite.
        """
        logger.debug("Validating Optimization fold degradation")
        if value is not None and not math.isfinite(value):
            raise ValueError("fold degradation must be finite")
        return value


class WalkForwardResult(BaseModel):
    """Aggregate walk-forward validation evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    splits: tuple[TimeSeriesSplit, ...]
    folds: tuple[WalkForwardFoldResult, ...]
    fold_pass_rate: float | None
    parameter_drift_score: float | None
    oos_retention_score: float | None
    walk_forward_efficiency: float | None
    status: str
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_result(self) -> WalkForwardResult:
        """Validate aggregate probability and fold relationships.

        Returns:
            Validated walk-forward result.

        Raises:
            ValueError: If aggregate evidence conflicts with folds.
        """
        logger.debug("Validating Optimization walk-forward result")
        if len(self.splits) != len(self.folds):
            raise ValueError("walk-forward splits and fold results must pair exactly")
        if self.fold_pass_rate is not None and not 0 <= self.fold_pass_rate <= 1:
            raise ValueError("fold pass rate must be a probability")
        for value in (
            self.parameter_drift_score,
            self.oos_retention_score,
            self.walk_forward_efficiency,
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError("walk-forward aggregate evidence must be finite")
        if self.status not in {"completed", "incomplete"}:
            raise ValueError("walk-forward status is unsupported")
        return self


__all__ = [
    "SplitMode",
    "TimeSeriesSplit",
    "WalkForwardFoldResult",
    "WalkForwardRequest",
    "WalkForwardResult",
]
