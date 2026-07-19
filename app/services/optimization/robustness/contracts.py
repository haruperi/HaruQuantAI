"""Immutable contracts for Optimization robustness evidence."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import logger


class MonteCarloMethod(StrEnum):
    """Approved initial Monte Carlo methods."""

    SHUFFLE_TRADES = "shuffle_trades"
    RESAMPLE_RETURNS = "resample_returns"
    BLOCK_BOOTSTRAP = "block_bootstrap"


class MonteCarloRequest(BaseModel):
    """Bounded, seeded Monte Carlo request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcomes: tuple[Decimal, ...]
    initial_balance: Decimal
    method: MonteCarloMethod
    simulations: int
    seed: int
    block_size: int | None = None
    ruin_threshold: Decimal | None = None
    confidence_level: float | None = None

    @model_validator(mode="after")
    def _validate_request(self) -> MonteCarloRequest:
        """Validate finite outcomes and method-specific inputs.

        Returns:
            Validated Monte Carlo request.

        Raises:
            ValueError: If values are empty, invalid, or incompatible.
        """
        logger.debug("Validating Optimization Monte Carlo request")
        if not self.outcomes or any(not value.is_finite() for value in self.outcomes):
            raise ValueError("Monte Carlo outcomes must be non-empty and finite")
        if not self.initial_balance.is_finite() or self.initial_balance <= 0:
            raise ValueError("Monte Carlo initial balance must be positive and finite")
        if self.simulations <= 0:
            raise ValueError("Monte Carlo simulations must be positive")
        if self.method is MonteCarloMethod.BLOCK_BOOTSTRAP:
            if self.block_size is None or not 1 <= self.block_size <= len(
                self.outcomes
            ):
                raise ValueError("block bootstrap requires a valid block size")
        elif self.block_size is not None:
            raise ValueError("block size is only valid for block bootstrap")
        if self.ruin_threshold is not None and (
            not self.ruin_threshold.is_finite()
            or self.ruin_threshold < 0
            or self.ruin_threshold >= self.initial_balance
        ):
            raise ValueError("ruin threshold must be below initial balance")
        if self.confidence_level is not None and not 0 < self.confidence_level < 1:
            raise ValueError("confidence level must be between zero and one")
        return self


class MonteCarloResult(BaseModel):
    """Reproducible Monte Carlo path summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method: MonteCarloMethod
    simulations: int
    seed: int
    sub_seed_policy: str
    final_equity: tuple[Decimal, ...]
    max_drawdowns: tuple[Decimal, ...]
    percentiles: Mapping[str, Decimal | None]
    ruin_probability: float | None
    warnings: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_result(self) -> MonteCarloResult:
        """Validate distribution counts, finiteness, and probabilities.

        Returns:
            Validated Monte Carlo result.

        Raises:
            ValueError: If result evidence is inconsistent.
        """
        logger.debug("Validating Optimization Monte Carlo result")
        if self.simulations <= 0 or len(self.final_equity) != self.simulations:
            raise ValueError("final-equity path count must equal simulations")
        if len(self.max_drawdowns) != self.simulations:
            raise ValueError("drawdown path count must equal simulations")
        if any(not value.is_finite() for value in self.final_equity):
            raise ValueError("final-equity values must be finite")
        if any(not value.is_finite() or value < 0 for value in self.max_drawdowns):
            raise ValueError("drawdowns must be finite and non-negative")
        if not self.sub_seed_policy.strip():
            raise ValueError("sub-seed policy is required")
        if self.ruin_probability is not None and (
            not math.isfinite(self.ruin_probability)
            or not 0 <= self.ruin_probability <= 1
        ):
            raise ValueError("ruin probability must be a finite probability")
        for name, value in self.percentiles.items():
            if not name.strip() or (value is not None and not value.is_finite()):
                raise ValueError("percentile evidence must be named and finite")
        return self


class ExecutionStressRequest(BaseModel):
    """One explicit execution-cost or skipped-trade stress assumption."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    value: Decimal
    seed: int | None = None

    @field_validator("kind")
    @classmethod
    def _validate_kind(cls, value: str) -> str:
        """Validate the approved stress catalog.

        Args:
            value: Stress kind.

        Returns:
            Validated stress kind.

        Raises:
            ValueError: If the kind is not approved.
        """
        logger.debug("Validating Optimization execution stress kind")
        approved = {"spread", "slippage", "commission", "skip_trade"}
        if value not in approved:
            raise ValueError("execution stress kind is unsupported")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> ExecutionStressRequest:
        """Validate explicit stress value and seed policy.

        Returns:
            Validated execution stress request.

        Raises:
            ValueError: If value or seed policy is invalid.
        """
        logger.debug("Validating Optimization execution stress request")
        if not self.value.is_finite() or self.value < 0:
            raise ValueError("execution stress value must be finite and non-negative")
        if self.kind == "skip_trade":
            if self.value > 1 or self.seed is None:
                raise ValueError("skip-trade stress requires probability and seed")
        elif self.seed is not None:
            raise ValueError("seed is only valid for skip-trade stress")
        return self


__all__ = [
    "ExecutionStressRequest",
    "MonteCarloMethod",
    "MonteCarloRequest",
    "MonteCarloResult",
]
