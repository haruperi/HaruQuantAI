# Research Domain — Capability Feature Extraction (from `12-research.md`)

Source: `docs/dev/phase-implementation-plan/12-research.md`. Module paths follow the plan's target tree under `app.services.research`. Test modules are omitted.

---

## FEAT-RES-01: Official Research Tool Surface (app.services.research.service)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `prepare_research_dataset_tool(request: PrepareDatasetRequest, request_id: str) -> ResearchEnvelope` | Dataset preparation tool; state-mutating only through the configured data gateway. | Missing |
| `run_edge_study_tool(request: EdgeStudyRequest, request_id: str) -> ResearchEnvelope` | Pure edge-study computation at a tool boundary; no trade/risk mutation. | Missing |
| `run_unsupervised_research_tool(request: UnsupervisedResearchRequest, request_id: str) -> ResearchEnvelope` | Seeded unsupervised research (PCA/clustering) tool. | Missing |
| `fetch_research_feed_tool(request: ExternalResearchRequest, request_id: str) -> ResearchEnvelope` | External provider access only through an approved adapter. | Missing |
| `build_research_report_tool(request: ResearchReportRequest, request_id: str) -> ResearchEnvelope` | Report building; read-only unless explicit persistence is selected. | Missing |

## FEAT-RES-02: Research Contracts, Envelopes, Errors, and Catalog (app.services.research.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_config(overrides: Mapping[str, object] \| None = None) -> EdgeLabConfig` | Validated immutable Edge Lab configuration with approved defaults (with config and resource-limit validators). | Missing |
| `canonicalize_research_model(value: ResearchSerializable) -> dict[str, object]` | JSON-safe, schema-versioned canonical serialization (with schema validation and reproducibility metadata). | Missing |
| `build_research_success(data: ResearchPayload, audit: AuditMetadata, timing: TimingMetadata) -> ResearchEnvelope` | Schema-versioned read-only success envelopes (with redacted error envelopes and fail-closed validation). | Missing |
| `classify_research_error(error: Exception, context: ErrorContext) -> ResearchErrorDetail` | Deterministic research error codes (with minimum-sample enforcement and retryability classification). | Missing |
| `validate_contract_first_readiness(catalog: CapabilityCatalog, approved_slice: ImplementationSlice) -> ContractReadinessReport` | Contract-first gate: every public capability needs schemas, error behavior, examples, and tests (with capability lookup and glossary). | Missing |

## FEAT-RES-03: Research Policies — Limits, Advisory Guard, Redaction, Reproducibility (app.services.research.policies)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_workload_size(rows: int, limits: ResearchResourceLimits) -> None` | Reject oversized requests before expensive work (with execution-budget checks and typed limit errors). | Missing |
| `assert_research_action_is_read_only(action: str) -> None` | Reject any live-trading, risk-mutation, or execution-routing action. | Missing |
| `decorate_advisory_evidence(payload: EvidencePayload) -> AdvisoryEvidencePayload` | Label observations/assumptions/warnings as non-approving advisory evidence (with governed-promotion boundary verification). | Missing |
| `mask_research_artifact(artifact: Mapping[str, object], policy: MaskingPolicy) -> dict[str, object]` | Non-mutating artifact masking with safe JSON output and unsafe-payload rejection. | Implemented |
| `resolve_effective_seed(explicit_seed: int \| None, config_seed: int \| None) -> int` | Deterministic seed selection with reproducibility manifest and input hashing. | Missing |
| `record_research_outcome(event: ResearchLogEvent) -> None` | Structured redacted observability events. | Missing |

## FEAT-RES-04: Dataset Preparation, Enrichment, and Leakage Controls (app.services.research.core)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_dataset(data: pd.DataFrame, schema: CanonicalOHLCVSSchema, source: DataSource) -> DataQualityReportModel` | Fatal-vs-warning dataset quality validation. | Implemented |
| `clean_dataset(data: pd.DataFrame, config: CleaningConfig) -> tuple[pd.DataFrame, DataQualityReportModel]` | Deterministic cleaning returning a new frame with recorded actions. | Implemented |
| `prepare_research_dataset(raw: pd.DataFrame \| DataSource, config: EdgeLabConfig) -> PreparedDataset` | End-to-end preparation orchestration (gateway-invoking only when configured). | Implemented |
| `enrich_dataset(data: pd.DataFrame, config: EnrichmentConfig) -> pd.DataFrame` | Copy-returning enrichment (with session tagging and enrichment metadata). | Implemented |
| `validate_no_lookahead_features(data: pd.DataFrame, metadata: FeatureMetadata, policy: LeakagePolicy) -> LeakageReport` | Lookahead-feature detection without input mutation. | Implemented |
| `enforce_time_split(data: pd.DataFrame, spec: TimeSplitSpec) -> TimeSplitResult` | Chronological train/validation/test partitioning (with data-snooping risk assessment). | Implemented |
| `compute_session_statistics(data: pd.DataFrame, session: SessionWindow) -> SessionStatistics` | Session statistics, seasonality runs, and session labeling helpers. | Missing |

## FEAT-RES-05: Core Metric Calculators and Registry (app.services.research.core.metrics)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_core_metric_profile(dataset: PreparedDataset, config: CoreMetricConfig) -> CoreMetricProfile` | Aggregate core metric profile across returns, ROC, candle, range, volatility, spread, and volume-activity calculators. | Implemented |
| `build_default_registry() -> MetricRegistry` | Deterministic calculator registry (with resolution and validation, under the `MetricCalculator` protocol). | Implemented |
| `normalize_metric_value(name: str, value: float \| None, metadata: Mapping[str, object]) -> MetricValue` | Normalized metric values with context validation. | Missing |

## FEAT-RES-06: Research Feature Library (app.services.research.core.features)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `log_returns(close: pd.Series) -> pd.Series` | Returns family: log/simple returns, RSI, rate-of-change, momentum. | Implemented |
| `forward_returns(close: pd.Series, horizon: int) -> pd.Series` | Research-only forward labels (with forward MFE/MAE excursions). | Implemented |
| `atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series` | Volatility family: ATR/ATR%, z-score, percent rank, Bollinger bands/width/%B, rolling percentiles. | Missing |
| `donchian_channel(high: pd.Series, low: pd.Series, window: int) -> DonchianChannel` | Market-structure family: Donchian, Hurst (point and rolling), pivots, ADR. | Missing |
| `detect_market_regime(features: FeatureSetFrame, config: RegimeFeatureConfig) -> pd.Series` | Volatility/trend regime detection with regime feature frames. | Missing |

## FEAT-RES-07: Edge Discovery Studies and Null-Hypothesis Testing (app.services.research.studies)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_eds_session(dataset: PreparedDataset, config: SessionEdgeConfig) -> EdgeResult` | Session edge-discovery study (with null-baseline, mean-reversion, and trend-persistence studies). | Missing |
| `run_session_breakout_strategy(dataset: PreparedDataset, config: SessionEdgeConfig) -> EdgeResult` | Evaluation-only session breakout/fade studies with edge classification; never emits trade orders. | Missing |
| `compare_to_null(observed: float, null_distribution: np.ndarray) -> NullComparison` | Null-model comparison with acceptance criteria and percentile/statistics helpers. | Implemented |
| `block_bootstrap_ci(values: np.ndarray, statistic: StatisticFn, config: BootstrapConfig, seed: int) -> ConfidenceInterval` | Seeded block-bootstrap CIs and distributions (with permutation tests). | Implemented |
| `random_entry_null(returns: np.ndarray, config: NullModelsConfig, seed: int) -> NullDistribution` | Null models: random entry, R-space, session-randomized, shuffled returns. | Implemented |
| `benjamini_hochberg(p_values: Sequence[float], alpha: float) -> MultipleComparisonResult` | Multiple-comparison corrections (with Holm–Bonferroni). | Implemented |

## FEAT-RES-08: Market-Structure Classification, Calibration, and Profiles (app.services.research.studies.market_structure)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `classify_with_candidate(dataset: PreparedDataset, candidate: MarketStructureCalibrationCandidate) -> ClassificationResult` | Candidate-based market-structure classification (with timeframe buckets, symbol classes, profile resolution/overrides, confidence buckets, and realized-behavior labeling). | Missing |
| `build_calibration_grid(config: MarketStructureConfig) -> tuple[MarketStructureCalibrationCandidate, ...]` | Calibration grids and candidate/metric/profile evaluation. | Missing |
| `build_market_structure_profile(dataset: PreparedDataset, config: MarketStructureConfig) -> MarketStructureProfile` | Profile construction with robustness, stability, and validation-summary reports. | Missing |
| `build_strategy_fit(profile: MarketStructureProfile, strategy_metadata: Mapping[str, object]) -> StrategyFitAdvisory` | Explicitly non-approving strategy-fit advisory. | Missing |
| `generate_research_hypothesis(inputs: HypothesisInputs) -> ResearchHypothesis` | Hypothesis generation with evidence packs and news parsing. | Missing |

## FEAT-RES-09: Unsupervised Research — PCA and Clustering (app.services.research.studies.unsupervised)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_unsupervised_research(request: UnsupervisedResearchRequest) -> UnsupervisedResearchResult` | Deterministic seeded unsupervised computation (with request validation and run metadata). | Missing |
| `run_pca(features: FeatureSetFrame, config: UnsupervisedResearchConfig) -> PcaModelResult` | PCA with risk-factor identification. | Missing |
| `cluster_feature_space(features: FeatureSetFrame, config: UnsupervisedResearchConfig, seed: int \| None = None) -> ClusterModelResult` | Clustering with copy-returning label attachment, forward-return analysis, cluster outperformance, and advisory-only signal adaptation. | Missing |
| `build_unsupervised_insight_report(result: UnsupervisedResearchResult) -> UnsupervisedInsightReport` | Insight-report composition. | Missing |

## FEAT-RES-10: External Research Feed Providers (app.services.research.providers)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ResearchFeedProvider` (Protocol) | Injectable boundary isolating all external feed I/O (with provider-policy validation and HTTP rate-limit classification). | Missing |
| `fetch_forexfactory_news(request: ForexFactoryNewsRequest, provider: ResearchFeedProvider) -> ResearchEnvelope` | Retry/rate-limit-bounded ForexFactory news fetching (with instrument-page fetch and pure payload normalization). | Missing |

## FEAT-RES-11: Interactive Analysis and Calendar Advisory (app.services.research.interactive)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `parse_calendar_events(items: Sequence[Mapping[str, object]]) -> tuple[CalendarEvent, ...]` | Calendar/sentiment parsing with symbol filtering and impact classification. | Missing |
| `create_news_blackout_windows(events: Sequence[CalendarEvent], policy: NewsWindowPolicy) -> tuple[AdvisoryBlackoutWindow, ...]` | Advisory-only news blackout windows; produces no live control. | Missing |
| `calculate_returns(prices: pd.Series) -> pd.Series` | Interactive analysis family: volatility, ATR, ADR, spread/session/seasonality statistics, correlation matrix. | Missing |
| `detect_trend_strength(data: pd.DataFrame, config: TrendStrengthConfig) -> TrendStrengthResult` | Condition detection: trend strength, mean-reversion, breakout. | Missing |
| `score_research_hypothesis(evidence: ResearchEvidencePack) -> HypothesisScore` | Hypothesis scoring with sample-size, lookahead-risk, testability, and contradiction checks. | Missing |

## FEAT-RES-12: Analytics Adapter (app.services.research.adapters.analytics)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `sharpe_ratio(result: TradingResult) -> float \| None` | Delegation-only metric access via documented Analytics public contracts: Sharpe, Sortino, Calmar, expectancy, max drawdown, MAE/MFE medians, profit factor, win rate. | Missing |

## FEAT-RES-13: Research Reports and Safe Persistence (app.services.research.reports)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `result_to_markdown(result: EdgeResult) -> str` | Report rendering: markdown/JSON summaries, multi-symbol reports, printable summaries. | Missing |
| `build_edge_profile_snapshot(tabs: ProgressiveEdgeLabResults) -> EdgeProfileSnapshot` | Edge profile snapshots with profile/dashboard summaries, JSON/markdown snapshot reports, comparisons, and scorecard reports. | Missing |
| `build_artifact_manifest(payload: Mapping[str, object], context: ArtifactContext) -> ResearchArtifactManifest` | Manifests with required hashes, versions, sources, seed, timezone, and assumptions. | Missing |
| `save_json(result: EdgeResult, path: SafeOutputPath, overwrite: bool) -> PersistedArtifact` | Masked, atomic-rename artifact persistence (markdown/JSON variants) — the only module allowed to write research files. | Missing |
| `validate_output_path(path: Path, policy: OutputPolicy) -> SafeOutputPath` | Reject traversal, disallowed roots, and accidental overwrite. | Missing |

## FEAT-RES-14: Research Governance Layers (app.services.research.governance)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `classify_research_capability(name: str) -> ResearchLayer` | Classify capabilities as `core` or `edge_lab`. | Missing |
| `validate_research_core_evidence_pack(pack: ResearchEvidencePack) -> None` | Canonical-contract checks before downstream consumption (with `assert_edge_lab_read_only`). | Missing |

---

**Note:** research is strictly advisory and read-only: it cannot execute orders, mutate risk, authorize promotion, or activate live execution; all randomness is seeded for reproducibility; `providers/` is the only network-capable location and `reports/persistence.py` the only file writer.
