"""Sizing request/result contracts and sizing method enum."""

from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from app.services.risk.models.contracts import (
    PositionSizingRequest,
    PositionSizingResult,
    RiskContract,
)


class SizingMethod(StrEnum):
    """Supported position sizing methods."""

    FIXED_LOT = "fixed_lot"
    FIXED_RISK = "fixed_risk"
    FIXED_FRACTIONAL = "fixed_fractional"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CORRELATION_ADJUSTED = "correlation_adjusted"
    MILESTONE = "milestone"
    KELLY = "kelly"


class SymbolRiskMetadata(RiskContract):
    """Symbol specifications needed for volume and precision normalizations."""

    symbol: str = Field(..., description="Symbol identifier.")
    volume_min: Decimal = Field(..., description="Minimum permitted volume.", ge=0)
    volume_max: Decimal = Field(..., description="Maximum permitted volume.", ge=0)
    volume_step: Decimal = Field(..., description="Minimum lot increment size.", gt=0)
    contract_size: Decimal = Field(
        ..., description="Underlying contract size per standard lot.", gt=0
    )
    digits: int = Field(..., description="Symbol decimal digits.", ge=0)
    tick_size: Decimal | None = Field(
        default=None, description="Minimum tick price increment.", gt=0
    )
    tick_value: Decimal | None = Field(
        default=None, description="Monetary value of a tick size increment.", gt=0
    )
    conversion_rate: Decimal = Field(
        default=Decimal("1.0"), description="Conversion rate to account currency.", gt=0
    )


class CorrelationImpact(RiskContract):
    """Correlation data for portfolio sizing adjustment."""

    portfolio_correlation: Decimal = Field(
        default=Decimal("0.0"), description="Correlation coefficient with portfolio."
    )


class RiskMilestone(RiskContract):
    """Milestone constraint mapping a multiplier."""

    name: str = Field(..., description="Milestone name.")
    multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Size scaling multiplier.", ge=0
    )


class KellyEvidence(RiskContract):
    """Trade performance metrics for Kelly sizing."""

    win_rate: Decimal = Field(
        default=Decimal("0.50"), description="Probability of win.", ge=0, le=1
    )
    win_loss_ratio: Decimal = Field(
        default=Decimal("1.50"),
        description="Avg win size divided by avg loss size.",
        ge=0,
    )
    historical_trade_count: int = Field(
        default=0, description="Number of closed trades.", ge=0
    )
    min_kelly_trades: int | None = Field(
        default=None, description="Minimum trades threshold."
    )
    kelly_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Fractional Kelly multiplier.", ge=0
    )
    enable_fractional_kelly: bool = Field(
        default=False, description="Enable active fractional Kelly sizing."
    )


class AdvisorySizingResult(RiskContract):
    """Kelly advisory-only sizing outcome."""

    calculated_volume: Decimal = Field(..., description="Calculated lot volume.", ge=0)
    kelly_fraction_applied: Decimal = Field(
        ..., description="Calculated Kelly fraction.", ge=0
    )
    constraints_applied: list[str] = Field(
        default_factory=list, description="Constraints/warnings applied."
    )
    is_advisory_only: bool = Field(
        default=True, description="Indicates if Kelly sizing is only advisory."
    )


__all__ = [
    "AdvisorySizingResult",
    "CorrelationImpact",
    "KellyEvidence",
    "PositionSizingRequest",
    "PositionSizingResult",
    "RiskMilestone",
    "SizingMethod",
    "SymbolRiskMetadata",
]
