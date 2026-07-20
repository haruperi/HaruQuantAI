"""Public research service exports.

Purpose:
    Public research service exports.

Classes:
    None.

Functions:
    __getattr__: Support internal getattr processing.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from app.services.utils.standard import (
    standardize_domain_exports,
    standardize_tool_callable,
)

from ._common import __getattr__ as _resolve_research_attr
from ._common import research_modeling_module

_LOCAL_EXPORTS = {
    # classifier.py tools
    "ClassificationResult": "classifier",
    "EdgeClass": "classifier",
    "EdgeSummary": "classifier",
    "classify_symbol": "classifier",
    # config.py tools
    "BootstrapConfig": "config",
    "DataConfig": "config",
    "EdgeLabConfig": "config",
    "MarketStructureConfig": "config",
    "MeanReversionConfig": "config",
    "NullModelsConfig": "config",
    "PermutationConfig": "config",
    "SessionConfig": "config",
    "SessionEdgeConfig": "config",
    "TrendPersistenceConfig": "config",
    "create_config": "config",
    # core_metrics.base.py tools
    "MetricCalculator": "core_metrics.base",
    "MetricContext": "core_metrics.base",
    "MetricValue": "core_metrics.base",
    # core_metrics.registry.py tools
    "MetricRegistry": "core_metrics.registry",
    # core_metrics.service.py tools
    "CandlesCalculator": "core_metrics.service",
    "CoreMetricProfile": "core_metrics.service",
    "RangesCalculator": "core_metrics.service",
    "ReturnsCalculator": "core_metrics.service",
    "RocCalculator": "core_metrics.service",
    "SpreadCalculator": "core_metrics.service",
    "VolatilityCalculator": "core_metrics.service",
    "VolumeActivityCalculator": "core_metrics.service",
    "build_core_metric_profile": "core_metrics.service",
    "build_default_registry": "core_metrics.service",
    # data.cleaning.py tools
    "CleaningConfig": "data.cleaning",
    "clean_dataset": "data.cleaning",
    # data.enrichment.py tools
    "EnrichmentConfig": "data.enrichment",
    "enrich_dataset": "data.enrichment",
    # data.models.py tools
    "CanonicalOHLCVSSchema": "data.models",
    "CleaningAction": "data.models",
    "DataQualityReportModel": "data.models",
    "DatasetIssue": "data.models",
    "PreparedDataset": "data.models",
    # data.preparation.py tools
    "prepare_research_dataset": "data.preparation",
    # data.validation.py tools
    "validate_dataset": "data.validation",
    # eds_mean_reversion.py tools
    "run_eds_mean_reversion": "eds_mean_reversion",
    # eds_null_models.py tools
    "compare_to_null": "eds_null_models",
    "get_acceptance_criteria": "eds_null_models",
    "run_eds_null_baseline": "eds_null_models",
    # eds_session.py tools
    "compute_session_statistics": "eds_session",
    "run_eds_session": "eds_session",
    "run_session_breakout_strategy": "eds_session",
    "run_session_fade_strategy": "eds_session",
    # eds_trend_persistence.py tools
    "run_eds_trend_persistence": "eds_trend_persistence",
    # features.calculations.py tools
    "adr": "features.calculations",
    "atr": "features.calculations",
    "atr_percent": "features.calculations",
    "bb_percent_b": "features.calculations",
    "bb_width": "features.calculations",
    "bollinger_bands": "features.calculations",
    "detect_trend_regime": "features.calculations",
    "detect_volatility_regime": "features.calculations",
    "donchian_channel": "features.calculations",
    "ema": "features.calculations",
    "forward_max_adverse_excursion": "features.calculations",
    "forward_max_favorable_excursion": "features.calculations",
    "forward_returns": "features.calculations",
    "hurst_exponent": "features.calculations",
    "log_returns": "features.calculations",
    "momentum": "features.calculations",
    "percent_rank": "features.calculations",
    "pivot_points": "features.calculations",
    "rate_of_change": "features.calculations",
    "rolling_hurst": "features.calculations",
    "rolling_percentile_rank": "features.calculations",
    "rsi": "features.calculations",
    "simple_returns": "features.calculations",
    "sma": "features.calculations",
    "std": "features.calculations",
    "zscore": "features.calculations",
    # features.leakage.py tools
    "TimeSplitResult": "features.leakage",
    "dump_masked_research_json": "features.leakage",
    "enforce_time_split": "features.leakage",
    "mask_research_artifact": "features.leakage",
    "validate_no_lookahead_features": "features.leakage",
    # features.pipeline.py tools
    "FeaturePipeline": "features.pipeline",
    "FeatureSpec": "features.pipeline",
    # market_structure.py tools
    "MarketStructureProfile": "market_structure",
    "TrendLeg": "market_structure",
    "TrendScoreRow": "market_structure",
    "TrendSwingPoint": "market_structure",
    "build_market_structure_profile": "market_structure",
    "build_market_structure_research_profile": "market_structure",
    # market_structure_calibration.py tools
    "MarketStructureCalibrationCandidate": "market_structure_calibration",
    "build_calibration_grid": "market_structure_calibration",
    "classify_with_candidate": "market_structure_calibration",
    "evaluate_calibration_candidates": "market_structure_calibration",
    # market_structure_metric_calibration.py tools
    "MarketStructureMetricCalibrationCandidate": "market_structure_metric_calibration",
    "build_metric_calibration_grid": "market_structure_metric_calibration",
    "evaluate_metric_calibration_candidates": "market_structure_metric_calibration",
    # market_structure_profile_calibration.py tools
    "evaluate_profile_calibration": "market_structure_profile_calibration",
    # market_structure_profiles.py tools
    "resolve_market_structure_profile": "market_structure_profiles",
    "resolve_market_structure_profile_overrides": "market_structure_profiles",
    "symbol_class": "market_structure_profiles",
    "timeframe_bucket": "market_structure_profiles",
    # market_structure_robustness.py tools
    "build_market_structure_robustness_report": "market_structure_robustness",
    # market_structure_stability.py tools
    "build_market_structure_stability_report": "market_structure_stability",
    # market_structure_strategy_fit.py tools
    "build_strategy_fit": "market_structure_strategy_fit",
    # market_structure_validation.py tools
    "build_validation_summary": "market_structure_validation",
    "confidence_bucket": "market_structure_validation",
    "label_realized_market_behavior": "market_structure_validation",
    # modeling.contracts.py tools
    "UnsupervisedResearchConfig": "modeling.contracts",
    "UnsupervisedResearchRequest": "modeling.contracts",
    "UnsupervisedResearchResult": "modeling.contracts",
    # modeling.feature_sets.py tools
    "FeatureSetFrame": "modeling.feature_sets",
    "build_market_regime_feature_frame": "modeling.feature_sets",
    # modeling.service.py tools
    "UnsupervisedResearchService": "modeling.service",
    # modeling.unsupervised.py tools
    "ClusterModelResult": "modeling.unsupervised",
    "PcaModelResult": "modeling.unsupervised",
    "attach_cluster_labels": "modeling.unsupervised",
    "cluster_feature_space": "modeling.unsupervised",
    "run_pca": "modeling.unsupervised",
    # modeling.unsupervised_insights.py tools
    "ClusterOutperformance": "modeling.unsupervised_insights",
    "InvestmentDataSummary": "modeling.unsupervised_insights",
    "PcaRiskFactor": "modeling.unsupervised_insights",
    "SignalAdaptationResult": "modeling.unsupervised_insights",
    "UnsupervisedInsightReport": "modeling.unsupervised_insights",
    "adapt_signals_by_cluster": "modeling.unsupervised_insights",
    "analyze_cluster_outperformance": "modeling.unsupervised_insights",
    "build_unsupervised_insight_report": "modeling.unsupervised_insights",
    "compute_forward_returns": "modeling.unsupervised_insights",
    "identify_pca_risk_factors": "modeling.unsupervised_insights",
    "summarize_investment_data": "modeling.unsupervised_insights",
    # null_models.py tools
    "benjamini_hochberg": "null_models",
    "block_bootstrap_ci": "null_models",
    "block_bootstrap_distribution": "null_models",
    "compute_null_percentile": "null_models",
    "exceeds_null_threshold": "null_models",
    "holm_bonferroni": "null_models",
    "null_distribution_stats": "null_models",
    "permutation_test": "null_models",
    "r_space_null": "null_models",
    "random_entry_null": "null_models",
    "session_randomized_null": "null_models",
    "shuffle_returns_null": "null_models",
    # profile_reporting.py tools
    "build_dashboard_summary": "profile_reporting",
    "build_profile_summary": "profile_reporting",
    "comparison_report_markdown": "profile_reporting",
    "save_json_report": "profile_reporting",
    "save_markdown_report": "profile_reporting",
    "snapshot_report_json": "profile_reporting",
    "snapshot_report_markdown": "profile_reporting",
    # profile_snapshot.py tools
    "build_edge_profile_snapshot": "profile_snapshot",
    # reporting.py tools
    "generate_multi_symbol_report": "reporting",
    "print_result_summary": "reporting",
    "result_to_markdown": "reporting",
    "result_to_summary": "reporting",
    "save_json": "reporting",
    "save_markdown": "reporting",
    # results_schema.py tools
    "EdgeResult": "results_schema",
    "EdgeStats": "results_schema",
    "TradeSample": "results_schema",
    # scorecard.py tools
    "SCORECARD_SPEC_VERSION": "scorecard",
    "build_edge_lab_scorecard_report": "scorecard",
    # seasonality.py tools
    "SeasonalityFilters": "seasonality",
    "run_seasonality": "seasonality",
    # session_config.py tools
    "active_sessions_for_hour": "session_config",
    "session_hours_payload": "session_config",
    "session_label_for_hour": "session_config",
    "tag_sessions": "session_config",
    # standard_tools.py tools
    "build_research_evidence_pack": "standard_tools",
    "calculate_adr": "standard_tools",
    "calculate_atr": "standard_tools",
    "calculate_correlation_matrix": "standard_tools",
    "calculate_regime_features": "standard_tools",
    "calculate_returns": "standard_tools",
    "calculate_seasonality_statistics": "standard_tools",
    "calculate_session_statistics": "standard_tools",
    "calculate_spread_statistics": "standard_tools",
    "calculate_volatility": "standard_tools",
    "check_contradictory_evidence": "standard_tools",
    "check_data_snooping_risk": "standard_tools",
    "check_hypothesis_testability": "standard_tools",
    "check_lookahead_bias_risk": "standard_tools",
    "check_sample_size": "standard_tools",
    "classify_news_impact": "standard_tools",
    "create_news_blackout_windows": "standard_tools",
    "detect_breakout_conditions": "standard_tools",
    "detect_market_regime": "standard_tools",
    "detect_mean_reversion_conditions": "standard_tools",
    "detect_trend_strength": "standard_tools",
    "fetch_forexfactory_calendar": "standard_tools",
    "fetch_forexfactory_instrument_page": "standard_tools",
    "fetch_forexfactory_news": "standard_tools",
    "fetch_forexfactory_sentiment": "standard_tools",
    "filter_events_by_symbol": "standard_tools",
    "generate_research_hypothesis": "standard_tools",
    "parse_calendar_events": "standard_tools",
    "parse_news_items": "standard_tools",
    "parse_sentiment_snapshot": "standard_tools",
    "score_research_hypothesis": "standard_tools",
}

# app.services.utils.validators dataset tools
_DATASET_EXPORTS = {
    "DataSource": ("app.services.utils.validators", "DataSource"),
    "OHLCVSchema": ("app.services.utils.validators", "OHLCVSchema"),
}

# app.services.analytics tools
_ANALYTICS_EXPORTS = {
    "calmar_ratio": ("app.services.analytics.ratios", "calmar_ratio"),
    "expectancy": ("app.services.analytics.ratios", "expectancy"),
    "max_drawdown": ("app.services.analytics.drawdowns", "max_drawdown"),
    "median_mae_mfe": ("app.services.analytics.metrics", "median_mae_mfe"),
    "profit_factor": ("app.services.analytics.ratios", "profit_factor"),
    "sharpe_ratio": ("app.services.analytics.ratios", "sharpe_ratio"),
    "sortino_ratio": ("app.services.analytics.ratios", "sortino_ratio"),
    "win_rate": ("app.services.analytics.metrics", "win_rate_fraction"),
}

__all__ = [
    "active_sessions_for_hour",
    "adapt_signals_by_cluster",
    "adr",
    "analyze_cluster_outperformance",
    "atr",
    "atr_percent",
    "attach_cluster_labels",
    "bb_percent_b",
    "bb_width",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "block_bootstrap_distribution",
    "bollinger_bands",
    "build_calibration_grid",
    "build_core_metric_profile",
    "build_dashboard_summary",
    "build_default_registry",
    "build_edge_lab_scorecard_report",
    "build_edge_profile_snapshot",
    "build_market_regime_feature_frame",
    "build_market_structure_profile",
    "build_market_structure_research_profile",
    "build_market_structure_robustness_report",
    "build_market_structure_stability_report",
    "build_metric_calibration_grid",
    "build_profile_summary",
    "build_research_evidence_pack",
    "build_strategy_fit",
    "build_unsupervised_insight_report",
    "build_validation_summary",
    "calculate_adr",
    "calculate_atr",
    "calculate_correlation_matrix",
    "calculate_regime_features",
    "calculate_returns",
    "calculate_seasonality_statistics",
    "calculate_session_statistics",
    "calculate_spread_statistics",
    "calculate_volatility",
    "calmar_ratio",
    "check_contradictory_evidence",
    "check_data_snooping_risk",
    "check_hypothesis_testability",
    "check_lookahead_bias_risk",
    "check_sample_size",
    "classify_news_impact",
    "classify_symbol",
    "classify_with_candidate",
    "clean_dataset",
    "cluster_feature_space",
    "compare_to_null",
    "comparison_report_markdown",
    "compute_forward_returns",
    "compute_null_percentile",
    "compute_session_statistics",
    "confidence_bucket",
    "create_config",
    "create_news_blackout_windows",
    "detect_breakout_conditions",
    "detect_market_regime",
    "detect_mean_reversion_conditions",
    "detect_trend_regime",
    "detect_trend_strength",
    "detect_volatility_regime",
    "donchian_channel",
    "dump_masked_research_json",
    "ema",
    "enforce_time_split",
    "enrich_dataset",
    "evaluate_calibration_candidates",
    "evaluate_metric_calibration_candidates",
    "evaluate_profile_calibration",
    "exceeds_null_threshold",
    "expectancy",
    "fetch_forexfactory_calendar",
    "fetch_forexfactory_instrument_page",
    "fetch_forexfactory_news",
    "fetch_forexfactory_sentiment",
    "filter_events_by_symbol",
    "forward_max_adverse_excursion",
    "forward_max_favorable_excursion",
    "forward_returns",
    "generate_multi_symbol_report",
    "generate_research_hypothesis",
    "get_acceptance_criteria",
    "holm_bonferroni",
    "hurst_exponent",
    "identify_pca_risk_factors",
    "label_realized_market_behavior",
    "log_returns",
    "mask_research_artifact",
    "max_drawdown",
    "median_mae_mfe",
    "momentum",
    "null_distribution_stats",
    "parse_calendar_events",
    "parse_news_items",
    "parse_sentiment_snapshot",
    "percent_rank",
    "permutation_test",
    "pivot_points",
    "prepare_research_dataset",
    "print_result_summary",
    "profit_factor",
    "r_space_null",
    "random_entry_null",
    "rate_of_change",
    "research_modeling_module",
    "resolve_market_structure_profile",
    "resolve_market_structure_profile_overrides",
    "result_to_markdown",
    "result_to_summary",
    "rolling_hurst",
    "rolling_percentile_rank",
    "rsi",
    "run_eds_mean_reversion",
    "run_eds_null_baseline",
    "run_eds_session",
    "run_eds_trend_persistence",
    "run_pca",
    "run_seasonality",
    "run_session_breakout_strategy",
    "run_session_fade_strategy",
    "save_json",
    "save_json_report",
    "save_markdown",
    "save_markdown_report",
    "score_research_hypothesis",
    "session_hours_payload",
    "session_label_for_hour",
    "session_randomized_null",
    "sharpe_ratio",
    "shuffle_returns_null",
    "simple_returns",
    "sma",
    "snapshot_report_json",
    "snapshot_report_markdown",
    "sortino_ratio",
    "std",
    "summarize_investment_data",
    "symbol_class",
    "tag_sessions",
    "timeframe_bucket",
    "validate_dataset",
    "validate_no_lookahead_features",
    "win_rate",
    "zscore",
]


def __getattr__(name: str) -> Any:
    """Resolve public research exports lazily."""
    if name in _LOCAL_EXPORTS:
        module = import_module(f"{__name__}.{_LOCAL_EXPORTS[name]}")
        value = getattr(module, name)
    elif name in _DATASET_EXPORTS:
        module_name, attr = _DATASET_EXPORTS[name]
        module = import_module(module_name)
        value = getattr(module, attr)
    elif name in _ANALYTICS_EXPORTS:
        module_name, attr = _ANALYTICS_EXPORTS[name]
        module = import_module(module_name)
        value = getattr(module, attr)
    else:
        value = _resolve_research_attr(name)

    if callable(value) and not isinstance(value, type):
        value = standardize_tool_callable(
            value,
            tool_name=name,
            tool_category="research",
        )
    globals()[name] = value
    return value


standardize_domain_exports(globals(), __all__, tool_category="research")
