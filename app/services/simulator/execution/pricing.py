"""Deterministic bid/ask and adverse-slippage pricing."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.simulator.errors import SimulationError
from app.utils import logger

if TYPE_CHECKING:
    from app.services.simulator.timeline import Tick
    from app.services.trading import OrderIntent


class SessionInterval(BaseModel):
    """One explicit half-open weekly UTC session interval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start_week_second: int
    end_week_second: int

    @model_validator(mode="after")
    def _validate_interval(self) -> SessionInterval:
        """Validate ordered interval bounds.

        Returns:
            Validated interval.

        Raises:
            ValueError: If bounds are invalid.
        """
        logger.debug("Validating Simulation UTC session interval")
        week_seconds = 7 * 24 * 60 * 60
        if not 0 <= self.start_week_second < self.end_week_second <= week_seconds:
            raise ValueError("Session interval is outside one UTC week")
        return self


class ExecutionProfile(BaseModel):
    """Explicit deterministic Phase 1 execution model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    slippage_mode: Literal["none", "fixed_points"]
    fixed_slippage_points: Decimal
    point_value: Decimal
    price_quantum: Decimal
    maximum_slippage_points: Decimal
    maximum_gap_points: Decimal
    liquidity_mode: Literal["unbounded", "tick_volume"]
    participation_rate: Decimal
    sessions: tuple[SessionInterval, ...]

    @field_validator(
        "fixed_slippage_points",
        "maximum_slippage_points",
        "maximum_gap_points",
        "participation_rate",
    )
    @classmethod
    def _validate_non_negative(cls, value: Decimal) -> Decimal:
        """Validate a finite non-negative model value.

        Args:
            value: Candidate value.

        Returns:
            Validated value.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating non-negative Simulation execution setting")
        if not value.is_finite() or value < 0:
            raise ValueError("Execution setting must be finite and non-negative")
        return value

    @field_validator("point_value", "price_quantum")
    @classmethod
    def _validate_positive(cls, value: Decimal) -> Decimal:
        """Validate a finite positive price setting.

        Args:
            value: Candidate value.

        Returns:
            Validated value.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating positive Simulation execution setting")
        if not value.is_finite() or value <= 0:
            raise ValueError("Price setting must be finite and positive")
        return value

    @model_validator(mode="after")
    def _validate_profile(self) -> ExecutionProfile:
        """Validate execution-model relationships.

        Returns:
            Validated profile.

        Raises:
            ValueError: If settings conflict.
        """
        logger.debug("Validating Simulation execution profile relationships")
        if self.slippage_mode == "none" and self.fixed_slippage_points != 0:
            raise ValueError("No-slippage mode requires zero fixed points")
        if self.fixed_slippage_points > self.maximum_slippage_points:
            raise ValueError("Configured slippage exceeds its approved maximum")
        if (
            self.liquidity_mode == "tick_volume"
            and not 0 < self.participation_rate <= 1
        ):
            raise ValueError("Tick-volume participation must be in (0, 1]")
        if self.liquidity_mode == "unbounded" and self.participation_rate != 0:
            raise ValueError("Unbounded liquidity requires zero participation rate")
        if not self.sessions:
            raise ValueError("At least one explicit UTC session is required")
        return self


def price_order(intent: OrderIntent, tick: Tick, model: ExecutionProfile) -> Decimal:
    """Price one order from current bid/ask and explicit adverse slippage.

    Args:
        intent: Trading-owned approved order intent.
        tick: Current canonical tick only.
        model: Explicit execution profile.

    Returns:
        Quantized executable price.

    Raises:
        SimulationError: If pricing evidence or slippage is invalid.
    """
    logger.info("Pricing Simulation %s intent %s", intent.side, intent.client_order_id)
    base = tick.ask if intent.side == "BUY" else tick.bid
    if not base.is_finite() or base <= 0:
        raise SimulationError("SIM_INVALID_PRICE", "Tick execution price is invalid")
    if model.fixed_slippage_points > model.maximum_slippage_points:
        raise SimulationError(
            "SIM_SLIPPAGE_EXCEEDED", "Configured slippage exceeds maximum"
        )
    adverse = model.fixed_slippage_points * model.point_value
    priced = base + adverse if intent.side == "BUY" else base - adverse
    if priced <= 0:
        raise SimulationError("SIM_INVALID_PRICE", "Slippage produced invalid price")
    return priced.quantize(model.price_quantum, rounding=ROUND_HALF_EVEN)


__all__ = ["ExecutionProfile", "SessionInterval", "price_order"]
