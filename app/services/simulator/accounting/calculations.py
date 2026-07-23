"""Deterministic fixed-precision calculations for Simulation accounting."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, DecimalException, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.data.evidence.fx_contracts import (
    FXConversionEvidence,  # noqa: TC001
)
from app.services.simulator.errors import SimulationError
from app.utils import canonical_digest, logger


class SymbolSpecification(BaseModel):
    """Immutable Phase 1 symbol volume and margin specification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_volume: Decimal
    maximum_volume: Decimal
    volume_step: Decimal
    contract_size: Decimal
    leverage: Decimal

    @field_validator(
        "minimum_volume", "maximum_volume", "volume_step", "contract_size", "leverage"
    )
    @classmethod
    def _validate_positive(cls, value: Decimal) -> Decimal:
        """Validate one finite positive specification value.

        Args:
            value: Candidate value.

        Returns:
            Validated value.

        Raises:
            ValueError: If the value is not finite and positive.
        """
        logger.debug("Validating Simulation symbol specification")
        if not value.is_finite() or value <= 0:
            raise ValueError("Symbol specification values must be finite and positive")
        return value


class ExecutionCostModel(BaseModel):
    """Explicit Phase 1 cash-per-lot execution cost model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commission_per_lot_per_side: Decimal
    long_swap_per_lot_rollover: Decimal
    short_swap_per_lot_rollover: Decimal

    @field_validator(
        "commission_per_lot_per_side",
        "long_swap_per_lot_rollover",
        "short_swap_per_lot_rollover",
    )
    @classmethod
    def _validate_cost(cls, value: Decimal) -> Decimal:
        """Validate one finite non-negative debit rate.

        Args:
            value: Candidate cost rate.

        Returns:
            Validated rate.

        Raises:
            ValueError: If the rate is invalid.
        """
        logger.debug("Validating Simulation execution cost rate")
        if not value.is_finite() or value < 0:
            raise ValueError("Execution cost rates must be finite and non-negative")
        return value


class ExecutionCostInput(BaseModel):
    """Exact inputs needed to calculate commission and swap."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    volume: Decimal
    side: Literal["BUY", "SELL"]
    rollover_multiplier: Decimal

    @field_validator("volume")
    @classmethod
    def _validate_volume(cls, value: Decimal) -> Decimal:
        """Validate positive fill volume.

        Args:
            value: Candidate volume.

        Returns:
            Validated volume.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating Simulation cost volume")
        if not value.is_finite() or value <= 0:
            raise ValueError("Cost volume must be finite and positive")
        return value

    @field_validator("rollover_multiplier")
    @classmethod
    def _validate_rollover(cls, value: Decimal) -> Decimal:
        """Validate non-negative rollover multiplier.

        Args:
            value: Candidate multiplier.

        Returns:
            Validated multiplier.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating Simulation rollover multiplier")
        if not value.is_finite() or value < 0:
            raise ValueError("Rollover multiplier must be finite and non-negative")
        return value


class ValidatedFXConversionEvidence(BaseModel):
    """Proof that Data-owned FX evidence was validated at a specific time."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    evidence: FXConversionEvidence
    evidence_hash: str
    validated_at: datetime


def _finite_positive(value: Decimal, code: str, field: str) -> None:
    """Validate one finite positive calculation input.

    Args:
        value: Candidate Decimal.
        code: Error code to raise.
        field: Safe field label.

    Raises:
        SimulationError: If the value is invalid.
    """
    logger.debug("Validating Simulation calculation input %s", field)
    if not value.is_finite() or value <= 0:
        raise SimulationError(code, f"{field} must be finite and positive")


def normalize_volume(volume: Decimal, specification: SymbolSpecification) -> Decimal:
    """Validate and preserve the exact Risk-approved volume.

    Args:
        volume: Exact approved volume.
        specification: Symbol limits and step.

    Returns:
        The unchanged approved volume.

    Raises:
        SimulationError: If volume violates any symbol constraint.
    """
    logger.info("Validating exact Risk-approved Simulation volume")
    if not volume.is_finite() or volume <= 0:
        raise SimulationError(
            "SIM_INVALID_VOLUME", "Volume must be finite and positive"
        )
    if volume < specification.minimum_volume:
        raise SimulationError("SIM_VOLUME_BELOW_MIN", "Volume is below symbol minimum")
    if volume > specification.maximum_volume:
        raise SimulationError("SIM_VOLUME_ABOVE_MAX", "Volume is above symbol maximum")
    try:
        steps = (volume - specification.minimum_volume) / specification.volume_step
    except InvalidOperation as error:
        raise SimulationError(
            "SIM_INVALID_VOLUME", "Volume step calculation failed"
        ) from error
    if steps != steps.to_integral_value():
        raise SimulationError(
            "SIM_VOLUME_STEP_MISMATCH", "Volume does not match symbol step"
        )
    return volume


def calculate_execution_costs(
    fill: ExecutionCostInput,
    model: ExecutionCostModel,
) -> dict[str, Decimal]:
    """Calculate deterministic signed commission and swap debits.

    Args:
        fill: Exact fill volume, side, and rollover multiplier.
        model: Explicit cost rates.

    Returns:
        Itemized negative-or-zero cost mapping.

    Raises:
        SimulationError: If commission or swap cannot be calculated finitely.
    """
    logger.info("Calculating Simulation commission and swap")
    try:
        commission = -(fill.volume * model.commission_per_lot_per_side)
    except DecimalException as error:
        raise SimulationError(
            "SIM_COMMISSION_CALCULATION_FAILED", "Commission calculation failed"
        ) from error
    if not commission.is_finite():
        raise SimulationError(
            "SIM_COMMISSION_CALCULATION_FAILED", "Commission is not finite"
        )
    swap_rate = (
        model.long_swap_per_lot_rollover
        if fill.side == "BUY"
        else model.short_swap_per_lot_rollover
    )
    try:
        swap = -(fill.volume * swap_rate * fill.rollover_multiplier)
    except DecimalException as error:
        raise SimulationError(
            "SIM_SWAP_CALCULATION_FAILED", "Swap calculation failed"
        ) from error
    if not swap.is_finite():
        raise SimulationError("SIM_SWAP_CALCULATION_FAILED", "Swap is not finite")
    return {"commission": commission, "swap": swap, "total": commission + swap}


def calculate_margin(
    volume: Decimal,
    price: Decimal,
    contract_size: Decimal,
    leverage: Decimal,
) -> Decimal:
    """Calculate required FX margin with the approved Phase 1 formula.

    Args:
        volume: Approved lot volume.
        price: Execution price.
        contract_size: Units represented by one lot.
        leverage: Positive leverage divisor.

    Returns:
        Required margin.

    Raises:
        SimulationError: If an input is invalid.
    """
    logger.info("Calculating required Simulation margin")
    for value, field in (
        (volume, "volume"),
        (price, "price"),
        (contract_size, "contract_size"),
        (leverage, "leverage"),
    ):
        _finite_positive(value, "SIM_INVALID_CONFIG", field)
    return volume * contract_size * price / leverage


def validate_fx_evidence(
    evidence: FXConversionEvidence,
    *,
    as_of: datetime,
) -> ValidatedFXConversionEvidence:
    """Validate fresh schema-compatible Data-owned conversion evidence.

    Args:
        evidence: Data-owned FX conversion evidence.
        as_of: UTC accounting time at which evidence is used.

    Returns:
        Immutable validation wrapper.

    Raises:
        SimulationError: If evidence is stale, premature, or incompatible.
    """
    logger.info("Validating Data-owned FX conversion evidence")
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise SimulationError(
            "SIM_FX_EVIDENCE_UNAVAILABLE", "FX validation time must be UTC"
        )
    if not evidence.as_of <= as_of < evidence.expires_at:
        raise SimulationError("SIM_FX_EVIDENCE_UNAVAILABLE", "FX evidence is not fresh")
    material = evidence.model_dump(mode="python", warnings=False)
    digest = canonical_digest(material)
    return ValidatedFXConversionEvidence(
        evidence=evidence,
        evidence_hash=digest,
        validated_at=as_of,
    )


def convert_fx_amount(
    amount: Decimal,
    evidence: ValidatedFXConversionEvidence,
) -> Decimal:
    """Convert an amount using only a previously validated composite rate.

    Args:
        amount: Exact monetary amount.
        evidence: Validated Data-owned conversion evidence.

    Returns:
        Converted exact amount.

    Raises:
        SimulationError: If amount or evidence is invalid.
    """
    logger.info("Converting Simulation monetary amount with supplied FX evidence")
    if not amount.is_finite():
        raise SimulationError("SIM_INVALID_CONFIG", "FX amount must be finite")
    return amount * evidence.evidence.composite_rate


__all__ = [
    "ExecutionCostInput",
    "ExecutionCostModel",
    "SymbolSpecification",
    "ValidatedFXConversionEvidence",
    "calculate_execution_costs",
    "calculate_margin",
    "convert_fx_amount",
    "normalize_volume",
    "validate_fx_evidence",
]
