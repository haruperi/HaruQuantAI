"""Value-at-Risk (VaR) and Expected Shortfall (ES) contracts and enums."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.services.risk.models.contracts import (
    PortfolioState,
    ProposedTrade,
    RiskContract,
)


class VaRMethod(StrEnum):
    """Supported Value-at-Risk computation methods."""

    PARAMETRIC = "parametric"
    HISTORICAL = "historical"


class ExpectedShortfallMethod(StrEnum):
    """Supported Expected Shortfall computation methods."""

    PARAMETRIC = "parametric"
    HISTORICAL = "historical"


class VaRCalculationRequest(RiskContract):
    """Input parameters required for portfolio Value-at-Risk calculations."""

    portfolio_state: PortfolioState = Field(..., description="Current portfolio state.")
    market_context: dict[str, Any] = Field(
        ..., description="Market context containing returns/prices history."
    )
    proposed_trade: ProposedTrade | None = Field(
        default=None, description="Optional candidate proposed trade."
    )
    lookback: int = Field(default=50, description="Returns lookback length.")
    confidence: Decimal = Field(
        default=Decimal("0.95"), description="Confidence level.", ge=0, le=1
    )
    method: VaRMethod = Field(
        default=VaRMethod.PARAMETRIC, description="VaR calculation method."
    )
    cov_method: str = Field(
        default="parametric", description="Covariance calculation method."
    )
    ewma_decay: Decimal = Field(
        default=Decimal("0.94"), description="EWMA decay factor."
    )
    shrinkage_intensity: Decimal = Field(
        default=Decimal("0.1"), description="Shrinkage intensity."
    )
    min_samples: int = Field(default=20, description="Minimum required return samples.")
    exclude_last: bool = Field(default=True, description="Exclude the last bar.")


class ExpectedShortfallRequest(RiskContract):
    """Input parameters required for portfolio Expected Shortfall calculations."""

    portfolio_state: PortfolioState = Field(..., description="Current portfolio state.")
    market_context: dict[str, Any] = Field(
        ..., description="Market context containing returns/prices history."
    )
    proposed_trade: ProposedTrade | None = Field(
        default=None, description="Optional candidate proposed trade."
    )
    lookback: int = Field(default=50, description="Returns lookback length.")
    confidence: Decimal = Field(
        default=Decimal("0.95"), description="Confidence level.", ge=0, le=1
    )
    method: ExpectedShortfallMethod = Field(
        default=ExpectedShortfallMethod.PARAMETRIC, description="ES calculation method."
    )
    cov_method: str = Field(
        default="parametric", description="Covariance calculation method."
    )
    ewma_decay: Decimal = Field(
        default=Decimal("0.94"), description="EWMA decay factor."
    )
    shrinkage_intensity: Decimal = Field(
        default=Decimal("0.1"), description="Shrinkage intensity."
    )
    min_samples: int = Field(default=20, description="Minimum required return samples.")
    exclude_last: bool = Field(default=True, description="Exclude the last bar.")


# =====================================================================
# Legacy Compat models (so rest of codebase is not broken)
# =====================================================================


class PortfolioVarianceInputs(RiskContract):
    """Input data parameters for portfolio variance calculations."""

    weights: dict[str, Decimal] = Field(
        ..., description="Signed portfolio weights per symbol."
    )
    covariance_matrix: dict[str, dict[str, Decimal]] = Field(
        ..., description="Pairwise covariance matrix."
    )


class VaRResult(RiskContract):
    """Encapsulates Value-at-Risk computation outputs."""

    method: str = Field(..., description="Method used (parametric or historical).")
    confidence: Decimal = Field(..., description="Confidence level (e.g. 0.95).")
    portfolio_volatility: Decimal = Field(..., description="Portfolio volatility.")
    exposure: Decimal = Field(
        ..., description="Evaluated exposure in account currency."
    )
    result: Decimal = Field(..., description="Value-at-Risk amount.")
    assumptions: dict[str, Any] = Field(
        default_factory=dict, description="Model assumptions and parameters."
    )


class ExpectedShortfallResult(RiskContract):
    """Encapsulates Expected Shortfall computation outputs."""

    confidence: Decimal = Field(..., description="Confidence level (e.g. 0.95).")
    threshold_loss: Decimal = Field(
        ..., description="Threshold loss level (VaR value)."
    )
    average_tail_loss: Decimal = Field(..., description="Average loss in tail.")
    sample_count: int = Field(..., description="Returns sample size used.")
    method: str = Field(..., description="Expected shortfall method name.")
