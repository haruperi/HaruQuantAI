## FEAT-STR-01: Deterministic strategy lifecycle, common SQX handling, and intent helpers (app.services.strategy.base)

| Function | Purpose |
|----------|---------|
| `SignalDict` (model) | Signal dictionary structure. |
| `StrategyEvent` (model) | Canonical strategy lifecycle/event payload. |
| `SignalIntent` (model) | Canonical strategy signal intent passed to routing/execution boundaries. |
| `BaseStrategy.__init__(params: dict[str, Any] \| None = None) -> None` | Initialize strategy. |
| `BaseStrategy.on_init() -> None` | Initialize strategy (optional). |
| `BaseStrategy.on_tick(data: pd.DataFrame) -> pd.DataFrame` | Process tick data (optional). |
| `BaseStrategy.on_trade(event: StrategyEvent) -> None` | Handle trade lifecycle events when an engine provides them. |
| `BaseStrategy.on_order_update(intent_id: str, broker_order_id: str, status: str) -> None` | Persist non-authoritative execution correlation for observability. |
| `BaseStrategy.on_timer(event: StrategyEvent) -> None` | Handle timer events when an engine provides them. |
| `BaseStrategy.on_shutdown(event: StrategyEvent \| None = None) -> None` | Handle strategy shutdown when an engine provides a shutdown event. |
| `BaseStrategy.on_bar(data: pd.DataFrame) -> pd.DataFrame` | Calculate indicators and add signal columns. |
| `BaseStrategy.get_signal(data: pd.DataFrame, index: int) -> SignalDict \| None` | Get signal details for a specific bar. |
| `BaseStrategy.get_indicator_value(data: pd.DataFrame, column: str, offset: int = 0) -> float \| None` | Get indicator value from data. |
| `BaseStrategy.crossover(series1: pd.Series, series2: pd.Series) -> bool` | Detect bullish crossover where series1 crosses above series2. |
| `BaseStrategy.crossunder(series1: pd.Series, series2: pd.Series) -> bool` | Detect bearish crossunder where series1 crosses below series2. |
| `StrategyPermissionError` (exception) | Raised when a strategy is evaluated in an unpermitted environment. |
| `BaseStrategy.evaluate(context: MarketContext) -> StrategyDecision` | Evaluate the latest completed main-chart bar exactly once. |
| `BaseStrategy.evaluate_execution_event(context: MarketContext, event_id: str) -> StrategyDecision` | Respond once to an execution event, for strategies with order ladders. |
| `BaseStrategy.required_warmup_bars -> int (property)` | Return the configured number of complete bars needed before evaluation. |
| `BaseStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate the signals in a vectorized way on the input DataFrame. |
| `BaseStrategy.precalculate_signals(context: MarketContext) -> None` | Precalculate and cache signals in a vectorized way from context bars. |
| `BaseStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | Optionally replace standard signal/action resolution for complex EAs. |
| `BaseStrategy.build_execution_event_intents(context: MarketContext, event_id: str) -> Sequence[TradeIntent]` | Optionally react to a reconciled broker fill/cancel/update event. |
| `BaseStrategy.build_protection_request(context: MarketContext, direction: Direction) -> ProtectionRequest` | Return strategy-proposed protection for the standard entry action. |


## FEAT-STR-02: JSON strategy configuration loading and deterministic validation (app.services.strategy.config)

| Function | Purpose |
|----------|---------|
| `ConfigurationError` (exception) | Raised when a strategy configuration violates the canonical contract. |
| `StrategyConfig.strategy_id -> str (property)` | Validated wrapper around a deep-copied canonical JSON object. |
| `StrategyConfig.version -> str (property)` | Validated wrapper around a deep-copied canonical JSON object. |
| `StrategyConfig.permitted_environments -> frozenset[str] (property)` | Validated wrapper around a deep-copied canonical JSON object. |
| `StrategyConfig.section(name: str) -> Mapping[str, Any]` | Return a named configuration section. |
| `StrategyConfig.parameter(name: str) -> Any` | Return active parameter value, falling back to the declared default. |
| `StrategyConfig.option(*path: str, default: Any = None) -> Any` | Read an optional nested value under trading_options. |
| `load_strategy_config(path: str \| Path) -> StrategyConfig` | Load and validate a UTF-8 JSON strategy config from disk. |
| `validate_strategy_config(value: Mapping[str, Any]) -> StrategyConfig` | Validate canonical strategy config without a third-party runtime dependency. |


## FEAT-STR-03: Strategies contracts module (app.services.strategy.contracts)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `StrategyInput.validate_boundary_times(v: str) -> str` | Validate and normalize evaluation window boundary timestamps. |
| `StrategySignal.validate_symbol_non_empty(v: str) -> str` | Reject empty or whitespace-only symbol strings. |
| `StrategySignal.validate_signal_integrity() -> StrategySignal` | Validate evidence references and reject expired signals. |
| `RuntimeMode` (enum) | Permitted execution environments for strategy evaluation. |
| `Direction` (enum) | Trade direction. |
| `IntentAction` (enum) | Broker-neutral proposal action. |
| `EntryType` (enum) | Order-entry classification independent of a particular broker API. |
| `Bar` (dataclass) | A completed canonical OHLCV bar. |
| `QuoteSnapshot.entry_price(direction: Direction) -> float` | Return the natural executable market-entry price for a direction. |
| `QuoteSnapshot.exit_price(direction: Direction) -> float` | Return the natural executable market-exit price for a position. |
| `AccountSnapshot` (dataclass) | Minimal account data needed for strategy-side sizing formulas. |
| `PositionSnapshot` (dataclass) | Read-only view of an open broker/portfolio position. |
| `PendingOrderSnapshot` (dataclass) | Read-only view of a broker pending order. |
| `MarketContext.signal_bar -> Bar (property)` | Return the latest completed main-chart bar. |
| `MarketContext.bars_for_chart(chart_name: str = "main") -> Sequence[Bar]` | Return main or named secondary-chart bars. |
| `ProtectionRequest` (dataclass) | Strategy-proposed protection and management changes. |
| `TradeIntent` (dataclass) | Idempotent broker-neutral request for Risk Governor and execution review. |
| `SignalSet` (dataclass) | The four canonical SQX-style boolean signal outputs. |
| `StrategyDecision` (dataclass) | Complete deterministic result of a strategy evaluation. |


## FEAT-STR-04: Deterministic error-code mapping for the strategy service boundary (app.services.strategy.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `to_strategy_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Strategy error payload. |
| `StrategyError` (exception) | Base error type for all strategy calculations and registry operations. |
| `StrategyConfigError` (exception) | Raised when strategy configuration fails schema validation. |
| `StrategyNotFoundError` (exception) | Raised when an unrecognized strategy ID is requested. |
| `StrategyVersionConstraintUnsatisfiableError` (exception) | Raised when no matching version fits the constraint. |
| `StrategyDeprecatedError` (exception) | Raised when strategy is deprecated and cannot be run. |
| `StrategyUnapprovedModuleError` (exception) | Raised when module resolution points to an unapproved file path. |
| `StrategySchemaValidationFailedError` (exception) | Raised when config JSON schema fails validation. |
| `StrategyUnsupportedTimingPolicyError` (exception) | Raised when timing policy is unsupported. |
| `StrategyLookaheadDetectedError` (exception) | Raised when lookahead risk or future data access is detected. |
| `SimArbitraryCodeRejectedError` (exception) | Raised when arbitrary user Python code execution is rejected. |
| `StrategyInternalError` (exception) | Raised when internal strategy computations fail. |
| `StrategyLifecycleNotApprovedError` (exception) | Raised when strategy environment exceeds lifecycle approval state. |
| `StrategyEnvironmentNotPermittedError` (exception) | Raised when the target environment is not declared in registry. |
| `StrategyArtifactHashMismatchError` (exception) | Raised when package artifact hash does not match registry entry. |
| `StrategyDependencyHashMismatchError` (exception) | Raised when lockfile hash mismatch is detected. |
| `IndicatorModuleError` (exception) | Raised when an underlying indicator module call fails. |
| `StrategyCheckpointInvalidError` (exception) | Raised when checkpoint data shape is invalid. |
| `StrategyCheckpointIncompatibleError` (exception) | Raised when restored checkpoint has mismatching settings or version. |
| `StrategyDataNotReadyError` (exception) | Raised when input data is missing or not ready. |
| `StrategyIndicatorNotReadyError` (exception) | Raised when required indicators are warm-up incomplete. |
| `StrategyMissingRequiredDataError` (exception) | Raised when data query yields missing fields. |
| `StrategyStaleDataError` (exception) | Raised when data arrival exceeds latency threshold. |
| `StrategyDuplicateIntentError` (exception) | Raised when idempotency or sequence keys collide. |
| `StrategyResourceLimitExceededError` (exception) | Raised when CPU time or memory allocations exceed limit. |
| `StrategyTimeoutError` (exception) | Raised when strategy hook timing exceeds budget limit. |
| `StrategyValidationArtifactRequiredError` (exception) | Raised when promotion fails due to missing evidence artifact. |
| `StrategyRiskProfileRequiredError` (exception) | Raised when strategy registry has no declared risk profile. |
| `StrategyCircuitBreakerTriggeredError` (exception) | Raised when circuit breaker stops intent generation. |
| `StrategyPositionLimitExceededError` (exception) | Raised when intent exceeds local position sizing caps. |
| `StrategyVolumeParticipationExceededError` (exception) | Raised when volume size exceeds visible participation limit. |
| `StrategyDataQualityGateFailedError` (exception) | Raised when timezone normalization or gaps reject tick inputs. |
| `StrategyPerformanceDegradedError` (exception) | Raised when analytics flag degraded returns. |
| `StrategyDriftDetectedError` (exception) | Raised when model inputs drift statistical limits. |
| `StrategyRegulatoryLimitBreachedError` (exception) | Raised when local validation hits regulatory caps. |
| `StrategyMarketAccessRevokedError` (exception) | Raised when broker reports login or venue suspension. |
| `StrategyHardKilledError` (exception) | Raised when external orchestration sends emergency hard kill signal. |
| `map_exception_to_strategy_error(exc: Exception) -> StrategyError` | Map any lower-level exception to a StrategyError code at boundaries. |


## FEAT-STR-05: Pure strategy rules (app.services.strategy.pybots._template.rules)

| Function | Purpose |
|----------|---------|
| `long_exit_signal(context: MarketContext, config: StrategyConfig) -> bool` | Return True only when a long position should be exited. |
| `short_exit_signal(context: MarketContext, config: StrategyConfig) -> bool` | Return True only when a short position should be exited. |


## FEAT-STR-06: Copy-ready strategy orchestration class (app.services.strategy.pybots._template.strategy)

| Function | Purpose |
|----------|---------|
| `TemplateStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Map the four pure rule functions into the canonical signal contract. |


## FEAT-STR-07: Broker-neutral translation of Decomposing Trade EA.mq5 (app.services.strategy.pybots.decomposing_trade_ea.strategy)

| Function | Purpose |
|----------|---------|
| `DecomposingTradeStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate signals in a vectorized way on the DataFrame. |
| `DecomposingTradeStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | RSI-triggered hedged averaging system with partial decompression. |


## FEAT-STR-08: Broker-neutral translation of Harriet Hedging EA.mq5 (app.services.strategy.pybots.harriet_hedging_ea.strategy)

| Function | Purpose |
|----------|---------|
| `HarrietHedgingStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate Harriet Hedging signals in a vectorized way. |
| `HarrietHedgingStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | Higher-low/lower-high confirmation with hedged basket management. |


## FEAT-STR-09: Broker-neutral translation of Market Structure EA.mq5 (app.services.strategy.pybots.market_structure_ea.strategy)

| Function | Purpose |
|----------|---------|
| `MarketStructureStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate market structure signals on the DataFrame. |
| `MarketStructureStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | ZigZag-structure breakout, opposite hedge, and event-driven grid ladder. |
| `MarketStructureStrategy.build_execution_event_intents(context: MarketContext, event_id: str) -> Sequence[TradeIntent]` | Rebuild source ``OnTrade`` actions from an execution-reconciled snapshot. |


## FEAT-STR-10: Pure helpers shared by the bundled MQL5 strategy translations (app.services.strategy.pybots.mql5_translation_helpers)

| Function | Purpose |
|----------|---------|
| `require_quote(context: MarketContext) -> QuoteSnapshot` | Return an executable quote or fail loudly; translations cannot invent prices. |
| `pip_value(context: MarketContext, pips: float, multiplier: float) -> float` | Convert an MQL-style pip input using the supplied instrument point size. |
| `by_direction(positions: Sequence[PositionSnapshot], direction: Direction) -> tuple[PositionSnapshot, ...]` | Return the subset of open positions matching the given trade direction. |
| `entry_price(position: PositionSnapshot) -> float` | Return the reconciled opening price required by MQL basket calculations. |
| `average_entry(positions: Sequence[PositionSnapshot]) -> float` | Return the arithmetic average entry price across the given positions. |


## FEAT-STR-11: Naïve moving-average trend-following strategy (app.services.strategy.pybots.naive_ma_trend.strategy)

| Function | Purpose |
|----------|---------|
| `NaiveMATrendStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate entries and exits in a vectorized way on the DataFrame. |


## FEAT-STR-12: Broker-neutral translation of RandomWalk EA.mq5 (app.services.strategy.pybots.random_walk_ea.strategy)

| Function | Purpose |
|----------|---------|
| `RandomWalkStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | The original EA has no directional signal calculation. |
| `RandomWalkStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | Dual fixed-size long/short basket launcher with layered SL and TP prices. |


## FEAT-STR-13: Explicit catalog of bundled strategies for agent/tool discovery (app.services.strategy.pybots.registry)

| Function | Purpose |
|----------|---------|
| `bundled_strategy_ids() -> tuple[str, ...]` | Return stable strategy IDs that agents are allowed to instantiate. |
| `load_bundled_strategy(strategy_id: str, state: StrategyState \| None = None) -> BaseStrategy` | Load a bundled config and construct its matching implementation class. |
| `strategy_from_config(config: StrategyConfig, state: StrategyState \| None = None) -> BaseStrategy` | Construct a bundled implementation from an already validated config. |


## FEAT-STR-14: Pure, no-lookahead SQX-style breakout signals (app.services.strategy.pybots.sqx_breakout_atr_trailing.rules)

| Function | Purpose |
|----------|---------|
| `long_entry_signal(context: MarketContext, config: StrategyConfig) -> bool` | Return opening-price break above the prior high channel after being below it. |
| `short_entry_signal(context: MarketContext, config: StrategyConfig) -> bool` | Return opening-price break below the prior low channel after being above it. |


## FEAT-STR-15: Working SQX-style breakout strategy built on the common template (app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy)

| Function | Purpose |
|----------|---------|
| `SQXBreakoutAtrTrailingStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate SQX-style entry signals in a vectorized way. |
| `SQXBreakoutAtrTrailingStrategy.build_protection_request(context: MarketContext, direction: Direction) -> ProtectionRequest` | Build distances from the configured ATR formulas for either direction. |


## FEAT-STR-16: Broker-neutral translation of White Fairy EA.mq5 (app.services.strategy.pybots.white_fairy_ea.strategy)

| Function | Purpose |
|----------|---------|
| `WhiteFairyStrategy.calculate_signals(df: pd.DataFrame, context: MarketContext) -> pd.DataFrame` | Calculate White Fairy signals in a vectorized way. |
| `WhiteFairyStrategy.build_custom_decision(context: MarketContext) -> StrategyDecision \| None` | Build the custom decision for White Fairy using the precalculated signals. |


## FEAT-STR-17: Strategy registry tools (app.services.strategy.registry)

| Function | Purpose |
|----------|---------|
| `StrategyRegistryError` (model) | Raised when a strategy cannot be resolved from the registry. |
| `register_strategy(name: str, strategy_cls: StrategyClass) -> None` | Register a strategy class by config-facing name. |
| `get_strategy_class(name: str) -> StrategyClass` | Resolve a strategy class by config-facing name. |
| `list_strategy_names() -> tuple[str, ...]` | Return registered strategy names in stable order. |
| `registered_strategies() -> dict[str, StrategyClass]` | Return a shallow copy of the strategy registry. |
| `register_builtin_strategies() -> None` | Register built-in simulation strategies. |


## FEAT-STR-18: Serializable strategy-local state; it is not the broker ledger (app.services.strategy.state)

| Function | Purpose |
|----------|---------|
| `StrategyState.entry_count_for(trading_day: str) -> int` | Minimal restart-safe state shared by standard and custom strategies. |
| `StrategyState.increment_entry_count(trading_day: str) -> None` | Minimal restart-safe state shared by standard and custom strategies. |
| `StrategyState.get_custom(key: str, default: Any = None) -> Any` | Minimal restart-safe state shared by standard and custom strategies. |
| `StrategyState.set_custom(key: str, value: Any) -> None` | Minimal restart-safe state shared by standard and custom strategies. |
| `StrategyState.to_dict() -> dict[str, Any]` | Minimal restart-safe state shared by standard and custom strategies. |
| `StrategyState.from_dict(value: dict[str, Any]) -> StrategyState` | Minimal restart-safe state shared by standard and custom strategies. |


## FEAT-STR-19: Stateful strategy helper tools (app.services.strategy.stateful_common)

| Function | Purpose |
|----------|---------|
| `ensure_signal_columns(data: pd.DataFrame, *, include_activators: bool = False, include_compat_columns: bool = True) -> pd.DataFrame` | Return bars with the HaruQuant v1.0 strategy signal schema. |
| `ensure_no_signal_columns(data: pd.DataFrame) -> pd.DataFrame` | Return bars with neutral signal columns for tick generation. |
| `is_bar_close(context: StrategyContext) -> bool` | Detect whether the current strategy context is at bar close. |
| `current_mid_price(context: StrategyContext) -> float` | Calculate the current bid/ask midpoint from a strategy context. |
| `historical_mid_prices(context: StrategyContext) -> pd.Series` | Build historical midpoint prices up to the current tick index. |
| `rolling_rsi(prices: pd.Series, period: int) -> float \| None` | Calculate the latest rolling RSI value. |
| `rolling_sma(prices: pd.Series, period: int) -> float \| None` | Calculate the latest simple moving average value. |
| `positions_for_side(context: StrategyContext, side: str) -> list[PositionSnapshot]` | Return open positions in the current context matching a side. |
| `basket_pnl(positions: Iterable[PositionSnapshot]) -> float` | Sum profit/loss for a basket of positions. |
| `weighted_average_price(positions: Iterable[PositionSnapshot]) -> float \| None` | Calculate volume-weighted average open price for a basket. |
| `oldest_position(positions: Iterable[PositionSnapshot]) -> PositionSnapshot \| None` | Return the oldest position in a basket. |


## FEAT-STR-20: File storage system for strategy code versioning (app.services.strategy.storage)

| Function | Purpose |
|----------|---------|
| `StrategyStorage.__init__(base_dir: str \| None = None) -> None` | Initialize strategy storage. |
| `StrategyStorage.save_strategy(user_id: int, strategy_id: int, version: str, code: str, parameters: dict[str, Any] \| None = None, metadata: dict[str, Any] \| None = None, username: str = '', strategy_name: str = '') -> str` | Save strategy code to file. |
| `StrategyStorage.load_strategy_code(user_id: int, strategy_id: int, version: str, username: str = '', strategy_name: str = '') -> str` | Load strategy code from file. |
| `StrategyStorage.load_strategy_metadata(user_id: int, strategy_id: int, version: str, username: str = '', strategy_name: str = '') -> dict[str, Any]` | Load strategy metadata from file. |
| `StrategyStorage.load_strategy_class(user_id: int, strategy_id: int, version: str, username: str = '', strategy_name: str = '') -> type[BaseStrategy]` | Load strategy class from file. |
| `StrategyStorage.delete_strategy(user_id: int, strategy_id: int, username: str = '', strategy_name: str = '') -> None` | Delete all versions of a strategy. |
| `StrategyStorage.delete_strategy_version(user_id: int, strategy_id: int, version: str, username: str = '', strategy_name: str = '') -> None` | Delete a specific version of a strategy. |
| `StrategyStorage.export_strategy(user_id: int, strategy_id: int, version: str, export_path: str, username: str = '', strategy_name: str = '') -> str` | Export strategy to a zip file. |
| `StrategyStorage.import_strategy(user_id: int, strategy_id: int, version: str, import_path: str, username: str = '', strategy_name: str = '') -> str` | Import strategy from a zip file. |
| `StrategyStorage.list_versions(username: str = '', strategy_name: str = '') -> list[str]` | List all versions of a strategy. |
| `StrategyStorage.get_strategy_path(user_id: int, strategy_id: int, version: str, username: str = '', strategy_name: str = '') -> str` | Get absolute path to strategy file. |
| `StrategyStorage.get_strategy_artifact_root(user_id: int, strategy_id: int, username: str = '', strategy_name: str = '') -> str` | Return the preferred artifact root for a strategy. |


## FEAT-STR-21: Standard HaruQuant strategy template (app.services.strategy.template_strategy)

| Function | Purpose |
|----------|---------|
| `TemplateStrategy.__init__(params: dict[str, Any] \| None = None) -> None` | Internal function for template_strategy.__init__. |
| `TemplateStrategy.on_init() -> None` | Public function for template_strategy.on_init. |
| `TemplateStrategy.on_bar(data: pd.DataFrame) -> pd.DataFrame` | Calculate features, simple signal columns, and event activators. |
| `TemplateStrategy.get_signal(data: pd.DataFrame, index: int) -> SignalDict \| None` | Public function for template_strategy.get_signal. |
