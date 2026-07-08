"""Regime evidence validation, reason-code composition, and input rejection.

Provides reusable pure checks that support fail-closed regime decisions
and guarantee that no regime check mutates input evidence.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.risk.models import (
    MarketRiskSnapshot,
    RiskReasonCode,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.regime.assessor import RegimeAssessment
    from app.utils.validations import ValidationResult


def validate_regime_inputs(market: MarketRiskSnapshot) -> ValidationResult:
    """Validate input MarketRiskSnapshot values for correctness.

    Args:
        market: The MarketRiskSnapshot containing spread, volatility, session,
          etc.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.debug("Validating market regime inputs.")

    # 1. Spread cannot be negative or inverted
    if market.spread < Decimal(0):
        msg = "Inverted or negative spread detected"
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INVALID_INPUT",
            "details": {"spread": str(market.spread)},
        }

    # 2. Volatility cannot be negative
    if market.volatility < Decimal(0):
        msg = "Negative volatility detected"
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INVALID_INPUT",
            "details": {"volatility": str(market.volatility)},
        }

    # 3. Session cannot be empty
    if not market.session:
        msg = "Market session is empty or missing"
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INVALID_INPUT",
            "details": {"session": market.session},
        }

    # 4. Freshness must be provided
    if market.freshness is None:
        msg = "Freshness timestamp is missing"
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INVALID_INPUT",
            "details": {"freshness": "None"},
        }

    return {
        "valid": True,
        "message": "Validation passed.",
        "code": "OK",
        "details": {},
    }


def build_regime_reason_codes(
    assessment: RegimeAssessment,
) -> tuple[RiskReasonCode, ...]:
    """Produces stable warning/block reason ordering based on assessment.

    Args:
        assessment: The RegimeAssessment result to evaluate.

    Returns:
        tuple[RiskReasonCode, ...]: Stable list of associated reason codes.
    """
    logger.debug("Building stable regime reason codes.")
    reasons: list[RiskReasonCode] = []

    if assessment.reason_code != RiskReasonCode.OK:
        reasons.append(assessment.reason_code)

    return tuple(reasons)
