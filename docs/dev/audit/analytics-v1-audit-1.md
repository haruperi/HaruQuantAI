# Analytics — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** analytics
* **Repository:** `haruperi/HaruQuantAI`
* **Branch / revision inspected:** `main` at commit `68851eb6898b229f49f1295c37748c63eefed3d3`
* **Package path:** `app/services/analytics`
* **Tests path requested:** `tests/analytics/unit/`
* **Usage/examples path requested:** `tests/analytics/usage/`
* **Actual test and usage evidence inspected:**
  * `tests/analytics/unit/test_metrics.py`
  * `tests/analytics/unit/test_report.py`
  * `tests/analytics/unit/test_scorecard.py`
  * `tests/analytics/unit/compat_test_helper.py`
  * `tests/analytics/usage/06_analytics.py`
  * additional test paths referenced by the source catalog and commit history
* **Files inspected:** all 54 Python files currently present under `app/services/analytics`, plus `app/services/analytics/README.md`, `app/__init__.py`, `pyproject.toml`, selected cross-domain files, current analytics tests, the usage script, package history, and the V1/V2 merge commits.
* **Related packages searched:** `app`, `app.utils`, `app.services.simulator`, `app.services.trading`, `app.services.risk`, `app.services.optimization`, `app.agentic`, `tests/analytics`.
* **Excluded:** generated files, caches, virtual environments, coverage output, unrelated service implementations, and Version 2 requirement design.
* **Audit limitations:**
  * The current repository is not a clean historical V1 snapshot. Commit history explicitly records a V1/V2 merge (`a499e332...`) followed by “Full analytics module from V1 to V2” (`5411bc53...`). This audit therefore describes the current code in the requested package and identifies retained compatibility behavior; it cannot prove the exact state of the pre-merge V1 package.
  * Repository-wide GitHub code search returned no indexed code hits, and a local clone could not be completed because outbound DNS resolution was unavailable. Static caller checks were therefore performed from available package imports, test imports, usage imports, known cross-domain files, commit diffs, registries, and explicit entry points.
  * No runtime service, API route, scheduled task, or agent tool was found invoking the analytics facade. Because full grep was unavailable, absence of a production caller is reported with **Medium**, not High, confidence.
  * Tests were read but not executed in this audit. Test assertions prove intended or currently accepted behavior, not successful production integration.

## 2. Executive Summary

The current `analytics` package is a broad, read-only analytics library and facade. It provides:

* canonicalization of backtest, paper, live-history, simulation-journal, and trading-journal data;
* trade, PnL, return, drawdown, risk, ratio, exposure, cost, efficiency, benchmark, distribution, and resampling calculations;
* structured analytics reports;
* strategy-quality scorecards;
* dashboard payload construction and deterministic curve truncation;
* report serialization and hashing;
* contracts, catalogs, warnings, redaction, workload limits, and a tool registry.

The strongest working path is:

```text
canonical trading-result dictionary
→ TradingResultAdapter.to_canonical()
→ build_analytics_report()
→ trade/equity/drawdown/risk/ratio/distribution/benchmark metrics
→ StandardResponse containing report sections
```

The package also has meaningful internal workflows for benchmark comparison, all/long/short analytics, dashboard projection, seeded bootstrap/permutation calculations, report serialization, and report hashing.

However, important advertised capabilities are incomplete:

* portfolio analytics returns fixed zero metrics;
* report comparison returns fixed zero differences;
* prop-firm compliance always returns `compliant=True`;
* White’s Reality Check, PBO, backtest permutation, and backtest bootstrap wrappers return constants;
* `format_summary_as_rows()` and `print_statistical_validation_report()` return empty output;
* the scorecard reads a flatter section shape than `build_analytics_report()` emits, so the two public workflows are not directly composable without reshaping;
* the registry exists but no package registration decorators were found populating it;
* no production/API/agent caller was confirmed.

The package surface is also highly fragmented. The root uses wildcard re-exporting and exposes hundreds of raw kernels, compatibility aliases, private-looking helpers, contracts, facade functions, and duplicate model types. Tests rely heavily on `tests/analytics/unit/compat_test_helper.py`, which implements a separate V1-to-V2 compatibility layer inside the test suite. This weakens the evidence that root-package compatibility is provided by production code itself.

**Audit metrics**

```text
Module folders: 10 | Python files: 54 | Public symbols: 351 root-exported names
Symbols with confirmed callers: at least 153 (43.6%, conservative lower bound from the usage script alone)
Workflows found: 11 (6 working, 3 partial, 2 broken)
```

The `351` count is the dynamic root `__all__` surface after resolving explicit imports plus `from app.services.analytics.metrics import *`. Subpackage-only public definitions are additionally catalogued below but are not added to that comparable root-surface metric.

**Evidence trustworthiness:** High for package/file existence, exports, signatures, internal call paths, and identified stubs; Medium for repository-wide production usage and unused-code conclusions.

## 3. Actual Package Structure

```text
Package: app.services.analytics
├── __init__.py
│   └── Dynamic root facade: 351 public names
│       ├── official tools and reports
│       ├── contracts and adapters
│       ├── raw metric kernels
│       ├── compatibility aliases
│       └── selected statistics/dashboard helpers
├── errors.py
│   ├── ErrorPayload
│   ├── AnalyticsError
│   ├── AnalyticsValidationError
│   ├── ANALYTICS_ERROR_CODES
│   ├── ERROR_MESSAGES
│   └── to_analytics_error_payload()
├── tool_api.py
│   ├── BuildAnalyticsReportRequest
│   ├── BuildPortfolioAnalyticsReportRequest
│   ├── AnalyticsReport
│   ├── PortfolioAnalyticsReport
│   ├── AnalyticsComparison
│   ├── ComplianceProfile
│   ├── ComplianceEvidence
│   ├── DEFAULT_CONFIGURATION_SOURCES
│   ├── get_analytics_overview()
│   └── build_analytics_report()
├── adapters/
│   ├── __init__.py
│   │   └── Re-exports adapters, protocol dictionaries, journals, converters,
│   │       plus compatibility aliases BacktestResult/TradingResult/etc.
│   ├── canonicalize.py
│   │   ├── BacktestResult
│   │   ├── PaperResult
│   │   ├── LiveResult
│   │   ├── PortfolioResult
│   │   ├── TradingResultAdapter
│   │   │   └── to_canonical()
│   │   ├── to_canonical()
│   │   └── to_trading_result()
│   ├── journal_adapters.py
│   │   ├── SimulationJournal
│   │   ├── LiveTradeJournal
│   │   ├── from_simulation_journal()
│   │   └── from_live_trade_journal()
│   └── protocols.py
│       ├── TradingResultDict
│       ├── BacktestResultDict
│       ├── PaperTradingResultDict
│       ├── LiveTradingResultDict
│       ├── TradingResultAdapter [Protocol]
│       │   └── to_canonical()
│       └── validate_adapter_contract()
├── benchmarks/
│   ├── __init__.py
│   │   └── Re-exports benchmark metrics and `_align_series`
│   ├── alignment.py
│   │   ├── bench_alignment_boundary()
│   │   └── `_align_series()` [private-looking but exported]
│   └── metrics.py
│       ├── beta()
│       ├── alpha()
│       ├── r_squared()
│       ├── tracking_error()
│       ├── information_ratio()
│       ├── batting_average()
│       ├── up_down_capture()
│       └── calculate_benchmark_metrics()
├── boundaries/
│   ├── __init__.py
│   │   └── Re-exports all boundary models/functions
│   ├── envelopes.py
│   │   ├── AnalyticsError [dataclass, not exception]
│   │   ├── success_envelope()
│   │   └── error_envelope()
│   ├── limits.py
│   │   ├── AnalyticsLimits
│   │   ├── WorkloadShape
│   │   └── enforce_limits()
│   ├── redaction.py
│   │   ├── RedactionPolicy
│   │   └── redact()
│   └── request_validation.py
│       ├── request_id()
│       ├── float64()
│       └── validate_request()
├── contracts/
│   ├── __init__.py
│   │   └── Re-exports 47 catalog, model, warning, and serialization names
│   ├── audit.py
│   │   ├── Contract
│   │   │   ├── validate_metadata_structure()
│   │   │   ├── validate_trace_identifiers()
│   │   │   ├── to_json()
│   │   │   ├── content_hash()
│   │   │   ├── contract_hash()
│   │   │   └── check_compatibility()
│   │   └── AuditEvent
│   ├── metric_catalog.py
│   │   ├── SCHEMA_COMPATIBILITY_MATRIX
│   │   ├── WARNING_SEVERITY_LEVELS
│   │   ├── DECIMAL_PRECISION_POLICY
│   │   ├── METRIC_DEFINITION_CATALOG
│   │   ├── OFFICIAL_ANALYTICS_TOOL_CATALOG
│   │   ├── get_metric_definition()
│   │   └── validate_metric_catalog()
│   ├── models.py
│   │   ├── SchemaCompatibility / SchemaCompatibilityMatrix
│   │   ├── CapabilityStability / MetricRole
│   │   ├── Lineage / BenchmarkData / TradingResult / ReproducibilityHashes
│   │   ├── AnalyticsWarning / QualityFlag
│   │   ├── AnalyticsReport / PortfolioAnalyticsReport
│   │   ├── TruncationMetadata / DashboardPayload / ErrorPayload / ToolEnvelope
│   │   ├── MetricDefinition / ToolDefinition / AnalyticsConfig / MetricConfig
│   │   ├── MetricResult / ExplainabilityOutput / PrecisionPolicy
│   │   ├── AnalyticsMetadata / AnalyticsRequest / AnalyticsResult
│   │   ├── Config / Metadata / Request / Result
│   │   ├── MetricDefinitionCatalog
│   │   └── validate_schema_version()
│   ├── portfolio.py
│   │   ├── Contract
│   │   │   ├── validate_metadata_structure()
│   │   │   ├── validate_trace_identifiers()
│   │   │   ├── to_json()
│   │   │   ├── content_hash()
│   │   │   ├── contract_hash()
│   │   │   └── check_compatibility()
│   │   ├── AccountSnapshot
│   │   │   └── validate_snap_time()
│   │   ├── Position
│   │   │   └── validate_pos_times()
│   │   └── PortfolioSnapshot
│   ├── serialization.py
│   │   ├── JsonValue
│   │   ├── to_json_safe()
│   │   └── canonical_json()
│   └── warnings.py
│       ├── WarningCatalogEntry
│       ├── QualityFlagCatalogEntry
│       ├── SENSITIVE_KEYS_RE
│       ├── SENSITIVE_VALUE_RE
│       ├── WARNING_CATALOG
│       ├── QUALITY_FLAG_CATALOG
│       ├── redact_sensitive_info()
│       ├── build_warning()
│       └── build_quality_flag()
├── dashboards/
│   ├── __init__.py
│   │   └── Re-exports payload models, truncation models, builder,
│   │       and `_downsample_curve`
│   ├── overview.py
│   │   ├── DashboardConfig
│   │   ├── TruncationMetadata
│   │   ├── DashboardPayload
│   │   └── build_overview_payload()
│   └── truncation.py
│       ├── ChartPoint
│       ├── TruncationPolicy
│       ├── TruncatedSeries
│       ├── truncate_series()
│       └── `_downsample_curve()` [private-looking but exported]
├── metrics/
│   ├── __init__.py
│   │   └── Re-exports 269 metric names
│   ├── aggregate.py
│   │   ├── TradeRecord / ReturnPoint
│   │   ├── metrics_aggregate_boundary()
│   │   ├── breakeven_epsilon()
│   │   ├── calculate_trade_metrics()
│   │   ├── calculate_analytics_for_subset()
│   │   └── compute_equity_metrics()
│   ├── costs.py
│   │   ├── TradeRecord
│   │   ├── calculate_spread_cost_impact()
│   │   ├── calculate_slippage_impact()
│   │   └── calculate_commission_impact()
│   ├── curves.py
│   │   ├── TradeRecord
│   │   ├── balance_curve_from_closed_trades()
│   │   ├── balance_curve()
│   │   ├── balance_curve_metric()
│   │   ├── equity_curve()
│   │   └── equity_curve_metric()
│   ├── distribution.py
│   │   ├── ReturnPoint
│   │   ├── skewness() / skewness_metric()
│   │   ├── kurtosis() / kurtosis_metric()
│   │   ├── percentile_summary()
│   │   ├── upside_downside_summary()
│   │   ├── fat_tail_score()
│   │   ├── jarque_bera_test() / jarque_bera_test_metric()
│   │   ├── bootstrap_metric()
│   │   ├── false_discovery_rate()
│   │   └── distribution_summary()
│   ├── drawdown.py
│   │   ├── metrics_drawdown_boundary()
│   │   ├── drawdown_series() / drawdown_series_metric()
│   │   ├── relative_drawdown_series()
│   │   ├── drawdown_duration_series()
│   │   ├── trade_level_drawdowns() / trade_level_drawdowns_metric()
│   │   ├── max_drawdown() / max_close_to_close_drawdown()
│   │   ├── max_close_to_close_drawdown_percent() / date()
│   │   ├── max_strategy_drawdown() / percent() / date()
│   │   ├── max_relative_drawdown_percent()
│   │   ├── max_drawdown_duration()
│   │   ├── max_drawdown_duration_from_returns()
│   │   ├── max_drawdown_duration_from_equity()
│   │   ├── avg_drawdown() / avg_drawdown_duration()
│   │   ├── avg_underwater_drawdown_percent()
│   │   ├── avg_yearly_max_drawdown()
│   │   ├── time_to_recovery()
│   │   ├── ulcer_index() / pain_index()
│   │   ├── recovery_factor() / pain_ratio() / calmar_ratio()
│   │   ├── fouse_ratio() / sterling_ratio() / rina_index()
│   │   ├── return_on_max_strategy_drawdown()
│   │   ├── return_on_max_close_to_close_drawdown()
│   │   ├── account_size_required()
│   │   ├── max_consecutive_drawdown_trades()
│   │   ├── avg_trade_drawdown()
│   │   ├── adjusted/net/select profit-to-drawdown functions
│   │   ├── trade_pnl_distribution()
│   │   ├── drawdown_distribution()
│   │   ├── drawdown_probability()
│   │   └── calculate_drawdown_metrics()
│   ├── efficiency.py
│   │   ├── metrics_efficiency_boundary()
│   │   ├── get_mae_mfe_r()
│   │   ├── median_mae_mfe() / median_mae_r() / median_mfe_r()
│   │   ├── mae_efficiency() / mfe_efficiency()
│   │   ├── aggregate_mfe_capture_ratio()
│   │   ├── loss_containment_efficiency()
│   │   ├── aggregate_loss_containment_efficiency()
│   │   ├── exit_efficiency() / trade_efficiency()
│   │   ├── capital_efficiency() / position_size_efficiency()
│   │   ├── avg_trade_notional_efficiency()
│   │   ├── return_per_unit_mae()
│   │   ├── return_per_calendar_day()
│   │   ├── return_per_market_hour()
│   │   ├── return_per_trade_hour()
│   │   ├── profit_per_trade_per_day()
│   │   ├── trades_per_day()
│   │   ├── longest_flat_period_duration()
│   │   └── calculate_efficiency_metrics()
│   ├── equity.py
│   │   ├── returns_series() / returns_series_metric()
│   │   ├── log_returns_series() / log_returns_series_metric()
│   │   ├── daily_returns() / weekly_returns() / monthly_returns() / annual_returns()
│   │   ├── benchmark_returns()
│   │   ├── total_return_usd()
│   │   ├── annualized_return()
│   │   ├── geometric_mean_return() / geometric_mean_return_metric()
│   │   ├── return_volatility() / return_volatility_metric()
│   │   ├── downside_return_volatility() / downside_return_volatility_metric()
│   │   ├── return_skewness() / return_kurtosis()
│   │   ├── best_return() / worst_return()
│   │   ├── avg_monthly_return() / monthly_return_stddev()
│   │   ├── return_on_account()
│   │   ├── kelly_criterion()
│   │   ├── win_loss_streaks()
│   │   ├── buy_and_hold_return()
│   │   ├── calculate_return_metrics()
│   │   └── calculate_equity_metrics()
│   ├── exports.py
│   │   ├── common_avg_loss()
│   │   ├── common_get_r_multiples()
│   │   ├── metrics_get_r_multiples()
│   │   ├── metrics_avg_loss()
│   │   ├── benchmark_information_ratio()
│   │   ├── metrics_win_rate_fraction()
│   │   ├── metrics_expectancy_r()
│   │   ├── ratios_information_ratio()
│   │   ├── distributions_r_multiple_distribution()
│   │   └── metrics_r_multiple_distribution()
│   ├── pnl.py
│   │   ├── net_profit() / adjusted_net_profit() / select_net_profit()
│   │   ├── gross_profit() / adjusted_gross_profit() / select_gross_profit()
│   │   ├── gross_loss() / adjusted_gross_loss() / select_gross_loss()
│   │   ├── total_return()
│   │   ├── return_on_initial_capital()
│   │   ├── cagr() / cagr_metric() / buy_and_hold_cagr()
│   │   ├── compound_monthly_growth_rate()
│   │   ├── max_runup() / max_runup_date()
│   │   └── return_over_drawdown()
│   ├── position_exposure.py
│   │   ├── TradeRecord / Duration
│   │   ├── max_gross_size_held()
│   │   ├── max_size_held()
│   │   ├── max_net_size_held()
│   │   ├── max_long_size_held()
│   │   ├── max_short_size_held()
│   │   ├── time_in_market_duration()
│   │   ├── percent_time_in_market()
│   │   ├── open_position_pnl()
│   │   ├── slippage_paid()
│   │   ├── commission_paid()
│   │   └── swap_paid()
│   ├── r_multiples.py
│   │   ├── TradeRecord
│   │   ├── get_r_multiples()
│   │   ├── avg_return_per_risk_unit()
│   │   ├── compute_r_trade_metrics()
│   │   └── compute_trade_metrics()
│   ├── ratios.py
│   │   ├── volatility()/return parsing support
│   │   ├── sharpe_ratio() / annualized_sharpe_ratio()
│   │   ├── sortino_ratio() / omega_ratio() / kappa_ratio()
│   │   ├── gain_to_pain_ratio() / martin_ratio()
│   │   ├── ulcer_performance_index() / drawdown_ratio()
│   │   ├── profit_factor() / profit_factor_metric()
│   │   ├── adjusted_profit_factor() / select_profit_factor()
│   │   ├── profit_factor_by_count()
│   │   ├── profit_factor_by_volume() / metric()
│   │   ├── payoff_ratio() / payoff_ratio_metric()
│   │   ├── adjusted_payoff_ratio() / average_win_loss_ratio()
│   │   ├── win_loss_ratio() / profit_loss_ratio() / gain_loss_ratio()
│   │   ├── expectancy_over_std() / adjusted_expectancy()
│   │   ├── expected_value() / expected_value_r()
│   │   ├── edge_ratio() / mfe_to_mae_ratio() / profit_to_mae_ratio()
│   │   ├── risk_reward_ratio() / odds_calculator()
│   │   ├── cpc_index() / tail_ratio() / treynor_ratio()
│   │   ├── sqn() / system_quality_number()
│   │   ├── largest-loss and adjusted/select percentage ratios
│   │   ├── ratio_of_adjusted_gross_profit_to_adjusted_gross_loss()
│   │   └── calculate_ratio_metrics()
│   ├── risk.py
│   │   ├── volatility() / annualized_volatility() / downside_volatility()
│   │   ├── value_at_risk() / conditional_var() / expected_shortfall()
│   │   ├── historical_var_by_symbol()
│   │   ├── portfolio_var_from_covariance()
│   │   ├── risk_of_ruin() / risk_of_ruin_with_custom_horizon()
│   │   ├── compounding_risk_of_ruin()
│   │   ├── max_loss_probability()
│   │   ├── max_gross_exposure()
│   │   ├── max_nominal_exposure_simple()
│   │   ├── avg_trade_nominal_exposure()
│   │   ├── exposure_time_ratio()
│   │   ├── time_weighted_avg_exposure()
│   │   ├── portfolio_margin_utilization_curve()
│   │   ├── max_single_trade_margin_utilization()
│   │   ├── avg_single_trade_margin_utilization()
│   │   ├── profit_per_pip_risk()
│   │   ├── risk_adjusted_efficiency()
│   │   ├── upside_potential_ratio()
│   │   └── calculate_risk_metrics()
│   ├── time_analysis.py
│   │   ├── TradeRecord
│   │   ├── avg_time_in_trade()
│   │   ├── median_time_in_trade()
│   │   ├── min_time_in_trade()
│   │   ├── max_time_in_trade()
│   │   ├── trading_period_duration()
│   │   ├── time_in_market_duration_metric()
│   │   ├── calculate_period_analysis()
│   │   ├── calculate_session_performance()
│   │   └── calculate_long_short_split()
│   └── trade_outcomes.py
│       ├── TradeRecord
│       ├── parse_utc_time()
│       ├── get_closed_trades() / get_ordered_closed_trades()
│       ├── classify_trades()
│       ├── winning_trades() / losing_trades() / breakeven_trades()
│       ├── long_trades() / short_trades() / count_open_trades()
│       ├── total_trades()
│       ├── win_rate() / win_rate_fraction()
│       ├── loss_rate() / loss_rate_fraction()
│       ├── avg_win() / avg_win_metric()
│       ├── avg_loss() / avg_loss_metric()
│       ├── median_win() / median_loss()
│       ├── largest_win() / largest_loss()
│       ├── expectancy() / expectancy_metric() / expectancy_r()
│       ├── consecutive_wins_losses()
│       ├── max_consecutive_wins() / max_consecutive_losses()
│       ├── avg_consecutive_wins() / avg_consecutive_losses()
│       ├── avg_win_loss()
│       ├── avg_r_multiple() / median_r_multiple()
│       ├── min_r_multiple() / max_r_multiple()
│       ├── r_signal_to_noise()
│       ├── rolling_expectancy_stability()
│       ├── win_after_win_probability()
│       ├── runs_test_zscore()
│       ├── shannon_entropy()
│       ├── trade_outcome_entropy()
│       └── t_statistic()
├── registry/
│   ├── __init__.py
│   │   └── Re-exports registry entry, constants, decorator, and request helpers
│   └── analytics_registry.py
│       ├── TOOL_REGISTRY
│       ├── OFFICIAL_TOOL_NAMES
│       ├── RegisteredToolEntry
│       ├── register_tool()
│       ├── get_active_requests()
│       ├── clear_active_requests()
│       └── request_id()
├── reports/
│   ├── __init__.py
│   │   └── Re-exports report models, builders, formatters, serializers, hashes
│   ├── formatters.py
│   │   ├── ReportFormat
│   │   ├── SerializedReport
│   │   ├── format_summary_as_rows()
│   │   ├── build_backtest_report()
│   │   ├── print_statistical_validation_report()
│   │   └── serialize_report()
│   ├── hashes.py
│   │   ├── HashPolicy
│   │   └── compute_report_hash()
│   └── sections.py
│       ├── AnalyticsReport
│       ├── PortfolioAnalyticsReport
│       ├── evaluate_section()
│       ├── request_id()
│       ├── build_analytics_report()
│       ├── build_portfolio_analytics_report()
│       ├── compare_analytics_reports()
│       ├── calculate_statistical_validation()
│       └── calculate_prop_firm_compliance()
├── scorecards/
│   ├── __init__.py
│   │   └── Re-exports scorecard models and evaluators
│   ├── labels.py
│   │   └── scorecards_policy_boundary()
│   └── quality.py
│       ├── NonBindingRecommendation
│       ├── StrategyQualityAssessment
│       ├── StrategyQualityConfig
│       ├── ScorecardRule
│       ├── ScorecardResult
│       ├── sqn()
│       ├── sample_size_warning()
│       └── evaluate_strategy_quality()
└── statistics/
    ├── __init__.py
    │   └── Re-exports 33 statistics names
    ├── distributions.py
    │   ├── statistics_distribution_boundary()
    │   ├── skewness() / kurtosis()
    │   ├── higher_moments()
    │   ├── percentile_summary()
    │   ├── upside_downside_summary()
    │   ├── fat_tail_score() / tail_ratio()
    │   ├── jarque_bera_test() / shapiro_wilk_test()
    │   ├── qq_plot_data()
    │   ├── fit_distribution() / distribution_fit_quality()
    │   ├── histogram_data()
    │   ├── detect_outliers() / outlier_ratio()
    │   ├── return_distribution() / r_multiple_distribution()
    │   ├── sample_size_warning()
    │   └── calculate_distribution_metrics()
    ├── multiple_testing.py
    │   ├── whites_reality_check()
    │   ├── whites_reality_check_backtests()
    │   ├── deflated_sharpe_ratio()
    │   ├── probability_of_backtest_overfitting()
    │   ├── walk_forward_degradation_score()
    │   ├── bonferroni_correction()
    │   ├── benjamini_hochberg_correction()
    │   └── stability_score()
    └── resampling.py
        ├── statistics_resampling_boundary()
        ├── bootstrap_confidence_intervals()
        ├── permutation_test()
        ├── permutation_test_backtest()
        ├── bootstrap_confidence_intervals_backtest()
        └── bootstrap_probability_above_threshold()
```

## 4. Module and File Inventory

Dependencies are shown in the requested order: **standard library; required third-party; local modules/symbols**.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| root | `__init__.py` | Aggregates nearly the entire package into one dynamic facade. | 351 names via explicit imports and metrics wildcard | Std: future annotations; 3P: none; Local: all analytics subpackages | Used as import surface in tests; no production caller confirmed | Questionable |
| root | `errors.py` | Analytics exception hierarchy, codes, and error-payload conversion. | `AnalyticsError`, `AnalyticsValidationError`, codes, `to_analytics_error_payload` | Std: `typing`; 3P: none; Local: none | Used throughout package | Supporting |
| root | `tool_api.py` | Intended architecture-approved, read-only facade. | overview/report plus re-exported official tools | Std: typing; 3P: none; Local: reports, metrics, benchmark, scorecard, `app.utils` | Test/example evidence; no external runtime caller confirmed | Useful |
| adapters | `__init__.py` | Adapter import surface and V1 compatibility aliases. | adapter types/functions | Std: typing; 3P: none; Local: adapter modules | Used by root/tests | Supporting |
| adapters | `canonicalize.py` | Validates and normalizes result dictionaries and converts to contract model. | `TradingResultAdapter`, `to_canonical`, `to_trading_result` | Std: copy/dataclasses/typing; 3P: none; Local: simulator model, analytics contracts/errors/logger | Used by report workflow and tests | Essential |
| adapters | `journal_adapters.py` | Converts simulation/live journal structures to analytics input. | journals and conversion functions | Std: dataclasses/typing; 3P: none; Local: trading contracts; type-only risk/simulator contracts | Example/test-only; cross-domain runtime unconfirmed | Useful |
| adapters | `protocols.py` | Structural adapter contracts and validator. | TypedDicts, protocol, `validate_adapter_contract` | Std: protocols/typing; 3P: none; Local: analytics error/logger | Example/test-only | Supporting |
| benchmarks | `__init__.py` | Benchmark import surface. | benchmark functions, exported `_align_series` | Std: none; 3P: none; Local: alignment/metrics | Used by root/report/tests | Supporting |
| benchmarks | `alignment.py` | Aligns strategy and benchmark sequences. | `bench_alignment_boundary`, `_align_series` | Std: typing; 3P: optional runtime pandas; Local: logger | Used by benchmark metrics | Essential |
| benchmarks | `metrics.py` | Relative performance metrics and official benchmark tool. | beta/alpha/R²/TE/IR/capture/tool | Std: math; 3P: none; Local: alignment, errors, `app.utils` | Used by report and tests | Essential |
| boundaries | `__init__.py` | Boundary import surface. | envelopes, limits, validation, redaction | Std: none; 3P: none; Local: boundary files | Used by root/examples | Supporting |
| boundaries | `envelopes.py` | Contract-style success/error `ToolEnvelope` builders. | dataclass `AnalyticsError`, two builders | Std: dataclasses/typing; 3P: none; Local: contract models | Example/test-only; official tools use `app.utils` envelopes instead | Questionable |
| boundaries | `limits.py` | In-memory workload-shape limits. | limits models, `enforce_limits` | Std: dataclasses; 3P: none; Local: analytics validation error | Example/test-only | Useful |
| boundaries | `redaction.py` | Recursive redaction. | `RedactionPolicy`, `redact` | Std: enum/typing; 3P: none; Local: logger | Example/test-only | Questionable |
| boundaries | `request_validation.py` | Request ID/numeric conversion and workload validation. | `request_id`, `float64`, `validate_request` | Std: math; 3P: none; Local: contracts, limits | Example/test-only | Supporting |
| contracts | `__init__.py` | Contract/catalog import surface. | 47 names | Std: none; 3P: none; Local: contract files | Used widely | Supporting |
| contracts | `audit.py` | Pydantic audit-event contract and deterministic hashes. | `Contract`, `AuditEvent` | Std: datetime/hashlib; 3P: pydantic; Local: analytics errors, utils normalization/standard | No confirmed runtime import; not package-exported | Questionable |
| contracts | `metric_catalog.py` | Metric/tool/schema catalogs and validation. | catalogs, lookup, validator | Std: typing; 3P: none; Local: contract models/errors | Used by contracts, registry, examples/tests | Useful |
| contracts | `models.py` | Main dataclass/type contract collection. | report/config/result/tool/dashboard models | Std: dataclasses/decimal/typing; 3P: none; Local: none | Used throughout package | Essential |
| contracts | `portfolio.py` | Pydantic portfolio snapshot contracts. | duplicated `Contract`, account/position/portfolio models | Std: datetime/hashlib/typing; 3P: pydantic; Local: analytics errors, utils | No confirmed runtime import; not package-exported | Questionable |
| contracts | `serialization.py` | JSON-safe conversion and canonical JSON. | `JsonValue`, `to_json_safe`, `canonical_json` | Std: dataclasses/decimal/enum/json; 3P: numpy, pandas; Local: contract precision | Used by tests/examples/catalog contracts | Useful |
| contracts | `warnings.py` | Warning/quality catalogs, construction, and redaction. | catalogs, builders, redactor | Std: dataclasses/re/typing; 3P: none; Local: contract models | Used by examples/tests; not central report implementation | Useful |
| dashboards | `__init__.py` | Dashboard import surface. | models, builder, truncation, private wrapper | Std: none; 3P: none; Local: dashboard files | Used by root/tests | Supporting |
| dashboards | `overview.py` | Converts report sections into UI-ready cards/chart payload. | dashboard models and builder | Std: dataclasses/typing; 3P: none; Local: truncation, errors, `app.utils` | Test/example evidence | Useful |
| dashboards | `truncation.py` | Deterministic curve decimation preserving extrema. | point/policy/result models, truncation functions | Std: sequences/dataclasses/typing; 3P: none; Local: logger | Used by dashboard/tests | Essential |
| metrics | `__init__.py` | Re-exports 269 metric names. | all metric families and aliases | Std: none; 3P: none; Local: all metric files | Used by root/tests | Questionable |
| metrics | `aggregate.py` | Composes trade/equity subsets. | aggregate boundary, trade/subset/equity aggregators | Std: sequences/typing; 3P: none; Local: contracts and multiple metric modules | Used by tool API/report/tests | Essential |
| metrics | `costs.py` | Spread/slippage/commission totals. | three cost functions | Std: sequences; 3P: none; Local: position exposure/contracts | Example/test; indirectly available to users | Useful |
| metrics | `curves.py` | Builds closed-trade balance/equity curves. | five curve functions | Std: sequences/typing; 3P: none; Local: trade-outcome helpers/contracts | Example/test-only; not report builder input path | Useful |
| metrics | `distribution.py` | Metric-contract distribution calculations. | moments, JB, bootstrap, FDR, summary | Std: math/random; 3P: none; Local: equity/ratios/contracts | Primarily tests/examples; overlaps statistics package | Questionable |
| metrics | `drawdown.py` | Very broad drawdown calculation kernel and wrappers. | 40+ drawdown functions | Std: math/datetime/statistics; 3P: none; Local: contracts/equity/PnL/trades/`app.utils` | Core subset/report use plus extensive tests | Essential |
| metrics | `efficiency.py` | MAE/MFE, capital, time, and exit-efficiency metrics. | 20+ efficiency functions | Std: math/statistics/sequences; 3P: none; Local: contracts/trade/time helpers | Example/test-only; no report section uses it | Useful |
| metrics | `equity.py` | Return series, period returns, equity metrics, and tool wrapper. | 25+ return/equity functions | Std: datetime/math/statistics; 3P: optional pandas-like inputs; Local: contracts/errors/`app.utils` | Core report use | Essential |
| metrics | `exports.py` | Compatibility aliases for name collisions. | ten forwarding wrappers | Std: sequences/typing; 3P: none; Local: underlying metrics | Root/test compatibility only | Questionable |
| metrics | `pnl.py` | Profit/loss, total return, CAGR, run-up. | PnL functions | Std: datetime/math/sequences; 3P: none; Local: contracts/trade helpers | Tests/examples; root compatibility aliases | Useful |
| metrics | `position_exposure.py` | Size, duration, open PnL, and cost totals. | exposure/cost functions | Std: datetime/sequences; 3P: none; Local: contracts/trade parser | Used by subset aggregator and tests | Essential |
| metrics | `r_multiples.py` | R-multiple extraction and summary. | four functions | Std: math/sequences; 3P: none; Local: contracts/trade PnL | Used by trade/ratio/distribution metrics and tests | Essential |
| metrics | `ratios.py` | Large collection of return/trade ratios. | 40+ ratio functions and tool wrapper | Std: math/statistics/sequences; 3P: none; Local: contracts/PnL/trades/R-multiples/`app.utils` | Core report use plus tests | Essential |
| metrics | `risk.py` | Return, VaR, ruin, exposure, margin, and risk metrics. | 20+ functions and tool wrapper | Std: math/random/statistics/sequences; 3P: none; Local: contracts/errors/`app.utils` | Core report use plus tests | Essential |
| metrics | `time_analysis.py` | Trade-duration, period, session, and direction splits. | nine functions | Std: datetime/statistics/sequences; 3P: none; Local: contracts/trade helpers | Example/test-only; not report builder section | Useful |
| metrics | `trade_outcomes.py` | Trade filtering, classification, rates, streaks, expectancy, entropy. | 40+ functions | Std: datetime/math/statistics/sequences; 3P: none; Local: contracts/R-multiples/errors/`app.utils` | Used by aggregators/curves/ratios/tests | Essential |
| registry | `__init__.py` | Registry import surface. | registry models/constants/functions | Std: none; 3P: none; Local: registry implementation | Example/test-only | Supporting |
| registry | `analytics_registry.py` | Mutable in-process tool and request registries. | `TOOL_REGISTRY`, decorator, request helpers | Std: re/dataclasses/collections/typing; 3P: none; Local: catalog/contracts/errors | Active-request helpers used in example; tool registry population unconfirmed | Questionable |
| reports | `__init__.py` | Report import surface. | builders, models, formatters, hashes | Std: none; 3P: none; Local: report files | Used by root/tool API/tests | Supporting |
| reports | `formatters.py` | Report serialization plus two placeholder formatters. | format enum/model and four functions | Std: json/dataclasses/enum/typing; 3P: none; Local: contracts/report builder | Serializer used in tests; two functions are stubs | Questionable |
| reports | `hashes.py` | Deterministic report hash excluding metadata. | `HashPolicy`, `compute_report_hash` | Std: hashlib/json/decimal/enum; 3P: none; Local: logger | Test/example evidence | Useful |
| reports | `sections.py` | Report orchestration and advertised report/compliance tools. | report models and seven functions | Std: dataclasses/datetime/typing; 3P: none; Local: adapters, metrics, statistics, `app.utils` | Main report path used internally/tests; several tools are stubs | Essential overall; mixed per symbol |
| scorecards | `__init__.py` | Scorecard import surface. | config/result/rules/evaluators | Std: none; 3P: none; Local: quality | Used by root/tool API/tests | Supporting |
| scorecards | `labels.py` | Returns no data; documents policy boundary through a logging call. | `scorecards_policy_boundary` | Std: none; 3P: none; Local: logger | No confirmed caller | No demonstrated value |
| scorecards | `quality.py` | Non-binding threshold scorecards and SQN/sample checks. | scorecard models and three evaluators | Std: dataclasses/typing; 3P: none; Local: errors/`app.utils` | Tool API/tests; direct report chaining is mismatched | Useful |
| statistics | `__init__.py` | Statistics import surface. | 33 names | Std: none; 3P: none; Local: statistics files | Used by root/report/tests | Supporting |
| statistics | `distributions.py` | Raw-value distribution diagnostics and official wrapper. | 20+ functions | Std: math/sequences; 3P: none; Local: errors/`app.utils` | Core report uses wrapper; other functions tests/examples | Essential overall |
| statistics | `multiple_testing.py` | Multiple-testing and overfitting functions. | eight functions | Std: math/typing; 3P: none; Local: logger | Test/example-only; several constant placeholders | Questionable |
| statistics | `resampling.py` | Seeded bootstrap/permutation and tool wrapper. | six functions | Std: random/sequences/typing; 3P: none; Local: errors/`app.utils` | Bootstrap used by report; other functions tests/examples | Useful |

## 5. Public Behaviour Inventory

### Shared interpretation

Unless a row states otherwise:

* the code is synchronous and read-only;
* side effects are **None** except logging;
* no function writes a database, filesystem, broker, order, risk state, or network resource;
* `MetricResult` kernels commonly return neutral values for empty or insufficient inputs;
* official tool wrappers return `StandardResponse` dictionaries and convert caught exceptions to error envelopes;
* direct kernels can still raise `TypeError`, `ValueError`, `KeyError`, or analytics validation exceptions during coercion or validation;
* test evidence means a caller exists, but does not establish production use.

### Root facade and errors

| File / symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Confirmed callers | Usage | Value |
|---|---|---|---|---|---|---|---|---|
| `__init__.py::__all__` | generated constant | Publishes every non-underscore imported name. | module globals → 351-name tuple | None | Import errors | unit tests, usage imports | Used as test import surface | Questionable |
| `errors.py::AnalyticsError` | exception | Base analytics exception. | message → exception | None | n/a | package validation paths | Used | Supporting |
| `errors.py::AnalyticsValidationError` | exception | Validation-specific error. | message → exception | None | n/a | adapters, tools, boundaries, reports | Used | Essential |
| `errors.py::ANALYTICS_ERROR_CODES`, `ERROR_MESSAGES` | constants | Stable code/message mappings. | n/a | None | None | error conversion/tests | Possibly used | Supporting |
| `errors.py::to_analytics_error_payload()` | function | Converts exceptions to `{code, details}`. | exception → `ErrorPayload` | None | None expected | tests/package error paths | Possibly used | Supporting |

### `tool_api.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises/failure | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|---|
| type aliases and `DEFAULT_CONFIGURATION_SOURCES` | aliases/constant | Documents facade request/report shapes and default sources. | n/a | None | None | facade output/tests | Used internally | Supporting |
| `get_analytics_overview(request, request_id=None)` | official tool | Splits trades into all/long/short and calls subset analytics. | dict → `StandardResponse` | None | Invalid request becomes error response | usage/tests; no production caller found | Possibly used | Useful |
| `build_analytics_report(request, request_id=None)` | official wrapper | Delegates to report builder and adds non-binding metadata. | dict → `StandardResponse` | None | Delegate error response | tests/usage | Possibly used | Essential |
| re-exported official functions | facade exports | Publishes report, metric, benchmark, risk, scorecard functions. | underlying signatures | None | underlying behavior | tests/usage | Possibly used | Supporting |

### Adapters

| File / symbols | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers/tests | Usage | Value |
|---|---|---|---|---|---|---|---|---|
| `canonicalize.py::TradingResultAdapter.REQUIRED_KEYS` | constant | Required canonical input fields. | n/a | None | None | `to_canonical` | Used | Supporting |
| `TradingResultAdapter.to_canonical(payload)` | class method | Validates schema/result/phase/trades/equity and supplies defaults. | dict → canonical dict | None | `AnalyticsValidationError` | report builder, tests, usage | Used | Essential |
| `to_canonical(payload)` | wrapper | Calls concrete adapter class. | dict → canonical dict | None | same as above | usage/tests | Test-only evidence | Supporting |
| `to_trading_result(source)` | function | Converts supported object/dict into `contracts.TradingResult`. | model/dataclass/dict → model | None | validation/coercion errors | usage/tests | Test-only evidence | Useful |
| canonicalization type aliases | aliases | Labels supported input categories. | n/a | None | None | imports/type checking | Possibly used | Supporting |
| `protocols.py` TypedDicts | types | Structural input shapes. | n/a | None | None | usage/tests/type checking | Test-only evidence | Supporting |
| `protocols.TradingResultAdapter.to_canonical()` | protocol method | Declares required adapter method. | source → dict | None | implementation-defined | validator/tests | Test-only evidence | Supporting |
| `validate_adapter_contract(adapter)` | function | Checks presence/callability of adapter conversion. | object → `None` | None | validation error | usage/tests | Test-only evidence | Supporting |
| `SimulationJournal`, `LiveTradeJournal` | dataclasses | In-memory adapter inputs. | fields → object | None | dataclass construction errors | usage/tests | Test-only evidence | Useful |
| `from_simulation_journal()` | function | Maps simulation events/equity to analytics dictionary. | journal → dict | None | malformed input errors | usage/tests | Test-only evidence | Useful |
| `from_live_trade_journal()` | function | Maps live trade fills/reports to analytics dictionary. | journal → dict | None | malformed input errors | usage/tests | Test-only evidence | Useful |

### Benchmarks

| Symbols | Responsibility | Inputs → Return | Side effects | Raises/failure | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| `_align_series()` | Converts and aligns/truncates two return sequences. | two series → two float lists | None | Invalid values may be dropped/empty | all benchmark metrics | Used | Essential |
| `bench_alignment_boundary()` | Logs an architectural declaration; returns `None`. | none → `None` | None | None | no confirmed caller | Unused/uncertain | No demonstrated value |
| `beta`, `alpha`, `r_squared`, `tracking_error`, `information_ratio`, `batting_average`, `up_down_capture` | Benchmark-relative calculations. | strategy/benchmark returns → scalar/dict | None | Mostly neutral/default values | report builder, official benchmark tool, tests/usage | Used | Essential |
| `calculate_benchmark_metrics()` | Official aggregate benchmark tool. | two series, optional request ID → response | None | error envelope on no aligned data or exception | report builder/tests/usage/tool API | Used | Essential |

### Boundaries

| Symbols | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| `envelopes.AnalyticsError` | Data object with `code/details`. | fields → dataclass | None | None | examples/tests only | Test-only | Questionable |
| `success_envelope`, `error_envelope` | Build contract `ToolEnvelope` objects. | payload/metadata → model | None | construction errors | examples/tests | Test-only | Supporting |
| `AnalyticsLimits`, `WorkloadShape` | Configures workload ceilings and observed sizes. | fields → dataclass | None | None | `enforce_limits`, usage/tests | Test-only evidence | Useful |
| `enforce_limits(shape, limits=None)` | Fails closed when counts exceed limits. | shape → `None` | None | validation error | request validation/examples/tests | Possibly used | Useful |
| `RedactionPolicy` | Standard/strict enum. | n/a | None | None | `redact` callers | Test-only | Questionable |
| `redact(value, policy=STANDARD)` | Recursively masks sensitive keys/string tokens. | JSON-like value → redacted value | None | recursion/type edge errors | usage/tests | Test-only | Useful, but duplicated |
| `request_id(input_value, config)` | Extracts request ID into `MetricResult`. | object/config → result | None | no strict failure | usage/tests | Test-only | Supporting |
| `float64(input_value, config)` | Converts one value to finite float result. | object/config → result | None | validation error for invalid/non-finite | usage/tests | Test-only | Supporting |
| `validate_request(request, request_id_val, limits)` | Checks request type/ID/workload. | request metadata → `None` | None | validation error | usage/tests | Test-only | Useful |

### Contracts

| File / symbols | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| `metric_catalog.py` constants | Formula, schema, precision, warning, and tool catalogs. | n/a | None | None | registry, tests, usage | Used | Useful |
| `get_metric_definition(name)` | Resolves a named metric definition. | string → definition | None | unknown-key validation error | usage/tests | Test-only evidence | Useful |
| `validate_metric_catalog(catalog=None)` | Checks catalog consistency and returns summary. | catalog → dict | None | validation error | usage/tests | Test-only evidence | Useful |
| `models.py` type aliases | Stable type vocabulary. | n/a | None | None | type annotations | Used | Supporting |
| `Lineage`, `BenchmarkData`, `TradingResult`, `ReproducibilityHashes`, `AnalyticsWarning`, `QualityFlag`, `AnalyticsReport`, `PortfolioAnalyticsReport`, `TruncationMetadata`, `DashboardPayload`, `ErrorPayload`, `ToolEnvelope`, `MetricDefinition`, `ToolDefinition`, `AnalyticsConfig`/`MetricConfig`, `MetricResult`, `ExplainabilityOutput`, `PrecisionPolicy`, `AnalyticsMetadata`, `AnalyticsRequest`, `AnalyticsResult` | Versioned/in-memory analytics contracts. | constructor fields → object | None | dataclass/value errors | broad package use/tests | Used | Essential/Supporting |
| `validate_schema_version()` | Classifies/validates schema version. | version/matrix → status | None | validation error for unsupported/future | adapter/tests/usage | Used | Essential |
| `serialization.to_json_safe()` | Recursively converts dataclasses, Decimal, numpy, pandas, enums, dates. | object/policy → JSON-safe value | None | unsupported/non-finite errors | tests/usage | Test-only evidence | Useful |
| `serialization.canonical_json()` | Stable sorted compact JSON. | object → string | None | serialization errors | contracts/tests | Used | Useful |
| warning catalog models/constants | Defines warning and quality-flag templates. | n/a | None | None | builders/tests | Used | Supporting |
| `redact_sensitive_info()` | Redacts keys/secret-like strings. | JSON-like value → redacted value | None | edge type errors | tests/usage | Test-only | Useful, duplicated |
| `build_warning()`, `build_quality_flag()` | Create structured evidence objects from catalogs. | code/context/detail → model | None | unknown code errors | tests/usage | Test-only | Useful |
| `audit.Contract` methods | Metadata validation, serialization, content/full hashes, compatibility. | model state/target version → values | Read-only; reads clock at construction | pydantic/value/serialization errors | no confirmed caller | Unknown | Questionable |
| `AuditEvent` | Audit event contract. | fields → model | None | pydantic errors | no confirmed caller | Unknown | Questionable |
| `portfolio.Contract` methods | Near-copy of `audit.Contract`. | model state/version → values | Read-only; reads clock at construction | pydantic/value errors | portfolio models only | Possibly used | Supporting but duplicated |
| `AccountSnapshot`, `Position`, `PortfolioSnapshot` | Canonical portfolio snapshot models and timestamp validators. | fields → model | None | pydantic/value errors | no confirmed runtime caller | Unknown | Useful concept; disconnected |

### Dashboards

| Symbols | Responsibility | Inputs → Return | Side effects | Raises/failure | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| dashboard data classes | Configure and represent chart/table output and truncation. | fields → objects | None | construction errors | builder/tests | Used | Supporting |
| `build_overview_payload(report, config=None, request_id=None)` | Projects report into summary cards and truncated equity chart. | report → response **or** `DashboardPayload` | None | error response or validation exception | tests/usage | Test-only evidence | Useful |
| `truncate_series(points, policy=None)` | Deterministic decimation preserving first/last/global peak/trough. | points → `TruncatedSeries` | None | invalid shapes/index edge errors | dashboard/tests/usage | Used | Essential |
| `_downsample_curve(curve, max_points=100)` | Dict compatibility wrapper. | curve → dict | None | delegate errors | tests; exported publicly | Test-only | Questionable |

### Metrics

All metric rows below are read-only. The predominant signature is:

```text
(input sequence, MetricConfig) → MetricResult[T]
```

Some V1-compatible raw helpers instead return scalars/dictionaries, while official `calculate_*` functions may return `StandardResponse`. This inconsistency is itself an audit finding.

| File | Public symbols / families | Actual responsibility | Confirmed callers | Usage status | Value status |
|---|---|---|---|---|---|
| `aggregate.py` | `metrics_aggregate_boundary`, `breakeven_epsilon`, `calculate_trade_metrics`, `calculate_analytics_for_subset`, `compute_equity_metrics` | Composes lower-level metrics; tool-compatible trade aggregate; all/long/short subset aggregate. | report builder, tool API, usage/tests | Used | Essential |
| `costs.py` | spread/slippage/commission impact | Sums cost fields or delegates to exposure totals. | usage/tests | Test-only evidence | Useful |
| `curves.py` | `balance_curve_from_closed_trades`, `balance_curve`, `balance_curve_metric`, `equity_curve`, `equity_curve_metric` | Builds cumulative curve from closed trades. `balance_curve` and `equity_curve` are identical aliases. | usage/tests | Test-only evidence | Useful; aliases questionable |
| `distribution.py` | raw moments plus `*_metric`, percentile/upside/downside, fat-tail, JB, bootstrap, FDR, summary | Contract-returning distribution kernels. | tests/usage; no report path uses this file | Test-only evidence | Questionable due overlap |
| `drawdown.py` | all symbols listed in Section 3 | Computes equity/trade drawdowns, durations, recovery and derived ratios; official aggregate wrapper. | report builder, subset aggregator, tests/usage | Used | Essential |
| `efficiency.py` | all MAE/MFE, capital/time/exit efficiency functions | Computes efficiency evidence from trade fields. | usage/tests only | Test-only evidence | Useful but disconnected from reports |
| `equity.py` | return series/period grouping/equity aggregate functions | Parses equity curves and calculates returns and basic equity metrics. | report builder/tests/usage | Used | Essential |
| `exports.py` | ten `common_*`, `metrics_*`, `benchmark_*`, `ratios_*`, `distributions_*` wrappers | Renames and forwards existing functions to avoid collisions. | root/tests | Test-only/compatibility | Questionable |
| `pnl.py` | PnL totals, return, CAGR, run-up | Calculates profit and growth measures. | tests/usage and root `app` compatibility | Possibly used | Useful |
| `position_exposure.py` | size/exposure/time/open-PnL/cost totals | Reads trade records for exposure-like metrics. | subset aggregator/tests/usage | Used | Essential, but some names overstate semantics |
| `r_multiples.py` | `get_r_multiples`, `avg_return_per_risk_unit`, `compute_r_trade_metrics`, `compute_trade_metrics` | Converts PnL to R-space; uses risk=1 proxy when missing. | trade/ratio/distribution kernels/tests | Used | Essential |
| `ratios.py` | all ratio functions listed in Section 3 | Calculates risk-adjusted, payoff, profit-factor, expectancy, drawdown, quality ratios and aggregate response. | report builder/tests/usage | Used | Essential |
| `risk.py` | all return/tail/exposure/margin/ruin risk functions | Calculates historical risk and simulations; aggregate response. | report builder/tests/usage | Used | Essential |
| `time_analysis.py` | duration, session, period, direction functions | Reads timestamps and groups trading outcomes. | usage/tests | Test-only evidence | Useful |
| `trade_outcomes.py` | all trade classification/rate/streak/expectancy/statistics functions | Core normalized closed-trade behavior. | aggregate, ratios, curves, R-multiples, tests | Used | Essential |

### Registry

| Symbol | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| `TOOL_REGISTRY` | Mutable name/alias map. | n/a | Local state mutation | n/a | decorator | No populated entries confirmed | Questionable |
| `OFFICIAL_TOOL_NAMES` | Catalog-derived names. | n/a | None | None | imports/tests | Possibly used | Supporting |
| `RegisteredToolEntry` | Registry record. | fields → object | None | construction errors | decorator | Possibly used | Supporting |
| `register_tool(...)` | Decorator that inserts names/aliases. | metadata → decorator | Local state mutation | duplicate-name validation error | no decorated analytics function found | Possibly used | Questionable |
| `get_active_requests()` | Returns request-ID set copy. | none → set | Read-only | None | usage/tests | Test-only | Supporting |
| `clear_active_requests()` | Clears active request IDs. | none → `None` | Local state mutation | None | usage/tests | Test-only | Supporting |
| `request_id(input_value, config)` | Extracts/coerces request ID and stores it. | object/config → result | Local state mutation | generally warns instead of raising | usage/tests | Test-only | Questionable |

### Reports

| Symbol | Responsibility | Inputs → Return | Side effects | Failure behavior | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| report dataclasses | Lightweight report wrappers separate from contract models. | fields → object | None | construction errors | dashboard/type checking/tests | Possibly used | Supporting, duplicated |
| `evaluate_section()` | Builds section status/criticality metadata. | section data → dict | None | unknown status becomes failed | usage/tests; not called by main builder | Test-only | Useful but disconnected |
| `sections.request_id()` | Returns input unchanged in `MetricResult`. | object/config → result | None | none | no confirmed caller | Unknown | No demonstrated value |
| `build_analytics_report()` | Main report orchestration. | trading result → response | Read-only; reads current clock for metadata | fail-closed on required trade/equity errors; optional benchmark partial | tool API/tests/usage | Used | Essential |
| `build_portfolio_analytics_report()` | Validates currency compatibility and emits portfolio wrapper. | portfolio dict → response | None | errors on invalid/multi-currency without FX | tests | Test-only; implementation incomplete | Questionable |
| `compare_analytics_reports()` | Advertised report comparison. | two dicts → response | None | catches exceptions | tests | Test-only; fixed zero differences | No demonstrated analytical value |
| `calculate_statistical_validation()` | Mean and bootstrap CI package. | returns → response | None | empty input error response | tests/usage | Test-only; partial | Useful but incomplete |
| `calculate_prop_firm_compliance()` | Advertised compliance evidence. | report → response | None | does not meaningfully validate report | tests | Test-only; always passes | No demonstrated value |
| `ReportFormat`, `SerializedReport` | Serialization format contract. | fields → object | None | enum/constructor errors | tests/usage | Used | Supporting |
| `format_summary_as_rows()` | Placeholder row formatter. | report/config → `[]` or empty result | None | none | tests/usage | Test-only | No demonstrated value |
| `build_backtest_report()` | Compatibility wrapper over report builder. | result/config → dict or empty `MetricResult` | None | suppresses failed response to `{}` | tests/usage | Test-only | Questionable |
| `print_statistical_validation_report()` | Placeholder text formatter. | returns/config → empty string/result | None | none | tests | Test-only | No demonstrated value |
| `serialize_report()` | JSON or minimal Markdown serialization. | report/format → `SerializedReport` | None | serialization/type errors | tests/usage | Test-only evidence | Useful |
| `HashPolicy`, `compute_report_hash()` | Hashes deterministic report projection excluding metadata. | report/policy → hex string | None | serialization errors | tests/usage | Test-only evidence | Useful |

### Scorecards

| Symbol | Responsibility | Inputs → Return | Side effects | Failure behavior | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| five scorecard dataclasses | Configuration, rule, recommendation, assessment, result. | fields → object | None | construction errors | evaluator/tests | Used | Supporting |
| `sqn(report, config=None)` | Reads SQN and creates assessment. | report → assessment | None | defaults missing SQN to zero | tests/usage | Test-only | Useful but shape-sensitive |
| `sample_size_warning(report, config=None)` | Scores trade sample count. | report → assessment | None | defaults missing count to zero | tests/usage | Test-only | Useful but shape-sensitive |
| `evaluate_strategy_quality(report, config=None, request_id=None)` | Threshold scorecard and recommendation. | report → response | None | invalid report error response | tool API/tests/usage | Possibly used | Useful but not directly composable with report output |
| `scorecards_policy_boundary()` | Logs and returns no evidence. | none → `None` | None | None | no confirmed caller | Unknown | No demonstrated value |

### Statistics

| File / symbols | Responsibility | Inputs → Return | Side effects | Failure/placeholder behavior | Callers | Usage | Value |
|---|---|---|---|---|---|---|---|
| `distributions.py` core functions | Moments, percentile, tail, normality approximation, Q-Q, fit, histogram, outliers. | numeric series → scalar/dict/list | None | neutral defaults for small/empty samples | tests/usage | Mostly test-only | Useful |
| `calculate_distribution_metrics()` | Aggregate distribution response used by report. | returns → response | None | validation/error envelope | report builder/tests | Used | Essential |
| `statistics_distribution_boundary()` | Returns declarative flags. | none → dict | None | none | usage only | Test-only | Questionable |
| `multiple_testing.py::whites_reality_check*` | Advertised reality checks. | returns/reports → float | None | always `0.25` | tests/usage | Test-only | No demonstrated analytical value |
| `deflated_sharpe_ratio()` | Fixed 10% haircut. | Sharpe/returns → float | None | does not implement full DSR | tests | Test-only | Questionable |
| `probability_of_backtest_overfitting()` | Advertised PBO. | matrix → float | None | always `0.15` | tests/usage | Test-only | No demonstrated analytical value |
| `walk_forward_degradation_score()` | Relative PF decay. | IS/OOS mappings → float | None | zero guards | tests | Test-only | Useful |
| Bonferroni/BH corrections | Multiple-testing p-value adjustments. | p-values → list | None | limited validation | tests/usage | Test-only | Useful |
| `stability_score()` | PF dispersion score. | window mappings → float | None | neutral defaults | tests/usage | Test-only | Useful |
| `bootstrap_confidence_intervals()` | Seeded non-parametric mean CI. | values/options → pair | None | empty → `(0,0)` | report builder/tests/usage | Used | Essential |
| `permutation_test()` | Seeded two-group mean-difference test. | two groups/options → float | None | empty → `1.0` | tests/usage | Test-only | Useful |
| `permutation_test_backtest()` | Backtest wrapper. | reports → float | None | always `0.05` | tests | Test-only | No demonstrated analytical value |
| `bootstrap_confidence_intervals_backtest()` | Backtest wrapper. | report → pair | None | always `(1.2, 1.8)` | tests | Test-only | No demonstrated analytical value |
| `bootstrap_probability_above_threshold()` | Official seeded bootstrap probability tool. | values/threshold → response | None | empty input error response | tests/usage | Test-only evidence | Useful |
| `statistics_resampling_boundary()` | Returns deterministic-control declaration. | none → dict | None | none | usage only | Test-only | Questionable |

## 6. Actual Workflows

### `V1-WF-ANALYTICS-001` — Build a Canonical Analytics Report

* **Scope:** Internal, with cross-domain input
* **Trigger:** Caller supplies a backtest, simulation, paper, or historical live trading-result dictionary.
* **Input boundary:** `tool_api.build_analytics_report()` or `reports.sections.build_analytics_report()`
* **Functions and methods used:**
  * `TradingResultAdapter.to_canonical()`
  * `calculate_trade_metrics()`
  * `calculate_equity_metrics()`
  * `_parse_equity_curve()`
  * `returns_series()`
  * `calculate_risk_metrics()`
  * `calculate_ratio_metrics()`
  * `calculate_distribution_metrics()`
  * `_raw_calculate_drawdown_metrics()`
  * optional `calculate_benchmark_metrics()`
* **Files involved:** `tool_api.py`, `adapters/canonicalize.py`, `reports/sections.py`, `metrics/aggregate.py`, `metrics/equity.py`, `metrics/drawdown.py`, `metrics/risk.py`, `metrics/ratios.py`, `statistics/distributions.py`, `benchmarks/*`
* **External dependencies:** `app.utils` response/metadata/stable-ID helpers; input originates from simulator/trading/history domains.
* **Output boundary:** `StandardResponse.data` containing report ID, status, section dictionary, warnings, quality flags, and metadata.
* **Failure behaviour:** Non-dictionary or invalid canonical data returns an error envelope. Trade/equity metric failure aborts. Missing benchmark produces a partial report and blocker warning rather than an error.
* **Operational status:** **Working**, with limitations
* **Evidence:** `reports/sections.py::build_analytics_report`; unit tests verify missing/available benchmark paths.

```text
trading result
→ TradingResultAdapter.to_canonical()
→ required trade metrics
→ required equity metrics
→ returns
→ risk + ratios + distribution + drawdown
→ optional benchmark comparison
→ structured StandardResponse report
```

### `V1-WF-ANALYTICS-002` — All / Long / Short Analytics Overview

* **Scope:** Internal
* **Trigger:** `tool_api.get_analytics_overview(request)`
* **Input boundary:** Request dictionary containing `trades`.
* **Sequence:** direction filtering → `calculate_analytics_for_subset()` three times → trade metrics + drawdown + cost totals.
* **Files involved:** `tool_api.py`, `metrics/aggregate.py`, `metrics/trade_outcomes.py`, `metrics/ratios.py`, `metrics/drawdown.py`, `metrics/position_exposure.py`
* **External dependencies:** `app.utils` response envelopes.
* **Output boundary:** `StandardResponse` containing `all`, `long`, and `short`.
* **Failure behaviour:** Bad request/trades type becomes error response; lower-level exceptions are enveloped.
* **Operational status:** **Working**
* **Evidence:** direct source call path and usage example.

```text
request.trades
→ split by direction
→ calculate_analytics_for_subset(all)
→ calculate_analytics_for_subset(long)
→ calculate_analytics_for_subset(short)
→ overview response
```

### `V1-WF-ANALYTICS-003` — Benchmark-Relative Performance

* **Scope:** Internal
* **Trigger:** direct official tool call or optional report benchmark section.
* **Input boundary:** strategy and benchmark return series.
* **Sequence:** `_align_series()` → beta/alpha/R²/tracking error/information ratio/batting average/capture.
* **Files involved:** `benchmarks/alignment.py`, `benchmarks/metrics.py`
* **External dependencies:** optional pandas behavior for pandas-like inputs.
* **Output boundary:** scalar kernels or aggregate `StandardResponse`.
* **Failure behaviour:** no aligned values returns validation error response. Several insufficient-data cases return neutral/default values; beta defaults to `1.0`.
* **Operational status:** **Working**, with questionable edge semantics.
* **Evidence:** report builder, benchmark unit tests, usage imports.

### `V1-WF-ANALYTICS-004` — Strategy Quality Scorecard

* **Scope:** Internal
* **Trigger:** caller passes report-like mapping to `evaluate_strategy_quality()`.
* **Input boundary:** flat `sections` mapping expected by scorecard.
* **Sequence:** read trade/ratio/drawdown values → threshold deductions → strengths/warnings → non-binding recommendation.
* **Files involved:** `scorecards/quality.py`
* **External dependencies:** `app.utils` response envelope.
* **Output boundary:** score, evidence strings, recommendation, disclaimer.
* **Failure behaviour:** invalid report returns error response.
* **Operational status:** **Partial**
* **Evidence:** scorecard unit tests use flat section values.
* **Disconnection:** `build_analytics_report()` emits each section as `{"status": ..., "data": {...}}`, but scorecard reads values directly from the section dictionary. Passing the report output directly causes defaults to be used unless a caller manually flattens sections.

```text
flat report sections
→ threshold score
→ recommendation

canonical report output
→ nested section.data
→ scorecard does not descend into data
→ defaults / misleading score
```

### `V1-WF-ANALYTICS-005` — Dashboard Overview Projection

* **Scope:** Internal, intended cross-domain output to UI/API
* **Trigger:** caller supplies report mapping/model.
* **Input boundary:** report sections and optional equity curve.
* **Sequence:** extract summary values → `truncate_series()` → produce cards/chart/warnings.
* **Files involved:** `dashboards/overview.py`, `dashboards/truncation.py`
* **External dependencies:** none beyond response utilities.
* **Output boundary:** `StandardResponse` when no config is supplied; raw `DashboardPayload` when config is supplied.
* **Failure behaviour:** invalid report returns error response.
* **Operational status:** **Working**, but return type is mode-dependent.
* **Evidence:** usage and metric tests.

### `V1-WF-ANALYTICS-006` — Journal-to-Analytics Input Adaptation

* **Scope:** Cross-domain
* **Trigger:** simulation or live-trading journal supplied.
* **Input boundary:** `SimulationJournal` or `LiveTradeJournal`.
* **Sequence:** extract events/fills → construct analytics result dictionary.
* **Files involved:** `adapters/journal_adapters.py`
* **External dependencies:** trading contracts; type-only references to simulator/risk/audit contracts.
* **Output boundary:** dictionary consumable by analytics canonicalization/reporting.
* **Failure behaviour:** malformed event structures can raise conversion errors.
* **Operational status:** **Unverified**
* **Evidence:** usage example and adapter code; no simulator/live runtime caller confirmed.

```text
simulation/live journal
→ journal adapter
→ analytics-shaped dictionary
→ optional canonicalization/reporting
```

### `V1-WF-ANALYTICS-007` — Seeded Statistical Validation

* **Scope:** Internal
* **Trigger:** return series supplied.
* **Input boundary:** `calculate_statistical_validation()` or direct bootstrap/permutation tools.
* **Sequence:** parse floats → seeded bootstrap CI; direct permutation tool also reshuffles two groups.
* **Files involved:** `reports/sections.py`, `statistics/resampling.py`
* **External dependencies:** standard-library `random`.
* **Output boundary:** tuple/scalar or `StandardResponse`.
* **Failure behaviour:** empty direct bootstrap returns zeros; official wrapper returns an error for empty values.
* **Operational status:** **Partial**
* **Evidence:** real bootstrap/permutation loops exist.
* **Limitation:** report wrapper inserts fixed `p_value_reality_check=0.25`; backtest-specific wrappers return constants.

### `V1-WF-ANALYTICS-008` — Serialize and Hash Report

* **Scope:** Internal, intended cross-domain output
* **Trigger:** report object/dictionary supplied.
* **Input boundary:** `serialize_report()` and `compute_report_hash()`.
* **Sequence:** project report fields → JSON/Markdown serialization; separately remove metadata/non-deterministic fields → SHA-256 or MD5.
* **Files involved:** `reports/formatters.py`, `reports/hashes.py`
* **External dependencies:** standard library.
* **Output boundary:** serialized string object and hash string.
* **Failure behaviour:** unsupported values can raise serialization errors.
* **Operational status:** **Working**
* **Evidence:** unit tests verify deterministic metadata exclusion and both formats.

### `V1-WF-ANALYTICS-009` — Portfolio Analytics Report

* **Scope:** Cross-domain
* **Trigger:** portfolio result supplied.
* **Input boundary:** `build_portfolio_analytics_report()`.
* **Sequence:** validate dictionary → inspect component currencies → require FX conversions if mixed → emit fixed aggregate metrics.
* **Files involved:** `reports/sections.py`
* **External dependencies:** caller-supplied FX evidence.
* **Output boundary:** portfolio report response.
* **Failure behaviour:** invalid input or mixed currencies without FX fails closed.
* **Operational status:** **Broken as analytics**
* **Evidence:** `aggregate_metrics` are always zero; component results are not calculated or aggregated.

### `V1-WF-ANALYTICS-010` — Compare Two Reports

* **Scope:** Internal
* **Trigger:** reference and candidate reports supplied.
* **Input boundary:** `compare_analytics_reports()`.
* **Sequence:** extract IDs → return three fixed zero differences.
* **Files involved:** `reports/sections.py`
* **External dependencies:** none.
* **Output boundary:** comparison response.
* **Failure behaviour:** missing mappings can become error response.
* **Operational status:** **Broken**
* **Evidence:** no metric extraction or subtraction occurs.

### `V1-WF-ANALYTICS-011` — Prop-Firm Compliance Evidence

* **Scope:** Cross-domain
* **Trigger:** report supplied.
* **Input boundary:** `calculate_prop_firm_compliance()`.
* **Sequence:** ignores report values → emits two passed rules and `compliant=True`.
* **Files involved:** `reports/sections.py`
* **External dependencies:** none.
* **Output boundary:** compliance response.
* **Failure behaviour:** even `None` succeeds under current test expectation.
* **Operational status:** **Broken**
* **Evidence:** no report inspection; unit test explicitly accepts success for `None`.

## 7. Usage and Caller Map

Because the root exports 351 names, the map is grouped by concrete implementation source while retaining the individual public names in Section 3 and Section 5.

| Public symbol / family | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `TradingResultAdapter.to_canonical` | `reports.sections.build_analytics_report` | direct class method | Runtime internal | report source call |
| `calculate_trade_metrics` | report builder; subset aggregator; tool API; usage/tests | direct | Runtime internal + tests | `sections.py`, `aggregate.py`, usage/test imports |
| `calculate_equity_metrics` | report builder; tool API; usage/tests | direct | Runtime internal + tests | `sections.py`, `tool_api.py` |
| `returns_series`, equity parsing | report builder | direct | Runtime internal | `sections.py` |
| `calculate_drawdown_metrics` | report builder; tool API; tests | direct | Runtime internal + tests | `sections.py`, `tool_api.py` |
| `calculate_risk_metrics` | report builder; tool API; tests | direct | Runtime internal + tests | `sections.py`, `tool_api.py` |
| `calculate_ratio_metrics` | report builder; tests | direct | Runtime internal + tests | `sections.py` |
| `calculate_distribution_metrics` | report builder; tests | direct | Runtime internal + tests | `sections.py` |
| benchmark metric family | aggregate benchmark tool; report builder; tests | direct | Runtime internal + tests | `benchmarks/metrics.py`, `sections.py` |
| trade-outcome metric family | aggregate, curves, ratios, R-multiples, tests | direct | Runtime internal + tests | local imports in metric files |
| R-multiple family | trade/ratio/distribution metrics; tests | direct | Runtime internal + tests | local imports and tests |
| exposure cost functions | subset aggregate; costs; tests | direct | Runtime internal + tests | `aggregate.py`, `costs.py` |
| `calculate_analytics_for_subset` | `tool_api.get_analytics_overview` | direct | Runtime internal | `tool_api.py` |
| `build_analytics_report` | tool API wrapper; formatter; tests/usage | direct/wrapper | Runtime internal + tests | `tool_api.py`, `formatters.py` |
| portfolio/comparison/compliance tools | tests and facade exports | direct | Test-only confirmed | `test_report.py` |
| scorecard functions | tool API exports; scorecard tests/usage | direct | Test-only external evidence | `tool_api.py`, `test_scorecard.py` |
| dashboard builder/truncation | dashboard builder, tests/usage | direct | Runtime internal + tests | `overview.py`, test/usage imports |
| report serializer/hash | tests/usage | direct | Test-only confirmed | `test_report.py`, usage |
| bootstrap confidence interval | statistical report wrapper; tests/usage | direct | Runtime internal + tests | `sections.py` |
| multiple-testing placeholders | tests/usage | direct | Test-only | `test_metrics.py`, usage |
| adapter protocol/journal functions | usage/tests | direct | Test/example-only | `06_analytics.py` |
| boundary functions | usage/tests | direct | Test/example-only | `06_analytics.py` |
| registry active-request functions | usage/tests | direct | Test/example-only | `06_analytics.py` |
| registry `register_tool` / `TOOL_REGISTRY` | no decorated package tool found | decorator/registry | Unconfirmed | registry source |
| `app.return_on_initial_capital`, `app.total_return` | lazy root compatibility exports | dynamic `__getattr__` | Production-compatible surface; external caller unconfirmed | `app/__init__.py` |
| `MetricDefinitionCatalog` | lazy root compatibility export | dynamic `__getattr__` | Production-compatible surface; external caller unconfirmed | `app/__init__.py` |
| 153 explicitly imported analytics names | `tests/analytics/usage/06_analytics.py` | direct imports | Usage/example | usage source |
| broad root metric surface | `tests/analytics/unit/test_metrics.py` and `compat_test_helper.py` | direct and wrapper imports | Tests | test source |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols/capabilities consumed | Where used | Evidence |
|---|---|---|---|
| `app.utils` | logging, `StandardResponse`, metadata, success/error envelopes, stable IDs, canonical JSON/security patterns, timestamp normalization | almost every tool/contract file | explicit imports |
| `app.services.simulator.models` | `BacktestResult` compatibility/input type | `adapters/canonicalize.py` | explicit import |
| `app.services.trading.contracts` | `TradeResult`, `ExecutionReport`, `Fill` | `adapters/journal_adapters.py` | explicit import |
| `app.services.risk` contracts | risk decision/snapshot typing | journal adapter type-checking paths | `TYPE_CHECKING` imports |
| pandas | alignment and JSON-safe Series/DataFrame conversion | benchmark alignment, serialization | runtime/required import paths |
| numpy | JSON-safe scalar/array conversion | contract serialization | explicit import |
| pydantic | audit and portfolio snapshot contracts | `contracts/audit.py`, `contracts/portfolio.py` | explicit import |
| standard library | math/statistics/random/datetime/hash/json/dataclasses | metric/statistics/report implementation | explicit imports |

No outbound broker call, network call, persistence write, event publication, or order mutation was found.

### Inbound — others depend on this domain

| Consuming package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| `app` root package | `return_on_initial_capital`, `total_return`, `MetricDefinitionCatalog` | lazy backwards-compatible top-level imports | `app/__init__.py` |
| analytics report internals | adapters and lower-level metrics | report orchestration | `reports/sections.py` |
| analytics dashboard | report model/sections and truncation | UI payload projection | `dashboards/overview.py` |
| analytics tool facade | report/benchmark/risk/scorecard functions | public read-only tool surface | `tool_api.py` |
| `tests/analytics/unit` | broad root/submodule surface | behavior and compatibility tests | inspected unit tests |
| `tests/analytics/usage` | at least 153 named imports | deterministic examples | `06_analytics.py` |
| production API/agent/runtime | none confirmed | n/a | no accessible caller evidence |

**Important boundary finding:** `app.services.optimization.scoring` independently implements Sharpe, Sortino, Calmar, drawdown, and return calculations rather than importing analytics. This is overlapping capability, not an inbound dependency.

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `errors.AnalyticsError` exception | `boundaries.envelopes.AnalyticsError` dataclass | Same public name, different category and semantics | both exported through different surfaces; root exports boundary version | Consumers may catch/construct the wrong type |
| `contracts.audit.Contract` | `contracts.portfolio.Contract` | Near-identical fields, validators, JSON/hash/version methods | matching implementations in both files | Divergent fixes and contract behavior |
| `contracts.models.DashboardPayload` / `TruncationMetadata` | `dashboards.overview` equivalents | Duplicate payload concepts with different fields | both public | Type incompatibility and caller confusion |
| `boundaries.redaction.redact` | `contracts.warnings.redact_sensitive_info` | Recursive sensitive-data masking | two implementations | Inconsistent policy/results |
| redaction implementations | `app.utils` sensitive-key utilities | Third overlapping security/redaction source | imports in contracts | Boundary drift |
| `boundaries.request_validation.request_id` | `registry.analytics_registry.request_id` | Request ID extraction | one validates; one mutates registry and warns | Same name, different side effects |
| the above | `reports.sections.request_id` | Third implementation | report version merely returns input | No coherent request-ID contract |
| `metrics.distribution` | `statistics.distributions` | Skew, kurtosis, percentiles, JB, tails, distributions | separate functions with different return conventions | Different formulas/defaults under similar names |
| `metrics.curves.balance_curve` | `metrics.curves.equity_curve` | Exact delegation to same function | source | Redundant public surface |
| `compute_trade_metrics` | `compute_r_trade_metrics` | Exact delegation | `r_multiples.py` | Wrapper adds no behavior |
| `jarque_bera_test_metric` | `jarque_bera_test` | Exact delegation | `metrics/distribution.py` | Wrapper adds no behavior |
| `metrics.exports` aliases | underlying metric functions | Ten forwarding wrappers | `exports.py` | Inflated API and naming complexity |
| `scorecards.quality.sqn` | `metrics.ratios.sqn` / `system_quality_number` | SQN calculation/evaluation split under same name | exports and source | Ambiguous import and responsibility |
| `metrics.position_exposure.max_gross_size_held` | `max_size_held` | Same maximum-individual-size implementation | source | Names imply different metrics but values match |
| analytics ratio/risk functions | `app.services.optimization.scoring` | Sharpe, Sortino, Calmar, drawdown, return scoring | optimization source implements its own calculations | Cross-domain metric inconsistency |
| report dataclasses in `reports.sections` | report dataclasses in `contracts.models` | Same report names, different field contracts | both public | Runtime/type confusion |
| `StandardResponse` tools | contract `ToolEnvelope` builders | Two response-envelope systems | `app.utils` vs boundaries | Inconsistent output types |

## 10. Unused or Questionable Items

No item is labelled dead code because a complete high-confidence repository grep was not available.

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `contracts/audit.py` | Not exported from `contracts.__init__`; no caller found in inspected files | exports, imports, tests, usage, known cross-domain files | Medium | file and package init |
| `contracts/portfolio.py` | Not exported from `contracts.__init__`; no runtime caller found | same categories | Medium | file and package init |
| `bench_alignment_boundary()` | Only logs and returns `None` | package imports, report path, tests/usage | Medium | source |
| `scorecards_policy_boundary()` | Only logs and returns `None` | package imports, tests/usage | Medium | source |
| `statistics_*_boundary()` and `metrics_*_boundary()` declarations | Return static declarations; used mainly in usage script | usage/tests and internal call paths | Medium | source/usage |
| `register_tool()` / `TOOL_REGISTRY` | Registry is defined, but no analytics function was found decorated/registered | package sources, imports, catalog, usage | Medium | registry source |
| `_align_series`, `_downsample_curve` | Private-looking helpers deliberately exported | `__all__` checks and tests | High for exposure; Medium for external need | package init files |
| `metrics/exports.py` | Compatibility wrappers mostly forward unchanged | implementation and test imports | High | source |
| `format_summary_as_rows()` | Always empty | implementation/tests | High | source and assertion |
| `print_statistical_validation_report()` | Always empty | implementation/tests | High | source and assertion |
| portfolio aggregate metrics | Fixed zeros | implementation/tests | High | report source |
| report comparison differences | Fixed zeros | implementation/tests | High | report source |
| compliance result | Always passes and ignores input | implementation/tests | High | report source |
| backtest-specific bootstrap/permutation helpers | Fixed values | implementation/tests | High | resampling source |
| White’s/PBO functions | Fixed values | implementation/tests | High | multiple-testing source |
| compatibility aliases in adapter and root packages | Exist primarily to preserve old import names | package init/history/tests | Medium | commit history and imports |
| `RedactionPolicy.STRICT` | Policy argument is accepted but not used to alter behavior | source inspection | High | `boundaries/redaction.py` |
| `reports.sections.request_id()` | Identity wrapper with no validation or metadata extraction | source and callers | Medium | source |

## 11. Incomplete or Disconnected Workflows

| Workflow/capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Report → scorecard | Scorecard does not read nested section `data` emitted by report builder | Direct chaining can score defaults instead of actual metrics | `sections.py` output shape vs `quality.py` reads |
| Report → dashboard equity chart | Report builder does not include top-level `equity_curve`; dashboard looks for it | Dashboard chart can be empty even when equity metrics exist | report and dashboard sources |
| Portfolio report | Component reports are not built/aggregated | All aggregate metrics are zero | `build_portfolio_analytics_report` |
| Report comparison | Metric values are not extracted | Comparison always reports no differences | `compare_analytics_reports` |
| Prop-firm compliance | No rule configuration or report values are evaluated | False assurance; even `None` succeeds | implementation/test |
| Statistical validation | Reality-check p-value is fixed | Output appears analytical but is not evidence-based | `calculate_statistical_validation` |
| Multiple-testing/PBO | Core algorithms absent | Misleading numerical outputs | `multiple_testing.py` |
| Backtest resampling | Report extraction/resampling absent | Fixed CI and p-value | `resampling.py` |
| Summary/text formatting | Formatting logic absent | Empty report output | `formatters.py` |
| Tool registry | No registration connection to official tools | Registry cannot discover/invoke tools automatically | registry and tool API |
| Journal adapters | No confirmed simulator/live call site | Valuable adapter path may remain isolated | adapter code/usage only |
| Efficiency/time/cost metrics | Not included in main report sections despite extensive implementation | Calculations remain isolated from primary workflow | report call graph |
| Workload limits | Main report/tool facade does not call `enforce_limits()` | Cataloged limits do not protect primary workloads | tool/report call graph |
| Contract `ToolEnvelope` | Official tools use `app.utils.StandardResponse` instead | Parallel envelope contract is disconnected | imports |
| Warning catalog | Main report constructs ad hoc dict warnings | Catalog/builder consistency is bypassed | report source |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-ANALYTICS-001` | Current package is a merged V1/V2 surface, not a clean V1 snapshot. | repository history/package | Historical behavior and current behavior cannot be cleanly separated. | commits `a499e332...`, `5411bc53...` |
| `V1-ISSUE-ANALYTICS-002` | Excessive root public surface using wildcard import and dynamic `__all__`. | `analytics/__init__.py` | 351 names obscure the supported boundary and expose internal/compatibility helpers. | root source |
| `V1-ISSUE-ANALYTICS-003` | No confirmed production/API/agent caller. | repository integration surface | Domain may be a library demonstrated only by tests/examples. | caller audit |
| `V1-ISSUE-ANALYTICS-004` | Conflicting `AnalyticsError` definitions. | `errors.py`, `boundaries/envelopes.py` | Exception handling and construction are ambiguous. | source |
| `V1-ISSUE-ANALYTICS-005` | Duplicated base `Contract`. | `contracts/audit.py`, `contracts/portfolio.py` | Validation/hash/version behavior can diverge. | source |
| `V1-ISSUE-ANALYTICS-006` | Duplicate report/dashboard models. | `contracts/models.py`, `reports/sections.py`, `dashboards/overview.py` | Incompatible objects with same names. | source |
| `V1-ISSUE-ANALYTICS-007` | Inconsistent return conventions. | metrics, dashboards, formatters, reports | Same capability can return raw value, `MetricResult`, model, dict, or `StandardResponse` depending arguments. | signatures/source |
| `V1-ISSUE-ANALYTICS-008` | Primary report and scorecard shapes do not compose. | `reports/sections.py`, `scorecards/quality.py` | Scorecard can use defaults rather than report metrics. | source comparison |
| `V1-ISSUE-ANALYTICS-009` | Portfolio report is a placeholder. | `build_portfolio_analytics_report` | Advertised aggregate analytics are absent. | fixed zero metrics |
| `V1-ISSUE-ANALYTICS-010` | Report comparison is a placeholder. | `compare_analytics_reports` | Candidate/reference differences are not calculated. | fixed zero output |
| `V1-ISSUE-ANALYTICS-011` | Compliance tool always passes. | `calculate_prop_firm_compliance` | Can provide false compliance evidence. | source/test |
| `V1-ISSUE-ANALYTICS-012` | Statistical functions return hard-coded results. | `statistics/multiple_testing.py`, backtest helpers in `resampling.py` | Numerical outputs appear authoritative but are not derived from input. | source |
| `V1-ISSUE-ANALYTICS-013` | Empty formatter implementations are treated as accepted behavior by tests. | `reports/formatters.py`, `test_report.py` | Tests preserve incompleteness rather than detect it. | source/test |
| `V1-ISSUE-ANALYTICS-014` | Test compatibility logic lives outside production package. | `tests/analytics/unit/compat_test_helper.py` | Passing tests may rely on test-only V1 wrappers/reimplementations. | test source |
| `V1-ISSUE-ANALYTICS-015` | Three request-ID implementations have different behavior. | boundaries, registry, reports | Traceability semantics are inconsistent. | source |
| `V1-ISSUE-ANALYTICS-016` | Parallel response-envelope systems. | `app.utils.StandardResponse`, `contracts.ToolEnvelope`, boundary envelope builders | Callers cannot assume one response contract. | imports/signatures |
| `V1-ISSUE-ANALYTICS-017` | Private-looking helpers are public exports. | benchmark/dashboard `__init__.py` | Internal implementation becomes compatibility surface. | `__all__` |
| `V1-ISSUE-ANALYTICS-018` | Redaction is duplicated and policy is ignored. | boundaries/contracts/app.utils | Security behavior may vary by import. | source |
| `V1-ISSUE-ANALYTICS-019` | Distribution calculations exist in two packages with different contracts. | `metrics/distribution.py`, `statistics/distributions.py` | Formula/default/result drift. | source/exports |
| `V1-ISSUE-ANALYTICS-020` | Alias wrappers inflate the package without new behavior. | `metrics/exports.py`, curves, R-multiples | Harder discovery and maintenance. | direct delegation |
| `V1-ISSUE-ANALYTICS-021` | Workload limits are not enforced by the main tool/report path. | boundaries vs tool/report modules | Large inputs can bypass cataloged ceilings. | call graph |
| `V1-ISSUE-ANALYTICS-022` | Registry is disconnected from official tools. | `registry/analytics_registry.py`, `tool_api.py` | Dynamic discovery cannot be confirmed. | no registrations found |
| `V1-ISSUE-ANALYTICS-023` | Exposure names overstate calculations. | `position_exposure.py` | “Gross held” is max individual size; net size accumulates trades without close-event unwinding. | implementation |
| `V1-ISSUE-ANALYTICS-024` | Benchmark alignment may not preserve original pandas index alignment. | `benchmarks/alignment.py` | Re-wrapping inputs in new `pd.Series` can discard source indices. | implementation |
| `V1-ISSUE-ANALYTICS-025` | Benchmark beta defaults to `1.0` for insufficient/zero-variance data. | `benchmarks/metrics.py::beta` | Missing evidence can look like market beta. | implementation |
| `V1-ISSUE-ANALYTICS-026` | Truncation is not guaranteed to honor `max_points`. | `dashboards/truncation.py` | Step sampling plus reserved extrema can return more points than configured. | algorithm |
| `V1-ISSUE-ANALYTICS-027` | Report claims deterministic behavior but inserts current time. | `reports/sections.py` | Full report payload differs across runs; hash only avoids this by excluding metadata. | source |
| `V1-ISSUE-ANALYTICS-028` | Main report omits implemented efficiency, cost, time, and statistical-validation sections advertised by architecture metadata. | `reports/sections.py` | Large portions of package remain isolated. | report sections vs metric surface |
| `V1-ISSUE-ANALYTICS-029` | README/test path drift. | `analytics/README.md` vs repository | Documentation references `tests/usage/06_analytics.py`; actual file is under `tests/analytics/usage/`. | fetch results |
| `V1-ISSUE-ANALYTICS-030` | R-multiple fallback silently changes units to PnL when risk is missing. | `metrics/r_multiples.py` | Values are not true R multiples; warning is returned separately and can be ignored. | implementation |
| `V1-ISSUE-ANALYTICS-031` | Root `AnalyticsError` resolves to boundary dataclass rather than exception due import choice. | `analytics/__init__.py` | `from app.services.analytics import AnalyticsError` is semantically surprising. | root imports |
| `V1-ISSUE-ANALYTICS-032` | Optimization independently reimplements overlapping analytics. | `app/services/optimization/scoring.py` | Cross-domain Sharpe/Sortino/Calmar values can disagree. | inspected optimization source |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-ANALYTICS-001` | Trading-result canonicalization | `adapters/canonicalize.py` | WF-001 | Used | Essential | Strong input boundary |
| `V1-CAP-ANALYTICS-002` | Simulation/live journal adaptation | `journal_adapters.py` | WF-006 | Test-only confirmed | Useful | Runtime connection unverified |
| `V1-CAP-ANALYTICS-003` | Trade outcome analytics | `trade_outcomes.py`, `aggregate.py` | WF-001, WF-002 | Used | Essential | Core report dependency |
| `V1-CAP-ANALYTICS-004` | Equity and return analytics | `equity.py`, `pnl.py`, `curves.py` | WF-001 | Used | Essential | Multiple return conventions |
| `V1-CAP-ANALYTICS-005` | Drawdown analytics | `drawdown.py` | WF-001, WF-002 | Used | Essential | Very large single file |
| `V1-CAP-ANALYTICS-006` | Risk analytics | `risk.py` | WF-001 | Used | Essential | Includes return, ruin, exposure, margin |
| `V1-CAP-ANALYTICS-007` | Ratio analytics | `ratios.py` | WF-001 | Used | Essential | Broad, overlapping names |
| `V1-CAP-ANALYTICS-008` | Benchmark comparison | `benchmarks/*` | WF-003, WF-001 | Used | Essential | Edge semantics questionable |
| `V1-CAP-ANALYTICS-009` | Distribution profiling | `statistics/distributions.py`, `metrics/distribution.py` | WF-001, WF-007 | Used/Test-only | Useful | Duplicated implementations |
| `V1-CAP-ANALYTICS-010` | Seeded bootstrap/permutation | `statistics/resampling.py` | WF-007 | Partly used | Useful | Backtest wrappers are stubs |
| `V1-CAP-ANALYTICS-011` | Multiple-testing/overfitting diagnostics | `statistics/multiple_testing.py` | WF-007 | Test-only | Questionable | Major functions hard-coded |
| `V1-CAP-ANALYTICS-012` | Canonical report generation | `reports/sections.py`, `tool_api.py` | WF-001 | Used internally/tests | Essential | No production caller confirmed |
| `V1-CAP-ANALYTICS-013` | Portfolio report | `build_portfolio_analytics_report` | WF-009 | Test-only | No demonstrated value | Fixed metrics |
| `V1-CAP-ANALYTICS-014` | Report comparison | `compare_analytics_reports` | WF-010 | Test-only | No demonstrated value | Fixed differences |
| `V1-CAP-ANALYTICS-015` | Prop-firm compliance evidence | `calculate_prop_firm_compliance` | WF-011 | Test-only | No demonstrated value | Always passes |
| `V1-CAP-ANALYTICS-016` | Strategy quality scorecard | `scorecards/quality.py` | WF-004 | Test-only external evidence | Useful | Report shape mismatch |
| `V1-CAP-ANALYTICS-017` | Dashboard projection | `dashboards/*` | WF-005 | Test-only external evidence | Useful | Inconsistent return type |
| `V1-CAP-ANALYTICS-018` | Report serialization | `reports/formatters.py::serialize_report` | WF-008 | Test-only | Useful | Markdown is minimal |
| `V1-CAP-ANALYTICS-019` | Deterministic report hashing | `reports/hashes.py` | WF-008 | Test-only | Useful | MD5 also exposed |
| `V1-CAP-ANALYTICS-020` | Cost analytics | `costs.py`, exposure cost functions | WF-002 | Partly used | Useful | Not in main report |
| `V1-CAP-ANALYTICS-021` | MAE/MFE and capital efficiency | `efficiency.py` | none confirmed | Test-only | Useful | Disconnected |
| `V1-CAP-ANALYTICS-022` | Time/session analysis | `time_analysis.py` | none confirmed | Test-only | Useful | Disconnected |
| `V1-CAP-ANALYTICS-023` | Workload limit validation | `boundaries/limits.py` | none in main facade | Test/example-only | Useful | Not enforced centrally |
| `V1-CAP-ANALYTICS-024` | Redaction and warning evidence | boundaries/contracts warnings | none in main report | Test/example-only | Useful | Duplicated/bypassed |
| `V1-CAP-ANALYTICS-025` | Tool/request registry | `registry/analytics_registry.py` | none confirmed | Test/example-only | Questionable | No tool registration found |
| `V1-CAP-ANALYTICS-026` | Catalog and schema validation | `contracts/metric_catalog.py`, `models.py` | adapter/support | Used | Supporting | Catalog test paths partly stale |
| `V1-CAP-ANALYTICS-027` | Portfolio snapshot contracts | `contracts/portfolio.py` | none confirmed | Unknown | Questionable | Not exported |
| `V1-CAP-ANALYTICS-028` | Audit event contracts | `contracts/audit.py` | none confirmed | Unknown | Questionable | Not exported |
| `V1-CAP-ANALYTICS-029` | V1 compatibility aliases | root, adapter init, metrics exports, app root | tests/legacy imports | Test/compatibility | Questionable | Inflates surface |
| `V1-CAP-ANALYTICS-030` | Standard read-only tool responses | `app.utils.StandardResponse` wrappers | WF-001–005, 007, 009–011 | Used internally | Supporting | Competes with `ToolEnvelope` |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The strongest demonstrated behavior is the pure/read-only metric core and canonical single-result report pipeline:

* trading-result validation and normalization;
* trade filtering/classification and aggregate trade metrics;
* equity/return series calculations;
* drawdown, risk, and ratio calculations;
* benchmark-relative calculations;
* distribution aggregate used by reports;
* seeded bootstrap confidence intervals;
* deterministic chart truncation;
* report JSON/Markdown serialization and metadata-excluding hash;
* standard error-envelope behavior for the main official tools.

These capabilities have real internal call paths and are exercised by tests/examples.

### Behaviour that exists but is disconnected

* journal adapters have no confirmed live/simulator caller;
* efficiency, time/session, detailed costs, many exposure metrics, and many statistics are not included in the main report;
* workload limits are not enforced by the main facade;
* warning/quality catalogs are bypassed by ad hoc report dictionaries;
* registry discovery is not connected to official tools;
* portfolio and audit snapshot contracts are not exposed through their package init;
* dashboard and scorecard outputs are not cleanly composable with the canonical report shape.

### Likely dead weight or no demonstrated value

The audit cannot label these as dead code with High confidence, but current value is not demonstrated for:

* static boundary-declaration functions that only log or return declarations;
* duplicate/parallel contracts and response envelopes;
* compatibility aliases that only forward calls;
* empty report formatter functions;
* fixed-value report comparison, compliance, PBO, White’s Reality Check, and backtest resampling functions;
* an unpopulated tool registry;
* unexported duplicate `Contract` implementations.

### Duplicated responsibilities

The package duplicates:

* errors;
* base contracts;
* dashboard/report models;
* redaction;
* request-ID handling;
* response envelopes;
* distribution metrics;
* R/SQN-related names;
* curve and compatibility wrappers.

There is additional cross-domain duplication in optimization scoring.

### Important uncertainties

* A complete repository grep could not be run, so indirect production imports, dynamic imports, configuration strings, plugin registration, and reflection cannot be ruled out.
* The current code is post-V1/V2 merge; exact legacy-only behavior requires checking out a known pre-merge commit or tag.
* Tests were not executed.
* No running API, agent, scheduler, or UI integration was available for runtime verification.

### Manual confirmation required

1. Identify the authoritative historical V1 commit/tag to separate legacy from current V2 code.
2. Confirm whether any API route, agent manifest, scheduler, or external service imports `tool_api` dynamically.
3. Confirm whether the fixed-value functions are intentional placeholders or unfinished production behavior.
4. Confirm whether consumers reshape report sections before scorecard/dashboard use.
5. Confirm whether `contracts/audit.py` and `contracts/portfolio.py` are imported through non-static mechanisms.
6. Run the analytics test suite and usage script against the audited revision and capture coverage by production file rather than relying on test-only compatibility wrappers.

## Evidence That Could Not Be Accessed

* A full local repository clone and repository-wide `rg`/AST call graph, because outbound DNS resolution was unavailable.
* GitHub code-search results for arbitrary symbol references, because the connector returned no indexed code hits.
* A clean historical V1 checkout/tag; the current branch contains an explicit V1/V2 merge.
* Runtime logs, deployed API/agent configuration, scheduler configuration, and dynamic plugin registrations outside the repository.
* Executed pytest/coverage results for the audited revision.
