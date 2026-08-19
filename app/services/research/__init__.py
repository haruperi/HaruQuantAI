"""Function-only public boundary for the Research domain."""

import typing
from collections.abc import Mapping
from typing import Literal

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.research.artifacts import (
        build_candidate_profile,
        build_research_migration_request,
        build_scenario_evidence_port,
        parse_candidate_profile,
        record_expectancy_review_evidence,
        write_research_artifact,
    )
    from app.services.research.contracts.evidence_fields import (
        build_research_source_classification,
        parse_research_source_classification,
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
        project_point_in_time_evidence,
        validate_dataset,
    )
    from app.services.research.drift import (
        build_performance_drift_evidence,
        load_latest_performance_drift_evidence,
        monitor_performance_drift,
        parse_performance_drift_evidence,
        persist_performance_drift_evidence,
        propose_drift_suspension,
    )
    from app.services.research.expectancy import (
        apply_expectancy_transition,
        build_approved_expectancy_profile,
        build_expectancy_profile,
        build_risk_expectancy_provider,
        build_strategy_expectancy_provider,
        evaluate_expectancy_eligibility,
        get_min_reward_risk_override,
        is_governance_transition_permitted,
        load_eligible_expectancy_profile,
        load_expectancy_profile,
        parse_approved_expectancy_profile,
        persist_expectancy_profile,
        transition_expectancy_governance,
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
        build_market_assumption_evidence,
        build_market_structure_profile,
        build_strategy_fit,
        build_validation_summary,
        calibrate_market_structure,
        evaluate_market_structure_quality,
        label_realized_market_behavior,
        parse_market_assumption_evidence,
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
    from app.services.research.runs import (
        load_research_experiments,
        load_research_run_batches,
        load_research_runs,
        persist_research_experiment,
        persist_research_run,
        persist_research_run_batch,
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
    from app.services.research.stress_evidence import (
        build_reasoned_stress_shock,
        build_registered_stress_scenario,
        build_stress_calibration_provider,
        build_stress_scenario_evidence,
        derive_historical_stress_shock,
        get_stress_scenario_catalog,
        load_latest_stress_scenario_evidence,
        parse_stress_scenario_evidence,
        persist_stress_scenario_evidence,
        validate_shock_basis,
    )
    from app.services.research.studies import (
        build_strategy_evidence_bundle,
        classify_symbol,
        compare_to_null,
        get_acceptance_criteria,
        parse_strategy_evidence_bundle,
        run_eds_mean_reversion,
        run_eds_null_baseline,
        run_eds_session,
        run_eds_trend_persistence,
    )

# Public export name to the module and attribute that owns it. Resolved on first
# access so importing this boundary never loads every Research feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "active_sessions_for_hour": (
        "app.services.research.seasonality",
        "active_sessions_for_hour",
    ),
    "analyze_cluster_outperformance": (
        "app.services.research.modeling",
        "analyze_cluster_outperformance",
    ),
    "apply_expectancy_transition": (
        "app.services.research.expectancy",
        "apply_expectancy_transition",
    ),
    "assess_intelligence_applicability": (
        "app.services.research.intelligence",
        "assess_intelligence_applicability",
    ),
    "attach_cluster_labels": (
        "app.services.research.modeling",
        "attach_cluster_labels",
    ),
    "benjamini_hochberg": ("app.services.research.statistics", "benjamini_hochberg"),
    "block_bootstrap_ci": ("app.services.research.statistics", "block_bootstrap_ci"),
    "block_bootstrap_distribution": (
        "app.services.research.statistics",
        "block_bootstrap_distribution",
    ),
    "build_approved_expectancy_profile": (
        "app.services.research.expectancy",
        "build_approved_expectancy_profile",
    ),
    "build_candidate_profile": (
        "app.services.research.artifacts",
        "build_candidate_profile",
    ),
    "build_core_metric_profile": (
        "app.services.research.metrics",
        "build_core_metric_profile",
    ),
    "build_dashboard_summary": (
        "app.services.research.profiles",
        "build_dashboard_summary",
    ),
    "build_default_registry": (
        "app.services.research.metrics",
        "build_default_registry",
    ),
    "build_expectancy_profile": (
        "app.services.research.expectancy",
        "build_expectancy_profile",
    ),
    "build_fundamental_source_evidence": (
        "app.services.research.intelligence",
        "build_fundamental_source_evidence",
    ),
    "build_market_assumption_evidence": (
        "app.services.research.market_structure",
        "build_market_assumption_evidence",
    ),
    "build_market_structure_profile": (
        "app.services.research.market_structure",
        "build_market_structure_profile",
    ),
    "build_performance_drift_evidence": (
        "app.services.research.drift",
        "build_performance_drift_evidence",
    ),
    "build_profile_summary": (
        "app.services.research.profiles",
        "build_profile_summary",
    ),
    "build_reasoned_stress_shock": (
        "app.services.research.stress_evidence",
        "build_reasoned_stress_shock",
    ),
    "build_registered_stress_scenario": (
        "app.services.research.stress_evidence",
        "build_registered_stress_scenario",
    ),
    "build_research_feature_frame": (
        "app.services.research.features",
        "build_research_feature_frame",
    ),
    "build_research_migration_request": (
        "app.services.research.artifacts",
        "build_research_migration_request",
    ),
    "build_research_profile_snapshot": (
        "app.services.research.profiles",
        "build_research_profile_snapshot",
    ),
    "build_research_scorecard": (
        "app.services.research.profiles",
        "build_research_scorecard",
    ),
    "build_research_source_classification": (
        "app.services.research.contracts.evidence_fields",
        "build_research_source_classification",
    ),
    "build_risk_expectancy_provider": (
        "app.services.research.expectancy",
        "build_risk_expectancy_provider",
    ),
    "build_scenario_evidence_port": (
        "app.services.research.artifacts",
        "build_scenario_evidence_port",
    ),
    "build_sentiment_source_evidence": (
        "app.services.research.intelligence",
        "build_sentiment_source_evidence",
    ),
    "build_strategy_evidence_bundle": (
        "app.services.research.studies",
        "build_strategy_evidence_bundle",
    ),
    "build_strategy_expectancy_provider": (
        "app.services.research.expectancy",
        "build_strategy_expectancy_provider",
    ),
    "build_strategy_fit": (
        "app.services.research.market_structure",
        "build_strategy_fit",
    ),
    "build_stress_calibration_provider": (
        "app.services.research.stress_evidence",
        "build_stress_calibration_provider",
    ),
    "build_stress_scenario_evidence": (
        "app.services.research.stress_evidence",
        "build_stress_scenario_evidence",
    ),
    "build_unsupervised_insight_report": (
        "app.services.research.modeling",
        "build_unsupervised_insight_report",
    ),
    "build_validation_summary": (
        "app.services.research.market_structure",
        "build_validation_summary",
    ),
    "calibrate_market_structure": (
        "app.services.research.market_structure",
        "calibrate_market_structure",
    ),
    "classify_symbol": ("app.services.research.studies", "classify_symbol"),
    "clean_dataset": ("app.services.research.data", "clean_dataset"),
    "cluster_feature_space": (
        "app.services.research.modeling",
        "cluster_feature_space",
    ),
    "compare_research_profiles": (
        "app.services.research.profiles",
        "compare_research_profiles",
    ),
    "compare_to_null": ("app.services.research.studies", "compare_to_null"),
    "compute_null_percentile": (
        "app.services.research.statistics",
        "compute_null_percentile",
    ),
    "create_research_metric_registry": (
        "app.services.research.contracts.factories",
        "create_research_metric_registry",
    ),
    "create_research_value": (
        "app.services.research.contracts.factories",
        "create_research_value",
    ),
    "derive_historical_stress_shock": (
        "app.services.research.stress_evidence",
        "derive_historical_stress_shock",
    ),
    "enforce_time_split": ("app.services.research.leakage", "enforce_time_split"),
    "enrich_dataset": ("app.services.research.data", "enrich_dataset"),
    "evaluate_expectancy_eligibility": (
        "app.services.research.expectancy",
        "evaluate_expectancy_eligibility",
    ),
    "evaluate_market_structure_quality": (
        "app.services.research.market_structure",
        "evaluate_market_structure_quality",
    ),
    "exceeds_null_threshold": (
        "app.services.research.statistics",
        "exceeds_null_threshold",
    ),
    "execute_research_value_operation": (
        "app.services.research.contracts.factories",
        "execute_research_value_operation",
    ),
    "forward_max_adverse_excursion": (
        "app.services.research.features",
        "forward_max_adverse_excursion",
    ),
    "forward_max_favorable_excursion": (
        "app.services.research.features",
        "forward_max_favorable_excursion",
    ),
    "forward_returns": ("app.services.research.features", "forward_returns"),
    "generate_multi_symbol_report": (
        "app.services.research.profiles",
        "generate_multi_symbol_report",
    ),
    "get_acceptance_criteria": (
        "app.services.research.studies",
        "get_acceptance_criteria",
    ),
    "get_min_reward_risk_override": (
        "app.services.research.expectancy",
        "get_min_reward_risk_override",
    ),
    "get_research_value_field": (
        "app.services.research.contracts.factories",
        "get_research_value_field",
    ),
    "get_stress_scenario_catalog": (
        "app.services.research.stress_evidence",
        "get_stress_scenario_catalog",
    ),
    "holm_bonferroni": ("app.services.research.statistics", "holm_bonferroni"),
    "hurst_exponent": ("app.services.research.features", "hurst_exponent"),
    "identify_pca_risk_factors": (
        "app.services.research.modeling",
        "identify_pca_risk_factors",
    ),
    "is_governance_transition_permitted": (
        "app.services.research.expectancy",
        "is_governance_transition_permitted",
    ),
    "is_research_metric_calculator": (
        "app.services.research.contracts.factories",
        "is_research_metric_calculator",
    ),
    "is_research_value": (
        "app.services.research.contracts.factories",
        "is_research_value",
    ),
    "label_realized_market_behavior": (
        "app.services.research.market_structure",
        "label_realized_market_behavior",
    ),
    "load_eligible_expectancy_profile": (
        "app.services.research.expectancy",
        "load_eligible_expectancy_profile",
    ),
    "load_expectancy_profile": (
        "app.services.research.expectancy",
        "load_expectancy_profile",
    ),
    "load_latest_performance_drift_evidence": (
        "app.services.research.drift",
        "load_latest_performance_drift_evidence",
    ),
    "load_latest_stress_scenario_evidence": (
        "app.services.research.stress_evidence",
        "load_latest_stress_scenario_evidence",
    ),
    "load_research_experiments": (
        "app.services.research.runs",
        "load_research_experiments",
    ),
    "load_research_run_batches": (
        "app.services.research.runs",
        "load_research_run_batches",
    ),
    "load_research_runs": ("app.services.research.runs", "load_research_runs"),
    "log_returns": ("app.services.research.features", "log_returns"),
    "mask_research_artifact": (
        "app.services.research.leakage",
        "mask_research_artifact",
    ),
    "monitor_performance_drift": (
        "app.services.research.drift",
        "monitor_performance_drift",
    ),
    "null_distribution_stats": (
        "app.services.research.statistics",
        "null_distribution_stats",
    ),
    "parse_approved_expectancy_profile": (
        "app.services.research.expectancy",
        "parse_approved_expectancy_profile",
    ),
    "parse_candidate_profile": (
        "app.services.research.artifacts",
        "parse_candidate_profile",
    ),
    "parse_market_assumption_evidence": (
        "app.services.research.market_structure",
        "parse_market_assumption_evidence",
    ),
    "parse_performance_drift_evidence": (
        "app.services.research.drift",
        "parse_performance_drift_evidence",
    ),
    "parse_research_source_classification": (
        "app.services.research.contracts.evidence_fields",
        "parse_research_source_classification",
    ),
    "parse_strategy_evidence_bundle": (
        "app.services.research.studies",
        "parse_strategy_evidence_bundle",
    ),
    "parse_stress_scenario_evidence": (
        "app.services.research.stress_evidence",
        "parse_stress_scenario_evidence",
    ),
    "permutation_test": ("app.services.research.statistics", "permutation_test"),
    "persist_expectancy_profile": (
        "app.services.research.expectancy",
        "persist_expectancy_profile",
    ),
    "persist_performance_drift_evidence": (
        "app.services.research.drift",
        "persist_performance_drift_evidence",
    ),
    "persist_research_experiment": (
        "app.services.research.runs",
        "persist_research_experiment",
    ),
    "persist_research_run": ("app.services.research.runs", "persist_research_run"),
    "persist_research_run_batch": (
        "app.services.research.runs",
        "persist_research_run_batch",
    ),
    "persist_stress_scenario_evidence": (
        "app.services.research.stress_evidence",
        "persist_stress_scenario_evidence",
    ),
    "prepare_research_dataset": (
        "app.services.research.data",
        "prepare_research_dataset",
    ),
    "project_intelligence_evidence": (
        "app.services.research.intelligence",
        "project_intelligence_evidence",
    ),
    "project_point_in_time_evidence": (
        "app.services.research.data",
        "project_point_in_time_evidence",
    ),
    "project_research_value": (
        "app.services.research.contracts.factories",
        "project_research_value",
    ),
    "propose_drift_suspension": (
        "app.services.research.drift",
        "propose_drift_suspension",
    ),
    "r_space_null": ("app.services.research.statistics", "r_space_null"),
    "random_entry_null": ("app.services.research.statistics", "random_entry_null"),
    "record_expectancy_review_evidence": (
        "app.services.research.artifacts",
        "record_expectancy_review_evidence",
    ),
    "render_profile_comparison": (
        "app.services.research.profiles",
        "render_profile_comparison",
    ),
    "render_research_report": (
        "app.services.research.profiles",
        "render_research_report",
    ),
    "rolling_hurst": ("app.services.research.features", "rolling_hurst"),
    "run_edge_lab_profile": ("app.services.research.profiles", "run_edge_lab_profile"),
    "run_eds_mean_reversion": (
        "app.services.research.studies",
        "run_eds_mean_reversion",
    ),
    "run_eds_null_baseline": ("app.services.research.studies", "run_eds_null_baseline"),
    "run_eds_session": ("app.services.research.studies", "run_eds_session"),
    "run_eds_trend_persistence": (
        "app.services.research.studies",
        "run_eds_trend_persistence",
    ),
    "run_pca": ("app.services.research.modeling", "run_pca"),
    "run_seasonality": ("app.services.research.seasonality", "run_seasonality"),
    "run_unsupervised_research": (
        "app.services.research.modeling",
        "run_unsupervised_research",
    ),
    "session_hours_payload": (
        "app.services.research.seasonality",
        "session_hours_payload",
    ),
    "session_label_for_hour": (
        "app.services.research.seasonality",
        "session_label_for_hour",
    ),
    "session_randomized_null": (
        "app.services.research.statistics",
        "session_randomized_null",
    ),
    "shuffle_returns_null": (
        "app.services.research.statistics",
        "shuffle_returns_null",
    ),
    "simple_returns": ("app.services.research.features", "simple_returns"),
    "summarize_investment_data": (
        "app.services.research.modeling",
        "summarize_investment_data",
    ),
    "tag_sessions": ("app.services.research.seasonality", "tag_sessions"),
    "transition_expectancy_governance": (
        "app.services.research.expectancy",
        "transition_expectancy_governance",
    ),
    "validate_dataset": ("app.services.research.data", "validate_dataset"),
    "validate_no_lookahead_features": (
        "app.services.research.leakage",
        "validate_no_lookahead_features",
    ),
    "validate_shock_basis": (
        "app.services.research.stress_evidence",
        "validate_shock_basis",
    ),
    "write_research_artifact": (
        "app.services.research.artifacts",
        "write_research_artifact",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public Research export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public Research export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


def get_public_api_classifications() -> Mapping[str, Literal["stable"]]:
    """Return the immutable Research public API classification map."""
    from app.services.research.contracts import PUBLIC_API_CLASSIFICATIONS

    return PUBLIC_API_CLASSIFICATIONS


__all__ = (
    "active_sessions_for_hour",
    "analyze_cluster_outperformance",
    "apply_expectancy_transition",
    "assess_intelligence_applicability",
    "attach_cluster_labels",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "block_bootstrap_distribution",
    "build_approved_expectancy_profile",
    "build_candidate_profile",
    "build_core_metric_profile",
    "build_dashboard_summary",
    "build_default_registry",
    "build_expectancy_profile",
    "build_fundamental_source_evidence",
    "build_market_assumption_evidence",
    "build_market_structure_profile",
    "build_performance_drift_evidence",
    "build_profile_summary",
    "build_reasoned_stress_shock",
    "build_registered_stress_scenario",
    "build_research_feature_frame",
    "build_research_migration_request",
    "build_research_profile_snapshot",
    "build_research_scorecard",
    "build_research_source_classification",
    "build_risk_expectancy_provider",
    "build_scenario_evidence_port",
    "build_sentiment_source_evidence",
    "build_strategy_evidence_bundle",
    "build_strategy_expectancy_provider",
    "build_strategy_fit",
    "build_stress_calibration_provider",
    "build_stress_scenario_evidence",
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
    "derive_historical_stress_shock",
    "enforce_time_split",
    "enrich_dataset",
    "evaluate_expectancy_eligibility",
    "evaluate_market_structure_quality",
    "exceeds_null_threshold",
    "execute_research_value_operation",
    "forward_max_adverse_excursion",
    "forward_max_favorable_excursion",
    "forward_returns",
    "generate_multi_symbol_report",
    "get_acceptance_criteria",
    "get_min_reward_risk_override",
    "get_public_api_classifications",
    "get_research_value_field",
    "get_stress_scenario_catalog",
    "holm_bonferroni",
    "hurst_exponent",
    "identify_pca_risk_factors",
    "is_governance_transition_permitted",
    "is_research_metric_calculator",
    "is_research_value",
    "label_realized_market_behavior",
    "load_eligible_expectancy_profile",
    "load_expectancy_profile",
    "load_latest_performance_drift_evidence",
    "load_latest_stress_scenario_evidence",
    "load_research_experiments",
    "load_research_run_batches",
    "load_research_runs",
    "log_returns",
    "mask_research_artifact",
    "monitor_performance_drift",
    "null_distribution_stats",
    "parse_approved_expectancy_profile",
    "parse_candidate_profile",
    "parse_market_assumption_evidence",
    "parse_performance_drift_evidence",
    "parse_research_source_classification",
    "parse_strategy_evidence_bundle",
    "parse_stress_scenario_evidence",
    "permutation_test",
    "persist_expectancy_profile",
    "persist_performance_drift_evidence",
    "persist_research_experiment",
    "persist_research_run",
    "persist_research_run_batch",
    "persist_stress_scenario_evidence",
    "prepare_research_dataset",
    "project_intelligence_evidence",
    "project_point_in_time_evidence",
    "project_research_value",
    "propose_drift_suspension",
    "r_space_null",
    "random_entry_null",
    "record_expectancy_review_evidence",
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
    "transition_expectancy_governance",
    "validate_dataset",
    "validate_no_lookahead_features",
    "validate_shock_basis",
    "write_research_artifact",
)
