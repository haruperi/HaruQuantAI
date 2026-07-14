# Research — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `research`
* **Repository:** `haruperi/HaruQuant`
* **Audited revision:** default branch `main`, observed at commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/research`
* **Requested tests path:** `ttests/unit/app/services/research`
* **Likely current tests path:** `tests/unit/app/services/research`
* **Known example path:** `tests/usage/app/services/12_research.py`
* **Primary runtime caller inspected:** `app/api/routes/edge.py`
* **Files represented:** 46 Python files registered by the package export surface or directly imported by those files.
* **Related packages searched or inspected:** `app/api/routes/edge.py`, `app/services/__init__.py`, `app/services/analytics`, `app/services/data`, `app/services/indicators`, `app/services/utils`, broker data access used by the Edge API, database persistence invoked by the Edge API, and the known usage example.
* **Audit limitations:**
  * The GitHub connector exposed individual files but not a reliable recursive directory listing. The 46-file boundary is reconstructed from the current package registry, subpackage `__init__.py` files, import relationships, and direct file retrieval. No additional Python file was observed, but filesystem completeness could not be independently proven.
  * Repository-wide code search returned no indexed results even for symbols known to exist. Caller conclusions therefore combine the current package export map, direct inspection of the production Edge API route, internal imports/calls, dynamic service-resolution code, the supplied usage example, and research-related commit evidence.
  * The requested `ttests/...` directory could not be resolved. The likely `tests/unit/...` directory could not be enumerated through the connector, so test-file coverage and pass/fail status are not independently verified.
  * Dynamic consumers outside the inspected route may resolve symbols through `app.services.research.__getattr__`, `_common.__getattr__`, `service_modules()`, or string-based agent/tool registries. Items without a direct caller are therefore marked **Possibly used** or **Unknown**, not dead code.
  * No code was changed and no Version 2 requirements were created.

## 2. Executive Summary

The Version 1 research domain is not a small isolated library. It provides a broad Edge Lab subsystem with five major operational stages:

1. market-data preparation and quality control;
2. core descriptive metrics and seasonality analysis;
3. statistical edge detectors and market-structure research;
4. PCA/K-Means unsupervised structure analysis;
5. scorecard, validation, calibration, reporting, snapshot, and automation support.

A production integration is confirmed in `app/api/routes/edge.py`. That route imports 38 package symbols and executes a progressive workflow:

```text
broker/data source
→ prepare_research_dataset()
→ build_core_metric_profile()
→ run_seasonality()
→ build_market_structure_profile()
→ UnsupervisedResearchService.analyze_frame()
→ build_edge_lab_scorecard_report()
→ database snapshot/cache
```

The same route also runs EDS-0 through EDS-3, forward-outcome validation, calibration, batch automation, and scheduled refresh. This makes the data, core-metric, seasonality, EDS, market-structure, unsupervised-modeling, and scorecard paths operational at the code-integration level.

The strongest structural problems are:

* a 207-symbol dynamic top-level facade mixing domain-owned behavior, third-party-facing tools, and re-exported analytics/utilities;
* several large multi-responsibility files, especially `standard_tools.py`, `market_structure.py`, `scorecard.py`, and `seasonality.py`;
* duplicated calculations and classification logic across feature, metric, market-structure, analytics, and standardized-tool layers;
* contradictory session definitions and inconsistent edge-confirmation rules;
* stale example code that no longer matches current signatures;
* public reporting and snapshot helpers whose current callers were not demonstrated;
* statistical weaknesses in several EDS null comparisons, including hard-coded BUY-side nulls for mixed-direction samples;
* incomplete repository-wide caller/test evidence due connector search limitations.

The production caller evidence is strong for the main Edge Lab path. Evidence is medium for package-wide non-usage conclusions and low for test completeness.

```text
Module folders: 5 | Files: 46 | Public symbols: 207 | Symbols with confirmed production callers: 38 (18.4%) | Workflows found: 9
```

**Metric notes:** “Module folders” counts the root plus four subpackages. “Public symbols” counts package-level resolvable exports; public methods are documented separately. The caller percentage is deliberately conservative and counts direct production imports from `app/api/routes/edge.py`, not internal support calls.

## 3. Actual Package Structure

```text
Package: app.services.research
├── Root module folder
│   ├── __init__.py
│   │   └── Dynamic package facade: 207 resolvable names through __getattr__()
│   ├── _common.py
│   │   └── research_modeling_module()
│   ├── classifier.py
│   │   ├── DEFAULT_MIN_TRADES, DEFAULT_DELTA_R, DEFAULT_STRONG_R
│   │   ├── EdgeClass
│   │   ├── EdgeSummary.is_real / is_positive
│   │   ├── ClassificationResult
│   │   └── classify_symbol()
│   ├── config.py
│   │   ├── DataConfig, SessionConfig, BootstrapConfig, PermutationConfig
│   │   ├── NullModelsConfig, MeanReversionConfig, TrendPersistenceConfig
│   │   ├── MarketStructureConfig, SessionEdgeConfig, EdgeLabConfig
│   │   └── create_config()
│   ├── results_schema.py
│   │   ├── TradeSample.to_dict()
│   │   ├── EdgeStats.to_dict / edge_confirmed / verdict
│   │   └── EdgeResult.to_dict / from_dict / summary
│   ├── null_models.py
│   │   ├── block_bootstrap_ci(), block_bootstrap_distribution()
│   │   ├── permutation_test(), random_entry_null(), r_space_null()
│   │   ├── session_randomized_null(), shuffle_returns_null()
│   │   ├── benjamini_hochberg(), holm_bonferroni()
│   │   ├── compute_null_percentile(), null_distribution_stats()
│   │   └── exceeds_null_threshold()
│   ├── eds_null_models.py
│   │   ├── run_eds_null_baseline()
│   │   ├── compare_to_null()
│   │   └── get_acceptance_criteria()
│   ├── eds_mean_reversion.py
│   │   └── run_eds_mean_reversion()
│   ├── eds_trend_persistence.py
│   │   └── run_eds_trend_persistence()
│   ├── eds_session.py
│   │   ├── compute_session_statistics()
│   │   ├── run_session_breakout_strategy()
│   │   ├── run_session_fade_strategy()
│   │   └── run_eds_session()
│   ├── session_config.py
│   │   ├── EDGE_SESSION_WINDOWS, EDGE_SESSION_ORDER
│   │   ├── active_sessions_for_hour(), session_label_for_hour()
│   │   ├── session_hours_payload()
│   │   └── tag_sessions()
│   ├── seasonality.py
│   │   ├── DEFAULT_ADR_PERIOD, SESSION_ORDER
│   │   ├── SeasonalityFilters
│   │   └── run_seasonality()
│   ├── market_structure.py
│   │   ├── TrendSwingPoint, TrendLeg
│   │   ├── TrendScoreRow.to_dict()
│   │   ├── MarketStructureProfile.to_dict()
│   │   ├── build_market_structure_profile()
│   │   └── build_market_structure_research_profile()
│   ├── market_structure_profiles.py
│   │   ├── MAJOR_FX, INDEX_MARKERS, METAL_MARKERS, CRYPTO_MARKERS
│   │   ├── PROFILE_OVERRIDES
│   │   ├── timeframe_bucket(), symbol_class()
│   │   ├── resolve_market_structure_profile()
│   │   └── resolve_market_structure_profile_overrides()
│   ├── market_structure_strategy_fit.py
│   │   └── build_strategy_fit()
│   ├── market_structure_stability.py
│   │   └── build_market_structure_stability_report()
│   ├── market_structure_robustness.py
│   │   └── build_market_structure_robustness_report()
│   ├── market_structure_validation.py
│   │   ├── confidence_bucket()
│   │   ├── label_realized_market_behavior()
│   │   └── build_validation_summary()
│   ├── market_structure_calibration.py
│   │   ├── MarketStructureCalibrationCandidate.to_dict()
│   │   ├── classify_with_candidate()
│   │   ├── build_calibration_grid()
│   │   └── evaluate_calibration_candidates()
│   ├── market_structure_metric_calibration.py
│   │   ├── MarketStructureMetricCalibrationCandidate.to_dict()
│   │   ├── build_metric_calibration_grid()
│   │   └── evaluate_metric_calibration_candidates()
│   ├── market_structure_profile_calibration.py
│   │   └── evaluate_profile_calibration()
│   ├── scorecard.py
│   │   ├── SCORECARD_SPEC_VERSION
│   │   └── build_edge_lab_scorecard_report()
│   ├── reporting.py
│   │   ├── result_to_markdown(), result_to_summary()
│   │   ├── save_markdown(), save_json()
│   │   ├── generate_multi_symbol_report()
│   │   └── print_result_summary()
│   ├── profile_snapshot.py
│   │   └── build_edge_profile_snapshot()
│   ├── profile_reporting.py
│   │   ├── build_profile_summary(), build_dashboard_summary()
│   │   ├── snapshot_report_json(), snapshot_report_markdown()
│   │   ├── comparison_report_markdown()
│   │   └── save_json_report(), save_markdown_report()
│   └── standard_tools.py
│       ├── ForexFactory fetch tools (4)
│       ├── news/calendar/sentiment normalization tools (6)
│       ├── market/statistical calculation tools (9)
│       ├── regime/condition detection tools (4)
│       └── hypothesis, validation, and evidence-pack tools (9)
├── data
│   ├── __init__.py
│   ├── models.py
│   │   ├── CanonicalOHLCVSSchema
│   │   ├── DatasetIssue, CleaningAction
│   │   ├── DataQualityReportModel
│   │   └── PreparedDataset
│   ├── validation.py
│   │   └── validate_dataset()
│   ├── cleaning.py
│   │   ├── CleaningConfig
│   │   └── clean_dataset()
│   ├── enrichment.py
│   │   ├── EnrichmentConfig
│   │   └── enrich_dataset()
│   └── preparation.py
│       └── prepare_research_dataset()
├── features
│   ├── __init__.py
│   ├── calculations.py
│   │   ├── returns, moving-average, dispersion, ATR, Bollinger, RSI
│   │   ├── momentum, Donchian, Hurst, pivot, ADR
│   │   ├── forward-return/MFE/MAE functions
│   │   └── volatility/trend regime detectors
│   ├── leakage.py
│   │   ├── TimeSplitResult
│   │   ├── validate_no_lookahead_features()
│   │   ├── enforce_time_split()
│   │   ├── mask_research_artifact()
│   │   └── dump_masked_research_json()
│   └── pipeline.py
│       ├── FeatureSpec
│       └── FeaturePipeline.describe / fingerprint / compute_batch /
│           compute_incremental / inspect_graph
├── core_metrics
│   ├── __init__.py
│   ├── base.py
│   │   ├── MetricValue
│   │   ├── MetricContext
│   │   └── MetricCalculator.compute()
│   ├── registry.py
│   │   └── MetricRegistry.register / get / all / families / from_calculators
│   └── service.py
│       ├── CoreMetricProfile.to_dict()
│       ├── ReturnsCalculator.compute()
│       ├── RocCalculator.compute()
│       ├── CandlesCalculator.compute()
│       ├── RangesCalculator.compute()
│       ├── VolatilityCalculator.compute()
│       ├── SpreadCalculator.compute()
│       ├── VolumeActivityCalculator.compute()
│       ├── DEFAULT_CALCULATORS
│       ├── build_default_registry()
│       └── build_core_metric_profile()
└── modeling
    ├── __init__.py
    ├── contracts.py
    │   ├── UnsupervisedResearchConfig.to_dict()
    │   ├── UnsupervisedResearchRequest
    │   └── UnsupervisedResearchResult.to_metadata()
    ├── feature_sets.py
    │   ├── FeatureSetFrame.to_metadata()
    │   └── build_market_regime_feature_frame()
    ├── unsupervised.py
    │   ├── PcaModelResult.to_metadata()
    │   ├── ClusterModelResult.to_metadata()
    │   ├── run_pca(), cluster_feature_space()
    │   └── attach_cluster_labels()
    ├── unsupervised_insights.py
    │   ├── InvestmentDataSummary.to_dict()
    │   ├── PcaRiskFactor.to_dict()
    │   ├── ClusterOutperformance.to_dict()
    │   ├── SignalAdaptationResult.to_metadata()
    │   ├── UnsupervisedInsightReport.to_metadata()
    │   ├── summarize_investment_data()
    │   ├── identify_pca_risk_factors()
    │   ├── compute_forward_returns()
    │   ├── analyze_cluster_outperformance()
    │   ├── adapt_signals_by_cluster()
    │   └── build_unsupervised_insight_report()
    └── service.py
        └── UnsupervisedResearchService.analyze / analyze_frame
```

## 4. Module and File Inventory

Dependencies are listed in the requested order: standard library; required third-party; local modules.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| data | `models.py` | Canonical dataset, issue, action, report, and prepared-dataset contracts | `CanonicalOHLCVSSchema`, `DatasetIssue`, `CleaningAction`, `DataQualityReportModel`, `PreparedDataset` | `dataclasses`, typing; `pandas`; none | **Used** | **Essential** |
| data | `validation.py` | Validate index, schema, OHLC relationships, timestamps, spread, volume, and gaps | `validate_dataset` | typing; `numpy`, `pandas`; `app.services.data.transforms.TimeframeManager`, research data models, utils validators | **Used** | **Essential** |
| data | `cleaning.py` | Copy and clean research data according to configurable policies | `CleaningConfig`, `clean_dataset` | `dataclasses`; `numpy`, `pandas`; research models | **Used** | **Essential** |
| data | `enrichment.py` | Add price geometry, returns, calendar/session, rollover, and quote metadata | `EnrichmentConfig`, `enrich_dataset` | `dataclasses`; `numpy`, `pandas`; session configuration and research models | **Used** | **Essential** |
| data | `preparation.py` | Orchestrate fetch → normalize → validate → clean → enrich | `prepare_research_dataset` | typing; `pandas`; utils `DataSource`/normalization, research data functions | **Used** | **Essential** |
| data | `__init__.py` | Stable data-pipeline export surface | All data contracts and functions | none; none; data submodules | **Used** | **Supporting** |
| features | `calculations.py` | Flat research feature/statistical kernels | 26 calculation functions | typing; `numpy`, `pandas`; none | **Used internally** | **Supporting** |
| features | `leakage.py` | Time split, masking, serialization, and look-ahead checks | `TimeSplitResult`, four functions | `dataclasses`, `json`, typing; `numpy`, `pandas`; utils security | **Used internally / Possibly used externally** | **Useful** |
| features | `pipeline.py` | Versioned batch/incremental indicator feature graph | `FeatureSpec`, `FeaturePipeline` | `dataclasses`, `hashlib`, `json`; `pandas`; indicator service functions | **Used** | **Essential** |
| features | `__init__.py` | Re-export all calculation functions plus leakage and pipeline APIs | Dynamic calculation `__all__` plus explicit exports | none; none; feature submodules | **Used** | **Supporting** |
| core_metrics | `base.py` | Normalized metric value/context and calculator protocol | `MetricValue`, `MetricContext`, `MetricCalculator` | `dataclasses`, typing; `pandas`; data models | **Used internally** | **Supporting** |
| core_metrics | `registry.py` | Family-keyed metric calculator registry | `MetricRegistry` | `dataclasses`, collections; none; metric protocol | **Used internally** | **Supporting** |
| core_metrics | `service.py` | Compute core return, ROC, candle, range, volatility, spread, and activity metrics | profile, seven calculators, registry builders | `dataclasses`, `math`, typing; `numpy`, `pandas`; core base/registry, data models | **Used** | **Essential** |
| core_metrics | `__init__.py` | Core-metric export surface | profile, protocol/context/value, registry, builders | none; none; core metric submodules | **Used** | **Supporting** |
| root | `results_schema.py` | Canonical EDS trade/stat/result contracts and serialization | `TradeSample`, `EdgeStats`, `EdgeResult` | `dataclasses`, `datetime`, typing; none; none | **Used** | **Essential** |
| root | `null_models.py` | Bootstrap, permutation, random-entry, R-space, session, shuffle, and multiplicity tests | 13 statistical functions | typing; `numpy`, `pandas`; none | **Used internally** | **Essential** |
| root | `config.py` | Configuration contracts for EDS and market structure | 10 dataclasses, `create_config` | `dataclasses`; none; none | **Used** | **Essential** |
| root | `eds_null_models.py` | Build null baselines and acceptance thresholds | three functions | `dataclasses`, typing; `numpy`, `pandas`; config, features, null models, schemas, logger | **Used** | **Essential** |
| root | `eds_mean_reversion.py` | Simulate and statistically evaluate mean-reversion edge | `run_eds_mean_reversion` | `dataclasses`; `numpy`, `pandas`; analytics, config, features, null models, schemas, logger | **Used** | **Essential** |
| root | `eds_trend_persistence.py` | Simulate and statistically evaluate trend-persistence edge | `run_eds_trend_persistence` | `dataclasses`; `numpy`, `pandas`; analytics, config, features, null models, schemas, logger | **Used** | **Essential** |
| root | `eds_session.py` | Session statistics plus breakout/fade strategy tests | four functions | `dataclasses`; `numpy`, `pandas`; analytics, config, sessions, features, null models, schemas, logger | **Used** | **Essential** |
| root | `classifier.py` | Convert MR/TP edge results into labels, robustness, and confidence | constants, three classes, `classify_symbol` | `dataclasses`, `enum`; none; `EdgeResult` | **Used** | **Useful** |
| root | `session_config.py` | Shared named session windows and timestamp tagging | constants and four functions | typing; `pandas`; none | **Used** | **Essential** |
| root | `seasonality.py` | Intraday/calendar/session opportunity and extreme statistics | constants, `SeasonalityFilters`, `run_seasonality` | `dataclasses`, collections, typing; `numpy`, `pandas`; session configuration | **Used** | **Essential** |
| root | `market_structure_profiles.py` | Symbol/timeframe grouping and profile overrides | constants and four functions | typing; none; none | **Used internally** | **Supporting** |
| root | `market_structure_strategy_fit.py` | Map market-structure summary to strategy archetype fit | `build_strategy_fit` | typing; none; none | **Used internally** | **Useful** |
| root | `market_structure.py` | Swing/leg analysis, EDS confirmation, distribution, range, excursion, regime, scoring, and final profile | four classes, two builders | `dataclasses`, typing; `numpy`, `pandas`; config, data/core models, EDS, features, profile/fit modules | **Used** | **Essential** |
| root | `market_structure_stability.py` | Re-run market structure across temporal slices | `build_market_structure_stability_report` | `collections`, typing; `numpy`, `pandas`; config, prepared data, market structure | **Used** | **Useful** |
| root | `market_structure_robustness.py` | Re-run market structure across parameter variants | `build_market_structure_robustness_report` | `collections`, `dataclasses`, typing; `numpy`; config, prepared data, market structure | **Used** | **Useful** |
| root | `market_structure_validation.py` | Label realized future behavior and aggregate prediction accuracy | three functions | typing; `numpy`, `pandas`; none | **Used** | **Useful** |
| root | `market_structure_calibration.py` | Grid-search top-level verdict thresholds/weights | candidate plus three functions | `collections`, `dataclasses`, `itertools`, typing; none; none | **Used** | **Useful** |
| root | `market_structure_metric_calibration.py` | Grid-search lower-level metric normalization bands | candidate plus two public functions | `collections`, `dataclasses`, `itertools`, typing; none; `MarketStructureConfig` | **Used** | **Useful** |
| root | `market_structure_profile_calibration.py` | Run calibration by symbol/timeframe profile | `evaluate_profile_calibration` | collections, typing; none; calibration and profile helpers | **Used** | **Useful** |
| modeling | `contracts.py` | Stable input/config/output contracts | three dataclasses | `dataclasses`, typing; `pandas`; insight report | **Used** | **Supporting** |
| modeling | `feature_sets.py` | Build a normalized market-regime feature frame | `FeatureSetFrame`, builder | `dataclasses`, typing; `pandas`; none | **Used** | **Essential** |
| modeling | `unsupervised.py` | PCA, K-Means, scaling, and label attachment | two result classes, three functions | `dataclasses`, collections, typing; `numpy`, `pandas`, `scikit-learn`; none | **Used** | **Essential** |
| modeling | `unsupervised_insights.py` | EDA, PCA interpretation, cluster forward performance, and advisory signal filtering | five classes, six functions | `dataclasses`, collections, typing; `pandas`; unsupervised kernels | **Used** | **Essential** |
| modeling | `service.py` | Single service boundary for unsupervised analysis | `UnsupervisedResearchService` | `dataclasses`, typing; `pandas`; modeling contracts/features/insights | **Used** | **Essential** |
| modeling | `__init__.py` | Modeling export surface | all modeling public APIs | none; none; modeling submodules | **Used** | **Supporting** |
| root | `scorecard.py` | Combine progressive outputs into score rows, strategy fit, tradeability, and readiness | `SCORECARD_SPEC_VERSION`, scorecard builder | collections, typing; none; none | **Used** | **Essential** |
| root | `profile_snapshot.py` | Normalize progressive Edge Lab payloads into persistence rows | `build_edge_profile_snapshot` | typing; none; none | **Possibly used** | **Questionable** |
| root | `reporting.py` | Render and persist EDS reports | six public functions | `json`, `datetime`, `pathlib`, typing; none; leakage masking, schemas, logger | **Possibly used** | **Useful** |
| root | `profile_reporting.py` | Render dashboard, snapshot, and comparison reports | seven public functions | `json`, `datetime`, `pathlib`, typing; none; none | **Possibly used** | **Useful** |
| root | `standard_tools.py` | Standardized agent-facing research, web, statistics, detection, hypothesis, and evidence tools | 32 functions | `datetime`, typing, `uuid`; `numpy`, `pandas`, optional runtime `requests`; utils standard response | **Possibly used** | **Questionable** |
| root | `_common.py` | Dynamic service-module resolution and modeling-module access | `research_modeling_module` | `types`, typing; none; `app.services` loader/resolver | **Possibly used** | **Supporting** |
| root | `__init__.py` | Dynamic top-level facade, lazy import map, callable standardization, analytics and utility re-exports | 207 resolvable symbols | `importlib`, typing; none; all research modules, analytics, validators, standardizer | **Used** | **Essential facade / structurally problematic** |

## 5. Public Behaviour Inventory

### Evidence notation

* **Runtime:** direct production import/call from `app/api/routes/edge.py`.
* **Internal:** direct call from another research module reached by a runtime workflow.
* **Dynamic:** resolvable through package/service `__getattr__`; no direct current caller confirmed.
* **Tests:** the known usage example was inspected; the unit-test directory was not enumerable.

### `data/models.py`

**File responsibility:** Canonical contracts shared by the data, metric, market-structure, and API layers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `CanonicalOHLCVSSchema` (`price_columns`, `required_columns`) | Dataclass | Name canonical OHLCVS columns | field names → schema/properties | None | None directly | data validation/preparation; core metrics; API route | Not independently enumerated | **Used** | **Essential** |
| `DatasetIssue` | Dataclass | Represent warning/fatal data issue | code/severity/message/count/details → record | None | None directly | `DataQualityReportModel`, validation | Not independently enumerated | **Supporting** | **Supporting** |
| `CleaningAction` | Dataclass | Represent a cleaning action | action/count/details → record | None | None directly | cleaning/report serialization/API | Not independently enumerated | **Used** | **Supporting** |
| `DataQualityReportModel` (`is_valid`, `add_issue`, `add_check`, `add_action`) | Dataclass + methods | Accumulate validation and cleaning evidence | issue/check/action → mutated report / bool | Local state mutation | None directly | all preparation and profile paths | Not independently enumerated | **Used** | **Essential** |
| `PreparedDataset` | Dataclass | Pair prepared frame, schema, and quality report | frame/report/schema → object | None | None directly | core metrics, market structure, modeling/API | Not independently enumerated | **Used** | **Essential** |

### `data/validation.py`, `cleaning.py`, `enrichment.py`, `preparation.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `validate_dataset(df, *, schema=None, timeframe=None)` | Function | Check index, required columns, numeric/OHLC rules, gaps, duplicates, spread, volume | DataFrame → `DataQualityReportModel` | Read-only | Propagated pandas/schema errors | preparation; direct facade | Not independently enumerated | **Used** | **Essential** |
| `CleaningConfig` | Dataclass | Select timezone, weekend/holiday, missing-bar, duplicate, and spread policies | configuration fields → object | None | None directly | preparation/API | Not independently enumerated | **Used** | **Supporting** |
| `clean_dataset(df, *, report, schema=None, config=None)` | Function | Apply configured cleaning to a copy and record actions | frame/report/config → cleaned frame | Local report mutation | `ValueError` for unsupported conditions where explicitly checked; pandas errors propagate | preparation | Not independently enumerated | **Used** | **Essential** |
| `EnrichmentConfig` | Dataclass | Select symbol/session/quote metadata enrichment | fields → object | None | None directly | preparation/API | Not independently enumerated | **Used** | **Supporting** |
| `enrich_dataset(df, *, report, schema=None, config=None)` | Function | Add pip/point, candle geometry, returns, temporal/session flags | frame/report/config → enriched frame | Local report mutation | `ValueError`/`KeyError` for missing structural inputs; pandas errors propagate | preparation | Not independently enumerated | **Used** | **Essential** |
| `prepare_research_dataset(source, symbol, timeframe, start_pos, end_pos, *, exclude_last_bar=True, schema=None, cleaning=None, enrichment=None)` | Function | Fetch and prepare canonical research data | data source request → `PreparedDataset` | Read-only external data-source call; local report mutation | `ValueError` for no data or fatal validation; provider errors propagate | `app/api/routes/edge.py`; automation; EDS/profile endpoints | Known example calls obsolete signature | **Used** | **Essential** |

### `features/calculations.py`

**File responsibility:** Pure or read-only numerical feature kernels.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `log_returns`, `simple_returns` | Functions | Calculate one-period returns | numeric series → series | Read-only | pandas/numeric errors propagate | EDS/null models; facade | Unit tests inaccessible | **Used internally** | **Supporting** |
| `sma`, `ema`, `std`, `zscore`, `percent_rank`, `rolling_percentile_rank` | Functions | Rolling location/dispersion/rank features | series + windows → series | Read-only | invalid window/data errors propagate | EDS and direct facade | Unit tests inaccessible | **Used internally** | **Supporting** |
| `atr`, `atr_percent`, `bollinger_bands`, `bb_width`, `bb_percent_b`, `rsi` | Functions | Volatility/band/oscillator features | OHLC/series + windows → series/tuple | Read-only | missing columns and invalid numeric inputs propagate | EDS/session/market structure | Unit tests inaccessible | **Used internally** | **Essential support** |
| `rate_of_change`, `momentum`, `donchian_channel`, `hurst_exponent`, `rolling_hurst`, `pivot_points`, `adr` | Functions | Momentum, channel, persistence, pivot, and daily range features | market series/frame → series/scalars/frames | Read-only | insufficient/missing data may yield NaN or propagate errors | package facade; some EDS paths | Unit tests inaccessible | **Possibly used / Internal** | **Useful** |
| `forward_returns`, `forward_max_favorable_excursion`, `forward_max_adverse_excursion` | Functions | Label future outcomes for research | price/OHLC + horizon/side → forward series | Read-only | bad side/columns/horizon errors | research consumers; stale example uses wrong signature | Known example broken | **Possibly used** | **Useful** |
| `detect_volatility_regime`, `detect_trend_regime` | Functions | Assign heuristic regime labels | series + thresholds/windows → series | Read-only | invalid columns/windows propagate | package facade; known example uses obsolete arguments | Known example broken | **Possibly used** | **Useful** |

### `features/leakage.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TimeSplitResult` | Dataclass | Hold train/validation/test frames and boundaries | frames/metadata → object | None | None directly | `enforce_time_split` consumers | Unit tests inaccessible | **Possibly used** | **Useful** |
| `validate_no_lookahead_features(data, *, feature_columns, timestamp_col=None)` | Function | Heuristically check feature alignment/correlation with immediate future close | frame + feature names → `(bool, str)` | Read-only | `ValueError`/`KeyError` for missing inputs | dynamic facade; stale example uses wrong call | Known example broken | **Possibly used** | **Questionable** |
| `enforce_time_split(data, *, train_fraction, validation_fraction, timestamp_col=None)` | Function | Chronologically split data | frame + fractions → `TimeSplitResult` | Read-only | `ValueError` for invalid fractions/insufficient structure | dynamic facade; stale example uses obsolete positional/result API | Known example broken | **Possibly used** | **Useful** |
| `mask_research_artifact`, `dump_masked_research_json` | Functions | Remove/mask sensitive or future-derived fields and serialize JSON | nested artifact → masked object/JSON string | Read-only | serialization/type errors may propagate | `reporting.save_json`; dynamic facade | Unit tests inaccessible | **Used internally** | **Supporting** |

### `features/pipeline.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `FeatureSpec` | Dataclass | Describe one named indicator feature and parameters | name/params/output → record | None | None directly | API unsupervised payload; `FeaturePipeline` | Unit tests inaccessible | **Used** | **Supporting** |
| `FeaturePipeline.describe()` | Method | Serialize pipeline definition | instance → dict | Read-only | None expected | fingerprint/introspection | Unit tests inaccessible | **Internal** | **Supporting** |
| `FeaturePipeline.fingerprint()` | Method | Hash deterministic pipeline description | instance → string | Read-only | serialization errors propagate | caching/reproducibility consumers | Unit tests inaccessible | **Possibly used** | **Useful** |
| `FeaturePipeline.compute_batch(data)` | Method | Apply configured indicator features to a copy | DataFrame → enriched DataFrame | Read-only | `ValueError` for unknown feature; indicator errors propagate | `app/api/routes/edge.py::_build_unsupervised_edge_payload` | Runtime caller confirmed | **Used** | **Essential** |
| `FeaturePipeline.compute_incremental(data)` | Method | Incrementally compute with internal buffer | DataFrame → enriched DataFrame | Local state mutation | same as batch | no direct current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Questionable** |
| `FeaturePipeline.inspect_graph()` | Method | Return graph/dependency metadata | instance → dict/list | Read-only | None expected | no direct current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Useful** |

### `core_metrics/base.py`, `registry.py`, `service.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `MetricValue`, `MetricContext` | Dataclasses | Normalize metric outputs and shared computation context | fields → records | None | None directly | calculators/profile builder | Unit tests inaccessible | **Supporting** | **Supporting** |
| `MetricCalculator.compute(context)` | Protocol method | Define metric-family contract | context → metric values | Read-only contract | implementation-specific | registry/calculators | Unit tests inaccessible | **Supporting** | **Supporting** |
| `MetricRegistry.register/get/all/families/from_calculators` | Methods | Register and retrieve calculators by family | calculator/family → mutation/value/list/registry | Local state mutation for registration | `KeyError` on missing family | default registry/profile builder | Unit tests inaccessible | **Used internally** | **Supporting** |
| `CoreMetricProfile.to_dict()` | Method | Serialize profile, report, and values | profile → dict | Read-only | serialization errors unlikely | API automation | Runtime caller confirmed | **Used** | **Essential** |
| `ReturnsCalculator.compute`, `RocCalculator.compute`, `CandlesCalculator.compute`, `RangesCalculator.compute`, `VolatilityCalculator.compute`, `SpreadCalculator.compute`, `VolumeActivityCalculator.compute` | Methods | Compute seven metric families | `MetricContext` → `list[MetricValue]` | Read-only | missing columns/numeric errors propagate | default registry/profile builder | Unit tests inaccessible | **Used internally** | **Essential support** |
| `DEFAULT_CALCULATORS` | Constant | Default calculator instances | N/A | Mutable module-level list; calculators stateless | N/A | `build_default_registry` | Unit tests inaccessible | **Used internally** | **Supporting** |
| `build_default_registry()` | Function | Register default calculators | none → `MetricRegistry` | Local registry construction | None expected | profile builder | Unit tests inaccessible | **Used internally** | **Supporting** |
| `build_core_metric_profile(prepared, *, symbol, timeframe, data_source, range_by, ...)` | Function | Produce normalized core metric profile | prepared dataset + metadata → `CoreMetricProfile` | Read-only | missing required columns/numeric errors propagate | `app/api/routes/edge.py` automation/endpoints | Runtime caller confirmed | **Used** | **Essential** |

### `config.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `DataConfig`, `BootstrapConfig`, `PermutationConfig` | Dataclasses | Data-range and resampling/permutation settings | fields → config | None | None directly | API/EDS | Unit tests inaccessible | **Used** | **Essential** |
| `NullModelsConfig`, `MeanReversionConfig`, `TrendPersistenceConfig`, `SessionEdgeConfig` | Dataclasses | EDS-specific settings | fields → config | None | None directly | EDS/API | Unit tests inaccessible | **Used** | **Essential** |
| `SessionConfig` | Dataclass | Legacy Asia/London/NY/off-hour definitions | hour tuples → config | None | None directly | `run_eds_session` | Unit tests inaccessible | **Used** | **Supporting but conflicting** |
| `MarketStructureConfig` | Dataclass | Thresholds, weights, profiles, stability, and robustness settings | fields → config | None | None directly | market structure/API/calibration | Unit tests inaccessible | **Used** | **Essential** |
| `EdgeLabConfig` | Dataclass | Aggregate EDS configuration; requires `data` | nested configs → config | None | constructor `TypeError` when required data omitted | API/EDS consumers | Known example constructs incorrectly | **Used** | **Useful** |
| `create_config(symbol, timeframe="M15", end_pos=5000, **overrides)` | Function | Convenience aggregate config builder | identifiers + prefixed overrides → `EdgeLabConfig` | None | dataclass argument errors for recognized bad values | no direct current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Questionable** |

### `results_schema.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TradeSample.to_dict()` | Method | Serialize one simulated trade | object → dict | Read-only | None expected | EDS/reporting/API persistence | Unit tests inaccessible | **Used** | **Essential** |
| `EdgeStats.to_dict()` | Method | Serialize aggregate edge statistics | object → dict | Read-only | None expected | `EdgeResult.to_dict`, API | Unit tests inaccessible | **Used** | **Essential** |
| `EdgeStats.edge_confirmed`, `EdgeStats.verdict` | Properties | Derive edge status/label | stats → bool/string | Read-only | None expected | market structure/report consumers | Unit tests inaccessible | **Used** | **Useful but inconsistent** |
| `EdgeResult.to_dict()`, `EdgeResult.from_dict()`, `EdgeResult.summary()` | Methods | Serialize, deserialize, and summarize EDS result | object/dict → dict/object | Read-only | malformed dict may raise `KeyError`/`TypeError` | API, reporting, classifier | Unit tests inaccessible | **Used** | **Essential** |

### `null_models.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `block_bootstrap_ci`, `block_bootstrap_distribution` | Functions | Block-resample a statistic and confidence interval | array/statistic/config → tuple/array | Read-only, seeded stochastic | invalid sizes/statistic errors | EDS-1/2/3 | Unit tests inaccessible | **Used internally** | **Essential** |
| `permutation_test` | Function | Compare observation with null distribution | scalar + null → p-value | Read-only | empty/invalid arrays may yield NaN or errors | EDS/session | Unit tests inaccessible | **Used internally** | **Essential** |
| `random_entry_null`, `r_space_null`, `session_randomized_null`, `shuffle_returns_null` | Functions | Generate strategy-null distributions | returns/OHLC + trade assumptions → array | Read-only, seeded stochastic | bad side/columns/insufficient samples | EDS-0/1/2/3 | Unit tests inaccessible | **Used internally** | **Essential** |
| `benjamini_hochberg`, `holm_bonferroni` | Functions | Multiple-hypothesis correction | p-values + alpha/q → boolean array | Read-only | invalid arrays propagate | EDS-3; facade | Unit tests inaccessible | **Used internally** | **Useful** |
| `compute_null_percentile`, `null_distribution_stats`, `exceeds_null_threshold` | Functions | Summarize and compare null distributions | null array/observation → scalar/dict/bool | Read-only | empty/invalid data handling varies | EDS-0/helpers | Unit tests inaccessible | **Used internally** | **Supporting** |

### EDS files

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `run_eds_null_baseline(df, symbol, timeframe, cfg, boot, perm, ...)` | Function | Build random-entry, R-space, and shuffle baselines | OHLC + configs → `EdgeResult` | Read-only; logging | missing columns/config/numeric errors propagate | `app/api/routes/edge.py` | Known example wrong signature | **Used** | **Essential** |
| `compare_to_null(observed_expectancy, null_result, hold_bars=32, side="BUY")` | Function | Compare observed expectancy with stored null summary | scalar/result → dict verdict | Read-only; logging | malformed result may raise | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful** |
| `get_acceptance_criteria(null_result)` | Function | Convert null thresholds to fixed acceptance criteria | result → dict | Read-only; logging | malformed result may raise | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful** |
| `run_eds_mean_reversion(df, symbol, timeframe, cfg, boot, perm, ...)` | Function | Simulate Bollinger/z-score/ADR mean-reversion trades and test expectancy | OHLC + configs → `EdgeResult` | Read-only; logging | missing data/config errors propagate | API; market structure | Known example wrong signature | **Used** | **Essential** |
| `run_eds_trend_persistence(df, symbol, timeframe, cfg, boot, perm, ...)` | Function | Simulate high-ADR breakout/continuation trades and test expectancy | OHLC + configs → `EdgeResult` | Read-only; logging | missing data/config errors propagate | API; market structure | Known example wrong signature | **Used** | **Essential** |
| `compute_session_statistics(df, session, ...)` | Function | Summarize return/range behavior by session | tagged frame + session → dict | Read-only | missing `session`/price columns | `run_eds_session` | Unit tests inaccessible | **Used internally** | **Supporting** |
| `run_session_breakout_strategy(...)`, `run_session_fade_strategy(...)` | Functions | Generate one-session breakout/fade trade samples | tagged OHLC/ATR + settings → trade list | Read-only | missing columns/index errors | `run_eds_session` | Unit tests inaccessible | **Used internally** | **Essential support** |
| `run_eds_session(df, symbol, timeframe, cfg, sessions_cfg, boot, perm, ...)` | Function | Evaluate session breakout/fade hypotheses with FDR correction | OHLC + configs → `EdgeResult` | Read-only; logging | missing columns/config errors propagate | `app/api/routes/edge.py` | Known example wrong signature | **Used** | **Essential** |

### `classifier.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `DEFAULT_MIN_TRADES`, `DEFAULT_DELTA_R`, `DEFAULT_STRONG_R` | Constants | Classification thresholds | N/A | None | N/A | classification helpers | Unit tests inaccessible | **Used internally** | **Supporting** |
| `EdgeClass` | Enum | Label trend/reversion/mixed/no-edge outcomes | enum values → string enum | None | invalid enum construction may raise | classifier/API serialization | Unit tests inaccessible | **Used** | **Useful** |
| `EdgeSummary.is_real`, `EdgeSummary.is_positive` | Properties | Evaluate CI/sample and expectancy conditions | summary → bool | Read-only | None expected | classifier | Unit tests inaccessible | **Used internally** | **Supporting** |
| `ClassificationResult` | Dataclass | Return class, robustness, confidence, and breakdown | fields → record | None | None directly | API route | Unit tests inaccessible | **Used** | **Useful** |
| `classify_symbol(mr, tp, *, delta_r=..., strong_r=...)` | Function | Classify one or two EDS results | optional MR/TP results → `ClassificationResult` | Read-only | malformed result attributes propagate | `app/api/routes/edge.py` | Unit tests inaccessible | **Used** | **Useful** |

### `session_config.py` and `seasonality.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `EDGE_SESSION_WINDOWS`, `EDGE_SESSION_ORDER` | Constants | Named Sydney/Tokyo/London/NY windows and order | N/A | Mutable mapping/list-like contents | N/A | seasonality/tagging | Unit tests inaccessible | **Used internally** | **Essential support** |
| `active_sessions_for_hour(hour)`, `session_label_for_hour(hour)` | Functions | Resolve active session names or one label | integer hour → tuple/string | Read-only | invalid numeric values follow comparisons | enrichment/seasonality | Unit tests inaccessible | **Used internally** | **Supporting** |
| `session_hours_payload()` | Function | Serialize session windows | none → dict | Read-only | None expected | metadata consumers | Unit tests inaccessible | **Possibly used** | **Useful** |
| `tag_sessions(df, ...)` | Function | Add session labels based on `DatetimeIndex` | frame → copied/tagged frame | Read-only | `ValueError` without `DatetimeIndex` | EDS-3 | Unit tests inaccessible | **Used internally** | **Essential support** |
| `DEFAULT_ADR_PERIOD`, `SESSION_ORDER` | Constants | Seasonality defaults | N/A | None | N/A | `run_seasonality` helpers | Unit tests inaccessible | **Used internally** | **Supporting** |
| `SeasonalityFilters` | Dataclass | Select decades/years/months/weekdays/hours | lists → config | None | None directly | API route | Runtime caller confirmed | **Used** | **Useful** |
| `run_seasonality(df, *, symbol, timeframe, point_size=1.0, pip_size=None, filters=None, data_offset=0, data_limit=20)` | Function | Produce calendar, heatmap, session, opportunity, row, and extreme summaries | OHLCVS + quote/filter metadata → dict | Read-only | `ValueError` when point/pip size invalid; missing columns propagate | API automation/endpoints | Runtime caller confirmed | **Used** | **Essential** |

### Market-structure files

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TrendSwingPoint`, `TrendLeg` | Dataclasses | Represent detected swings and directional legs | fields → records | None | None directly | market structure profile | Unit tests inaccessible | **Used internally** | **Supporting** |
| `TrendScoreRow.to_dict()` | Dataclass method | Represent and serialize one weighted score row | object → dict | Read-only | None expected | profile/scorecard consumers | Unit tests inaccessible | **Used internally** | **Supporting** |
| `MarketStructureProfile.to_dict()` | Dataclass method | Serialize full market structure output | object → dict | Read-only | serialization errors unlikely | API automation | Runtime caller confirmed | **Used** | **Essential** |
| `build_market_structure_profile(prepared, *, symbol, timeframe, data_source, range_by, ...)` | Function | Build swings, legs, EDS confirmations, range/distribution/excursion/regime metrics, strategy fit, and verdict | prepared dataset + config → profile | Read-only; high CPU; logging through nested EDS | missing columns/insufficient-data numeric errors may propagate | `app/api/routes/edge.py`; stability/robustness | Runtime caller confirmed | **Used** | **Essential** |
| `build_market_structure_research_profile(...)` | Function | Run base profile with expensive quality-adjusted research settings | prepared dataset + config → profile | Read-only; high CPU | same as base profile | no direct current external caller demonstrated | Unit tests inaccessible | **Possibly used** | **Questionable** |
| `timeframe_bucket`, `symbol_class` | Functions | Group timeframe and symbol | string → class label | Read-only | None expected | profile resolution/calibration | Unit tests inaccessible | **Used internally** | **Supporting** |
| `resolve_market_structure_profile`, `resolve_market_structure_profile_overrides` | Functions | Return profile key and configured overrides | symbol/timeframe → dict | Read-only | None expected | market structure/profile calibration | Unit tests inaccessible | **Used internally** | **Supporting** |
| `MAJOR_FX`, `INDEX_MARKERS`, `METAL_MARKERS`, `CRYPTO_MARKERS`, `PROFILE_OVERRIDES` | Constants | Static classification and override tables | N/A | Mutable module-level containers | N/A | profile functions | Unit tests inaccessible | **Used internally** | **Supporting** |
| `build_strategy_fit(summary)` | Function | Rank five strategy archetypes from structure metrics | summary dict → ranked dict | Read-only | malformed/non-numeric values may raise | market structure | Unit tests inaccessible | **Used internally** | **Useful** |
| `build_market_structure_stability_report(...)` | Function | Compare verdict/direction/confidence across temporal blocks | prepared dataset + config → dict | Read-only; high CPU | nested profile errors propagate | API and quality-adjusted profile | Runtime caller confirmed | **Used** | **Useful** |
| `build_market_structure_robustness_report(...)` | Function | Compare verdict/direction/score across parameter grid | prepared dataset + config → dict | Read-only; high CPU | nested profile errors propagate | API and quality-adjusted profile | Runtime caller confirmed | **Used** | **Useful** |
| `confidence_bucket(score)` | Function | Convert confidence to high/medium/low/unknown | value → string | Read-only | None; conversion caught | API forward validation | Runtime caller confirmed | **Used** | **Supporting** |
| `label_realized_market_behavior(df, *, symbol, ...)` | Function | Label future window trend/reversion/mixed and diagnostics | future OHLC → dict | Read-only | missing columns propagate; <5 rows returns insufficient-data result | API evaluation refresh | Runtime caller confirmed | **Used** | **Useful** |
| `build_validation_summary(rows)` | Function | Aggregate prediction accuracy by confidence, verdict, symbol, and timeframe | evaluation rows → dict | Read-only | malformed rows may propagate conversion errors | API validation endpoint | Runtime caller confirmed | **Used** | **Useful** |
| `MarketStructureCalibrationCandidate.to_dict()`, `classify_with_candidate`, `build_calibration_grid`, `evaluate_calibration_candidates` | Class/method/functions | Test top-level verdict thresholds and weights against realized labels | run/validation rows → ranked candidates | Read-only; CPU | malformed run rows may raise | API calibration endpoints; profile calibration | Runtime caller confirmed | **Used** | **Useful** |
| `MarketStructureMetricCalibrationCandidate.to_dict()`, `build_metric_calibration_grid`, `evaluate_metric_calibration_candidates` | Class/method/functions | Recalculate lower-level metric bands and evaluate prediction accuracy | run/validation rows → ranked candidates | Read-only; potentially large grid CPU | malformed rows may raise | API calibration endpoint | Runtime caller confirmed | **Used** | **Useful** |
| `evaluate_profile_calibration(run_rows, validation_rows)` | Function | Group runs by symbol/timeframe profile and calibrate each group | rows → report dict | Read-only | malformed profile key may raise | API calibration endpoint | Runtime caller confirmed | **Used** | **Useful** |

### Modeling files

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `UnsupervisedResearchConfig.to_dict()` | Dataclass/method | Hold and serialize modeling settings | fields → dict | Read-only | None expected | API/service | Runtime caller confirmed | **Used** | **Supporting** |
| `UnsupervisedResearchRequest` | Dataclass | Package data, optional signals, and config | frames/config → request | None | None directly | service | Unit tests inaccessible | **Used internally** | **Supporting** |
| `UnsupervisedResearchResult.to_metadata()` | Dataclass/method | Hold completed/skipped outputs and serialize metadata | result → dict | Read-only | nested serialization errors may propagate | API payload builder | Runtime caller confirmed | **Used** | **Essential** |
| `FeatureSetFrame.to_metadata()` | Dataclass/method | Hold feature frame, columns, and lineage | object → dict | Read-only | None expected | service | Unit tests inaccessible | **Used internally** | **Supporting** |
| `build_market_regime_feature_frame(data, *, ...)` | Function | Create return, volatility, momentum, range, and optional EMA-spread features | lower-case market frame → `FeatureSetFrame` | Read-only | `ValueError` for empty/missing price column | service | Runtime path confirmed | **Used** | **Essential** |
| `PcaModelResult.to_metadata`, `ClusterModelResult.to_metadata` | Dataclass methods | Serialize PCA/K-Means model evidence | result → dict | Read-only | None expected | report/service | Unit tests inaccessible | **Used internally** | **Supporting** |
| `run_pca`, `cluster_feature_space`, `attach_cluster_labels` | Functions | Scale and fit PCA/K-Means; attach labels to a copy | feature frame + settings → results/frame | Read-only; CPU | `ValueError` for invalid dimensions/clusters/data | insight report | Runtime path confirmed | **Used** | **Essential** |
| `InvestmentDataSummary.to_dict`, `PcaRiskFactor.to_dict`, `ClusterOutperformance.to_dict`, `SignalAdaptationResult.to_metadata`, `UnsupervisedInsightReport.to_metadata` | Dataclass methods | Serialize EDA, factor, cluster, adaptation, and report outputs | object → dict | Read-only | None expected | service/API | Unit tests inaccessible | **Used internally** | **Supporting** |
| `summarize_investment_data` | Function | Produce descriptive, return, missingness, duplicate, and correlation summary | frame → summary | Read-only | `ValueError` for empty data | report builder | Runtime path confirmed | **Used** | **Useful** |
| `identify_pca_risk_factors` | Function | Extract and interpret top absolute PCA loadings | PCA result → factor tuple | Read-only | `ValueError` for non-positive top count | report builder | Runtime path confirmed | **Used** | **Useful** |
| `compute_forward_returns` | Function | Produce horizon-aligned forward return label | frame + horizon → series | Read-only | `ValueError` for bad horizon/missing price | cluster analysis | Runtime path confirmed | **Used** | **Supporting** |
| `analyze_cluster_outperformance` | Function | Compare each cluster’s in-sample forward performance and name regimes | data/labels → tuple | Read-only | malformed features/labels may raise | report builder | Runtime path confirmed | **Used** | **Useful** |
| `adapt_signals_by_cluster` | Function | Zero signals in clusters without positive relative performance | signal frame + cluster stats → result | Read-only copy | `ValueError` for missing label/signal column | report builder when signals provided | No current API signal frame supplied | **Possibly used** | **Questionable** |
| `build_unsupervised_insight_report` | Function | Orchestrate EDA, PCA, clustering, factors, performance, optional signal adaptation | features + settings → report | Read-only; CPU | nested validation/model errors | service | Runtime path confirmed | **Used** | **Essential** |
| `UnsupervisedResearchService.analyze`, `.analyze_frame` | Methods | Build features, enforce minimum sample, run report, and produce strategy/risk context | request/frame → completed or skipped result | Read-only; CPU | feature/model errors propagate; insufficient samples return `SKIPPED` | `app/api/routes/edge.py::_build_unsupervised_edge_payload` | Runtime caller confirmed | **Used** | **Essential** |

### `scorecard.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SCORECARD_SPEC_VERSION` | Constant | Version scorecard output semantics | N/A | None | N/A | API dataset metadata/snapshot | Runtime caller confirmed | **Used** | **Supporting** |
| `build_edge_lab_scorecard_report(*, dataset, core_metric_profile, seasonality_result, market_structure_profile, stability=None, robustness=None)` | Function | Build deterministic score rows, strategy ranking, tradeability, final score, confidence, and readiness | progressive output dicts → report dict or `None` | Read-only | returns `None` when prerequisites absent; malformed nested values may raise | API automation/endpoints | Runtime caller confirmed | **Used** | **Essential** |

### Reporting and snapshot files

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `result_to_markdown`, `result_to_summary` | Functions | Render one `EdgeResult` as Markdown or concise dict | result → string/dict | Read-only; Markdown includes current local timestamp | malformed result attributes | no current production caller demonstrated | Known example references reporting generally but is broken | **Possibly used** | **Useful** |
| `save_markdown`, `save_json` | Functions | Persist one EDS report | result/path → `Path` | Persistence write | filesystem/serialization errors | no current production caller demonstrated | Unit tests inaccessible | **Possibly used** | **Useful** |
| `generate_multi_symbol_report` | Function | Persist per-symbol/combined report files | results/output dir → summary path | Persistence write; directory creation | filesystem errors | no current production caller demonstrated | Unit tests inaccessible | **Possibly used** | **Useful** |
| `print_result_summary` | Function | Print concise result summary | result → `None` | Console output | malformed result attributes | no current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Questionable** |
| `build_edge_profile_snapshot(payload)` | Function | Flatten progressive UI/service payload into normalized metrics/scores/strategy-fit data | nested dict → snapshot dict | Read-only | malformed nested numeric conversions may raise | no import from current Edge API; DB route builds/persists payload directly | Unit tests inaccessible | **Possibly used** | **Questionable** |
| `build_profile_summary`, `build_dashboard_summary` | Functions | Extract concise UI/dashboard summaries | snapshot dict → dict | Read-only | malformed input mostly defaults | no current caller demonstrated in inspected route | Unit tests inaccessible | **Possibly used** | **Useful** |
| `snapshot_report_json`, `snapshot_report_markdown`, `comparison_report_markdown` | Functions | Render complete snapshot/comparison reports | snapshot/comparison → dict/string | Read-only; embeds current local timestamp | malformed rows may raise | no current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Useful** |
| `save_json_report`, `save_markdown_report` | Functions | Persist rendered profile reports | content/path → `Path` | Persistence write | filesystem/serialization errors | no current caller demonstrated | Unit tests inaccessible | **Possibly used** | **Useful** |

### `standard_tools.py`

All functions return the shared standard tool envelope unless an uncaught preprocessing error occurs.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `fetch_forexfactory_news`, `fetch_forexfactory_calendar`, `fetch_forexfactory_sentiment`, `fetch_forexfactory_instrument_page` | Functions | GET raw ForexFactory pages | optional trace metadata/symbol → standard envelope | External API call | HTTP/import errors are caught and returned; unexpected setup errors may propagate | dynamic package facade; no direct current caller confirmed | Unit tests inaccessible | **Possibly used** | **Questionable** |
| `parse_news_items`, `parse_calendar_events`, `parse_sentiment_snapshot`, `filter_events_by_symbol`, `classify_news_impact`, `create_news_blackout_windows` | Functions | Normalize and filter research/news/event inputs | lists/dicts/symbol/time settings → standard envelope | Read-only | generally converted to error envelopes | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful if registered** |
| `calculate_returns`, `calculate_volatility`, `calculate_atr`, `calculate_adr`, `calculate_spread_statistics`, `calculate_session_statistics`, `calculate_seasonality_statistics`, `calculate_regime_features`, `calculate_correlation_matrix` | Functions | Agent-facing statistical calculation wrappers | records/series/settings → standard envelope | Read-only | generally converted to error envelopes | dynamic facade | Unit tests inaccessible | **Possibly used** | **Questionable due overlap** |
| `detect_trend_strength`, `detect_market_regime`, `detect_mean_reversion_conditions`, `detect_breakout_conditions` | Functions | Agent-facing condition/regime detection | market records/settings → standard envelope | Read-only | generally converted to error envelopes | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful if registered** |
| `generate_research_hypothesis`, `score_research_hypothesis` | Functions | Create/score structured research hypotheses | evidence/claims/settings → standard envelope | Read-only | generally converted to error envelopes | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful if registered** |
| `check_sample_size`, `check_data_snooping_risk`, `check_lookahead_bias_risk`, `check_hypothesis_testability`, `check_contradictory_evidence` | Functions | Apply heuristic research guardrails | evidence/settings → standard envelope | Read-only | generally converted to error envelopes | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful if registered** |
| `build_research_evidence_pack` | Function | Assemble structured evidence package | component outputs → standard envelope | Read-only | generally converted to error envelope | dynamic facade | Unit tests inaccessible | **Possibly used** | **Useful if registered** |

### Package facades

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `app.services.research.__getattr__(name)` | Dynamic resolver | Import mapped research/re-export symbol, standardize callables, cache result | name → object | Module-global cache mutation | `AttributeError`/import errors | all `from app.services.research import ...` callers | Runtime route confirms | **Used** | **Essential facade** |
| `research_modeling_module()` | Function | Load modeling service module | none → module | Import/module cache mutation | import errors | dynamic facade; no direct caller confirmed | Unit tests inaccessible | **Possibly used** | **Supporting** |
| `_common.__getattr__(name)` | Dynamic resolver | Search all discovered research modules for an attribute | name → object | Import/module cache mutation | `AttributeError`/import errors | dynamic consumers | Unit tests inaccessible | **Possibly used** | **Supporting** |
| Analytics re-exports: `calmar_ratio`, `expectancy`, `max_drawdown`, `median_mae_mfe`, `profit_factor`, `sharpe_ratio`, `sortino_ratio`, `win_rate` | Re-exported functions | Expose analytics calculations through research facade | analytics inputs → analytics outputs | Depends on analytics implementation | analytics errors | EDS imports analytics directly; external research callers unknown | Unit tests outside scope | **Possibly used** | **Questionable boundary** |
| Utility re-exports: `DataSource`, `OHLCVSchema` | Re-exported types | Expose shared data-source/schema contracts | N/A | None | N/A | API/data preparation | Runtime route uses equivalent contracts | **Used/Supporting** | **Supporting** |

## 6. Actual Workflows

### `V1-WF-RESEARCH-001` — Prepare an Analysis-Ready Research Dataset

* **Scope:** Cross-domain
* **Trigger:** Edge API request or automated Edge Lab run.
* **Input boundary:** Broker/data-domain `DataSource`, symbol, timeframe, and range.
* **Functions and methods used:** `prepare_research_dataset()` → normalization → `validate_dataset()` → `clean_dataset()` → `enrich_dataset()`.
* **Files involved:** `data/preparation.py`, `data/validation.py`, `data/cleaning.py`, `data/enrichment.py`, `data/models.py`, `session_config.py`.
* **External dependencies:** Broker/data provider through `DataSource`; pandas/numpy; data timeframe manager; utility validators.
* **Output boundary:** `PreparedDataset` passed to core metrics, seasonality, market structure, and modeling.
* **Failure behaviour:** No/empty provider data or fatal validation raises `ValueError`; provider and dataframe errors propagate to the API layer.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync`; `app/services/research/data/preparation.py::prepare_research_dataset`.

```text
API or scheduled trigger
→ broker/data source fetch
→ prepare_research_dataset()
→ validate_dataset()
→ clean_dataset()
→ enrich_dataset()
→ PreparedDataset
```

### `V1-WF-RESEARCH-002` — Build Core Market Metrics

* **Scope:** Internal, invoked cross-domain through API.
* **Trigger:** Core-metric endpoint or full/partial automation stage.
* **Input boundary:** `PreparedDataset` plus symbol/timeframe/source metadata.
* **Functions and methods used:** `build_core_metric_profile()` → `build_default_registry()` → each calculator’s `compute()`.
* **Files involved:** `core_metrics/base.py`, `registry.py`, `service.py`.
* **External dependencies:** pandas/numpy.
* **Output boundary:** `CoreMetricProfile.to_dict()` supplied to scorecard and persistence.
* **Failure behaviour:** Missing canonical columns or invalid numeric frames propagate errors.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync`; `core_metrics/service.py`.

```text
PreparedDataset
→ build_core_metric_profile()
→ registry.all()
→ returns/ROC/candles/ranges/volatility/spread/activity calculators
→ CoreMetricProfile
```

### `V1-WF-RESEARCH-003` — Analyze Calendar and Session Opportunity

* **Scope:** Internal, invoked cross-domain through API.
* **Trigger:** Seasonality endpoint or automated profile.
* **Input boundary:** Prepared OHLCVS frame, symbol/timeframe, point/pip size, optional filters.
* **Functions and methods used:** `run_seasonality()` and private aggregation helpers; session labels from `session_config.py`.
* **Files involved:** `seasonality.py`, `session_config.py`.
* **External dependencies:** pandas/numpy.
* **Output boundary:** Intraday bias, heatmaps, calendar tables, session rankings, best/dead windows, paginated rows, extremes.
* **Failure behaviour:** Invalid point/pip sizes raise `ValueError`; required-column failures propagate.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py` calls `run_seasonality()` in automation.

```text
PreparedDataset.data
→ run_seasonality()
→ calendar/session/hour aggregations
→ opportunity windows and extremes
```

### `V1-WF-RESEARCH-004` — Run Statistical Edge Detectors

* **Scope:** Internal, exposed through API.
* **Trigger:** Edge Lab EDS request selecting null, MR, TP, session, or all.
* **Input boundary:** Prepared OHLC data, EDS configs, bootstrap/permutation configs.
* **Functions and methods used:** `run_eds_null_baseline()`, `run_eds_mean_reversion()`, `run_eds_trend_persistence()`, `run_eds_session()`, null-model functions, analytics metrics, `classify_symbol()`.
* **Files involved:** `eds_*.py`, `null_models.py`, `features/calculations.py`, `results_schema.py`, `classifier.py`, `config.py`.
* **External dependencies:** pandas/numpy; analytics metrics/ratios.
* **Output boundary:** `EdgeResult` objects, optional classification, API/database serialization.
* **Failure behaviour:** The API route catches and logs individual EDS failures, allowing other detectors to continue.
* **Operational status:** **Working with statistical caveats**
* **Evidence:** direct imports and calls in `app/api/routes/edge.py`; internal EDS call paths.

```text
Prepared OHLC
→ EDS-0 null baseline
→ EDS-1 mean reversion
→ EDS-2 trend persistence
→ EDS-3 session edge
→ EdgeResult(s)
→ optional classify_symbol()
```

### `V1-WF-RESEARCH-005` — Build Market-Structure Profile

* **Scope:** Internal, invoked cross-domain through API.
* **Trigger:** Market-structure endpoint or automation stage.
* **Input boundary:** `PreparedDataset`, symbol/timeframe/source metadata, `MarketStructureConfig`.
* **Functions and methods used:** `build_market_structure_profile()` → swing/leg/range/distribution/excursion/regime helpers → EDS-1/EDS-2 → profile override resolution → `build_strategy_fit()`. Optional research mode calls stability and robustness.
* **Files involved:** `market_structure.py`, profiles, strategy-fit, stability, robustness, EDS/config/core/data files.
* **External dependencies:** pandas/numpy; analytics through nested EDS.
* **Output boundary:** `MarketStructureProfile.to_dict()` passed to scorecard, validation, cache, snapshot.
* **Failure behaviour:** Nested profile/EDS errors propagate to route unless handled there; insufficient inputs can produce weak/NaN metrics rather than a single canonical failure result.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py` automation; `market_structure.py::build_market_structure_profile`.

```text
PreparedDataset
→ detect swings and legs
→ run EDS-1 and EDS-2
→ range/distribution/excursion/regime analysis
→ weighted scores and verdict
→ strategy fit
→ MarketStructureProfile
```

### `V1-WF-RESEARCH-006` — Run Unsupervised Structure Research

* **Scope:** Cross-domain boundary through API, internal modeling implementation.
* **Trigger:** Unsupervised endpoint or automated profile.
* **Input boundary:** Prepared frame normalized to lower-case columns.
* **Functions and methods used:** API `FeaturePipeline.compute_batch()` → `UnsupervisedResearchService.analyze_frame()` → `build_market_regime_feature_frame()` → PCA/K-Means → insight report.
* **Files involved:** `features/pipeline.py`, all `modeling/*`.
* **External dependencies:** pandas/numpy/scikit-learn; indicator service.
* **Output boundary:** metadata, cluster labels/statistics, PCA factors, strategy/risk context.
* **Failure behaviour:** Insufficient rows/features return `UnsupervisedResearchResult(status="SKIPPED")`; invalid dimensions/model inputs raise.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py::_build_unsupervised_edge_payload`.

```text
PreparedDataset
→ normalize column names
→ FeaturePipeline(EMA fast/slow).compute_batch()
→ UnsupervisedResearchService.analyze_frame()
→ feature frame
→ PCA + K-Means
→ cluster outperformance and risk context
```

### `V1-WF-RESEARCH-007` — Build, Cache, and Persist a Complete Edge Profile

* **Scope:** Cross-domain
* **Trigger:** Manual, batch, or scheduled Edge Lab automation.
* **Input boundary:** Symbol/timeframe/source/range and optional requested metric families.
* **Functions and methods used:** Workflows 001–006 plus `build_edge_lab_scorecard_report()`.
* **Files involved:** data, core metrics, seasonality, market structure, modeling, scorecard; caller-side database manager.
* **External dependencies:** broker/data service and database.
* **Output boundary:** response summary, cache hit/reuse metadata, and optional persisted profile snapshot.
* **Failure behaviour:** Missing prerequisites for partial recompute raise HTTP 400; stage errors propagate; configured scheduler may return skipped when symbols are absent.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync`, `run_scheduled_edge_lab_refresh`, `DatabaseManager.find_matching_profile_snapshot`, `save_profile_snapshot`.

```text
manual/batch/scheduled trigger
→ prepare dataset
→ core metrics
→ seasonality
→ market structure
→ unsupervised structure
→ scorecard
→ cache lookup/reuse
→ optional snapshot persistence
```

### `V1-WF-RESEARCH-008` — Forward Validation and Calibration

* **Scope:** Cross-domain
* **Trigger:** Evaluation/calibration API flow after future bars are available.
* **Input boundary:** Persisted market-structure run plus future broker/data bars.
* **Functions and methods used:** `label_realized_market_behavior()` → `confidence_bucket()` → database evaluation write → `build_validation_summary()` and one or more calibration evaluators.
* **Files involved:** validation and three calibration modules; API route.
* **External dependencies:** broker/data service and database.
* **Output boundary:** persisted realized labels, accuracy summaries, ranked calibration settings.
* **Failure behaviour:** Individual runs with missing metadata/data are skipped; malformed evaluation rows can fail calibration.
* **Operational status:** **Working / partially tolerant**
* **Evidence:** `app/api/routes/edge.py::_refresh_market_structure_evaluations` and direct imports of all calibration functions.

```text
persisted prediction + future bars
→ label_realized_market_behavior()
→ confidence_bucket()
→ save evaluation
→ build_validation_summary()
→ evaluate calibration candidates
```

### `V1-WF-RESEARCH-009` — Agent-Facing Standard Research Tools

* **Scope:** Cross-domain, dynamic/agent-facing.
* **Trigger:** Intended tool or agent invocation through the research package facade.
* **Input boundary:** web requests, records, market series, hypotheses, and evidence.
* **Functions and methods used:** one of 32 functions in `standard_tools.py`, all returning `standard_tool_response`.
* **Files involved:** `standard_tools.py`, package facade, utils standard response.
* **External dependencies:** optional `requests`, ForexFactory web pages, pandas/numpy.
* **Output boundary:** standard tool envelope.
* **Failure behaviour:** Most tool errors are converted to error envelopes; web source format/status remains provider-dependent.
* **Operational status:** **Unverified**
* **Evidence:** functions are exported and dynamically resolvable; no current API route, agent registry, scheduler, or direct caller was confirmed in accessible evidence.

```text
dynamic tool request
→ app.services.research facade
→ standard_tools function
→ standard response envelope
```

## 7. Usage and Caller Map

| Public symbol(s) | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `CanonicalOHLCVSSchema`, `CleaningAction`, `CleaningConfig`, `DataQualityReportModel`, `DatasetIssue`, `EnrichmentConfig`, `PreparedDataset` | `app/api/routes/edge.py` | Direct package import; construction/serialization | Runtime | Import block and dataset helper functions |
| `prepare_research_dataset` | `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync` and dataset endpoints | Direct function call | Runtime | Progressive automation implementation |
| `FeatureSpec`, `FeaturePipeline` | `app/api/routes/edge.py::_build_unsupervised_edge_payload` | Direct construction and `compute_batch` | Runtime | Unsupervised payload builder |
| `build_core_metric_profile` | `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync` | Direct function call then `.to_dict()` | Runtime | Core-metric automation stage |
| `SeasonalityFilters`, `run_seasonality` | `app/api/routes/edge.py::_run_edge_lab_symbol_profile_sync` | Direct construction/call | Runtime | Seasonality automation stage |
| `BootstrapConfig`, `PermutationConfig`, `DataConfig`, `EdgeLabConfig` | Edge API EDS and configuration paths | Direct construction/import | Runtime | Edge route import and EDS execution helpers |
| `EdgeResult`, `EdgeStats` | Edge API result serialization/request-response logic | Direct type use | Runtime | Edge route import and result helpers |
| `run_eds_null_baseline`, `run_eds_mean_reversion`, `run_eds_trend_persistence`, `run_eds_session` | Edge API EDS runner | Direct function calls | Runtime | EDS runner in route |
| `classify_symbol` | Edge API EDS result handling | Direct function call | Runtime | Direct import and classification path |
| `MarketStructureConfig`, `build_market_structure_profile` | Edge API market-structure and automation paths | Direct construction/call then `.to_dict()` | Runtime | Market-structure stage |
| `build_market_structure_stability_report`, `build_market_structure_robustness_report` | Edge API quality endpoints; optional research profile | Direct function calls | Runtime | Direct imports and route helpers |
| `confidence_bucket`, `label_realized_market_behavior`, `build_validation_summary` | `app/api/routes/edge.py::_refresh_market_structure_evaluations` and validation endpoint | Direct calls | Runtime | Forward evaluation flow |
| `evaluate_calibration_candidates`, `evaluate_metric_calibration_candidates`, `evaluate_profile_calibration` | Edge API calibration endpoints | Direct calls | Runtime | Direct imports and calibration flow |
| `UnsupervisedResearchConfig`, `UnsupervisedResearchService` | `app/api/routes/edge.py::_build_unsupervised_edge_payload` | Direct construction and `.analyze_frame()` | Runtime | Unsupervised stage |
| `SCORECARD_SPEC_VERSION`, `build_edge_lab_scorecard_report` | Edge API automation and snapshot metadata | Direct use/call | Runtime | Scorecard stage and metadata |
| Data validators/cleaners/enrichers | `prepare_research_dataset` | Internal direct calls | Runtime-supporting | `data/preparation.py` |
| Feature calculations/null functions/analytics metrics | EDS and market-structure modules | Internal direct calls | Runtime-supporting | Imports in `eds_*.py`, `market_structure.py` |
| Core metric calculators/registry | `build_core_metric_profile` | Internal protocol/registry calls | Runtime-supporting | `core_metrics/service.py` |
| Modeling kernels/insights | `UnsupervisedResearchService` | Internal direct calls | Runtime-supporting | `modeling/service.py` |
| `build_strategy_fit`, profile resolvers | `build_market_structure_profile` | Internal direct calls | Runtime-supporting | `market_structure.py` |
| `result_to_*`, `save_*`, profile report/snapshot helpers | No current direct caller confirmed | Export/dynamic only in inspected evidence | Unknown | Package registry; absent from inspected Edge route imports |
| 32 `standard_tools.py` functions | No current direct caller confirmed | Dynamic package export; intended agent tool | Unknown | Package export map and callable standardization |
| Many research symbols | `tests/usage/app/services/12_research.py` | Direct example imports/calls | Test/example | Example is incompatible with current API and does not establish successful use |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.services.utils.validators` | `DataSource`, OHLCV schema/normalization/validation helpers | data preparation/validation; package re-export | `data/preparation.py`, `data/validation.py`, `__init__.py` |
| `app.services.data.transforms` | `TimeframeManager` / timeframe cadence | gap and expected-timestamp validation | `data/validation.py` |
| `app.services.indicators` | SMA/EMA/WMA/RSI/ATR/Bollinger/ADL computations | `FeaturePipeline` | `features/pipeline.py` |
| `app.services.analytics` | expectancy, profit factor, win rate, MAE/MFE, drawdown/ratios; additional facade re-exports | EDS modules and package facade | imports in `eds_*.py`; `research/__init__.py` |
| `app.services.utils.logger` | structured logging | EDS/reporting | `eds_*.py`, `reporting.py` |
| `app.services.utils.security` | artifact masking support | leakage/reporting | `features/leakage.py` |
| `app.services.utils.standard` | `ToolStandardSpec`, `standard_tool_response`, callable standardization | standardized tools and package facade | `standard_tools.py`, `research/__init__.py` |
| pandas/numpy | dataframe and statistical operations | nearly all computational modules | direct imports |
| scikit-learn | `PCA`, `KMeans`, `StandardScaler` | unsupervised modeling | `modeling/unsupervised.py` |
| `requests` | HTTP GET | ForexFactory tools | runtime import in `standard_tools.py` |
| External ForexFactory pages | news, calendar, sentiment, instrument HTML | standardized fetch tools | hard-coded URLs in `standard_tools.py` |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
|---|---|---|---|
| `app/api/routes/edge.py` | 38 direct imports spanning data, EDS, metrics, market structure, modeling, scorecard, validation, and calibration | API endpoints, automation, cache, scheduler, persistence, evaluation | current production route |
| Broker/data service through Edge API | `prepare_research_dataset` indirectly receives fetched data | supply research input | route data-source creation/fetch |
| Database layer through Edge API | serialized profiles, snapshots, evaluations | persistence/cache/validation history | `DatabaseManager` calls in route |
| Dynamic service/tool consumers | any package facade name through `__getattr__` / `_common.__getattr__` | lazy service or agent-tool resolution | `research/__init__.py`, `_common.py`, `app/services/__init__.py` |
| `tests/usage/app/services/12_research.py` | legacy research exports and older signatures | example/demo | inspected file; currently broken |
| Internal research modules | data contracts, feature kernels, null models, EDS results, profile helpers | complete domain workflows | explicit internal imports |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `features/calculations.py` | `core_metrics/service.py` | returns, ROC, volatility, range, spread-adjacent calculations | both compute similar statistics independently | Formula drift and inconsistent assumptions |
| `features/calculations.py` | `FeaturePipeline` + `app.services.indicators` | moving averages, RSI, ATR, Bollinger features | pipeline delegates to indicator domain while flat research functions reimplement | Two feature sources with different naming/casing |
| `standard_tools.py` calculation functions | feature/core/seasonality/market modules | returns, volatility, ATR, ADR, sessions, seasonality, correlation, regimes | 13+ agent wrappers repeat domain calculations | Divergent results and maintenance burden |
| `config.SessionConfig` | `session_config.EDGE_SESSION_WINDOWS` | session-hour definitions | legacy config uses Asia/London/NY ranges different from Sydney/Tokyo/London/NY shared windows | Same timestamp can receive different session interpretation |
| `EdgeStats.edge_confirmed` / `verdict` | `reporting._verdict_emoji` / `result_to_summary`; `classifier.EdgeSummary.is_real` | edge confirmation semantics | reporting requires CI and p-value; classifier ignores p-value; schema applies its own rule | Contradictory user-facing decisions |
| `market_structure.py` normalization/classification helpers | `market_structure_calibration.py` and `market_structure_metric_calibration.py` | score normalization and verdict logic | separate private implementations | Calibrated result may not exactly match production scoring |
| `reporting.py` | `profile_reporting.py` | Markdown/JSON rendering and file writes | separate EDS vs profile report systems | Inconsistent timestamps, formatting, and persistence behavior |
| `profile_snapshot.py` | Edge API snapshot assembly/database persistence | construct normalized snapshot payload | route builds a different payload and saves directly | Helper can become disconnected or schema-stale |
| `_common.__getattr__` | package `__init__.__getattr__` | dynamic symbol resolution | two resolution mechanisms plus root service resolver | Ambiguous source and import-time behavior |
| `_pip_size` implementations | core metrics, market structure, validation, and other modules | infer FX pip size | repeated suffix heuristic | Instrument-class errors and inconsistent quote metadata |
| Scorecard strategy fit | `market_structure_strategy_fit.build_strategy_fit` | rank strategy archetypes | market structure and scorecard each derive fit-like outputs | Duplicate recommendations can disagree |

## 10. Unused or Questionable Items

No item is labelled dead code because a complete repository-wide indexed search was unavailable.

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `tests/usage/app/services/12_research.py` | Obsolete example; current imports/signatures/results do not match implementation | direct file inspection against current modules | **High** for incompatibility; not a dead-code claim | missing exports and numerous signature mismatches |
| `build_market_structure_research_profile` | Implemented but no direct external caller confirmed | package exports, Edge route imports/calls, internal imports | **Medium** | base builder is called; research builder is not in inspected route |
| `profile_snapshot.build_edge_profile_snapshot` | Current Edge route persists snapshots without importing this helper | package exports and full inspected route integration | **Medium** | current route constructs `snapshot_payload` and calls DB manager directly |
| `profile_reporting` public functions | Useful renderers, but no current caller confirmed | package exports and Edge route imports | **Medium** | not imported by inspected runtime route |
| `reporting` public render/save functions | Useful EDS output helpers, but no current caller confirmed | package exports, route imports, known example | **Medium** | absent from inspected route; example is broken |
| `FeaturePipeline.compute_incremental` | Stateful incremental path exists; only batch path confirmed | API route and internal imports | **Medium** | runtime route calls `compute_batch` |
| `create_config` | Convenience builder exported; direct caller not confirmed | API route, EDS modules, package map | **Medium** | runtime constructs configs directly |
| `compare_to_null`, `get_acceptance_criteria` | Implemented/exported helper functions; no direct current caller confirmed | EDS/API imports and package map | **Medium** | route calls baseline runner, not these helpers in inspected code |
| `adapt_signals_by_cluster` | End-to-end implementation exists, but current API provides no signal frame | API unsupervised payload and modeling service | **Medium** | API calls `analyze_frame` without `signal_frame` |
| `research_modeling_module` | Dynamic helper exported, but no direct caller confirmed | package/_common resolver and Edge route | **Medium** | Edge route imports service/classes directly |
| 32 `standard_tools.py` functions | Exported and standardized but no current registry, API, scheduler, or agent caller confirmed | facade map, dynamic resolver, Edge route, known example, research commits; indexed code search unavailable | **Low–Medium** | dynamic use cannot be ruled out |
| Package analytics re-exports | Research domain exposes analytics functions that EDS modules import directly from analytics | facade map and EDS imports | **Medium** | boundary convenience exists; external value not demonstrated |
| Public module constants not in package `__all__` | Importable by direct module path but inconsistently exposed | module inspection and facade map | **Medium** | constants exist but are omitted from root facade lists |

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Known usage/example workflow | Example was not updated after API evolution | Cannot serve as executable proof or onboarding reference | `tests/usage/app/services/12_research.py` vs current signatures |
| Agent-facing standardized tools | No current tool registry/agent/API caller was demonstrated | Broad API may be dormant despite appearing production-ready | `standard_tools.py` exports only in accessible evidence |
| Profile report generation | Current automation persists snapshots but does not call profile report render/save helpers | Report helpers may be manual or disconnected | Edge route imports omit `profile_reporting` |
| Snapshot normalization helper | Route bypasses `build_edge_profile_snapshot` | Two snapshot shapes can drift | current route constructs DB payload directly |
| Leakage validation | Function description implies stronger no-lookahead assurance than implementation provides | False confidence is possible | `validate_no_lookahead_features` uses heuristic correlation/alignment checks only |
| Mixed-direction EDS null comparison | EDS-1/EDS-2/EDS-3 compare mixed BUY/SELL samples against hard-coded BUY nulls | p-values/thresholds may not match tested trade direction | `side="BUY"` in EDS null calls |
| EDS-0 configuration | Accepted bootstrap config and some null-model options are not materially used by baseline logic | Config surface overstates behavior | `run_eds_null_baseline` and `NullModelsConfig` |
| Session configuration | Two conflicting session models remain active | Seasonality and EDS-3 can analyze different windows | `config.SessionConfig` vs `session_config.py` |
| Custom schema support in core metrics | Context carries schema but several calculators hard-code title-case columns | Custom schema can fail after otherwise valid preparation | `_point_columns` and range/candle calculators |
| In-sample cluster adaptation | Clusters and their forward performance are learned/evaluated on the same dataset | Signal filtering is research evidence, not validated out-of-sample behavior | modeling insight workflow |
| Error normalization | Some top-level paths return skipped/error envelopes; others propagate exceptions or NaNs | Callers need capability-specific handling | data prep, EDS, modeling, standard tools differ |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-RESEARCH-001` | Dynamic facade is excessively broad and boundary-mixed | `app/services/research/__init__.py` | 207 names obscure ownership and make import behavior non-obvious | local, analytics, validator, and standardized-tool exports share one resolver |
| `V1-ISSUE-RESEARCH-002` | Root `__all__` and lazy-resolvable API are not the same surface | `research/__init__.py` | Star imports, introspection, documentation, and direct imports can disagree | many classes/configs resolve through `__getattr__` but are omitted from `__all__` |
| `V1-ISSUE-RESEARCH-003` | Callable behavior is modified at import time | `research.__getattr__` | Hidden wrapper can alter signatures/metadata/error behavior and complicate debugging | every non-type callable is passed through callable standardization and cached |
| `V1-ISSUE-RESEARCH-004` | Very large files combine unrelated responsibilities | `standard_tools.py`, `market_structure.py`, `scorecard.py`, `seasonality.py` | High change coupling and difficult isolated validation | approximately 2207, 2063, 876, and 691 lines respectively |
| `V1-ISSUE-RESEARCH-005` | Duplicate calculation stacks | features, core metrics, standard tools, indicators, analytics | Formula and naming drift | repeated returns/ATR/volatility/regime/session functions |
| `V1-ISSUE-RESEARCH-006` | Conflicting session definitions | `config.SessionConfig`, `session_config.py` | EDS and seasonality may label identical bars differently | different London/NY/Asia-Sydney-Tokyo windows |
| `V1-ISSUE-RESEARCH-007` | Edge-confirmation criteria are inconsistent | `results_schema.py`, `reporting.py`, `classifier.py` | Same result may be confirmed, potential, or weak depending on consumer | p-value is required in reporting, ignored in classifier |
| `V1-ISSUE-RESEARCH-008` | EDS null direction is hard-coded to BUY | `eds_mean_reversion.py`, `eds_trend_persistence.py`, `eds_session.py` | Statistical comparison can be invalid for SELL/mixed samples | `side="BUY"` passed to null generators |
| `V1-ISSUE-RESEARCH-009` | Leakage guardrail is weaker than its stated purpose | `features/leakage.py::validate_no_lookahead_features` | May certify features without recomputation or provenance proof | heuristic checks only |
| `V1-ISSUE-RESEARCH-010` | Current example is stale and broken | `tests/usage/app/services/12_research.py` | Misleads users and cannot demonstrate a working workflow | missing symbols and wrong signatures/result fields |
| `V1-ISSUE-RESEARCH-011` | Core metric schema abstraction is inconsistently honored | `core_metrics/service.py` | Non-default schemas can fail | `_point_columns` and multiple calculators hard-code canonical title-case names |
| `V1-ISSUE-RESEARCH-012` | Data casing conventions differ | data/core/EDS use `Open`/`High`/...; modeling expects `open`/`high`/... | Direct consumers must know and implement adapters | API explicitly creates a lower-case frame before modeling |
| `V1-ISSUE-RESEARCH-013` | Direct provider coupling in web research tools | `standard_tools.py` | HTML/URL changes can break four tools; raw pages lack stable contract | hard-coded ForexFactory URLs and direct `requests.get` |
| `V1-ISSUE-RESEARCH-014` | Calibration reimplements production scoring logic | calibration modules vs `market_structure.py` | Candidate accuracy may not exactly reflect production verdict behavior | duplicate normalization, weighting, and classification helpers |
| `V1-ISSUE-RESEARCH-015` | Config fields and parameters overstate used behavior | `create_config`, `run_eds_null_baseline`, EDS/session configs | Callers can believe a setting is active when it is ignored | limited override prefixes, unused bootstrap/config options |
| `V1-ISSUE-RESEARCH-016` | Reporting and snapshot paths are fragmented | `reporting.py`, `profile_reporting.py`, `profile_snapshot.py`, Edge API persistence | Multiple schemas/timestamps/save paths can drift | current route bypasses some helpers |
| `V1-ISSUE-RESEARCH-017` | Timestamp conventions are inconsistent | result/report modules | Reproducibility and timezone interpretation are weakened | naive `datetime.now()` / local-formatted timestamps coexist with UTC API metadata |
| `V1-ISSUE-RESEARCH-018` | In-sample cluster performance can be mistaken for validated edge | modeling insight/adaptation functions | Advisory signal suppression can overfit | clustering and forward-return scoring use the same feature frame |
| `V1-ISSUE-RESEARCH-019` | Mutable module-level containers expose shared state | calculator list, profile/session tables | Accidental mutation can alter later runs | `DEFAULT_CALCULATORS`, profile overrides, session mappings |
| `V1-ISSUE-RESEARCH-020` | Error contracts are inconsistent | data, EDS, modeling, standard tools, scorecard | Integrators must handle exceptions, NaNs, `None`, `SKIPPED`, and envelopes | capability-specific failure behavior |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-RESEARCH-001` | Canonical research dataset contracts | `data/models.py` | 001–008 | Used | Essential | Shared schema/report/prepared dataset |
| `V1-CAP-RESEARCH-002` | Data quality validation | `validate_dataset` | 001 | Used | Essential | Index, OHLC, gap, spread, volume checks |
| `V1-CAP-RESEARCH-003` | Configurable data cleaning | `clean_dataset` | 001 | Used | Essential | Records cleaning actions |
| `V1-CAP-RESEARCH-004` | Research data enrichment | `enrich_dataset` | 001 | Used | Essential | Quote, candle, return, calendar/session metadata |
| `V1-CAP-RESEARCH-005` | Provider-to-prepared-data orchestration | `prepare_research_dataset` | 001, 007 | Used | Essential | Confirmed API caller |
| `V1-CAP-RESEARCH-006` | Flat numerical feature library | `features/calculations.py` | 004, 005 | Used internally | Supporting | Broad but overlapping |
| `V1-CAP-RESEARCH-007` | Versioned feature pipeline | `FeaturePipeline` | 006 | Used | Essential | Batch path confirmed; incremental unverified |
| `V1-CAP-RESEARCH-008` | Leakage/time-split/masking helpers | `features/leakage.py` | Supporting/reporting | Possibly used | Useful/Questionable | Leakage check is heuristic |
| `V1-CAP-RESEARCH-009` | Core market metric profile | `core_metrics/*` | 002, 007 | Used | Essential | Seven metric families |
| `V1-CAP-RESEARCH-010` | Statistical null baselines | `null_models.py`, `eds_null_models.py` | 004 | Used | Essential | Random-entry/R-space/shuffle |
| `V1-CAP-RESEARCH-011` | Mean-reversion edge detector | `run_eds_mean_reversion` | 004, 005 | Used | Essential | Confirmed API and market-structure caller |
| `V1-CAP-RESEARCH-012` | Trend-persistence edge detector | `run_eds_trend_persistence` | 004, 005 | Used | Essential | Confirmed API and market-structure caller |
| `V1-CAP-RESEARCH-013` | Session breakout/fade edge detector | `run_eds_session` | 004 | Used | Essential | FDR-corrected multi-hypothesis output |
| `V1-CAP-RESEARCH-014` | Edge classification | `classify_symbol` | 004 | Used | Useful | Criteria inconsistent with reporting |
| `V1-CAP-RESEARCH-015` | Seasonality and opportunity analysis | `run_seasonality` | 003, 007 | Used | Essential | Calendar/session/hour heatmaps/rankings |
| `V1-CAP-RESEARCH-016` | Market-structure profile | `build_market_structure_profile` | 005, 007 | Used | Essential | Swings, legs, ranges, distributions, regimes |
| `V1-CAP-RESEARCH-017` | Market-structure strategy fit | `build_strategy_fit` | 005 | Used internally | Useful | Five archetypes |
| `V1-CAP-RESEARCH-018` | Stability and parameter robustness | stability/robustness builders | 005, 008 | Used | Useful | Repeated high-cost profile runs |
| `V1-CAP-RESEARCH-019` | Forward-outcome validation | validation module | 008 | Used | Useful | Persisted by API caller |
| `V1-CAP-RESEARCH-020` | Verdict and metric calibration | three calibration modules | 008 | Used | Useful | Grid-search against realized labels |
| `V1-CAP-RESEARCH-021` | Unsupervised feature construction | `build_market_regime_feature_frame` | 006 | Used | Essential | Lower-case schema |
| `V1-CAP-RESEARCH-022` | PCA and K-Means modeling | `run_pca`, `cluster_feature_space` | 006 | Used | Essential | scikit-learn |
| `V1-CAP-RESEARCH-023` | Unsupervised insight report | modeling insights/service | 006, 007 | Used | Essential | Risk factors, cluster performance, context |
| `V1-CAP-RESEARCH-024` | Advisory cluster-based signal suppression | `adapt_signals_by_cluster` | 006 | Possibly used | Questionable | No current signal-frame caller confirmed; in-sample |
| `V1-CAP-RESEARCH-025` | Deterministic Edge Lab scorecard | `build_edge_lab_scorecard_report` | 007 | Used | Essential | Confirmed API caller |
| `V1-CAP-RESEARCH-026` | Full profile automation/caching/scheduling | research outputs orchestrated by `app/api/routes/edge.py` | 007 | Used | Essential | Orchestration resides outside domain |
| `V1-CAP-RESEARCH-027` | EDS Markdown/JSON reports | `reporting.py` | Reporting | Possibly used | Useful | No current caller confirmed |
| `V1-CAP-RESEARCH-028` | Profile/dashboard/comparison reports | `profile_reporting.py` | Reporting | Possibly used | Useful | No current caller confirmed |
| `V1-CAP-RESEARCH-029` | Profile snapshot normalization | `build_edge_profile_snapshot` | Snapshot | Possibly used | Questionable | Current route appears to bypass it |
| `V1-CAP-RESEARCH-030` | Standardized web research fetch tools | four ForexFactory functions | 009 | Possibly used | Questionable | Direct provider coupling |
| `V1-CAP-RESEARCH-031` | Standardized news/event interpretation tools | six standard tools | 009 | Possibly used | Useful if connected | No caller/registry confirmed |
| `V1-CAP-RESEARCH-032` | Standardized market calculation/detection tools | 13 standard tools | 009 | Possibly used | Questionable | Significant overlap |
| `V1-CAP-RESEARCH-033` | Hypothesis and evidence guardrails | nine standard tools | 009 | Possibly used | Useful if connected | No caller/registry confirmed |
| `V1-CAP-RESEARCH-034` | Dynamic package/service symbol resolution | package facade and `_common.py` | All | Used | Supporting | Powerful but obscures boundary |
| `V1-CAP-RESEARCH-035` | Analytics and validator convenience re-exports | root package facade | External convenience | Possibly used | Questionable | Cross-domain ownership leakage |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The strongest demonstrated Version 1 value is the operational Edge Lab chain used by `app/api/routes/edge.py`:

* canonical dataset preparation with quality evidence;
* core metrics and session/calendar opportunity analysis;
* EDS null, mean-reversion, trend-persistence, and session tests;
* market-structure profiling with swings, legs, range behavior, distributions, regimes, and strategy fit;
* unsupervised PCA/K-Means structure analysis;
* deterministic scorecard/readiness output;
* forward validation and calibration;
* caching, partial recomputation, scheduled runs, and database snapshots at the API boundary.

These capabilities have confirmed runtime callers and coherent input/output paths.

### Behaviour that exists but is disconnected or uncertain

The standardized agent tools, report renderers/savers, profile snapshot normalizer, incremental feature pipeline, research-mode market-structure builder, cluster-based signal adaptation, and several convenience helpers are implemented but lack a confirmed current caller in accessible evidence. Dynamic resolution means they may still be invoked indirectly, so they are **Possibly used**, not unused.

### Likely dead weight

No symbol is formally classified as dead code because the required high-confidence repository-wide search could not be completed. The stale usage example is confidently obsolete, but that conclusion applies to the example, not necessarily to every symbol it mentions.

The highest-questionable areas are:

* duplicate agent-facing calculation wrappers in `standard_tools.py`;
* bypassed snapshot/report helpers;
* convenience re-exports from analytics and validators;
* incremental or research-only variants without demonstrated callers;
* config parameters that are accepted but not used.

### Duplicated responsibilities

Calculation, session, verdict, calibration, reporting, pip-size, and dynamic-resolution responsibilities are duplicated across multiple files. These duplications create measurable risk of different outputs for the same conceptual question.

### Important uncertainties

* Complete unit/integration test inventory and current pass/fail state.
* Additional dynamic agent/tool registrations outside the inspected files.
* Current callers of reporting, snapshot, and standardized tool functions.
* Whether any direct-module imports bypass the package facade.
* Whether all 46 reconstructed files are the complete directory tree.

### Areas requiring manual confirmation

1. Enumerate `tests/unit/app/services/research` and run the tests.
2. Run a repository-native search for every root export and `app.services.research` import.
3. Inspect agent/tool registries, workflow YAML/JSON, scheduler configuration, and string-based registrations for the 32 standardized tools.
4. Confirm whether report/snapshot helper modules are used by UI, scripts, notebooks, or external jobs.
5. Execute the main Edge API workflow with representative MT5 and Dukascopy inputs to verify runtime behavior, not only call-path completeness.

### Final validation result

* Every Python file discoverable from the current export registry and direct import graph is represented: **46 files**.
* Every documented package export in the inspected `__init__.py` files was checked against a mapped module or re-export source.
* Root and subpackage `__init__.py` behavior was inspected.
* The production Edge API caller and known usage example were inspected.
* Dynamic service resolution was inspected.
* Inbound and outbound domain surfaces are summarized.
* Workflows are based on actual calls, not intended documentation.
* Runtime usage is distinguished from test/example and uncertain dynamic usage.
* Uncertain findings are labelled.
* No Version 2 design was invented.
* No code was changed.
