"""Function-only public boundary for the Research domain."""

from collections.abc import Mapping
from typing import Literal

from app.services.research.artifacts import (
    build_research_migration_request,
    write_research_artifact,
)
from app.services.research.contracts.factories import (
    create_research_metric_registry,
    create_research_value,
    execute_research_value_operation,
    get_research_value_field,
    is_research_metric_calculator,
    is_research_value,
    project_research_value,
)
from app.services.research.data import (
    clean_dataset,
    enrich_dataset,
    prepare_research_dataset,
    validate_dataset,
)
from app.services.research.features import (
    build_research_feature_frame,
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    rolling_hurst,
    simple_returns,
)
from app.services.research.intelligence import (
    assess_intelligence_applicability,
    build_fundamental_source_evidence,
    build_sentiment_source_evidence,
    project_intelligence_evidence,
)
from app.services.research.leakage import (
    enforce_time_split,
    mask_research_artifact,
    validate_no_lookahead_features,
)
from app.services.research.market_structure import (
    build_market_structure_profile,
    build_strategy_fit,
    build_validation_summary,
    calibrate_market_structure,
    evaluate_market_structure_quality,
    label_realized_market_behavior,
)
from app.services.research.metrics import (
    build_core_metric_profile,
    build_default_registry,
)
from app.services.research.modeling import (
    analyze_cluster_outperformance,
    attach_cluster_labels,
    build_unsupervised_insight_report,
    cluster_feature_space,
    identify_pca_risk_factors,
    run_pca,
    run_unsupervised_research,
    summarize_investment_data,
)
from app.services.research.profiles import (
    build_dashboard_summary,
    build_profile_summary,
    build_research_profile_snapshot,
    build_research_scorecard,
    compare_research_profiles,
    generate_multi_symbol_report,
    render_profile_comparison,
    render_research_report,
    run_edge_lab_profile,
)
from app.services.research.seasonality import (
    active_sessions_for_hour,
    run_seasonality,
    session_hours_payload,
    session_label_for_hour,
    tag_sessions,
)
from app.services.research.statistics import (
    benjamini_hochberg,
    block_bootstrap_ci,
    block_bootstrap_distribution,
    compute_null_percentile,
    exceeds_null_threshold,
    holm_bonferroni,
    null_distribution_stats,
    permutation_test,
    r_space_null,
    random_entry_null,
    session_randomized_null,
    shuffle_returns_null,
)
from app.services.research.studies import (
    classify_symbol,
    compare_to_null,
    get_acceptance_criteria,
    run_eds_mean_reversion,
    run_eds_null_baseline,
    run_eds_session,
    run_eds_trend_persistence,
)


def get_public_api_classifications() -> Mapping[str, Literal["stable"]]:
    """Return the immutable Research public API classification map."""
    from app.services.research.contracts import PUBLIC_API_CLASSIFICATIONS

    return PUBLIC_API_CLASSIFICATIONS


__all__ = (
    "active_sessions_for_hour",
    "analyze_cluster_outperformance",
    "assess_intelligence_applicability",
    "attach_cluster_labels",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "block_bootstrap_distribution",
    "build_core_metric_profile",
    "build_dashboard_summary",
    "build_default_registry",
    "build_fundamental_source_evidence",
    "build_market_structure_profile",
    "build_profile_summary",
    "build_research_feature_frame",
    "build_research_migration_request",
    "build_research_profile_snapshot",
    "build_research_scorecard",
    "build_sentiment_source_evidence",
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
    "create_research_metric_registry",
    "create_research_value",
    "enforce_time_split",
    "enrich_dataset",
    "evaluate_market_structure_quality",
    "exceeds_null_threshold",
    "execute_research_value_operation",
    "forward_max_adverse_excursion",
    "forward_max_favorable_excursion",
    "forward_returns",
    "generate_multi_symbol_report",
    "get_acceptance_criteria",
    "get_public_api_classifications",
    "get_research_value_field",
    "holm_bonferroni",
    "hurst_exponent",
    "identify_pca_risk_factors",
    "is_research_metric_calculator",
    "is_research_value",
    "label_realized_market_behavior",
    "log_returns",
    "mask_research_artifact",
    "null_distribution_stats",
    "permutation_test",
    "prepare_research_dataset",
    "project_intelligence_evidence",
    "project_research_value",
    "r_space_null",
    "random_entry_null",
    "render_profile_comparison",
    "render_research_report",
    "rolling_hurst",
    "run_edge_lab_profile",
    "run_eds_mean_reversion",
    "run_eds_null_baseline",
    "run_eds_session",
    "run_eds_trend_persistence",
    "run_pca",
    "run_seasonality",
    "run_unsupervised_research",
    "session_hours_payload",
    "session_label_for_hour",
    "session_randomized_null",
    "shuffle_returns_null",
    "simple_returns",
    "summarize_investment_data",
    "tag_sessions",
    "validate_dataset",
    "validate_no_lookahead_features",
    "write_research_artifact",
)
