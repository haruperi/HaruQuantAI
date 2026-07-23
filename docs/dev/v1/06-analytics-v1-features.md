## FEAT-ANLT-01: Trading result canonicalization engine (ANL-NFR-092, ANL-NFR-093) (app.services.analytics.adapters.canonicalize)

| Function | Purpose |
|----------|---------|
| `to_canonical(source_payload: dict[str, Any]) -> dict[str, Any]` | Module-level convenience wrapper for TradingResultAdapter.to_canonical. |
| `to_trading_result(source: BacktestResult \| PaperResult \| LiveResult \| PortfolioResult \| TradingResult) -> TradingResult` | Convert raw trading/backtest results into the canonical TradingResult dataclass. |


## FEAT-ANLT-02: Simulation-journal and live-journal analytics adapters (ANL-NFR-449) (app.services.analytics.adapters.journal_adapters)

| Function | Purpose |
|----------|---------|
| `SimulationJournal` (dataclass) | Simulation execution journal container structure (ANL-NFR-449). |
| `LiveTradeJournal` (dataclass) | Live execution journal container structure (ANL-NFR-449). |
| `from_simulation_journal(journal: SimulationJournal) -> TradingResult` | Convert a SimulationJournal into a canonical TradingResult (ANL-NFR-449). |
| `from_live_trade_journal(journal: LiveTradeJournal) -> TradingResult` | Convert a LiveTradeJournal into a canonical TradingResult (ANL-NFR-449). |


## FEAT-ANLT-03: Trading result adapter protocols and validators (ANL-NFR-095) (app.services.analytics.adapters.protocols)

| Function | Purpose |
|----------|---------|
| `TradingResultDict` (TypedDict) | Canonical trading result dictionary representation. |
| `BacktestResultDict` (TypedDict) | Backtest-specific result dictionary contract. |
| `PaperTradingResultDict` (TypedDict) | Paper trading result dictionary contract. |
| `LiveTradingResultDict` (TypedDict) | Live trading result dictionary contract. |
| `TradingResultAdapter.to_canonical(source_payload: dict[str, Any]) -> dict[str, Any]` | Convert a raw dictionary source payload to a canonical dictionary format. |
| `validate_adapter_contract(adapter: Any) -> None` | Validate that an adapter class or instance conforms to the Protocol. |


## FEAT-ANLT-04: Benchmark series alignment and boundary rules for Analytics (app.services.analytics.benchmarks.alignment)

| Function | Purpose |
|----------|---------|
| `bench_alignment_boundary() -> None` | Pure architectural boundary declaration for benchmark alignment. |


## FEAT-ANLT-05: Benchmark comparison metrics for Analytics (app.services.analytics.benchmarks.metrics)

| Function | Purpose |
|----------|---------|
| `benchmark_returns(benchmark_equity: pd.Series, freq: str \| None = None) -> dict[str, Any]` | AI Tool wrapper for _benchmark_returns_impl. |
| `beta(strategy_returns: object, benchmark_returns: object) -> float` | Calculate the strategy beta coefficient relative to benchmark returns. |
| `alpha(strategy_returns: pd.Series, benchmark_returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> dict[str, Any]` | AI Tool wrapper for _alpha_impl. |
| `r_squared(strategy_returns: object, benchmark_returns: object) -> float` | Calculate coefficient of determination between strategy and benchmark returns. |
| `tracking_error(strategy_returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = 252) -> dict[str, Any]` | AI Tool wrapper for _tracking_error_impl. |
| `relative_drawdown_series(strategy_equity: pd.Series, benchmark_equity: pd.Series) -> dict[str, Any]` | AI Tool wrapper for _relative_drawdown_series_impl. |
| `batting_average(strategy_returns: object, benchmark_returns: object) -> float` | Calculate the percentage of periods where strategy outperformed benchmark. |
| `calculate_benchmark_metrics(strategy_returns: object, benchmark_returns: object, request_id: str \| None = None) -> StandardResponse` | Calculate combined benchmark-relative metrics (alpha, beta, IR). |


## FEAT-ANLT-06: Standard success/error envelopes and metadata helpers for Analytics boundaries (app.services.analytics.boundaries.envelopes)

| Function | Purpose |
|----------|---------|
| `success_envelope(data: object, metadata: AnalyticsMetadata) -> ToolEnvelope` | Wrap output data inside a standard success envelope. |
| `error_envelope(error: AnalyticsError, metadata: AnalyticsMetadata) -> ToolEnvelope` | Wrap structured error info inside a standard error envelope. |


## FEAT-ANLT-07: Workload limits configuration and enforcement for Analytics boundaries (app.services.analytics.boundaries.limits)

| Function | Purpose |
|----------|---------|
| `AnalyticsLimits` (dataclass) | Configured limits for analytics payloads and calculation sizes. |
| `WorkloadShape` (dataclass) | Describes the counts/sizes of the current workload elements. |
| `enforce_limits(shape: WorkloadShape, limits: AnalyticsLimits) -> None` | Verify shape boundaries against the limits configurations. |


## FEAT-ANLT-08: Recursive key and token redaction boundary helper for Analytics (app.services.analytics.boundaries.redaction)

| Function | Purpose |
|----------|---------|
| `RedactionPolicy` (enum) | Policies for level of redaction coverage. |
| `redact(value: object, policy: RedactionPolicy = RedactionPolicy.STANDARD) -> object` | Recursively redact secrets and credentials from data payloads. |


## FEAT-ANLT-09: Request schema and ID validations for Analytics boundaries (app.services.analytics.boundaries.request_validation)

| Function | Purpose |
|----------|---------|
| `float64(input_value: object, config: MetricConfig) -> MetricResult[object]` | Float64 validation and casting boundary wrapper. |
| `validate_request(request: object, request_id_val: str, limits: AnalyticsLimits) -> None` | Validate request trace ID and workload limits shape before processing. |


## FEAT-ANLT-10: Common (app.services.analytics.common)

| Function | Purpose |
|----------|---------|
| `analytics_tool_result(tool_name: str, *, data: dict[str, Any] \| None = None, status: str = 'success', errors: list[str] \| None = None, warnings: list[str] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True, approval_required: str = 'none', risk_level: str = 'low', side_effects: list[str] \| None = None) -> dict[str, Any]` | Build the standard result envelope for analytics tool functions. |
| `analytics_business_payload(payload: dict[str, Any]) -> dict[str, Any]` | Return business inputs after removing standard control fields. |
| `time_in_market_duration(trades: pd.DataFrame, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _time_in_market_duration_impl. |
| `percent_time_in_market(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _percent_time_in_market_impl. |


## FEAT-ANLT-11: Audit trail contracts module (app.services.analytics.contracts.audit)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `AuditEvent` (class) | The canonical audit log record contract. |


## FEAT-ANLT-12: Metric definition catalog, tool catalog, configurations, and validations (app.services.analytics.contracts.metric_catalog)

| Function | Purpose |
|----------|---------|
| `get_metric_definition(name: str) -> MetricDefinition` | Retrieve an approved metric definition by name (ANL-NFR-075, ANL-NFR-076). |
| `validate_metric_catalog(catalog: Mapping[str, MetricDefinition] \| None = None) -> dict[str, Any]` | Validate that metric catalog entries are complete and unique (ANL-NFR-082). |


## FEAT-ANLT-13: Analytics schema versioning and contracts support models (app.services.analytics.contracts.models)

| Function | Purpose |
|----------|---------|
| `Lineage` (dataclass) | Lineage and provenance metadata for traceability. |
| `BenchmarkData` (dataclass) | Benchmark price and return data for comparison. |
| `TradingResult` (dataclass) | Versioned canonical trading result input contract. |
| `ReproducibilityHashes` (dataclass) | Hashes of inputs, config, and report for validation and audit. |
| `AnalyticsWarning` (dataclass) | Warning object emitted during analytics compilation. |
| `QualityFlag` (dataclass) | Quality flag object emitted during strategy quality scorecard evaluation. |
| `AnalyticsReport` (dataclass) | Versioned canonical analytics report contract. |
| `ToolEnvelope` (dataclass) | Standard success/error envelope wrapper. |
| `MetricDefinition` (dataclass) | Approved definition for a metric exposed by analytics. |
| `ToolDefinition` (dataclass) | Public analytics tool catalog entry. |
| `AnalyticsConfig` (dataclass) | Deterministic analytics configuration. |
| `MetricResult` (dataclass) | Unified wrapper around a single metric calculation outcome. |
| `validate_schema_version(version: str, matrix: SchemaCompatibilityMatrix) -> SchemaCompatibility` | Validate a schema version against a compatibility matrix. |
| `ExplainabilityOutput` (dataclass) | Explainability output container (ANL-NFR-280). |
| `PrecisionPolicy` (dataclass) | Precision policy configurations for rounding and formatting (ANL-NFR-086). |
| `AnalyticsMetadata` (dataclass) | Trace and reproducibility metadata for analytics payloads. |
| `AnalyticsRequest` (dataclass) | Canonical analytics request wrapper. |
| `AnalyticsResult` (dataclass) | Canonical analytics result wrapper. |


## FEAT-ANLT-14: Portfolio state contracts module (app.services.analytics.contracts.portfolio)

| Function | Purpose |
|----------|---------|
| `AccountSnapshot.validate_snap_time(v: str) -> str` | Validate and normalize snapshot timestamp. |
| `Position.validate_pos_times(v: str) -> str` | Validate and normalize position lifecycle timestamps. |
| `PortfolioSnapshot` (class) | Standardized composite snapshot of the entire portfolio state. |


## FEAT-ANLT-15: Serialization helpers for canonical JSON formatting and safe float validation (app.services.analytics.contracts.serialization)

| Function | Purpose |
|----------|---------|
| `to_json_safe(value: Any, precision: PrecisionPolicy) -> JsonValue` | Recursively convert any python object to a JSON-safe format (ANL-NFR-433). |
| `canonical_json(value: JsonValue) -> str` | Generate sorted, whitespace-free canonical JSON representation (ANL-NFR-433). |


## FEAT-ANLT-16: Warning and quality-flag catalogs, redaction policies, and constructors (app.services.analytics.contracts.warnings)

| Function | Purpose |
|----------|---------|
| `WarningCatalogEntry` (dataclass) | Catalog entry metadata for an AnalyticsWarning. |
| `QualityFlagCatalogEntry` (dataclass) | Catalog entry metadata for a QualityFlag. |
| `redact_sensitive_info(data: Any) -> Any` | Recursively redact sensitive keys and values from payloads (ANL-NFR-276). |
| `build_warning(code: str, source_context: str \| None = None, detail: dict[str, Any] \| None = None) -> AnalyticsWarning` | Build a validated AnalyticsWarning (ANL-NFR-278, ANL-NFR-279). |
| `build_quality_flag(code: str, source_context: str \| None = None, detail: dict[str, Any] \| None = None) -> QualityFlag` | Build a validated QualityFlag (ANL-NFR-278, ANL-NFR-279). |


## FEAT-ANLT-17: Dashboard payload builders for Analytics UI/API representation (app.services.analytics.dashboards.overview)

| Function | Purpose |
|----------|---------|
| `calculate_analytics_for_subset(trades: pd.DataFrame, initial_balance: float, start_time: pd.Timestamp \| str \| None = None, end_time: pd.Timestamp \| str \| None = None, benchmark_returns_series: pd.Series \| None = None, benchmark_equity_series: pd.Series \| None = None) -> dict[str, Any]` | AI Tool wrapper for _calculate_analytics_for_subset_impl. |
| `get_analytics_overview(trades: Any, initial_balance: float, start_time: Any = None, end_time: Any = None, benchmark_equity: pd.Series \| None = None) -> dict[str, Any]` | AI Tool wrapper for _get_analytics_overview_impl. |
| `build_overview_payload(trades: Any, initial_balance: float, start_time: Any = None, end_time: Any = None, equity_curve_records: list[Any] \| None = None, summary_overrides: dict[str, Any] \| None = None) -> dict[str, Any]` | AI Tool wrapper for _build_overview_payload_impl. |
| `calculate_spread_cost_impact(*, spread_costs: list[float], gross_profit: float, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_spread_cost_impact_impl. |
| `calculate_slippage_impact(*, slippage_costs: list[float], gross_profit: float, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_slippage_impact_impl. |
| `calculate_commission_impact(*, commission_costs: list[float], gross_profit: float, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_commission_impact_impl. |
| `build_backtest_report(*, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True, **report_sections: Any) -> dict[str, Any]` | AI Tool wrapper for _build_backtest_report_impl. |
| `DashboardConfig` (dataclass) | Configuration options for API and UI dashboard generation. |
| `TruncationMetadata` (dataclass) | Preserved metadata describing the downsample / truncation details. |
| `DashboardPayload` (dataclass) | Structured UI overview presentation schema payload. |


## FEAT-ANLT-18: Deterministic chart downsampling/truncation for Analytics (app.services.analytics.dashboards.truncation)

| Function | Purpose |
|----------|---------|
| `ChartPoint` (dataclass) | Data point representation in charts. |
| `TruncationPolicy` (dataclass) | Configured downsampling and truncation policy limits. |
| `TruncatedSeries` (dataclass) | Container for downsampled series response data. |
| `truncate_series(points: Sequence[ChartPoint] \| list[dict[str, Any]], policy: TruncationPolicy \| None = None) -> TruncatedSeries` | Deterministic downsampling of series points preserving key extrema. |


## FEAT-ANLT-19: Deterministic error-code mapping for the analytics service boundary (app.services.analytics.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `AnalyticsError` (exception) | Base exception for analytics domain errors. |
| `AnalyticsValidationError` (exception) | Validation exception for analytics domain. |
| `to_analytics_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Analytics error payload. |


## FEAT-ANLT-20: Group-level composition and aggregation of metrics (ANL-NFR-100) (app.services.analytics.metrics.aggregate)

| Function | Purpose |
|----------|---------|
| `metrics_aggregate_boundary() -> dict[str, object]` | Describe aggregate metric boundary rules from the analytics architecture. |
| `breakeven_epsilon(input_value: object, config: MetricConfig) -> MetricResult[float]` | Return the configured breakeven epsilon value (ANL-NFR-102). |
| `compute_equity_metrics(input_value: object, config: MetricConfig) -> MetricResult[dict[str, Any]]` | Calculate equity metrics from return inputs (ANL-NFR-189). |


## FEAT-ANLT-21: Balance and equity curve construction (ANL-NFR-167) (app.services.analytics.metrics.curves)

| Function | Purpose |
|----------|---------|
| `balance_curve_metric(input_value: object, config: MetricConfig) -> MetricResult[list[dict[str, Any]]]` | Expose balance-curve behavior as a metric (ANL-NFR-168). |
| `equity_curve_metric(input_value: object, config: MetricConfig) -> MetricResult[list[dict[str, Any]]]` | Expose equity-curve behavior as a metric (ANL-NFR-169). |


## FEAT-ANLT-22: Distribution higher moments, outliers, and statistical correction (ANL-NFR-214) (app.services.analytics.metrics.distribution)

| Function | Purpose |
|----------|---------|
| `skewness_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate returns skewness (ANL-NFR-214). |
| `kurtosis_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate returns excess kurtosis (ANL-NFR-215). |
| `percentile_summary(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate standard percentile breaks (ANL-NFR-272). |
| `upside_downside_summary(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, Any]]` | Compare properties of gains versus losses (ANL-NFR-273). |
| `fat_tail_score(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate excess kurtosis as a proxy for tail thickness (ANL-NFR-274). |
| `jarque_bera_test(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate Jarque-Bera statistic and its chi-squared p-value (ANL-NFR-275). |
| `jarque_bera_test_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Alias for jarque_bera_test (ANL-NFR-276). |
| `bootstrap_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Estimate a bootstrapped return metric exceeding a threshold (ANL-NFR-277). |
| `false_discovery_rate(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[list[float]]` | Apply Benjamini-Hochberg FDR adjustments to p-values (ANL-NFR-278). |
| `distribution_summary(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Expose general moments and percentile ranges (ANL-NFR-279). |


## FEAT-ANLT-23: Drawdown statistics, underwater series, recovery duration, and ratios (ANL-NFR-115) (app.services.analytics.metrics.drawdown)

| Function | Purpose |
|----------|---------|
| `validate_request_id_strict(request_id: str \| None) -> None` | Raise ``ValidationError`` when ``request_id`` is present but invalid. |
| `metrics_drawdown_boundary() -> dict[str, bool]` | Describe drawdown metric boundary declarations. |
| `drawdown_series(equity_values: Sequence[float]) -> list[float]` | Compute peak-to-trough fractional drawdown series. |
| `drawdown_duration_series(equity_curve: Any) -> list[float]` | Compute hours-since-peak drawdown duration at each equity point. |
| `trade_pnl_distribution(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate a statistical summary of realized trade PnL (ANL-NFR-115). |
| `trade_level_drawdowns(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]` | AI Tool wrapper for _trade_level_drawdowns_impl. |
| `trade_level_drawdowns_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Expose trade_level_drawdowns as a metric (ANL-NFR-116). |
| `max_close_to_close_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum trade-level peak-to-valley decline (ANL-NFR-117). |
| `avg_trade_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate mean trade-level close-to-close drawdown depth (ANL-NFR-118). |
| `max_consecutive_drawdown_trades(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[int]` | Calculate maximum number of consecutive trades inside drawdown (ANL-NFR-119). |
| `max_close_to_close_drawdown_date(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[str]` | Identify the timestamp of deepest trade-level valley (ANL-NFR-120). |
| `drawdown_series_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Calculate drawdown values from an equity curve (ANL-NFR-183). |
| `drawdown_duration_series_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Calculate drawdown duration values from an equity curve (ANL-NFR-184). |
| `max_drawdown_duration_from_equity(equity: Any, config: Any = None) -> Any` | Calculate maximum drawdown duration from equity values (ANL-NFR-185). |
| `max_strategy_drawdown_date(equity: Any, config: Any = None) -> Any` | Identify the timestamp of deepest strategy equity valley (ANL-NFR-186). |
| `avg_underwater_drawdown_percent(equity: Any, config: Any = None) -> Any` | Calculate average drawdown depth while equity is below peak (ANL-NFR-187). |
| `calculate_drawdown_metrics(equity: Any, config: Any = None, request_id: str \| None = None) -> Any` | Compute a full drawdown metric bundle from an equity curve. |
| `max_relative_drawdown_percent(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum relative underperformance as a positive percentage (ANL-NFR-220). |
| `max_strategy_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate deepest peak-to-valley decline in currency units (ANL-NFR-221). |
| `max_strategy_drawdown_percent(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate deepest percentage decline relative to running peak (ANL-NFR-222). |
| `max_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum drawdown from returns (ANL-NFR-223). |
| `avg_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average drawdown depth (ANL-NFR-224). |
| `drawdown_distribution(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate detailed drawdown distribution statistics (ANL-NFR-225). |
| `max_drawdown_duration_from_returns(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum drawdown duration from return values (ANL-NFR-226). |
| `max_drawdown_duration(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum drawdown duration (ANL-NFR-227). |
| `avg_drawdown_duration(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average duration of drawdown episodes (ANL-NFR-228). |
| `time_to_recovery(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Calculate recovery periods for unique drawdowns (ANL-NFR-229). |
| `recovery_factor(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate net profit relative to maximum drawdown (ANL-NFR-230). |
| `max_close_to_close_drawdown_percent(trades: pd.DataFrame, initial_balance: float, closed_only: bool = True) -> dict[str, Any]` | AI Tool wrapper for _max_close_to_close_drawdown_percent_impl. |
| `account_size_required(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Estimate capital required to withstand max close-to-close dips (ANL-NFR-232). |
| `avg_yearly_max_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Average the maximum drawdown observed in each year (ANL-NFR-233). |
| `ulcer_index(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate squared-drawdown-based ulcer index (ANL-NFR-234). |
| `pain_index(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate mean absolute percentage drawdown (ANL-NFR-235). |
| `pain_ratio(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return relative to pain index (ANL-NFR-236). |
| `sterling_ratio(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate CAGR relative to adjusted average yearly maximum drawdown (ANL-NFR-239). |
| `rina_index(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate select net profit relative to average drawdown and time in market (ANL-NFR-240). |
| `return_on_max_strategy_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate total return relative to maximum strategy drawdown (ANL-NFR-242). |
| `return_on_max_close_to_close_drawdown(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate net profit relative to maximum close-to-close drawdown (ANL-NFR-243). |
| `drawdown_probability(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate probability of drawdown exceeding a threshold (ANL-NFR-244). |


## FEAT-ANLT-24: MAE/MFE and return-efficiency calculations (ANL-NFR-121) (app.services.analytics.metrics.efficiency)

| Function | Purpose |
|----------|---------|
| `metrics_efficiency_boundary() -> dict[str, bool]` | Describe efficiency metric boundary declarations. |
| `avg_trade_notional_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate mean PnL per unit of notional exposure (ANL-NFR-121). |
| `return_per_trade_hour(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate net profit per hour spent in active trades (ANL-NFR-123). |
| `return_per_market_hour(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate net profit per hour where at least one trade was open (ANL-NFR-124). |
| `trades_per_day(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _trades_per_day_impl. |
| `profit_per_trade_per_day(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _profit_per_trade_per_day_impl. |
| `mfe_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average percentage of MFE captured by winning trades (ANL-NFR-127). |
| `aggregate_mfe_capture_ratio(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate aggregate MFE capture ratio for winning trades (ANL-NFR-128). |
| `mae_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate realized-loss-to-MAE efficiency for losing trades (ANL-NFR-129). |
| `aggregate_loss_containment_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate aggregate loss containment for losing trades (ANL-NFR-130). |
| `position_size_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate relationship between position size and normalized trade outcome (ANL-NFR-131). |
| `calculate_efficiency_metrics(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate aggregate MAE/MFE efficiency context from trades (ANL-NFR-132). |
| `trade_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate realized outcome relative to maximum favorable excursion (ANL-NFR-157). |
| `capital_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate return per unit of nominal capital deployed (ANL-NFR-368). |
| `return_per_unit_mae(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total return relative to adverse excursion experienced (ANL-NFR-369). |
| `return_per_calendar_day(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _return_per_calendar_day_impl. |
| `exit_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate combined win-capture and loss-containment efficiency (ANL-NFR-371). |
| `loss_containment_efficiency(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate how well realized losses stayed above their adverse excursion (ANL-NFR-372). |
| `median_mae_mfe(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate median MAE and MFE values (ANL-NFR-375). |
| `get_mae_mfe_r(trades: Sequence[TradeRecord], config: MetricConfig) -> tuple[dict[str, float], ...]` | Calculate MAE and MFE normalized to R-space (ANL-NFR-376). |
| `median_mae_r(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median MAE in R-multiple terms (ANL-NFR-377). |
| `median_mfe_r(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median MFE in R-multiple terms (ANL-NFR-378). |


## FEAT-ANLT-25: Equity returns, resampling, and distribution calculations (ANL-NFR-181) (app.services.analytics.metrics.equity)

| Function | Purpose |
|----------|---------|
| `returns_series(equity_values: Sequence[float]) -> list[float]` | Compute period-over-period simple returns. |
| `log_returns_series(equity_values: Sequence[float]) -> list[float]` | Compute period-over-period log returns. |
| `return_volatility(returns: Sequence[float]) -> float` | Compute sample standard deviation of a return series. |
| `total_return_usd(equity: Any, config: Any = None) -> Any` | Calculate total return in currency units (ANL-NFR-190). |
| `returns_series_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Calculate percentage returns between equity points (ANL-NFR-191). |
| `log_returns_series_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[list[float]]` | Calculate logarithmic returns between equity points (ANL-NFR-192). |
| `daily_returns(equity: Any, config: Any = None) -> Any` | Calculate daily percentage returns from an equity curve (ANL-NFR-193). |
| `weekly_returns(equity: Any, config: Any = None) -> Any` | Calculate weekly percentage returns from an equity curve (ANL-NFR-194). |
| `monthly_returns(equity: Any, config: Any = None) -> Any` | Calculate monthly percentage returns from an equity curve (ANL-NFR-195). |
| `annual_returns(equity: Any, config: Any = None) -> Any` | Calculate annual percentage returns from an equity curve (ANL-NFR-196). |
| `win_loss_streaks(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[dict[str, list[int]]]` | Return winning and losing streak sequences (ANL-NFR-203). |
| `kelly_criterion(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate Kelly criterion percentage from R-multiples or returns (ANL-NFR-204). |
| `avg_monthly_return(equity: Any, config: Any = None) -> Any` | Calculate arithmetic average monthly return (ANL-NFR-205). |
| `monthly_return_stddev(equity: Any, config: Any = None) -> Any` | Calculate monthly return volatility (ANL-NFR-206). |
| `geometric_mean_return_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate geometric mean return (ANL-NFR-208). |
| `best_return(equity_or_returns: Any, config: Any = None) -> Any` | Calculate best single-period return (ANL-NFR-209). |
| `worst_return(equity_or_returns: Any, config: Any = None) -> Any` | Calculate worst single-period return (ANL-NFR-210). |
| `buy_and_hold_return(equity_or_prices: Any, config: Any = None) -> Any` | Calculate total buy-and-hold return from price data (ANL-NFR-211). |
| `return_volatility_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return standard deviation (ANL-NFR-212). |
| `downside_return_volatility_metric(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate volatility of returns below target (ANL-NFR-213). |
| `return_skewness(equity_or_returns: Any, config: Any = None) -> Any` | Calculate return-distribution skewness (ANL-NFR-214). |
| `return_kurtosis(equity_or_returns: Any, config: Any = None) -> Any` | Calculate return-distribution excess kurtosis (ANL-NFR-215). |
| `return_on_account(equity: Sequence[EquityPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return on required account size (ANL-NFR-216). |
| `calculate_equity_metrics(equity_curve: Any, request_id: str \| None = None) -> StandardResponse` | Calculate aggregate return and drawdown metrics from an equity curve. |


## FEAT-ANLT-26: Compatibility aliases resolving name collisions across modules (ANL-NFR-016) (app.services.analytics.metrics.exports)

| Function | Purpose |
|----------|---------|
| `common_avg_loss(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose common-module average-loss behavior without collision (ANL-NFR-016). |
| `common_get_r_multiples(input_value: object, config: MetricConfig) -> MetricResult[tuple[float, ...]]` | Expose common-module R-multiple behavior without collision (ANL-NFR-017). |
| `metrics_get_r_multiples(input_value: object, config: MetricConfig) -> MetricResult[tuple[float, ...]]` | Expose metrics-module R-multiple behavior without collision (ANL-NFR-020). |
| `metrics_avg_loss(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose metrics-module average-loss behavior without collision (ANL-NFR-029). |
| `benchmark_information_ratio(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose benchmark information ratio without colliding with ratios module export (ANL-NFR-281). |
| `metrics_win_rate_fraction(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose metrics-module win-rate fraction behavior without ratios collision (ANL-NFR-283). |
| `metrics_expectancy_r(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose metrics-module R-expectancy behavior without ratios collision (ANL-NFR-284). |
| `ratios_information_ratio(input_value: object, config: MetricConfig) -> MetricResult[float]` | Expose ratios-module information ratio without benchmark collision (ANL-NFR-288). |
| `distributions_r_multiple_distribution(input_value: object, config: MetricConfig) -> MetricResult[dict[str, float]]` | Expose distribution-module R-multiple distribution behavior without collision (ANL-NFR-318). |
| `metrics_r_multiple_distribution(input_value: object, config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate R-multiple distribution statistics (ANL-NFR-339). |


## FEAT-ANLT-27: PnL, CAGR, and select/adjusted profit calculations (ANL-NFR-050) (app.services.analytics.metrics.pnl)

| Function | Purpose |
|----------|---------|
| `total_return(trades_or_equity: Any, config: Any = None) -> Any` | Calculate total return as a percentage of initial capital (ANL-NFR-077). |
| `net_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total realized profit or loss from closed trades (ANL-NFR-164). |
| `gross_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Sum winning closed-trade profit (ANL-NFR-165). |
| `gross_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Sum losing closed-trade loss (ANL-NFR-166). |
| `balance_curve_from_closed_trades(trades: pd.DataFrame, initial_balance: float, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _balance_curve_from_closed_trades_impl. |
| `balance_curve(trades: pd.DataFrame, initial_balance: float, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _balance_curve_impl. |
| `equity_curve(trades: pd.DataFrame, initial_balance: float, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _equity_curve_impl. |
| `cagr(initial_value: float, final_value: float, years: float) -> float` | Compute compound annual growth rate (ANL-NFR-050). |
| `compound_monthly_growth_rate(trades_or_initial: Any, config_or_final: Any = None, months: Any = None) -> Any` | Compute compound monthly growth rate (ANL-NFR-051). |
| `annualized_return(rets: pd.Series, periods_per_year: int = 252) -> dict[str, Any]` | AI Tool wrapper for _annualized_return_impl. |
| `geometric_mean_return(rets: pd.Series) -> dict[str, Any]` | AI Tool wrapper for _geometric_mean_return_impl. |
| `buy_and_hold_cagr(trades_or_prices: Any, config_or_years: Any = None) -> Any` | Compute buy-and-hold CAGR from price data (ANL-NFR-052). |
| `downside_return_volatility(rets: pd.Series, target: float = 0.0) -> dict[str, Any]` | AI Tool wrapper for _downside_return_volatility_impl. |
| `adjusted_gross_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Sum winning PnL excluding extreme outliers (ANL-NFR-053). |
| `adjusted_gross_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Sum losing PnL excluding extreme outliers (ANL-NFR-054). |
| `adjusted_net_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Compute net profit after removing outliers from both tails (ANL-NFR-055). |
| `select_net_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Compute net profit after trimming 2 % from each tail (ANL-NFR-056). |
| `select_gross_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Compute gross profit after trimming the top 2 % of wins (ANL-NFR-057). |
| `select_gross_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Compute gross loss after trimming the bottom 2 % of losses (ANL-NFR-058). |
| `return_on_initial_capital(trades_or_equity: Any, config: Any = None) -> Any` | Calculate net profit as a percentage of initial capital (ANL-NFR-078). |
| `max_runup(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Find the maximum gain from valley to peak (ANL-NFR-059). |
| `max_runup_date(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[str]` | Identify the timestamp of maximum runup peak (ANL-NFR-060). |
| `calculate_return_metrics(*, equity_curve: list[float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_return_metrics_impl. |
| `calculate_period_analysis(*, records: list[dict[str, Any]], value_column: str = 'return', request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_period_analysis_impl. |
| `calculate_long_short_split(*, trades: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_long_short_split_impl. |
| `calculate_session_performance(*, records: list[dict[str, Any]], value_column: str = 'return', request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_session_performance_impl. |
| `cagr_metric(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | CAGR metric from trades (ANL-NFR-050). |
| `return_over_drawdown(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total return relative to maximum trade drawdown (ANL-NFR-162). |
| `adjusted_net_profit_as_percent_of_max_trade_drawdown(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate adjusted net profit as a percentage of max trade drawdown (ANL-NFR-163). |


## FEAT-ANLT-28: Position exposure metrics calculation kernel (ANL-NFR-018) (app.services.analytics.metrics.position_exposure)

| Function | Purpose |
|----------|---------|
| `max_gross_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate the maximum individual absolute trade size (ANL-NFR-018). |
| `max_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum total contracts held (ANL-NFR-031). |
| `max_net_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum net directional size held (ANL-NFR-032). |
| `max_long_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum total long contracts held (ANL-NFR-033). |
| `max_short_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum total short contracts held (ANL-NFR-034). |
| `open_position_pnl(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total unrealized PnL from open positions (ANL-NFR-025). |
| `slippage_paid(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total absolute slippage costs paid (ANL-NFR-026). |
| `commission_paid(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total absolute commission costs paid (ANL-NFR-027). |
| `swap_paid(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total absolute swap costs paid (ANL-NFR-028). |


## FEAT-ANLT-29: R-multiple metrics calculation kernel (ANL-NFR-114) (app.services.analytics.metrics.r_multiples)

| Function | Purpose |
|----------|---------|
| `get_r_multiples(trades: Sequence[TradeRecord], config: MetricConfig \| None = None) -> tuple[list[float], list[str]]` | Calculate R-multiples for each trade (ANL-NFR-114). |
| `avg_return_per_risk_unit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average R-multiple per closed trade (ANL-NFR-122). |
| `compute_trade_metrics(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate trade metrics from numeric R values and optional MAE/MFE arrays (ANL-NFR-156). |


## FEAT-ANLT-30: Ratio and performance index calculations (ANL-NFR-218) (app.services.analytics.metrics.ratios)

| Function | Purpose |
|----------|---------|
| `normal_cdf(x: float) -> float` | Standard normal cumulative distribution function. |
| `sharpe_ratio(returns_in: pd.Series \| np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 252, annualize: bool = True) -> dict[str, Any]` | AI Tool wrapper for _sharpe_ratio_impl. |
| `sortino_ratio(returns_in: pd.Series \| np.ndarray, target_return: float = 0.0, periods_per_year: int = 252, annualize: bool = True) -> dict[str, Any]` | AI Tool wrapper for _sortino_ratio_impl. |
| `omega_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate gains-to-losses relative to target threshold Omega ratio (ANL-NFR-220). |
| `probabilistic_sharpe_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate probabilistic Sharpe ratio (ANL-NFR-221). |
| `tail_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate 95th percentile divided by absolute 5th percentile return (ANL-NFR-222). |
| `profit_factor(trades: Sequence[TradeRecord]) -> float` | Calculate gross winning profit divided by absolute gross losing loss (ANL-NFR-223). |
| `profit_factor_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Profit factor exposed as a metric wrapper (ANL-NFR-223). |
| `profit_factor_by_volume(trades: Sequence[TradeRecord]) -> float` | Calculate sum of volume of winning trades divided by losing trades (ANL-NFR-224). |
| `profit_factor_by_volume_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Profit factor by volume exposed as a metric (ANL-NFR-224). |
| `payoff_ratio(trades: Sequence[TradeRecord], config: MetricConfig \| None = None) -> float` | Calculate average win divided by average absolute loss (ANL-NFR-225). |
| `payoff_ratio_metric(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Payoff ratio exposed as a metric (ANL-NFR-225). |
| `average_win_loss_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Alias for payoff_ratio_metric (ANL-NFR-226). |
| `adjusted_profit_factor(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate profit factor excluding outliers (ANL-NFR-227). |
| `select_profit_factor(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate select profit factor excluding largest wins/losses (ANL-NFR-228). |
| `adjusted_payoff_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average winning trade PnL to average losing trade PnL excluding outliers (ANL-NFR-228). |
| `cpc_index(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate Sunny Harris CPC Index (ANL-NFR-229). |
| `system_quality_number(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate Van Tharp System Quality Number (ANL-NFR-230). |
| `information_ratio(returns_in: pd.Series, benchmark_returns: pd.Series, annualize: bool = True, periods_per_year: int = 252) -> dict[str, Any]` | AI Tool wrapper for _information_ratio_impl. |
| `treynor_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate excess return per unit of systematic risk (ANL-NFR-233). |
| `active_premium(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate annualized difference between strategy and benchmark return (ANL-NFR-234). |
| `expectancy(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate arithmetic expectancy per trade (ANL-NFR-236). |
| `expectancy_r(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate mean R-multiple (ANL-NFR-237). |
| `profit_loss_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average winning trade PnL to average losing trade PnL (ANL-NFR-238). |
| `gain_loss_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate total gains divided by total absolute losses (ANL-NFR-239). |
| `win_loss_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate win count divided by loss count (ANL-NFR-240). |
| `profit_factor_by_count(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate win count divided by loss count (ANL-NFR-241). |
| `loss_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate loss count divided by total trade count (ANL-NFR-242). |
| `ulcer_performance_index(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate annualized return divided by ulcer index (ANL-NFR-243). |
| `martin_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate annualized return divided by ulcer index (ANL-NFR-244). |
| `adjusted_expectancy(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate expectancy excluding outlier trades (ANL-NFR-245). |
| `ratio_of_adjusted_gross_profit_to_adjusted_gross_loss(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate adjusted gross profit divided by adjusted gross loss (ANL-NFR-246). |
| `expected_value(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate probability-weighted outcome in currency units (ANL-NFR-247). |
| `expected_value_r(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate probability-weighted outcome in R-multiple units (ANL-NFR-248). |
| `odds_calculator(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate probability odds indicators (ANL-NFR-249). |
| `risk_reward_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate risk-reward ratio (ANL-NFR-250). |
| `drawdown_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return over maximum drawdown ratio (ANL-NFR-251). |
| `annualized_sharpe_ratio(monthly_returns: pd.Series, risk_free_rate_monthly: float = 0.0) -> dict[str, Any]` | AI Tool wrapper for _annualized_sharpe_ratio_impl. |
| `gain_to_pain_ratio(returns_in: pd.Series) -> dict[str, Any]` | AI Tool wrapper for _gain_to_pain_ratio_impl. |
| `kappa_ratio(returns_in: pd.Series \| np.ndarray, target: float = 0.0, order: int = 3) -> dict[str, Any]` | AI Tool wrapper for _kappa_ratio_impl. |
| `edge_ratio(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _edge_ratio_impl. |
| `profit_to_mae_ratio(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _profit_to_mae_ratio_impl. |
| `mfe_to_mae_ratio(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _mfe_to_mae_ratio_impl. |
| `expectancy_over_std(trades: list[dict[str, Any]]) -> float` | Compute expectancy divided by standard deviation of PnL. |
| `net_profit_as_percent_of_largest_loss(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _net_profit_as_percent_of_largest_loss_impl. |
| `select_net_profit_as_percent_of_largest_loss(select_net_profit: float, largest_loss: float) -> float` | Express trimmed net profit as a percentage of largest loss. |
| `adjusted_net_profit_as_percent_of_largest_loss(adjusted_net_profit: float, largest_loss: float) -> float` | Express adjusted net profit as a percentage of largest loss. |
| `calculate_ratio_metrics(*, returns: list[float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_ratio_metrics_impl. |
| `up_down_capture(strategy_returns: Sequence[float], benchmark_returns: Sequence[float]) -> dict[str, float]` | Calculate up-capture and down-capture ratios. |
| `calmar_ratio(cagr_value: float \| pd.Series \| np.ndarray, max_dd: float \| None = None, periods_per_year: int = 252) -> dict[str, Any]` | AI Tool wrapper for _calmar_ratio_impl. |
| `fouse_ratio(monthly_returns: pd.Series \| np.ndarray, risk_tolerance: float, risk_free_rate_monthly: float = 0.0) -> dict[str, Any]` | AI Tool wrapper for _fouse_ratio_impl. |
| `net_profit_as_percent_of_max_trade_drawdown(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _net_profit_as_percent_of_max_trade_drawdown_impl. |
| `net_profit_as_percent_of_max_strategy_drawdown(net_profit_val: float, max_strategy_drawdown: float) -> dict[str, Any]` | AI Tool wrapper for _net_profit_as_percent_of_max_strategy_drawdown_impl. |
| `select_net_profit_as_percent_of_max_trade_drawdown(trades: pd.DataFrame) -> dict[str, Any]` | AI Tool wrapper for _select_net_profit_as_percent_of_max_trade_drawdown_impl. |
| `select_net_profit_as_percent_of_max_strategy_drawdown(select_net_profit_val: float, max_strategy_drawdown: float) -> dict[str, Any]` | AI Tool wrapper for _select_net_profit_as_percent_of_max_strategy_drawdown_impl. |
| `adjusted_net_profit_as_percent_of_max_strategy_drawdown(adjusted_net_profit_val: float, max_strategy_drawdown: float) -> dict[str, Any]` | AI Tool wrapper for _adjusted_net_profit_as_percent_of_max_strategy_drawdown_impl. |


## FEAT-ANLT-31: Risk and volatility calculations (ANL-NFR-170) (app.services.analytics.metrics.risk)

| Function | Purpose |
|----------|---------|
| `max_loss_probability(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate probability of a single trade loss exceeding a threshold (ANL-NFR-170). |
| `risk_of_ruin(trades: pd.DataFrame, risk_per_trade_pct: float \| None = None, target_drawdown_pct: float = 50.0, num_simulations: int = 10000, **kwargs) -> dict[str, Any]` | AI Tool wrapper for _risk_of_ruin_impl. |
| `avg_trade_nominal_exposure(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average nominal exposure per trade (ANL-NFR-172). |
| `max_single_trade_margin_utilization(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum margin used by a single trade as a percentage of equity (ANL-NFR-173). |
| `avg_single_trade_margin_utilization(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate average margin used per trade as a percentage of equity (ANL-NFR-174). |
| `risk_of_ruin_with_custom_horizon(trades: pd.DataFrame, risk_per_trade_pct: float, horizon: int, target_drawdown_pct: float = 50.0, num_simulations: int = 10000) -> dict[str, Any]` | AI Tool wrapper for _risk_of_ruin_with_custom_horizon_impl. |
| `risk_adjusted_efficiency(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return relative to total defined initial risk (ANL-NFR-254). |
| `profit_per_pip_risk(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate reward-to-risk based on profit pips relative to MAE pips (ANL-NFR-255). |
| `upside_potential_ratio(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate upside potential relative to downside risk (ANL-NFR-256). |
| `volatility(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate return standard deviation as a positive percentage (ANL-NFR-257). |
| `annualized_volatility(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate annualized volatility as a positive percentage (ANL-NFR-258). |
| `downside_volatility(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate downside deviation as a positive percentage (ANL-NFR-259). |
| `value_at_risk(rets: pd.Series \| np.ndarray, confidence: float = 0.95, method: Literal['historical', 'parametric'] = 'historical') -> dict[str, Any]` | AI Tool wrapper for _value_at_risk_impl. |
| `conditional_var(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate conditional value-at-risk as a positive percentage (ANL-NFR-261). |
| `expected_shortfall(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate expected shortfall (ANL-NFR-262). |
| `max_nominal_exposure_simple(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum nominal exposure held at one time (ANL-NFR-263). |
| `max_gross_exposure(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[float]` | Calculate maximum gross nominal exposure (ANL-NFR-264). |
| `exposure_time_ratio(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _exposure_time_ratio_impl. |
| `time_weighted_avg_exposure(trades: pd.DataFrame, contract_size: float = 100000.0, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _time_weighted_avg_exposure_impl. |
| `portfolio_margin_utilization_curve(trades: pd.DataFrame, account_equity: float, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _portfolio_margin_utilization_curve_impl. |
| `compounding_risk_of_ruin(trades: pd.DataFrame, risk_fraction: float, target_drawdown_pct: float = 50.0, num_simulations: int = 10000) -> dict[str, Any]` | AI Tool wrapper for _compounding_risk_of_ruin_impl. |
| `historical_var_by_symbol(returns: Sequence[ReturnPoint], config: MetricConfig) -> MetricResult[dict[str, float]]` | Calculate historical value-at-risk by symbol (ANL-NFR-269). |
| `portfolio_var_from_covariance(returns_df: pd.DataFrame, weights: np.ndarray \| None = None, confidence: float = 0.95) -> dict[str, Any]` | AI Tool wrapper for _portfolio_var_from_covariance_impl. |
| `calculate_risk_metrics(*, returns: list[float], alpha: float = 0.05, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_risk_metrics_impl. |


## FEAT-ANLT-32: Trade duration and market presence calculations (ANL-NFR-061) (app.services.analytics.metrics.time_analysis)

| Function | Purpose |
|----------|---------|
| `avg_time_in_trade(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average trade duration in hours (ANL-NFR-191). |
| `median_time_in_trade(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median trade duration in hours (ANL-NFR-192). |
| `max_time_in_trade(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum trade duration in hours (ANL-NFR-193). |
| `min_time_in_trade(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate minimum trade duration in hours (ANL-NFR-194). |
| `time_in_market_duration_metric(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate total duration where at least one position was open in hours (ANL-NFR-313). |


## FEAT-ANLT-33: Trade outcomes calculation kernel (ANL-NFR-021) (app.services.analytics.metrics.trade_outcomes)

| Function | Purpose |
|----------|---------|
| `avg_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate the mean loss of losing trades (ANL-NFR-113). |
| `get_ordered_closed_trades(trades: Sequence[TradeRecord], config: MetricConfig \| None = None) -> tuple[TradeRecord, ...]` | Sort closed trades chronologically (ANL-NFR-133). |
| `win_rate_fraction(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate win rate on a 0-to-1 scale (ANL-NFR-021). |
| `avg_win_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate ratio of mean winning to mean losing outcomes (ANL-NFR-022). |
| `consecutive_wins_losses(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[dict[str, int]]` | Calculate maximum consecutive wins and losses from numeric outcomes (ANL-NFR-023). |
| `t_statistic(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate the t-statistic for mean outcome (ANL-NFR-024). |
| `total_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed trades (ANL-NFR-134). |
| `winning_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed winning trades (ANL-NFR-135). |
| `losing_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed losing trades (ANL-NFR-136). |
| `breakeven_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed breakeven trades (ANL-NFR-137). |
| `long_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed long trades (ANL-NFR-138). |
| `short_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count closed short trades (ANL-NFR-139). |
| `count_open_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Count currently open trades (ANL-NFR-140). |
| `win_rate(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate percentage of winning trades (ANL-NFR-141). |
| `loss_rate(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate percentage of losing trades (ANL-NFR-142). |
| `avg_win(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate mean profit of winning trades (ANL-NFR-143). |
| `largest_win(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum single-trade profit (ANL-NFR-144). |
| `largest_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum single-trade loss (ANL-NFR-145). |
| `median_win(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median PnL of winning trades (ANL-NFR-146). |
| `median_loss(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median PnL of losing trades (ANL-NFR-147). |
| `avg_r_multiple(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average R-multiple (ANL-NFR-035). |
| `median_r_multiple(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate median R-multiple (ANL-NFR-036). |
| `r_expectancy(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate R-space expectancy (ANL-NFR-037). |
| `max_r_multiple(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate maximum R-multiple (ANL-NFR-038). |
| `min_r_multiple(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate minimum R-multiple (ANL-NFR-039). |
| `max_consecutive_wins(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Calculate maximum consecutive winning trades (ANL-NFR-149). |
| `max_consecutive_losses(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[int]` | Calculate maximum consecutive losing trades (ANL-NFR-150). |
| `avg_consecutive_wins(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average length of winning streaks (ANL-NFR-040). |
| `avg_consecutive_losses(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate average length of losing streaks (ANL-NFR-041). |
| `compute_r_trade_metrics(r_values: np.ndarray, mae_r: np.ndarray \| None = None, mfe_r: np.ndarray \| None = None) -> dict[str, Any]` | AI Tool wrapper for _compute_r_trade_metrics_impl. |
| `r_signal_to_noise(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate mean R relative to R volatility (ANL-NFR-042). |
| `rolling_expectancy_stability(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate expectancy stability over a rolling window (ANL-NFR-043). |
| `win_after_win_probability(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate probability that a win follows a win (ANL-NFR-044). |
| `runs_test_zscore(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate Wald-Wolfowitz runs-test z-score (ANL-NFR-045). |
| `trading_period_duration(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _trading_period_duration_impl. |
| `trade_outcome_entropy(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Calculate Shannon entropy of trade outcomes (ANL-NFR-158). |
| `longest_flat_period_duration(trades: pd.DataFrame, start_time: pd.Timestamp \| None = None, end_time: pd.Timestamp \| None = None) -> dict[str, Any]` | AI Tool wrapper for _longest_flat_period_duration_impl. |
| `calculate_trade_metrics(*, trades: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_trade_metrics_impl. |
| `parse_utc_time(t_val: Any) -> datetime \| None` | Parse any timestamp representation to a UTC-aware ``datetime``. |
| `get_closed_trades(trades: Sequence[TradeRecord], config: MetricConfig \| None = None) -> tuple[TradeRecord, ...]` | Filter to closed trades (ANL-NFR-111, ANL-NFR-101). |
| `classify_trades(trades: Sequence[TradeRecord], config: MetricConfig) -> dict[str, list[TradeRecord]]` | Partition trades into wins, losses, and breakevens (ANL-NFR-112, ANL-NFR-102). |
| `avg_win_metric(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Expose average win as MetricResult. |
| `avg_loss_metric(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Expose average loss as MetricResult. |
| `expectancy_metric(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Expose trade expectancy as MetricResult. |
| `loss_rate_fraction(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[float]` | Expose loss rate fraction as MetricResult. |


## FEAT-ANLT-34: Analytics Registry module (app.services.analytics.registry.analytics_registry)

| Function | Purpose |
|----------|---------|
| `RegisteredToolEntry` (dataclass) | Registry entry configuration for an analytics public capability or tool. |
| `register_tool(name: str, stability: Literal["stable", "approved_experimental", "deprecated", "internal_support_only"], safe_for_agent_api: bool, category: Literal["official_tool", "internal_metric_kernel", "compatibility_alias", "deprecated_export"], aliases: tuple[str, ...] = ()) -> Callable[[Any], Any]` | Decorator to register a capability in the central registry (ANL-NFR-008). |
| `get_active_requests() -> set[str]` | Retrieve active requests registered in the local observability log. |
| `clear_active_requests() -> None` | Clear all active requests in the local observability log. |
| `request_id(input_value: object, config: MetricConfig) -> MetricResult[object]` | Extract, validate, and record request_id for traceability (ANL-NFR-009). |


## FEAT-ANLT-35: Report formatters and serializers for Analytics (app.services.analytics.reports.formatters)

| Function | Purpose |
|----------|---------|
| `ReportFormat` (enum) | Supported export formats for Analytics reports. |
| `SerializedReport` (dataclass) | Container for serialized report content. |
| `format_summary_as_rows(report: object, config: MetricConfig \| None = None) -> list[dict[str, Any]] \| MetricResult[object]` | Format raw summary data into display rows. |
| `serialize_report(report: AnalyticsReport \| dict[str, Any], report_format: ReportFormat) -> SerializedReport` | Serialize report object or dict representation deterministically. |


## FEAT-ANLT-36: Canonical, deterministic report hash creation for Analytics (app.services.analytics.reports.hashes)

| Function | Purpose |
|----------|---------|
| `HashPolicy` (enum) | Policies for computing report verification hashes. |
| `compute_report_hash(report: dict[str, Any] \| object, policy: HashPolicy \| None = None) -> str` | Compute deterministic hash of report sections, excluding metadata. |


## FEAT-ANLT-37: Report composition orchestrations for Analytics (app.services.analytics.reports.sections)

| Function | Purpose |
|----------|---------|
| `PortfolioAnalyticsReport` (dataclass) | Versioned portfolio analytics report schema wrapper. |
| `evaluate_section(section_name: str, status: str, data: dict[str, Any] \| None = None, *, criticality: str = "optional", diagnostic_partial_mode: bool = False, warning: dict[str, Any] \| None = None, quality_flag: dict[str, Any] \| None = None) -> dict[str, Any]` | Evaluate report-section status and partial-report metadata. |
| `build_analytics_report(trading_result: dict[str, Any], diagnostic_partial_mode: bool = False, request_id: str \| None = None) -> StandardResponse` | Build a structured backtest or live trading analytics report. |
| `build_portfolio_analytics_report(portfolio_result: dict[str, Any], request_id: str \| None = None) -> StandardResponse` | Build an aggregated portfolio report from component strategy results. |
| `compare_analytics_reports(reference_report: dict[str, Any], candidate_report: dict[str, Any], request_id: str \| None = None) -> StandardResponse` | Compare performance metrics between two strategy run reports. |
| `calculate_statistical_validation(returns: object, request_id: str \| None = None) -> StandardResponse` | Package a comprehensive statistical validation report. |
| `calculate_prop_firm_compliance(report: dict[str, Any], request_id: str \| None = None) -> StandardResponse` | Verify strategy compliance metrics against standard prop firm limits. |


## FEAT-ANLT-38: Labeling policy boundaries and separations for Scorecards (app.services.analytics.scorecards.labels)

| Function | Purpose |
|----------|---------|
| `scorecards_policy_boundary() -> None` | Pure architectural boundary declaration for scorecard labeling policy. |


## FEAT-ANLT-39: Strategy quality scorecard evaluations for Analytics (app.services.analytics.scorecards.quality)

| Function | Purpose |
|----------|---------|
| `NonBindingRecommendation` (dataclass) | Non-binding recommendation container. |
| `StrategyQualityAssessment` (dataclass) | Non-binding strategy-quality scorecard result assessment. |
| `StrategyQualityConfig` (dataclass) | Configuration options for strategy quality scorecard rules. |
| `ScorecardRule` (dataclass) | Non-binding analytics scorecard rule. |
| `ScorecardResult` (dataclass) | Non-binding strategy-quality scorecard result wrapper. |
| `sqn(report: AnalyticsReport \| dict[str, Any] \| None, _config: StrategyQualityConfig \| None = None) -> StrategyQualityAssessment` | Calculate and assess System Quality Number (SQN). |
| `sample_size_warning(report: AnalyticsReport \| dict[str, Any] \| None, config: StrategyQualityConfig \| None = None) -> StrategyQualityAssessment` | Assess metric reliability based on trade sample size. |
| `evaluate_strategy_quality(report: AnalyticsReport \| dict[str, Any] \| None, config: StrategyQualityConfig \| None = None, request_id: str \| None = None) -> StandardResponse` | Evaluate a strategy report to provide a non-binding quality score. |


## FEAT-ANLT-40: Statistical distributions and profiling diagnostics for Analytics (app.services.analytics.statistics.distributions)

| Function | Purpose |
|----------|---------|
| `statistics_distribution_boundary() -> dict[str, bool]` | Describe distribution statistics boundary declarations. |
| `skewness(values: Sequence[float] \| object) -> float` | Compute the Fisher-Pearson coefficient of skewness. |
| `kurtosis(data: pd.Series \| np.ndarray) -> dict[str, Any]` | AI Tool wrapper for _kurtosis_impl. |
| `higher_moments(values: Sequence[float] \| object) -> dict[str, float]` | Compute standard higher moments (mean, std, skewness, kurtosis). |
| `shapiro_wilk_test(values: Sequence[float] \| object) -> dict[str, float]` | Run a Shapiro-Wilk normality diagnostic approximation. |
| `qq_plot_data(values: Sequence[float] \| object) -> list[dict[str, float]]` | Generate theoretical and actual quantile data for Q-Q plotting. |
| `fit_distribution(data: pd.Series \| np.ndarray, dist_name: Literal['norm', 't', 'lognorm', 'gamma'] = 'norm') -> dict[str, Any]` | AI Tool wrapper for _fit_distribution_impl. |
| `distribution_fit_quality(data: pd.Series \| np.ndarray, dist_name: Literal['norm', 't', 'lognorm', 'gamma'] = 'norm') -> dict[str, Any]` | AI Tool wrapper for _distribution_fit_quality_impl. |
| `histogram_data(values: Sequence[float] \| object, bins: int = 10) -> dict[str, list[float]]` | Generate histogram bin data for plotting. |
| `detect_outliers(data: pd.Series \| np.ndarray, method: Literal['zscore', 'iqr'] = 'zscore', threshold: float \| None = None) -> dict[str, Any]` | AI Tool wrapper for _detect_outliers_impl. |
| `outlier_ratio(data: pd.Series \| np.ndarray, method: Literal['zscore', 'iqr'] = 'zscore', threshold: float \| None = None) -> dict[str, Any]` | AI Tool wrapper for _outlier_ratio_impl. |
| `return_distribution(values: Sequence[float] \| object) -> dict[str, float]` | Calculate a statistical summary of returns. |
| `r_multiple_distribution(values: Sequence[float] \| object) -> dict[str, float]` | Calculate a statistical summary of R-multiple values. |
| `calculate_distribution_metrics(*, values: list[float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | AI Tool wrapper for _calculate_distribution_metrics_impl. |


## FEAT-ANLT-41: Statistical multiple hypothesis testing and corrections for Analytics (app.services.analytics.statistics.multiple_testing)

| Function | Purpose |
|----------|---------|
| `BootstrapResult` (model) | Point estimate and confidence intervals for a metric. |
| `PermutationTestResult` (model) | Significance from random reshuffling. |
| `WhitesRealityCheckResult` (model) | Data snooping bias correction results. |
| `whites_reality_check(strategy_returns: list[np.ndarray \| pd.Series], benchmark_returns: np.ndarray \| pd.Series, metric_func: Callable[[np.ndarray], float] \| None = None, n_bootstrap: int = 1000, block_size: int = 1, significance_level: float = 0.05, seed: int \| None = None) -> dict[str, Any]` | AI Tool wrapper for _whites_reality_check_impl. |
| `permutation_test(returns: np.ndarray \| pd.Series, metric_func: Callable[[np.ndarray], float] \| None = None, method: Literal['shuffle', 'sign_flip'] = 'sign_flip', n_permutations: int = 1000, significance_level: float = 0.05, seed: int \| None = None) -> dict[str, Any]` | AI Tool wrapper for _permutation_test_impl. |
| `bootstrap_confidence_intervals(returns: np.ndarray \| pd.Series, metrics_dict: dict[str, Callable[[np.ndarray], float]] \| None = None, n_bootstrap: int = 1000, block_size: int = 1, confidence_level: float = 0.95, periods_per_year: int = 252, seed: int \| None = None) -> dict[str, Any]` | AI Tool wrapper for _bootstrap_confidence_intervals_impl. |
| `deflated_sharpe_ratio(observed_sharpe: float, n_trials: int, n_observations: int, expected_sharpe: float = 0.0, skew: float = 0.0, kurt: float = 3.0) -> dict[str, Any]` | AI Tool wrapper for _deflated_sharpe_ratio_impl. |
| `probability_of_backtest_overfitting(in_sample_scores: np.ndarray, out_of_sample_scores: np.ndarray) -> dict[str, Any]` | AI Tool wrapper for _probability_of_backtest_overfitting_impl. |
| `walk_forward_degradation_score(train_scores: np.ndarray \| pd.Series, test_scores: np.ndarray \| pd.Series) -> dict[str, Any]` | AI Tool wrapper for _walk_forward_degradation_score_impl. |
| `bootstrap_probability_above_threshold(returns: np.ndarray \| pd.Series, metric_func: Callable[[np.ndarray], float], threshold: float, n_bootstrap: int = 1000, block_size: int = 1, seed: int \| None = None) -> dict[str, Any]` | AI Tool wrapper for _bootstrap_probability_above_threshold_impl. |
| `bonferroni_correction(p_values: np.ndarray \| list[float], alpha: float = 0.05) -> dict[str, Any]` | AI Tool wrapper for _bonferroni_correction_impl. |
| `benjamini_hochberg_correction(p_values: np.ndarray \| list[float], alpha: float = 0.05) -> dict[str, Any]` | AI Tool wrapper for _benjamini_hochberg_correction_impl. |
| `stability_score(walk_forward_results: list[dict[str, Any]], metric_key: str = 'sharpe_ratio') -> dict[str, Any]` | AI Tool wrapper for _stability_score_impl. |
| `whites_reality_check_backtests(strategy_results: list['BacktestResult'], benchmark_result: 'BacktestResult', metric_func: Callable[[np.ndarray], float] \| None = None, **kwargs) -> dict[str, Any]` | AI Tool wrapper for _whites_reality_check_backtests_impl. |
| `bootstrap_confidence_intervals_backtest(strategy_result: 'BacktestResult', **kwargs) -> dict[str, Any]` | AI Tool wrapper for _bootstrap_confidence_intervals_backtest_impl. |
| `print_statistical_validation_report(permutation_result: PermutationTestResult \| None = None, bootstrap_results: list[BootstrapResult] \| None = None, deflated_sharpe_result: tuple[float, float] \| None = None, stability_result: dict[str, float] \| None = None, whites_result: WhitesRealityCheckResult \| None = None) -> dict[str, Any]` | AI Tool wrapper for _print_statistical_validation_report_impl. |


## FEAT-ANLT-42: Seeded permutation, bootstrap, and resampling diagnostics for Analytics (app.services.analytics.statistics.resampling)

| Function | Purpose |
|----------|---------|
| `statistics_resampling_boundary() -> dict[str, object]` | Describe deterministic resampling boundary controls. |
| `permutation_test_backtest(_report1: dict[str, Any], _report2: dict[str, Any]) -> float` | Run permutation testing against backtest result objects. |
