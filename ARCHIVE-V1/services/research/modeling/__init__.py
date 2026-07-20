"""Modeling services for AI trading workflows.

Purpose:
    Modeling services for AI trading workflows.

Classes:
    None.

Functions:
    None.
"""

from app.services.research.modeling.contracts import (
    UnsupervisedResearchConfig,
    UnsupervisedResearchRequest,
    UnsupervisedResearchResult,
)
from app.services.research.modeling.feature_sets import (
    FeatureSetFrame,
    build_market_regime_feature_frame,
)
from app.services.research.modeling.service import UnsupervisedResearchService
from app.services.research.modeling.unsupervised import (
    ClusterModelResult,
    PcaModelResult,
    attach_cluster_labels,
    cluster_feature_space,
    run_pca,
)
from app.services.research.modeling.unsupervised_insights import (
    ClusterOutperformance,
    InvestmentDataSummary,
    PcaRiskFactor,
    SignalAdaptationResult,
    UnsupervisedInsightReport,
    adapt_signals_by_cluster,
    analyze_cluster_outperformance,
    build_unsupervised_insight_report,
    compute_forward_returns,
    identify_pca_risk_factors,
    summarize_investment_data,
)

__all__ = [
    "ClusterModelResult",
    "ClusterOutperformance",
    "FeatureSetFrame",
    "InvestmentDataSummary",
    "PcaModelResult",
    "PcaRiskFactor",
    "SignalAdaptationResult",
    "UnsupervisedInsightReport",
    "UnsupervisedResearchConfig",
    "UnsupervisedResearchRequest",
    "UnsupervisedResearchResult",
    "UnsupervisedResearchService",
    "adapt_signals_by_cluster",
    "analyze_cluster_outperformance",
    "attach_cluster_labels",
    "build_market_regime_feature_frame",
    "build_unsupervised_insight_report",
    "cluster_feature_space",
    "compute_forward_returns",
    "identify_pca_risk_factors",
    "run_pca",
    "summarize_investment_data",
]
