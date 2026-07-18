# Functions Register

This document registers all public and planned exported functions across the HaruQuantAI domain packages.

<h3>1. Utils (<code>app/utils/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4">errors.py</td>
      <td><code>map_exception(exc: Exception) -> ErrorEvidence</code></td>
      <td>Convert caught exceptions to deterministic secret-safe shared error evidence.</td>
    </tr>
    <tr>
      <td><code>normalize_error_code(code: str) -> str</code></td>
      <td>Normalize an error code to a consistent format.</td>
    </tr>
    <tr>
      <td><code>get_error_metadata(code: str) -> ErrorMetadata</code></td>
      <td>Look up immutable safe error metadata without a mutable registry.</td>
    </tr>
    <tr>
      <td><code>route_error_event(exc: Exception, sink: ErrorSink) -> None</code></td>
      <td>Synchronously deliver a safe error payload to an explicitly injected sink.</td>
    </tr>
    <tr>
      <td rowspan="3">identity.py</td>
      <td><code>generate_id(prefix: str) -> str</code></td>
      <td>Generate prefixed UUID4 identifiers without embedded secrets.</td>
    </tr>
    <tr>
      <td><code>validate_id(identifier: str) -> None</code></td>
      <td>Validate supported prefixes and canonical identifier syntax.</td>
    </tr>
    <tr>
      <td><code>derive_stable_id(material: str) -> str</code></td>
      <td>Derive deterministic SHA-256 identifiers from canonical, caller-supplied identity material.</td>
    </tr>
    <tr>
      <td rowspan="5">time.py</td>
      <td><code>utc_now(clock: Clock | None = None) -> datetime</code></td>
      <td>Return aware UTC time from an injectable clock.</td>
    </tr>
    <tr>
      <td><code>parse_utc_timestamp(timestamp: str) -> datetime</code></td>
      <td>Parse UTC timestamps using canonical output.</td>
    </tr>
    <tr>
      <td><code>format_utc_timestamp(dt: datetime) -> str</code></td>
      <td>Format UTC timestamps using canonical Z output.</td>
    </tr>
    <tr>
      <td><code>age_seconds(dt: datetime, reference: datetime | None = None) -> float</code></td>
      <td>Calculate non-negative age against an injected instant.</td>
    </tr>
    <tr>
      <td><code>is_fresh(dt: datetime, max_age_seconds: float, reference: datetime | None = None) -> bool</code></td>
      <td>Evaluate freshness against an injected instant.</td>
    </tr>
    <tr>
      <td rowspan="2">serialization.py</td>
      <td><code>to_json_safe(value: Any) -> Any</code></td>
      <td>Convert supported datetimes, decimals, enums, dataclasses, mappings, and sequences to deterministic JSON-safe values.</td>
    </tr>
    <tr>
      <td><code>canonical_json(value: Any) -> str</code></td>
      <td>Produce stable UTF-8 JSON with sorted keys and no hidden redaction.</td>
    </tr>
    <tr>
      <td rowspan="9">security.py</td>
      <td><code>is_sensitive_key(key: str) -> bool</code></td>
      <td>Detect sensitive keys case-insensitively.</td>
    </tr>
    <tr>
      <td><code>redact_text_value(value: str, policy: RedactionPolicy) -> str</code></td>
      <td>Redact message patterns in a string without mutating input.</td>
    </tr>
    <tr>
      <td><code>redact_mapping_value(value: Mapping[str, Any], policy: RedactionPolicy) -> Mapping[str, Any]</code></td>
      <td>Recursively redact a JSON-safe mapping without mutating input.</td>
    </tr>
    <tr>
      <td><code>hash_password(password: str) -> str</code></td>
      <td>Hash passwords with a random salt.</td>
    </tr>
    <tr>
      <td><code>verify_password(password: str, hashed: str) -> bool</code></td>
      <td>Verify passwords using constant-time comparison.</td>
    </tr>
    <tr>
      <td><code>generate_fernet_key() -> str</code></td>
      <td>Generate Fernet keys.</td>
    </tr>
    <tr>
      <td><code>encrypt_text(text: str, key: str) -> str</code></td>
      <td>Encrypt UTF-8 text with authenticated symmetric encryption.</td>
    </tr>
    <tr>
      <td><code>decrypt_text(token: str, key: str) -> str</code></td>
      <td>Decrypt UTF-8 text with authenticated symmetric encryption.</td>
    </tr>
    <tr>
      <td><code>select_active_secret_version(versions: Sequence[SecretVersion]) -> SecretVersion</code></td>
      <td>Select exactly one explicitly active immutable secret version.</td>
    </tr>
    <tr>
      <td rowspan="2">settings.py</td>
      <td><code>load_settings(profile: str | None = None) -> RuntimeSettings</code></td>
      <td>Load explicit values and centralized settings in precedence order.</td>
    </tr>
    <tr>
      <td><code>resolve_secret_reference(reference: str, source: SecretSource) -> str</code></td>
      <td>Resolve secret references at the composition root.</td>
    </tr>
    <tr>
      <td rowspan="4">logging.py</td>
      <td><code>get_logger(name: str) -> BoundLogger</code></td>
      <td>Return stable child loggers without configuring handlers.</td>
    </tr>
    <tr>
      <td><code>configure_logging(settings: LoggingSettings) -> None</code></td>
      <td>Atomically install console and file handlers from the approved default profile.</td>
    </tr>
    <tr>
      <td><code>flush_logging() -> None</code></td>
      <td>Flush buffered log records to their sinks.</td>
    </tr>
    <tr>
      <td><code>shutdown_logging() -> None</code></td>
      <td>Stop queue thread listeners and release logging resources.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>2. Brokers (<code>app/services/brokers/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function / Method</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="3">registry.py</td>
      <td><code>create_broker_adapter(broker_id: str, config: BrokerConnectionConfig) -> BrokerAdapter</code></td>
      <td>Factory function to instantiate provider adapters.</td>
    </tr>
    <tr>
      <td><code>get_broker_capability_catalogue(broker_id: str) -> BrokerCapability</code></td>
      <td>Retrieve capability matrix details for a provider.</td>
    </tr>
    <tr>
      <td><code>get_registered_brokers() -> tuple[str, ...]</code></td>
      <td>Expose all registered/supported brokers.</td>
    </tr>
    <tr>
      <td rowspan="2">mt5.py</td>
      <td><code>MT5BrokerAdapter.connect() -> None</code></td>
      <td>Establish MT5 provider connection.</td>
    </tr>
    <tr>
      <td><code>MT5BrokerAdapter.disconnect() -> None</code></td>
      <td>Disconnect MT5 provider connection.</td>
    </tr>
    <tr>
      <td rowspan="2">ctrader.py</td>
      <td><code>CTraderBrokerAdapter.connect() -> None</code></td>
      <td>Establish cTrader provider connection.</td>
    </tr>
    <tr>
      <td><code>CTraderBrokerAdapter.disconnect() -> None</code></td>
      <td>Disconnect cTrader provider connection.</td>
    </tr>
    <tr>
      <td rowspan="2">binance.py</td>
      <td><code>BinanceBrokerAdapter.connect() -> None</code></td>
      <td>Establish Binance provider connection.</td>
    </tr>
    <tr>
      <td><code>BinanceBrokerAdapter.disconnect() -> None</code></td>
      <td>Disconnect Binance provider connection.</td>
    </tr>
    <tr>
      <td rowspan="2">dukascopy.py</td>
      <td><code>DukascopyBrokerAdapter.connect() -> None</code></td>
      <td>Establish Dukascopy provider connection.</td>
    </tr>
    <tr>
      <td><code>DukascopyBrokerAdapter.disconnect() -> None</code></td>
      <td>Disconnect Dukascopy provider connection.</td>
    </tr>
    <tr>
      <td rowspan="2">yahoo.py</td>
      <td><code>YahooBrokerAdapter.connect() -> None</code></td>
      <td>Establish Yahoo provider connection.</td>
    </tr>
    <tr>
      <td><code>YahooBrokerAdapter.disconnect() -> None</code></td>
      <td>Disconnect Yahoo provider connection.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>3. Data (<code>app/services/data/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="23">public_api.py</td>
      <td><code>aggregate_ticks_to_bars(ticks: Sequence[TickRecord], timeframe: str) -> Sequence[BarRecord]</code></td>
      <td>Aggregate a list of tick records to bars.</td>
    </tr>
    <tr>
      <td><code>align_multitimeframe_data(data: Mapping[str, Sequence[BarRecord]], primary_timeframe: str) -> Mapping[str, Sequence[BarRecord]]</code></td>
      <td>Align multitimeframe bars to a primary timeframe index.</td>
    </tr>
    <tr>
      <td><code>clear_data_cache() -> None</code></td>
      <td>Clear cached historical datasets.</td>
    </tr>
    <tr>
      <td><code>create_data_update_job(job_config: JobConfig) -> str</code></td>
      <td>Create a new historical data update job.</td>
    </tr>
    <tr>
      <td><code>generate_synthetic_bars(spec: SyntheticBarSpec) -> Sequence[BarRecord]</code></td>
      <td>Generate synthetic bar data for testing.</td>
    </tr>
    <tr>
      <td><code>generate_synthetic_ticks(spec: SyntheticTickSpec) -> Sequence[TickRecord]</code></td>
      <td>Generate synthetic tick data for testing.</td>
    </tr>
    <tr>
      <td><code>get_data_availability(source_id: str, symbol: str) -> DataAvailability</code></td>
      <td>Get stored range and record count evidence.</td>
    </tr>
    <tr>
      <td><code>get_data_update_job_status(job_id: str) -> JobStatus</code></td>
      <td>Get historical update job execution status.</td>
    </tr>
    <tr>
      <td><code>get_feed_status(feed_id: str) -> FeedStatus</code></td>
      <td>Check real-time subscription feed connection status.</td>
    </tr>
    <tr>
      <td><code>get_historical_volume(source_id: str, symbol: str) -> VolumeResult</code></td>
      <td>Retrieve historical execution volume summary.</td>
    </tr>
    <tr>
      <td><code>get_market_data(source_id: str, symbol: str, timeframe: str) -> MarketDataResult</code></td>
      <td>Retrieve historical bar datasets.</td>
    </tr>
    <tr>
      <td><code>get_market_hours(source_id: str, symbol: str) -> MarketHours</code></td>
      <td>Retrieve market hours and sessions for a symbol.</td>
    </tr>
    <tr>
      <td><code>get_spread_data(source_id: str, symbol: str) -> SpreadResult</code></td>
      <td>Retrieve historical spread statistics.</td>
    </tr>
    <tr>
      <td><code>get_symbol_metadata(source_id: str, symbol: str) -> SymbolMetadata</code></td>
      <td>Retrieve static contract and pricing rules.</td>
    </tr>
    <tr>
      <td><code>get_tick_data(source_id: str, symbol: str) -> TickResult</code></td>
      <td>Retrieve historical tick datasets.</td>
    </tr>
    <tr>
      <td><code>get_trading_sessions(source_id: str, symbol: str) -> TradingSessions</code></td>
      <td>Retrieve trading sessions for a symbol.</td>
    </tr>
    <tr>
      <td><code>list_symbols(source_id: str, query: str) -> SymbolList</code></td>
      <td>Search and list symbols matching query.</td>
    </tr>
    <tr>
      <td><code>load_local_dataset(path: str) -> MarketDataset</code></td>
      <td>Load local parquet/CSV files.</td>
    </tr>
    <tr>
      <td><code>resample_ohlcv(bars: Sequence[BarRecord], target_timeframe: str) -> Sequence[BarRecord]</code></td>
      <td>Resample OHLCV bars to target timeframe.</td>
    </tr>
    <tr>
      <td><code>run_data_update_job_once(job_id: str) -> None</code></td>
      <td>Trigger single update/backfill job execution.</td>
    </tr>
    <tr>
      <td><code>save_market_data(dataset: MarketDataset) -> None</code></td>
      <td>Persist new market data snapshot.</td>
    </tr>
    <tr>
      <td><code>start_data_update_job(job_id: str) -> None</code></td>
      <td>Start background scheduler/worker update daemon.</td>
    </tr>
    <tr>
      <td><code>stop_data_update_job(job_id: str) -> None</code></td>
      <td>Stop background scheduler/worker update daemon.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>4. Indicators (<code>app/services/indicators/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4">candles.py</td>
      <td><code>doji(candles: Sequence[BarRecord]) -> Sequence[bool]</code></td>
      <td>Detect Doji candles.</td>
    </tr>
    <tr>
      <td><code>engulfing(candles: Sequence[BarRecord]) -> Sequence[bool]</code></td>
      <td>Detect Engulfing candles.</td>
    </tr>
    <tr>
      <td><code>inside_bar(candles: Sequence[BarRecord]) -> Sequence[bool]</code></td>
      <td>Detect Inside Bar candles.</td>
    </tr>
    <tr>
      <td><code>pinbar(candles: Sequence[BarRecord]) -> Sequence[bool]</code></td>
      <td>Detect Pinbar candles.</td>
    </tr>
    <tr>
      <td rowspan="4">core.py</td>
      <td><code>get_capability_matrix() -> Mapping[str, Any]</code></td>
      <td>Expose indicator capability matrix.</td>
    </tr>
    <tr>
      <td><code>get_indicator(name: str) -> IndicatorProtocol</code></td>
      <td>Factory function for indicators.</td>
    </tr>
    <tr>
      <td><code>list_indicators() -> tuple[str, ...]</code></td>
      <td>Expose all registered indicators.</td>
    </tr>
    <tr>
      <td><code>validate_indicator(name: str) -> None</code></td>
      <td>Validate indicator parameters.</td>
    </tr>
    <tr>
      <td rowspan="2">momentum.py</td>
      <td><code>rsi(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Relative Strength Index.</td>
    </tr>
    <tr>
      <td><code>williams_r(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Williams %R.</td>
    </tr>
    <tr>
      <td rowspan="6">trend.py</td>
      <td><code>adx(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Average Directional Index.</td>
    </tr>
    <tr>
      <td><code>bollinger_bands(prices: Sequence[Decimal], period: int, standard_deviations: int) -> BollingerBandsResult</code></td>
      <td>Compute Bollinger Bands.</td>
    </tr>
    <tr>
      <td><code>ema(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Exponential Moving Average.</td>
    </tr>
    <tr>
      <td><code>hull_ma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Hull Moving Average.</td>
    </tr>
    <tr>
      <td><code>sma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Simple Moving Average.</td>
    </tr>
    <tr>
      <td><code>wma(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Weighted Moving Average.</td>
    </tr>
    <tr>
      <td rowspan="4">volatility.py</td>
      <td><code>adr(highs: Sequence[Decimal], lows: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Average Daily Range.</td>
    </tr>
    <tr>
      <td><code>atr(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Average True Range.</td>
    </tr>
    <tr>
      <td><code>rolling_volatility(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute rolling volatility.</td>
    </tr>
    <tr>
      <td><code>standard_deviation(prices: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute rolling standard deviation.</td>
    </tr>
    <tr>
      <td rowspan="4">volume.py</td>
      <td><code>cmf(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], volumes: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Chaikin Money Flow.</td>
    </tr>
    <tr>
      <td><code>mfi(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], volumes: Sequence[Decimal], period: int) -> Sequence[Decimal]</code></td>
      <td>Compute Money Flow Index.</td>
    </tr>
    <tr>
      <td><code>obv(prices: Sequence[Decimal], volumes: Sequence[Decimal]) -> Sequence[Decimal]</code></td>
      <td>Compute On-Balance Volume.</td>
    </tr>
    <tr>
      <td><code>price_volume_distribution(prices: Sequence[Decimal], volumes: Sequence[Decimal], bin_count: int) -> PriceVolumeDistributionResult</code></td>
      <td>Compute price-volume distribution bins.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>5. Strategy (<code>app/services/strategy/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>intents.py</td>
      <td><code>build_trade_intent(decision: StrategyDecision, context: StrategyExecutionContext, sequence: int) -> StrategyOutcome[TradeIntent]</code></td>
      <td>Build a schema-valid intent with deterministic IDs, sequence, and parent/lineage references.</td>
    </tr>
    <tr>
      <td rowspan="3">replay.py</td>
      <td><code>create_strategy_checkpoint(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, state: Mapping[str, JsonValue], authorization_ref: str) -> StrategyOutcome[StrategyCheckpoint]</code></td>
      <td>Serialize and checksum candidate local decision state.</td>
    </tr>
    <tr>
      <td><code>validate_strategy_checkpoint(checkpoint: StrategyCheckpoint, ref: ValidatedStrategyRef, config: ValidatedStrategyConfig) -> StrategyOutcome[Mapping[str, JsonValue]]</code></td>
      <td>Reject corrupt, incompatible, or oversized checkpoints before execution.</td>
    </tr>
    <tr>
      <td><code>create_strategy_replay_manifest(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, context: StrategyExecutionContext, data_checksum: str, indicator_manifest_hash: str, simulation_config_hash: str) -> StrategyOutcome[StrategyReplayManifest]</code></td>
      <td>Create deterministic replay manifest from inputs.</td>
    </tr>
    <tr>
      <td>diagnostics.py</td>
      <td><code>export_strategy_diagnostics(context: StrategyExecutionContext, facts: Mapping[str, JsonValue]) -> StrategyOutcome[StrategyDiagnostics]</code></td>
      <td>Export schema-valid diagnostics after size enforcement.</td>
    </tr>
    <tr>
      <td rowspan="5">registry.py</td>
      <td><code>list_strategy_versions(strategy_id: str | None = None) -> StrategyOutcome[tuple[ValidatedStrategyRef, ...]]</code></td>
      <td>Return registered entries in deterministic order.</td>
    </tr>
    <tr>
      <td><code>register_strategy_version(request: StrategyRegistrationRequest, auth: AuthContext) -> StrategyOutcome[ValidatedStrategyRef]</code></td>
      <td>Register unique version after module, hash, and lifecycle checks.</td>
    </tr>
    <tr>
      <td><code>update_strategy_parameters(request: StrategyParameterUpdateRequest, auth: AuthContext) -> StrategyOutcome[ValidatedStrategyConfig]</code></td>
      <td>Validate and record parameter updates.</td>
    </tr>
    <tr>
      <td><code>validate_strategy_config(ref: ValidatedStrategyRef, config: StrategyConfig) -> StrategyOutcome[ValidatedStrategyConfig]</code></td>
      <td>Validate declarative config and resource limits.</td>
    </tr>
    <tr>
      <td><code>validate_strategy_ref(ref: StrategyRef) -> StrategyOutcome[ValidatedStrategyRef]</code></td>
      <td>Resolve exactly one approved reference.</td>
    </tr>
    <tr>
      <td>vectorized.py</td>
      <td><code>run_vectorized_strategy_signals(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, market: MarketDataset, indicators: tuple[IndicatorSeries, ...], context: StrategyExecutionContext) -> StrategyOutcome[StrategyExecutionResult]</code></td>
      <td>Run synchronous vectorized logic without lookahead.</td>
    </tr>
    <tr>
      <td>event.py</td>
      <td><code>run_event_strategy_hook(ref: ValidatedStrategyRef, config: ValidatedStrategyConfig, event: StrategyEvent, context: StrategyExecutionContext, local_state: Mapping[str, JsonValue] | None = None) -> StrategyOutcome[StrategyExecutionResult]</code></td>
      <td>Invoke stateful hook in priority order.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>6. Risk (<code>app/services/risk/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function / Method</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>portfolio.py</td>
      <td><code>normalize_risk_evidence(evidence: Mapping[str, object]) -> RiskEvidence</code></td>
      <td>Validate and normalize risk snapshots.</td>
    </tr>
    <tr>
      <td rowspan="2">policy.py</td>
      <td><code>evaluate_risk_limits(request: AllocationReviewRequest) -> AllocationRiskDecision</code></td>
      <td>Assess portfolio limits, allocation caps, and stop conditions.</td>
    </tr>
    <tr>
      <td><code>evaluate_compliance_limits(request: AllocationReviewRequest) -> AllocationRiskDecision</code></td>
      <td>Assess regulatory and prop-firm compliance constraints.</td>
    </tr>
    <tr>
      <td>regimes.py</td>
      <td><code>evaluate_market_regime(evidence: MarketContextEvidence) -> RegimeAssessment</code></td>
      <td>Determine volatility regimes.</td>
    </tr>
    <tr>
      <td rowspan="2">sizing.py</td>
      <td><code>calculate_position_size(request: SizingRequest) -> SizingResult</code></td>
      <td>Compute leverage and risk-adjusted sizing.</td>
    </tr>
    <tr>
      <td><code>validate_sizing_limits(result: SizingResult) -> SizingResult</code></td>
      <td>Validate sizing against absolute bounds.</td>
    </tr>
    <tr>
      <td rowspan="3">approvals.py</td>
      <td><code>create_approval_token(principal: str, action: str, ttl: int) -> ApprovalToken</code></td>
      <td>Create ephemeral approval token.</td>
    </tr>
    <tr>
      <td><code>revoke_approval_token(token_id: str) -> None</code></td>
      <td>Revoke approval token.</td>
    </tr>
    <tr>
      <td><code>verify_approval_token(token_id: str, action: str) -> bool</code></td>
      <td>Verify approval token validity.</td>
    </tr>
    <tr>
      <td>decisions.py</td>
      <td><code>RiskGovernor.submit_run_request(request: RunRequest) -> RunDecision</code></td>
      <td>Evaluate and authorize strategy runs.</td>
    </tr>
    <tr>
      <td>scenarios.py</td>
      <td><code>evaluate_risk_scenarios(portfolio: ActivePortfolioAllocation, shocks: Sequence[Mapping[str, object]]) -> ScenarioResult</code></td>
      <td>Evaluate simulated shocks.</td>
    </tr>
    <tr>
      <td>reporting.py</td>
      <td><code>build_risk_summary(decision: AllocationRiskDecision) -> dict[str, object]</code></td>
      <td>Render human-readable risk diagnostics.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>7. Trading (<code>app/services/trading/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function / Method</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="3">validation.py</td>
      <td><code>validate_trading_readiness(session_id: str) -> ReadinessResult</code></td>
      <td>Ensure database, feeds, and adapters are active.</td>
    </tr>
    <tr>
      <td><code>validate_rebalance_plan(plan: PortfolioRebalancePlan) -> RebalancePlanResult</code></td>
      <td>Verify targets and current positions.</td>
    </tr>
    <tr>
      <td><code>validate_order_intent(intent: OrderIntent) -> OrderIntentResult</code></td>
      <td>Ensure orders satisfy strategy constraints.</td>
    </tr>
    <tr>
      <td>routing.py</td>
      <td><code>dispatch_order(order: OrderIntent) -> ExecutionReceipt</code></td>
      <td>Direct validated orders to MT5 or cTrader adapters.</td>
    </tr>
    <tr>
      <td rowspan="2">reconciliation.py</td>
      <td><code>compare_order_states(client_order: OrderIntent, broker_order: BrokerOrder) -> ReconciliationResult</code></td>
      <td>Match gateway intents with broker confirmations.</td>
    </tr>
    <tr>
      <td><code>retry_failed_order(order_id: str) -> ExecutionReceipt</code></td>
      <td>Re-dispatch orders using idempotency keys.</td>
    </tr>
    <tr>
      <td rowspan="3">monitoring.py</td>
      <td><code>get_portfolio_exposure() -> PortfolioExposure</code></td>
      <td>Calculate net positions, leverage, and margin.</td>
    </tr>
    <tr>
      <td><code>get_risk_budget_status() -> BudgetStatus</code></td>
      <td>Reconcile active risk utilization.</td>
    </tr>
    <tr>
      <td><code>report_operational_incident(event: OperationalEvent) -> None</code></td>
      <td>Log connection losses or hard-kills.</td>
    </tr>
    <tr>
      <td rowspan="2">live.py</td>
      <td><code>TradingSession.start() -> None</code></td>
      <td>Initialize connection adapters and start trading execution loop.</td>
    </tr>
    <tr>
      <td><code>TradingSession.stop() -> None</code></td>
      <td>Disconnect feeds and halt session loops.</td>
    </tr>
    <tr>
      <td rowspan="4">actions.py</td>
      <td><code>submit_order(intent: OrderIntent) -> ExecutionReceipt</code></td>
      <td>Submit order request.</td>
    </tr>
    <tr>
      <td><code>cancel_order(order_id: str) -> ExecutionReceipt</code></td>
      <td>Cancel active working order.</td>
    </tr>
    <tr>
      <td><code>close_position(position_id: str) -> ExecutionReceipt</code></td>
      <td>Close position.</td>
    </tr>
    <tr>
      <td><code>close_all_positions() -> tuple[ExecutionReceipt, ...]</code></td>
      <td>Close all positions.</td>
    </tr>
    <tr>
      <td>reporting.py</td>
      <td><code>build_execution_evidence(receipt: ExecutionReceipt) -> ExecutionEvidence</code></td>
      <td>Assemble execution reports.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>8. Analytics (<code>app/services/analytics/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>performance.py</td>
      <td><code>calculate_performance_metrics(trades: Sequence[TradeRecord], equity_curve: Sequence[Decimal]) -> PerformanceMetrics</code></td>
      <td>Calculate Sharpe, Sortino, CAGR, and drawdowns.</td>
    </tr>
    <tr>
      <td>portfolio.py</td>
      <td><code>calculate_portfolio_attribution(portfolio: ActivePortfolioAllocation, components: Mapping[str, PerformanceMetrics]) -> PortfolioAttribution</code></td>
      <td>Allocate performance and risk metrics to component strategies.</td>
    </tr>
    <tr>
      <td>benchmarks.py</td>
      <td><code>compare_to_benchmark(portfolio: ActivePortfolioAllocation, benchmark: Sequence[Decimal]) -> BenchmarkComparison</code></td>
      <td>Reconcile alpha, beta, and tracking error.</td>
    </tr>
    <tr>
      <td rowspan="2">statistics.py</td>
      <td><code>calculate_drawdown_profile(equity_curve: Sequence[Decimal]) -> DrawdownProfile</code></td>
      <td>Compute peak-to-trough drops.</td>
    </tr>
    <tr>
      <td><code>calculate_streak_statistics(trades: Sequence[TradeRecord]) -> StreakStatistics</code></td>
      <td>Quantify consecutive win/loss patterns.</td>
    </tr>
    <tr>
      <td>reporting.py</td>
      <td><code>build_dashboard_report(performance: PerformanceMetrics, attribution: PortfolioAttribution) -> dict[str, object]</code></td>
      <td>Compile chart-ready datasets.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>9. Simulator (<code>app/services/simulator/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2">run.py</td>
      <td><code>run_backtest(request: SimulationBacktestRequestV1) -> SimulationResult</code></td>
      <td>Run a deterministic, canonical backtest.</td>
    </tr>
    <tr>
      <td><code>run_fast_research(request: SimulationBacktestRequestV1) -> SimulationResult</code></td>
      <td>Run an isolated, non-canonical bar-based backtest approximation.</td>
    </tr>
    <tr>
      <td rowspan="3">validation.py</td>
      <td><code>validate_run_inputs(request: SimulationBacktestRequestV1) -> None</code></td>
      <td>Validate request schema bounds.</td>
    </tr>
    <tr>
      <td><code>validate_market_data(data: MarketDataset) -> None</code></td>
      <td>Validate OHLC and spread data quality.</td>
    </tr>
    <tr>
      <td><code>validate_phase_one_scope(request: SimulationBacktestRequestV1) -> None</code></td>
      <td>Ensure requests fit Phase 1 constraints.</td>
    </tr>
    <tr>
      <td rowspan="2">timeline.py</td>
      <td><code>build_tick_timeline(bars: Sequence[BarRecord]) -> tuple[TickRecord, ...]</code></td>
      <td>Combine bars or ticks into ordered timeline.</td>
    </tr>
    <tr>
      <td><code>validate_intent_timing(intent: OrderIntent, tick_time: datetime) -> None</code></td>
      <td>Prevent lookahead bias.</td>
    </tr>
    <tr>
      <td rowspan="4">accounting.py</td>
      <td><code>normalize_volume(volume: Decimal, symbol: str) -> Decimal</code></td>
      <td>Quantize volume to contract rules.</td>
    </tr>
    <tr>
      <td><code>calculate_execution_costs(fill: BrokerDeal) -> Decimal</code></td>
      <td>Calculate execution fees.</td>
    </tr>
    <tr>
      <td><code>calculate_margin(position: BrokerPosition) -> Decimal</code></td>
      <td>Calculate margin capacity.</td>
    </tr>
    <tr>
      <td><code>validate_fx_evidence(rates: FXConversionEvidence) -> None</code></td>
      <td>Reconcile currency rates.</td>
    </tr>
    <tr>
      <td rowspan="2">journal.py</td>
      <td><code>replay_journal(events_stream: Iterator[str]) -> tuple[SimulationEvent, ...]</code></td>
      <td>Reconstruct state from event logs.</td>
    </tr>
    <tr>
      <td><code>resolve_idempotent_run(request_hash: str) -> SimulationResult | None</code></td>
      <td>Match hashes to avoid duplicate runs.</td>
    </tr>
    <tr>
      <td rowspan="2">execution.py</td>
      <td><code>price_order(order: OrderIntent, tick: TickRecord) -> Decimal</code></td>
      <td>Compute execution price.</td>
    </tr>
    <tr>
      <td><code>match_order(order: OrderIntent, tick: TickRecord) -> BrokerDeal | None</code></td>
      <td>Match orders on tick events.</td>
    </tr>
    <tr>
      <td rowspan="3">reporting.py</td>
      <td><code>build_artifact_manifest(directory: Path) -> dict[str, object]</code></td>
      <td>Scan and checksum run outputs.</td>
    </tr>
    <tr>
      <td><code>build_json_report(result: SimulationResult) -> str</code></td>
      <td>Format run outputs as JSON.</td>
    </tr>
    <tr>
      <td><code>build_markdown_report(result: SimulationResult) -> str</code></td>
      <td>Render human-readable summaries.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>10. Optimization (<code>app/services/optimization/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="10">public_api.py</td>
      <td><code>run_parameter_sweep(request: SearchRequest) -> OptimizationResult</code></td>
      <td>Run parameter sweeps.</td>
    </tr>
    <tr>
      <td><code>run_walk_forward_optimization(request: WalkForwardRequest) -> OptimizationResult</code></td>
      <td>Execute walk-forward validation.</td>
    </tr>
    <tr>
      <td><code>run_walk_forward_matrix(requests: Sequence[WalkForwardRequest]) -> tuple[OptimizationResult, ...]</code></td>
      <td>Run multiple walk-forward matrices.</td>
    </tr>
    <tr>
      <td><code>run_robustness_analysis(request: RobustnessRequest) -> RobustnessResult</code></td>
      <td>Run Monte Carlo/stress tests.</td>
    </tr>
    <tr>
      <td><code>compare_optimization_runs(results: Sequence[OptimizationResult]) -> ComparisonResult</code></td>
      <td>Compare run metrics.</td>
    </tr>
    <tr>
      <td><code>calculate_parameter_stability(candidates: Sequence[Mapping[str, object]]) -> StabilityResult</code></td>
      <td>Evaluate parameter stability metrics.</td>
    </tr>
    <tr>
      <td><code>detect_overfit_parameters(is_evidence: Mapping[str, object], oos_evidence: Mapping[str, object]) -> OverfitResult</code></td>
      <td>Detect overfitting in training/OOS.</td>
    </tr>
    <tr>
      <td><code>rank_parameter_sets(candidates: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]</code></td>
      <td>Sort candidates.</td>
    </tr>
    <tr>
      <td><code>calculate_robustness_score(checks: Sequence[Mapping[str, object]]) -> float</code></td>
      <td>Compute robustness score.</td>
    </tr>
    <tr>
      <td><code>build_optimization_handoff(request: EvidenceAssemblyRequest) -> OptimizationResult</code></td>
      <td>Pack result envelope.</td>
    </tr>
    <tr>
      <td rowspan="2">parameters.py</td>
      <td><code>validate_parameter_space(space: Mapping[str, object]) -> None</code></td>
      <td>Verify space definitions.</td>
    </tr>
    <tr>
      <td><code>compute_space_provenance(space: Mapping[str, object]) -> str</code></td>
      <td>Hash space settings.</td>
    </tr>
    <tr>
      <td rowspan="5">scoring.py</td>
      <td><code>calculate_candidate_score(metrics: PerformanceReport, objective: str) -> float</code></td>
      <td>Compute candidate score.</td>
    </tr>
    <tr>
      <td><code>rank_candidates(candidates: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]</code></td>
      <td>Rank candidates.</td>
    </tr>
    <tr>
      <td><code>calculate_deflated_sharpe(sharpe: float, trials: int, variance: float) -> float</code></td>
      <td>Compute Deflated Sharpe Ratio.</td>
    </tr>
    <tr>
      <td><code>count_nominal_trials(space: Mapping[str, object]) -> int</code></td>
      <td>Compute nominal trials count.</td>
    </tr>
    <tr>
      <td><code>assess_overfit_evidence(is_metrics: PerformanceReport, oos_metrics: PerformanceReport) -> dict[str, object]</code></td>
      <td>Compare IS/OOS metrics.</td>
    </tr>
    <tr>
      <td>execution.py</td>
      <td><code>execute_candidate(candidate: Mapping[str, object]) -> SimulationResult</code></td>
      <td>Run candidates via Simulation.</td>
    </tr>
    <tr>
      <td rowspan="3">search.py</td>
      <td><code>iter_grid_candidates(space: Mapping[str, object]) -> Iterator[Mapping[str, object]]</code></td>
      <td>Generate grid options.</td>
    </tr>
    <tr>
      <td><code>sample_random_candidates(space: Mapping[str, object], size: int) -> Iterator[Mapping[str, object]]</code></td>
      <td>Generate random options.</td>
    </tr>
    <tr>
      <td><code>run_bounded_search(space: Mapping[str, object]) -> SearchSummary</code></td>
      <td>Run search sweep.</td>
    </tr>
    <tr>
      <td rowspan="2">validation.py</td>
      <td><code>build_time_series_splits(data: MarketDataset, folds: int) -> Sequence[TimeSplitResult]</code></td>
      <td>Construct training/OOS folds.</td>
    </tr>
    <tr>
      <td><code>run_walk_forward_validation(request: WalkForwardRequest) -> WalkForwardResult</code></td>
      <td>Coordinate walk-forward testing.</td>
    </tr>
    <tr>
      <td rowspan="3">robustness.py</td>
      <td><code>run_monte_carlo(trades: Sequence[TradeRecord], runs: int) -> MonteCarloResult</code></td>
      <td>Run shuffling bootstrap.</td>
    </tr>
    <tr>
      <td><code>apply_execution_cost_stress(trades: Sequence[TradeRecord], stress_factor: float) -> Sequence[TradeRecord]</code></td>
      <td>Apply slippage/spread stress.</td>
    </tr>
    <tr>
      <td><code>assess_strategy_robustness(monte_carlo: MonteCarloResult, stress_checks: Sequence[Mapping[str, object]]) -> dict[str, object]</code></td>
      <td>Compile robustness checks.</td>
    </tr>
    <tr>
      <td rowspan="2">evidence.py</td>
      <td><code>build_optimization_evidence(request: EvidenceAssemblyRequest) -> OptimizationResult</code></td>
      <td>Assemble candidate results.</td>
    </tr>
    <tr>
      <td><code>build_report_package(result: OptimizationResult) -> dict[str, object]</code></td>
      <td>Format report dictionaries.</td>
    </tr>
    <tr>
      <td rowspan="5">state.py</td>
      <td><code>save_search_checkpoint(checkpoint: OptimizationCheckpoint) -> None</code></td>
      <td>Save active checkpoint.</td>
    </tr>
    <tr>
      <td><code>load_search_checkpoint(search_id: str) -> OptimizationCheckpoint</code></td>
      <td>Restore last checkpoint.</td>
    </tr>
    <tr>
      <td><code>persist_optimization_result(result: OptimizationResult) -> OptimizationPersistenceReceipt</code></td>
      <td>Atomic result persistence.</td>
    </tr>
    <tr>
      <td><code>build_optimization_artifact_path(search_id: str) -> Path</code></td>
      <td>Build target artifact path.</td>
    </tr>
    <tr>
      <td><code>get_optimization_migrations() -> tuple[MigrationDefinition, ...]</code></td>
      <td>Expose database migrations.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>11. Portfolio (<code>app/services/portfolio/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function / Method</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2">evidence.py</td>
      <td><code>validate_construction_evidence(request: PortfolioConstructionRequest) -> None</code></td>
      <td>Validate strategies and FX rates.</td>
    </tr>
    <tr>
      <td><code>revalidate_activation_evidence(allocation: ActivePortfolioAllocation) -> None</code></td>
      <td>Check gates prior to activation.</td>
    </tr>
    <tr>
      <td rowspan="3">construction.py</td>
      <td><code>fixed_weights(components: Sequence[str], weights: Sequence[Decimal]) -> Mapping[str, Decimal]</code></td>
      <td>Calculate fixed weights.</td>
    </tr>
    <tr>
      <td><code>equal_weights(components: Sequence[str]) -> Mapping[str, Decimal]</code></td>
      <td>Calculate equal weights.</td>
    </tr>
    <tr>
      <td><code>inverse_volatility_weights(components: Sequence[str], volatilities: Sequence[Decimal]) -> Mapping[str, Decimal]</code></td>
      <td>Calculate inverse-volatility weights.</td>
    </tr>
    <tr>
      <td rowspan="7">api.py</td>
      <td><code>PortfolioService.construct(request: PortfolioConstructionRequest, auth_context: AuthContext) -> PortfolioConstructionResult</code></td>
      <td>Construct candidate allocations.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.status(scope: str, auth_context: AuthContext) -> ActivePortfolioAllocation</code></td>
      <td>Inspect active allocations.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.activate(result: PortfolioConstructionResult, auth_context: AuthContext) -> ActivePortfolioAllocation</code></td>
      <td>Activate target allocations.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.assess_drift(allocation: ActivePortfolioAllocation, auth_context: AuthContext) -> PortfolioRebalancePlan</code></td>
      <td>Reconcile active weights.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.plan_rebalance(plan: PortfolioRebalancePlan, auth_context: AuthContext) -> PortfolioRebalancePlan</code></td>
      <td>Generate rebalance trades.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.rollback(target_version: str, auth_context: AuthContext) -> ActivePortfolioAllocation</code></td>
      <td>Rollback active allocations.</td>
    </tr>
    <tr>
      <td><code>PortfolioService.history(scope: str, auth_context: AuthContext) -> Sequence[ActivePortfolioAllocation]</code></td>
      <td>Read allocation history.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>12. Research (<code>app/services/research/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4">data.py</td>
      <td><code>validate_dataset(dataset: MarketDataset) -> DataQualityReport</code></td>
      <td>Check dataset quality.</td>
    </tr>
    <tr>
      <td><code>clean_dataset(dataset: MarketDataset, config: CleaningConfig) -> DataFrame</code></td>
      <td>Clean data copies.</td>
    </tr>
    <tr>
      <td><code>enrich_dataset(data: DataFrame, config: EnrichmentConfig) -> DataFrame</code></td>
      <td>Add returns/geometry.</td>
    </tr>
    <tr>
      <td><code>prepare_research_dataset(dataset: MarketDataset, config: CleaningConfig, enrichment: EnrichmentConfig) -> PreparedDataset</code></td>
      <td>Prepare research data.</td>
    </tr>
    <tr>
      <td rowspan="5">features.py</td>
      <td><code>calculate_returns(prices: Series) -> Series</code></td>
      <td>Calculate returns series.</td>
    </tr>
    <tr>
      <td><code>calculate_hurst(prices: Series) -> float</code></td>
      <td>Compute Hurst exponents.</td>
    </tr>
    <tr>
      <td><code>calculate_forward_returns(prices: Series, horizons: Sequence[int]) -> DataFrame</code></td>
      <td>Calculate forward returns.</td>
    </tr>
    <tr>
      <td><code>calculate_excursions(highs: Series, lows: Series, closes: Series) -> DataFrame</code></td>
      <td>Compute excursions.</td>
    </tr>
    <tr>
      <td><code>assemble_feature_frame(data: DataFrame, config: FeatureConfig) -> DataFrame</code></td>
      <td>Assemble feature matrix.</td>
    </tr>
    <tr>
      <td rowspan="6">leakage.py</td>
      <td><code>validate_leakage(features: DataFrame, allowed_forward: Sequence[str]) -> LeakageReport</code></td>
      <td>Detect lookahead leakage.</td>
    </tr>
    <tr>
      <td><code>validate_features(features: DataFrame) -> None</code></td>
      <td>Validate feature matrices.</td>
    </tr>
    <tr>
      <td><code>split_chronological(features: DataFrame, train_ratio: float) -> TimeSplitResult</code></td>
      <td>Run chronological splits.</td>
    </tr>
    <tr>
      <td><code>build_time_splits(features: DataFrame, config: FeatureConfig) -> TimeSplitResult</code></td>
      <td>Build train/validation/test folds.</td>
    </tr>
    <tr>
      <td><code>apply_embargo(splits: TimeSplitResult, embargo_seconds: int) -> TimeSplitResult</code></td>
      <td>Discard overlapping OOS logs.</td>
    </tr>
    <tr>
      <td><code>mask_recursive(payload: Mapping[str, Any]) -> Mapping[str, Any]</code></td>
      <td>Mask nested payload structures.</td>
    </tr>
    <tr>
      <td rowspan="8">metrics.py</td>
      <td><code>build_metric_registry() -> MetricRegistry</code></td>
      <td>Expose metric calculators.</td>
    </tr>
    <tr>
      <td><code>calculate_returns_distribution(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute returns profile.</td>
    </tr>
    <tr>
      <td><code>calculate_streak_distribution(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute streak profile.</td>
    </tr>
    <tr>
      <td><code>calculate_drawdown_distribution(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute drawdown profile.</td>
    </tr>
    <tr>
      <td><code>calculate_volatility_profile(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute volatility profile.</td>
    </tr>
    <tr>
      <td><code>calculate_seasonality_profile(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute seasonality profile.</td>
    </tr>
    <tr>
      <td><code>calculate_structure_metrics(prices: Series) -> Mapping[str, float]</code></td>
      <td>Compute structure profile.</td>
    </tr>
    <tr>
      <td><code>build_core_metric_profile(dataset: PreparedDataset, config: EdgeLabConfig) -> CoreMetricProfile</code></td>
      <td>Build core metric profiles.</td>
    </tr>
    <tr>
      <td rowspan="5">statistics.py</td>
      <td><code>run_eds_bootstrap(data: Series, samples: int) -> tuple[Series, ...]</code></td>
      <td>Run bootstrap resamples.</td>
    </tr>
    <tr>
      <td><code>run_eds_permutation(data: Series, samples: int) -> tuple[Series, ...]</code></td>
      <td>Run permutation tests.</td>
    </tr>
    <tr>
      <td><code>build_null_model(data: Series) -> Series</code></td>
      <td>Build null models.</td>
    </tr>
    <tr>
      <td><code>apply_bonferroni(p_values: Sequence[float]) -> tuple[float, ...]</code></td>
      <td>Apply Bonferroni correction.</td>
    </tr>
    <tr>
      <td><code>apply_fdr_bh(p_values: Sequence[float]) -> tuple[float, ...]</code></td>
      <td>Apply FDR BH correction.</td>
    </tr>
    <tr>
      <td rowspan="14">studies.py</td>
      <td><code>run_eds_null_baseline(study: str, config: StudyConfig) -> Mapping[str, float]</code></td>
      <td>Generate baseline null models.</td>
    </tr>
    <tr>
      <td><code>compare_to_null(observed: float, null_dist: Sequence[float]) -> float</code></td>
      <td>Check observed against null.</td>
    </tr>
    <tr>
      <td><code>get_acceptance_criteria(alpha: float) -> float</code></td>
      <td>Compute alpha thresholds.</td>
    </tr>
    <tr>
      <td><code>run_mean_reversion_study(features: DataFrame, config: StudyConfig) -> EdgeResult</code></td>
      <td>Run mean reversion study.</td>
    </tr>
    <tr>
      <td><code>run_trend_persistence_study(features: DataFrame, config: StudyConfig) -> EdgeResult</code></td>
      <td>Run trend persistence study.</td>
    </tr>
    <tr>
      <td><code>run_session_edge_study(features: DataFrame, config: StudyConfig) -> EdgeResult</code></td>
      <td>Run session edge study.</td>
    </tr>
    <tr>
      <td><code>evaluate_run_significance(observed: float, null_baseline: Mapping[str, float]) -> float</code></td>
      <td>Calculate edge p-values.</td>
    </tr>
    <tr>
      <td><code>calculate_hurst_bootstrap(prices: Series, samples: int) -> tuple[float, float]</code></td>
      <td>Compute Hurst bootstrap.</td>
    </tr>
    <tr>
      <td><code>calculate_streak_bootstrap(prices: Series, samples: int) -> tuple[float, float]</code></td>
      <td>Compute streak bootstrap.</td>
    </tr>
    <tr>
      <td><code>calculate_excursion_bootstrap(highs: Series, lows: Series, closes: Series, samples: int) -> tuple[float, float]</code></td>
      <td>Compute excursion bootstrap.</td>
    </tr>
    <tr>
      <td><code>run_edge_studies_sweep(features: DataFrame, sweep_config: Mapping[str, object]) -> Sequence[EdgeResult]</code></td>
      <td>Sweep multiple edge configurations.</td>
    </tr>
    <tr>
      <td><code>verify_isolated_study_failures(results: Sequence[EdgeResult]) -> None</code></td>
      <td>Verify and handle failures.</td>
    </tr>
    <tr>
      <td><code>classify_edge(metrics: Mapping[str, float]) -> str</code></td>
      <td>Classify edge results.</td>
    </tr>
    <tr>
      <td><code>confirm_edge(result: EdgeResult, criteria: float) -> bool</code></td>
      <td>Assess edge confidence.</td>
    </tr>
    <tr>
      <td rowspan="6">seasonality.py</td>
      <td><code>tag_session_timezone(data: DataFrame, config: SessionConfig) -> DataFrame</code></td>
      <td>Tag dataset sessions.</td>
    </tr>
    <tr>
      <td><code>get_session_hours(session: str) -> tuple[time, time]</code></td>
      <td>Get session hour boundaries.</td>
    </tr>
    <tr>
      <td><code>analyze_intraday_returns(data: DataFrame) -> Mapping[str, float]</code></td>
      <td>Analyze intraday patterns.</td>
    </tr>
    <tr>
      <td><code>analyze_day_of_week(data: DataFrame) -> Mapping[str, float]</code></td>
      <td>Analyze weekday patterns.</td>
    </tr>
    <tr>
      <td><code>analyze_month_of_year(data: DataFrame) -> Mapping[str, float]</code></td>
      <td>Analyze monthly patterns.</td>
    </tr>
    <tr>
      <td><code>run_seasonality_analysis(data: DataFrame, config: SessionConfig) -> Mapping[str, float]</code></td>
      <td>Run seasonality analysis.</td>
    </tr>
    <tr>
      <td rowspan="6">market_structure.py</td>
      <td><code>detect_structure_legs(prices: Series) -> DataFrame</code></td>
      <td>Detect structural high/low legs.</td>
    </tr>
    <tr>
      <td><code>build_market_structure_profile(dataset: PreparedDataset, config: MarketStructureConfig) -> MarketStructureProfile</code></td>
      <td>Compile structural profiles.</td>
    </tr>
    <tr>
      <td><code>evaluate_structure_stability(profile: MarketStructureProfile) -> MarketStructureQualityReport</code></td>
      <td>Assess structure stability.</td>
    </tr>
    <tr>
      <td><code>validate_market_structure(profile: MarketStructureProfile) -> None</code></td>
      <td>Validate structural regimes.</td>
    </tr>
    <tr>
      <td><code>calibrate_market_structure(profile: MarketStructureProfile) -> MarketStructureProfile</code></td>
      <td>Calibrate regime parameters.</td>
    </tr>
    <tr>
      <td><code>evaluate_strategy_fit(profile: MarketStructureProfile, strategy_id: str) -> Mapping[str, float]</code></td>
      <td>Assess suitability scores.</td>
    </tr>
    <tr>
      <td rowspan="7">modeling.py</td>
      <td><code>decompose_pca(features: DataFrame, components: int) -> Mapping[str, Any]</code></td>
      <td>Compute PCA components.</td>
    </tr>
    <tr>
      <td><code>cluster_kmeans(features: DataFrame, clusters: int) -> Series</code></td>
      <td>Compute K-Means clusters.</td>
    </tr>
    <tr>
      <td><code>generate_cluster_insights(features: DataFrame, labels: Series) -> Mapping[str, Any]</code></td>
      <td>Generate cluster summaries.</td>
    </tr>
    <tr>
      <td><code>identify_pca_risk_factors(pca: Mapping[str, Any], top_count: int) -> tuple[Mapping[str, Any], ...]</code></td>
      <td>Extract PCA absolute factor weights.</td>
    </tr>
    <tr>
      <td><code>analyze_cluster_outperformance(data: DataFrame, labels: Series, horizon: int) -> tuple[Mapping[str, Any], ...]</code></td>
      <td>Compare cluster forward returns.</td>
    </tr>
    <tr>
      <td><code>build_unsupervised_insight_report(features: DataFrame, config: UnsupervisedResearchConfig) -> Mapping[str, Any]</code></td>
      <td>Build unsupervised insight reports.</td>
    </tr>
    <tr>
      <td><code>run_unsupervised_research(features: DataFrame, config: UnsupervisedResearchConfig, limits: ResearchResourceLimits) -> UnsupervisedResearchResult</code></td>
      <td>Run unsupervised modeling workflow.</td>
    </tr>
    <tr>
      <td rowspan="8">profiles.py</td>
      <td><code>build_research_scorecard(metric_profile: CoreMetricProfile, seasonality: Mapping[str, Any] | None, edges: Sequence[EdgeResult], market_structure: MarketStructureProfile | None, modeling: UnsupervisedResearchResult | None, performance: PerformanceReport | None = None) -> ResearchScorecard</code></td>
      <td>Score structural evidence metrics.</td>
    </tr>
    <tr>
      <td><code>build_research_profile_snapshot(stages: Mapping[str, Any], scorecard: ResearchScorecard, dataset_hash: str, configuration_hash: str) -> ResearchProfileSnapshot</code></td>
      <td>Compile stage records.</td>
    </tr>
    <tr>
      <td><code>build_profile_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, Any]</code></td>
      <td>Summarize snapshot profiles.</td>
    </tr>
    <tr>
      <td><code>build_dashboard_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, Any]</code></td>
      <td>Format snapshot dashboard parameters.</td>
    </tr>
    <tr>
      <td><code>render_research_report(report: ResearchReport, format: str) -> str</code></td>
      <td>Render snapshot reports.</td>
    </tr>
    <tr>
      <td><code>render_profile_comparison(left: ResearchProfileSnapshot, right: ResearchProfileSnapshot) -> str</code></td>
      <td>Render diff comparison reports.</td>
    </tr>
    <tr>
      <td><code>generate_multi_symbol_report(reports: Mapping[str, ResearchReport], format: str) -> str</code></td>
      <td>Render multi-report summaries.</td>
    </tr>
    <tr>
      <td><code>run_edge_lab_profile(dataset: MarketDataset, config: EdgeLabConfig, performance: PerformanceReport | None = None) -> ResearchReport</code></td>
      <td>Orchestrate complete edge lab run.</td>
    </tr>
    <tr>
      <td>artifacts.py</td>
      <td><code>write_research_artifact(report: ResearchReport, config: ArtifactWriteConfig) -> ArtifactReference</code></td>
      <td>Persist report artifact.</td>
    </tr>
  </tbody>
</table>

<br/>

<h3>13. API (<code>app/services/api/</code>)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 15%;">File</th>
      <th style="width: 50%;">Function</th>
      <th style="width: 35%;">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2">composition.py</td>
      <td><code>create_app(settings: RuntimeSettings) -> FastAPI</code></td>
      <td>Initialize the FastAPI gateway application.</td>
    </tr>
    <tr>
      <td><code>build_broker_connection_config(credentials: Mapping[str, Any]) -> BrokerConnectionConfig</code></td>
      <td>Construct connection configs from credentials.</td>
    </tr>
    <tr>
      <td rowspan="11">identity.py</td>
      <td><code>hash_password(password: str) -> str</code></td>
      <td>Hash passwords.</td>
    </tr>
    <tr>
      <td><code>verify_password(password: str, hashed: str) -> bool</code></td>
      <td>Verify password hashes.</td>
    </tr>
    <tr>
      <td><code>store_credential(ref: str, payload: Mapping[str, Any]) -> CredentialRecord</code></td>
      <td>Encrypt and store broker credentials.</td>
    </tr>
    <tr>
      <td><code>resolve_credential_reference(ref: str) -> Mapping[str, Any]</code></td>
      <td>Decrypt credentials.</td>
    </tr>
    <tr>
      <td><code>authenticate_user(username: str, password: str) -> AuthenticatedUser</code></td>
      <td>Authenticate user credentials.</td>
    </tr>
    <tr>
      <td><code>create_session(user: AuthenticatedUser) -> SessionCredential</code></td>
      <td>Establish secure sessions.</td>
    </tr>
    <tr>
      <td><code>validate_session(credential: SessionCredential) -> AuthenticatedPrincipal</code></td>
      <td>Verify session validity and permissions.</td>
    </tr>
    <tr>
      <td><code>revoke_session(credential: SessionCredential) -> None</code></td>
      <td>Invalidate session tokens.</td>
    </tr>
    <tr>
      <td><code>build_auth_context(principal: AuthenticatedPrincipal, trace: TraceContext) -> AuthContext</code></td>
      <td>Translate user claims to AuthContext.</td>
    </tr>
    <tr>
      <td><code>require_permission(context: AuthContext, permission: str) -> None</code></td>
      <td>Enforce permission limits.</td>
    </tr>
    <tr>
      <td><code>validate_governed_request(context: AuthContext, governed: GovernedRequestContext) -> None</code></td>
      <td>Enforce governed action limits.</td>
    </tr>
    <tr>
      <td rowspan="2">health.py</td>
      <td><code>get_liveness() -> ApiResponse[Liveness]</code></td>
      <td>Probe process liveness.</td>
    </tr>
    <tr>
      <td><code>get_readiness(context: AuthContext) -> ApiResponse[Readiness]</code></td>
      <td>Probe process readiness.</td>
    </tr>
    <tr>
      <td>streams.py</td>
      <td><code>build_stream_event(event: OwnerEvent, trace: TraceContext) -> StreamEvent[Any]</code></td>
      <td>Format domain events for stream wrappers.</td>
    </tr>
  </tbody>
</table>
