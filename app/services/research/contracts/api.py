"""Classifications for the implemented Research contract surface."""

from __future__ import annotations

from types import MappingProxyType
from typing import Literal

from app.utils import get_logger

logger = get_logger(__name__)

logger.debug("Defining implemented Research contract API classifications")

_RESEARCH_PUBLIC_CALLABLES = (
    "assess_intelligence_applicability",
    "build_fundamental_source_evidence",
    "build_sentiment_source_evidence",
    "create_research_metric_registry",
    "create_research_value",
    "execute_research_value_operation",
    "get_research_value_field",
    "is_research_metric_calculator",
    "is_research_value",
    "project_research_value",
    "project_intelligence_evidence",
    "get_public_api_classifications",
    "active_sessions_for_hour",
    "analyze_cluster_outperformance",
    "attach_cluster_labels",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "block_bootstrap_distribution",
    "build_core_metric_profile",
    "build_dashboard_summary",
    "build_default_registry",
    "build_market_structure_profile",
    "build_profile_summary",
    "build_research_feature_frame",
    "build_research_migration_request",
    "build_research_profile_snapshot",
    "build_research_scorecard",
    "build_strategy_fit",
    "build_unsupervised_insight_report",
    "build_validation_summary",
    "calibrate_market_structure",
    "classify_symbol",
    "clean_dataset",
    "cluster_feature_space",
    "compare_research_profiles",
    "compare_to_null",
    "compute_null_percentile",
    "enforce_time_split",
    "enrich_dataset",
    "evaluate_market_structure_quality",
    "exceeds_null_threshold",
    "forward_max_adverse_excursion",
    "forward_max_favorable_excursion",
    "forward_returns",
    "generate_multi_symbol_report",
    "get_acceptance_criteria",
    "holm_bonferroni",
    "hurst_exponent",
    "identify_pca_risk_factors",
    "label_realized_market_behavior",
    "log_returns",
    "mask_research_artifact",
    "null_distribution_stats",
    "permutation_test",
    "prepare_research_dataset",
    "random_entry_null",
    "render_profile_comparison",
    "render_research_report",
    "run_eds_mean_reversion",
    "run_eds_null_baseline",
    "run_eds_session",
    "run_eds_trend_persistence",
    "run_edge_lab_profile",
    "run_pca",
    "run_seasonality",
    "run_unsupervised_research",
    "r_space_null",
    "rolling_hurst",
    "session_hours_payload",
    "session_label_for_hour",
    "session_randomized_null",
    "simple_returns",
    "shuffle_returns_null",
    "summarize_investment_data",
    "tag_sessions",
    "validate_dataset",
    "validate_no_lookahead_features",
    "write_research_artifact",
)

PUBLIC_API_CLASSIFICATIONS: MappingProxyType[str, Literal["stable"]] = MappingProxyType(
    dict.fromkeys(_RESEARCH_PUBLIC_CALLABLES, "stable")
)

__all__ = ("PUBLIC_API_CLASSIFICATIONS",)
