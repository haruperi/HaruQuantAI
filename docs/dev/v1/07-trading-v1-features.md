## FEAT-TRD-01: Shared packaging helpers for trading action primitives (app.services.trading.actions._common)

| Function | Purpose |
|----------|---------|
| `LiveGatePipeline.evaluate(request: TradingRequestEnvelope) -> TradingResponseEnvelope` | Evaluate the live gate pipeline for a packaged request. |
| `TradingActionDependencies` (class) | Injected dependencies shared by trading action primitives. |
| `package_request(*, action: TradingAction, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, symbol: str \| None, payload: JsonObject, quote_snapshot: QuoteSnapshot \| None = None, oco_group_id: str \| None = None, linked_order_ids: tuple[str, ...] = ()) -> TradingRequestEnvelope` | Build a canonical trading request envelope for a packaged action. |
| `dispatch_or_package(*, request: TradingRequestEnvelope, deps: TradingActionDependencies, message: str = "Trading request packaged; live gate pipeline not yet engaged.") -> TradingResponseEnvelope` | Evaluate the injected live gate pipeline or return a packaged response. |


## FEAT-TRD-02: Platform-independent strategy and session control action primitives (app.services.trading.actions.controls)

| Function | Purpose |
|----------|---------|
| `ShutdownResult` (class) | Structured outcome of a graceful session shutdown request. |
| `pause_strategy(*, strategy_id: str, reason: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies) -> TradingResponseEnvelope` | Pause a strategy's local operational state (TRD-FR-028). |
| `resume_strategy(*, strategy_id: str, reason: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies) -> TradingResponseEnvelope` | Resume a previously paused strategy (TRD-FR-028). |
| `sync_positions(*, route: TradingRoute, request_id: str, correlation_id: str, deps: TradingActionDependencies) -> TradingResponseEnvelope` | Retrieve current broker state and synchronize local projections. |
| `shutdown(*, pending_request_count: int, deps: TradingActionDependencies, flush: object \| None = None, drain: object \| None = None, reconcile: object \| None = None, drain_timeout_seconds: float = DEFAULT_DRAIN_TIMEOUT_SECONDS) -> ShutdownResult` | Stop admitting new requests, drain in-flight work, and flush state. |
| `trigger_global_kill_switch(*, reason: str, actor: str, route: TradingRoute, promotion_stage: PromotionStage, request_id: str, correlation_id: str, deps: TradingActionDependencies, idempotency_store: IdempotencyStore, event_journal: EventJournal, idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS) -> TradingResponseEnvelope` | Activate the global kill switch (TRD-FR-031, TRD-FR-034). |
| `trigger_strategy_kill_switch(*, strategy_id: str, reason: str, actor: str, route: TradingRoute, promotion_stage: PromotionStage, request_id: str, correlation_id: str, deps: TradingActionDependencies, idempotency_store: IdempotencyStore, event_journal: EventJournal, idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS) -> TradingResponseEnvelope` | Activate a strategy-scoped kill switch (TRD-FR-032, TRD-FR-034). |
| `trigger_symbol_kill_switch(*, symbol: str, reason: str, actor: str, route: TradingRoute, promotion_stage: PromotionStage, request_id: str, correlation_id: str, deps: TradingActionDependencies, idempotency_store: IdempotencyStore, event_journal: EventJournal, idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS) -> TradingResponseEnvelope` | Activate a symbol-scoped kill switch (TRD-FR-033, TRD-FR-034). |


## FEAT-TRD-03: Platform-independent emergency safety action primitives (app.services.trading.actions.emergency)

| Function | Purpose |
|----------|---------|
| `EmergencyScope` (enum) | Emergency action scope classification. |
| `cancel_all_orders(*, scope: EmergencyScope, target: str \| None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Cancel all working pending orders within a scope (TRD-FR-035). |
| `close_all_positions(*, scope: EmergencyScope, target: str \| None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Close all open positions within a scope (TRD-FR-035). |
| `flatten_account(*, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Cancel all orders and close all positions for the account (TRD-FR-035). |
| `flatten_strategy(*, strategy_id: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Cancel all orders and close all positions for a strategy (TRD-FR-035). |
| `flatten_symbol(*, symbol: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Cancel all orders and close all positions for a symbol (TRD-FR-035). |


## FEAT-TRD-04: Platform-independent order action primitives (app.services.trading.actions.orders)

| Function | Purpose |
|----------|---------|
| `Trade.__init__(store: TradeStore \| None = None) -> None` | Initialize Trade helper with default parameters and services. |
| `Trade.set_symbol(symbol: str) -> None` | Set default symbol for trade operations. |
| `Trade.set_order_filling(filling: int) -> None` | Set order execution filling mode. |
| `Trade.set_deviation_in_points(deviation: int) -> None` | Set maximum price deviation in points. |
| `Trade.set_expert_magic_number(magic: int) -> None` | Set Expert Advisor magic number. |
| `Trade.result_retcode() -> int` | Get result code of the last execution. |
| `Trade.result_deal() -> int` | Get deal ticket of the last execution. |
| `Trade.result_order() -> int` | Get order ticket of the last execution. |
| `Trade.result_volume() -> float` | Get volume of the last executed request. |
| `Trade.result_price() -> float` | Get price of the last executed request. |
| `Trade.result_bid() -> float` | Get current bid price of the last executed request. |
| `Trade.result_ask() -> float` | Get current ask price of the last executed request. |
| `Trade.result_comment() -> str` | Get comments on the execution results. |
| `Trade.buy(volume: float, symbol: str \| None = None, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> bool` | Open a long market position. |
| `Trade.sell(volume: float, symbol: str \| None = None, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> bool` | Open a short market position. |
| `Trade.buy_limit(volume: float, price: float, symbol: str \| None = None, sl: float = 0.0, tp: float = 0.0, expiration: int = 0, comment: str = '') -> bool` | Place a Buy Limit pending order. |
| `Trade.sell_limit(volume: float, price: float, symbol: str \| None = None, sl: float = 0.0, tp: float = 0.0, expiration: int = 0, comment: str = '') -> bool` | Place a Sell Limit pending order. |
| `Trade.buy_stop(volume: float, price: float, symbol: str \| None = None, sl: float = 0.0, tp: float = 0.0, expiration: int = 0, comment: str = '') -> bool` | Place a Buy Stop pending order. |
| `Trade.sell_stop(volume: float, price: float, symbol: str \| None = None, sl: float = 0.0, tp: float = 0.0, expiration: int = 0, comment: str = '') -> bool` | Place a Sell Stop pending order. |
| `Trade.position_open(symbol: str, order_type: int, volume: float, price: float, sl: float, tp: float, comment: str = '') -> bool` | Open a position with specified properties. |
| `Trade.position_close(symbol_or_ticket: str \| int, deviation: int = -1) -> bool` | Close an active open position fully. |
| `Trade.position_modify(symbol_or_ticket: str \| int, sl: float, tp: float) -> bool` | Modify SL/TP of an active open position. |
| `Trade.order_modify(ticket: int, price: float, sl: float, tp: float) -> bool` | Modify a pending order properties. |
| `Trade.order_delete(ticket: int) -> bool` | Cancel/Delete a pending order. |
| `Trade.set_kill_switch(active: bool, flatten_positions: bool = False) -> None` | Set the global kill switch state. |
| `Trade.shutdown(timeout: float = 5.0) -> None` | Shutdown the trading service gracefully. |
| `buy(*, symbol: str, volume: Decimal, sl: Decimal \| None = None, tp: Decimal \| None = None, deviation_points: int \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a buy market order intent (TRD-FR-021). |
| `sell(*, symbol: str, volume: Decimal, sl: Decimal \| None = None, tp: Decimal \| None = None, deviation_points: int \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a sell market order intent (TRD-FR-021). |
| `buy_limit(*, symbol: str, volume: Decimal, price: Decimal, sl: Decimal \| None = None, tp: Decimal \| None = None, tif: TimeInForce = TimeInForce.GTC, expiration: str \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a buy-limit pending order intent (TRD-FR-022). |
| `sell_limit(*, symbol: str, volume: Decimal, price: Decimal, sl: Decimal \| None = None, tp: Decimal \| None = None, tif: TimeInForce = TimeInForce.GTC, expiration: str \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a sell-limit pending order intent (TRD-FR-022). |
| `buy_stop(*, symbol: str, volume: Decimal, price: Decimal, stop_limit_price: Decimal \| None = None, sl: Decimal \| None = None, tp: Decimal \| None = None, tif: TimeInForce = TimeInForce.GTC, expiration: str \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a buy-stop pending order intent (TRD-FR-022). |
| `sell_stop(*, symbol: str, volume: Decimal, price: Decimal, stop_limit_price: Decimal \| None = None, sl: Decimal \| None = None, tp: Decimal \| None = None, tif: TimeInForce = TimeInForce.GTC, expiration: str \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Formulate a sell-stop pending order intent (TRD-FR-022). |
| `order_modify(*, ticket: str, price: Decimal \| None = None, sl: Decimal \| None = None, tp: Decimal \| None = None, expected_state_version: int \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, symbol: str \| None, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Package a pending order mutation while preserving order identity. |
| `order_delete(*, ticket: str, expected_state_version: int \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, symbol: str \| None, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Package a pending order cancellation (TRD-FR-023). |
| `submit_oco_group(orders: tuple[OrderIntent, ...], *, contexts: tuple[OrderValidationContext, ...], oco_group_id: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Submit an OCO/bracket order group with consistent group parameters. |


## FEAT-TRD-05: Platform-independent position lifecycle action primitives (app.services.trading.actions.positions)

| Function | Purpose |
|----------|---------|
| `NettingMode` (enum) | Account position-netting mode. |
| `PositionCloseMode` (enum) | Resolved close addressing mode. |
| `ReduceExposureScope` (enum) | Approved scope for an exposure reduction command. |
| `position_open(*, symbol: str, side: OrderSide, volume: Decimal, sl: Decimal \| None = None, tp: Decimal \| None = None, deviation_points: int \| None = None, magic_number: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, context: OrderValidationContext, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Open a position via a validated market order intent (TRD-FR-026). |
| `position_close(*, netting_mode: NettingMode, ticket: str \| None = None, symbol: str \| None = None, volume: Decimal \| None = None, deviation_points: int \| None = None, comment: str \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Package a position close by ticket or by symbol (TRD-FR-026). |
| `position_modify(*, position_id: str, sl: Decimal \| None = None, tp: Decimal \| None = None, expected_state_version: int \| None = None, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, symbol: str \| None = None, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Package a position SL/TP mutation (TRD-FR-026). |
| `reduce_exposure(*, scope: ReduceExposureScope, target: str, volume: Decimal, risk_decision_id: str, route: TradingRoute, promotion_stage: PromotionStage, mutation_capability: MutationCapability, request_id: str, correlation_id: str, deps: TradingActionDependencies, quote_snapshot: QuoteSnapshot \| None = None) -> TradingResponseEnvelope` | Package a partial-close/volume-reduction command (TRD-FR-027). |


## FEAT-TRD-06: Local trading action validation and parameter normalization primitives (app.services.trading.actions.validation)

| Function | Purpose |
|----------|---------|
| `OrderSide` (enum) | Trade direction for an order intent. |
| `OrderType` (enum) | Local order type classification used to route validation rules. |
| `SymbolTradingConstraints.validate_constraints() -> SymbolTradingConstraints` | Validate symbol constraint consistency. |
| `AccountMarginContext.validate_margin_context() -> AccountMarginContext` | Validate account margin context fields. |
| `ConversionRateEvidence.validate_conversion_evidence() -> ConversionRateEvidence` | Validate conversion-rate evidence identifiers. |
| `ConversionRateEvidence.is_fresh() -> bool` | Return whether the conversion-rate evidence is within its TTL. |
| `MarketSessionEvidence.validate_session_evidence() -> MarketSessionEvidence` | Validate market session evidence identifiers. |
| `MarketSessionEvidence.is_fresh() -> bool` | Return whether the session evidence is within its TTL. |
| `LocateSnapshot.validate_locate_snapshot() -> LocateSnapshot` | Validate locate snapshot identifiers. |
| `LocateSnapshot.is_fresh() -> bool` | Return whether the locate snapshot is within its TTL. |
| `DefenseInDepthRailLimits` (class) | Static, un-overridable defense-in-depth rail ceilings (TRD-FR-048). |
| `DailyRailState` (class) | Mutable rail counters supplied by the caller for one evaluation. |
| `OrderIntent.validate_intent() -> OrderIntent` | Validate structural order intent completeness. |
| `OrderValidationContext` (class) | Evidence bundle required to validate one order intent. |
| `OrderValidationResult` (class) | Validated and normalized order intent plus the audit trail. |
| `normalize_decimal_to_step(value: Decimal, *, step: Decimal, rounding: str) -> Decimal` | Normalize a Decimal value to the nearest instrument step. |
| `normalize_volume(volume: Decimal, *, constraints: SymbolTradingConstraints, allow_round_up: bool = False) -> tuple[Decimal, Decimal]` | Normalize requested volume to the symbol's volume step. |
| `normalize_stop_price(value: Decimal, *, tick_size: Decimal, below_market: bool) -> tuple[Decimal, Decimal]` | Normalize a stop price to the tick size, rounding away from market. |
| `compute_account_currency_notional(*, volume: Decimal, reference_price: Decimal, constraints: SymbolTradingConstraints, account_currency: str, conversion: ConversionRateEvidence \| None) -> tuple[Decimal, Decimal \| None]` | Compute order notional value expressed in account currency. |
| `validate_volume(volume: Decimal, *, constraints: SymbolTradingConstraints) -> JsonObject` | Validate requested volume against dynamic symbol constraints. |
| `validate_stops(*, side: OrderSide, sl: Decimal \| None, tp: Decimal \| None, reference_price: Decimal, constraints: SymbolTradingConstraints) -> JsonObject` | Validate direction-aware stop-loss/take-profit geometry. |
| `validate_margin(*, volume: Decimal, reference_price: Decimal, constraints: SymbolTradingConstraints, account: AccountMarginContext, conversion: ConversionRateEvidence \| None) -> JsonObject` | Validate that free margin covers the trade intent's margin requirement. |
| `validate_market_session(*, route: TradingRoute, symbol: str, evidence: MarketSessionEvidence \| None) -> JsonObject` | Validate instrument trading session availability. |
| `validate_time_in_force(*, tif: TimeInForce, supported: tuple[TimeInForce, ...]) -> JsonObject` | Validate that the requested TIF is supported by broker capabilities. |
| `validate_execution_protections(*, order_type: OrderType, max_slippage_points: int \| None, price: Decimal \| None, reference_price: Decimal, price_collar_bps: Decimal) -> JsonObject` | Validate mandatory slippage protection and pending-order price collars. |
| `validate_fat_finger_ceiling(*, volume: Decimal, reference_price: Decimal, constraints: SymbolTradingConstraints, account_currency: str, conversion: ConversionRateEvidence \| None, ceiling: Decimal) -> JsonObject` | Validate the immutable fat-finger notional ceiling (TRD-FR-045/047). |
| `validate_defense_in_depth_rails(*, notional: Decimal, limits: DefenseInDepthRailLimits, state: DailyRailState) -> JsonObject` | Validate the static defense-in-depth rails (TRD-FR-048). |
| `validate_short_locate(*, is_short: bool, locate: LocateSnapshot \| None) -> JsonObject` | Validate short-sale locate/hard-to-borrow authorization (TRD-FR-049). |
| `validate_order_request(intent: OrderIntent, *, context: OrderValidationContext) -> OrderValidationResult` | Combine all local order parameter validations (TRD-FR-046). |
| `ValidationService.normalize_precision(value: float \| Decimal, precision: float) -> Decimal` | Round financial values using Decimal to avoid floating point issues. |
| `ValidationService.validate_volume(symbol: str, volume: float, symbol_info: SymbolInfo) -> float` | Validate trade lot volume sizes. |
| `ValidationService.validate_price(symbol: str, price: float, order_type: int, symbol_info: SymbolInfo) -> float` | Validate price constraints. |
| `ValidationService.validate_stops(symbol: str, sl: float, tp: float, order_type: int, price: float, symbol_info: SymbolInfo) -> tuple[float, float]` | Validate stop-loss and take-profit geometry. |
| `ValidationService.validate_margin(account_id: str, symbol: str, _volume: float, _price: float, _order_type: int, account_info: AccountInfo) -> None` | Validate margin requirements. |
| `ValidationService.validate_slippage(slippage: int, max_tolerance: int = 100) -> None` | Validate price slippage limits. |
| `ValidationService.validate_dealing_mode_compatibility(_action: int, _ticket: int \| None, account_info: AccountInfo) -> None` | Validate position modifications match Netting vs Hedging accounting. |
| `ValidationService.validate_market_session(symbol: str) -> None` | Validate that requested action is within active market session hours. |
| `ValidationService.validate_order_request(request: dict[str, Any], symbol_info: SymbolInfo, account_info: AccountInfo) -> dict[str, Any]` | Perform full validation and parameter sanitization on a request. |


## FEAT-TRD-07: Concurrency ordering and locking logic (app.services.trading.concurrency)

| Function | Purpose |
|----------|---------|
| `ConcurrencyQueue.__init__() -> None` | Initialize ConcurrencyQueue. |
| `ConcurrencyQueue.get_instance() -> 'ConcurrencyQueue'` | Get the shared ConcurrencyQueue singleton. |
| `ConcurrencyQueue.lock(account_id: str, symbol: str) -> AsyncGenerator[None]` | Async context manager to acquire and release lock per (account, symbol). |
| `ConcurrencyQueue.lock_sync(account_id: str, symbol: str) -> Generator[None]` | Sync context manager to acquire and release lock per (account, symbol). |


## FEAT-TRD-08: Trading runtime configuration loading and reload policy (app.services.trading.config.loader)

| Function | Purpose |
|----------|---------|
| `ConfigChangeEvent` (model) | Journal-ready effective configuration change event. |
| `load_trading_config(source: TradingConfigSource) -> TradingRuntimeConfig` | Load and validate a trading runtime configuration. |
| `hash_effective_config(config: TradingRuntimeConfig) -> str` | Hash the redacted effective config. |
| `build_config_change_event(*, config: TradingRuntimeConfig, actor: str, effective_at: str) -> ConfigChangeEvent` | Build a journal event for an effective config change. |
| `apply_trading_config_reload(*, current: TradingRuntimeConfig, proposed: TradingRuntimeConfig, session_state: str, actor: str, effective_at: str) -> ConfigChangeEvent` | Validate hot reload policy and return the change event. |


## FEAT-TRD-09: Trading runtime configuration contracts (app.services.trading.config.models)

| Function | Purpose |
|----------|---------|
| `TradingConfigModel` (model) | Base class for immutable trading configuration models. |
| `SecretReference.validate_reference() -> SecretReference` | Validate the secret reference has no raw secret shape. |
| `SecretReference.redacted() -> str` | Return a redacted display value for this reference. |
| `RouteSettings.validate_routes() -> RouteSettings` | Validate route settings. |
| `RouteSettings.passing_gate_side_effect() -> SideEffectMode` | Return the side-effect mode for a passing live gate. |
| `RateLimitSettings` (model) | Client-side rate limit settings. |
| `TimeoutSettings` (model) | Trading runtime timeout settings in milliseconds. |
| `CostBudgetSettings.validate_currency() -> CostBudgetSettings` | Validate the budget currency code. |
| `StalenessSettings` (model) | Staleness and TTL limits. |
| `StoreConnectionTargets` (model) | Opaque store connection target references. |
| `BrokerCapabilityEvidence.validate_fresh() -> None` | Fail closed if capability evidence exceeds its TTL. |
| `ReconciliationSettings.validate_reconciliation_settings() -> ReconciliationSettings` | Validate settings. |
| `MonitoringSettings.validate_monitoring_settings() -> MonitoringSettings` | Validate monitoring settings and incident taxonomy constraints. |
| `TradingRuntimeConfig.validate_runtime_config() -> TradingRuntimeConfig` | Validate trading runtime configuration constraints. |
| `TradingRuntimeConfig.live_mutation_side_effect() -> SideEffectMode` | Return passing-gate side-effect mode from route settings. |
| `TradingRuntimeConfig.redacted_model_dump() -> dict[str, object]` | Return a redacted configuration mapping. |


## FEAT-TRD-10: Operational notification channel configuration and payload redaction (app.services.trading.config.notifications)

| Function | Purpose |
|----------|---------|
| `NotificationChannel.validate_channel() -> NotificationChannel` | Validate notification channel metadata. |
| `NotificationConfig.approved_channel(name: str) -> NotificationChannel` | Resolve an approved notification channel. |
| `build_notification_payload(*, config: NotificationConfig, channel_name: str, event_type: str, payload: JsonObject) -> JsonObject` | Build a strictly redacted notification payload. |


## FEAT-TRD-11: Secret-reference resolution and rotation contracts (app.services.trading.config.secrets)

| Function | Purpose |
|----------|---------|
| `SecretResolutionResult` (model) | Redacted result of secret reference resolution. |
| `CredentialRotationResult` (model) | Outcome of mid-session credential rotation. |
| `SecretResolver.resolve_metadata(reference: SecretReference) -> SecretResolutionResult` | Resolve secret metadata without returning raw secret values. |
| `ReauthenticationAdapter.reauthenticate(reference: SecretReference) -> bool` | Re-authenticate using the adapter-owned secret path. |
| `resolve_secret_reference(*, reference: SecretReference, resolver: SecretResolver) -> SecretResolutionResult` | Resolve a secret reference without exposing the raw value. |
| `handle_credential_rotation(*, reference: SecretReference, adapter: ReauthenticationAdapter) -> CredentialRotationResult` | Handle mid-session credential rotation through adapter re-authentication. |


## FEAT-TRD-12: Broker communication security profile contracts (app.services.trading.config.security_profile)

| Function | Purpose |
|----------|---------|
| `BrokerSecurityProfile.validate_profile() -> BrokerSecurityProfile` | Validate security profile shape. |
| `validate_live_security_profile(*, profile: BrokerSecurityProfile, adapter_name: str) -> None` | Validate that a live mutation may use this security profile. |


## FEAT-TRD-13: Canonical trading runtime contracts (app.services.trading.contracts)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `validate_redacted_json_value(value: JsonValue, *, path: str = "$") -> None` | Validate that a JSON value contains no obvious unredacted secrets. |
| `TradingContract.validate_schema_version() -> TradingContract` | Validate schema compatibility for trading contracts. |
| `TradingRoute` (enum) | Supported trading runtime routes. |
| `TradingAction` (enum) | Canonical platform-independent trading action names. |
| `SideEffectMode` (enum) | Side-effect classification for trading responses. |
| `RetrySafety` (enum) | Retry safety classification for trading outcomes. |
| `TimeInForce` (enum) | Supported order time-in-force policies. |
| `FixExecutionState` (enum) | Granular FIX-style order and position lifecycle states. |
| `PromotionStage` (enum) | Trading promotion ladder stages. |
| `MutationCapability` (enum) | Mutation capability allowed by a request context. |
| `TradingStatus` (enum) | Public response status values. |
| `AllocationVector.serialize_weights(weights: dict[str, Decimal]) -> dict[str, str]` | Serialize Decimal weights as JSON-safe strings. |
| `AllocationVector.validate_weights() -> AllocationVector` | Validate allocation vector entries. |
| `RegulatoryTags.validate_regulatory_tags() -> RegulatoryTags` | Validate optional regulatory tag payload. |
| `RegulatoryTags.to_broker_payload() -> JsonObject` | Return the JSON-safe broker adapter regulatory tag payload. |
| `QuoteSnapshot.serialize_decimal(value: Decimal) -> str` | Serialize Decimal quote values as JSON-safe strings. |
| `QuoteSnapshot.validate_quote() -> QuoteSnapshot` | Validate quote snapshot price relationships. |
| `TradingError.validate_error() -> TradingError` | Validate the error detail contract. |
| `TradingMetadata.serialize_execution_ms(value: Decimal) -> str` | Serialize execution duration as a JSON-safe string. |
| `TradingMetadata.validate_metadata() -> TradingMetadata` | Validate metadata consistency. |
| `TradingRequestEnvelope.validate_request() -> TradingRequestEnvelope` | Validate request envelope safety requirements. |
| `TradingRequestEnvelope.to_broker_dispatch_payload() -> JsonObject` | Build a JSON-safe broker dispatch payload. |
| `NormalizedTradeResult.serialize_optional_decimal(value: Decimal \| None) -> str \| None` | Serialize optional Decimal values as JSON-safe strings. |
| `NormalizedTradeResult.validate_normalized_result() -> NormalizedTradeResult` | Validate normalized broker result identifiers. |
| `TradingResponseEnvelope.validate_response() -> TradingResponseEnvelope` | Validate response envelope fields. |
| `TradingResponseEnvelope.accepted_from_command(*, command: TradingCommandAccepted, route: TradingRoute, correlation_id: str, audit_ref: str \| None = None) -> TradingResponseEnvelope` | Build the initial async response from local command acceptance. |
| `OrderState.serialize_order_decimal(value: Decimal \| None) -> str \| None` | Serialize order Decimal fields as JSON-safe strings. |
| `OrderState.validate_order_state() -> OrderState` | Validate order state volume accounting. |
| `PositionState.serialize_position_decimal(value: Decimal \| None) -> str \| None` | Serialize position Decimal fields as JSON-safe strings. |
| `PositionState.validate_position_state() -> PositionState` | Validate position state identifiers. |
| `TradingCommandAccepted` (class) | Local command acceptance event for asynchronous live execution. |
| `TradingCommandRejected` (class) | Local command rejection event. |
| `BrokerDispatchEvent` (class) | Broker dispatch event emitted after local command acceptance. |
| `BrokerAcknowledgementEvent` (class) | Broker acknowledgement event separated from final execution reports. |
| `ExecutionReportEvent` (class) | Execution report event carrying normalized fill or reject facts. |
| `ReconciliationResolutionEvent` (class) | Reconciliation resolution event after unknown or divergent outcomes. |
| `TradingToolDefinition.validate_tool_definition() -> TradingToolDefinition` | Validate trading tool metadata. |
| `TradingToolRegistry.validate_registry() -> TradingToolRegistry` | Validate registry key and definition consistency. |
| `OrderIntent` (class) | Canonical post-risk pre-execution trade intention contract. |
| `TradeRequest.validate_submitted_time(v: str) -> str` | Validate and normalize the submission timestamp. |
| `TradeResult` (class) | Standard outcome response after execution adapter returns. |
| `Fill.validate_fill_time(v: str) -> str` | Validate and normalize the fill execution timestamp. |
| `ExecutionReport.validate_report_time(v: str) -> str` | Validate and normalize the execution report timestamp. |
| `BrokerCapabilities` (class) | Supported order features and policies of an execution provider. |


## FEAT-TRD-14: Deterministic error-code mapping for the trading service boundary (app.services.trading.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `TradingError` (exception) | Base error for deterministic trading execution failures. |
| `TradingExternalServiceError` (exception) | External service failure in trading domain. |
| `to_trading_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Trading error payload. |
| `TradingTimeoutError` (exception) | Raised when broker execution exceeds the configured timeout. |
| `UnknownOutcomeError` (exception) | Raised when broker execution outcome cannot be determined safely. |
| `classify_broker_error(raw_error: Exception \| object) -> dict[str, object]` | Classify broker errors into deterministic internal error metadata. |
| `trading_retry_delay(attempt: int, *, base_seconds: float = 0.25, max_seconds: float = 5.0, jitter_ratio: float = 0.2) -> float` | Compute exponential backoff with randomized jitter for idempotent retries. |


## FEAT-TRD-15: Broker adapter capability validation primitives (app.services.trading.execution.broker_capability_validation)

| Function | Purpose |
|----------|---------|
| `BrokerCapabilityProfile.validate_profile() -> BrokerCapabilityProfile` | Validate the capability profile is non-empty and well-formed. |
| `CapabilityCheckResult` (class) | Aggregate broker capability validation outcome. |
| `validate_order_type_capability(*, profile: BrokerCapabilityProfile, order_type: str) -> None` | Validate that the adapter supports the requested order type. |
| `validate_filling_mode_capability(*, profile: BrokerCapabilityProfile, filling_mode: str) -> None` | Validate that the adapter supports the requested filling mode. |
| `validate_precision_capability(*, profile: BrokerCapabilityProfile, price: Decimal, volume: Decimal) -> None` | Validate price and volume precision against adapter capability limits. |
| `validate_rate_limit_capability(*, profile: BrokerCapabilityProfile, requested_rate: Decimal) -> None` | Validate that requested throughput fits the adapter's rate capability. |
| `validate_broker_capabilities(*, profile: BrokerCapabilityProfile, order_type: str, filling_mode: str, price: Decimal, volume: Decimal) -> CapabilityCheckResult` | Validate every adapter capability contract before broker execution. |
| `requires_cancel_on_disconnect_failsafe(*, profile: BrokerCapabilityProfile) -> bool` | Return whether the local Cancel-on-Disconnect failsafe must run. |


## FEAT-TRD-16: The single broker mutation boundary for the trading package (BF-TRD-003) (app.services.trading.execution.broker_dispatch)

| Function | Purpose |
|----------|---------|
| `active_broker_name() -> str` | Return the name of the currently configured broker adapter. |
| `build_broker_dispatch_callable(*, payload: JsonObject, request_id: str, provider: str \| None = None) -> Callable[[], NormalizedTradeResult]` | Bind a dispatch payload to the active broker's ``trade()`` entrypoint. |
| `is_success_retcode(retcode: str) -> bool` | Return whether a provider return code represents a successful mutation. |
| `snapshot_broker_state() -> tuple[list[JsonObject], list[JsonObject]]` | Read live positions and orders for a forced reconciliation pass. |


## FEAT-TRD-17: Asynchronous execution coordination and lifecycle-mutation primitives (app.services.trading.execution.coordinator)

| Function | Purpose |
|----------|---------|
| `resolve_dispatch_target(*, route: TradingRoute) -> str` | Resolve the execution handler target for a runtime route (TRD-FR-102). |
| `AsyncDispatchExecutor.submit(dispatch_callable: Callable[[], NormalizedTradeResult]) -> Future[NormalizedTradeResult]` | Submit a dispatch callable for asynchronous execution. |
| `InFlightRequestCounter.increment() -> int` | Increment the in-flight counter. |
| `InFlightRequestCounter.decrement() -> int` | Decrement the in-flight counter, floored at zero. |
| `InFlightRequestCounter.current() -> int` | Return the current in-flight count. |
| `InFlightRequestCounter.is_drained() -> bool` | Return whether no requests are currently in flight. |
| `InFlightRequestCounter.wait_drained(timeout_seconds: float, poll_seconds: float = 0.1) -> bool` | Block until no requests are in flight, or the timeout elapses. |
| `generate_client_order_id(*, request_id: str, rng: RNG) -> str` | Generate a globally unique ``client_order_id`` (TRD-FR-104). |
| `truncate_client_order_id(*, client_order_id: str, max_length: int) -> str` | Deterministically truncate a client order ID to fit a broker field. |
| `ClientOrderIdMapping.validate_mapping() -> ClientOrderIdMapping` | Validate the client order ID mapping is well-formed. |
| `build_client_order_id_mapping(*, client_order_id: str, comment_max_length: int, external_id_max_length: int) -> ClientOrderIdMapping` | Build broker metadata field propagation for a client order ID. |
| `AllocationDispatchPlan` (class) | Multi-account allocation dispatch plan (TRD-FR-105). |
| `plan_allocation_dispatch(*, allocation: AllocationVector, base_payload: JsonObject, total_volume: Decimal, broker_supports_native_allocation: bool) -> AllocationDispatchPlan` | Plan multi-account allocation-vector dispatch (TRD-FR-105). |
| `TwoStepProtectionResult` (class) | Two-step SL/TP protection workflow outcome (TRD-FR-106). |
| `requires_two_step_protection(*, profile: BrokerCapabilityProfile) -> bool` | Return whether SL/TP must be attached via a two-step workflow. |
| `evaluate_two_step_protection_outcome(*, open_succeeded: bool, protect_succeeded: bool) -> TwoStepProtectionResult` | Evaluate a two-step open-then-protect workflow outcome (TRD-FR-106). |
| `ResidualPolicy` (enum) | Partial-fill residual handling policy (TRD-FR-107). |
| `ResidualHandlingDecision` (class) | Resolved residual handling action for a partially filled order. |
| `apply_residual_policy(*, order_id: str, policy: ResidualPolicy, remaining_volume: Decimal) -> ResidualHandlingDecision` | Resolve the dispatch action for a partial-fill residual (TRD-FR-107). |
| `NonAtomicModifyStage` (enum) | Cancel-then-replace non-atomic modify workflow stage (TRD-FR-108). |
| `NonAtomicModifyState` (class) | Stateful non-atomic modify workflow record. |
| `begin_non_atomic_modify(*, order_id: str) -> NonAtomicModifyState` | Reserve an order for a non-atomic cancel-then-replace modify (TRD-FR-108). |
| `record_cancel_dispatched(*, state: NonAtomicModifyState) -> NonAtomicModifyState` | Record that the cancel step of a non-atomic modify was dispatched. |
| `record_cancel_confirmed(*, state: NonAtomicModifyState) -> NonAtomicModifyState` | Record confirmed cancellation of the working order. |
| `record_replace_dispatched(*, state: NonAtomicModifyState) -> NonAtomicModifyState` | Record that the replace step of a non-atomic modify was dispatched. |
| `NonAtomicModifyResolution` (class) | Resolved outcome after a non-atomic modify replace step (TRD-FR-108). |
| `resolve_replace_outcome(*, state: NonAtomicModifyState, replace_succeeded: bool, reentry_allowed: bool) -> NonAtomicModifyResolution` | Resolve the outcome of a non-atomic modify replace step (TRD-FR-108). |
| `OcoExecutionMode` (enum) | Resolved OCO/bracket group execution mode (TRD-FR-110). |
| `resolve_oco_execution_mode(*, profile: BrokerCapabilityProfile, synthetic_emulation_enabled: bool) -> OcoExecutionMode` | Resolve how an OCO/bracket group should be executed (TRD-FR-110). |
| `require_oco_submission_allowed(*, mode: OcoExecutionMode) -> None` | Fail closed on OCO submission when no execution mode is available. |
| `evaluate_oco_sibling_cancellation(*, filled_order_id: str, sibling_order_ids: tuple[str, ...]) -> tuple[str, ...]` | Resolve sibling orders to cancel after an OCO leg fills (TRD-FR-109). |
| `OcoWatchdog.register_group(*, group_id: str, order_ids: tuple[str, ...]) -> None` | Register an OCO/bracket group for watchdog tracking. |
| `OcoWatchdog.on_execution_report(*, group_id: str, order_id: str, execution_state: str) -> tuple[str, ...]` | Process an execution report and resolve sibling cancellations. |
| `MultiLegDecision` (class) | Multi-leg execution rollback decision (TRD-FR-111). |
| `MultiLegExecutionCoordinator.register_legs(*, group_id: str, leg_order_ids: tuple[str, ...]) -> None` | Register the leg order IDs belonging to a multi-leg group. |
| `MultiLegExecutionCoordinator.on_leg_outcome(*, group_id: str, leg_order_id: str, rejected: bool, unfilled_fraction: Decimal) -> MultiLegDecision` | Evaluate a leg outcome and resolve rollback of sibling legs. |
| `TransactionCostFacts` (class) | Captured transaction cost facts for one order (TRD-FR-112). |
| `CostAdjustmentEvent` (class) | Transaction cost capture or later adjustment event (TRD-FR-112). |
| `capture_transaction_cost(*, order_id: str, cost_facts: TransactionCostFacts, recorded_at: str, is_adjustment: bool = False) -> CostAdjustmentEvent` | Capture transaction cost facts for an order (TRD-FR-112). |
| `finalize_dispatch_outcome(*, trade_store: TradeStore, route: TradingRoute, tenant_id: str, order_state: JsonObject, expected_version: int \| None, idempotency_store: IdempotencyStore, idempotency_key: str, idempotency_outcome: JsonObject, completed_at: object, release_concurrency_lease: Callable[[], None] \| None = None) -> str` | Finalize post-response state after a dispatch completes (TRD-FR-114). |
| `ExecutionCoordinator.build_broker_dispatch_payload(request: TradingRequestEnvelope) -> JsonObject` | Build a JSON-safe broker dispatch payload. |
| `ExecutionCoordinator.dispatch_async(*, request_id: str, action: TradingAction, accepted_at: str, executor: AsyncDispatchExecutor, dispatch_callable: Callable[[], NormalizedTradeResult], on_complete: Callable[[NormalizedTradeResult \| BaseException], None]) -> TradingCommandAccepted` | Dispatch a request asynchronously and return control immediately. |


## FEAT-TRD-18: Client-side token-bucket rate limiting primitives (app.services.trading.execution.rate_limiter)

| Function | Purpose |
|----------|---------|
| `RateLimitDecision` (class) | Outcome of one rate-limit acquisition attempt. |
| `TokenBucketRateLimiter.try_acquire(*, cost: Decimal = Decimal(1)) -> RateLimitDecision` | Attempt to acquire tokens for one client-side request. |
| `ProviderRateLimiterRegistry.configure_provider(*, provider: str, settings: RateLimitSettings) -> None` | Configure (or replace) the rate limiter for one provider. |
| `ProviderRateLimiterRegistry.is_configured(*, provider: str) -> bool` | Return whether a rate limiter is configured for a provider. |
| `ProviderRateLimiterRegistry.try_acquire(*, provider: str, cost: Decimal = Decimal(1)) -> RateLimitDecision` | Attempt to acquire tokens for a request against one provider. |


## FEAT-TRD-19: Structured trading report and execution-quality event construction (app.services.trading.execution.reporting)

| Function | Purpose |
|----------|---------|
| `ExecutionLatencyEntry.validate_latency_entry() -> ExecutionLatencyEntry` | Validate the latency entry identifier and component consistency. |
| `ReconciliationDiscrepancyEntry.validate_discrepancy_entry() -> ReconciliationDiscrepancyEntry` | Validate discrepancy entry identifiers. |
| `TradingReport.validate_report() -> TradingReport` | Validate trading report identifiers. |
| `build_trading_report(*, report_id: str, generated_at: str, tenant_id: str, positions: tuple[PositionState, ...] = (), orders: tuple[OrderState, ...] = (), execution_latencies: tuple[ExecutionLatencyEntry, ...] = (), cost_entries: tuple[CostAdjustmentEvent, ...] = (), reconciliation_discrepancies: tuple[ReconciliationDiscrepancyEntry, ...] = ()) -> TradingReport` | Construct a structured trading report (TRD-FR-132). |
| `ExecutionQualityEvent.validate_event() -> ExecutionQualityEvent` | Validate execution-quality event identifiers and owner tag. |
| `compute_realized_slippage_bps(*, quote_snapshot: QuoteSnapshot, executed_price: Decimal, side: str) -> Decimal` | Compute realized slippage versus the mandatory quote snapshot. |
| `compute_implementation_shortfall(*, executed_price: Decimal, decision_price: Decimal, side: str) -> Decimal` | Compute direction-adjusted implementation shortfall. |
| `build_execution_quality_event(*, order_id: str, symbol: str, quote_snapshot: QuoteSnapshot, executed_price: Decimal, decision_price: Decimal, side: str, fill_latency_ms: Decimal, partial_fill_count: int, cost_facts: TransactionCostFacts, owner: str = "internal") -> ExecutionQualityEvent` | Build a standardized execution-quality event (TRD-XM-004). |


## FEAT-TRD-20: Broker response and execution event classification primitives (app.services.trading.execution.response_classifier)

| Function | Purpose |
|----------|---------|
| `BrokerOutcomeStatus` (enum) | Classified broker execution outcome status. |
| `BrokerInitiatedEventKind` (enum) | Sub-classification for broker-initiated (non-commanded) events. |
| `CorporateActionKind` (enum) | Corporate action classification. |
| `BrokerOutcomeClassification` (class) | Classified broker execution outcome (TRD-FR-118). |
| `BrokerInitiatedExecutionEvent` (class) | Classified broker-initiated execution event (TRD-FR-120, TRD-FR-122). |
| `CorporateActionEvent.validate_action() -> CorporateActionEvent` | Validate corporate action identifiers and per-kind requirements. |
| `normalize_broker_response(*, provider: str, raw_response: object, request_id: str) -> NormalizedTradeResult` | Convert a provider-specific broker response into a normalized result. |
| `classify_stream_event(*, provider: str, raw_event: object, request_id: str) -> NormalizedTradeResult` | Classify a dynamically pushed WebSocket/FIX execution event. |
| `classify_broker_outcome(*, normalized: NormalizedTradeResult, timed_out: bool = False, transport_disconnected: bool = False, malformed: bool = False) -> BrokerOutcomeClassification` | Classify a normalized broker result into an execution outcome. |
| `classify_broker_initiated_event(*, normalized: NormalizedTradeResult) -> BrokerInitiatedExecutionEvent` | Classify a deal/execution not commanded by this runtime (TRD-FR-120). |
| `classify_corporate_action(*, raw_event: JsonObject) -> CorporateActionEvent` | Classify a corporate-action notification payload (TRD-FR-121). |


## FEAT-TRD-21: Shadow-routing execution comparison primitives (app.services.trading.execution.shadow)

| Function | Purpose |
|----------|---------|
| `ShadowIntentRecord.validate_record() -> ShadowIntentRecord` | Validate shadow intent record identifiers. |
| `ShadowFillComparison` (class) | Comparison of a shadow intent against live market/account evidence. |
| `record_shadow_intent(*, request_id: str, symbol: str, side: str, volume: Decimal, expected_price: Decimal, recorded_at: str, payload: JsonObject \| None = None) -> ShadowIntentRecord` | Record a shadow-route order intent without dispatching to a broker. |
| `compare_shadow_fill(*, intent: ShadowIntentRecord, live_reference_price: Decimal, expected_balance_after: Decimal, live_balance: Decimal) -> ShadowFillComparison` | Compare a recorded shadow intent against live quote/balance evidence. |


## FEAT-TRD-22: Order and position lifecycle state machine primitives (app.services.trading.execution.state_machine)

| Function | Purpose |
|----------|---------|
| `LifecycleKind` (enum) | Entity kind tracked by the state machine. |
| `AmendmentKind` (enum) | Requested amendment kind for version-gated evaluation. |
| `AmendmentOutcome` (enum) | Explicit terminal outcome for a version-gated amendment request. |
| `TransitionRecord.validate_record() -> TransitionRecord` | Validate transition record identifiers. |
| `StateTransitionEvent.validate_event() -> StateTransitionEvent` | Validate state transition event identifiers. |
| `AmendmentResult` (class) | Version-gated amendment evaluation outcome. |
| `TransitionApplyResult` (class) | Outcome of applying one execution report to a transition record. |
| `is_terminal_state(state: FixExecutionState) -> bool` | Return whether a FIX-style lifecycle state is terminal. |
| `validate_transition(*, from_state: FixExecutionState, to_state: FixExecutionState) -> None` | Validate a lifecycle state transition against the canonical table. |
| `initialize_transition_record(*, entity_id: str, kind: LifecycleKind, volume: Decimal, initial_state: FixExecutionState = FixExecutionState.SUBMITTED) -> TransitionRecord` | Build a fresh version-1 transition record for a new order or position. |
| `evaluate_amendment(*, record: TransitionRecord, expected_state_version: int, amendment_kind: AmendmentKind) -> AmendmentResult` | Evaluate a version-gated order amendment request (TRD-FR-129/130). |
| `apply_execution_report(*, record: TransitionRecord, report_state: FixExecutionState, broker_event_id: str, event_source: str, timestamp: str, request_id: str, correlation_id: str, dedup_window_size: int, filled_volume_delta: Decimal = Decimal(0), vwap: Decimal \| None = None) -> TransitionApplyResult` | Apply a broker execution report as an authoritative state transition. |


## FEAT-TRD-23: Shared gate step contracts for the deterministic gate pipeline (app.services.trading.gates._common)

| Function | Purpose |
|----------|---------|
| `GateName` (enum) | Canonical gate identifiers for the 16-step live route pipeline. |
| `GateStepStatus` (enum) | Outcome status for one gate evaluation. |
| `GateStepResult.validate_step_result() -> GateStepResult` | Validate that blocked results always carry a reason code. |
| `passed_step(*, gate: GateName, latency_ms: Decimal = Decimal(0), message: str = "") -> GateStepResult` | Build a passing gate step result. |
| `blocked_step(*, gate: GateName, reason_code: str, message: str, latency_ms: Decimal = Decimal(0)) -> GateStepResult` | Build a blocking gate step result. |
| `diagnostic_skipped_step(*, gate: GateName) -> GateStepResult` | Build a diagnostic-only skipped gate result (TRD-FR-087). |


## FEAT-TRD-24: Operator approval and risk decision binding verification primitives (app.services.trading.gates.approval)

| Function | Purpose |
|----------|---------|
| `ApprovalScope` (class) | Account/strategy/symbol scope for approval matching. |
| `OperatorApprovalToken.validate_token() -> OperatorApprovalToken` | Validate operator approval token identifiers. |
| `RiskDecisionEvidence.validate_evidence() -> RiskDecisionEvidence` | Validate risk decision evidence identifiers. |
| `compute_canonical_request_hash(*, symbol: str, account_id: str, side: str, volume: str, price: str \| None, sl: str \| None, tp: str \| None, route: str, strategy_id: str) -> str` | Compute the canonical SHA-256 request-binding hash (TRD-FR-091). |
| `validate_operator_approval(*, token: OperatorApprovalToken, now: datetime, expected_request_hash: str, expected_scope: ApprovalScope) -> None` | Validate one operator approval token before a governed action (TRD-FR-090). |
| `requires_dual_approval(*, governed_action_id: str, matrix_entry: PolicyMatrixEntry \| None = None) -> bool` | Return whether a governed action requires dual-operator approval. |
| `validate_dual_operator_approval(*, tokens: tuple[OperatorApprovalToken, ...], now: datetime, expected_request_hash: str, expected_scope: ApprovalScope) -> None` | Validate dual-operator approval evidence (TRD-FR-092). |
| `validate_risk_decision(*, evidence: RiskDecisionEvidence, now: datetime, expected_request_hash: str) -> None` | Validate risk decision signature evidence (gate 7). |


## FEAT-TRD-25: Pre-mutation audit recording gate primitive (app.services.trading.gates.audit_and_compensation)

| Function | Purpose |
|----------|---------|
| `record_pre_mutation_audit(*, audit_sink: AuditSink, event: JsonObject, recorded_at: datetime) -> str` | Persist a pre-mutation audit event, blocking on write failure. |


## FEAT-TRD-26: Kill-switch evaluation, dual-control clearing, and durable persistence (app.services.trading.gates.kill_switch)

| Function | Purpose |
|----------|---------|
| `KillSwitchScope` (enum) | Kill-switch activation scope. |
| `OperationalMode` (enum) | Session-wide operational mode. |
| `KillSwitchState` (class) | Durable kill-switch activation record. |
| `KillSwitchEvaluation` (class) | Kill-switch gate evaluation outcome. |
| `evaluate_kill_switches(*, switches: tuple[KillSwitchState, ...], action: TradingAction, policy_entry: PolicyMatrixEntry) -> KillSwitchEvaluation` | Evaluate active kill switches against a requested action (TRD-FR-097). |
| `clear_kill_switch_after_approval(*, current: KillSwitchState, tokens: tuple[OperatorApprovalToken, ...], now: datetime, expected_request_hash: str, expected_scope: ApprovalScope) -> KillSwitchState` | Clear a kill switch after validated governance approval (TRD-FR-098). |
| `restore_kill_switch_state(*, state_store: TradingStateStore, route: TradingRoute, tenant_id: str, snapshot_id: str) -> tuple[KillSwitchState, ...]` | Restore durable kill-switch state before the first gate evaluation. |
| `persist_kill_switch_state(*, state_store: TradingStateStore, route: TradingRoute, tenant_id: str, switches: tuple[KillSwitchState, ...], expected_version: int \| None) -> str` | Durably persist kill-switch state (TRD-FR-100). |


## FEAT-TRD-27: Concrete 16-step live gate pipeline with broker dispatch (BF-TRD-003) (app.services.trading.gates.live_pipeline)

| Function | Purpose |
|----------|---------|
| `passthrough_risk_evaluator() -> GateStepResult` | Pass the RISK_DECISION gate without evaluating risk (BF-TRD-004). |
| `DispatchOutcome` (dataclass) | Mutable holder for the result of the DISPATCH gate. |
| `LiveGateEvidence` (dataclass) | Caller-supplied evidence bundle for one live gate pipeline evaluation. |
| `LiveGatePipelineImpl.evaluate(request: TradingRequestEnvelope) -> TradingResponseEnvelope` | Run the 16-step live gate pipeline and dispatch when every gate passes. |
| `build_live_gate_pipeline(*, clock: Clock, tenant_id: str, evidence: LiveGateEvidence, policy_matrix: PolicyMatrix, session_manager: SessionManager, turbulence_monitor: MarketTurbulenceMonitor, idempotency_store: IdempotencyStore, lock_manager: ConcurrencyLockManager, authority_guard: AuthorityAndRetryGuard, audit_sink: AuditSink, trade_store: TradeStore, dispatch_executor: AsyncDispatchExecutor, risk_evaluator: Callable[[], GateStepResult], dispatch_callable_factory: Callable[[JsonObject, str], Callable[[], NormalizedTradeResult]] \| None = None, **kwargs: object) -> LiveGatePipelineImpl` | Build a live gate pipeline wired to the active broker by default. |


## FEAT-TRD-28: Canonical live-route gate pipeline orchestrator (app.services.trading.gates.pipeline)

| Function | Purpose |
|----------|---------|
| `ComplianceEvidence` (class) | Compliance restricted-symbol list evidence. |
| `GatePipelineDecision` (class) | Aggregate outcome of one gate pipeline evaluation. |
| `evaluate_compliance_gate(*, evidence: ComplianceEvidence, symbol: str \| None) -> GateStepResult` | Evaluate the compliance restricted-symbol gate (TRD-FR-084). |
| `MarketTurbulenceMonitor.is_suspended(*, symbol: str) -> bool` | Return whether a symbol is currently suspended for turbulence. |
| `MarketTurbulenceMonitor.resume(*, symbol: str) -> None` | Resume a previously suspended symbol. |
| `MarketTurbulenceMonitor.observe(*, symbol: str, mid_price: Decimal) -> GateStepResult` | Observe a new mid-price and evaluate the turbulence gate. |
| `evaluate_adapter_permission_gate(*, profile: BrokerCapabilityProfile, order_type: str, filling_mode: str, price: Decimal, volume: Decimal) -> GateStepResult` | Evaluate adapter permission/capability as gate 15. |
| `evaluate_seam_gate(*, gate: GateName, evaluator: Callable[[], GateStepResult] \| None) -> GateStepResult` | Evaluate a gate whose backing module is future work. |
| `compute_effective_deadline(*, request: TradingRequestEnvelope, clock: Clock, default_budget_ms: Decimal) -> datetime` | Resolve the effective pipeline deadline (TRD-FR-088). |
| `run_gate_pipeline(*, steps: tuple[GateStep, ...], clock: Clock, deadline: datetime, quote_snapshot: QuoteSnapshot \| None = None, quote_ttl_ms: int \| None = None) -> GatePipelineDecision` | Run an ordered sequence of gate steps with short-circuit enforcement. |


## FEAT-TRD-29: Trading gate policy matrix resolution primitives (app.services.trading.gates.policy_matrix)

| Function | Purpose |
|----------|---------|
| `PolicyMatrixEntry` (class) | Governed-action policy rule set. |
| `PolicyMatrix` (class) | Injected registry of policy matrix entries keyed by action. |
| `resolve_policy(*, matrix: PolicyMatrix, action: TradingAction) -> PolicyMatrixEntry` | Resolve the policy matrix entry for a governed action (TRD-FR-089). |


## FEAT-TRD-30: Broker readiness and clock synchronization gate primitives (app.services.trading.gates.readiness)

| Function | Purpose |
|----------|---------|
| `BrokerReadinessEvidence` (class) | Broker readiness evidence resolved by the caller (TRD-FR-093). |
| `ClockDriftEvidence` (class) | Clock synchronization and PTP latency evidence (TRD-FR-094/095). |
| `ReadinessCheckResult` (class) | Non-mutating live readiness dry run outcome (TRD-FR-096). |
| `validate_broker_readiness(*, evidence: BrokerReadinessEvidence) -> None` | Validate broker connection, trading allowance, and rate capacity. |
| `validate_clock_drift(*, evidence: ClockDriftEvidence) -> None` | Validate local clock drift and optional PTP end-to-end latency. |
| `run_live_readiness_dry_run(*, broker_evidence: BrokerReadinessEvidence, clock_evidence: ClockDriftEvidence, symbol_metadata_present: bool, stores_durable: bool) -> ReadinessCheckResult` | Run a non-mutating live readiness dry run (TRD-FR-096). |


## FEAT-TRD-31: MQL5-compatible HistoryOrderInfo class wrapping history order properties (app.services.trading.history_order_info)

| Function | Purpose |
|----------|---------|
| `HistoryOrderInfo.__init__(ticket: int \| None = None) -> None` | Initialize the HistoryOrderInfo helper. |
| `HistoryOrderInfo.ticket() -> int` | Get the ticket of the history order. |
| `HistoryOrderInfo.time_setup() -> int` | Get the setup time of the history order. |
| `HistoryOrderInfo.time_setup_msc() -> int` | Get the setup time in milliseconds. |
| `HistoryOrderInfo.time_expiration() -> int` | Get the expiration time of the history order. |
| `HistoryOrderInfo.time_done() -> int` | Get the execution/cancellation time of the history order. |
| `HistoryOrderInfo.time_done_msc() -> int` | Get the done time in milliseconds. |
| `HistoryOrderInfo.type() -> int` | Get the type of the history order. |
| `HistoryOrderInfo.type_description() -> str` | Get the description of the order type. |
| `HistoryOrderInfo.type_time() -> int` | Get the expiration type of the history order. |
| `HistoryOrderInfo.type_time_description() -> str` | Get description of the expiration type. |
| `HistoryOrderInfo.type_filling() -> int` | Get execution type of the history order. |
| `HistoryOrderInfo.type_filling_description() -> str` | Get description of execution type. |
| `HistoryOrderInfo.state() -> int` | Get status of the history order. |
| `HistoryOrderInfo.state_description() -> str` | Get description of the order status. |
| `HistoryOrderInfo.magic() -> int` | Get the magic number of the history order. |
| `HistoryOrderInfo.position_id() -> int` | Get the associated position ID. |
| `HistoryOrderInfo.position_by_id() -> int` | Get the associated position ID by which order was placed. |
| `HistoryOrderInfo.volume_initial() -> float` | Get the initial volume of the history order. |
| `HistoryOrderInfo.volume_current() -> float` | Get the current volume of the history order. |
| `HistoryOrderInfo.price_open() -> float` | Get the price level of the history order. |
| `HistoryOrderInfo.stop_loss() -> float` | Get the Stop Loss level. |
| `HistoryOrderInfo.take_profit() -> float` | Get the Take Profit level. |
| `HistoryOrderInfo.price_current() -> float` | Get the current price of the symbol. |
| `HistoryOrderInfo.price_stop_limit() -> float` | Get the stop limit price. |
| `HistoryOrderInfo.symbol() -> str` | Get the symbol of the history order. |
| `HistoryOrderInfo.comment() -> str` | Get the comment of the history order. |
| `HistoryOrderInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `HistoryOrderInfo.info_double(prop_id: int) -> float` | Get generic double property. |
| `HistoryOrderInfo.info_string(prop_id: int) -> str` | Get generic string property. |


## FEAT-TRD-32: Idempotency service implementation (app.services.trading.idempotency)

| Function | Purpose |
|----------|---------|
| `IdempotencyService.__init__(store: TradeStore) -> None` | Initialize IdempotencyService with a TradeStore instance. |
| `IdempotencyService.generate_key(account_id: str, symbol: str, action_type: int, volume: float, price: float, slippage: int, window_seconds: int = 10) -> str` | Generate a deterministic idempotency key. |
| `IdempotencyService.check_duplicate(key: str) -> dict[str, Any] \| None` | Query store for an existing record matching the key. |
| `IdempotencyService.register_in_progress(key: str, request_data: dict[str, Any], ttl_seconds: int = 60) -> None` | Mark the key as 'in_progress' in the store. |
| `IdempotencyService.register_completed(key: str, result_dict: dict[str, Any], ttl_seconds: int = 86400) -> None` | Mark the key as 'completed' and store the execution result. |


## FEAT-TRD-33: Shared helpers for trading read-only info facades (app.services.trading.info._common)

| Function | Purpose |
|----------|---------|
| `broker_call(name: str, *args: object, **kwargs: object) -> object` | Call a read-only broker information function. |
| `first_or_none(value: object) -> object \| None` | Return the first item from a broker collection. |
| `iter_or_empty(value: object) -> tuple[object, ...]` | Return a type-narrowed tuple view of a broker collection. |
| `safe_attr(data: object \| None, name: str, default: T, caster: Callable[..., T]) -> T` | Read and cast a broker attribute with a neutral fallback. |
| `redacted_info_payload(payload: JsonObject) -> JsonObject` | Redact an exported info payload. |


## FEAT-TRD-34: Shared ticket-based read-only info facade base (app.services.trading.info._ticket)

| Function | Purpose |
|----------|---------|
| `TicketInfoFacade.select(ticket: int) -> bool` | Select a record by ticket using a read-only broker query. |
| `TicketInfoFacade.ticket() -> int` | Return record ticket. |
| `TicketInfoFacade.time() -> int` | Return record time. |
| `TicketInfoFacade.time_msc() -> int` | Return record millisecond time. |
| `TicketInfoFacade.type() -> int` | Return record type. |
| `TicketInfoFacade.type_description() -> str` | Return record type description. |
| `TicketInfoFacade.magic() -> int` | Return magic number. |
| `TicketInfoFacade.position_id() -> int` | Return associated position ID. |
| `TicketInfoFacade.volume() -> float` | Return record volume. |
| `TicketInfoFacade.price() -> float` | Return record price. |
| `TicketInfoFacade.symbol() -> str` | Return record symbol. |
| `TicketInfoFacade.comment() -> str` | Return record comment. |
| `TicketInfoFacade.info_integer(prop_id: int) -> int` | Return integer property. |
| `TicketInfoFacade.info_double(prop_id: int) -> float` | Return float property. |
| `TicketInfoFacade.info_string(prop_id: int) -> str` | Return string property. |
| `TicketInfoFacade.payload() -> JsonObject` | Return a redacted ticket record payload. |


## FEAT-TRD-35: Read-only account information facade (app.services.trading.info.account)

| Function | Purpose |
|----------|---------|
| `AccountInfo.__init__() -> None` | Initialize the AccountInfo instance. |
| `AccountInfo.login() -> int` | Return account login number. |
| `AccountInfo.trade_mode() -> int` | Get trading account mode (0=Demo, 1=Contest, 2=Real). |
| `AccountInfo.trade_mode_description() -> str` | Return account trade mode description. |
| `AccountInfo.leverage() -> int` | Return account leverage. |
| `AccountInfo.limit_orders() -> int` | Get maximum allowed pending orders count. |
| `AccountInfo.trade_allowed() -> bool` | Check if trading is allowed for this account. |
| `AccountInfo.trade_expert() -> bool` | Check if Expert Advisor trading is allowed for this account. |
| `AccountInfo.margin_so_mode() -> int` | Return stop-out mode. |
| `AccountInfo.margin_mode() -> int` | Get margin calculation mode (0=hedging, 1=netting). |
| `AccountInfo.margin_mode_description() -> str` | Get margin mode description string. |
| `AccountInfo.balance() -> float` | Return account balance. |
| `AccountInfo.credit() -> float` | Get account credit value. |
| `AccountInfo.profit() -> float` | Get current account floating profit. |
| `AccountInfo.equity() -> float` | Get current account equity. |
| `AccountInfo.margin() -> float` | Get current account used margin. |
| `AccountInfo.free_margin() -> float` | Get account free margin. |
| `AccountInfo.free_margin_mode() -> int` | Get free margin calculation mode. |
| `AccountInfo.margin_level() -> float` | Get account margin level percentage. |
| `AccountInfo.margin_so_level() -> float` | Get stop out level value. |
| `AccountInfo.name() -> str` | Return account holder name. |
| `AccountInfo.server() -> str` | Get trading server name. |
| `AccountInfo.currency() -> str` | Get account currency name. |
| `AccountInfo.company() -> str` | Get broker company name. |
| `AccountInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `AccountInfo.info_double(prop_id: int) -> float` | Get generic double property. |
| `AccountInfo.info_string(prop_id: int) -> str` | Get generic string property. |
| `AccountInfo.payload() -> JsonObject` | Return a redacted account metadata payload. |


## FEAT-TRD-36: Read-only historical deal facade (app.services.trading.info.deal)

| Function | Purpose |
|----------|---------|
| `DealInfo.__init__(ticket: int \| None = None) -> None` | Initialize the DealInfo helper. |
| `DealInfo.select(ticket: int) -> bool` | Select a history deal by ticket. |
| `DealInfo.ticket() -> int` | Get the ticket of the deal. |
| `DealInfo.order() -> int` | Get the ticket of the order that initiated the deal. |
| `DealInfo.time() -> int` | Get the deal execution time. |
| `DealInfo.time_msc() -> int` | Get the deal execution time in milliseconds. |
| `DealInfo.type() -> int` | Get the deal type (0=Buy, 1=Sell). |
| `DealInfo.type_description() -> str` | Get description of the deal type. |
| `DealInfo.entry() -> int` | Get the deal entry type (0=In, 1=Out, 2=InOut, 3=OutBy). |
| `DealInfo.entry_description() -> str` | Get description of the deal entry type. |
| `DealInfo.magic() -> int` | Get the magic number of the deal. |
| `DealInfo.position_id() -> int` | Get the associated position ID. |
| `DealInfo.volume() -> float` | Get the volume of the deal. |
| `DealInfo.price() -> float` | Get the price of the deal. |
| `DealInfo.commission() -> float` | Get the commission of the deal. |
| `DealInfo.swap() -> float` | Get the swap of the deal. |
| `DealInfo.profit() -> float` | Get the gross profit of the deal. |
| `DealInfo.symbol() -> str` | Get the symbol of the deal. |
| `DealInfo.comment() -> str` | Get the comment of the deal. |
| `DealInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `DealInfo.info_double(prop_id: int) -> float` | Get generic double property. |
| `DealInfo.info_string(prop_id: int) -> str` | Get generic string property. |


## FEAT-TRD-37: Read-only historical order facade (app.services.trading.info.history_order)

| Function | Purpose |
|----------|---------|
| `HistoryOrderInfo.select(ticket: int) -> bool` | Select a historical order by ticket. |


## FEAT-TRD-38: Read-only pending order facade (app.services.trading.info.order)

| Function | Purpose |
|----------|---------|
| `OrderInfo.__init__(ticket: int \| None = None) -> None` | Initialize the OrderInfo helper. |
| `OrderInfo.select(ticket: int) -> bool` | Select a pending order by ticket. |
| `OrderInfo.ticket() -> int` | Get the ticket of the pending order. |
| `OrderInfo.time_setup() -> int` | Get the setup time of the pending order. |
| `OrderInfo.time_setup_msc() -> int` | Get the setup time in milliseconds. |
| `OrderInfo.time_expiration() -> int` | Get the expiration time of the pending order. |
| `OrderInfo.time_done() -> int` | Get the execution/cancellation time of the pending order. |
| `OrderInfo.time_done_msc() -> int` | Get the done time in milliseconds. |
| `OrderInfo.type() -> int` | Get the type of the pending order. |
| `OrderInfo.type_description() -> str` | Get the description of the order type. |
| `OrderInfo.type_time() -> int` | Get the expiration type of the pending order. |
| `OrderInfo.type_time_description() -> str` | Get description of the expiration type. |
| `OrderInfo.type_filling() -> int` | Get execution type of the pending order. |
| `OrderInfo.type_filling_description() -> str` | Get description of execution type. |
| `OrderInfo.state() -> int` | Get status of the pending order. |
| `OrderInfo.state_description() -> str` | Get description of the order status. |
| `OrderInfo.magic() -> int` | Get the magic number of the pending order. |
| `OrderInfo.position_id() -> int` | Get the associated position ID. |
| `OrderInfo.position_by_id() -> int` | Get the associated position ID by which order was placed. |
| `OrderInfo.volume_initial() -> float` | Get the initial volume of the pending order. |
| `OrderInfo.volume_current() -> float` | Get the current volume of the pending order. |
| `OrderInfo.price_open() -> float` | Get the price level of the pending order. |
| `OrderInfo.stop_loss() -> float` | Get the Stop Loss level. |
| `OrderInfo.take_profit() -> float` | Get the Take Profit level. |
| `OrderInfo.price_current() -> float` | Get the current price of the symbol. |
| `OrderInfo.price_stop_limit() -> float` | Get the stop limit price. |
| `OrderInfo.symbol() -> str` | Get the symbol of the pending order. |
| `OrderInfo.comment() -> str` | Get the comment of the pending order. |
| `OrderInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `OrderInfo.info_double(prop_id: int) -> float` | Get generic double property. |
| `OrderInfo.info_string(prop_id: int) -> str` | Get generic string property. |


## FEAT-TRD-39: Read-only open position facade (app.services.trading.info.position)

| Function | Purpose |
|----------|---------|
| `PositionInfo.__init__(ticket: int \| None = None) -> None` | Initialize the PositionInfo helper. |
| `PositionInfo.select(symbol: str) -> bool` | Select an open position by symbol using a read-only query. |
| `PositionInfo.select_by_ticket(ticket: int) -> bool` | Select an open position by ticket using a read-only query. |
| `PositionInfo.ticket() -> int` | Get the ticket of the open position. |
| `PositionInfo.time() -> int` | Get the open time of the position. |
| `PositionInfo.time_msc() -> int` | Get the open time in milliseconds. |
| `PositionInfo.time_update() -> int` | Get the update time of the position. |
| `PositionInfo.time_update_msc() -> int` | Return position millisecond update time. |
| `PositionInfo.type() -> int` | Get the type of the position (0=Buy, 1=Sell). |
| `PositionInfo.type_description() -> str` | Get the description of the position type. |
| `PositionInfo.magic() -> int` | Get the magic number of the position. |
| `PositionInfo.identifier() -> int` | Get the position identifier. |
| `PositionInfo.volume() -> float` | Get the current volume of the position. |
| `PositionInfo.price_open() -> float` | Get the open price of the position. |
| `PositionInfo.stop_loss() -> float` | Get the Stop Loss level. |
| `PositionInfo.take_profit() -> float` | Get the Take Profit level. |
| `PositionInfo.price_current() -> float` | Get the current price of the symbol. |
| `PositionInfo.swap() -> float` | Get the accumulated swap of the position. |
| `PositionInfo.profit() -> float` | Get the current floating profit of the position. |
| `PositionInfo.symbol() -> str` | Get the symbol of the position. |
| `PositionInfo.comment() -> str` | Get the comment of the position. |
| `PositionInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `PositionInfo.info_double(prop_id: int) -> float` | Return position float property. |
| `PositionInfo.info_string(prop_id: int) -> str` | Get generic string property. |


## FEAT-TRD-40: Read-only symbol information facade (app.services.trading.info.symbol)

| Function | Purpose |
|----------|---------|
| `SymbolInfo.__init__(name: str \| None = None) -> None` | Initialize the SymbolInfo instance. |
| `SymbolInfo.name(name: str \| None = None) -> str \| bool` | Get or set the local symbol name without broker mutation. |
| `SymbolInfo.refresh() -> bool` | Refresh symbol specifications from broker. |
| `SymbolInfo.refresh_rates() -> bool` | Refresh current prices (bid/ask). |
| `SymbolInfo.select(select: bool) -> bool` | Validate local symbol selection without broker mutation. |
| `SymbolInfo.is_synchronized() -> bool` | Return whether read-only symbol data is synchronized. |
| `SymbolInfo.digits() -> int` | Get symbol decimal digits. |
| `SymbolInfo.point() -> float` | Get symbol point value (1 / 10^digits). |
| `SymbolInfo.tick_size() -> float` | Return symbol tick size. |
| `SymbolInfo.trade_mode() -> int` | Return symbol trade mode. |
| `SymbolInfo.trade_mode_description() -> str` | Return symbol trade mode description. |
| `SymbolInfo.contract_size() -> float` | Return symbol contract size. |
| `SymbolInfo.volume_min() -> float` | Get minimum allowed order volume. |
| `SymbolInfo.volume_max() -> float` | Get maximum allowed order volume. |
| `SymbolInfo.volume_step() -> float` | Get minimum lot volume step. |
| `SymbolInfo.swap_mode() -> int` | Get symbol swap mode. |
| `SymbolInfo.swap_long() -> float` | Get swap value for long positions. |
| `SymbolInfo.swap_short() -> float` | Get swap value for short positions. |
| `SymbolInfo.bid() -> float` | Get current bid price. |
| `SymbolInfo.ask() -> float` | Get current ask price. |
| `SymbolInfo.last() -> float` | Get current last transaction price. |
| `SymbolInfo.spread() -> int` | Get current spread in points. |
| `SymbolInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `SymbolInfo.info_double(prop_id: int) -> float` | Get generic double property. |
| `SymbolInfo.info_string(prop_id: int) -> str` | Get generic string property. |
| `SymbolInfo.payload() -> JsonObject` | Return a redacted symbol payload. |


## FEAT-TRD-41: Read-only terminal information facade (app.services.trading.info.terminal)

| Function | Purpose |
|----------|---------|
| `TerminalInfo.__init__() -> None` | Initialize the TerminalInfo instance. |
| `TerminalInfo.language() -> str` | Return terminal language. |
| `TerminalInfo.company() -> str` | Get broker company name. |
| `TerminalInfo.name() -> str` | Return terminal name. |
| `TerminalInfo.path() -> str` | Return terminal executable path. |
| `TerminalInfo.data_path() -> str` | Get terminal data folder path. |
| `TerminalInfo.common_data_path() -> str` | Return terminal common data path. |
| `TerminalInfo.build() -> int` | Get terminal build number. |
| `TerminalInfo.connected() -> bool` | Check if terminal is connected to the trade server. |
| `TerminalInfo.trade_allowed() -> bool` | Check if trading is allowed for the terminal. |
| `TerminalInfo.dlls_allowed() -> bool` | Return terminal DLL permission state. |
| `TerminalInfo.ping_last() -> int` | Get last ping time to trade server. |
| `TerminalInfo.info_integer(prop_id: int) -> int` | Get generic integer property. |
| `TerminalInfo.info_string(prop_id: int) -> str` | Get generic string property. |
| `TerminalInfo.payload() -> JsonObject` | Return a redacted terminal payload. |


## FEAT-TRD-42: Periodic liveness heartbeat emission to external watchdog nodes (app.services.trading.monitoring.heartbeat_watchdog)

| Function | Purpose |
|----------|---------|
| `HeartbeatEmitter.send_heartbeat(status: str = "HEALTHY") -> bool` | Send a liveness heartbeat payload to the external watchdog node. |
| `HeartbeatEmitter.last_heartbeat_time -> datetime \| None (property)` | Get last successful heartbeat time. |
| `HeartbeatEmitter.last_success -> bool (property)` | Get last status of heartbeat send. |


## FEAT-TRD-43: Declare severity signals taxonomy, rate limiting, and escalation runbooks (app.services.trading.monitoring.operational_signals)

| Function | Purpose |
|----------|---------|
| `IncidentSignal` (dataclass) | Represents an operational monitoring incident signal. |
| `OperationalSignalsManager.emit_signal(incident_id: str, incident_class: str, severity: str, message: str) -> IncidentSignal \| None` | Emit an operational signal with rate limiting and runbook lookup. |
| `OperationalSignalsManager.acknowledge_incident(incident_id: str) -> bool` | Acknowledge a pending active incident, stopping the escalation chain. |
| `OperationalSignalsManager.check_escalations(window_seconds: float = 60.0) -> list[dict[str, Any]]` | Scan active unacknowledged high/critical incidents for escalation. |
| `OperationalSignalsManager.audit_log -> list[IncidentSignal] (property)` | Return full audit log. |


## FEAT-TRD-44: Monitoring and Health Coordination Service (app.services.trading.monitoring.service)

| Function | Purpose |
|----------|---------|
| `MonitoringService.record_broker_success(latency_ms: float) -> None` | Record a successful broker action, updating health metrics. |
| `MonitoringService.record_broker_reject() -> None` | Record a broker command rejection. |
| `MonitoringService.record_unknown_outcome() -> None` | Record a transaction resulting in an unknown outcome. |
| `MonitoringService.record_reconciliation_mismatch(details: str = "") -> None` | Record a reconciliation state mismatch breach. |
| `MonitoringService.record_stream_gap() -> None` | Record a stream or sequence gap incident. |
| `MonitoringService.record_durability_failure() -> None` | Record a persistence or audit write durability failure. |
| `MonitoringService.run_stale_order_check(active_orders: list[dict[str, Any]], reconciliation_service: ReconciliationService, route: TradingRoute, tenant_id: str, account_id: str) -> list[str]` | Verify active orders for staleness and transition status. |
| `MonitoringService.run_heartbeat_cycle() -> bool` | Trigger dead man's switch heartbeat emission to external node. |
| `MonitoringService.reset_circuit_breaker() -> None` | Reset operational circuit breaker and reset counts. |
| `MonitoringService.get_monitoring_status() -> dict[str, Any]` | Aggregate status metrics into a structured health status event. |
| `MonitoringService.circuit_breaker_tripped -> bool (property)` | Check if circuit breaker is tripped. |
| `MonitoringService.current_capability -> str (property)` | Get current route execution capability. |


## FEAT-TRD-45: Track execution latency statistics and implement the lost-order recovery watchdog (app.services.trading.monitoring.timeouts_and_staleness)

| Function | Purpose |
|----------|---------|
| `LatencyTracker.record_latency(latency_ms: float) -> None` | Record a single latency observation in milliseconds. |
| `LatencyTracker.get_p95_latency() -> float` | Calculate the 95th percentile execution latency. |
| `LatencyTracker.samples -> list[float] (property)` | Return the current sample list. |
| `LostOrderWatchdog.check_stale_orders(active_orders: list[dict[str, Any]], reconciliation_service: ReconciliationService, route: TradingRoute, tenant_id: str, account_id: str) -> list[str]` | Verify active orders and flag those exceeding life-to-live as stale. |


## FEAT-TRD-46: Degrade tool health status dynamically after consecutive timeouts (app.services.trading.monitoring.tool_health)

| Function | Purpose |
|----------|---------|
| `ToolHealthMonitor.record_success() -> None` | Record a successful tool execution. |
| `ToolHealthMonitor.record_failure(error_message: str = "") -> None` | Record a tool execution timeout or adapter failure. |
| `ToolHealthMonitor.status -> ToolStatus (property)` | Get the current tool health status. |
| `ToolHealthMonitor.consecutive_failures -> int (property)` | Get the current count of consecutive failures. |
| `ToolHealthMonitor.is_healthy -> bool (property)` | Check if the tool is healthy. |


## FEAT-TRD-47: Runtime permission checks for strategy lifecycle state (app.services.trading.permissions)

| Function | Purpose |
|----------|---------|
| `StrategyPermissionError` (model) | Raised when a strategy lifecycle state does not permit a runtime context. |
| `StrategyRuntimePermissionService.__init__(db_manager: DatabaseManager \| None = None, governance_repository: GovernanceRepository \| None = None) -> None` | Initialize the service with database and governance dependencies. |
| `StrategyRuntimePermissionService.assert_strategy_allowed(*, strategy_id: int, context: StrategyRuntimeContext) -> None` | Assert a strategy may run in the requested runtime context. |
| `assert_strategy_allowed(strategy_id: int, context: StrategyRuntimeContext, *, db_manager: DatabaseManager \| None = None, governance_repository: GovernanceRepository \| None = None) -> None` | Convenience wrapper for one-off runtime permission checks. |


## FEAT-TRD-48: Promotion ladder stages and transition validation logic (app.services.trading.promotion.ladder)

| Function | Purpose |
|----------|---------|
| `validate_route_stage_capability(route: TradingRoute, stage: PromotionStage, capability: MutationCapability) -> None` | Validate route, promotion stage, and mutation capability compatibility. |
| `evaluate_promotion_stage_gate(*, request: TradingRequestEnvelope) -> GateStepResult` | Evaluate the route/promotion stage compatibility check (Gate 3). |
| `compute_canonical_promotion_hash(*, strategy_id: str, current_stage: PromotionStage, target_stage: PromotionStage) -> str` | Compute canonical hash of promotion request parameters (TRD-FR-183). |
| `validate_promotion_transition(*, strategy_id: str, current_stage: PromotionStage, target_stage: PromotionStage, approvals: tuple[OperatorApprovalToken, ...], clock: Clock, risk_policy_ok: bool, reconciliation_state_ok: bool, audit_sinks_ok: bool) -> None` | Validate a promotion ladder stage transition (TRD-FR-183, TRD-FR-184). |


## FEAT-TRD-49: Pre-activation conditions and simulation route metadata lookup validations (app.services.trading.promotion.preconditions)

| Function | Purpose |
|----------|---------|
| `validate_preactivation_conditions(*, route: TradingRoute, stage: PromotionStage, active_kill_switches: bool, reconciliation_blocked: bool, context_is_stale: bool, security_profile_missing: bool) -> None` | Validate pre-activation conditions for live routes (TRD-FR-185). |
| `validate_sim_metadata_lookup(*, mode: str, has_captured_snapshot: bool) -> None` | Validate broker metadata lookups in the simulation route (TRD-FR-186). |


## FEAT-TRD-50: RateLimiter service for broker api throttling (app.services.trading.rate_limiter)

| Function | Purpose |
|----------|---------|
| `RateLimiter.__init__(capacity: float = 10.0, fill_rate: float = 2.0) -> None` | Initialize the RateLimiter. |
| `RateLimiter.check_rate_limit() -> bool` | Check if at least one token is available without consuming it. |
| `RateLimiter.acquire(tokens: float = 1.0) -> bool` | Consume tokens from the bucket. |
| `RateLimiter.get_status() -> dict[str, Any]` | Get the current rate limiter state. |
| `get_rate_limiter(provider: str) -> RateLimiter` | Get or create the RateLimiter singleton instance for a given provider. |


## FEAT-TRD-51: ReadinessService implementation for checking trade readiness (app.services.trading.readiness)

| Function | Purpose |
|----------|---------|
| `ReadinessService.run_execution_readiness_check(provider: str, symbol: str, term: TerminalInfo, acc: AccountInfo) -> dict[str, Any]` | Aggregate readiness checks before trade execution. |


## FEAT-TRD-52: Reconciliation service implementation (app.services.trading.reconciliation)

| Function | Purpose |
|----------|---------|
| `ReconciliationService.__init__(store: TradeStore) -> None` | Initialize ReconciliationService. |
| `ReconciliationService.set_block_trading_on_startup(block: bool) -> None` | Set whether trading is blocked until initial reconciliation passes. |
| `ReconciliationService.reconcile(live_positions: list[dict[str, Any]], live_orders: list[dict[str, Any]], account_equity: float = 100000.0) -> dict[str, Any]` | Perform reconciliation pass comparing local store to live broker state. |


## FEAT-TRD-53: Authority and retry guard for state reconciliation (app.services.trading.reconciliation.authority_and_retry_guard)

| Function | Purpose |
|----------|---------|
| `AuthorityAndRetryGuard.transition_to_unresolved(account_id: str, symbol: str \| None, request_id: str) -> None` | Transition a scope to UNRESOLVED status due to an unknown outcome. |
| `AuthorityAndRetryGuard.resolve_scope(account_id: str, symbol: str \| None) -> None` | Resolve a previously blocked scope. |
| `AuthorityAndRetryGuard.is_blocked(account_id: str, symbol: str) -> bool` | Return whether mutations are blocked for the given scope. |
| `AuthorityAndRetryGuard.report_stream_gap(account_id: str, symbol: str \| None) -> None` | Report a stream-gap incident, immediately halting mutations. |
| `AuthorityAndRetryGuard.process_event_id(broker_event_id: str) -> bool` | Record event ID and return whether it is a duplicate. |
| `evaluate_reconciliation_authority_gate(*, guard: AuthorityAndRetryGuard, account_id: str, symbol: str) -> GateStepResult` | Evaluate the reconciliation authority gate step (Gate 13). |


## FEAT-TRD-54: Reconciliation service for orchestrating state syncs and authority policies (app.services.trading.reconciliation.service)

| Function | Purpose |
|----------|---------|
| `ReconciliationReport` (class) | Report summarizing the outcome of a reconciliation run. |
| `ReconciliationService.run_reconciliation(*, route: TradingRoute, tenant_id: str, account_id: str, run_type: str) -> ReconciliationReport` | Execute a state reconciliation check. |


## FEAT-TRD-55: State snapshot comparison logic for trading reconciliation (app.services.trading.reconciliation.snapshots_and_compare)

| Function | Purpose |
|----------|---------|
| `compare_snapshots(*, local_orders: list[JsonObject], broker_orders: list[JsonObject], local_positions: list[JsonObject], broker_positions: list[JsonObject], local_balance: Decimal, broker_balance: Decimal, local_margin: Decimal, broker_margin: Decimal, price_drift_threshold: Decimal, volume_drift_threshold: Decimal, balance_drift_threshold: Decimal, margin_drift_threshold: Decimal, clock: Clock) -> list[ReconciliationDiscrepancyEntry]` | Compare local states against broker snapshots. |


## FEAT-TRD-56: ReportingService implementation (app.services.trading.reporting)

| Function | Purpose |
|----------|---------|
| `ReportingService.build_report(store: TradeStore, reconciliation_summary: dict[str, Any] \| None = None, validation_warnings: list[str] \| None = None) -> dict[str, Any]` | Aggregate data to form a structured trading report. |


## FEAT-TRD-57: Result builders and response normalizers (app.services.trading.result)

| Function | Purpose |
|----------|---------|
| `NormalizedTradeResult.__init__(retcode: int, deal: int, order: int, volume: float, price: float, bid: float, ask: float, comment: str, filled_volume: float = 0.0, average_price: float = 0.0, remaining_volume: float = 0.0, request_id: str = '', correlation_id: str = '', trace_id: str = '') -> None` | Initialize NormalizedTradeResult. |
| `NormalizedTradeResult.to_dict() -> dict[str, Any]` | Convert result to dictionary. |
| `BrokerResponseNormalizer.normalize_response(provider: str, raw_result: Any) -> NormalizedTradeResult` | Normalize raw results from different brokers. |
| `ResultBuilder.success(provider: str, raw_result: Any) -> NormalizedTradeResult` | Create a successful normalized result wrapper. |
| `ResultBuilder.failure(comment: str, retcode: int = 10001) -> NormalizedTradeResult` | Create a failure normalized result wrapper. |


## FEAT-TRD-58: Concurrency lock and strategy ownership coordination services (app.services.trading.runtime.coordination)

| Function | Purpose |
|----------|---------|
| `ConcurrencyLockManager.acquire_lock(account_id: str, symbol: str, timeout: float = 1.0) -> bool` | Acquire a concurrency lock with timeout and queue-based backpressure. |
| `ConcurrencyLockManager.release_lock(account_id: str, symbol: str) -> None` | Release the concurrency lock for (account_id, symbol). |
| `StrategyOwnershipValidator.validate_ownership(*, record_strategy_id: str, request_strategy_id: str, policy_matrix: object = None) -> None` | Verify strategy ownership constraints (TRD-FR-075). |
| `CrossStrategyPolicyEvaluator.detect_opposing_orders_or_positions(*, request_strategy_id: str, account_id: str, symbol: str, request_side: str, working_orders: list[JsonObject], active_positions: list[JsonObject], policy_matrix: object = None) -> str` | Detect when strategy A mutations oppose strategy B working orders/positions. |


## FEAT-TRD-59: Cost control and budget verification service (app.services.trading.runtime.cost_control)

| Function | Purpose |
|----------|---------|
| `CostController.validate_pre_dispatch_budget(*, request: TradingRequestEnvelope, estimated_cost: Decimal, limits: dict[str, Decimal]) -> None` | Check estimated cost against budget limits before broker dispatch. |
| `CostController.record_cost(*, request: TradingRequestEnvelope, actual_cost: Decimal, limits: dict[str, Decimal], post_dispatch: bool = False) -> None` | Accumulate cost and raise critical incident if limits are breached. |
| `CostController.reset_accumulated_costs() -> None` | Reset all accumulated cost state statistics. |


## FEAT-TRD-60: Session manager coordinating runtime states, heartbeats, and watchdogs (app.services.trading.runtime.session_manager)

| Function | Purpose |
|----------|---------|
| `SessionState` (enum) | Session lifecycle states. |
| `SessionManager.state -> SessionState (property)` | Return the current session state. |
| `SessionManager.mode -> OperationalMode (property)` | Return the current session operational mode. |
| `SessionManager.start_session() -> None` | Start the trading session and restore persisted state. |
| `SessionManager.stop_session() -> None` | Stop the trading session. |
| `SessionManager.recover_session(*, has_unknown_broker_outcomes: bool, is_unreconciled: bool, missing_audit_logs: bool) -> None` | Execute session recovery checks (TRD-FR-066). |
| `SessionManager.update_connection_state(connected: bool) -> None` | Update connection state and handle reconnection auto-resync (TRD-FR-072). |
| `SessionManager.complete_reconciliation() -> None` | Mark connection reconciliation as completed and restore normal mode. |
| `SessionManager.check_cod_failsafe() -> bool` | Check Cancel-on-Disconnect heartbeat failsafe (TRD-FR-067). |
| `SessionManager.check_synthetic_emulation(*, active_orders: set[str], heartbeat_received: bool) -> None` | Track and monitor synthetic stop/OCO order heartbeats (TRD-FR-070). |
| `SessionManager.run_expiry_watchdog(working_orders: list[JsonObject]) -> list[str]` | Cancel expired GTD/DAY working orders when native expiry is unsupported. |
| `SessionManager.halt_symbol(symbol: str) -> None` | Add symbol to halted symbols set. |
| `SessionManager.resume_symbol(symbol: str) -> None` | Remove symbol from halted symbols set. |
| `SessionManager.is_symbol_halted(symbol: str) -> bool` | Return True if symbol is currently halted. |
| `SessionManager.save_session_state() -> str` | Persist current session state to TradingStateStore. |


## FEAT-TRD-61: Signal processor translating strategy signals to request envelopes (app.services.trading.runtime.signal_processor)

| Function | Purpose |
|----------|---------|
| `SignalProcessor.process_strategy_signal(*, signal: dict[str, Any], gate_pipeline_runner: Callable[[TradingRequestEnvelope], GatePipelineDecision]) -> tuple[TradingRequestEnvelope, GatePipelineDecision]` | Transform signal into envelope and validate via pipeline. |


## FEAT-TRD-62: Trading exception hierarchy and public error mapping (app.services.trading.security.error_mapping)

| Function | Purpose |
|----------|---------|
| `TradingMappedError` (exception) | Mapped exception for trading runtime errors. |
| `TradingValidationError` (exception) | Trading request or payload validation failure. |
| `TradingPermissionError` (exception) | Trading permission or authentication failure. |
| `TradingServiceUnavailableError` (exception) | Trading broker or network unavailability failure. |
| `map_exception_to_trading_error(error: BaseException, *, request_id: str, correlation_id: str, provider: str \| None = None) -> TradingError` | Map an exception to a redacted public trading error contract. |


## FEAT-TRD-63: Recursive redaction boundary and durable dead-letter logging (app.services.trading.security.redaction_boundary)

| Function | Purpose |
|----------|---------|
| `RedactionBoundaryResult.validate_result() -> RedactionBoundaryResult` | Validate redaction boundary result. |
| `DeadLetterRecord.validate_record() -> DeadLetterRecord` | Validate a dead-letter record. |
| `DeadLetterRecord.with_retry_count(retry_count: int) -> DeadLetterRecord` | Return a copy with an updated retry count. |
| `ManualReviewRecord.validate_manual_review() -> ManualReviewRecord` | Validate manual-review record. |
| `DeadLetterWriteResult.validate_write_result() -> DeadLetterWriteResult` | Validate DLQ write result. |
| `WriteAheadDeadLetterQueue.write_failed_event(*, source: str, reason: str, payload: Mapping[str, object], affected_live_scopes: tuple[str, ...]) -> DeadLetterWriteResult` | Write a failed critical event to the write-ahead DLQ. |
| `WriteAheadDeadLetterQueue.recover_pending(*, processor: DeadLetterProcessor) -> tuple[str, ...]` | Replay pending DLQ records exactly once where processing succeeds. |
| `WriteAheadDeadLetterQueue.read_pending() -> tuple[DeadLetterRecord, ...]` | Read all pending DLQ records. |
| `WriteAheadDeadLetterQueue.read_manual_review() -> tuple[ManualReviewRecord, ...]` | Read all manual-review poison-pill records. |
| `redact_for_boundary(payload: Mapping[str, object], *, blocked_live_scopes: tuple[str, ...] = (), alert_message: str \| None = None) -> RedactionBoundaryResult` | Redact a payload before export to logs, notifications, events, or chat. |


## FEAT-TRD-64: Append-only trading event journal and replay utilities (app.services.trading.state.event_journal)

| Function | Purpose |
|----------|---------|
| `JournalBuildMetadata.validate_metadata() -> Self` | Validate build provenance. |
| `JournalEvent.validate_event() -> Self` | Validate immutable journal event identifiers. |
| `JournalEvent.hash_material() -> JsonObject` | Return event material excluding the event hash. |
| `StateSnapshot.validate_snapshot() -> Self` | Validate snapshot identifiers. |
| `ReconciliationLock.validate_lock() -> Self` | Validate reconciliation lock. |
| `JournalIntegrityResult.validate_result() -> Self` | Validate integrity result. |
| `SegmentSeal.validate_seal() -> Self` | Validate segment seal. |
| `JournalRetentionPolicy.validate_policy() -> Self` | Validate retention policy. |
| `AppendOnlyEventJournal.append_event(*, event_type: str, request_id: str, correlation_id: str, route: TradingRoute, account_id: str, symbol: str, actor: str, payload: JsonObject) -> JournalEvent` | Append an immutable journal event. |
| `AppendOnlyEventJournal.read_events() -> tuple[JournalEvent, ...]` | Read and decrypt all journal events. |
| `AppendOnlyEventJournal.scan_unresolved(*, route: TradingRoute, account_id: str) -> tuple[ReconciliationLock, ...]` | Scan unresolved in-flight commands and return mutation locks. |
| `AppendOnlyEventJournal.write_snapshot(*, route: TradingRoute, account_id: str, state: JsonObject) -> StateSnapshot` | Write a durable encrypted state snapshot. |
| `AppendOnlyEventJournal.rebuild_from_snapshot(*, snapshot: StateSnapshot, until_sequence_id: int \| None = None) -> JsonObject` | Rebuild state as snapshot plus replay of subsequent events. |
| `AppendOnlyEventJournal.verify_hash_chain() -> JournalIntegrityResult` | Verify the full journal previous-hash chain. |
| `AppendOnlyEventJournal.seal_segment() -> SegmentSeal` | Write a detached signature for the current journal segment. |
| `AppendOnlyEventJournal.compact_after_snapshot(*, snapshot: StateSnapshot, retention_policy: JournalRetentionPolicy) -> JournalEvent` | Model route-aware compaction by appending a segment-seal event. |
| `replay_builder(*, snapshot: JsonObject, events: Iterable[JournalEvent]) -> JsonObject` | Re-materialize projection state from snapshot and journal events. |


## FEAT-TRD-65: Trading idempotency keys and durable lease records (app.services.trading.state.idempotency)

| Function | Purpose |
|----------|---------|
| `IdempotencyStatus` (enum) | Idempotency record lifecycle status. |
| `IdempotencyDecision` (enum) | Reservation decision returned to callers. |
| `IdempotencyMaterial.validate_material() -> Self` | Validate required idempotency material fields. |
| `IdempotencyMaterial.canonical_payload() -> JsonObject` | Return canonical JSON-safe idempotency material. |
| `IdempotencyRecord.validate_record() -> Self` | Validate idempotency record identifiers. |
| `IdempotencyReservation.validate_reservation() -> Self` | Validate cached outcome consistency. |
| `compute_idempotency_key(material: IdempotencyMaterial) -> str` | Compute a SHA-256 idempotency key from canonical JSON material. |
| `compute_material_hash(payload: JsonObject) -> str` | Compute a SHA-256 material hash from a canonical JSON payload. |
| `JsonlIdempotencyStore.reserve(*, route: TradingRoute, tenant_id: str, material: IdempotencyMaterial, ttl: timedelta) -> IdempotencyReservation` | Reserve an idempotency key or return duplicate state. |
| `JsonlIdempotencyStore.resolve(*, route: TradingRoute, tenant_id: str, key: str) -> IdempotencyRecord \| None` | Resolve a durable idempotency record. |
| `JsonlIdempotencyStore.complete(*, route: TradingRoute, tenant_id: str, key: str, outcome: JsonObject, completed_at: datetime \| None = None) -> IdempotencyRecord` | Mark an in-progress idempotency record completed. |
| `JsonlIdempotencyStore.mark_expired_leases() -> tuple[IdempotencyRecord, ...]` | Transition expired in-progress leases to reconciliation-required. |


## FEAT-TRD-66: Local trading state update coordinators (app.services.trading.state.manager)

| Function | Purpose |
|----------|---------|
| `StateUpdateResult.validate_result() -> StateUpdateResult` | Validate state update result. |
| `LocalStateManager.apply_state_update(*, route: TradingRoute, tenant_id: str, account_id: str, symbol: str, request_id: str, correlation_id: str, actor: str, event_type: str, update: JsonObject, expected_version: int \| None) -> StateUpdateResult` | Persist a local state update and append its journal event. |


## FEAT-TRD-67: Trading runtime persistence and infrastructure ports (app.services.trading.state.ports)

| Function | Purpose |
|----------|---------|
| `Clock.now_utc() -> datetime` | Return the current UTC timestamp. |
| `Clock.now_ptp() -> datetime` | Return the current PTP-aligned timestamp. |
| `Clock.monotonic() -> float` | Return monotonic elapsed time from the injected clock. |
| `RNG.random() -> float` | Return a pseudo-random float in the half-open interval [0.0, 1.0). |
| `RNG.randint(lower_inclusive: int, upper_inclusive: int) -> int` | Return a pseudo-random integer from an inclusive range. |
| `EncryptionProvider.encrypt(plaintext: str) -> str` | Encrypt plaintext data. |
| `EncryptionProvider.decrypt(ciphertext: str) -> str` | Decrypt ciphertext data. |
| `EncryptionProvider.sign(payload: str) -> str` | Sign a canonical payload. |
| `TradeStore.save_order_state(*, route: TradingRoute, tenant_id: str, order_state: JsonObject, expected_version: int \| None) -> str` | Persist an order state projection. |
| `TradeStore.save_position_state(*, route: TradingRoute, tenant_id: str, position_state: JsonObject, expected_version: int \| None) -> str` | Persist a position state projection. |
| `TradeStore.record_execution_fill(*, route: TradingRoute, tenant_id: str, order_id: str, filled_volume: Decimal, fill_price: Decimal, broker_event_id: str) -> JsonObject` | Record a fill and update remaining volume and VWAP projections. |
| `TradeStore.apply_corporate_action(*, route: TradingRoute, tenant_id: str, corporate_action: JsonObject, audit_ref: str) -> JsonObject` | Atomically apply a corporate-action adjustment. |
| `TradeStore.get_order_state(*, route: TradingRoute, tenant_id: str, order_id: str) -> JsonObject \| None` | Retrieve an order state projection by ID. |
| `TradeStore.get_position_state(*, route: TradingRoute, tenant_id: str, position_id: str) -> JsonObject \| None` | Retrieve a position state projection by ID. |
| `TradeStore.list_order_states(*, route: TradingRoute, tenant_id: str) -> list[JsonObject]` | List all active or historical order states for the tenant. |
| `TradeStore.list_position_states(*, route: TradingRoute, tenant_id: str) -> list[JsonObject]` | List all active or historical position states for the tenant. |
| `TradingStateStore.save_state(*, route: TradingRoute, tenant_id: str, snapshot: JsonObject, expected_version: int \| None) -> str` | Persist a trading runtime state snapshot. |
| `TradingStateStore.load_state(*, route: TradingRoute, tenant_id: str, snapshot_id: str) -> JsonObject \| None` | Load a trading runtime state snapshot. |
| `AuditSink.append(*, event: JsonObject, recorded_at: datetime) -> str` | Append a redacted audit event. |
| `AuditSink.flush() -> None` | Flush pending audit records. |
| `IdempotencyStore.reserve(*, route: TradingRoute, tenant_id: str, key: str, material_hash: str, expires_at: datetime) -> JsonObject` | Reserve an idempotency key before audit or broker mutation. |
| `IdempotencyStore.resolve(*, route: TradingRoute, tenant_id: str, key: str, material_hash: str) -> JsonObject \| None` | Resolve a previously reserved idempotency key. |
| `IdempotencyStore.complete(*, route: TradingRoute, tenant_id: str, key: str, outcome: JsonObject, completed_at: datetime) -> None` | Complete an idempotency record. |
| `EventJournal.append(*, event: JsonObject, recorded_at: datetime) -> str` | Append a trading command or event. |
| `EventJournal.scan_unresolved(*, route: TradingRoute, tenant_id: str) -> tuple[JsonObject, ...]` | Scan unresolved journal entries for recovery. |


## FEAT-TRD-68: Concrete ``TradeStore`` implementations (BF-TRD-002) (app.services.trading.state.trade_store)

| Function | Purpose |
|----------|---------|
| `InMemoryTradeStore` (class) | Volatile in-process trade projection store. |
| `JsonlTradeStore` (class) | Durable JSONL-backed trade projection store. |


## FEAT-TRD-69: Stateful strategy contracts for portfolio-aware execution logic (app.services.trading.stateful)

| Function | Purpose |
|----------|---------|
| `PositionType` (model) | Legacy buy/sell position enum used by older saved strategy code. |
| `PositionSnapshot` (model) | Read-only position view passed into stateful strategy decisions. |
| `OrderSnapshot` (model) | Read-only pending/open order view passed into stateful strategies. |
| `TradeSnapshot` (model) | Read-only completed trade view for lifecycle-aware strategies. |
| `StrategyRuntimeState` (model) | Mutable per-strategy state persisted by the runtime between events. |
| `StrategyContext.positions_for_symbol(symbol: str \| None = None) -> list[PositionSnapshot]` | Return open positions matching a symbol, defaulting to this context symbol. |
| `StrategyContext.orders_for_symbol(symbol: str \| None = None) -> list[OrderSnapshot]` | Return pending/open orders matching a symbol, defaulting to this context symbol. |
| `TradeAction.hold(*, symbol: str, strategy_id: str \| None = None, reason: str \| None = None) -> TradeAction` | Create an explicit no-op action for audit trails. |
| `StatefulStrategyProtocol.on_event(context: StrategyContext) -> list[TradeAction]` | Return trade actions for the current market/runtime event. |
| `StatefulStrategyProtocol.on_order_update(event: Mapping[str, Any]) -> None` | Handle order lifecycle updates. |
| `StatefulStrategyProtocol.on_trade_update(event: Mapping[str, Any]) -> None` | Handle trade lifecycle updates. |
| `StatefulStrategyMixin.on_event(context: StrategyContext) -> list[TradeAction]` | Return trade actions for the current market/runtime event. |
| `StatefulStrategyMixin.on_order_update(event: Mapping[str, Any]) -> None` | Handle order lifecycle updates when the runtime provides them. |
| `StatefulStrategyMixin.on_trade_update(event: Mapping[str, Any]) -> None` | Handle trade lifecycle updates when the runtime provides them. |


## FEAT-TRD-70: TradeStore interface and in-memory implementation (app.services.trading.store)

| Function | Purpose |
|----------|---------|
| `TradeStore.get_idempotency_record(key: str) -> dict[str, Any] \| None` | Retrieve idempotency record by key. |
| `TradeStore.save_idempotency_record(key: str, record: dict[str, Any], ttl_seconds: int = 86400) -> None` | Save an idempotency record. |
| `TradeStore.get_order(ticket: int) -> dict[str, Any] \| None` | Retrieve an order by ticket. |
| `TradeStore.save_order(ticket: int, order: dict[str, Any]) -> None` | Save order details. |
| `TradeStore.get_orders() -> list[dict[str, Any]]` | Retrieve all active orders. |
| `TradeStore.get_position(ticket: int) -> dict[str, Any] \| None` | Retrieve a position by ticket. |
| `TradeStore.save_position(ticket: int, position: dict[str, Any]) -> None` | Save position details. |
| `TradeStore.delete_position(ticket: int) -> None` | Remove a position. |
| `TradeStore.get_positions() -> list[dict[str, Any]]` | Retrieve all active positions. |
| `TradeStore.get_execution(ticket: int) -> dict[str, Any] \| None` | Retrieve an execution deal by ticket. |
| `TradeStore.save_execution(ticket: int, execution: dict[str, Any]) -> None` | Save execution deal details. |
| `TradeStore.get_executions() -> list[dict[str, Any]]` | Retrieve all execution deals. |
| `InMemoryTradeStore.__init__() -> None` | Initialize the dictionaries. |
| `InMemoryTradeStore.get_idempotency_record(key: str) -> dict[str, Any] \| None` | Retrieve idempotency record, checking TTL expiration. |
| `InMemoryTradeStore.save_idempotency_record(key: str, record: dict[str, Any], ttl_seconds: int = 86400) -> None` | Save idempotency record with absolute expiration time. |
| `InMemoryTradeStore.get_order(ticket: int) -> dict[str, Any] \| None` | Retrieve order. |
| `InMemoryTradeStore.save_order(ticket: int, order: dict[str, Any]) -> None` | Save order. |
| `InMemoryTradeStore.get_orders() -> list[dict[str, Any]]` | Get all orders. |
| `InMemoryTradeStore.get_position(ticket: int) -> dict[str, Any] \| None` | Retrieve position. |
| `InMemoryTradeStore.save_position(ticket: int, position: dict[str, Any]) -> None` | Save position. |
| `InMemoryTradeStore.delete_position(ticket: int) -> None` | Delete position. |
| `InMemoryTradeStore.get_positions() -> list[dict[str, Any]]` | Get all positions. |
| `InMemoryTradeStore.get_execution(ticket: int) -> dict[str, Any] \| None` | Retrieve execution deal. |
| `InMemoryTradeStore.save_execution(ticket: int, execution: dict[str, Any]) -> None` | Save execution deal. |
| `InMemoryTradeStore.get_executions() -> list[dict[str, Any]]` | Get all execution deals. |
| `get_default_store() -> TradeStore` | Get default singleton TradeStore instance. |


## FEAT-TRD-71: Pure trading tool registry accessors (app.services.trading.tool_registry)

| Function | Purpose |
|----------|---------|
| `build_trading_tool_registry() -> TradingToolRegistry` | Build the approved trading tool registry. |
| `list_trading_tools(registry: TradingToolRegistry) -> tuple[TradingToolDefinition, ...]` | List deterministic public trading tool definitions. |
| `get_trading_tool_definition(name: str, registry: TradingToolRegistry) -> TradingToolDefinition` | Resolve a trading tool definition by name. |
