# Functions Register

This document registers all public and planned exported functions across the HaruQuantAI domain packages.

# Utils

## FEAT-UTIL-00: Shared Authentication and Audit Contracts (utils.contracts)

***

| Public export | Purpose | Status |
| :--- | :--- | :--- |
| `AuthContext` | Immutable authenticated principal and UUID4 trace context contract. | Completed |
| `AuditEvent` | Immutable bounded redacted audit-event envelope. | Completed |

## FEAT-UTIL-01: Error Mapping and Exception Normalization (utils.errors)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `map_exception(exception: BaseException) -> dict[str, str]` | Convert caught exceptions to deterministic secret-safe shared error evidence. | Completed |
| `normalize_error_code(code: str) -> str` | Normalize an error code to a consistent format. | Completed |
| `get_error_metadata(code: str) -> ErrorMetadata` | Look up immutable safe error metadata without a mutable registry. | Completed |
| `route_error_event(exception: BaseException, sink: ErrorSink) -> dict[str, str]` | Synchronously deliver and return a safe error payload through an explicitly injected sink. | Completed |

## FEAT-UTIL-02: Prefixed and Deterministic SHA-256 Identity Generation (utils.identity)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `generate_id(prefix: str) -> str` | Generate prefixed UUID4 trace identifiers without embedded secrets. | Completed |
| `validate_id(value: str, *, expected_prefix: str \| None = None) -> str` | Validate UUID4 trace or deterministic non-trace identifier syntax. | Completed |
| `derive_stable_id(prefix: str, identity_material: str) -> str` | Derive a deterministic `id`-prefixed SHA-256 identity from canonical caller material. | Completed |

## FEAT-UTIL-03: Aware UTC Time and Timestamp Utilities (utils.time)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `utc_now(clock: Clock \| None = None) -> datetime` | Return aware UTC time from an injectable clock. | Completed |
| `parse_utc_timestamp(value: str) -> datetime` | Parse UTC timestamps using canonical output. | Completed |
| `format_utc_timestamp(value: datetime) -> str` | Format UTC timestamps using canonical Z output. | Completed |
| `age_seconds(value: datetime, *, reference: datetime) -> Decimal` | Calculate exact non-negative age against an explicit instant. | Completed |
| `is_fresh(value: datetime, *, reference: datetime, max_age_seconds: Decimal) -> bool` | Evaluate freshness against an explicit instant. | Completed |

## FEAT-UTIL-04: Canonical JSON Serialization and Value Safe Conversion (utils.serialization)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `to_json_safe(value: object) -> JsonValue` | Convert supported datetimes, decimals, enums, dataclasses, mappings, and sequences to deterministic JSON-safe values. | Completed |
| `canonical_json(value: object) -> str` | Produce stable UTF-8 JSON with sorted keys and no hidden redaction. | Completed |

## FEAT-UTIL-05: Sensitive Data Redaction (utils.security)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `is_sensitive_key(key: str, policy: RedactionPolicy \| None = None) -> bool` | Detect sensitive keys case-insensitively. | Completed |
| `redact_text_value(value: str, policy: RedactionPolicy \| None = None) -> RedactionResult` | Redact bounded message patterns without mutating input. | Completed |
| `redact_mapping_value(value: Mapping[str, object], policy: RedactionPolicy \| None = None) -> RedactionResult` | Recursively redact a JSON-safe mapping without mutating input. | Completed |

## FEAT-UTIL-06: Precedence-Ordered Settings Loading (utils.settings)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `load_settings(explicit_values: Mapping[str, object] \| None = None, environment: Mapping[str, str] \| None = None) -> RuntimeSettings` | Load explicit values and centralized settings in precedence order. | Completed |

## FEAT-UTIL-07: Non-Blocking Console and File Log Handler Configuration (utils.logging)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_logger(name: str) -> logging.Logger` | Return stable child loggers without configuring handlers. | Completed |
| `configure_logging(settings: LoggingSettings \| None = None, redaction_policy: RedactionPolicy \| None = None) -> None` | Atomically install console and file handlers from the approved default or explicit specialized profile. | Completed |
| `flush_logging() -> None` | Flush buffered log records to their sinks. | Completed |
| `shutdown_logging() -> None` | Stop queue thread listeners and release logging resources. | Completed |

# Brokers

## FEAT-BRK-01: Broker Provider Adapter Registry and Capability Discovery (services.brokers.registry)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_broker_adapter(broker_id: str, config: BrokerConnectionConfig) -> BrokerAdapter` | Factory function to instantiate provider adapters. | Completed |
| `get_broker_capability_catalogue(broker_id: str) -> BrokerCapability` | Retrieve capability matrix details for a provider. | Completed |
| `get_registered_brokers() -> tuple[str, ...]` | Expose all registered/supported brokers. | Completed |

## FEAT-BRK-02: MetaTrader 5 Broker Connection and Disconnection (services.brokers.mt5)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `MT5BrokerAdapter.connect() -> None` | Establish MT5 provider connection. | Completed |
| `MT5BrokerAdapter.disconnect() -> None` | Disconnect MT5 provider connection. | Completed |

## FEAT-BRK-03: cTrader Broker Connection and Disconnection (services.brokers.ctrader)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `CTraderBrokerAdapter.connect() -> None` | Establish cTrader provider connection. | Completed |
| `CTraderBrokerAdapter.disconnect() -> None` | Disconnect cTrader provider connection. | Completed |

## FEAT-BRK-04: Binance Broker Connection and Disconnection (services.brokers.binance)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `BinanceBrokerAdapter.connect() -> None` | Establish Binance provider connection. | Completed |
| `BinanceBrokerAdapter.disconnect() -> None` | Disconnect Binance provider connection. | Completed |

## FEAT-BRK-05: Dukascopy Broker Connection and Disconnection (services.brokers.dukascopy)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `DukascopyBrokerAdapter.connect() -> None` | Establish Dukascopy provider connection. | Completed |
| `DukascopyBrokerAdapter.disconnect() -> None` | Disconnect Dukascopy provider connection. | Completed |

## FEAT-BRK-06: Yahoo Finance Broker Connection and Disconnection (services.brokers.yahoo)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `YahooBrokerAdapter.connect() -> None` | Establish Yahoo provider connection. | Completed |
| `YahooBrokerAdapter.disconnect() -> None` | Disconnect Yahoo provider connection. | Completed |

# Data

## FEAT-DATA-01: Historical and Real-Time Market Data and Update Jobs Management (services.data.public_api)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `aggregate_ticks_to_bars(ticks: Sequence[TickRecord], timeframe: str) -> Sequence[BarRecord]` | Aggregate a list of tick records to bars. | Completed |
| `align_multitimeframe_data(data: Mapping[str, Sequence[BarRecord]], primary_timeframe: str) -> Mapping[str, Sequence[BarRecord]]` | Align multitimeframe bars to a primary timeframe index. | Completed |
| `clear_data_cache() -> None` | Clear cached historical datasets. | Completed |
| `create_data_update_job(job_config: JobConfig) -> str` | Create a new historical data update job. | Completed |
| `generate_synthetic_bars(spec: SyntheticBarSpec) -> Sequence[BarRecord]` | Generate synthetic bar data for testing. | Completed |
| `generate_synthetic_ticks(spec: SyntheticTickSpec) -> Sequence[TickRecord]` | Generate synthetic tick data for testing. | Completed |
| `generate_tick_series(dataset: MarketDataset, **generation_arguments: object) -> MarketDataset` | Derive a canonical tick dataset from real bar or real tick evidence. | Completed |
| `generate_tick_series_to_parquet(dataset: MarketDataset, **generation_arguments: object) -> Mapping[str, object]` | Stream a generated tick series to a bounded Parquet artifact. | Completed |
| `get_data_availability(source_id: str, symbol: str) -> DataAvailability` | Get stored range and record count evidence. | Completed |
| `get_data_update_job_status(job_id: str) -> JobStatus` | Get historical update job execution status. | Completed |
| `get_feed_status(feed_id: str) -> FeedStatus` | Check real-time subscription feed connection status. | Completed |
| `get_historical_volume(source_id: str, symbol: str) -> VolumeResult` | Retrieve historical execution volume summary. | Completed |
| `get_market_data(source_id: str, symbol: str, timeframe: str) -> MarketDataResult` | Retrieve historical bar datasets. | Completed |
| `get_market_hours(source_id: str, symbol: str) -> MarketHours` | Retrieve market hours and sessions for a symbol. | Completed |
| `get_spread_data(source_id: str, symbol: str) -> SpreadResult` | Retrieve historical spread statistics. | Completed |
| `get_symbol_metadata(source_id: str, symbol: str) -> SymbolMetadata` | Retrieve static contract and pricing rules. | Completed |
| `get_tick_data(source_id: str, symbol: str) -> TickResult` | Retrieve historical tick datasets. | Completed |
| `get_trading_sessions(source_id: str, symbol: str) -> TradingSessions` | Retrieve trading sessions for a symbol. | Completed |
| `list_symbols(source_id: str, query: str) -> SymbolList` | Search and list symbols matching query. | Completed |
| `load_local_dataset(path: str) -> MarketDataset` | Load local parquet/CSV files. | Completed |
| `resample_ohlcv(bars: Sequence[BarRecord], target_timeframe: str) -> Sequence[BarRecord]` | Resample OHLCV bars to target timeframe. | Completed |
| `run_data_update_job_once(job_id: str) -> None` | Trigger single update/backfill job execution. | Completed |
| `save_market_data(dataset: MarketDataset) -> None` | Persist new market data snapshot. | Completed |
| `start_data_update_job(job_id: str) -> None` | Start background scheduler/worker update daemon. | Completed |
| `stop_data_update_job(job_id: str) -> None` | Stop background scheduler/worker update daemon. | Completed |
| `to_ohlcv_dataframe(dataset: MarketDataset) -> DataFrame` | Return a six-column float64 analytical copy of one OHLCV dataset. | Completed |
| `to_tick_dataframe(dataset: MarketDataset) -> DataFrame` | Return a four-column float64 analytical copy of one tick dataset. | Completed |
| `inspect_data_quality(dataset: MarketDataset, policy: QualityPolicy \| None = None) -> DataQualityReport` | Detect series-level gaps, spikes, flat-lines, zero-volume runs, duplicate bars, and spread breaches, and produce scored bounded quality evidence. | Missing |
| `get_quality_policy() -> QualityPolicy` | Expose the active immutable quality thresholds and strictness profile resolved from settings. | Missing |
| `summarize_quality_remediation(report: DataQualityReport) -> Mapping[str, str]` | Map each detected issue code to its deterministic recommended remediation action. | Missing |

# Indicators

## FEAT-INDI-01: Candlestick Pattern Detection (services.indicators.candles)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `doji(candles: Sequence[BarRecord]) -> Sequence[bool]` | Detect Doji candles. | Completed |
| `engulfing(candles: Sequence[BarRecord]) -> Sequence[bool]` | Detect Engulfing candles. | Completed |
| `inside_bar(candles: Sequence[BarRecord]) -> Sequence[bool]` | Detect Inside Bar candles. | Completed |
| `pinbar(candles: Sequence[BarRecord]) -> Sequence[bool]` | Detect Pinbar candles. | Completed |

## FEAT-INDI-02: Indicator Core Capability Matrix and Validation (services.indicators.core)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_capability_matrix() -> Mapping[str, Any]` | Expose indicator capability matrix. | Completed |
| `get_indicator(name: str) -> IndicatorProtocol` | Factory function for indicators. | Completed |
| `list_indicators() -> tuple[str, ...]` | Expose all registered indicators. | Completed |
| `validate_indicator(name: str) -> None` | Validate indicator parameters. | Completed |

## FEAT-INDI-03: Momentum and Relative Strength Indicators (services.indicators.momentum)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `rsi(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Relative Strength Index. | Completed |
| `williams_r(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Williams %R. | Completed |

## FEAT-INDI-04: Trend Analysis and Moving Averages (services.indicators.trend)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `adx(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Average Directional Index. | Completed |
| `bollinger_bands(prices: Sequence[Decimal], period: int, standard_deviations: int) -> BollingerBandsResult` | Compute Bollinger Bands. | Completed |
| `ema(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Exponential Moving Average. | Completed |
| `hull_ma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Hull Moving Average. | Completed |
| `sma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Simple Moving Average. | Completed |
| `wma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Weighted Moving Average. | Completed |

## FEAT-INDI-05: Historical and Rolling Volatility Computation (services.indicators.volatility)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `adr(highs: Sequence[Decimal], lows: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Average Daily Range. | Completed |
| `atr(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Average True Range. | Completed |
| `rolling_volatility(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute rolling volatility. | Completed |
| `standard_deviation(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute rolling standard deviation. | Completed |

## FEAT-INDI-06: Volume Flow and Price-Volume Distribution (services.indicators.volume)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `cmf(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], volumes: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Chaikin Money Flow. | Completed |
| `mfi(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], volumes: Sequence[Decimal], period: int) -> Sequence[Decimal]` | Compute Money Flow Index. | Completed |
| `obv(prices: Sequence[Decimal], volumes: Sequence[Decimal]) -> Sequence[Decimal]` | Compute On-Balance Volume. | Completed |
| `price_volume_distribution(prices: Sequence[Decimal], volumes: Sequence[Decimal], bin_count: int) -> PriceVolumeDistributionResult` | Compute price-volume distribution bins. | Completed |

# Strategy

## FEAT-STR-01: Trade Intent Construction and Lineage Tracking (services.strategy.intents)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_trade_intent(decision: StrategyDecision, context: StrategyExecutionContext, sequence: int) -> StrategyOutcome[TradeIntent]` | Build a schema-valid intent with deterministic IDs, sequence, and parent/lineage references. | Completed |

## FEAT-STR-02: Strategy State Checkpoints and Replay Manifests (services.strategy.replay)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_strategy_checkpoint(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, state: Mapping[str, JsonValue], authorization_ref: str) -> StrategyOutcome[StrategyCheckpoint]` | Serialize and checksum candidate local decision state. | Completed |
| `validate_strategy_checkpoint(checkpoint: StrategyCheckpoint, ref: ValidatedStrategyRef, config: ValidatedStrategyConfig) -> StrategyOutcome[Mapping[str, JsonValue]]` | Reject corrupt, incompatible, or oversized checkpoints before execution. | Completed |
| `create_strategy_replay_manifest(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, context: StrategyExecutionContext, data_checksum: str, indicator_manifest_hash: str, simulation_config_hash: str) -> StrategyOutcome[StrategyReplayManifest]` | Create deterministic replay manifest from inputs. | Completed |

## FEAT-STR-03: Strategy Diagnostics and Fact Exporting (services.strategy.diagnostics)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `export_strategy_diagnostics(context: StrategyExecutionContext, facts: Mapping[str, JsonValue]) -> StrategyOutcome[StrategyDiagnostics]` | Export schema-valid diagnostics after size enforcement. | Completed |

## FEAT-STR-04: Strategy Registration, Parameter Configuration and Lifecycle Checks (services.strategy.registry)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `list_strategy_versions(strategy_id: str \| None = None) -> StrategyOutcome[tuple[ValidatedStrategyRef, ...]]` | Return registered entries in deterministic order. | Completed |
| `register_strategy_version(request: StrategyRegistrationRequest, auth: AuthContext) -> StrategyOutcome[ValidatedStrategyRef]` | Register unique version after module, hash, and lifecycle checks. | Completed |
| `update_strategy_parameters(request: StrategyParameterUpdateRequest, auth: AuthContext) -> StrategyOutcome[ValidatedStrategyConfig]` | Validate and record parameter updates. | Completed |
| `validate_strategy_config(ref: ValidatedStrategyRef, config: StrategyConfig) -> StrategyOutcome[ValidatedStrategyConfig]` | Validate declarative config and resource limits. | Completed |
| `validate_strategy_ref(ref: StrategyRef) -> StrategyOutcome[ValidatedStrategyRef]` | Resolve exactly one approved reference. | Completed |

## FEAT-STR-05: Synchronous Vectorized Strategy Execution (services.strategy.vectorized)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_vectorized_strategy_signals(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, market: MarketDataset, indicators: tuple[IndicatorSeries, ...], context: StrategyExecutionContext) -> StrategyOutcome[StrategyExecutionResult]` | Run synchronous vectorized logic without lookahead. | Completed |

## FEAT-STR-06: Stateful Strategy Hook Execution (services.strategy.event)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_event_strategy_hook(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, event: StrategyEvent, context: StrategyExecutionContext, local_state: Mapping[str, JsonValue] \| None = None) -> StrategyOutcome[StrategyExecutionResult]` | Invoke stateful hook in priority order. | Completed |

## FEAT-STR-07: Strategy Signals Evaluation Orchestration (services.strategy.evaluators)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `evaluate_strategy_signals(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, evidence: StrategySignalEvidence, indicators: tuple[IndicatorResult, ...], context: StrategyExecutionContext, evaluator: _SignalEvaluator) -> StrategyOutcome[tuple[StrategySignal, ...]]` | Atomically execute one registry-bound concrete signal evaluator. | Completed |

# Risk

## FEAT-RISK-01: Portfolio Risk Snapshot Normalization (services.risk.portfolio)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_portfolio_risk_snapshot(portfolio: PortfolioState, settings: RiskSettings) -> PortfolioRiskSnapshot` | Assemble and normalize a point-in-time risk snapshot from active state. | Completed |

## FEAT-RISK-02: Allocation Limits and Compliance Constraint Evaluation (services.risk.policy)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `evaluate_portfolio_limits(proposal: ProposedTrade, snapshot: PortfolioRiskSnapshot, settings: RiskSettings) -> RiskLimitResult` | Assess portfolio limits, allocation caps, and stop conditions. | Completed |
| `review_allocation_proposal(request: AllocationReviewRequest, settings: RiskSettings) -> AllocationRiskDecision` | Evaluate compliance limits and policy verdicts for target allocation proposals. | Completed |
| `review_strategy_admission(request: StrategyOperationalEligibilityRequest, settings: RiskSettings) -> StrategyOperationalEligibilityDecision` | Review registered strategies for operational profile and route compatibility. | Completed |
| `activate_allocation_budget(request: AllocationBudgetActivationRequest, settings: RiskSettings) -> PortfolioBudgetExecutionVerdict` | Authorize and activate target portfolio allocations under compliance limits. | Completed |

## FEAT-RISK-03: Volatility Regimes and Market Context Assessment (services.risk.regimes)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `assess_risk_regime(evidence: MarketContextEvidence, settings: RiskSettings) -> RegimeAssessment` | Determine volatility regimes and active market context bands. | Completed |
| `evaluate_market_context(evidence: MarketContextEvidence, settings: RiskSettings) -> None` | Reconcile and assert validity of market-context evidence before run requests. | Completed |
| `validate_market_context_evidence(evidence: MarketContextEvidence) -> None` | Ensure the structure and freshness of context metadata are compliant. | Completed |

## FEAT-RISK-04: Position Sizing and Risk-Adjusted Limits Validation (services.risk.sizing)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_position_size(request: PositionSizingRequest, settings: RiskSettings) -> PositionSizingResult` | Compute risk-adjusted sizing and leverage bounds for proposed trades. | Completed |

## FEAT-RISK-05: Ephemeral Principal Approvals and Token Revocation (services.risk.approvals)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `ApprovalTokenService.issue(decision: RiskDecisionPackage, attestation: ApprovalAttestation, *, now: datetime) -> RiskApprovalToken` | Issue and durably record one eligible signed scoped token. | Completed |
| `ApprovalTokenService.validate_reserve_and_consume(token: RiskApprovalToken, attestation: ApprovalAttestation, expected: Mapping[str, str], *, now: datetime) -> ApprovalValidationResult` | Validate, atomically reserve, consume, and authorize one action. | Completed |
| `ApprovalTokenService.revoke_scope(scope: Mapping[str, str], reason: str, *, now: datetime) -> int` | Revoke every outstanding token intersecting an authorized scope. | Completed |

## FEAT-RISK-06: Strategy Run Request Governance (services.risk.decisions)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `RiskGovernor.submit_run_request(request: RunRequest) -> RunDecision` | Evaluate and authorize strategy runs. | Completed |
| `apply_kill_switch_command(command: KillSwitchCommand, state: KillSwitchState, occurred_at: datetime) -> KillSwitchState` | Mutate and persist kill switch state under active validation gates. | Completed |
| `check_risk_kill_switch(scope: Mapping[str, str], state: KillSwitchState) -> None` | Validate and enforce kill-switch restrictions for a target scope. | Completed |
| `revalidate_risk_decision(decision: RiskDecisionPackage, settings: RiskSettings, now: datetime) -> None` | Assert ongoing validity of a previously approved risk decision. | Completed |

# Trading

## FEAT-TRD-01: Database, Feeds, and Adapter Readiness Validation (services.trading.validation)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `assess_execution_readiness(dependencies: TradingDependencies) -> ReadinessAssessment` | Verify database, feeds, and adapters are active and ready. | Completed |
| `validate_order_request(request: TradingRequest) -> None` | Ensure incoming order requests satisfy strategy and validation rules. | Completed |
| `build_execution_plan(request: TradingRequest, snapshot: RouteSnapshot) -> None` | Build order target allocations and rebalance boundaries. | Completed |
| `get_route_snapshot(dependencies: TradingDependencies) -> RouteSnapshot` | Capture snapshot of current target route environment features. | Completed |

## FEAT-TRD-02: Order Routing to Provider Adapters (services.trading.routing)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `dispatch_order_intent(intent: OrderIntent, adapter: BrokerAdapter) -> ExecutionReceipt` | Direct validated orders to MT5, cTrader, or other connection adapters. | Completed |
| `classify_authority_response(response: BrokerResult) -> None` | Classify responses from the connection adapter into canonical outcomes. | Completed |
| `validate_adapter_capability(adapter: BrokerAdapter, capability: str) -> None` | Ensure the adapter supports target features (e.g. live mutations). | Completed |

## FEAT-TRD-03: Order State Reconciliation and Gateway Recovery (services.trading.reconciliation)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `compare_authority_state(expected: OrderIntent, actual: BrokerOrder) -> ReconciliationReport` | Match gateway intents with broker confirmations. | Completed |
| `resolve_unknown_outcome(order_id: str, dependencies: TradingDependencies) -> ExecutionReceipt` | Re-evaluate unknown broker states using idempotency keys. | Completed |

## FEAT-TRD-04: Net Exposure and Risk Budget Utilization Tracking (services.trading.monitoring)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `BudgetGate.check_exposure(exposure: PortfolioExposure) -> None` | Reconcile active risk utilization against allocated budget limits. | Completed |
| `emit_runtime_event(event: OperationalEvent) -> None` | Emit redacted execution health, latency, or incident signals. | Completed |

## FEAT-TRD-05: Real-Time Session Loops and Adapters Management (services.trading.live)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `LiveSession.start() -> None` | Initialize connection adapters and start trading execution loop. | Completed |
| `LiveSession.stop() -> None` | Disconnect feeds and halt session loops. | Completed |
| `evaluate_live_gate(settings: TradingSettings) -> None` | Ensure live trading flags and credentials meet constraints. | Completed |

## FEAT-TRD-06: Position and Active Order Operations (services.trading.actions)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `submit_order(intent: OrderIntent) -> ExecutionReceipt` | Submit order request. | Completed |
| `cancel_order(order_id: str) -> ExecutionReceipt` | Cancel active working order. | Completed |
| `close_position(position_id: str) -> ExecutionReceipt` | Close position. | Completed |
| `close_all_positions() -> tuple[ExecutionReceipt, ...]` | Close all positions. | Completed |
| `cancel_all_orders() -> tuple[ExecutionReceipt, ...]` | Cancel all active orders. | Completed |
| `clear_kill_switch() -> None` | Clear active kill switch state. | Completed |
| `execute_portfolio_rebalance(plan: PortfolioRebalancePlan) -> tuple[ExecutionReceipt, ...]` | Rebalance positions to target weights. | Completed |
| `modify_order(order_id: str, modifications: dict) -> ExecutionReceipt` | Modify parameters of an active order. | Completed |
| `modify_position(position_id: str, modifications: dict) -> ExecutionReceipt` | Modify parameters of a position. | Completed |
| `pause_strategy(strategy_id: str) -> None` | Pause strategy execution. | Completed |
| `reduce_exposure(scope: dict) -> None` | Reduce portfolio exposure. | Completed |
| `resume_strategy(strategy_id: str) -> None` | Resume strategy execution. | Completed |
| `run_live_evaluation_cycle(dependencies: TradingDependencies) -> None` | Run a single live evaluation cycle. | Completed |
| `sync_positions(dependencies: TradingDependencies) -> None` | Synchronize local states with broker truth. | Completed |
| `trigger_kill_switch(command: KillSwitchCommand) -> None` | Trigger kill switch state. | Completed |

## FEAT-TRD-07: Execution Evidence and Reports Assembly (services.trading.reporting)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `build_trading_report(receipt: ExecutionReceipt) -> ExecutionEvidence` | Assemble execution reports and reconciled evidence. | Completed |

# Analytics

## FEAT-ANLT-01: Sharpe, Sortino, CAGR, and Drawdown Calculation (services.analytics.reports.builder)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_performance_report(config: AnalyticsRunConfig, trades: Sequence[TradeRecord], equity_basis: str) -> PerformanceReport` | Core performance report builder. Computes Sharpe, Sortino, CAGR, drawdowns. | Completed |
| `calculate_performance_metrics(trades: Sequence[TradeRecord], equity_curve: Sequence[Decimal]) -> PerformanceMetrics` | Calculate Sharpe, Sortino, CAGR, and drawdowns. | Missing |

## FEAT-ANLT-02: Strategy-Level Performance Attribution Allocation (services.analytics.reports.allocation)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_portfolio_allocation_evidence(trades: Sequence[TradeRecord], curve: Sequence[Decimal]) -> PortfolioAllocationEvidence` | Core portfolio allocation evidence calculation. | Completed |
| `calculate_portfolio_attribution(portfolio: ActivePortfolioAllocation, components: Mapping[str, PerformanceMetrics]) -> PortfolioAttribution` | Allocate performance and risk metrics to component strategies. | Missing |

## FEAT-ANLT-03: Alpha, Beta, and Tracking Error Benchmarking (services.analytics.reports.builder)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `compare_to_benchmark(portfolio: ActivePortfolioAllocation, benchmark: Sequence[Decimal]) -> BenchmarkComparison` | Reconcile alpha, beta, and tracking error. | Missing |

## FEAT-ANLT-04: Peak-to-Trough Drawdown and Win/Loss Streak Calculation (services.analytics.reports.builder)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_drawdown_profile(equity_curve: Sequence[Decimal]) -> DrawdownProfile` | Compute peak-to-trough drops. | Missing |
| `calculate_streak_statistics(trades: Sequence[TradeRecord]) -> StreakStatistics` | Quantify consecutive win/loss patterns. | Missing |

## FEAT-ANLT-05: Chart-Ready Dashboard Report Compilation (services.analytics.dashboards)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_dashboard_payload(report: PerformanceReport, config: AnalyticsRunConfig) -> DashboardPayload` | Compile chart-ready dashboard payload datasets. | Completed |
| `truncate_series(series: Sequence[object], limit: int) -> tuple[object, ...]` | Truncate series datasets to bounded limits. | Completed |
| `build_dashboard_report(performance: PerformanceReport, attribution: PortfolioAllocationEvidence) -> dict[str, object]` | Compile chart-ready dashboard report. | Missing |

## FEAT-ANLT-06: Portfolio Rebalance Measurement (services.analytics.reports.allocation)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_portfolio_rebalance_measurement(request: PortfolioRebalanceMeasurementRequest, config: AnalyticsRunConfig) -> PortfolioRebalanceMeasurementEvidence` | Compute rebalance plan drift and performance verification metrics. | Completed |

# Simulator

## FEAT-SIM-01: Canonical Tick Backtesting and Fast Research Approximations (services.simulator.run)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `run_backtest(request: SimulationBacktestRequestV1, dependencies: SimulationRunDependencies) -> SimulationResult` | Run a deterministic, canonical backtest. | Completed |
| `run_fast_research(request: SimulationBacktestRequestV1, dependencies: SimulationRunDependencies) -> FastResearchResult` | Run an isolated, non-canonical bar-based backtest approximation. | Completed |
| `run_portfolio_backtest(request: PortfolioBacktestRequestV1, dependencies: SimulationRunDependencies) -> PortfolioSimulationResult` | Run a deterministic backtest over a portfolio construction setup. | Completed |

## FEAT-SIM-02: OHLCV Quality Validation and Request Scope Enforcement (services.simulator.validation)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_run_inputs(request: SimulationBacktestRequestV1) -> None` | Validate request schema bounds. | Completed |
| `validate_market_data(data: MarketDataset) -> None` | Validate OHLC and spread data quality. | Completed |
| `validate_phase_one_scope(request: SimulationBacktestRequestV1) -> None` | Ensure requests fit Phase 1 constraints. | Completed |

## FEAT-SIM-03: Multi-Timeframe Timeline Construction and Lookahead Prevention (services.simulator.timeline)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_tick_timeline(bars: Sequence[BarRecord]) -> tuple[TickRecord, ...]` | Combine bars or ticks into ordered timeline. | Completed |
| `validate_intent_timing(intent: OrderIntent, tick_time: datetime) -> None` | Prevent lookahead bias. | Completed |

## FEAT-SIM-04: Margin Utilization and Execution Fee Calculation (services.simulator.accounting)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `normalize_volume(volume: Decimal, symbol: str) -> Decimal` | Quantize volume to contract rules. | Completed |
| `calculate_execution_costs(fill: BrokerDeal) -> Decimal` | Calculate execution fees. | Completed |
| `calculate_margin(position: BrokerPosition) -> Decimal` | Calculate margin capacity. | Completed |
| `validate_fx_evidence(rates: FXConversionEvidence) -> None` | Reconcile currency rates. | Completed |

## FEAT-SIM-05: State Reconstruction and Idempotent Run Resolution (services.simulator.journal)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `replay_journal(events_stream: Iterator[str]) -> tuple[SimulationEvent, ...]` | Reconstruct state from event logs. | Completed |
| `resolve_idempotent_run(request_hash: str) -> SimulationResult \| None` | Match hashes to avoid duplicate runs. | Completed |

## FEAT-SIM-06: Order Execution Pricing and Tick-Level Matching (services.simulator.execution)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `SimTrader.price_order(order: OrderIntent, tick: TickRecord) -> Decimal` | Compute execution price. | Completed |
| `SimTrader.match_order(order: OrderIntent, tick: TickRecord) -> BrokerDeal \| None` | Match orders on tick events. | Completed |

## FEAT-SIM-07: Checksummed Artifact Manifests and Run Output Formatting (services.simulator.reporting)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_artifact_manifest(directory: Path) -> dict[str, object]` | Scan and checksum run outputs. | Completed |
| `build_json_report(result: SimulationResult) -> str` | Format run outputs as JSON. | Completed |
| `build_markdown_report(result: SimulationResult) -> str` | Render human-readable summaries. | Completed |

# Optimization

## FEAT-OPT-01: Parameter Sweep and Robustness Validation (services.optimization.public_api)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_parameter_sweep(request: SearchRequest) -> OptimizationResult` | Run parameter sweeps. | Completed |
| `run_walk_forward_optimization(request: WalkForwardRequest) -> OptimizationResult` | Execute walk-forward validation. | Completed |
| `run_walk_forward_matrix(requests: Sequence[WalkForwardRequest]) -> tuple[OptimizationResult, ...]` | Run multiple walk-forward matrices. | Completed |
| `run_robustness_analysis(request: RobustnessRequest) -> RobustnessResult` | Run Monte Carlo/stress tests. | Completed |
| `compare_optimization_runs(results: Sequence[OptimizationResult]) -> ComparisonResult` | Compare run metrics. | Completed |
| `calculate_parameter_stability(candidates: Sequence[Mapping[str, object]]) -> StabilityResult` | Evaluate parameter stability metrics. | Completed |
| `detect_overfit_parameters(is_evidence: Mapping[str, object], oos_evidence: Mapping[str, object]) -> OverfitResult` | Detect overfitting in training/OOS. | Completed |
| `rank_parameter_sets(candidates: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]` | Sort candidates. | Completed |
| `calculate_robustness_score(checks: Sequence[Mapping[str, object]]) -> float` | Compute robustness score. | Completed |
| `build_optimization_handoff(request: EvidenceAssemblyRequest) -> OptimizationResult` | Pack result envelope. | Completed |

## FEAT-OPT-02: Parameter Space Definitions Verification and Provenance Hashing (services.optimization.parameters)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_parameter_space(space: Mapping[str, object]) -> None` | Verify space definitions. | Completed |
| `compute_space_provenance(space: Mapping[str, object]) -> str` | Hash space settings. | Completed |

## FEAT-OPT-03: Candidate Performance Objective Scoring and Deflated Sharpe Ratio (services.optimization.scoring)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_candidate_score(metrics: PerformanceReport, objective: str) -> float` | Compute candidate score. | Completed |
| `rank_candidates(candidates: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]` | Rank candidates. | Completed |
| `calculate_deflated_sharpe(sharpe: float, trials: int, variance: float) -> float` | Compute Deflated Sharpe Ratio. | Completed |
| `count_nominal_trials(space: Mapping[str, object]) -> int` | Compute nominal trials count. | Completed |
| `assess_overfit_evidence(is_metrics: PerformanceReport, oos_metrics: PerformanceReport) -> dict[str, object]` | Compare IS/OOS metrics. | Completed |

## FEAT-OPT-04: Candidate Simulation Run Execution (services.optimization.execution)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `execute_candidate(candidate: Mapping[str, object]) -> SimulationResult` | Run candidates via Simulation. | Completed |

## FEAT-OPT-05: Grid, Bounded, and Random Candidate Generation (services.optimization.search)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `iter_grid_candidates(space: Mapping[str, object]) -> Iterator[Mapping[str, object]]` | Generate grid options. | Completed |
| `sample_random_candidates(space: Mapping[str, object], size: int) -> Iterator[Mapping[str, object]]` | Generate random options. | Completed |
| `run_bounded_search(space: Mapping[str, object]) -> SearchSummary` | Run search sweep. | Completed |

## FEAT-OPT-06: Chronological Training/OOS Splits and Walk-Forward Validation (services.optimization.validation)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_time_series_splits(data: MarketDataset, folds: int) -> Sequence[TimeSplitResult]` | Construct training/OOS folds. | Completed |
| `run_walk_forward_validation(request: WalkForwardRequest) -> WalkForwardResult` | Coordinate walk-forward testing. | Completed |

## FEAT-OPT-07: Monte Carlo Shuffling Bootstrap and Execution Cost Stressing (services.optimization.robustness)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_monte_carlo(trades: Sequence[TradeRecord], runs: int) -> MonteCarloResult` | Run shuffling bootstrap. | Completed |
| `apply_execution_cost_stress(trades: Sequence[TradeRecord], stress_factor: float) -> Sequence[TradeRecord]` | Apply slippage/spread stress. | Completed |
| `assess_strategy_robustness(monte_carlo: MonteCarloResult, stress_checks: Sequence[Mapping[str, object]]) -> dict[str, object]` | Compile robustness checks. | Completed |

## FEAT-OPT-08: Candidate Results Assembly and Report Package Formatting (services.optimization.evidence)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_optimization_evidence(request: EvidenceAssemblyRequest) -> OptimizationResult` | Assemble candidate results. | Completed |
| `build_report_package(result: OptimizationResult) -> dict[str, object]` | Format report dictionaries. | Completed |

## FEAT-OPT-09: Active Optimization Checkpoint Persistence and Migrations (services.optimization.state)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `save_search_checkpoint(checkpoint: OptimizationCheckpoint) -> None` | Save active checkpoint. | Completed |
| `load_search_checkpoint(search_id: str) -> OptimizationCheckpoint` | Restore last checkpoint. | Completed |
| `persist_optimization_result(result: OptimizationResult) -> OptimizationPersistenceReceipt` | Atomic result persistence. | Completed |
| `build_optimization_artifact_path(search_id: str) -> Path` | Build target artifact path. | Completed |
| `get_optimization_migrations() -> tuple[MigrationDefinition, ...]` | Expose database migrations. | Completed |

# Portfolio

## FEAT-PORT-01: Construction Evidence and Target Activation Validation (services.portfolio.evidence)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_construction_evidence(request: PortfolioConstructionRequest) -> None` | Validate strategies and FX rates. | Completed |
| `revalidate_activation_evidence(allocation: ActivePortfolioAllocation) -> None` | Check gates prior to activation. | Completed |

## FEAT-PORT-02: Fixed, Equal, and Inverse Volatility Weights Optimization (services.portfolio.construction)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `ConstructionService.construct(evidence: ValidatedConstructionEvidence, *, created_at: datetime) -> PortfolioConstructionResult` | Construct candidate allocations. | Completed |
| `fixed_weights(weights: Mapping[str, Decimal], *, tolerance: Decimal, minimum: Decimal, maximum: Decimal) -> tuple[WeightRow, ...]` | Calculate deterministic fixed weights. | Completed |
| `equal_weights(components: Sequence[str], *, minimum: Decimal, maximum: Decimal) -> tuple[WeightRow, ...]` | Calculate deterministic equal weights. | Completed |
| `inverse_volatility_weights(volatilities: Mapping[str, Decimal], observations: Mapping[str, int], *, minimum_observations: int, minimum: Decimal, maximum: Decimal) -> tuple[WeightRow, ...]` | Calculate deterministic inverse-volatility weights. | Completed |

## FEAT-PORT-03: Active Allocations Management and Rebalance Plan Generation (services.portfolio.api)

***

| Function / Method | Purpose | Status |
| :--- | :--- | :--- |
| `PortfolioService.construct(request: PortfolioConstructionRequest, auth_context: AuthContext) -> PortfolioConstructionResult` | Construct candidate allocations. | Completed |
| `PortfolioService.status(scope: str, auth_context: AuthContext) -> ActivePortfolioAllocation` | Inspect active allocations. | Completed |
| `PortfolioService.activate(result: PortfolioConstructionResult, auth_context: AuthContext) -> ActivePortfolioAllocation` | Activate target allocations. | Completed |
| `PortfolioService.assess_drift(allocation: ActivePortfolioAllocation, auth_context: AuthContext) -> PortfolioRebalancePlan` | Reconcile active weights. | Completed |
| `PortfolioService.plan_rebalance(plan: PortfolioRebalancePlan, auth_context: AuthContext) -> PortfolioRebalancePlan` | Generate rebalance trades. | Completed |
| `PortfolioService.rollback(target_version: str, auth_context: AuthContext) -> ActivePortfolioAllocation` | Rollback active allocations. | Completed |
| `PortfolioService.history(scope: str, auth_context: AuthContext) -> Sequence[ActivePortfolioAllocation]` | Read allocation history. | Completed |

# Research

## FEAT-RES-01: Dataset Quality Assessment and Cleaning (services.research.data)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_dataset(dataset: MarketDataset) -> DataQualityReport` | Check dataset quality. | Completed |
| `clean_dataset(dataset: MarketDataset, config: CleaningConfig) -> DataFrame` | Clean data copies. | Completed |
| `enrich_dataset(data: DataFrame, config: EnrichmentConfig) -> DataFrame` | Add returns/geometry. | Completed |
| `prepare_research_dataset(dataset: MarketDataset, config: CleaningConfig, enrichment: EnrichmentConfig) -> PreparedDataset` | Prepare research data. | Completed |

## FEAT-RES-02: Excursions, Hurst Exponent, and Technical Features Assembly (services.research.features)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_research_feature_frame(data: DataFrame, config: FeatureConfig) -> DataFrame` | Assemble feature matrix. | Completed |
| `forward_max_adverse_excursion(highs: Series, closes: Series, horizons: Sequence[int]) -> DataFrame` | Compute max adverse excursions. | Completed |
| `forward_max_favorable_excursion(lows: Series, closes: Series, horizons: Sequence[int]) -> DataFrame` | Compute max favorable excursions. | Completed |
| `forward_returns(closes: Series, horizons: Sequence[int]) -> DataFrame` | Calculate forward returns. | Completed |
| `hurst_exponent(prices: Series) -> float` | Compute Hurst exponents. | Completed |
| `rolling_hurst(prices: Series, window: int) -> Series` | Compute rolling Hurst exponent. | Completed |
| `log_returns(prices: Series) -> Series` | Calculate log returns series. | Completed |
| `simple_returns(prices: Series) -> Series` | Calculate simple returns series. | Completed |
| `calculate_returns(prices: Series) -> Series` | Calculate returns series. | Missing |
| `calculate_hurst(prices: Series) -> float` | Compute Hurst exponents. | Missing |
| `calculate_forward_returns(prices: Series, horizons: Sequence[int]) -> DataFrame` | Calculate forward returns. | Missing |
| `calculate_excursions(highs: Series, lows: Series, closes: Series) -> DataFrame` | Compute excursions. | Missing |
| `assemble_feature_frame(data: DataFrame, config: FeatureConfig) -> DataFrame` | Assemble feature matrix. | Missing |

## FEAT-RES-03: Lookahead Leakage Prevention and Time-Series splits (services.research.leakage)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `enforce_time_split(features: DataFrame, train_ratio: float, validation_ratio: float, embargo_pct: float) -> TimeSplitResult` | Run chronological splits with embargo mask. | Completed |
| `mask_research_artifact(artifact: Mapping[str, Any], allowed_keys: Sequence[str]) -> Mapping[str, Any]` | Redact sensitive/secret info in serialized output mappings. | Completed |
| `validate_no_lookahead_features(features: DataFrame, allowed_forward: Sequence[str]) -> None` | Verify features contain no future values / leakages. | Completed |
| `validate_leakage(features: DataFrame, allowed_forward: Sequence[str]) -> LeakageReport` | Detect lookahead leakage. | Missing |
| `validate_features(features: DataFrame) -> None` | Validate feature matrices. | Missing |
| `split_chronological(features: DataFrame, train_ratio: float) -> TimeSplitResult` | Run chronological splits. | Missing |
| `build_time_splits(features: DataFrame, config: FeatureConfig) -> TimeSplitResult` | Build train/validation/test folds. | Missing |
| `apply_embargo(splits: TimeSplitResult, embargo_seconds: int) -> TimeSplitResult` | Discard overlapping OOS logs. | Missing |
| `mask_recursive(payload: Mapping[str, Any]) -> Mapping[str, Any]` | Mask nested payload structures. | Missing |

## FEAT-RES-04: Returns, Drawdowns, Volatility, and Seasonality Profiling (services.research.metrics)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_core_metric_profile(dataset: PreparedDataset, config: EdgeLabConfig) -> CoreMetricProfile` | Build core metric profiles. | Completed |
| `build_default_registry() -> MetricRegistry` | Expose metric calculators. | Completed |
| `build_metric_registry() -> MetricRegistry` | Expose metric calculators. | Missing |
| `calculate_returns_distribution(prices: Series) -> Mapping[str, float]` | Compute returns profile. | Missing |
| `calculate_streak_distribution(prices: Series) -> Mapping[str, float]` | Compute streak profile. | Missing |
| `calculate_drawdown_distribution(prices: Series) -> Mapping[str, float]` | Compute drawdown profile. | Missing |
| `calculate_volatility_profile(prices: Series) -> Mapping[str, float]` | Compute volatility profile. | Missing |
| `calculate_seasonality_profile(prices: Series) -> Mapping[str, float]` | Compute seasonality profile. | Missing |
| `calculate_structure_metrics(prices: Series) -> Mapping[str, float]` | Compute structure profile. | Missing |

## FEAT-RES-05: Null Hypothesis Model Baseline and EDS Resampling (services.research.statistics)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `benjamini_hochberg(p_values: Sequence[float]) -> tuple[float, ...]` | Apply FDR Benjamini-Hochberg correction. | Completed |
| `block_bootstrap_ci(data: Series, samples: int, alpha: float) -> tuple[float, float]` | Compute block bootstrap confidence intervals. | Completed |
| `block_bootstrap_distribution(data: Series, samples: int) -> tuple[float, ...]` | Compute block bootstrap distribution. | Completed |
| `compute_null_percentile(observed: float, null_dist: Sequence[float]) -> float` | Compute percentile of observed against null distribution. | Completed |
| `exceeds_null_threshold(observed: float, null_dist: Sequence[float], alpha: float) -> bool` | Check if observed value is statistically significant. | Completed |
| `holm_bonferroni(p_values: Sequence[float]) -> tuple[float, ...]` | Apply Holm-Bonferroni step-down correction. | Completed |
| `null_distribution_stats(null_dist: Sequence[float]) -> Mapping[str, float]` | Compute descriptive statistics of null distribution. | Completed |
| `permutation_test(data_a: Series, data_b: Series, samples: int) -> float` | Perform two-sample permutation test. | Completed |
| `r_space_null(data: Series, samples: int) -> tuple[Series, ...]` | Compute random parameter space null hypothesis base. | Completed |
| `random_entry_null(data: Series, samples: int) -> tuple[Series, ...]` | Compute random entry strategy null hypothesis base. | Completed |
| `session_randomized_null(data: Series, samples: int) -> tuple[Series, ...]` | Compute session randomized null hypothesis base. | Completed |
| `shuffle_returns_null(data: Series, samples: int) -> tuple[Series, ...]` | Compute shuffled returns null hypothesis base. | Completed |
| `run_eds_bootstrap(data: Series, samples: int) -> tuple[Series, ...]` | Run bootstrap resamples. | Missing |
| `run_eds_permutation(data: Series, samples: int) -> tuple[Series, ...]` | Run permutation tests. | Missing |
| `build_null_model(data: Series) -> Series` | Build null models. | Missing |
| `apply_bonferroni(p_values: Sequence[float]) -> tuple[float, ...]` | Apply Bonferroni correction. | Missing |
| `apply_fdr_bh(p_values: Sequence[float]) -> tuple[float, ...]` | Apply FDR BH correction. | Missing |

## FEAT-RES-06: Session Edge, Mean Reversion, and Trend Persistence Studies (services.research.studies)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `classify_symbol(profile: CoreMetricProfile) -> str` | Classify market structures or asset edges. | Completed |
| `compare_to_null(observed: float, null_dist: Sequence[float]) -> float` | Check observed against null. | Completed |
| `get_acceptance_criteria(alpha: float) -> float` | Compute alpha thresholds. | Completed |
| `run_eds_null_baseline(study: str, config: StudyConfig) -> Mapping[str, float]` | Generate baseline null models. | Completed |
| `run_mean_reversion_study(features: DataFrame, config: StudyConfig) -> EdgeResult` | Run mean reversion study. | Missing |
| `run_trend_persistence_study(features: DataFrame, config: StudyConfig) -> EdgeResult` | Run trend persistence study. | Missing |
| `run_session_edge_study(features: DataFrame, config: StudyConfig) -> EdgeResult` | Run session edge study. | Missing |
| `evaluate_run_significance(observed: float, null_baseline: Mapping[str, float]) -> float` | Calculate edge p-values. | Missing |
| `calculate_hurst_bootstrap(prices: Series, samples: int) -> tuple[float, float]` | Compute Hurst bootstrap. | Missing |
| `calculate_streak_bootstrap(prices: Series, samples: int) -> tuple[float, float]` | Compute streak bootstrap. | Missing |
| `calculate_excursion_bootstrap(highs: Series, lows: Series, closes: Series, samples: int) -> tuple[float, float]` | Compute excursion bootstrap. | Missing |
| `run_edge_studies_sweep(features: DataFrame, sweep_config: Mapping[str, object]) -> Sequence[EdgeResult]` | Sweep multiple edge configurations. | Missing |
| `verify_isolated_study_failures(results: Sequence[EdgeResult]) -> None` | Verify and handle failures. | Missing |
| `classify_edge(metrics: Mapping[str, float]) -> str` | Classify edge results. | Missing |
| `confirm_edge(result: EdgeResult, criteria: float) -> bool` | Assess edge confidence. | Missing |

## FEAT-RES-07: Seasonality Hour Boundaries and Intraday Return Analysis (services.research.seasonality)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `active_sessions_for_hour(hour: int, *, config: SessionConfig) -> tuple[str, ...]` | Return every configured session active for a timezone-aware hour using canonical overlap precedence. (`FR-RES-069`) | Missing |
| `session_label_for_hour(hour: int, *, config: SessionConfig) -> str` | Return the deterministic primary session label for an hour while preserving overlap evidence. (`FR-RES-070`) | Missing |
| `session_hours_payload(*, config: SessionConfig) -> Mapping[str, JSONValue]` | Return a machine-readable payload of timezone, windows, order, overlaps, and schema version. (`FR-RES-071`) | Missing |
| `tag_sessions(data: DataFrame, *, config: SessionConfig) -> tuple[DataFrame, tuple[ResearchWarning, ...]]` | Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order. (`FR-RES-072`) | Missing |
| `SeasonalityFilters(years: tuple[int, ...] = (), months: tuple[int, ...] = (), weekdays: tuple[int, ...] = (), hours: tuple[int, ...] = (), sessions: tuple[str, ...] = ())` | Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions. (`FR-RES-073`) | Missing |
| `run_seasonality(prepared: PreparedDataset, *, sessions: SessionConfig, filters: SeasonalityFilters, limits: ResearchResourceLimits) -> Mapping[str, JSONValue]` | Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes from supplied data and filters. (`FR-RES-074`) | Missing |

## FEAT-RES-08: Market Structure Legs Detection and Stability Assessment (services.research.market_structure)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `detect_structure_legs(prices: Series) -> DataFrame` | Detect structural high/low legs. | Missing |
| `build_market_structure_profile(dataset: PreparedDataset, config: MarketStructureConfig) -> MarketStructureProfile` | Compile structural profiles. | Missing |
| `evaluate_structure_stability(profile: MarketStructureProfile) -> MarketStructureQualityReport` | Assess structure stability. | Missing |
| `validate_market_structure(profile: MarketStructureProfile) -> None` | Validate structural regimes. | Missing |
| `calibrate_market_structure(profile: MarketStructureProfile) -> MarketStructureProfile` | Calibrate regime parameters. | Missing |
| `evaluate_strategy_fit(profile: MarketStructureProfile, strategy_id: str) -> Mapping[str, float]` | Assess suitability scores. | Missing |

## FEAT-RES-09: Unsupervised PCA and K-Means Risk Factor Clustering (services.research.modeling)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `decompose_pca(features: DataFrame, components: int) -> Mapping[str, Any]` | Compute PCA components. | Missing |
| `cluster_kmeans(features: DataFrame, clusters: int) -> Series` | Compute K-Means clusters. | Missing |
| `generate_cluster_insights(features: DataFrame, labels: Series) -> Mapping[str, Any]` | Generate cluster summaries. | Missing |
| `identify_pca_risk_factors(pca: Mapping[str, Any], top_count: int) -> tuple[Mapping[str, Any], ...]` | Extract PCA absolute factor weights. | Missing |
| `analyze_cluster_outperformance(data: DataFrame, labels: Series, horizon: int) -> tuple[Mapping[str, Any], ...]` | Compare cluster forward returns. | Missing |
| `build_unsupervised_insight_report(features: DataFrame, config: UnsupervisedResearchConfig) -> Mapping[str, Any]` | Build unsupervised insight reports. | Missing |
| `run_unsupervised_research(features: DataFrame, config: UnsupervisedResearchConfig, limits: ResearchResourceLimits) -> UnsupervisedResearchResult` | Run unsupervised modeling workflow. | Missing |

## FEAT-RES-10: Complete Scorecards compilation and Profile Snapshot Rendering (services.research.profiles)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_research_scorecard(metric_profile: CoreMetricProfile, seasonality: Mapping[str, Any] \| None, edges: Sequence[EdgeResult], market_structure: MarketStructureProfile \| None, modeling: UnsupervisedResearchResult \| None, performance: PerformanceReport \| None = None) -> ResearchScorecard` | Score structural evidence metrics. | Missing |
| `build_research_profile_snapshot(stages: Mapping[str, Any], scorecard: ResearchScorecard, dataset_hash: str, configuration_hash: str) -> ResearchProfileSnapshot` | Compile stage records. | Missing |
| `build_profile_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, Any]` | Summarize snapshot profiles. | Missing |
| `build_dashboard_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, Any]` | Format snapshot dashboard parameters. | Missing |
| `render_research_report(report: ResearchReport, format: str) -> str` | Render snapshot reports. | Missing |
| `render_profile_comparison(left: ResearchProfileSnapshot, right: ResearchProfileSnapshot) -> str` | Render diff comparison reports. | Missing |
| `generate_multi_symbol_report(reports: Mapping[str, ResearchReport], format: str) -> str` | Render multi-report summaries. | Missing |
| `run_edge_lab_profile(dataset: MarketDataset, config: EdgeLabConfig, performance: PerformanceReport \| None = None) -> ResearchReport` | Orchestrate complete edge lab run. | Missing |

## FEAT-RES-11: Research Report Artifact Writer (services.research.artifacts)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `write_research_artifact(report: ResearchReport, config: ArtifactWriteConfig) -> ArtifactReference` | Persist report artifact. | Missing |

# API

## FEAT-API-01: FastAPI Gateway Application Initialization (services.api.composition)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_app(settings: RuntimeSettings) -> FastAPI` | Initialize the FastAPI gateway application. | Missing |
| `build_broker_connection_config(credentials: Mapping[str, Any]) -> BrokerConnectionConfig` | Construct connection configs from credentials. | Missing |

## FEAT-API-02: User Authentication and Session Token Validation (services.api.identity)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `hash_password(password: str) -> str` | Hash passwords. | Missing |
| `verify_password(password: str, hashed: str) -> bool` | Verify password hashes. | Missing |
| `store_credential(ref: str, payload: Mapping[str, Any]) -> CredentialRecord` | Encrypt and store broker credentials. | Missing |
| `resolve_credential_reference(ref: str) -> Mapping[str, Any]` | Decrypt credentials. | Missing |
| `authenticate_user(username: str, password: str) -> AuthenticatedUser` | Authenticate user credentials. | Missing |
| `create_session(user: AuthenticatedUser) -> SessionCredential` | Establish secure sessions. | Missing |
| `validate_session(credential: SessionCredential) -> AuthenticatedPrincipal` | Verify session validity and permissions. | Missing |
| `revoke_session(credential: SessionCredential) -> None` | Invalidate session tokens. | Missing |
| `build_auth_context(principal: AuthenticatedPrincipal, trace: TraceContext) -> AuthContext` | Translate user claims to AuthContext. | Missing |
| `require_permission(context: AuthContext, permission: str) -> None` | Enforce permission limits. | Missing |
| `validate_governed_request(context: AuthContext, governed: GovernedRequestContext) -> None` | Enforce governed action limits. | Missing |

## FEAT-API-03: Liveness and Readiness Probes (services.api.health)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_liveness() -> ApiResponse[Liveness]` | Probe process liveness. | Missing |
| `get_readiness(context: AuthContext) -> ApiResponse[Readiness]` | Probe process readiness. | Missing |
| `check_clock_drift(reference: datetime, *, tolerance_seconds: Decimal) -> Decimal` | Report signed local-clock drift against an authoritative external instant for readiness diagnostics. | Missing |

## FEAT-API-04: FastAPI Gateway Owner Event Stream Event Formatting (services.api.streams)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_stream_event(event: OwnerEvent, trace: TraceContext) -> StreamEvent[Any]` | Format domain events for stream wrappers. | Missing |

## FEAT-API-05: Operational Telemetry Recording and Prometheus Exposition (services.api.observability)

***

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `record_metric(name: str, value: Decimal, *, labels: Mapping[str, str], sink: MetricSink) -> None` | Record one counter, gauge, or timing observation through an explicitly injected sink. | Missing |
| `validate_metric_labels(labels: Mapping[str, str]) -> None` | Reject high-cardinality and secret-bearing label values before emission. | Missing |
| `build_metric_snapshot(sink: MetricSink) -> MetricSnapshot` | Collect a bounded point-in-time view of recorded telemetry. | Missing |
| `export_prometheus_metrics(snapshot: MetricSnapshot) -> str` | Render a metric snapshot in Prometheus text exposition format. | Missing |
| `get_metrics(context: AuthContext) -> ApiResponse[str]` | Serve the protected Prometheus scrape endpoint. | Missing |
