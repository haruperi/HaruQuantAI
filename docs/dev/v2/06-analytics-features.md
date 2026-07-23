# Analytics Domain — Capability Feature Extraction (from `06-analytics.md`)

Source: `docs/dev/phase-implementation-plan/06-analytics.md`. Module paths follow the plan's target tree. The metrics modules define very large metric families; tables below list the primary capabilities and aggregate entry points, with individual metrics summarized by family. Documentation and test modules are omitted.

---

## FEAT-ANLT-01: Official Analytics Tools (app.services.analytics.tool_api)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_analytics_overview(request: BuildAnalyticsReportRequest, request_id: str) -> ToolEnvelope[AnalyticsReport]` | Comprehensive analytics across all, long, and short subsets; read-only. | Missing |
| `build_analytics_report(request: BuildAnalyticsReportRequest, request_id: str) -> ToolEnvelope[AnalyticsReport]` | Build the full analytics report envelope with metadata and side-effect flags. | Missing |
| `build_portfolio_analytics_report(request: BuildPortfolioAnalyticsReportRequest, request_id: str) -> ToolEnvelope[PortfolioAnalyticsReport]` | Portfolio-level analytics report. | Missing |
| `compare_analytics_reports(left: AnalyticsReport, right: AnalyticsReport, request_id: str) -> ToolEnvelope[AnalyticsComparison]` | Deterministic report comparison. | Missing |
| `calculate_prop_firm_compliance(report: AnalyticsReport, profile: ComplianceProfile, request_id: str) -> ToolEnvelope[ComplianceEvidence]` | Prop-firm compliance evidence only; makes no enforcement decision. | Missing |

## FEAT-ANLT-02: Versioned Contracts, Metric Catalog, and Warnings (app.services.analytics.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_schema_version(version: str, matrix: SchemaCompatibilityMatrix) -> SchemaCompatibility` | Versioned-schema compatibility for reports, dashboards, warnings, and error envelopes. | Missing |
| `METRIC_DEFINITION_CATALOG` / `get_metric_definition(...)` | Metric Definition Catalog: formula, units, inputs, aliases, annualization basis, minimum samples, undefined-result behavior, and golden fixtures per official metric. | Implemented |
| `build_warning(code: str, severity: WarningSeverity, section: str, detail: Mapping[str, object]) -> AnalyticsWarning` | Bounded warning/quality-flag construction with code, severity, and affected section. | Implemented |
| `to_json_safe(value: object, precision: PrecisionPolicy) -> JsonValue` | Canonical JSON safety and Decimal normalization (with `canonical_json` deterministic serialization). | Missing |

## FEAT-ANLT-03: Analytics Registry (app.services.analytics.registry)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `AnalyticsRegistry` (analytics_registry.py) | Bounded local registry/cache/observability state mapping official metrics and tools to definitions. | Missing |

## FEAT-ANLT-04: Input Adapters and Canonicalization (app.services.analytics.adapters)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_adapter_contract(adapter: TradingResultAdapter) -> None` | Enforce the adapter protocol contract. | Missing |
| `to_trading_result(source: BacktestResult \| PaperResult \| LiveResult \| PortfolioResult \| TradingResult) -> TradingResult` | Canonicalize any supported result source into the single `TradingResult` input model. | Missing |
| `from_simulation_journal(journal: SimulationJournal) -> TradingResult` | Adapt simulator journals (with `from_live_trade_journal` counterpart). | Missing |

## FEAT-ANLT-05: Trade-Level Metrics (app.services.analytics.metrics — trade_outcomes / r_multiples / costs / efficiency / time_analysis / position_exposure / pnl)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `compute_trade_metrics(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | Aggregate trade-outcome metric computation (win/loss counts and rates, averages, streaks, expectancy, entropy, t-statistic). | Missing |
| `compute_r_trade_metrics(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | R-multiple family: `get_r_multiples`, average/median/max/min R, R expectancy, signal-to-noise, distribution; explicit initial-risk preferred over documented proxies. | Missing |
| `calculate_spread_cost_impact(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | Cost family: spread, slippage, and commission impact. | Missing |
| `calculate_efficiency_metrics(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | Efficiency family: MFE/MAE capture, exit/entry efficiency, capital efficiency, returns per hour/day/unit-risk. | Missing |
| `calculate_period_analysis(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | Time family: period analysis, long/short split, session performance, time-in-trade and time-in-market durations. | Missing |
| `net_profit(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | PnL family: net/gross/adjusted/select profit and loss, CAGR, CMGR, total return, run-up, return-on-capital. | Missing |
| `max_gross_size_held(trades: Sequence[TradeRecord], config: MetricConfig) -> MetricResult[...]` | Position/exposure family: max long/short/net/gross size, percent time in market, open-position PnL, paid costs. | Missing |

## FEAT-ANLT-06: Equity Curves and Drawdown Metrics (app.services.analytics.metrics — curves / equity / drawdown)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `equity_curve(input_value: object, config: MetricConfig) -> MetricResult[object]` | Equity/balance curve construction (with closed-trade balance curve variants). | Missing |
| `calculate_return_metrics(equity: Sequence[EquityPoint], config: EquityMetricConfig) -> MetricResult[...]` | Return family: returns/log-returns series, daily-to-annual periods, volatility, skewness, kurtosis, Kelly criterion, best/worst return. | Missing |
| `calculate_drawdown_metrics(equity: Sequence[EquityPoint], config: EquityMetricConfig) -> MetricResult[...]` | Drawdown family: max/avg/relative/close-to-close drawdown, durations, recovery, distribution, probability. | Missing |
| `ulcer_index(equity: Sequence[EquityPoint], config: EquityMetricConfig) -> MetricResult[...]` | Pain family: ulcer index, pain index/ratio, Calmar, Sterling, Fouse, RINA, account-size-required. | Missing |

## FEAT-ANLT-07: Risk and Ratio Metrics (app.services.analytics.metrics — risk / ratios / aggregate)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_risk_metrics(returns: Sequence[ReturnPoint], config: ReturnMetricConfig) -> MetricResult[...]` | Risk family: volatility, VaR/CVaR/expected shortfall, risk of ruin (fixed/compounding/custom horizon), exposure and margin-utilization metrics. | Missing |
| `calculate_ratio_metrics(returns: Sequence[ReturnPoint], config: ReturnMetricConfig) -> MetricResult[...]` | Ratio family: Sharpe (plain/annualized/deflated), Sortino, omega, gain-to-pain, kappa, profit factor variants, payoff, edge, MFE/MAE ratios, up/down capture. | Missing |
| `calculate_analytics_for_subset(input_value: object, config: MetricConfig) -> MetricResult[object]` | Subset analytics used by all/long/short overview computation (with `calculate_trade_metrics`, `compute_equity_metrics`, and breakeven-epsilon defaults). | Missing |

## FEAT-ANLT-08: Statistical Validation (app.services.analytics.statistics)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `whites_reality_check(values: Sequence[Decimal \| float], config: StatisticalConfig) -> MetricResult[...]` | Multiple-testing family: White's reality check, PBO, walk-forward degradation, Bonferroni, Benjamini–Hochberg, stability score. | Missing |
| `calculate_distribution_metrics(values: Sequence[Decimal \| float], config: StatisticalConfig) -> MetricResult[...]` | Distribution family: return/R distributions, percentiles, moments, fat-tail score, normality tests (Jarque–Bera, Shapiro–Wilk), QQ data, outlier detection. | Missing |
| `bootstrap_confidence_intervals(values: Sequence[Decimal \| float], config: StatisticalConfig) -> MetricResult[...]` | Resampling family: bootstrap CIs, threshold probabilities, permutation tests (including backtest variants). | Missing |

## FEAT-ANLT-09: Benchmark Comparison Metrics (app.services.analytics.benchmarks)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_benchmark_metrics(strategy_returns: Sequence[ReturnPoint], benchmark_returns: Sequence[ReturnPoint], config: BenchmarkConfig) -> MetricResult[...]` | Aggregate benchmark comparison entry point. | Missing |
| `beta(...)` / `alpha(...)` / `r_squared(...)` / `tracking_error(...)` / `information_ratio(...)` / `batting_average(...)` | Individual benchmark-relative metrics over aligned return series. | Missing |

## FEAT-ANLT-10: Strategy Quality Scorecards (app.services.analytics.scorecards)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `evaluate_strategy_quality(report: AnalyticsReport, config: StrategyQualityConfig) -> StrategyQualityAssessment` | Non-binding strategy quality assessment; never a final approval/promotion/live decision. | Missing |
| `sqn(report: AnalyticsReport, config: StrategyQualityConfig) -> StrategyQualityAssessment` | System Quality Number scoring (with sample-size warnings). | Missing |

## FEAT-ANLT-11: Report Assembly, Hashing, and Formatting (app.services.analytics.reports)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `compute_report_hash(report: AnalyticsReportDraft, policy: HashPolicy) -> str` | Deterministic report hashing for reproducibility. | Missing |
| `serialize_report(report: AnalyticsReport, format: ReportFormat) -> SerializedReport` | Report serialization (with summary-row and backtest-report formatters and statistical-validation report output). | Implemented |

## FEAT-ANLT-12: Dashboard Payloads (app.services.analytics.dashboards)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_overview_payload(report: AnalyticsReport, config: DashboardConfig) -> DashboardPayload` | Build bounded dashboard overview payloads from a report. | Missing |
| `truncate_series(points: Sequence[ChartPoint], policy: TruncationPolicy) -> TruncatedSeries` | Deterministic chart-series truncation under dashboard limits. | Implemented |

## FEAT-ANLT-13: Request Validation, Envelopes, Limits, and Redaction (app.services.analytics.boundaries)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_request(request: object, request_id: str, limits: AnalyticsLimits) -> None` | Boundary request validation against analytics limits. | Missing |
| `success_envelope(data: JsonValue, metadata: AnalyticsMetadata) -> ToolEnvelope[JsonValue]` | Standard success envelope (with `error_envelope` counterpart). | Missing |
| `enforce_limits(shape: WorkloadShape, limits: AnalyticsLimits) -> None` | Enforce workload shape/size limits. | Missing |
| `redact(value: object, policy: RedactionPolicy) -> object` | Redact sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, and diagnostics. | Missing |

---

**Note:** all analytics functions are read-only (no database, network, broker, or filesystem side effects); undefined metric values are omitted or `None` with structured warnings — never `NaN`, infinity, or fabricated zeros. Low-level helpers (skewness, tail-ratio, date helpers, etc.) remain internal unless promoted by the Official Analytics Tool Catalog.
