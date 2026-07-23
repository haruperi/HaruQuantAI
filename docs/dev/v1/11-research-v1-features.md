## FEAT-RES-01: Flat public research tools (app.services.research._common)

| Function | Purpose |
|----------|---------|
| `research_modeling_module() -> ModuleType` | Return the research modeling service module. |


## FEAT-RES-02: Edge Classification Logic (app.services.research.classifier)

| Function | Purpose |
|----------|---------|
| `EdgeClass` (model) | Enumeration of edge classifications. |
| `EdgeSummary.is_real -> bool` | Check if edge is statistically real. |
| `EdgeSummary.is_positive -> bool` | Check if expectancy is positive. |
| `classify_symbol(mr: EdgeResult \| None, tp: EdgeResult \| None, *, delta_r: float = DEFAULT_DELTA_R, strong_r: float = DEFAULT_STRONG_R) -> ClassificationResult` | Classify a symbol based on Mean Reversion (MR) and Trend Persistence (TP) edges. |


## FEAT-RES-03: Edge Lab configuration dataclasses (app.services.research.config)

| Function | Purpose |
|----------|---------|
| `DataConfig` (model) | Configuration for data loading and preprocessing. |
| `SessionConfig` (model) | FX session boundaries in UTC hours. |
| `BootstrapConfig` (model) | Block bootstrap configuration for autocorrelation-aware inference. |
| `PermutationConfig` (model) | Permutation/randomization test configuration. |
| `NullModelsConfig` (model) | EDS-0: Null Models / Baseline configuration. |
| `MeanReversionConfig` (model) | EDS-1: Mean Reversion Detector configuration. |
| `TrendPersistenceConfig` (model) | EDS-2: Trend Persistence Detector configuration. |
| `MarketStructureConfig` (model) | Market Structure engine configuration. |
| `SessionEdgeConfig` (model) | EDS-3: Session Edge Detector configuration. |
| `EdgeLabConfig` (model) | Top-level configuration for Edge Lab. |
| `create_config(symbol: str, timeframe: str = 'M15', end_pos: int = 5000, **overrides) -> EdgeLabConfig` | Create EdgeLabConfig with common defaults. |


## FEAT-RES-04: Base types for Edge Core Metric calculators (app.services.research.core_metrics.base)

| Function | Purpose |
|----------|---------|
| `MetricValue` (model) | Normalized metric output. |
| `MetricCalculator.compute(context: MetricContext) -> list[MetricValue]` | Compute normalized metrics for one family. |


## FEAT-RES-05: Registry for Edge Core Metric calculators (app.services.research.core_metrics.registry)

| Function | Purpose |
|----------|---------|
| `MetricRegistry.get(family: str) -> MetricCalculator` | Run get processing. |
| `MetricRegistry.all() -> list[MetricCalculator]` | Run all processing. |
| `MetricRegistry.families() -> list[str]` | Run families processing. |
| `MetricRegistry.from_calculators(calculators: Iterable[MetricCalculator]) -> MetricRegistry` | Run from calculators processing. |


## FEAT-RES-06: Data preparation and validation service for Research Edge Lab (app.services.research.data)

| Function | Purpose |
|----------|---------|
| `DatasetIssue` (model) | Represents a detected dataset quality issue. |
| `CleaningAction` (model) | Represents a cleaning action applied to research data. |
| `DataQualityReportModel` (model) | Summarizes validation issues and cleaning actions for a dataset. |
| `PreparedDataset` (class) | Carries cleaned, validated, enriched data with its quality report and metadata. |
| `CoreMetricProfile` (model) | Core dataset metrics profile. |


## FEAT-RES-07: Cleaning policies for analysis-ready OHLCVS datasets (app.services.research.data.cleaning)

| Function | Purpose |
|----------|---------|
| `CleaningConfig` (model) | Cleaning policies for OHLCVS preparation. |
| `clean_dataset(df: pd.DataFrame, *, report: DataQualityReportModel, schema: CanonicalOHLCVSSchema \| None = None, config: CleaningConfig \| None = None) -> pd.DataFrame` | Normalize timezone, handle missing bars, weekends/holidays, and spread anomalies. |


## FEAT-RES-08: Dataset enrichment for Edge Lab analysis-ready OHLCVS frames (app.services.research.data.enrichment)

| Function | Purpose |
|----------|---------|
| `EnrichmentConfig` (model) | Configuration for deterministic dataset enrichment. |
| `enrich_dataset(df: pd.DataFrame, *, schema: CanonicalOHLCVSSchema \| None = None, config: EnrichmentConfig \| None = None) -> pd.DataFrame` | Add pip metadata, bar geometry, returns, labels, and calendar/session fields. |


## FEAT-RES-09: Models for Edge Lab dataset validation, cleaning, and enrichment (app.services.research.data.models)

| Function | Purpose |
|----------|---------|
| `CanonicalOHLCVSSchema.price_columns -> list[str]` | Run price columns processing. |
| `CanonicalOHLCVSSchema.required_columns -> list[str]` | Run required columns processing. |
| `DataQualityReportModel.is_valid -> bool` | Run is valid processing. |
| `DataQualityReportModel.add_issue(issue: DatasetIssue) -> None` | Run add issue processing. |
| `DataQualityReportModel.add_check(name: str) -> None` | Run add check processing. |
| `DataQualityReportModel.add_action(action: CleaningAction) -> None` | Run add action processing. |


## FEAT-RES-10: Research dataset preparation pipeline (app.services.research.data.preparation)

| Function | Purpose |
|----------|---------|
| `prepare_research_dataset(source: DataSource, symbol: str, timeframe: str, start_pos: int, end_pos: int, *, exclude_last_bar: bool = True, schema: OHLCVSchema \| None = None, cleaning: Any \| None = None, enrichment: Any \| None = None) -> PreparedDataset` | Fetch, clean, validate, and enrich a research-ready OHLCVS dataset. |


## FEAT-RES-11: Validation helpers for analysis-ready OHLCVS datasets (app.services.research.data.validation)

| Function | Purpose |
|----------|---------|
| `validate_dataset(df: pd.DataFrame, *, schema: CanonicalOHLCVSSchema \| None = None, timeframe: str \| None = None) -> DataQualityReportModel` | Validate schema, continuity, OHLC logic, duplicates, spread, and volume. |


## FEAT-RES-12: EDS-1 mean reversion edge discovery strategy (app.services.research.eds_mean_reversion)

| Function | Purpose |
|----------|---------|
| `run_eds_mean_reversion(df: pd.DataFrame, symbol: str, timeframe: str, cfg: MeanReversionConfig, boot: BootstrapConfig, perm: PermutationConfig, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> EdgeResult` | EDS-1 Mean Reversion Detector: compression + z-score fade. |


## FEAT-RES-13: EDS-0: Null Models / Baseline Detector (app.services.research.eds_null_models)

| Function | Purpose |
|----------|---------|
| `run_eds_null_baseline(df: pd.DataFrame, symbol: str, timeframe: str, cfg: NullModelsConfig, boot: BootstrapConfig, perm: PermutationConfig, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> EdgeResult` | EDS-0: Establish null model baselines. |
| `compare_to_null(observed_expectancy: float, null_result: EdgeResult, hold_bars: int = 32, side: str = 'BUY') -> dict[str, Any]` | Compare observed expectancy to null distribution. |


## FEAT-RES-14: EDS-3: Session Edge Detector (app.services.research.eds_session)

| Function | Purpose |
|----------|---------|
| `compute_session_statistics(df: pd.DataFrame, session: str, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> dict[str, float]` | Compute detailed statistics for a specific session. |
| `run_session_breakout_strategy(df: pd.DataFrame, session: str, opening_range_bars: int, hold_bars: int, k_stop_atr: float, atr_series: pd.Series, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> list[TradeSample]` | Run opening range breakout strategy for a session. |
| `run_session_fade_strategy(df: pd.DataFrame, session: str, hold_bars: int, k_stop_atr: float, atr_series: pd.Series, zscore_threshold: float = 2.0, close_col: str = 'Close') -> list[TradeSample]` | Run mean-reversion fade strategy within session. |
| `run_eds_session(df: pd.DataFrame, symbol: str, timeframe: str, cfg: SessionEdgeConfig, sessions_cfg: SessionConfig, boot: BootstrapConfig, perm: PermutationConfig, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> EdgeResult` | EDS-3: Session Edge Detector. |


## FEAT-RES-15: EDS-2 trend persistence edge discovery strategy (app.services.research.eds_trend_persistence)

| Function | Purpose |
|----------|---------|
| `run_eds_trend_persistence(df: pd.DataFrame, symbol: str, timeframe: str, cfg: TrendPersistenceConfig, boot: BootstrapConfig, perm: PermutationConfig, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> EdgeResult` | EDS-2 Trend Persistence Detector: high-ATR breakout follow-through. |


## FEAT-RES-16: Deterministic error-code mapping for the research service boundary (app.services.research.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `ResearchError` (exception) | Base exception for research domain errors. |
| `ResearchValidationError` (exception) | Validation exception for research domain. |
| `to_research_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Research error payload. |


## FEAT-RES-17: Feature engineering service for Research Edge Lab (app.services.research.features)

| Function | Purpose |
|----------|---------|
| `log_returns(close: pd.Series) -> pd.Series` | Compute log returns from close prices. |
| `simple_returns(close: pd.Series) -> pd.Series` | Compute simple (arithmetic) returns from close prices. |
| `zscore(close: pd.Series, window: int = 20) -> pd.Series` | Compute a close-price z-score relative to a moving average and standard deviation. |
| `percent_rank(series: pd.Series, window: int = 20) -> pd.Series` | Compute rolling percentile rank values. |
| `rolling_percentile_rank(series: pd.Series, window: int = 20) -> pd.Series` | Compute rolling percentile rank for a supplied series. |
| `atr(df: pd.DataFrame, n: int, high_col: str = 'High', low_col: str = 'Low', close_col: str = 'Close') -> pd.Series` | Average True Range. |
| `atr_percent(df: pd.DataFrame, n: int, high_col: str = 'High', low_col: str = 'Low', close_col: str = 'Close') -> pd.Series` | ATR as percentage of close price. |
| `bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]` | Compute Bollinger-style upper, middle, and lower bands. |
| `bb_width(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series` | Compute Bollinger Band width. |
| `bb_percent_b(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series` | Compute Bollinger Band percent-B. |
| `rsi(close: pd.Series, window: int = 14) -> pd.Series` | Compute Relative Strength Index. |
| `rate_of_change(close: pd.Series, window: int = 14) -> pd.Series` | Compute rate of change as a momentum measure. |
| `momentum(close: pd.Series, window: int = 14) -> pd.Series` | Compute simple price-difference momentum. |
| `donchian_channel(df: pd.DataFrame, n: int, high_col: str = 'High', low_col: str = 'Low') -> tuple[pd.Series, pd.Series, pd.Series]` | Donchian Channel (breakout levels). |
| `hurst_exponent(series: pd.Series, lags: int = 20) -> float` | Estimate Hurst exponent for mean reversion vs trending detection. |
| `rolling_hurst(series: pd.Series, window: int = 100, lags: int = 20) -> pd.Series` | Compute rolling Hurst exponent. |
| `pivot_points(df: pd.DataFrame, high_col: str = 'High', low_col: str = 'Low', close_col: str = 'Close') -> pd.DataFrame` | Calculate pivot points and support/resistance levels. |
| `adr(df: pd.DataFrame, n: int = 14, high_col: str = 'High', low_col: str = 'Low') -> pd.Series` | Average Daily Range. |
| `forward_returns(close: pd.Series, horizon: int = 5) -> pd.Series` | Compute horizon-aligned forward log returns (labeled with research_ prefix). |
| `forward_max_favorable_excursion(df: pd.DataFrame, horizon: int, side: str, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> pd.Series` | Maximum favorable price excursion over horizon. |
| `forward_max_adverse_excursion(df: pd.DataFrame, horizon: int, side: str, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> pd.Series` | Maximum adverse price excursion over horizon. |
| `detect_volatility_regime(df: pd.DataFrame, atr_n: int = 14, window: int = 252, n_regimes: int = 3, high_col: str = 'High', low_col: str = 'Low', close_col: str = 'Close') -> pd.Series` | Detect volatility regime based on ATR percentile. |
| `detect_trend_regime(df: pd.DataFrame, fast_window: int = 20, slow_window: int = 50) -> pd.Series` | Classify trend regime from moving-average relationships. |
| `sma(series: pd.Series, n: int) -> pd.Series` | Compute simple moving average. |
| `ema(series: pd.Series, n: int) -> pd.Series` | Exponential Moving Average. |
| `std(series: pd.Series, n: int) -> pd.Series` | Compute rolling standard deviation. |


## FEAT-RES-18: Batch + streaming feature pipeline built on top of indicator modules (IP-13) (app.services.research.features.pipeline)

| Function | Purpose |
|----------|---------|
| `FeatureSpec` (model) | One feature in the pipeline. |
| `FeaturePipeline.__init__(features: Iterable[FeatureSpec], *, pipeline_version: str = '1.0.0', max_buffer_bars: int = 2000) -> None` | Support internal init processing. |
| `FeaturePipeline.describe() -> dict[str, Any]` | Return pipeline metadata for run manifests/inspection. |
| `FeaturePipeline.fingerprint() -> str` | Return a deterministic sha256 fingerprint for this pipeline definition. |
| `FeaturePipeline.compute_batch(data: pd.DataFrame) -> pd.DataFrame` | Compute all configured features on a batch DataFrame. |
| `FeaturePipeline.compute_incremental(*, symbol: str, bar: Mapping[str, Any]) -> dict[str, Any]` | Update streaming buffer for one symbol and compute latest feature row. |
| `FeaturePipeline.inspect_graph() -> dict[str, Any]` | Return inspectable feature dependency graph. |


## FEAT-RES-19: Helper services and analytics functions for Research Edge Lab (app.services.research.helpers)

| Function | Purpose |
|----------|---------|
| `calmar_ratio(annualized_return: float, max_dd: float) -> float` | Calculate Calmar ratio. |
| `expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float` | Calculate trade expectancy. |
| `max_drawdown(equity_curve: pd.Series) -> float` | Calculate maximum drawdown. |
| `median_mae_mfe(trades: list[dict[str, Any]]) -> dict[str, float]` | Calculate median MAE/MFE values. |
| `profit_factor(trades: list[dict[str, Any]]) -> float` | Calculate profit factor. |
| `sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float` | Calculate Sharpe ratio. |
| `sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float` | Calculate Sortino ratio. |
| `win_rate(trades: list[dict[str, Any]]) -> float` | Calculate win rate. |
| `ResearchResourceLimits.check_limits(row_count: int) -> None` | Check row counts and fail closed if rows exceed limits. |


## FEAT-RES-20: Data leakage checks and chronological splitting for Research Edge Lab (app.services.research.leakage)

| Function | Purpose |
|----------|---------|
| `LeakageReport` (model) | Defines suspected columns, severity, evidence, recommendations, and metadata. |
| `validate_no_lookahead_features(df: pd.DataFrame, allowed_forward_columns: list[str] \| None = None, target_column: str \| None = None) -> LeakageReport` | Inspect DataFrame columns for lookahead bias without mutating the input frame. |
| `validate_no_lookahead(df: pd.DataFrame, allowed_forward_columns: list[str] \| None = None, target_column: str \| None = None) -> LeakageReport` | Wrapper for validate_no_lookahead_features. |
| `detect_feature_leakage(df: pd.DataFrame, allowed_forward_columns: list[str] \| None = None, target_column: str \| None = None) -> LeakageReport` | Wrapper for validate_no_lookahead_features. |
| `mask_forward_columns(df: pd.DataFrame, report: LeakageReport) -> pd.DataFrame` | Return a copy of the DataFrame with suspected lookahead columns dropped. |
| `TimeSplitResult.to_dict() -> dict[str, int]` | Return counts of splits. |
| `enforce_time_split(data: pd.DataFrame, *, train_frac: float, val_frac: float, test_frac: float, min_gap: int = 0, timestamp_col: str \| None = None) -> TimeSplitResult` | Enforce deterministic chronological train/validation/test split. |
| `mask_research_artifact(artifact: dict[str, Any]) -> dict[str, Any]` | Remove or redact sensitive fields from research artifacts before persistence or sharing. |
| `dump_masked_research_json(artifact: dict[str, Any]) -> str` | Serialize a masked research artifact to JSON. |
| `TimeSplitResult` (model) | Chronological train/validation/test split result. |


## FEAT-RES-21: Market Structure engine for directional structure and non-trending behavior (app.services.research.market_structure)

| Function | Purpose |
|----------|---------|
| `TrendScoreRow.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `MarketStructureProfile.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `build_market_structure_profile(prepared: PreparedDataset, *, symbol: str, timeframe: str, data_source: str, range_by: str, start_date: str \| None = None, end_date: str \| None = None, number_of_bars: int \| None = None, config: MarketStructureConfig \| None = None, tp_config: TrendPersistenceConfig \| None = None) -> MarketStructureProfile` | Build a reproducible directional structure profile from a prepared dataset. |
| `build_market_structure_research_profile(prepared: PreparedDataset, *, symbol: str, timeframe: str, data_source: str, range_by: str, start_date: str \| None = None, end_date: str \| None = None, number_of_bars: int \| None = None, config: MarketStructureConfig \| None = None, tp_config: TrendPersistenceConfig \| None = None) -> MarketStructureProfile` | Build Market Structure with expensive quality-adjusted research layers enabled. |


## FEAT-RES-22: Top-level calibration helpers for Market Structure verdict thresholds (app.services.research.market_structure_calibration)

| Function | Purpose |
|----------|---------|
| `MarketStructureCalibrationCandidate.to_dict() -> dict[str, float]` | Run to dict processing. |
| `classify_with_candidate(*, trend_bias_score: float, reversion_bias_score: float, trend_confidence_score: float, reversion_confidence_score: float, candidate: MarketStructureCalibrationCandidate) -> str` | Run classify with candidate processing. |


## FEAT-RES-23: Lower-level metric-band calibration helpers for Market Structure (app.services.research.market_structure_metric_calibration)

| Function | Purpose |
|----------|---------|
| `MarketStructureMetricCalibrationCandidate.to_dict() -> dict[str, float]` | Run to dict processing. |
| `evaluate_metric_calibration_candidates(run_rows: Iterable[dict[str, Any]], validation_rows: Iterable[dict[str, Any]], *, cfg: MarketStructureConfig \| None = None) -> dict[str, Any]` | Run evaluate metric calibration candidates processing. |


## FEAT-RES-24: Profile-aware calibration aggregation for Market Structure (app.services.research.market_structure_profile_calibration)

| Function | Purpose |
|----------|---------|
| `evaluate_profile_calibration(run_rows: Iterable[dict[str, Any]], validation_rows: Iterable[dict[str, Any]]) -> dict[str, Any]` | Run evaluate profile calibration processing. |


## FEAT-RES-25: Parameter robustness helpers for Market Structure (app.services.research.market_structure_robustness)

| Function | Purpose |
|----------|---------|
| `build_market_structure_robustness_report(prepared: PreparedDataset, *, symbol: str, timeframe: str, data_source: str, range_by: str, start_date: str \| None = None, end_date: str \| None = None, number_of_bars: int \| None = None, config: MarketStructureConfig \| None = None) -> dict[str, Any]` | Run build market structure robustness report processing. |


## FEAT-RES-26: Regime stability helpers for Market Structure (app.services.research.market_structure_stability)

| Function | Purpose |
|----------|---------|
| `build_market_structure_stability_report(prepared: PreparedDataset, *, symbol: str, timeframe: str, data_source: str, range_by: str, start_date: str \| None = None, end_date: str \| None = None, number_of_bars: int \| None = None, config: MarketStructureConfig \| None = None) -> dict[str, Any]` | Run build market structure stability report processing. |


## FEAT-RES-27: Validation helpers for Market Structure forward-outcome reporting (app.services.research.market_structure_validation)

| Function | Purpose |
|----------|---------|
| `label_realized_market_behavior(df: pd.DataFrame, *, symbol: str, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> dict[str, float \| str]` | Classify the realized future window as trend, reversion, or mixed. |
| `build_validation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]` | Run build validation summary processing. |


## FEAT-RES-28: Core metric calculators for Research Edge Lab (app.services.research.metrics)

| Function | Purpose |
|----------|---------|
| `MetricValue.to_dict() -> dict[str, Any]` | Convert metric value to a dict. |
| `MetricContext` (class) | Provides the dataset and metadata needed by metric calculators. |
| `MetricCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate the metric from the context. |
| `ReturnsCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate mean return and return metrics. |
| `RocCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate rate of change. |
| `CandlesCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate candle body and shadows. |
| `RangesCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate high-low ranges. |
| `VolatilityCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate annualized volatility. |
| `SpreadCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate spread statistics. |
| `VolumeActivityCalculator.calculate(context: MetricContext) -> MetricValue` | Calculate volume statistics. |
| `MetricRegistry.register(name: str, calculator: MetricCalculator) -> None` | Register a calculator. |
| `MetricRegistry.calculate_all(context: MetricContext) -> dict[str, MetricValue]` | Calculate all registered metrics. |
| `build_default_registry() -> MetricRegistry` | Build the default registry of research metric calculators. |
| `CoreMetricProfile.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `ReturnsCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `RocCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `CandlesCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `RangesCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `VolatilityCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `SpreadCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `VolumeActivityCalculator.compute(context: MetricContext) -> list[MetricValue]` | Run compute processing. |
| `build_core_metric_profile(prepared: PreparedDataset, *, symbol: str, timeframe: str, data_source: str, range_by: str, start_date: str \| None = None, end_date: str \| None = None, number_of_bars: int \| None = None, registry: MetricRegistry \| None = None) -> CoreMetricProfile` | Build a normalized Core Metric profile from a prepared dataset. |


## FEAT-RES-29: Contracts for reusable unsupervised research tools (app.services.research.modeling.contracts)

| Function | Purpose |
|----------|---------|
| `UnsupervisedResearchConfig.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `UnsupervisedResearchRequest` (model) | Input contract for reusable unsupervised analysis. |
| `UnsupervisedResearchResult.to_metadata() -> dict[str, Any]` | Run to metadata processing. |


## FEAT-RES-30: Reusable feature-set builders for unsupervised modeling workflows (app.services.research.modeling.feature_sets)

| Function | Purpose |
|----------|---------|
| `FeatureSetFrame.to_metadata() -> dict[str, Any]` | Run to metadata processing. |
| `build_market_regime_feature_frame(data: pd.DataFrame, *, fast_period: int = 20, slow_period: int = 50, volatility_window: int = 20, momentum_window: int = 5, min_periods: int = 3, include_ema_spread: bool = True, price_column: str = 'close') -> FeatureSetFrame` | Build timestamp-aligned features for PCA/K-Means regime research. |


## FEAT-RES-31: Reusable unsupervised research service for strategy and optimization flows (app.services.research.modeling.service)

| Function | Purpose |
|----------|---------|
| `UnsupervisedResearchService.analyze(request: UnsupervisedResearchRequest) -> UnsupervisedResearchResult` | Run analyze processing. |
| `UnsupervisedResearchService.analyze_frame(data: pd.DataFrame, *, signal_frame: pd.DataFrame \| None = None, config: UnsupervisedResearchConfig \| None = None) -> UnsupervisedResearchResult` | Run analyze frame processing. |


## FEAT-RES-32: Unsupervised investment-data insight helpers (app.services.research.modeling.unsupervised_insights)

| Function | Purpose |
|----------|---------|
| `InvestmentDataSummary.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `PcaRiskFactor.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `ClusterOutperformance.to_dict() -> dict[str, Any]` | Run to dict processing. |
| `SignalAdaptationResult.to_metadata() -> dict[str, Any]` | Run to metadata processing. |
| `UnsupervisedInsightReport.to_metadata() -> dict[str, Any]` | Run to metadata processing. |
| `summarize_investment_data(data: pd.DataFrame, *, price_column: str = 'close') -> InvestmentDataSummary` | Explore investment data and return key descriptive statistics. |
| `identify_pca_risk_factors(pca_result: PcaModelResult, *, top_n_per_component: int = 3) -> tuple[PcaRiskFactor, ...]` | Extract the largest PCA loadings as interpretable risk factors. |
| `compute_forward_returns(data: pd.DataFrame, *, price_column: str = 'close', horizon: int = 1, output_column: str = 'forward_return') -> pd.Series` | Compute horizon-aligned forward returns from a price column. |
| `analyze_cluster_outperformance(data: pd.DataFrame, labels: pd.Series, *, price_column: str = 'close', forward_returns: pd.Series \| None = None, horizon: int = 1, feature_columns: Sequence[str] = ()) -> tuple[ClusterOutperformance, ...]` | Score each cluster by future returns and assign semantic regime names. |
| `adapt_signals_by_cluster(signal_frame: pd.DataFrame, cluster_outperformance: Sequence[ClusterOutperformance], *, label_column: str = 'cluster_label', signal_column: str = 'entry_signal', min_observations: int = 1) -> SignalAdaptationResult` | Suppress strategy entries in clusters with weak forward returns. |
| `build_unsupervised_insight_report(data: pd.DataFrame, *, feature_columns: Sequence[str], price_column: str = 'close', n_components: int = 2, n_clusters: int = 3, random_state: int = 42, forward_return_horizon: int = 1, label_column: str = 'cluster_label', signal_frame: pd.DataFrame \| None = None, signal_column: str = 'entry_signal', scale_features: bool = True) -> UnsupervisedInsightReport` | Build a complete unsupervised insight report for trading workflows. |


## FEAT-RES-33: Reporting helpers for full Edge Lab profile snapshots (app.services.research.profile_reporting)

| Function | Purpose |
|----------|---------|
| `snapshot_report_json(snapshot: dict[str, Any]) -> dict[str, Any]` | Build a machine-readable complete pair report. |
| `snapshot_report_markdown(snapshot: dict[str, Any]) -> str` | Render one human-readable Markdown pair report. |
| `comparison_report_markdown(comparison: dict[str, Any]) -> str` | Render one Markdown comparison report from two snapshots. |


## FEAT-RES-34: Reporting and serialization service for Research Edge Lab (app.services.research.reporting)

| Function | Purpose |
|----------|---------|
| `result_to_markdown(res: EdgeResult, include_trades: bool = False) -> str` | Convert EdgeResult to formatted Markdown report. |
| `result_to_summary(result: EdgeResult) -> dict[str, Any]` | Generate a concise summary dictionary from an edge result. |
| `save_markdown(result: EdgeResult, filepath: str, overwrite: bool = True) -> bool` | Persist an edge result report as Markdown. |
| `save_json(result: EdgeResult, filepath: str, overwrite: bool = True) -> bool` | Persist an edge result report as JSON. |
| `generate_multi_symbol_report(results: list[EdgeResult], output_dir: str \| Path) -> Path` | Generate a combined report for multiple symbols. |
| `build_edge_profile_snapshot(symbol: str, timeframe: str, results: list[EdgeResult]) -> dict[str, Any]` | Build a normalized snapshot payload from progressive Edge Lab tab results. |
| `build_profile_summary(snapshot: dict[str, Any]) -> dict[str, Any]` | Build a concise dashboard-ready summary from one profile snapshot. |
| `build_dashboard_summary(snapshot: dict[str, Any]) -> dict[str, Any]` | Build a UI or dashboard summary block from one profile snapshot. |
| `save_json_report(snapshot: dict[str, Any], filepath: str, overwrite: bool = True) -> bool` | Save one complete JSON profile report. |
| `save_markdown_report(snapshot: dict[str, Any], filepath: str, overwrite: bool = True) -> bool` | Save one complete Markdown profile report. |
| `print_result_summary(res: EdgeResult) -> None` | Print a concise result summary to console. |


## FEAT-RES-35: Edge Lab result schemas (app.services.research.results_schema)

| Function | Purpose |
|----------|---------|
| `TradeSample.to_dict() -> dict[str, Any]` | Convert to dictionary for JSON serialization. |
| `EdgeStats.to_dict() -> dict[str, Any]` | Convert to dictionary for JSON serialization. |
| `EdgeStats.edge_confirmed -> bool` | Check if edge is statistically confirmed. |
| `EdgeStats.verdict -> str` | Return human-readable verdict. |
| `EdgeResult.to_dict() -> dict[str, Any]` | Convert to dictionary for JSON serialization. |
| `EdgeResult.from_dict(data: dict[str, Any]) -> EdgeResult` | Create from dictionary. |
| `EdgeResult.summary() -> str` | Return concise summary string. |


## FEAT-RES-36: Backend Edge Lab scorecard builder for automation and snapshot runs (app.services.research.scorecard)

| Function | Purpose |
|----------|---------|
| `build_edge_lab_scorecard_report(*, dataset: dict[str, Any], core_metric_profile: dict[str, Any], seasonality_result: dict[str, Any], market_structure_profile: dict[str, Any], stability: dict[str, Any] \| None = None, robustness: dict[str, Any] \| None = None) -> dict[str, Any] \| None` | Build a deterministic backend scorecard report from progressive Edge Lab outputs. |


## FEAT-RES-37: Seasonality analytics for Edge Lab (Phase A) (app.services.research.seasonality)

| Function | Purpose |
|----------|---------|
| `SeasonalityFilters` (model) | Filters for seasonality analysis. |
| `run_seasonality(df: pd.DataFrame, *, symbol: str, timeframe: str, point_size: float = 1.0, pip_size: float \| None = None, filters: SeasonalityFilters \| None = None, data_offset: int = 0, data_limit: int = 20) -> dict[str, Any]` | Run seasonality analysis on the provided dataframe. |


## FEAT-RES-38: Shared Edge Lab session windows and helpers (app.services.research.session_config)

| Function | Purpose |
|----------|---------|
| `active_sessions_for_hour(hour: int, session_windows: Mapping[str, Sequence[int]] \| None = None) -> list[str]` | Run active sessions for hour processing. |
| `session_label_for_hour(hour: int, session_windows: Mapping[str, Sequence[int]] \| None = None) -> str` | Run session label for hour processing. |
| `session_hours_payload(session_windows: Mapping[str, Sequence[int]] \| None = None) -> dict[str, list[int]]` | Run session hours payload processing. |
| `tag_sessions(df: pd.DataFrame, asia_hours: Sequence[int] \| None = None, london_hours: Sequence[int] \| None = None, ny_hours: Sequence[int] \| None = None, off_hours: Sequence[int] \| None = None) -> pd.DataFrame` | Tag each bar with its trading session label. |


## FEAT-RES-39: Standardized agent-facing research tools (app.services.research.standard_tools)

| Function | Purpose |
|----------|---------|
| `fetch_forexfactory_news(*, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Pull the ForexFactory news feed. |
| `fetch_forexfactory_calendar(*, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Pull the ForexFactory economic calendar. |
| `fetch_forexfactory_sentiment(*, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Pull the ForexFactory sentiment page. |
| `fetch_forexfactory_instrument_page(*, symbol: str, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Pull a symbol-specific ForexFactory page. |
| `parse_news_items(*, raw_items: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Normalize raw news items. |
| `parse_calendar_events(*, raw_events: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Normalize economic calendar events. |
| `parse_sentiment_snapshot(*, raw_snapshot: dict[str, Any], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Normalize sentiment positioning. |
| `filter_events_by_symbol(*, events: list[dict[str, Any]], symbol: str, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Filter calendar events by symbol currencies. |
| `classify_news_impact(*, event: dict[str, Any], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Classify economic news impact. |
| `create_news_blackout_windows(*, events: list[dict[str, Any]], minutes_before: int = 30, minutes_after: int = 30, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Create no-trade windows around news events. |
| `calculate_returns(*, prices: list[float] \| None = None, records: list[dict[str, Any]] \| None = None, column: str = 'close', log: bool = False, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate price returns. |
| `calculate_volatility(*, returns: list[float], window: int = 20, annualization_factor: float = 252.0, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate rolling annualized volatility. |
| `calculate_atr(*, records: list[dict[str, Any]], period: int = 14, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate Average True Range. |
| `calculate_adr(*, records: list[dict[str, Any]], period: int = 10, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate Average Daily Range. |
| `calculate_spread_statistics(*, spreads: list[float], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate spread distribution statistics. |
| `calculate_session_statistics(*, records: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate session return statistics. |
| `calculate_seasonality_statistics(*, records: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate calendar seasonality statistics. |
| `calculate_regime_features(*, records: list[dict[str, Any]], fast_window: int = 20, slow_window: int = 50, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate regime feature rows. |
| `calculate_correlation_matrix(*, series_by_name: dict[str, list[float]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Calculate a correlation matrix. |
| `detect_trend_strength(*, records: list[dict[str, Any]], fast_window: int = 20, slow_window: int = 50, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Detect trend strength from moving averages. |
| `detect_market_regime(*, records: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Classify market regime. |
| `detect_mean_reversion_conditions(*, records: list[dict[str, Any]], window: int = 20, z_threshold: float = 2.0, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Detect mean-reversion conditions. |
| `detect_breakout_conditions(*, records: list[dict[str, Any]], window: int = 20, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Detect breakout conditions. |
| `generate_research_hypothesis(*, symbol: str, strategy_type: str, timeframe: str, observation: str, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Generate a structured research hypothesis. |
| `score_research_hypothesis(*, evidence: dict[str, Any], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Score research evidence quality. |
| `check_sample_size(*, observations: int, minimum: int = 200, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Validate sample size sufficiency. |
| `check_data_snooping_risk(*, tests_run: int, adjusted: bool = False, request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Check data-snooping risk. |
| `check_lookahead_bias_risk(*, field_names: list[str], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Check lookahead-bias risk. |
| `check_hypothesis_testability(*, hypothesis: dict[str, Any], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Check whether a hypothesis is testable. |
| `check_contradictory_evidence(*, supporting: list[str], contradicting: list[str], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Check contradictory evidence risk. |
| `build_research_evidence_pack(*, hypothesis: dict[str, Any], evidence: dict[str, Any], validation: dict[str, Any], request_id: str \| None = None, agent_name: str \| None = None, environment: EnvironmentName = 'development') -> dict[str, Any]` | Build a structured research evidence pack. |


## FEAT-RES-40: Null models, resampling, and hypothesis testing for Research Edge Lab (app.services.research.studies.null_models)

| Function | Purpose |
|----------|---------|
| `compute_null_percentile(observed: float, null_distribution: list[float] \| np.ndarray) -> float` | Compute the percentile of an observed value within a null distribution. |
| `get_acceptance_criteria(null_distribution: list[float] \| np.ndarray, alpha: float = 0.05) -> dict[str, float]` | Extract acceptance criteria from a null baseline. |
| `block_bootstrap_distribution(data: np.ndarray \| pd.Series, n_iterations: int = 1000, block_size: int = 10, seed: int \| None = None) -> np.ndarray` | Generate a bootstrap distribution for a statistic (default: mean) using block bootstrap resampling. |
| `block_bootstrap_ci(data: np.ndarray \| pd.Series, n_iterations: int = 1000, block_size: int = 10, confidence_level: float = 0.95, seed: int \| None = None) -> tuple[float, float]` | Compute a confidence interval using block bootstrap resampling. |
| `permutation_test(group1: np.ndarray \| pd.Series, group2: np.ndarray \| pd.Series, n_permutations: int = 1000, seed: int \| None = None) -> float` | Compute a permutation-test p-value. |
| `random_entry_null(log_returns: np.ndarray, n_trades: int, hold_bars: int, side: str = 'BUY', n_perm: int = 2000, seed: int \| None = 11) -> np.ndarray` | Generate null distribution via random entries (log-return space). |
| `r_space_null(df: pd.DataFrame, n_trades: int, hold_bars: int, side: str, k_stop_atr: float, atr_series: pd.Series, n_perm: int = 2000, seed: int \| None = 11, close_col: str = 'Close', high_col: str = 'High', low_col: str = 'Low') -> np.ndarray` | Generate null distribution in R-multiple space. |
| `session_randomized_null(df: pd.DataFrame, entry_indices: np.ndarray, hold_bars: int, side: str, k_stop_atr: float, atr_series: pd.Series, n_perm: int = 2000, seed: int \| None = 11, close_col: str = 'Close') -> np.ndarray` | Generate null by shuffling entries within same session. |
| `shuffle_returns_null(log_returns: np.ndarray, entry_indices: np.ndarray, hold_bars: int, side: str = 'BUY', n_perm: int = 2000, seed: int \| None = 11) -> np.ndarray` | Generate null by shuffling return blocks. |
| `benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[bool]` | Apply Benjamini-Hochberg false-discovery-rate correction. |
| `holm_bonferroni(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray` | Holm-Bonferroni correction (more conservative than BH). |
| `null_distribution_stats(null_distribution: list[float] \| np.ndarray) -> dict[str, float]` | Compute summary statistics for a null distribution. |
| `exceeds_null_threshold(observed: float, null_samples: np.ndarray, percentile: float = 95.0) -> bool` | Check if observed value exceeds null distribution threshold. |


## FEAT-RES-41: Market Structure tracking and calibration service for Research Edge Lab (app.services.research.studies.structure)

| Function | Purpose |
|----------|---------|
| `TrendSwingPoint` (model) | Represents a detected swing point used in market-structure analysis. |
| `TrendLeg` (model) | Represents a directional leg between swing points. |
| `TrendScoreRow` (model) | Represents one market-structure score row. |
| `MarketStructureProfile` (model) | Represents a reproducible directional structure profile. |
| `MarketStructureCalibrationCandidate` (model) | Represents one calibration candidate for market-structure classification. |
| `MarketStructureMetricCalibrationCandidate` (model) | Represents one metric-calibration candidate. |
| `ClassificationResult` (model) | Represents the result of classifying a symbol's edge profile. |
| `detect_swing_points(df: pd.DataFrame, window: int = 5) -> list[TrendSwingPoint]` | Detect swing highs and swing lows in historical data. |
| `build_calibration_grid(windows: list[int], thresholds: list[float]) -> list[MarketStructureCalibrationCandidate]` | Build candidate parameter grids for market-structure calibration. |
| `evaluate_calibration_candidates(df: pd.DataFrame, candidates: list[MarketStructureCalibrationCandidate]) -> list[MarketStructureCalibrationCandidate]` | Evaluate market-structure calibration candidates against realized evidence. |
| `build_metric_calibration_grid(metric_names: list[str], param_values: list[float]) -> list[MarketStructureMetricCalibrationCandidate]` | Build candidate grids for market-structure metric calibration. |
| `timeframe_bucket(timeframe: str) -> str` | Map a timeframe into a market-structure profile bucket. |
| `symbol_class(symbol: str) -> str` | Map a symbol into a market-structure symbol class. |
| `resolve_market_structure_profile(symbol: str, timeframe: str) -> MarketStructureProfile` | Resolve the applicable market-structure profile for a symbol and timeframe. |
| `resolve_market_structure_profile_overrides(symbol: str, timeframe: str, profile_class: str) -> MarketStructureProfile` | Resolve profile overrides for a symbol, timeframe, or profile class. |
| `confidence_bucket(score: float) -> str` | Convert validation evidence into a confidence bucket. |
| `build_strategy_fit(df: pd.DataFrame) -> dict[str, Any]` | Assess advisory strategy-fit evidence from market-structure research. |


## FEAT-RES-42: Unsupervised learning and dimensionality reduction service for Research Edge Lab (app.services.research.studies.unsupervised)

| Function | Purpose |
|----------|---------|
| `UnsupervisedResearchResult` (model) | Represents a complete unsupervised research result. |
| `run_pca(data: pd.DataFrame, *, feature_columns: Sequence[str] \| None = None, n_components: int = 2, scale: bool = True, component_prefix: str = 'pc') -> PcaModelResult` | Run PCA on numeric feature columns and return component scores/loadings. |
| `cluster_feature_space(data: pd.DataFrame, *, feature_columns: Sequence[str] \| None = None, n_clusters: int = 3, random_state: int = 42, scale: bool = True, label_name: str = 'cluster_label') -> ClusterModelResult` | Cluster numeric feature rows with deterministic K-Means labels. |
| `attach_cluster_labels(data: pd.DataFrame, result: ClusterModelResult, *, column_name: str \| None = None) -> pd.DataFrame` | Attach cluster labels to a feature frame without mutating the input. |
| `PcaModelResult.to_metadata() -> dict[str, Any]` | Return compact serializable metadata for agentic/audit/reports/evidence. |
| `ClusterModelResult.to_metadata() -> dict[str, Any]` | Return compact serializable metadata for agentic/audit/reports/evidence. |
