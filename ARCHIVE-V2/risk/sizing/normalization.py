"""Broker volume normalization and precision validations."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.risk.models.contracts import PositionSizingResult
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.models import RiskReasonCode
    from app.services.risk.sizing.contracts import SymbolRiskMetadata
    from app.services.risk.validations import ValidationResult


def validate_symbol_volume_metadata(
    symbol: SymbolRiskMetadata,
) -> ValidationResult:
    """Validate symbol specification parameters before volume checks.

    Args:
        symbol: Symbol spec metadata contract to validate.

    Returns:
        ValidationResult: Outcome showing validity status.
    """
    sym_name = getattr(symbol, "symbol", "UNKNOWN")
    logger.debug("Validating symbol volume metadata for %s", sym_name)
    v_min = getattr(symbol, "volume_min", None)
    v_max = getattr(symbol, "volume_max", None)
    v_step = getattr(symbol, "volume_step", None)
    c_size = getattr(symbol, "contract_size", None)

    if v_min is None or v_max is None or v_step is None or c_size is None:
        msg = f"Missing volume specs for {sym_name}"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {},
        }

    if v_min <= 0 or v_max <= 0 or v_step <= 0 or c_size <= 0:
        msg = f"Invalid volume bounds or size limits for {sym_name}"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {},
        }

    return {
        "valid": True,
        "message": "Symbol volume metadata is valid.",
        "code": "OK",
        "details": {},
    }


def normalize_volume(size: Decimal, symbol: SymbolRiskMetadata) -> Decimal:
    """Floor size to broker lot-step increments.

    Args:
        size: Raw volume size.
        symbol: Symbol metadata holding the volume_step constraint.

    Returns:
        Decimal: Floored volume size.
    """
    logger.debug("Normalizing volume size %s for %s", size, symbol.symbol)
    if symbol.volume_step <= 0:
        logger.warning("Step size is zero or negative; returning 0.0 lot")
        return Decimal("0.0")

    steps = math.floor(size / symbol.volume_step)
    normalized = Decimal(str(steps)) * symbol.volume_step
    return normalized


def validate_normalized_volume(
    size: Decimal, symbol: SymbolRiskMetadata
) -> ValidationResult:
    """Check if normalized volume satisfies broker constraints.

    Args:
        size: Normalized volume to validate.
        symbol: Symbol metadata holding bounds.

    Returns:
        ValidationResult: Outcome showing validation status.
    """
    logger.debug("Checking volume bounds for %s: %s", symbol.symbol, size)

    if size < symbol.volume_min:
        msg = f"Calculated volume {size} is below broker minimum {symbol.volume_min}"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {"under_min": True},
        }

    if size > symbol.volume_max:
        msg = f"Calculated volume {size} is above broker maximum {symbol.volume_max}"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {"over_max": True},
        }

    remainder = size % symbol.volume_step
    # Small tolerance for floating/precision issues
    if remainder > Decimal("1e-9"):
        msg = (
            f"Calculated volume {size} is not aligned with broker step "
            f"{symbol.volume_step}"
        )
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {"step_mismatch": True},
        }

    return {
        "valid": True,
        "message": "Volume is valid.",
        "code": "OK",
        "details": {},
    }


def build_volume_rejection(
    size: Decimal,
    symbol: SymbolRiskMetadata,
    reason: RiskReasonCode,
) -> PositionSizingResult:
    """Return rejection result with zero volume and constraints list.

    Args:
        size: Target size that triggered rejection.
        symbol: Symbol metadata.
        reason: Stable reason code for rejection.

    Returns:
        PositionSizingResult: Failed positioning result.
    """
    logger.warning("Rejecting volume %s for %s due to %s", size, symbol.symbol, reason)
    return PositionSizingResult(
        calculated_volume=Decimal("0.0"),
        sizing_method="fixed_lot",
        constraints_applied=[reason.value],
        risk_contribution=Decimal("0.0"),
    )
