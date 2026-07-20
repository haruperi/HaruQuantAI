# ruff: noqa: ANN401
"""Tail-risk engine package initialization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.models.contracts import (
    ExpectedShortfallSnapshot,
    PortfolioState,
    ProposedTrade,
    VaRSnapshot,
)
from app.services.risk.tail_risk.contracts import (
    ExpectedShortfallMethod,
    ExpectedShortfallRequest,
    ExpectedShortfallResult,
    PortfolioVarianceInputs,
    VaRCalculationRequest,
    VaRMethod,
    VaRResult,
)
from app.services.risk.tail_risk.expected_shortfall import (
    ExpectedShortfallEngine,
    calculate_expected_shortfall,
    select_tail_losses,
    validate_tail_risk_assumptions,
)
from app.services.risk.tail_risk.var import (
    PortfolioVaREngine,
    calculate_covariance,
    calculate_covariance_matrix,
    calculate_ewma_covariance,
    calculate_historical_var,
    calculate_historical_var_es,
    calculate_parametric_var,
    calculate_parametric_var_es,
    calculate_portfolio_volatility,
    calculate_risk_contribution,
    calculate_risk_contributions,
    calculate_var_component_contribution,
    shrink_covariance_matrix,
    validate_covariance_matrix,
)
from app.utils.logger import logger

__all__ = [
    "ExpectedShortfallEngine",
    "ExpectedShortfallMethod",
    "ExpectedShortfallRequest",
    "ExpectedShortfallResult",
    "PortfolioVaREngine",
    "PortfolioVarianceInputs",
    "VaRCalculationRequest",
    "VaRMethod",
    "VaRResult",
    "calculate_covariance",
    "calculate_covariance_matrix",
    "calculate_ewma_covariance",
    "calculate_expected_shortfall",
    "calculate_historical_var",
    "calculate_historical_var_es",
    "calculate_parametric_var",
    "calculate_parametric_var_es",
    "calculate_portfolio_var",
    "calculate_portfolio_volatility",
    "calculate_risk_contribution",
    "calculate_risk_contributions",
    "calculate_var_component_contribution",
    "calculate_var_es_snapshots",
    "select_tail_losses",
    "shrink_covariance_matrix",
    "validate_covariance_matrix",
    "validate_tail_risk_assumptions",
]


def calculate_portfolio_var(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: Any = None,
    proposed_trade: ProposedTrade | None = None,
    lookback: int = 50,
    confidence: Decimal = Decimal("0.95"),
    method: str = "parametric",
) -> Decimal:
    """Calculate portfolio Value-at-Risk.

    Args:
        portfolio_state: Current portfolio state.
        market_context: Market context containing returns/prices history.
        config: Active risk configuration profile.
        proposed_trade: Optional candidate proposed trade.
        lookback: Returns lookback length.
        confidence: Confidence level.
        method: VaR calculation method.

    Returns:
        Decimal: Value-at-Risk amount.
    """
    logger.info("calculate_portfolio_var called in package init.")
    var_snap, _ = calculate_var_es_snapshots(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_context=market_context,
        config=config,
        lookback=lookback,
        var_confidence=confidence,
        var_method=method,
    )
    return var_snap.result


def calculate_var_es_snapshots(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: Any = None,
    lookback: int = 50,
    var_confidence: Decimal = Decimal("0.95"),
    es_confidence: Decimal = Decimal("0.95"),
    var_method: str = "parametric",
    es_method: str = "parametric",
    cov_method: str = "parametric",
    ewma_decay: Decimal = Decimal("0.94"),
    shrinkage_intensity: Decimal = Decimal("0.1"),
    min_samples: int = 20,
    exclude_last: bool = True,
) -> tuple[VaRSnapshot, ExpectedShortfallSnapshot]:
    """Execute pre-trade Value-at-Risk and Expected Shortfall checks.

    Args:
        portfolio_state: Portfolio state snapshot.
        proposed_trade: Proposed trade candidate.
        market_context: Market context data (prices, returns history).
        config: Active risk configuration profile.
        lookback: Returns lookback length.
        var_confidence: Confidence level for VaR.
        es_confidence: Confidence level for ES.
        var_method: Method to evaluate VaR ('parametric', 'historical').
        es_method: Method to evaluate ES ('parametric', 'historical').
        cov_method: Method for covariance matrix estimation ('parametric', 'ewma').
        ewma_decay: EWMA decay factor.
        shrinkage_intensity: Shrinkage intensity.
        min_samples: Minimum required returns samples.
        exclude_last: Exclude the last bar.

    Returns:
        tuple[VaRSnapshot, ExpectedShortfallSnapshot]: Snapshot tuple.
    """
    logger.info("calculate_var_es_snapshots called in package init.")
    _ = config

    var_req = VaRCalculationRequest(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
        lookback=lookback,
        confidence=var_confidence,
        method=VaRMethod(var_method),
        cov_method=cov_method,
        ewma_decay=ewma_decay,
        shrinkage_intensity=shrinkage_intensity,
        min_samples=min_samples,
        exclude_last=exclude_last,
    )

    es_req = ExpectedShortfallRequest(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
        lookback=lookback,
        confidence=es_confidence,
        method=ExpectedShortfallMethod(es_method),
        cov_method=cov_method,
        ewma_decay=ewma_decay,
        shrinkage_intensity=shrinkage_intensity,
        min_samples=min_samples,
        exclude_last=exclude_last,
    )

    if var_req.method == VaRMethod.PARAMETRIC:
        var_snap = calculate_parametric_var(var_req)
    else:
        var_snap = calculate_historical_var(var_req)

    es_snap = calculate_expected_shortfall(es_req)

    return var_snap, es_snap
