"""Public Research unsupervised modeling API."""

from app.services.research.modeling.clustering import (
    attach_cluster_labels,
    cluster_feature_space,
)
from app.services.research.modeling.decomposition import run_pca
from app.services.research.modeling.insights import (
    analyze_cluster_outperformance,
    build_unsupervised_insight_report,
    identify_pca_risk_factors,
    summarize_investment_data,
)
from app.services.research.modeling.workflow import run_unsupervised_research

__all__ = (
    "analyze_cluster_outperformance",
    "attach_cluster_labels",
    "build_unsupervised_insight_report",
    "cluster_feature_space",
    "identify_pca_risk_factors",
    "run_pca",
    "run_unsupervised_research",
    "summarize_investment_data",
)
