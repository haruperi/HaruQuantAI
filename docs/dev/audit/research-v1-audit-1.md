# Research — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `research`
* **Repository:** `haruperi/HaruQuantAI`
* **Branch inspected:** default branch `main`
* **Package path:** `app/services/research/`
* **Tests path:** `tests/research/unit/`
* **Related packages searched:** `tests/research/usage/`, `app/utils/settings.py`, `app/utils/standard.py`, `app/utils/logger.py`, `app/utils/security.py`, repository history for the research initialization commit, and the package public facade.
* **Files inspected:** 13 Python files and 1 package README under `app/services/research/`; 2 unit-test files; 1 usage-example file; shared settings, standard errors, and project configuration.
* **Source-of-truth rule:** Conclusions below are based on the current code on `main`. The package README and initialization commit are used only to identify claimed intent and historical context.
* **Audit limitations:** The connected repository's code-search index was unavailable and the sandbox could not clone GitHub. Exact files could be fetched and repository commits compared, but an exhaustive repository-wide grep across every source file, configuration file, decorator, registry, string reference, and generated artifact could not be completed. Therefore, no item is labelled dead code with High confidence. Production usage findings are conservative: no production caller was confirmed, but indirect callers outside the accessible evidence cannot be ruled out.

### Files represented

**Domain package**

1. `app/services/research/README.md`
2. `app/services/research/__init__.py`
3. `app/services/research/data.py`
4. `app/services/research/errors.py`
5. `app/services/research/features.py`
6. `app/services/research/helpers.py`
7. `app/services/research/leakage.py`
8. `app/services/research/metrics.py`
9. `app/services/research/reporting.py`
10. `app/services/research/studies/__init__.py`
11. `app/services/research/studies/eds.py`
12. `app/services/research/studies/null_models.py`
13. `app/services/research/studies/structure.py`
14. `app/services/research/studies/unsupervised.py`

**Tests and examples**

1. `tests/research/unit/__init__.py`
2. `tests/research/unit/test_research.py`
3. `tests/research/usage/12_research.py`

## 2. Executive Summary

The Version 1 research domain is a broad, in-memory quantitative research library. It prepares OHLCV(S) `pandas.DataFrame` inputs, engineers indicators and forward labels, performs heuristic leakage checks and chronological splitting, calculates descriptive metrics, runs two rule-based edge studies, generates statistical null distributions, performs market-structure and optional unsupervised studies, and serializes reports to Markdown or JSON.

Eight coherent workflows can be reconstructed from the executable usage script and unit tests. The strongest workflows are dataset preparation, feature calculation, edge-study execution, basic bootstrap/permutation statistics, and local report generation. These workflows execute entirely from synthetic/in-memory data in tests and examples. No FastAPI route, agent tool, scheduler, production service, broker workflow, or other runtime caller was confirmed.

The package contains meaningful quantitative computations, but it also contains placeholder behavior presented as completed research capability. Examples include hard-coded session-strategy results, fixed market-structure scores, fixed strategy-fit and stability reports, a profile resolver that always returns `trending`, and a fixed report timestamp. The null-baseline implementation shuffles returns and then calculates their mean; permutation preserves the mean, so the resulting distribution is effectively constant and does not provide a useful baseline for the statistic being measured.

The package facade exports 149 names, including shared configuration classes from `app.utils.settings`. This creates a very large public surface and causes research import to execute the shared settings module, whose module-level singleton reads environment variables and an optional `.env` file. That contradicts the research facade and README claim that importing the package is side-effect-free.

The README also overstates leakage protection: it claims a gap buffer and detection of derived lookahead features, while the code performs only column-name keyword matching and adjacent chronological slicing without a purge/gap/embargo interval.

**Audit metrics:** Module folders: 2 | Files: 13 Python (+1 README) | Public symbols: 149 package exports | Symbols with confirmed callers: 66 (44.3%; test/example callers only) | Workflows found: 8

**Evidence confidence:** High for file contents, signatures, internal call paths, unit-test/example usage, and identified hard-coded behavior. Medium-to-low for repository-wide non-usage because full code search was unavailable.

## 3. Actual Package Structure

```text
Package: app.services.research
├── README.md
├── __init__.py
│   └── 149 re-exported public names from research modules and app.utils.settings
├── data.py
│   ├── CanonicalOHLCVSSchema
│   ├── DatasetIssue
│   ├── CleaningAction
│   ├── DataQualityReportModel
│   ├── PreparedDataset
│   ├── validate_dataset()
│   ├── enrich_dataset()
│   ├── prepare_research_dataset()
│   ├── CoreMetricProfile
│   ├── build_core_metric_profile()
│   ├── build_market_structure_profile()
│   └── run_seasonality()
├── errors.py
│   ├── ErrorPayload
│   ├── ResearchError
│   ├── ResearchValidationError
│   ├── RESEARCH_ERROR_CODES
│   ├── ERROR_MESSAGES
│   └── to_research_error_payload()
├── features.py
│   ├── log_returns()
│   ├── simple_returns()
│   ├── zscore()
│   ├── percent_rank()
│   ├── rolling_percentile_rank()
│   ├── atr()
│   ├── atr_percent()
│   ├── bollinger_bands()
│   ├── bb_width()
│   ├── bb_percent_b()
│   ├── rsi()
│   ├── rate_of_change()
│   ├── momentum()
│   ├── donchian_channel()
│   ├── hurst_exponent()
│   ├── rolling_hurst()
│   ├── pivot_points()
│   ├── adr()
│   ├── forward_returns()
│   ├── forward_max_favorable_excursion()
│   ├── forward_max_adverse_excursion()
│   ├── detect_volatility_regime()
│   ├── detect_trend_regime()
│   ├── active_sessions_for_hour()
│   ├── session_label_for_hour()
│   ├── calculate_regime_features()
│   ├── build_market_regime_feature_frame()
│   └── detect_market_regime()
├── helpers.py
│   ├── parse_calendar_events()
│   ├── parse_sentiment_snapshot()
│   ├── filter_events_by_symbol()
│   ├── classify_news_impact()
│   ├── create_news_blackout_windows()
│   ├── calculate_returns()
│   ├── calculate_volatility()
│   ├── calculate_atr()
│   ├── calculate_adr()
│   ├── calculate_spread_statistics()
│   ├── calculate_session_statistics()
│   ├── calculate_seasonality_statistics()
│   ├── calculate_correlation_matrix()
│   ├── check_sample_size()
│   ├── check_lookahead_bias_risk()
│   ├── check_hypothesis_testability()
│   ├── check_contradictory_evidence()
│   ├── run_session_breakout_strategy()
│   ├── run_session_fade_strategy()
│   ├── calmar_ratio()
│   ├── expectancy()
│   ├── max_drawdown()
│   ├── median_mae_mfe()
│   ├── profit_factor()
│   ├── sharpe_ratio()
│   ├── sortino_ratio()
│   ├── win_rate()
│   └── ResearchResourceLimits
│       └── check_limits()
├── leakage.py
│   ├── LeakageReport
│   ├── LeakageCheckResult
│   ├── validate_no_lookahead_features()
│   ├── validate_no_lookahead()
│   ├── detect_feature_leakage()
│   ├── mask_forward_columns()
│   ├── TimeSplitResult
│   │   └── to_dict()
│   ├── enforce_time_split()
│   ├── mask_research_artifact()
│   └── dump_masked_research_json()
├── metrics.py
│   ├── MetricValue
│   │   └── to_dict()
│   ├── MetricContext
│   ├── MetricCalculator
│   │   └── calculate()
│   ├── ReturnsCalculator.calculate()
│   ├── RocCalculator.calculate()
│   ├── CandlesCalculator.calculate()
│   ├── RangesCalculator.calculate()
│   ├── VolatilityCalculator.calculate()
│   ├── SpreadCalculator.calculate()
│   ├── VolumeActivityCalculator.calculate()
│   ├── MetricRegistry
│   │   ├── register()
│   │   └── calculate_all()
│   └── build_default_registry()
├── reporting.py
│   ├── result_to_markdown()
│   ├── result_to_summary()
│   ├── save_markdown()
│   ├── save_json()
│   ├── generate_multi_symbol_report()
│   ├── build_edge_profile_snapshot()
│   ├── build_profile_summary()
│   ├── build_dashboard_summary()
│   ├── save_json_report()
│   ├── save_markdown_report()
│   └── build_edge_lab_scorecard_report()
└── studies
    ├── __init__.py
    │   └── __all__ = []
    ├── eds.py
    │   ├── run_eds_null_baseline()
    │   ├── run_eds_mean_reversion()
    │   └── run_eds_trend_persistence()
    ├── null_models.py
    │   ├── compute_null_percentile()
    │   ├── compare_to_null()
    │   ├── get_acceptance_criteria()
    │   ├── block_bootstrap_distribution()
    │   ├── block_bootstrap_ci()
    │   ├── permutation_test()
    │   ├── random_entry_null()
    │   ├── r_space_null()
    │   ├── session_randomized_null()
    │   ├── shuffle_returns_null()
    │   ├── benjamini_hochberg()
    │   ├── holm_bonferroni()
    │   └── null_distribution_stats()
    ├── structure.py
    │   ├── TrendSwingPoint
    │   ├── TrendLeg
    │   ├── TrendScoreRow
    │   ├── MarketStructureProfile
    │   ├── MarketStructureCalibrationCandidate
    │   ├── MarketStructureMetricCalibrationCandidate
    │   ├── ClassificationResult
    │   ├── detect_swing_points()
    │   ├── classify_with_candidate()
    │   ├── build_calibration_grid()
    │   ├── evaluate_calibration_candidates()
    │   ├── build_metric_calibration_grid()
    │   ├── evaluate_metric_calibration_candidates()
    │   ├── evaluate_profile_calibration()
    │   ├── timeframe_bucket()
    │   ├── symbol_class()
    │   ├── resolve_market_structure_profile()
    │   ├── resolve_market_structure_profile_overrides()
    │   ├── confidence_bucket()
    │   ├── label_realized_market_behavior()
    │   ├── build_validation_summary()
    │   ├── build_market_structure_stability_report()
    │   ├── build_strategy_fit()
    │   ├── parse_news_items()
    │   ├── generate_research_hypothesis()
    │   └── build_research_evidence_pack()
    └── unsupervised.py
        ├── UnsupervisedResearchRequest
        ├── UnsupervisedResearchResult
        ├── run_pca()
        ├── cluster_feature_space()
        ├── attach_cluster_labels()
        ├── identify_pca_risk_factors()
        ├── compute_forward_returns()
        ├── analyze_cluster_outperformance()
        ├── adapt_signals_by_cluster()
        └── build_unsupervised_insight_report()
```

### Public facade observations

* `app/services/research/__init__.py` re-exports 149 names.
* Sixteen exported configuration/result symbols are owned by `app/utils/settings.py`, not by the research package: `BootstrapConfig`, `CleaningConfig`, `DataConfig`, `EdgeLabConfig`, `EdgeResult`, `EdgeStats`, `MarketStructureConfig`, `MeanReversionConfig`, `NullModelsConfig`, `PermutationConfig`, `SessionConfig`, `SessionEdgeConfig`, `TradeSample`, `TrendPersistenceConfig`, `create_config`, and `research_modeling_module`.
* Several public module symbols are not exported by the package facade, including `DatasetIssue`, `CleaningAction`, `DataQualityReportModel`, `CoreMetricProfile`, `build_core_metric_profile`, `build_market_structure_profile`, `run_seasonality`, `ResearchResourceLimits`, `LeakageReport`, `LeakageCheckResult`, `TimeSplitResult`, `MetricValue`, `MetricContext`, `ResearchError`, `ResearchValidationError`, `RESEARCH_ERROR_CODES`, `ERROR_MESSAGES`, and `to_research_error_payload`.
* `app/services/research/studies/__init__.py` exports nothing, even though the root package re-exports study functions directly.

## 4. Module and File Inventory

Files are ordered from foundational contracts and preparation through computations, studies, and reporting.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `research` | `errors.py` | Research-specific exceptions and redacted error payload mapping | `ResearchError`, `ResearchValidationError`, `to_research_error_payload` | Stdlib: `typing`<br>Third-party: none<br>Local: `app.utils.logger.logger`, `app.utils.security.redact_text` | Unknown; exception classes are used internally, mapper has no confirmed caller | Supporting / Questionable |
| `research` | `data.py` | Validate, clean, enrich, and package OHLCV(S) data; build profile wrappers | `prepare_research_dataset`, `validate_dataset`, `enrich_dataset`, models | Stdlib: `typing`<br>Third-party: NumPy, pandas, Pydantic<br>Local: research errors/metrics/structure/helpers, logger, settings | Test-only | Essential / Useful |
| `research` | `features.py` | Technical features, forward labels, excursions, sessions, and rule-based regimes | 28 functions | Stdlib: none<br>Third-party: NumPy, pandas<br>Local: research validation error | Test-only | Useful |
| `research` | `helpers.py` | Mixed parsing, statistics, validity checks, advisory strategy placeholders, performance metrics, row limits | 27 functions, `ResearchResourceLimits` | Stdlib: `typing`<br>Third-party: NumPy, pandas<br>Local: research errors/leakage | Test-only for a small subset; remainder Unknown | Mixed Useful / Questionable |
| `research` | `leakage.py` | Name-based lookahead detection, masking, chronological slicing, artifact redaction | leakage models/functions, `TimeSplitResult` | Stdlib: `json`, `typing`<br>Third-party: NumPy, pandas, Pydantic<br>Local: research errors, security redaction | Test-only | Useful but Partial |
| `research` | `metrics.py` | Registry-driven descriptive metrics over a prepared frame | calculator classes, registry | Stdlib: `typing`<br>Third-party: NumPy; pandas/settings under `TYPE_CHECKING`<br>Local: none at runtime | Test-only | Useful |
| `research.studies` | `null_models.py` | Bootstrap, permutation tests, multiple-testing corrections, null generators | 13 functions | Stdlib: `typing`<br>Third-party: NumPy, pandas<br>Local: none | Test-only for 5 functions; remainder Unknown | Useful / Questionable |
| `research.studies` | `eds.py` | Mean-reversion, trend-persistence, and null-baseline studies | `run_eds_*` | Stdlib: `datetime`, `typing`, deferred `math`<br>Third-party: NumPy<br>Local: research data/features/helpers/null models, settings models | Test-only | Essential / Useful; baseline Partial |
| `research.studies` | `structure.py` | Swing detection, calibration data models, profile classification, evidence packaging | models and 20 functions | Stdlib: `datetime`, `typing`<br>Third-party: pandas, Pydantic<br>Local: none | Test-only for 4 functions; remainder Unknown | Useful core plus Questionable placeholders |
| `research.studies` | `unsupervised.py` | Optional PCA/K-Means, cluster analysis, advisory recommendations | request/result models and 8 functions | Stdlib: `datetime`, `typing`<br>Third-party: NumPy, pandas, Pydantic, optional scikit-learn<br>Local: research errors | Test-only; conditional on sklearn | Useful but Unverified operational dependency |
| `research` | `reporting.py` | Serialize results/snapshots and persist Markdown/JSON files | 11 functions | Stdlib: `json`, `pathlib`, `typing`<br>Third-party: none<br>Local: research errors, logger, security, settings `EdgeResult` | Test-only | Useful |
| `research.studies` | `__init__.py` | Namespace marker | Empty `__all__` | Stdlib: future annotations | No direct caller | Supporting / No demonstrated behavior |
| `research` | `__init__.py` | Root public facade | 149 re-exports | Stdlib: future annotations<br>Third-party: none directly<br>Local: all research modules plus `app.utils.settings` | Test-only via usage example | Supporting / Questionable breadth |
| `research` | `README.md` | Documents intended package responsibilities | N/A | N/A | Documentation | Questionable accuracy |

## 5. Public Behaviour Inventory

### `research/errors.py`

**File responsibility:** Define research exceptions and map exceptions to redacted boundary payloads.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ErrorPayload` | `TypedDict` | Shape `{code, details}` | N/A | None | None | Type use only | None found | Unknown | Supporting |
| `ResearchError` | Exception class | Base research-domain exception with `.code` | `message`, optional `code` → exception instance | Local state mutation | None in constructor | Parent of `ResearchValidationError` | Indirect through raised subclass | Possibly used | Supporting |
| `ResearchValidationError` | Exception class | Validation/service failure used throughout research | `message`, optional `code` → exception instance | Local state mutation | None in constructor | `data.py`, `features.py`, `helpers.py`, `leakage.py`, `reporting.py`, `unsupervised.py` | Caught/asserted in unit tests | Test-only externally | Essential |
| `RESEARCH_ERROR_CODES` | Constant | Declared approved code subset | N/A | None | None | No confirmed reader | None found | Unknown | Questionable |
| `ERROR_MESSAGES` | Constant | Maps declared codes to public messages | N/A | None | None | No confirmed reader | None found | Unknown | Questionable |
| `to_research_error_payload()` | Function | Convert exception to redacted `{code, details}` and log mapping | `BaseException`, optional request id → `ErrorPayload` | Event/log publication | Security/logger failures are not handled | No confirmed caller | None found | Unknown | Questionable |

**Evidence:** `app/services/research/errors.py:17-95`.

### `research/data.py`

**File responsibility:** Prepare canonical in-memory research datasets and provide thin profile wrappers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `CanonicalOHLCVSSchema` | Mutable set constant | Names expected OHLCV(S) fields | N/A | None unless mutated by caller | None | No confirmed reader | None | Unknown | Questionable; not an enforcing schema |
| `DatasetIssue` | Pydantic model | Represent validation issue | fields → model | Local state mutation | Pydantic validation errors | `validate_dataset()` | Indirect | Test-only internally | Supporting |
| `CleaningAction` | Pydantic model | Represent cleaning action | fields → model | Local state mutation | Pydantic validation errors | `prepare_research_dataset()` | Indirect | Test-only internally | Supporting |
| `DataQualityReportModel` | Pydantic model | Collect issues/actions | fields → model | Local state mutation | Pydantic validation errors | validation/preparation | Indirect | Test-only internally | Supporting |
| `PreparedDataset` | Class | Carry frame, report, metadata | DataFrame, report, dict → object | Local state mutation | None explicit | EDS, data profile builders, tests/examples | Direct | Test-only | Essential |
| `validate_dataset()` | Function | Validate OHLC presence, monotonic/unique index, OHLC consistency, volume/spread signs | DataFrame → report | Read-only; logging on fatal errors | `ResearchValidationError` for missing OHLC, non-monotonic or duplicate index; raw `KeyError` possible for malformed frames | `prepare_research_dataset()`, unit tests | Direct | Test-only | Essential |
| `enrich_dataset()` | Function | Add returns, calendar, and candle geometry to a copy | DataFrame → enriched DataFrame | None to caller; local copy mutation | Raw `KeyError`/numeric errors | `prepare_research_dataset()`, unit tests | Direct | Test-only | Essential |
| `prepare_research_dataset()` | Function | Copy, timezone-normalize, clean missing values, cap spread, validate, enrich, package metadata | DataFrame, optional `EdgeLabConfig` → `PreparedDataset` | None to input; logging through validation | Research validation plus raw pandas errors | Unit test and examples; calls `validate_dataset`, `enrich_dataset` | Direct | Test-only | Essential |
| `CoreMetricProfile` | Pydantic model | Hold normalized metric dictionary, warnings, metadata | fields → model | Local state mutation | Pydantic validation errors | `build_core_metric_profile()` | None | Unknown | Supporting |
| `build_core_metric_profile()` | Function | Run default metric registry over a prepared dataset | `PreparedDataset` → `CoreMetricProfile` | None | Raw metric/data errors | No external caller confirmed | None | Unknown | Useful |
| `build_market_structure_profile()` | Function | Resolve a profile from dataset metadata | `PreparedDataset` → profile | None | Import/model errors | No external caller confirmed | None | Unknown | Questionable because resolver is hard-coded |
| `run_seasonality()` | Function | Delegate to seasonality statistics helper | DataFrame, optional filters → dict | None | Raw helper/data errors | No external caller confirmed | None | Unknown | Useful |

**Evidence:** `app/services/research/data.py:22-354`.

### `research/features.py`

**File responsibility:** Calculate indicators, future research labels, excursions, sessions, and simple regimes.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `log_returns()` | Function | Log price returns | close series → series | None | Numeric/pandas errors | Unit test, usage example | Direct | Test-only | Useful |
| `simple_returns()` | Function | Arithmetic returns | close series → series | None | Pandas errors | Unit test | Direct | Test-only | Useful |
| `zscore()` | Function | Rolling price z-score | series, window → series | None | `ResearchValidationError` if window ≤ 0 | EDS mean-reversion, unit test | Direct/indirect | Test-only | Essential |
| `percent_rank()` | Function | Rolling percentile rank | series, window → series | None | `ResearchValidationError` if window ≤ 0 | volatility regime, unit test | Direct/indirect | Test-only | Useful |
| `rolling_percentile_rank()` | Function | Alias wrapper over `percent_rank` | series, window → series | None | Propagates validation error | Unit test | Direct | Test-only | Questionable wrapper |
| `atr()` | Function | Average true range | high, low, close, window → series | None | `ResearchValidationError` if window ≤ 0 | trend EDS, volatility regime, unit test | Direct/indirect | Test-only | Essential |
| `atr_percent()` | Function | ATR divided by close | series inputs, window → series | None | Propagates ATR errors | regime feature frame, unit test | Direct/indirect | Test-only | Useful |
| `bollinger_bands()` | Function | Rolling upper/middle/lower bands | close, window, std multiplier → tuple of series | None | Validation error if window ≤ 0 | BB helpers, unit test | Direct/indirect | Test-only | Useful |
| `bb_width()` | Function | Relative Bollinger width | close/config → series | None | Propagates errors | Unit test | Direct | Test-only | Useful |
| `bb_percent_b()` | Function | Bollinger percent-B | close/config → series | None | Propagates errors | Unit test | Direct | Test-only | Useful |
| `rsi()` | Function | Simple rolling RSI | close, window → series | None | Validation error if window ≤ 0 | regime features, unit test | Direct/indirect | Test-only | Useful |
| `rate_of_change()` | Function | Price ROC | close, window → series | None | Validation error if window ≤ 0 | regime features, unit test | Direct/indirect | Test-only | Useful |
| `momentum()` | Function | Price difference momentum | close, window → series | None | Validation error if window ≤ 0 | Unit test | Direct | Test-only | Useful |
| `donchian_channel()` | Function | Rolling upper/lower breakout levels | high, low, window → tuple | None | Validation error if window ≤ 0 | Unit test | Direct | Test-only | Useful |
| `hurst_exponent()` | Function | Estimate Hurst exponent using rescaled-range approximation | series → float | None | Numeric errors for invalid positive-price assumptions | rolling Hurst, unit test/example | Direct/indirect | Test-only | Useful |
| `rolling_hurst()` | Function | Apply Hurst calculation over rolling windows | series, window → series | None | Validation error if window ≤ 0 | Unit test | Direct | Test-only | Useful but potentially expensive |
| `pivot_points()` | Function | Standard pivot/support/resistance series | high, low, close → dict | None | Pandas alignment/errors | Unit test | Direct | Test-only | Useful |
| `adr()` | Function | Rolling average high-low range | high, low, window → series | None | Validation error if window ≤ 0 | Unit test | Direct | Test-only | Useful |
| `forward_returns()` | Function | Future log-return label named `research_forward_returns` | close, horizon → series | None | Validation error if horizon ≤ 0 | Unit test and leakage example | Direct | Test-only | Essential for supervised research labels |
| `forward_max_favorable_excursion()` | Function | Loop-based future favorable excursion label | close, high, horizon → series | None | Validation error if horizon ≤ 0; indexing errors | Unit test and usage example | Direct | Test-only | Useful |
| `forward_max_adverse_excursion()` | Function | Loop-based future adverse excursion label | close, low, horizon → series | None | Validation error if horizon ≤ 0; indexing errors | Unit test and usage example | Direct | Test-only | Useful |
| `detect_volatility_regime()` | Function | Label high/low volatility from ATR percentile | DataFrame/config → series | None to input | Missing-column and validation errors | Unit test and usage example | Direct | Test-only | Useful |
| `detect_trend_regime()` | Function | Label bullish/bearish/sideways by dual rolling means | DataFrame/windows → series | None to input | Missing-column errors | Unit test and usage example | Direct | Test-only | Useful |
| `active_sessions_for_hour()` | Function | Return London/New York/Tokyo sessions for integer hour | hour → list[str] | None | None explicit | `session_label_for_hour`, unit test | Direct/indirect | Test-only | Useful |
| `session_label_for_hour()` | Function | Join active session labels or return `Asian_Quiet` | hour → str | None | None explicit | Unit test and usage example | Direct | Test-only | Useful |
| `calculate_regime_features()` | Function | Add ATR%, RSI, z-score, ROC columns | DataFrame → copied DataFrame | None to input; local copy mutation | Missing-column/validation errors | feature frame and market regime | Indirect only | Test-only internally | Supporting |
| `build_market_regime_feature_frame()` | Function | Return non-null four-column feature matrix | DataFrame → DataFrame | None | Propagates feature errors | Unit test and usage example | Direct | Test-only | Essential for unsupervised workflow |
| `detect_market_regime()` | Function | Label `normal`, `overbought`, `oversold` using RSI only | DataFrame → series | None | Propagates feature errors | Unit test | Direct | Test-only | Useful but name overstates scope |

**Evidence:** `app/services/research/features.py:18-359`.

### `research/helpers.py`

**File responsibility:** A mixed collection of parsers, statistics, checks, placeholders, and resource limits.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `parse_calendar_events()` | Function | Normalize economic-calendar dictionaries | list[dict] → list[dict] | None | Conversion errors are possible | Unit test | Direct | Test-only | Useful |
| `parse_sentiment_snapshot()` | Function | Normalize sentiment-positioning records | list[dict] → list[dict] | None | `ValueError`/`TypeError` on nonnumeric fields | No caller confirmed | None | Unknown | Useful |
| `filter_events_by_symbol()` | Function | Filter events by first/last three symbol characters | events, symbol → list | None | None explicit | No caller confirmed | None | Unknown | Useful but FX-specific |
| `classify_news_impact()` | Function | Normalize impact labels | string → `high`/`medium`/`low` | None | Attribute error for non-string | blackout-window helper | Indirect | Test-only internally | Supporting |
| `create_news_blackout_windows()` | Function | Build advisory windows for high-impact events | events, before/after minutes → list[dict] | None | Swallows all per-event exceptions | Unit test | Direct | Test-only | Useful but silently lossy |
| `calculate_returns()` | Function | Arithmetic returns | close series → series | None | Pandas errors | No caller confirmed | None | Unknown | Useful; duplicates `simple_returns` |
| `calculate_volatility()` | Function | Rolling annualized volatility with fixed √252 | returns, window → series | None | Pandas errors | No caller confirmed | None | Unknown | Useful with timeframe caveat |
| `calculate_atr()` | Function | Average true range | high, low, close, window → series | None | Pandas errors; no window validation | No caller confirmed | None | Unknown | Questionable duplicate of `features.atr` |
| `calculate_adr()` | Function | Average high-low range | high, low, window → series | None | Pandas errors; no window validation | No caller confirmed | None | Unknown | Questionable duplicate of `features.adr` |
| `calculate_spread_statistics()` | Function | Spread mean/std/min/max/p95 | series → dict | None | Pandas numeric errors | No caller confirmed | None | Unknown | Useful |
| `calculate_session_statistics()` | Function | Summary statistics over `returns` column | DataFrame → dict | None | Missing-column error | No caller confirmed | None | Unknown | Useful |
| `calculate_seasonality_statistics()` | Function | Mean returns grouped by day/hour after optional equality filters | DataFrame, filters → dict | None to input | Grouping/conversion errors | `data.run_seasonality()` | No direct test | Unknown | Useful |
| `calculate_correlation_matrix()` | Function | Correlate close series across frames by positional index | list[DataFrame] → DataFrame | None | Missing-column errors | No caller confirmed | None | Unknown | Useful with alignment caveat |
| `check_sample_size()` | Function | Fail when sample count below minimum | integers → `True` | None | `ResearchValidationError` with undeclared code `ERR_INSUFFICIENT_SAMPLES` | EDS functions, unit test | Direct/indirect | Test-only | Essential |
| `check_lookahead_bias_risk()` | Function | Return whether name-based leakage report is critical | DataFrame → bool | None | Leakage errors | No caller confirmed | None | Unknown | Questionable naming/semantics |
| `check_hypothesis_testability()` | Function | Return whether frame has at least 30 rows | DataFrame → bool | None | None explicit | No caller confirmed | None | Unknown | Questionable fixed threshold |
| `check_contradictory_evidence()` | Function | Treat negative mean return as contradiction | DataFrame → bool | None | Numeric errors | No caller confirmed | None | Unknown | Questionable domain assumption |
| `run_session_breakout_strategy()` | Function | Return fixed advisory metrics; uses input only for sample size | DataFrame/hours → dict | None | None explicit | No caller confirmed | None | Unknown | No demonstrated analytical value |
| `run_session_fade_strategy()` | Function | Return fixed advisory metrics; uses input only for sample size | DataFrame/hours → dict | None | None explicit | No caller confirmed | None | Unknown | No demonstrated analytical value |
| `calmar_ratio()` | Function | Annualized return divided by positive max drawdown input | floats → float | None | None explicit | No caller confirmed | None | Unknown | Useful with sign-convention ambiguity |
| `expectancy()` | Function | Weighted win/loss result | win rate, avg win/loss → float | None | None explicit | No caller confirmed | None | Unknown | Useful |
| `max_drawdown()` | Function | Minimum percentage drawdown from running max | equity series → float | None | Divide-by-zero/numeric issues possible | No caller confirmed | None | Unknown | Useful |
| `median_mae_mfe()` | Function | Median `mae` and `mfe` keys | list[dict] → dict | None | Numeric conversion issues | No caller confirmed | None | Unknown | Useful |
| `profit_factor()` | Function | Gross positive R divided by absolute negative R | trades → float | None | Missing `r_multiple` key | No caller confirmed | None | Unknown | Useful |
| `sharpe_ratio()` | Function | Mean/std × √252 | returns, risk-free rate → float | None | Numeric errors | No caller confirmed | None | Unknown | Useful with timeframe/risk-free-period caveat |
| `sortino_ratio()` | Function | Mean/downside std × √252 | returns, risk-free rate → float | None | Numeric errors | No caller confirmed | None | Unknown | Useful with timeframe caveat |
| `win_rate()` | Function | Fraction of positive `r_multiple` trades | trades → float | None | Missing-key errors | No caller confirmed | None | Unknown | Useful |
| `ResearchResourceLimits` | Class | Store duration, memory, and row limits | limits → object | Local state mutation | None in constructor | Unit test constructs it | Direct | Test-only | Questionable: only row limit is enforced |
| `ResearchResourceLimits.check_limits()` | Method | Reject row count above maximum | row count → `None` | None | `ResearchValidationError` with undeclared code `ERR_RESOURCE_LIMIT` | Unit test | Direct | Test-only | Useful but incomplete |

**Evidence:** `app/services/research/helpers.py:20-358`.

### `research/leakage.py`

**File responsibility:** Detect suspicious names, mask columns/artifacts, and create chronological slices.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `LeakageReport` | Pydantic model | Represent suspected columns and evidence | fields → model | Local state mutation | Pydantic validation errors | leakage functions/tests | Indirect | Test-only internally | Supporting |
| `LeakageCheckResult` | Alias | Alias of `LeakageReport` | N/A | None | None | No caller confirmed | None | Unknown | Questionable duplicate name |
| `validate_no_lookahead_features()` | Function | Flag column names containing five keywords | DataFrame, allow-list, target → report | Read-only | None explicit | tests/example; helper wrapper | Direct | Test-only | Useful as lint only; not true leakage validation |
| `validate_no_lookahead()` | Function | Pass-through wrapper | same inputs → report | Read-only | Propagates | No caller confirmed | None | Unknown | No additional value |
| `detect_feature_leakage()` | Function | Pass-through wrapper | same inputs → report | Read-only | Propagates | No caller confirmed | None | Unknown | No additional value |
| `mask_forward_columns()` | Function | Drop suspected columns from a copy | DataFrame, report → DataFrame | None to input | Pandas errors | unit test/example | Direct | Test-only | Useful |
| `TimeSplitResult` | Class | Hold train/validation/test frames and counts | three frames → object | Local state mutation | None explicit | `enforce_time_split`, tests/example | Direct/indirect | Test-only | Supporting |
| `TimeSplitResult.to_dict()` | Method | Return split counts | none → dict | None | None | No caller confirmed | None | Unknown | Supporting |
| `enforce_time_split()` | Function | Sort index and slice adjacent partitions by proportions | DataFrame and three percentages → `TimeSplitResult` | None to input | Validation error only if sum not close to 1; other invalid values may produce odd slices | unit test/example | Direct | Test-only | Useful but incomplete |
| `mask_research_artifact()` | Function | Delegate recursive sensitive-field redaction | dict → dict | None | Security helper errors | unit test; JSON dump | Direct/indirect | Test-only | Useful |
| `dump_masked_research_json()` | Function | Redact then JSON-serialize supported custom objects | dict → JSON string | None | JSON serialization errors | unit test | Direct | Test-only | Useful |

**Evidence:** `app/services/research/leakage.py:23-214`.

### `research/metrics.py`

**File responsibility:** Provide a small registry and seven descriptive metric calculators.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `MetricValue` | Class | Hold scalar value and metadata | float, optional dict → object | Local state mutation | None explicit | all calculators | Indirect | Test-only internally | Supporting |
| `MetricValue.to_dict()` | Method | Serialize metric value | none → dict | None | None | `build_core_metric_profile()` | No direct test | Unknown | Supporting |
| `MetricContext` | Class | Hold DataFrame and research config | frame/config → object | Local state mutation | None explicit | calculators/tests | Direct | Test-only | Supporting |
| `MetricCalculator` | Base class | Define calculator interface | context → `MetricValue` | None | `NotImplementedError` | inherited by seven calculators | None direct | Supporting | Supporting |
| `ReturnsCalculator.calculate()` | Method | Mean return plus std/skew/kurt/count | context → metric | Read-only | Missing-column errors | default registry | Indirect | Test-only | Useful |
| `RocCalculator.calculate()` | Method | Mean 10-bar ROC plus std/count | context → metric | Read-only | Missing-column errors | default registry | Indirect | Test-only | Useful |
| `CandlesCalculator.calculate()` | Method | Mean body and shadows | context → metric | Read-only | Missing shadow-column errors | default registry | Indirect | Test-only | Useful |
| `RangesCalculator.calculate()` | Method | Mean/max/min high-low range | context → metric | Read-only | Missing-column errors | default registry | Indirect | Test-only | Useful |
| `VolatilityCalculator.calculate()` | Method | Return std × √252 | context → metric | Read-only | Missing-column errors | default registry | Indirect | Test-only | Useful with timeframe caveat |
| `SpreadCalculator.calculate()` | Method | Mean/max/min spread | context → metric | Read-only | Empty spread may yield NaN | default registry | Indirect | Test-only | Useful |
| `VolumeActivityCalculator.calculate()` | Method | Mean/max/min volume | context → metric | Read-only | Empty volume may yield NaN | default registry | Indirect | Test-only | Useful |
| `MetricRegistry` | Class | Store named calculators | none → object | Local state mutation | None | data profile builder/tests | Direct/indirect | Test-only | Supporting |
| `MetricRegistry.register()` | Method | Insert/replace calculator by name | name/calculator → `None` | Local state mutation | None; silently overwrites | `build_default_registry()` | Indirect | Test-only internally | Supporting |
| `MetricRegistry.calculate_all()` | Method | Execute all registered calculators | context → dict | Read-only over registry/context | Propagates calculator errors | data profile builder/unit test | Direct/indirect | Test-only | Essential |
| `build_default_registry()` | Function | Register seven standard calculators | none → registry | Local state mutation on new instance | None explicit | unit test/data profile builder | Direct | Test-only | Essential |

**Evidence:** `app/services/research/metrics.py:22-188`.

### `research/reporting.py`

**File responsibility:** Convert results to summaries/reports and perform local file writes.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `result_to_markdown()` | Function | Render one `EdgeResult` as Markdown with redaction | result → string | None | JSON/model errors | unit test/example; `save_markdown` | Direct | Test-only | Essential |
| `result_to_summary()` | Function | Extract concise scalar summary | result → dict | None | Attribute errors | unit test/example; snapshot builder | Direct | Test-only | Essential |
| `save_markdown()` | Function | Render and atomically write Markdown | result/path/overwrite → bool | Persistence write | `ResearchValidationError` for `..`; filesystem errors | unit test/example | Direct | Test-only | Useful |
| `save_json()` | Function | Redact and atomically write JSON | result/path/overwrite → bool | Persistence write | Validation/filesystem/JSON errors | unit test/example | Direct | Test-only | Useful |
| `generate_multi_symbol_report()` | Function | Render comparison table | results → Markdown string | None | Attribute errors | No caller confirmed | None | Unknown | Useful |
| `build_edge_profile_snapshot()` | Function | Build schema-versioned list of result summaries | symbol/timeframe/results → dict | None | Result conversion errors | unit test/example; scorecard builder | Direct | Test-only | Useful but contains fixed timestamp |
| `build_profile_summary()` | Function | Aggregate average win rate/expectancy | snapshot → dict | None | Missing-key/type/division errors | unit test/example; dashboard/scorecard | Direct | Test-only | Useful |
| `build_dashboard_summary()` | Function | Add UI display type to profile summary | snapshot → dict | Local mutation of newly created summary | Propagates | unit test/example | Direct | Test-only | Supporting |
| `save_json_report()` | Function | Redact/write snapshot JSON | snapshot/path/overwrite → bool | Persistence write | Validation/filesystem/JSON errors | No caller confirmed | None | Unknown | Useful |
| `save_markdown_report()` | Function | Render/write snapshot Markdown | snapshot/path/overwrite → bool | Persistence write | Key/format/filesystem errors | No caller confirmed | None | Unknown | Useful |
| `build_edge_lab_scorecard_report()` | Function | Compose snapshot, summary, disclaimer | symbol/timeframe/results → dict | None | Propagates | No caller confirmed | None | Unknown | Useful |

**Evidence:** `app/services/research/reporting.py:22-219`. Private `_safe_write()` at lines 75-97 creates directories, writes a shared `.tmp` path, and replaces the target.

### `research/studies/eds.py`

**File responsibility:** Run two actual rule-based edge studies and one nominal null baseline.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `run_eds_null_baseline()` | Function | Shuffle returns 500 times and report mean/std/quantiles | prepared dataset/config → dict | Nondeterministic computation controlled by seed | Sample-size validation; missing-data errors | unit test/example | Direct | Test-only | Questionable due invariant shuffled mean |
| `run_eds_mean_reversion()` | Function | Generate z-score fade trades and summary statistics | prepared dataset/config → `EdgeResult` | Reads current UTC time | Sample-size, missing-column/index/model errors | unit test/example | Direct | Test-only | Essential |
| `run_eds_trend_persistence()` | Function | Generate ATR breakout follow-through trades and statistics | prepared dataset/config → `EdgeResult` | Reads current UTC time | Sample-size, missing-column/index/model errors | unit test/example | Direct | Test-only | Essential |

**Evidence:** `app/services/research/studies/eds.py:26-248`.

### `research/studies/null_models.py`

**File responsibility:** Statistical resampling, null generators, and multiple-testing corrections.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `compute_null_percentile()` | Function | Percentile of observed statistic | scalar/distribution → float | None | Numeric conversion errors | `compare_to_null` | None direct | Unknown | Useful |
| `compare_to_null()` | Function | One-sided empirical comparison and significance flag | scalar/distribution → dict | None | Empty array produces NaN/warnings rather than explicit failure | No external caller confirmed | None | Unknown | Useful but incomplete |
| `get_acceptance_criteria()` | Function | Lower/upper percentile cutoffs | distribution/alpha → dict | None | Empty/invalid percentile errors | No caller confirmed | None | Unknown | Useful |
| `block_bootstrap_distribution()` | Function | Block-resample and calculate sample means | data/config → ndarray | Nondeterministic computation controlled by seed | Numeric errors; invalid iterations | unit test and CI helper | Direct/indirect | Test-only | Useful |
| `block_bootstrap_ci()` | Function | Percentile confidence interval over bootstrap means | data/config → tuple | Nondeterministic computation controlled by seed | Propagates bootstrap/percentile errors | unit test/example | Direct | Test-only | Useful |
| `permutation_test()` | Function | Two-sided empirical difference-in-means p-value | two groups/config → float | Nondeterministic computation controlled by seed | Empty/nonnumeric input problems | unit test/example | Direct | Test-only | Useful |
| `random_entry_null()` | Function | Sample 30 random entry horizons repeatedly | DataFrame/config → ndarray | Nondeterministic computation controlled by seed | Missing data generally returns zeros; indexing/numeric errors possible | No caller confirmed | None | Unknown | Useful but hard-coded sample size |
| `r_space_null()` | Function | Coin-flip ±1R mean distribution | counts/config → ndarray | Nondeterministic computation controlled by seed | Invalid sizes | No caller confirmed | None | Unknown | Useful |
| `session_randomized_null()` | Function | Shuffle returns within hour groups, then calculate total mean | DataFrame/config → ndarray | Nondeterministic computation controlled by seed | Data/index errors | No caller confirmed | None | Unknown | Questionable: within-group shuffle also preserves overall mean |
| `shuffle_returns_null()` | Function | Shuffle all returns, then calculate mean | DataFrame/config → ndarray | Nondeterministic ordering only | Missing input returns zeros | EDS null baseline | Indirect | Test-only | No meaningful null variance for mean statistic |
| `benjamini_hochberg()` | Function | FDR rejection flags | p-values/alpha → list[bool] | None | Invalid values not checked | unit test/example | Direct | Test-only | Useful |
| `holm_bonferroni()` | Function | Step-down familywise rejection flags | p-values/alpha → list[bool] | None | Invalid values not checked | unit test/example | Direct | Test-only | Useful |
| `null_distribution_stats()` | Function | Summary statistics | distribution → dict | None | Numeric errors | No caller confirmed | None | Unknown | Useful |

**Evidence:** `app/services/research/studies/null_models.py:18-270`.

### `research/studies/structure.py`

**File responsibility:** Define market-structure data models, detect swing points, and expose a mixture of calculations and placeholders.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `TrendSwingPoint` | Pydantic model | Swing timestamp/price/type | fields → model | Local state mutation | Pydantic errors | swing detector/profile | Indirect | Test-only internally | Supporting |
| `TrendLeg` | Pydantic model | Directional leg between swings | fields → model | Local state mutation | Pydantic errors | classifier/profile | Indirect | Test-only internally | Supporting |
| `TrendScoreRow` | Pydantic model | Timestamped trend score | fields → model | Local state mutation | Pydantic errors | No caller confirmed | None | Unknown | No demonstrated value |
| `MarketStructureProfile` | Pydantic model | Symbol/timeframe/regime and detected structure | fields → model | Local state mutation | Pydantic errors | classifier/resolvers/data wrapper | Indirect | Test-only internally | Supporting |
| `MarketStructureCalibrationCandidate` | Pydantic model | Swing-window/threshold candidate and score | fields → model | Local state mutation | Pydantic errors | grid/evaluator | Direct/indirect | Test-only | Supporting |
| `MarketStructureMetricCalibrationCandidate` | Pydantic model | Metric/parameter candidate and fit score | fields → model | Local state mutation | Pydantic errors | metric grid/evaluator | None | Unknown | Supporting |
| `ClassificationResult` | Pydantic model | Edge class/confidence/timestamp | fields → model | Local state mutation | Pydantic errors | No caller confirmed | None | Unknown | No demonstrated value |
| `detect_swing_points()` | Function | Detect strict local highs/lows | DataFrame/window → list | Read-only | Missing-column/index errors; invalid window not validated | unit test/example; classifier | Direct | Test-only | Useful |
| `classify_with_candidate()` | Function | Build legs and classify directional ratio | DataFrame/candidate → profile | Read-only | Data/model errors | candidate evaluator | Indirect | Test-only | Questionable: hard-coded symbol/timeframe |
| `build_calibration_grid()` | Function | Cartesian product of windows/thresholds | lists → candidates | None | Pydantic errors | unit test/example | Direct | Test-only | Useful |
| `evaluate_calibration_candidates()` | Function | Score candidates by number of detected legs | DataFrame/candidates → sorted candidates | Mutates candidate `.score` | Data/model errors | unit test/example | Direct | Test-only | Useful but weak objective |
| `build_metric_calibration_grid()` | Function | Cartesian metric/parameter grid | lists → candidates | None | Pydantic errors | No caller confirmed | None | Unknown | Useful |
| `evaluate_metric_calibration_candidates()` | Function | Set `100/(1+parameter)` as fit score | DataFrame/candidates → list | Mutates candidate `.fit_score` | Division/model errors | No caller confirmed | None | Unknown | No demonstrated evidence-based value |
| `evaluate_profile_calibration()` | Function | Return 90% of existing calibration score | profile/validation frame → float | None | None explicit | No caller confirmed | None | Unknown | No demonstrated evidence-based value |
| `timeframe_bucket()` | Function | Map timeframe into three labels | string → string | None | Attribute error on non-string | No caller confirmed | None | Unknown | Useful |
| `symbol_class()` | Function | Label any symbol containing USD as major, otherwise cross | string → string | None | Attribute error on non-string | No caller confirmed | None | Unknown | Questionable oversimplification |
| `resolve_market_structure_profile()` | Function | Return fixed trending/high profile | symbol/timeframe → profile | None | Pydantic errors | data wrapper/override resolver | No direct test | Unknown | No demonstrated analytical value |
| `resolve_market_structure_profile_overrides()` | Function | Change confidence to fixed `high_override` | symbol/timeframe/profile class → profile | Local model mutation | Pydantic errors | No caller confirmed | None | Unknown | No demonstrated value; ignores `profile_class` |
| `confidence_bucket()` | Function | Map score to high/medium/low | float → string | None | Comparison errors | No caller confirmed | None | Unknown | Useful |
| `label_realized_market_behavior()` | Function | Classify future mean return as trend/reversion/mixed | DataFrame → string | Read-only | Missing-column/numeric errors | No caller confirmed | None | Unknown | Useful but simplistic |
| `build_validation_summary()` | Function | Mean high/low and row count | DataFrame → dict | Read-only | Missing-column/numeric errors | No caller confirmed | None | Unknown | Useful |
| `build_market_structure_stability_report()` | Function | Return fixed stability/variance plus window count | DataFrame/count → dict | None | None explicit | No caller confirmed | None | Unknown | No demonstrated analytical value |
| `build_strategy_fit()` | Function | Return fixed advisory fit result | DataFrame → dict | None | None explicit | unit test/example | Direct | Test-only | No demonstrated analytical value |
| `parse_news_items()` | Function | Normalize news records | list[dict] → list[dict] | None | Conversion errors possible | No caller confirmed | None | Unknown | Useful |
| `generate_research_hypothesis()` | Function | Package description/evidence/testability/time | string/list → dict | Reads current UTC time | None explicit | No caller confirmed | None | Unknown | Useful |
| `build_research_evidence_pack()` | Function | Package symbol/timeframe/hypothesis/statistics | inputs → dict | None | None explicit | No caller confirmed | None | Unknown | Useful |

**Evidence:** `app/services/research/studies/structure.py:19-383`.

### `research/studies/unsupervised.py`

**File responsibility:** Optional dimensionality reduction, clustering, cluster outcome analysis, and advisory reporting.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `UnsupervisedResearchRequest` | Pydantic model | Model feature columns/components/clusters/seed | fields → model | Local state mutation | Pydantic errors | No caller confirmed | None | Unknown | Questionable; orchestration does not consume it |
| `UnsupervisedResearchResult` | Pydantic model | Model variance/centers/silhouette/metadata | fields → model | Local state mutation | Pydantic errors | No caller confirmed | None | Unknown | Questionable; functions return dicts instead |
| `run_pca()` | Function | Standardize numeric complete rows, fit PCA, return variance/loadings | DataFrame/components → dict | CPU computation | Research validation for insufficient data/missing sklearn; sklearn errors | unit test/example | Direct | Test-only | Useful |
| `cluster_feature_space()` | Function | Standardize numeric complete rows, fit K-Means | DataFrame/clusters/seed → dict | CPU computation | Research validation for insufficient data/missing sklearn; sklearn errors | unit test/example | Direct | Test-only | Useful |
| `attach_cluster_labels()` | Function | Add labels to copied frame | DataFrame/labels → DataFrame | None to input; local copy mutation | Length mismatch errors | unit test/example | Direct | Test-only | Supporting |
| `identify_pca_risk_factors()` | Function | Select largest absolute loading per component | PCA dict/columns → list[dict] | None | Empty/misaligned inputs can raise | unit test | Direct | Test-only | Useful |
| `compute_forward_returns()` | Function | Future log returns | close/horizon → series | None | Research validation if horizon ≤ 0 | No caller confirmed | None | Unknown | Questionable duplicate of `features.forward_returns` |
| `analyze_cluster_outperformance()` | Function | Attach labels, aggregate forward returns, assign semantic regime | DataFrame/labels/column → dict | None to input; local copy mutation | Research validation if column missing; length/data errors | usage example | Direct | Test-only | Useful |
| `adapt_signals_by_cluster()` | Function | Return advisory maintain/reduce recommendations | cluster stats → dict | Reads current UTC time | Missing-key/type errors | usage example | Direct | Test-only | Useful advisory output |
| `build_unsupervised_insight_report()` | Function | Package PCA variance and cluster centers | symbol/timeframe/results → dict | Reads current UTC time | None explicit | No caller confirmed | None | Unknown | Useful |

**Evidence:** `app/services/research/studies/unsupervised.py:21-229`.

### `research/__init__.py` and shared settings re-exports

**File responsibility:** Expose a flat package API. The facade contains no wrappers; imported objects are re-exported directly.

| Re-export source | Public symbols | Usage evidence | Status | Value observation |
| ---------------- | -------------- | -------------- | ------ | ----------------- |
| `research.data` | `CanonicalOHLCVSSchema`, `PreparedDataset`, `enrich_dataset`, `prepare_research_dataset`, `validate_dataset` | `PreparedDataset`, `enrich_dataset`, `prepare_research_dataset`, `validate_dataset` used in unit tests; `prepare_research_dataset` in usage example | Test-only | Useful; facade omits several data publics |
| `research.features` | `active_sessions_for_hour`, `adr`, `atr`, `atr_percent`, `bb_percent_b`, `bb_width`, `bollinger_bands`, `build_market_regime_feature_frame`, `calculate_regime_features`, `detect_market_regime`, `detect_trend_regime`, `detect_volatility_regime`, `donchian_channel`, `forward_max_adverse_excursion`, `forward_max_favorable_excursion`, `forward_returns`, `hurst_exponent`, `log_returns`, `momentum`, `percent_rank`, `pivot_points`, `rate_of_change`, `rolling_hurst`, `rolling_percentile_rank`, `rsi`, `session_label_for_hour`, `simple_returns`, `zscore` | 27/28 have unit-test or example evidence; `calculate_regime_features` is internally called | Test-only | Broad but functional |
| `research.helpers` | `calculate_adr`, `calculate_atr`, `calculate_correlation_matrix`, `calculate_returns`, `calculate_seasonality_statistics`, `calculate_session_statistics`, `calculate_spread_statistics`, `calculate_volatility`, `calmar_ratio`, `check_sample_size`, `create_news_blackout_windows`, `expectancy`, `max_drawdown`, `median_mae_mfe`, `parse_calendar_events`, `parse_sentiment_snapshot`, `profit_factor`, `run_session_breakout_strategy`, `run_session_fade_strategy`, `sharpe_ratio`, `sortino_ratio`, `win_rate` | Only `check_sample_size`, `create_news_blackout_windows`, `parse_calendar_events` confirmed externally; others Unknown | Mixed | Duplicates and placeholders inflate surface |
| `research.leakage` | `dump_masked_research_json`, `enforce_time_split`, `mask_forward_columns`, `mask_research_artifact`, `validate_no_lookahead_features` | All unit-tested; three used in example | Test-only | Useful but weaker than naming/docs imply |
| `research.metrics` | `CandlesCalculator`, `MetricCalculator`, `MetricRegistry`, `RangesCalculator`, `ReturnsCalculator`, `RocCalculator`, `SpreadCalculator`, `VolatilityCalculator`, `VolumeActivityCalculator`, `build_default_registry` | Registry directly tested; calculators exercised indirectly | Test-only | Useful |
| `research.reporting` | `build_dashboard_summary`, `build_edge_lab_scorecard_report`, `build_edge_profile_snapshot`, `build_profile_summary`, `generate_multi_symbol_report`, `result_to_markdown`, `result_to_summary`, `save_json`, `save_json_report`, `save_markdown`, `save_markdown_report` | Seven confirmed in tests/examples; four Unknown | Test-only / Unknown | Useful with fixed timestamp issue |
| `research.studies.eds` | `run_eds_mean_reversion`, `run_eds_null_baseline`, `run_eds_trend_persistence` | All unit-tested and demonstrated | Test-only | Two meaningful, one statistically flawed |
| `research.studies.null_models` | `benjamini_hochberg`, `block_bootstrap_ci`, `block_bootstrap_distribution`, `compare_to_null`, `compute_null_percentile`, `get_acceptance_criteria`, `holm_bonferroni`, `null_distribution_stats`, `permutation_test`, `r_space_null`, `random_entry_null`, `session_randomized_null`, `shuffle_returns_null` | Five directly tested/exampled; shuffle called by EDS | Test-only / Unknown | Mixed |
| `research.studies.structure` | `ClassificationResult`, `MarketStructureCalibrationCandidate`, `MarketStructureMetricCalibrationCandidate`, `MarketStructureProfile`, `TrendLeg`, `TrendScoreRow`, `TrendSwingPoint`, `build_calibration_grid`, `build_market_structure_stability_report`, `build_metric_calibration_grid`, `build_research_evidence_pack`, `build_strategy_fit`, `build_validation_summary`, `classify_with_candidate`, `confidence_bucket`, `detect_swing_points`, `evaluate_calibration_candidates`, `evaluate_metric_calibration_candidates`, `evaluate_profile_calibration`, `generate_research_hypothesis`, `label_realized_market_behavior`, `parse_news_items`, `resolve_market_structure_profile`, `resolve_market_structure_profile_overrides`, `symbol_class`, `timeframe_bucket` | Four functions confirmed in tests/example; internal model/classifier calls | Test-only / Unknown | Many placeholders |
| `research.studies.unsupervised` | `UnsupervisedResearchRequest`, `UnsupervisedResearchResult`, `adapt_signals_by_cluster`, `analyze_cluster_outperformance`, `attach_cluster_labels`, `build_unsupervised_insight_report`, `cluster_feature_space`, `compute_forward_returns`, `identify_pca_risk_factors`, `run_pca` | Six functions confirmed; models/report/duplicate forward function Unknown | Test-only / Unknown | Useful core, inconsistent result contracts |
| `app.utils.settings` | `BootstrapConfig`, `CleaningConfig`, `DataConfig`, `EdgeLabConfig`, `EdgeResult`, `EdgeStats`, `MarketStructureConfig`, `MeanReversionConfig`, `NullModelsConfig`, `PermutationConfig`, `SessionConfig`, `SessionEdgeConfig`, `TradeSample`, `TrendPersistenceConfig`, `create_config`, `research_modeling_module` | `EdgeLabConfig`, `EdgeResult`, `EdgeStats`, `TradeSample` used internally/tests; `research_modeling_module()` is a dynamic string import of unsupervised module | Test-only / Possibly used dynamically | Cross-package ownership and import side effect |

**Evidence:** `app/services/research/__init__.py:12-360`; `app/utils/settings.py` research configuration section and `research_modeling_module()`.

## 6. Actual Workflows

### `V1-WF-RESEARCH-001` — Prepare and Validate a Research Dataset

* **Scope:** Internal
* **Trigger:** Caller supplies an in-memory OHLCV(S) `DataFrame` and optional `EdgeLabConfig`.
* **Input boundary:** Python call to `prepare_research_dataset()`; no data-service adapter is present.
* **Functions and methods used:** `prepare_research_dataset()` → `validate_dataset()` → `enrich_dataset()` → `PreparedDataset`.
* **Files involved:** `data.py`; configuration models from `app/utils/settings.py`; logger and research errors.
* **External dependencies:** pandas, NumPy, Pydantic.
* **Output boundary:** `PreparedDataset` containing copied/enriched frame, quality report, and symbol/timeframe/row metadata.
* **Failure behaviour:** Fails on missing core OHLC fields, non-monotonic index, duplicate timestamps, or raw pandas errors. Warning-level OHLC, volume, and spread issues do not block output.
* **Operational status:** Working in unit test and usage example; production integration Unverified.
* **Evidence:** `data.py:64-309`; `tests/research/unit/test_research.py::test_prepare_research_dataset`; `tests/research/usage/12_research.py::example_01_research_config_and_data_prep`.

```text
In-memory OHLCV(S) DataFrame
→ prepare_research_dataset()
→ timezone/missing/spread cleaning
→ validate_dataset()
→ enrich_dataset()
→ PreparedDataset
```

### `V1-WF-RESEARCH-002` — Engineer Technical and Regime Features

* **Scope:** Internal
* **Trigger:** Caller supplies price series or OHLC frame.
* **Input boundary:** Individual feature functions or `build_market_regime_feature_frame()`.
* **Functions and methods used:** Indicator functions; for unsupervised feature frame: `calculate_regime_features()` → `atr_percent()`, `rsi()`, `zscore()`, `rate_of_change()`.
* **Files involved:** `features.py`.
* **External dependencies:** pandas, NumPy.
* **Output boundary:** Series, tuples, dictionaries, or non-null feature frame.
* **Failure behaviour:** Several functions validate positive windows/horizons; missing columns and invalid numeric data raise raw pandas/NumPy errors.
* **Operational status:** Working in unit tests and usage example; production integration Unverified.
* **Evidence:** `features.py`; `test_technical_features`, `test_regime_features`; usage `example_02_feature_engineering`.

```text
OHLC series/frame
→ indicator or regime function
→ timestamp-aligned Series/DataFrame
→ downstream edge or clustering study
```

### `V1-WF-RESEARCH-003` — Build Forward Labels, Check Names, Mask, and Split

* **Scope:** Internal
* **Trigger:** Researcher creates future labels for supervised analysis.
* **Input boundary:** Price series and feature frame.
* **Functions and methods used:** `forward_returns()` / MFE / MAE → `validate_no_lookahead_features()` → `mask_forward_columns()` → `enforce_time_split()`.
* **Files involved:** `features.py`, `leakage.py`.
* **External dependencies:** pandas, NumPy, Pydantic.
* **Output boundary:** Masked frame and adjacent train/validation/test frames.
* **Failure behaviour:** Invalid horizon or split-sum raises research validation error. The detector can miss leakage whose column name lacks a keyword, and can flag legitimate columns merely because of a name.
* **Operational status:** Partial. Demonstrated, but not equivalent to the README's claimed derivation-aware detector or gap-buffer split.
* **Evidence:** `features.py:230-273`; `leakage.py:39-193`; `test_leakage_checks`, `test_time_split`; usage `example_03_leakage_controls`.

```text
Prepared prices
→ forward labels
→ name-based leakage report
→ drop flagged columns
→ sort and adjacent percentage slices
→ train / validation / test
```

### `V1-WF-RESEARCH-004` — Execute Edge Discovery Studies

* **Scope:** Internal
* **Trigger:** Caller has `PreparedDataset` and `EdgeLabConfig`.
* **Input boundary:** `run_eds_null_baseline()`, `run_eds_mean_reversion()`, or `run_eds_trend_persistence()`.
* **Functions and methods used:** sample-size check; z-score or ATR calculations; loop-based trade extraction; private statistics calculation; optional shuffle baseline.
* **Files involved:** `studies/eds.py`, `features.py`, `helpers.py`, `studies/null_models.py`, shared settings models.
* **External dependencies:** NumPy.
* **Output boundary:** `EdgeResult` for mean reversion/trend, or baseline dictionary.
* **Failure behaviour:** Insufficient total rows fail closed; trade sample may still be small and only generate a warning. Missing columns/index assumptions raise raw errors.
* **Operational status:** Partial. Mean-reversion and trend studies calculate from data; null baseline does not generate meaningful mean-statistic variation.
* **Evidence:** `studies/eds.py`; unit `test_eds_studies`; usage `example_04_edge_studies`.

```text
PreparedDataset + EdgeLabConfig
→ check_sample_size()
→ z-score fade OR ATR breakout rule
→ TradeSample list
→ EdgeStats
→ EdgeResult
```

### `V1-WF-RESEARCH-005` — Run Statistical Validation

* **Scope:** Internal
* **Trigger:** Researcher supplies return samples or p-values.
* **Input boundary:** Bootstrap, permutation, and correction functions.
* **Functions and methods used:** `block_bootstrap_distribution()` → `block_bootstrap_ci()`; `permutation_test()`; `benjamini_hochberg()`; `holm_bonferroni()`.
* **Files involved:** `studies/null_models.py`.
* **External dependencies:** NumPy, pandas.
* **Output boundary:** ndarray, confidence interval, p-value, or rejection flags.
* **Failure behaviour:** Input validation is minimal; empty or malformed arrays can return zero distributions, NaNs, warnings, or raw exceptions depending on function.
* **Operational status:** Working for demonstrated nonempty inputs; broader null-generator suite Partial/Unverified.
* **Evidence:** `null_models.py`; unit `test_null_models`; usage `example_05_statistical_validation`.

```text
Returns / groups / p-values
→ bootstrap or permutation
→ confidence interval / p-value
→ multiple-comparison correction
→ rejection decisions
```

### `V1-WF-RESEARCH-006` — Detect and Calibrate Market Structure

* **Scope:** Internal
* **Trigger:** Researcher supplies OHLC frame and candidate parameters.
* **Input boundary:** `detect_swing_points()`, grid builder, evaluator.
* **Functions and methods used:** `build_calibration_grid()` → `evaluate_calibration_candidates()` → `classify_with_candidate()` → `detect_swing_points()`; optionally `build_strategy_fit()`.
* **Files involved:** `studies/structure.py`.
* **External dependencies:** pandas, Pydantic.
* **Output boundary:** Ranked candidate models, profile, or advisory fit dictionary.
* **Failure behaviour:** Invalid windows/columns are not explicitly validated. Several outputs are fixed or ignore supplied evidence.
* **Operational status:** Partial. Swing detection and candidate iteration work; strategy fit, profile resolution, metric calibration, stability, and override behavior are placeholders.
* **Evidence:** `structure.py`; unit `test_structure_studies`; usage `example_06_market_structure`.

```text
OHLC frame + parameter lists
→ calibration grid
→ swing detection per candidate
→ leg count score
→ sorted candidates
→ fixed advisory strategy-fit output
```

### `V1-WF-RESEARCH-007` — Run Optional PCA and Cluster Analysis

* **Scope:** Internal
* **Trigger:** Researcher builds a non-null numeric feature frame.
* **Input boundary:** `run_pca()` and `cluster_feature_space()`.
* **Functions and methods used:** feature-frame builder → StandardScaler/PCA/KMeans → labels → `attach_cluster_labels()` → forward-return aggregation → `adapt_signals_by_cluster()`.
* **Files involved:** `features.py`, `studies/unsupervised.py`.
* **External dependencies:** scikit-learn (optional but not declared in project dependencies), pandas, NumPy.
* **Output boundary:** Dictionaries containing variance/loadings/centers/labels and advisory recommendations.
* **Failure behaviour:** Missing sklearn or insufficient rows raises `ResearchValidationError`; sklearn/data errors otherwise propagate. The usage script catches shared `app.utils.standard.ValidationError`, not the independent `ResearchValidationError`, so its intended graceful skip does not catch the package's missing-sklearn error.
* **Operational status:** Partial/Unverified. Unit test conditionally passes if sklearn exists, but dependency installation is not guaranteed by `pyproject.toml`.
* **Evidence:** `unsupervised.py`; unit `test_unsupervised`; usage `example_07_unsupervised_analysis`; `pyproject.toml` dependencies.

```text
OHLC frame
→ build_market_regime_feature_frame()
→ PCA and K-Means
→ labels attached
→ forward returns aggregated by cluster
→ advisory exposure recommendations
```

### `V1-WF-RESEARCH-008` — Build and Persist Research Reports

* **Scope:** Internal; local filesystem boundary
* **Trigger:** Edge study returns an `EdgeResult`.
* **Input boundary:** Result conversion, snapshot builder, or save function.
* **Functions and methods used:** `result_to_markdown()` / `result_to_summary()` → snapshot/profile/dashboard builders → `_safe_write()` via save functions.
* **Files involved:** `reporting.py`; redaction helper from `app.utils.security`.
* **External dependencies:** local filesystem.
* **Output boundary:** Markdown/JSON string, dict payload, or files written to supplied path.
* **Failure behaviour:** Explicit `..` path components rejected; existing file with `overwrite=False` returns `False`; other filesystem errors are logged and re-raised. Absolute paths and paths outside an application root are allowed.
* **Operational status:** Working in temporary-path unit test and usage example; production consumer Unverified.
* **Evidence:** `reporting.py`; unit `test_reporting`; usage `example_08_research_reports`.

```text
EdgeResult
→ redacted Markdown / summary
→ profile snapshot / dashboard summary
→ optional temp-file write and replace
→ local report artifact
```

## 7. Usage and Caller Map

No production/runtime caller was confirmed. The table groups symbols sharing identical or closely related caller evidence; all named symbols were checked in the accessible test, usage, internal-import, and facade evidence.

| Public symbol | Called from | Call type | Runtime or test | Evidence |
| ------------- | ----------- | --------- | --------------- | -------- |
| `prepare_research_dataset` | `test_prepare_research_dataset`, `test_eds_studies`, `test_reporting`, examples 1/4/8 | Direct | Test/example | Test and usage files |
| `validate_dataset`, `enrich_dataset` | Unit tests; `prepare_research_dataset` | Direct + internal | Test/example | `data.py`, unit test |
| `PreparedDataset` | Unit assertion; EDS type boundary | Instantiation/type | Test/example | `data.py`, `eds.py`, unit test |
| `log_returns`, `simple_returns`, `zscore`, `percent_rank`, `rolling_percentile_rank`, `atr`, `atr_percent`, `bollinger_bands`, `bb_width`, `bb_percent_b`, `rsi`, `rate_of_change`, `momentum`, `donchian_channel`, `hurst_exponent`, `rolling_hurst`, `pivot_points`, `adr` | `test_technical_features`; selected functions in example 2; `zscore`/`atr` internal to EDS | Direct/internal | Test/example | Unit and usage files; `eds.py` |
| `forward_returns`, `forward_max_favorable_excursion`, `forward_max_adverse_excursion` | `test_forward_features`, example 3 | Direct | Test/example | Unit and usage files |
| `detect_volatility_regime`, `detect_trend_regime`, `build_market_regime_feature_frame`, `detect_market_regime` | `test_regime_features`; selected functions examples 2/7 | Direct | Test/example | Unit and usage files |
| `active_sessions_for_hour`, `session_label_for_hour` | Unit `test_sessions`; example 2 | Direct/internal | Test/example | Unit and usage files |
| `calculate_regime_features` | feature-frame and market-regime builders | Internal | Test/example path | `features.py` |
| `parse_calendar_events`, `create_news_blackout_windows`, `check_sample_size`, `ResearchResourceLimits.check_limits` | Unit `test_helpers`; `check_sample_size` in EDS | Direct/internal | Test/example | Unit test; `eds.py` |
| Other helper functions | No confirmed caller in accessible evidence | None found | Unknown | Package facade and source only |
| `validate_no_lookahead_features`, `mask_forward_columns`, `enforce_time_split` | unit leakage/split tests; example 3 | Direct | Test/example | Unit and usage files |
| `mask_research_artifact`, `dump_masked_research_json` | unit artifact test; dump calls mask | Direct/internal | Test | Unit test; `leakage.py` |
| `validate_no_lookahead`, `detect_feature_leakage`, `TimeSplitResult.to_dict` | No confirmed external caller | None found | Unknown | Source only |
| `build_default_registry`, `MetricContext`, `MetricRegistry.calculate_all` | unit metric test; data core-profile wrapper | Direct/internal | Test | Unit test; `data.py` |
| Calculator classes and `.calculate()` methods | Instantiated/registered by `build_default_registry`, executed by `calculate_all` | Registry dispatch | Test | `metrics.py`, unit test |
| `run_eds_null_baseline`, `run_eds_mean_reversion`, `run_eds_trend_persistence` | unit EDS test; example 4; mean-reversion also reporting workflow | Direct | Test/example | Unit and usage files |
| `block_bootstrap_distribution`, `block_bootstrap_ci`, `permutation_test`, `benjamini_hochberg`, `holm_bonferroni` | unit null-model test; example 5 | Direct | Test/example | Unit and usage files |
| `shuffle_returns_null` | `run_eds_null_baseline` | Internal | Test/example path | `eds.py` |
| Other null-model functions | No confirmed caller | None found | Unknown | Source/facade only |
| `detect_swing_points`, `build_calibration_grid`, `evaluate_calibration_candidates`, `build_strategy_fit` | unit structure test; example 6 | Direct | Test/example | Unit and usage files |
| `classify_with_candidate` | `evaluate_calibration_candidates` | Internal | Test/example path | `structure.py` |
| Other structure models/functions | Internal model construction or no confirmed caller | Internal/none | Test path / Unknown | `structure.py` |
| `run_pca`, `cluster_feature_space`, `attach_cluster_labels`, `identify_pca_risk_factors` | unit unsupervised test; first three in example 7 | Direct | Test/example | Unit and usage files |
| `analyze_cluster_outperformance`, `adapt_signals_by_cluster` | example 7 | Direct | Example | Usage file |
| Other unsupervised models/functions | No confirmed caller | None found | Unknown | Source/facade only |
| `result_to_markdown`, `result_to_summary`, `save_markdown`, `save_json`, `build_edge_profile_snapshot`, `build_profile_summary`, `build_dashboard_summary` | unit reporting test; example 8 | Direct/internal | Test/example | Unit and usage files |
| Other reporting functions | No confirmed caller | None found | Unknown | Source/facade only |
| `EdgeLabConfig` | unit tests and usage examples | Construction | Test/example | Test and usage files |
| `EdgeResult`, `EdgeStats`, `TradeSample` | EDS implementation and reporting type boundary | Construction/type | Test/example path | `eds.py`, `reporting.py` |
| `research_modeling_module` | No direct caller; dynamically imports string `app.services.research.studies.unsupervised` when invoked | Dynamic string import | Possibly used | `app/utils/settings.py` |
| Root package exports used by usage script | `tests/research/usage/12_research.py` imports 36 names from `app.services.research` | Package import | Example | Usage file lines 23-60 |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --------------------------- | -------------------------------- | ------------------------- | -------- |
| `app.utils.settings` | Research configs, trade/result models, dynamic module resolver | root facade, `data.py`, `metrics.py` typing, `eds.py`, `reporting.py` | `__init__.py`, settings research section |
| `app.utils.logger` | Error/warning logging | `data.py`, `errors.py`, `reporting.py` | imports and calls |
| `app.utils.security` | `redact_text`, `redact_mapping` | `errors.py`, `leakage.py`, `reporting.py` | imports and calls |
| `app.services.research` internal modules | Data, features, helpers, metrics, leakage, studies | deferred and direct internal imports | source call paths |
| pandas | DataFrame/Series operations, time conversion, grouping, rolling windows | all computational modules except errors/reporting | imports |
| NumPy | statistics, RNG, vector operations | data/features/helpers/leakage/metrics/studies | imports |
| Pydantic | domain/config/result models | data/leakage/structure/unsupervised; shared settings | imports |
| scikit-learn | StandardScaler, PCA, KMeans | `studies/unsupervised.py` | deferred imports inside functions |
| Local filesystem | directory creation, temp writes, atomic replace | `reporting.py` save functions | `_safe_write()` |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| `tests/research/unit/test_research.py` | 66 imports/called or indirectly exercised symbols, including data prep, features, leakage, metrics, EDS, null models, structure, unsupervised, reporting | Unit coverage | Current test file |
| `tests/research/usage/12_research.py` | 36 root-facade exports | Eight executable examples | Current usage file |
| `app.utils.settings.research_modeling_module()` | Dynamic import of `app.services.research.studies.unsupervised` | Resolve modeling module by string | `settings.py` |
| Production services/routes/agents/schedulers | No confirmed consumption | Unknown | Full repository grep unavailable; no accessible caller evidence |

### Boundary assessment

* The research domain does not fetch market data itself; callers must supply pandas objects.
* No broker, trading, live, risk, strategy, API, or agent-tool mutation is present in this package.
* Reporting performs local filesystem writes, so the package is not wholly read-only in the general side-effect sense; it is only non-mutating toward trading/broker state.
* The root facade imports shared settings definitions and therefore crosses into utility-owned configuration at import time.

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| `features.simple_returns()` | `helpers.calculate_returns()` | Both call `Series.pct_change()` | `features.py:23-25`; `helpers.py:111-113` | Divergent naming/public entry points |
| `features.atr()` | `helpers.calculate_atr()` | Same true-range and rolling mean formula | `features.py:61-71`; `helpers.py:121-132` | One validates window, one does not |
| `features.adr()` | `helpers.calculate_adr()` | Same rolling high-low mean | `features.py:223-227`; `helpers.py:135-137` | Duplicate maintenance surface |
| `features.forward_returns()` | `unsupervised.compute_forward_returns()` | Same future log-return formula | `features.py:230-236`; `unsupervised.py:145-149` | Different naming metadata; one sets series name |
| `validate_no_lookahead_features()` | `validate_no_lookahead()` | Exact wrapper | `leakage.py:39-103` | No added behavior |
| `validate_no_lookahead_features()` | `detect_feature_leakage()` | Exact wrapper | `leakage.py:39-116` | No added behavior |
| `LeakageReport` | `LeakageCheckResult` | Exact type alias | `leakage.py:23-36` | Duplicate public vocabulary |
| Metric calculations in `metrics.py` | helper statistics in `helpers.py` and features in `data.py` | Returns, volatility, ranges, spread, volume are calculated in multiple layers | files cited | Inconsistent formulas/contracts |
| `UnsupervisedResearchResult` | Dict returns from `run_pca()` / `cluster_feature_space()` | Model exists but implementation returns raw dicts | `unsupervised.py` | Contract fragmentation |
| Root `__init__.py` | Direct submodule imports in unit tests | Two public access styles | facade and unit imports | Public boundary is not consistently exercised |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| Production integration for entire package | Only unit and usage-example callers confirmed | Exact known files, package facade, initialization commit, commit comparison, attempted repository code search | Low | Search index unavailable; no accessible production caller |
| `to_research_error_payload`, `RESEARCH_ERROR_CODES`, `ERROR_MESSAGES` | Boundary mapping/constants have no confirmed caller | Domain imports, tests, usage, facade | Medium | Not re-exported or tested |
| `CanonicalOHLCVSSchema` | Mutable set named as schema but not used by validation | Domain source/test/usage | Medium | `validate_dataset` creates a separate `required` set |
| `run_session_breakout_strategy`, `run_session_fade_strategy` | Return fixed metrics, ignore price behavior and session arguments | Source, facade, tests, usage | Medium | `helpers.py:238-266` |
| `TrendScoreRow`, `ClassificationResult` | Defined and exported but no construction/caller found | Source/facade/tests/usage | Medium | `structure.py` |
| `evaluate_metric_calibration_candidates` | Ignores supplied DataFrame; score depends only on parameter value | Source and callers | Medium | `structure.py:221-231` |
| `evaluate_profile_calibration` | Ignores validation frame | Source and callers | Medium | `structure.py:234-239` |
| `resolve_market_structure_profile` | Always returns trending/high/1.0 profile | Source and callers | Medium | `structure.py:260-273` |
| `resolve_market_structure_profile_overrides` | Ignores `profile_class` | Source and callers | Medium | `structure.py:276-284` |
| `build_market_structure_stability_report` | Fixed 0.85/0.05 values | Source and callers | Medium | `structure.py:318-327` |
| `build_strategy_fit` | Fixed fit score/type; only status asserted by test | Source/test/usage | Medium | `structure.py:330-339` |
| `UnsupervisedResearchRequest`, `UnsupervisedResearchResult` | Public models not consumed by exposed computations | Source/facade/tests/usage | Medium | `unsupervised.py:21-37` |
| Many helper/performance functions | Public and exported but no confirmed caller | Source/facade/tests/usage | Medium | `helpers.py` |
| `studies/__init__.py` empty `__all__` | Namespace only; root facade bypasses it | Source/facade | Medium | `studies/__init__.py` |
| Shared config fields | `non_trading_period_strategy`, session config, permutation config, market structure config, and several bootstrap fields are not consumed by demonstrated main workflows | Settings plus domain call paths | Medium | `settings.py`, EDS/data source |

**Confidence note:** No row is labelled dead code. Medium means the known static evidence was checked, but unavailable repository-wide search prevents ruling out indirect external use.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Research data ingestion | No adapter from data service, files, database, broker, or API | Every workflow requires caller-created DataFrames; usage generates synthetic data | `data.py`; usage `_generate_synthetic_ohlcv()` |
| Leakage prevention | No provenance/AST/lag analysis and no purge/gap/embargo split | README safety claim is not met; false negatives and temporal overlap risk remain | README versus `leakage.py` |
| Null baseline | Shuffling observations then measuring mean preserves the statistic | Baseline standard deviation is effectively zero and comparison is not informative | `shuffle_returns_null`, `run_eds_null_baseline` |
| Session edge studies | Strategy functions do not use prices or session hours | Outputs appear analytical but are constants | `helpers.py` |
| Market-structure calibration | Several functions ignore evidence or return constants | Capability is partly a scaffold rather than operational calibration | `structure.py` |
| Unsupervised workflow | scikit-learn absent from declared dependencies; result models unused | Runtime availability and contract stability are uncertain | `pyproject.toml`, `unsupervised.py` |
| Research-to-strategy handoff | Recommendations are dictionaries only; no confirmed consumer | Advisory findings are disconnected from strategy lifecycle | caller search evidence |
| Research-to-UI/API handoff | Dashboard payload builder exists but no route/UI caller confirmed | Dashboard summary has no verified delivery path | `reporting.py`, caller search evidence |
| Official tool/error boundary | Error mapper exists but no research tool facade or caller confirmed | Errors remain inconsistent/raw at public calls | `errors.py`; no tool module |
| Report artifact lifecycle | Files are written to arbitrary supplied paths; no catalogue/index/retention consumer | Artifacts can exist without discoverability or ownership | `reporting.py` |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-RESEARCH-001` | No confirmed production caller | Entire package | Real system value is unproven beyond tests/examples | Only test and usage callers confirmed |
| `V1-ISSUE-RESEARCH-002` | Public facade is excessively broad | `research/__init__.py` | 149-name API increases coupling and obscures intended entry points | `__all__` lines 199-360 |
| `V1-ISSUE-RESEARCH-003` | Research facade re-exports utility-owned config/result types | `research/__init__.py`, `app/utils/settings.py` | Ownership is blurred; research imports shared runtime settings module | imports lines 179-197 |
| `V1-ISSUE-RESEARCH-004` | Side-effect-free import claim is false | `research/__init__.py` → `app/utils/settings.py` | Importing research executes `settings = Settings()`, reading environment and optional `.env` | research docstring/README versus settings module docstring and singleton |
| `V1-ISSUE-RESEARCH-005` | README overstates time-split leakage protection | README, `leakage.enforce_time_split` | No gap/purge/embargo despite explicit documentation | README line 40; `leakage.py:160-193` |
| `V1-ISSUE-RESEARCH-006` | Leakage detection is only a column-name heuristic | `validate_no_lookahead_features` | Cannot prove derivation safety; false positives/negatives | `leakage.py:61-80` |
| `V1-ISSUE-RESEARCH-007` | Null baseline statistic is invariant under shuffle | `shuffle_returns_null`, `run_eds_null_baseline` | Null distribution of means has no meaningful variance | `null_models.py:192-209`; `eds.py:36-50` |
| `V1-ISSUE-RESEARCH-008` | Placeholder strategy outputs live in production package | `run_session_breakout_strategy`, `run_session_fade_strategy` | Fixed metrics may be mistaken for measured performance | `helpers.py:238-266` |
| `V1-ISSUE-RESEARCH-009` | Placeholder market-structure outputs | Multiple functions in `structure.py` | Calibration/profile/fit/stability claims can mislead consumers | hard-coded values and unused inputs |
| `V1-ISSUE-RESEARCH-010` | Hard-coded report timestamp | `build_edge_profile_snapshot` | Every snapshot claims creation at `2026-06-19T16:44:44Z` | `reporting.py:142-146` |
| `V1-ISSUE-RESEARCH-011` | Direct dependencies are undeclared | `pyproject.toml` versus research imports | NumPy/pandas are relied on transitively; sklearn workflow may be unavailable | dependencies list lacks numpy/pandas/sklearn |
| `V1-ISSUE-RESEARCH-012` | Usage example catches the wrong validation hierarchy | `tests/research/usage/12_research.py`, `research/errors.py`, `app/utils/standard.py` | Missing sklearn raises `ResearchValidationError`, not shared `ValidationError`; graceful skip fails | independent exception bases |
| `V1-ISSUE-RESEARCH-013` | Error code registry is inconsistent with raised codes | `errors.py`, `helpers.py`, `reporting.py` | `ERR_INSUFFICIENT_SAMPLES`, `ERR_RESOURCE_LIMIT`, and `PERMISSION_DENIED` are not in declared research code set/messages | source codes |
| `V1-ISSUE-RESEARCH-014` | Error handling is inconsistent | Package-wide | Some paths raise research errors; others raw `KeyError`, pandas/sklearn/filesystem errors; one helper silently swallows exceptions | source behavior |
| `V1-ISSUE-RESEARCH-015` | `helpers.py` contains unrelated responsibilities | `helpers.py` | Parsers, indicators, validation, strategies, ratios, and limits are coupled | file sections 1-6 |
| `V1-ISSUE-RESEARCH-016` | Duplicate calculations have different validation/contracts | features/helpers/unsupervised | Results and failure behavior can diverge | duplicate table above |
| `V1-ISSUE-RESEARCH-017` | Result contract inconsistency | `unsupervised.py` | Pydantic request/result models exist, but public functions return untyped dicts | models versus function returns |
| `V1-ISSUE-RESEARCH-018` | Resource-limits class does not enforce declared duration or memory limits | `ResearchResourceLimits` | Names imply three enforced safeguards; only row count is checked | `helpers.py:338-358` |
| `V1-ISSUE-RESEARCH-019` | Spread cleaning implementation contradicts README wording | README, `prepare_research_dataset` | README says multiple of median; code caps at fixed configured absolute threshold | README line 31; `data.py:277-290` |
| `V1-ISSUE-RESEARCH-020` | Chronological split validation is incomplete | `enforce_time_split` | Negative or >1 components can pass if sum equals 1 and create invalid slices | only sum validation at lines 177-181 |
| `V1-ISSUE-RESEARCH-021` | Fixed √252 annualization is used without timeframe awareness | helpers/metrics | Hourly or intraday research is annualized as daily observations | volatility/Sharpe/Sortino implementations |
| `V1-ISSUE-RESEARCH-022` | Report path protection is incomplete | `reporting._safe_write` | Rejects explicit `..` only; absolute/out-of-root writes remain possible | `reporting.py:75-97` |
| `V1-ISSUE-RESEARCH-023` | Temporary report path is shared per target stem/suffix replacement | `reporting._safe_write` | Concurrent writers to same destination can collide on `.tmp` | `path.with_suffix(".tmp")` |
| `V1-ISSUE-RESEARCH-024` | Tests validate presence/shapes more than correctness | `tests/research/unit/test_research.py` | Hard-coded outputs and statistical semantics can pass without being correct | assertions mostly type/name/length/status |
| `V1-ISSUE-RESEARCH-025` | Package naming overstates some functions | `detect_market_regime`, `check_lookahead_bias_risk`, schema constant | Consumers may infer stronger behavior than implemented | implementations cited above |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-RESEARCH-001` | OHLC core validation | `data.validate_dataset` | WF-001 | Test-only | Essential | Fatal core/index checks; warnings for other quality issues |
| `V1-CAP-RESEARCH-002` | Dataset cleaning and timezone normalization | `data.prepare_research_dataset` | WF-001 | Test-only | Essential | Missing-value strategies and fixed spread cap |
| `V1-CAP-RESEARCH-003` | Dataset enrichment | `data.enrich_dataset` | WF-001 | Test-only | Essential | Returns, calendar, candle geometry |
| `V1-CAP-RESEARCH-004` | Technical indicators | `features.py` | WF-002 | Test-only | Useful | Broad indicator set |
| `V1-CAP-RESEARCH-005` | Forward-return and excursion labels | `features.forward_*` | WF-003 | Test-only | Useful | Explicit `research_` naming |
| `V1-CAP-RESEARCH-006` | Rule-based regime labels | feature regime functions | WF-002/007 | Test-only | Useful | ATR/MA/RSI based |
| `V1-CAP-RESEARCH-007` | Trading-session labels | `active_sessions_for_hour`, `session_label_for_hour` | WF-002 | Test-only | Useful | Fixed UTC-like hours; no timezone parameter |
| `V1-CAP-RESEARCH-008` | Lookahead-name linting | `validate_no_lookahead_features` | WF-003 | Test-only | Questionable | Not provenance-based validation |
| `V1-CAP-RESEARCH-009` | Forward-column masking | `mask_forward_columns` | WF-003 | Test-only | Useful | Drops reported names from copy |
| `V1-CAP-RESEARCH-010` | Chronological percentage split | `enforce_time_split` | WF-003 | Test-only | Useful | No gap/purge/embargo |
| `V1-CAP-RESEARCH-011` | Core metric registry | `metrics.py`, data profile wrapper | WF-001/002 | Test-only | Useful | Seven calculators |
| `V1-CAP-RESEARCH-012` | Mean-reversion edge study | `run_eds_mean_reversion` | WF-004 | Test-only | Essential | Z-score fade and future close exit |
| `V1-CAP-RESEARCH-013` | Trend-persistence edge study | `run_eds_trend_persistence` | WF-004 | Test-only | Essential | ATR breakout and follow-through |
| `V1-CAP-RESEARCH-014` | Null baseline for EDS | `run_eds_null_baseline`, `shuffle_returns_null` | WF-004 | Test-only | No demonstrated value | Statistic invariant under shuffle |
| `V1-CAP-RESEARCH-015` | Block bootstrap | `block_bootstrap_*` | WF-005 | Test-only | Useful | Mean statistic only |
| `V1-CAP-RESEARCH-016` | Permutation test | `permutation_test` | WF-005 | Test-only | Useful | Difference in means |
| `V1-CAP-RESEARCH-017` | Multiple-testing correction | BH and Holm-Bonferroni functions | WF-005 | Test-only | Useful | Minimal input validation |
| `V1-CAP-RESEARCH-018` | Other null generators | random-entry, R-space, session shuffle | WF-005 | Unknown | Questionable | Some untested; session mean invariant issue |
| `V1-CAP-RESEARCH-019` | Swing-point detection | `detect_swing_points` | WF-006 | Test-only | Useful | Strict local extrema |
| `V1-CAP-RESEARCH-020` | Market-structure candidate grid/evaluation | structure grid/evaluator | WF-006 | Test-only | Useful / Questionable | Objective is number of legs |
| `V1-CAP-RESEARCH-021` | Market-structure profile/stability/fit | structure resolvers/reports | WF-006 | Test-only / Unknown | No demonstrated value | Multiple constants/ignored inputs |
| `V1-CAP-RESEARCH-022` | PCA | `run_pca` | WF-007 | Test-only | Useful | Optional undeclared sklearn dependency |
| `V1-CAP-RESEARCH-023` | K-Means clustering | `cluster_feature_space` | WF-007 | Test-only | Useful | Optional undeclared sklearn dependency |
| `V1-CAP-RESEARCH-024` | Cluster outperformance analysis | `analyze_cluster_outperformance` | WF-007 | Example-only | Useful | Uses future returns by cluster |
| `V1-CAP-RESEARCH-025` | Advisory cluster recommendations | `adapt_signals_by_cluster` | WF-007 | Example-only | Useful | No strategy consumer confirmed |
| `V1-CAP-RESEARCH-026` | Economic-calendar normalization and blackout advice | helper parser/window functions | None standalone | Test-only | Useful | Invalid events silently skipped |
| `V1-CAP-RESEARCH-027` | Sentiment normalization | `parse_sentiment_snapshot` | None confirmed | Unknown | Useful | No caller |
| `V1-CAP-RESEARCH-028` | Session breakout/fade evaluation | fixed helper functions | None confirmed | Unknown | No demonstrated value | Hard-coded metrics |
| `V1-CAP-RESEARCH-029` | Performance ratios/statistics | helper metrics | None confirmed | Unknown | Useful | Duplicates analytics-like behavior; no caller |
| `V1-CAP-RESEARCH-030` | Research resource row limit | `ResearchResourceLimits.check_limits` | Helper test | Test-only | Supporting | Duration/memory fields not enforced |
| `V1-CAP-RESEARCH-031` | Artifact redaction | leakage/reporting security helpers | WF-003/008 | Test-only | Useful | Shared security dependency |
| `V1-CAP-RESEARCH-032` | Edge Markdown/JSON rendering | result converters | WF-008 | Test-only | Essential | Advisory disclaimer included |
| `V1-CAP-RESEARCH-033` | Local report persistence | save functions/private writer | WF-008 | Test-only | Useful | Filesystem write; incomplete path boundary |
| `V1-CAP-RESEARCH-034` | Profile/dashboard/scorecard payloads | reporting builders | WF-008 | Test-only / Unknown | Useful | Snapshot timestamp is fixed |
| `V1-CAP-RESEARCH-035` | Research error redaction boundary | `to_research_error_payload` | None confirmed | Unknown | Questionable | Not connected to official tools |
| `V1-CAP-RESEARCH-036` | Dynamic modeling module resolution | `research_modeling_module` | None confirmed | Possibly used | Supporting | String-imports unsupervised module |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The strongest V1 behavior is the in-memory research core: OHLC validation and enrichment, reusable indicator calculations, forward return/MAE/MFE labels, two actual edge-study implementations, bootstrap and permutation utilities, multiple-testing corrections, swing-point detection, optional PCA/K-Means, and report serialization. These functions have concrete implementations and are exercised by current unit tests or executable examples.

### Behaviour that exists but is disconnected

The whole domain is disconnected from confirmed production workflows. No caller from the data service, strategy service, optimization service, API, agentic tools, scheduler, UI, or runtime orchestration was found in accessible evidence. Dashboard summaries, evidence packs, profile resolvers, news/sentiment parsers, most performance helpers, and the official error mapper exist as callable APIs but have no confirmed consumer.

### Likely dead weight or placeholder behavior

Because repository-wide search was unavailable, nothing is declared dead code. However, several items have no demonstrated analytical value in their current implementation: fixed session strategy metrics, fixed market-structure stability and fit, the always-trending profile resolver, metric/profile calibration functions that ignore evidence, unused structure result models, and the invariant shuffled-mean null baseline. These should be treated as placeholders rather than working research evidence.

### Duplicated responsibilities

Returns, ATR, ADR, forward returns, and several metric concepts are implemented more than once with different names and validation behavior. Three leakage function names expose effectively one implementation. Unsupervised result models coexist with raw-dictionary return contracts. This creates ambiguity about the canonical API.

### Important uncertainties

The largest uncertainty is full repository usage. Exact files and known callers were inspected, but the repository code-search index was unavailable and the sandbox could not clone the repository. Dynamic use through string lookup, configuration, plugin discovery, or code outside the fetched evidence may exist. `research_modeling_module()` is one confirmed string-based dynamic reference.

### Manual confirmation required

1. Confirm whether any production route, agent tool, scheduler, notebook, or external application imports the research package.
2. Confirm whether NumPy, pandas, and scikit-learn are intentionally supplied transitively or by an external environment.
3. Confirm whether fixed strategy/profile outputs are deliberate demonstrations or unfinished production code.
4. Confirm whether the intended leakage split requires purge/gap/embargo behavior.
5. Confirm the intended owner of research configuration/result models currently stored in `app/utils/settings.py`.
6. Execute the complete unit and usage suites in the repository environment; this audit inspected tests but did not run them because the repository was not locally available.

### Final validation checklist

* Every Python file currently identified under `app/services/research/` is represented.
* The package README is represented and checked against implementation.
* Every root `__init__.py` export was inventoried by source group; all 149 names exist in its import surface.
* Public module-level symbols not re-exported by the root facade were identified.
* Current unit tests and usage examples were inspected.
* Internal call paths for all eight workflows were reconstructed from code.
* Test/example usage is separated from production usage.
* Inbound and outbound dependency surfaces are summarized.
* Dynamic string import through `research_modeling_module()` is recorded.
* Uncertain non-usage findings are labelled Medium or Low; no dead-code claim is made.
* No Version 2 requirement or redesign is included.
* No repository code was modified.

## Evidence Not Accessible

* Exhaustive repository-wide code search/grep across all branches and files.
* Runtime dependency graph, import telemetry, API traffic, scheduled-job history, or deployed process logs.
* Local execution of pytest, coverage, mypy, Ruff, or the usage script.
* External notebooks, scripts, downstream repositories, or uncommitted local files that may consume the package.
* Non-default branches unless represented by the inspected commit history.
