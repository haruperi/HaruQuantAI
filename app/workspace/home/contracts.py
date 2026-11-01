"""Validated contracts for native project execution settings.

Description:
    Validates the execution section of native TaskDocument settings before job
    submission. No market, task, strategy, or algorithm is selected implicitly.
Purpose:
    FEAT-HOME-EXECUTION-CONTRACTS: Bounded reproducible research execution.
Key Capabilities:
    - FR-home-execution-validation: Reject unsupported modes and invalid bounds;
      acceptance tests verify errors before writes and explicit validation logs.
Python API Usage:
    settings = ExecutionSettings.model_validate(task.settings["execution"])
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_execution_acceptance.py --no-cov
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.backtest.contracts import BacktestSettings

logger = get_logger(__name__)
_MAX_GRID_EVALUATIONS = 10000


class DatasetSettings(BaseModel):
    """Explicit catalog identity and optional epoch-second range."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    source: str = Field(min_length=1)
    revision: str | int | None = None
    start: int | None = None
    end: int | None = None

    @model_validator(mode="after")
    def validate_range(self) -> DatasetSettings:
        """Reject inverted time bounds."""
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("Dataset start exceeds end")
        return self


class SearchRange(BaseModel):
    """One finite bounded numeric optimization dimension."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    name: str = Field(min_length=1)
    start: float
    end: float
    step: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> SearchRange:
        """Reject reversed bounds before generating a parameter grid."""
        if self.end < self.start:
            raise ValueError("Parameter end is below start")
        if (self.end - self.start) / self.step > _MAX_GRID_EVALUATIONS - 1:
            raise ValueError("Parameter dimension exceeds 10000 evaluations")
        return self


class FixedSizing(BaseModel):
    """Configuration for the existing fixed-size position-sizing owner."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    method: Literal["FixedSize"] = "FixedSize"
    size: float = Field(gt=0)
    decimals: int = Field(default=8, ge=0, le=8)


class ExecutionSettings(BaseModel):
    """Supported execution configuration stored inside native task settings."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    dataset: DatasetSettings
    model: BacktestSettings = Field(default_factory=BacktestSettings)
    mode: Literal["RANDOM", "RETEST", "GRID"]
    seed: int = Field(ge=0)
    candidates: int = Field(default=1, ge=1, le=1000)
    max_rule_depth: int = Field(default=1, ge=1, le=8)
    allowed_blocks: tuple[str, ...] = ()
    strategy_result_ids: tuple[str, ...] = ()
    parameter_ranges: tuple[SearchRange, ...] = ()
    split_time: int | None = None
    money_management: FixedSizing | None = None

    @model_validator(mode="after")
    def validate_execution(self) -> ExecutionSettings:
        """Reject unavailable models, empty strategies, and unbounded grids."""
        if not all(
            math.isfinite(value)
            for value in (
                self.model.initial_capital,
                self.model.point_value,
                self.model.pip_size,
                self.model.commission_per_order,
                self.model.slippage_points,
            )
        ):
            raise ValueError("Execution model values must be finite")
        if self.model.precision_mode != "OHLC":
            raise ValueError("Only the Core OHLC backtest model is available")
        if self.model.initial_capital <= 0 or self.model.point_value <= 0:
            raise ValueError("Initial capital and point value must be positive")
        if self.model.pip_size <= 0:
            raise ValueError("Pip size must be positive")
        if self.model.commission_per_order < 0 or self.model.slippage_points < 0:
            raise ValueError("Execution costs must be nonnegative")
        if self.mode != "RANDOM" and not self.strategy_result_ids:
            raise ValueError("Selected stored strategy results are required")
        if self.mode == "GRID":
            self._validate_grid()
        logger.info("FR-home-execution-validation: validated mode %s", self.mode)
        return self

    def _validate_grid(self) -> None:
        """Bound the named grid before Core index construction."""
        if len(self.strategy_result_ids) != 1 or not self.parameter_ranges:
            raise ValueError("Grid search requires one strategy and parameter ranges")
        names = [r.name for r in self.parameter_ranges]
        if len(set(names)) != len(names):
            raise ValueError("Parameter names must be unique")
        total = 1
        for dimension in self.parameter_ranges:
            total *= int((dimension.end - dimension.start) / dimension.step + 1.000001)
            if total > _MAX_GRID_EVALUATIONS:
                raise ValueError("Grid search exceeds 10000 evaluations")
