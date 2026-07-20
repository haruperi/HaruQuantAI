"""Correlation and cluster risk engine package."""

from app.services.risk.correlation.contracts import (
    AlignedReturns,
    ClosedBar,
    ClusterExposureAssessment,
    ComponentRiskContribution,
    CorrelationAlignmentPolicy,
    CorrelationCluster,
    CorrelationFallbackContext,
    CorrelationMethod,
    CovarianceMatrix,
    ReturnMethod,
    ReturnSeries,
)
from app.services.risk.correlation.engine import (
    CorrelationEngine,
    _get_symbol_gross_exposure,
    build_correlation_clusters,
    calculate_cluster_exposure,
    calculate_cluster_exposures,
    calculate_component_risk_contribution,
    calculate_correlation_impact,
    calculate_correlation_matrix,
    calculate_correlation_multiplier,
    calculate_correlation_snapshot,
    calculate_marginal_correlation,
    calculate_portfolio_returns,
    calculate_symbol_cluster_exposure,
    detect_correlation_spikes,
    evaluate_proposed_trade_correlation,
)
from app.services.risk.correlation.fallbacks import (
    build_conservative_correlation_snapshot,
    resolve_correlation_fallback,
    should_fail_closed_for_missing_correlation,
)
from app.services.risk.correlation.returns import (
    align_return_series,
    build_return_series,
    calculate_pearson,
    calculate_returns,
    validate_correlation_inputs,
)


class ReturnType:
    """Supported returns calculation types (V1 compatibility)."""

    CLOSE_TO_CLOSE = "close_to_close"
    LOG = "log"
    OPEN_TO_CLOSE = "open_to_close"
    SIGMA_NORMALIZED = "sigma_normalized"


__all__ = [
    "AlignedReturns",
    "ClosedBar",
    "ClusterExposureAssessment",
    "ComponentRiskContribution",
    "CorrelationAlignmentPolicy",
    "CorrelationCluster",
    "CorrelationEngine",
    "CorrelationFallbackContext",
    "CorrelationMethod",
    "CovarianceMatrix",
    "ReturnMethod",
    "ReturnSeries",
    "ReturnType",
    "_get_symbol_gross_exposure",
    "align_return_series",
    "build_conservative_correlation_snapshot",
    "build_correlation_clusters",
    "build_return_series",
    "calculate_cluster_exposure",
    "calculate_cluster_exposures",
    "calculate_component_risk_contribution",
    "calculate_correlation_impact",
    "calculate_correlation_matrix",
    "calculate_correlation_multiplier",
    "calculate_correlation_snapshot",
    "calculate_marginal_correlation",
    "calculate_pearson",
    "calculate_portfolio_returns",
    "calculate_returns",
    "calculate_symbol_cluster_exposure",
    "detect_correlation_spikes",
    "evaluate_proposed_trade_correlation",
    "resolve_correlation_fallback",
    "should_fail_closed_for_missing_correlation",
    "validate_correlation_inputs",
]
