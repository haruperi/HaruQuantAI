## FEAT-EXEC-01: Shared execution-service helpers (app.services.execution._common)

| Function | Purpose |
|----------|---------|
| `execution_approval_module() -> ModuleType` | Return the execution approval service module. |
| `execution_live_module() -> ModuleType` | Return the live execution service module. |
| `execution_monitoring_module() -> ModuleType` | Return the execution monitoring service module. |
| `execution_performance_module() -> ModuleType` | Return the execution performance service module. |
| `execution_reconciliation_module() -> ModuleType` | Return the execution reconciliation service module. |
| `execution_trade_governor_module() -> ModuleType` | Return the trade action governor service module. |
| `execution_tool_result(name: str, *, status: str = 'success', data: dict[str, Any] \| None = None, errors: list[str] \| None = None, warnings: list[str] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True, risk_level: str = 'high', approval_required: str = 'risk_governor_required', side_effects: list[str] \| None = None) -> dict[str, Any]` | Build the standard HaruQuant result envelope for execution tools. |
| `execution_tool_context(kwargs: dict[str, Any]) -> dict[str, Any]` | Extract common execution tool context fields from keyword arguments. |
| `package_execution_request(name: str, kwargs: dict[str, Any], *, critical: bool = False) -> dict[str, Any]` | Package a deterministic execution request without live side effects. |


## FEAT-EXEC-02: Approval domain models (app.services.execution.approval.models)

| Function | Purpose |
|----------|---------|
| `ApprovalState` (model) | Represent ApprovalState behavior in execution service workflows. |
| `RiskClass` (model) | Action risk classification (Playbook §11.1). |
| `ApprovalPacket.is_complete() -> bool` | Return True if all required fields are populated. |
| `ApprovalPacket.missing_fields() -> list[str]` | Return list of required fields that are empty. |
| `ApprovalRequest` (model) | Represent ApprovalRequest behavior in execution service workflows. |


## FEAT-EXEC-03: Override request skeleton (app.services.execution.approval.override)

| Function | Purpose |
|----------|---------|
| `OverrideRequestDraft` (model) | Represent OverrideRequestDraft behavior in execution service workflows. |
| `OverrideRequestService.validate(draft: OverrideRequestDraft) -> OverrideRequestDraft` | Perform the validate execution service operation. |


## FEAT-EXEC-04: Approval packet builder helper (app.services.execution.approval.packet_builder)

| Function | Purpose |
|----------|---------|
| `ApprovalPacketBuilder.__init__() -> None` | Fluent builder for ApprovalPacket. |
| `ApprovalPacketBuilder.action(value: str) -> ApprovalPacketBuilder` | Perform the action execution service operation. |
| `ApprovalPacketBuilder.reason(value: str) -> ApprovalPacketBuilder` | Perform the reason execution service operation. |
| `ApprovalPacketBuilder.evidence(items: list[dict[str, Any]]) -> ApprovalPacketBuilder` | Perform the evidence execution service operation. |
| `ApprovalPacketBuilder.confidence(value: float) -> ApprovalPacketBuilder` | Perform the confidence execution service operation. |
| `ApprovalPacketBuilder.uncertainty(items: dict[str, str]) -> ApprovalPacketBuilder` | Perform the uncertainty execution service operation. |
| `ApprovalPacketBuilder.policy_checks(items: list[str]) -> ApprovalPacketBuilder` | Perform the policy_checks execution service operation. |
| `ApprovalPacketBuilder.risk_class(value: RiskClass) -> ApprovalPacketBuilder` | Perform the risk_class execution service operation. |
| `ApprovalPacketBuilder.alternatives(items: list[str]) -> ApprovalPacketBuilder` | Perform the alternatives execution service operation. |
| `ApprovalPacketBuilder.expected_impact(value: dict[str, Any]) -> ApprovalPacketBuilder` | Perform the expected_impact execution service operation. |
| `ApprovalPacketBuilder.rollback_plan(value: str) -> ApprovalPacketBuilder` | Perform the rollback_plan execution service operation. |
| `ApprovalPacketBuilder.escalation_triggers(items: list[str]) -> ApprovalPacketBuilder` | Perform the escalation_triggers execution service operation. |
| `ApprovalPacketBuilder.build() -> ApprovalPacket` | Perform the build execution service operation. |
| `ApprovalPacketBuilder.from_dict(data: dict[str, Any]) -> ApprovalPacketBuilder` | Create builder from dictionary. |


## FEAT-EXEC-05: Approval creation and voting tools (app.services.execution.approval.services)

| Function | Purpose |
|----------|---------|
| `ApprovalCreateRequest` (model) | Represent ApprovalCreateRequest behavior in execution service workflows. |
| `ApprovalCreationService.__init__(repository: GovernanceRepository) -> None` | Create approval requests with minimal validation. |
| `ApprovalCreationService.create(request: ApprovalCreateRequest) -> ApprovalRecord` | Perform the create execution service operation. |
| `ApprovalVoteRequest` (model) | Represent ApprovalVoteRequest behavior in execution service workflows. |
| `ApprovalVoteService.__init__(repository: GovernanceRepository) -> None` | Persist approval votes while enforcing distinct approver identity. |
| `ApprovalVoteService.vote(request: ApprovalVoteRequest) -> ApprovalVoteRecord` | Perform the vote execution service operation. |


## FEAT-EXEC-06: Approval state machine (app.services.execution.approval.state_machine)

| Function | Purpose |
|----------|---------|
| `ApprovalStateMachine.validate(from_state: ApprovalState, to_state: ApprovalState) -> None` | Perform the validate execution service operation. |


## FEAT-EXEC-07: Execution intent assembly from approved proposal and risk decision (app.services.execution.assembler)

| Function | Purpose |
|----------|---------|
| `ExecutionIntentAssemblyConfig` (model) | Static defaults for execution intent assembly. |
| `assemble_execution_intent(proposal: TradeProposal, risk_decision: RiskAssessmentDecision, *, idempotency_key: str, clock: Clock \| None = None, config: ExecutionIntentAssemblyConfig \| None = None) -> ExecutionIntent` | Build a canonical execution intent linked to the approved proposal and risk decision. |


## FEAT-EXEC-08: Execution send-attempt persistence helpers (app.services.execution.attempts)

| Function | Purpose |
|----------|---------|
| `ExecutionAttemptPersistenceService.__init__(repository: ExecutionRepository) -> None` | Persist send attempts with stable submitted-payload hashing. |
| `ExecutionAttemptPersistenceService.persist_attempt(*, execution_intent_id: str, submitted_payload: dict[str, object], transport_status: str, broker_request_ref: str \| None = None, error_code: str \| None = None, error_message: str \| None = None, finished_at: str \| None = None, latency_ms: int \| None = None) -> ExecutionSendAttemptRecord` | Perform the persist_attempt execution service operation. |


## FEAT-EXEC-09: Authority-state propagation helpers for execution status views (app.services.execution.authority)

| Function | Purpose |
|----------|---------|
| `AuthorityStateView` (model) | Resolved authority-state badge for an execution record. |
| `propagate_authority_state(*, has_receipt: bool, receipt_authoritative_state: str \| None = None, reconciliation_result_state: str \| None = None) -> AuthorityStateView` | Resolve the current authority-state badge for operator and audit views. |


## FEAT-EXEC-10: Base interface for broker execution bridges (app.services.execution.bridges.base_bridge)

| Function | Purpose |
|----------|---------|
| `BaseExecutionBridge.__init__(*, live_enabled: bool = False) -> None` | Represent BaseExecutionBridge behavior in execution service workflows. |
| `BaseExecutionBridge.heartbeat() -> dict[str, Any]` | Perform the heartbeat execution service operation. |
| `BaseExecutionBridge.place_order(order: dict[str, Any]) -> dict[str, Any]` | Perform the place_order execution service operation. |


## FEAT-EXEC-11: cTrader bridge preparation with normalized metadata and fail-closed mutations (app.services.execution.bridges.ctrader_bridge)

| Function | Purpose |
|----------|---------|
| `CTraderBridge.get_symbol_info(symbol: str) -> dict[str, Any]` | Perform the get_symbol_info execution service operation. |
| `CTraderBridge.normalize_order_status(status: str) -> str` | Perform the normalize_order_status execution service operation. |
| `CTraderBridge.normalize_position_status(status: str) -> str` | Perform the normalize_position_status execution service operation. |


## FEAT-EXEC-12: MT5 bridge preparation with live mutation methods fail-closed by default (app.services.execution.bridges.mt5_bridge)

| Function | Purpose |
|----------|---------|
| `MT5Bridge.__init__(*, live_enabled: bool = False) -> None` | Represent MT5Bridge behavior in execution service workflows. |
| `MT5Bridge.reconnect() -> bool` | Perform the reconnect execution service operation. |
| `MT5Bridge.heartbeat() -> dict[str, Any]` | Perform the heartbeat execution service operation. |
| `MT5Bridge.get_account_info() -> dict[str, Any]` | Perform the get_account_info execution service operation. |
| `MT5Bridge.get_symbol_info(symbol: str) -> dict[str, Any]` | Perform the get_symbol_info execution service operation. |
| `MT5Bridge.get_latest_tick(symbol: str) -> dict[str, Any]` | Perform the get_latest_tick execution service operation. |
| `MT5Bridge.get_open_positions() -> list[dict[str, Any]]` | Perform the get_open_positions execution service operation. |
| `MT5Bridge.get_pending_orders() -> list[dict[str, Any]]` | Perform the get_pending_orders execution service operation. |
| `MT5Bridge.place_order(order: dict[str, Any]) -> dict[str, Any]` | Perform the place_order execution service operation. |
| `MT5Bridge.close_position(position_id: str) -> dict[str, Any]` | Perform the close_position execution service operation. |
| `MT5Bridge.cancel_order(order_id: str) -> dict[str, Any]` | Perform the cancel_order execution service operation. |


## FEAT-EXEC-13: Broker connectivity execution tools (app.services.execution.broker_connectivity)

| Function | Purpose |
|----------|---------|
| `check_broker_connection(**kwargs: Any) -> dict[str, Any]` | Check MT5 or cTrader broker connection status. |
| `get_account_info(**kwargs: Any) -> dict[str, Any]` | Retrieve account balance, equity, margin, and leverage context. |
| `get_symbol_info(**kwargs: Any) -> dict[str, Any]` | Retrieve broker metadata for one symbol. |
| `get_current_bid_ask(**kwargs: Any) -> dict[str, Any]` | Retrieve current bid and ask prices. |
| `get_current_spread(**kwargs: Any) -> dict[str, Any]` | Retrieve current spread for one symbol. |
| `get_trade_permissions(**kwargs: Any) -> dict[str, Any]` | Retrieve whether trading is allowed for the account and symbol. |
| `get_broker_time(**kwargs: Any) -> dict[str, Any]` | Retrieve broker timestamp. |
| `check_market_open(**kwargs: Any) -> dict[str, Any]` | Check whether a symbol can be traded now. |
| `check_min_lot(**kwargs: Any) -> dict[str, Any]` | Check broker minimum lot rule. |
| `check_max_lot(**kwargs: Any) -> dict[str, Any]` | Check broker maximum lot rule. |
| `check_lot_step(**kwargs: Any) -> dict[str, Any]` | Check broker lot step rule. |
| `check_stop_distance(**kwargs: Any) -> dict[str, Any]` | Check broker minimum stop distance. |
| `check_free_margin(**kwargs: Any) -> dict[str, Any]` | Check free margin availability. |


## FEAT-EXEC-14: Deterministic paper broker for live-like execution simulation (app.services.execution.brokers.paper_broker)

| Function | Purpose |
|----------|---------|
| `PaperBrokerConfig` (model) | Represent PaperBrokerConfig behavior in execution service workflows. |
| `PaperOrderRequest` (model) | Represent PaperOrderRequest behavior in execution service workflows. |
| `PaperOrderResult` (model) | Represent PaperOrderResult behavior in execution service workflows. |
| `PaperPosition` (model) | Represent PaperPosition behavior in execution service workflows. |
| `PaperAccountState` (model) | Represent PaperAccountState behavior in execution service workflows. |
| `PaperBroker.place_order(*, symbol: str, side: str, order_type: str, size: float, price: float, spread: float = 0.0, slippage: float = 0.0, commission: float = 0.0, swap: float = 0.0) -> dict[str, Any]` | Perform the place_order execution service operation. |
| `PaperBroker.process_pending_orders(*, market_price: float) -> list[dict[str, Any]]` | Perform the process_pending_orders execution service operation. |
| `PaperBroker.account_snapshot() -> dict[str, Any]` | Perform the account_snapshot execution service operation. |


## FEAT-EXEC-15: Compensation plan base class (Playbook §13) (app.services.execution.compensation.base)

| Function | Purpose |
|----------|---------|
| `CompensationPlan.__init__(action_id: str, description: str = '') -> None` | Abstract base for compensation plans. |
| `CompensationPlan.execute(context: dict[str, Any]) -> bool` | Execute the compensation action. |
| `CompensationPlan.validate(context: dict[str, Any]) -> bool` | Validate that compensation is applicable. |
| `CompensationPlan.log(entry: dict[str, Any]) -> None` | Log a compensation step entry. |
| `CompensationPlan.log_entries -> list[dict[str, Any]]` | Perform the log_entries execution service operation. |


## FEAT-EXEC-16: Order compensation plan: offsetting orders, cancel pending (app.services.execution.compensation.order_compensation)

| Function | Purpose |
|----------|---------|
| `OrderCompensationPlan.__init__(action_id: str) -> None` | Compensate for partial order failures. |
| `OrderCompensationPlan.execute(context: dict[str, Any]) -> bool` | Execute order compensation. |
| `OrderCompensationPlan.validate(context: dict[str, Any]) -> bool` | Validate order compensation is applicable. |


## FEAT-EXEC-17: Position compensation plan: close position, adjust size (app.services.execution.compensation.position_compensation)

| Function | Purpose |
|----------|---------|
| `PositionCompensationPlan.__init__(action_id: str) -> None` | Compensate for position-related failures. |
| `PositionCompensationPlan.execute(context: dict[str, Any]) -> bool` | Execute position compensation. |
| `PositionCompensationPlan.validate(context: dict[str, Any]) -> bool` | Validate position compensation is applicable. |


## FEAT-EXEC-18: Compensation registry mapping action classes to plans (app.services.execution.compensation.registry)

| Function | Purpose |
|----------|---------|
| `CompensationRegistry.__init__() -> None` | Registry mapping action classes (A-E) to compensation plans. |
| `CompensationRegistry.register(action_class: str, plan_class: type[CompensationPlan]) -> None` | Register a compensation plan for an action class. |
| `CompensationRegistry.get_plan(action_class: str, action_id: str) -> CompensationPlan \| None` | Get a compensation plan instance for an action class. |
| `CompensationRegistry.has_plan(action_class: str) -> bool` | Perform the has_plan execution service operation. |
| `CompensationRegistry.registered_classes -> list[str]` | Perform the registered_classes execution service operation. |


## FEAT-EXEC-19: Core simulator components (app.services.execution.core)

| Function | Purpose |
|----------|---------|
| `DotDict` (model) | Dictionary that supports dot notation access to attributes. |
| `TerminalInfo` (model) | Container for Terminal information. |
| `DealInfo` (model) | Container for Deal information. |
| `PositionInfo` (model) | Container for Position information. |
| `OrderInfo` (model) | Container for active Order information. |
| `HistoryOrderInfo` (model) | Container for History Order information. |
| `SymbolInfo` (model) | Container for Symbol information. |
| `TradeRecord.to_dict()` | Perform the to_dict execution service operation. |
| `TradeTracker` (model) | Runtime-only tracker for an open trade. |
| `CloseType` (model) | Canonical close type enums for trade records. |
| `ExitReason` (model) | Exit reason enum for trade records. |
| `BacktestResult` (model) | Backtest result container (legacy compatibility). |
| `EquityPoint.to_dict()` | Perform the to_dict execution service operation. |
| `RunResult.to_dict()` | Perform the to_dict execution service operation. |
| `SimulatorState.__init__(account_info=None) -> None` | Holds the current state for the backtest simulator. |
| `history_deals_get(state: SimulatorState, date_from=None, date_to=None, group=None, ticket=None)` | Retrieve historical deals from state. |
| `history_deals_total(state: SimulatorState, date_from, date_to)` | Perform the history_deals_total execution service operation. |
| `positions_get(state: SimulatorState, symbol=None, group=None, ticket=None)` | Perform the positions_get execution service operation. |
| `positions_total(state: SimulatorState)` | Perform the positions_total execution service operation. |
| `orders_get(state: SimulatorState, symbol=None, group=None, ticket=None)` | Perform the orders_get execution service operation. |
| `orders_total(state: SimulatorState)` | Perform the orders_total execution service operation. |
| `history_orders_get(state: SimulatorState, date_from=None, date_to=None, group=None, ticket=None)` | Perform the history_orders_get execution service operation. |
| `history_orders_total(state: SimulatorState, date_from, date_to)` | Perform the history_orders_total execution service operation. |
| `symbols_get(state: SimulatorState, group=None)` | Perform the symbols_get execution service operation. |
| `symbols_total(state: SimulatorState)` | Perform the symbols_total execution service operation. |
| `symbol_info(state: SimulatorState, name: str)` | Perform the symbol_info execution service operation. |
| `monitor_positions(state: SimulatorState, verbose: bool = False, allow_auto_close: bool = True, profit_calculator=None, strict_calc_access: bool = False) -> None` | Monitor open positions, update mark-to-market fields, and close on SL/TP. |
| `monitor_pending_orders(state: SimulatorState, verbose: bool = False, allow_auto_trigger: bool = True, allow_auto_expire: bool = True, profit_calculator=None, margin_calculator=None, strict_calc_access: bool = False) -> None` | Monitor pending orders, expire them, and trigger matched entries. |
| `monitor_account(state: SimulatorState, verbose: bool = False) -> None` | Monitor account aggregates from open positions. |
| `order_send(state: SimulatorState, request, profit_calculator=None, margin_calculator=None, strict_calc_access: bool = False, verbose: bool = False) -> DotDict` | Process a TradeRequest and update the SimulatorState. |


## FEAT-EXEC-20: Cost enforcement service (Playbook §17) (app.services.execution.cost.enforcer)

| Function | Purpose |
|----------|---------|
| `CostEntry` (model) | Represent CostEntry behavior in execution service workflows. |
| `CostTracker.__init__(*, cost_per_input_token: float \| None = None, cost_per_output_token: float \| None = None) -> None` | Small in-memory token and cost tracker for cost enforcement. |
| `CostTracker.record(trace_id: str, span_id: str = '', model: str = '', input_tokens: int = 0, output_tokens: int = 0) -> CostEntry` | Perform the record execution service operation. |
| `CostTracker.total_cost(trace_id: str = '') -> float` | Perform the total_cost execution service operation. |
| `CostTracker.total_tokens(trace_id: str = '') -> dict[str, int]` | Perform the total_tokens execution service operation. |
| `CostTracker.cost_breakdown_by_model(trace_id: str = '') -> dict[str, float]` | Perform the cost_breakdown_by_model execution service operation. |
| `CostTracker.entry_count -> int` | Perform the entry_count execution service operation. |
| `CostTracker.clear() -> None` | Perform the clear execution service operation. |
| `CostEnforcer.__init__() -> None` | Enforce cost limits per request, workflow, and session. |
| `CostEnforcer.check_request_budget(tier: str, estimated_cost: float) -> bool` | Check if estimated cost is within the tier budget. |
| `CostEnforcer.check_workflow_budget(current_cost: float) -> bool` | Check if cumulative workflow cost is within budget. |
| `CostEnforcer.record_cost(trace_id: str, span_id: str = '', model: str = '', input_tokens: int = 0, output_tokens: int = 0) -> None` | Record cost for a trace/span. |
| `CostEnforcer.get_current_cost(trace_id: str = '') -> float` | Get current cumulative cost. |
| `CostEnforcer.get_fallback_model() -> str` | Get the fallback model name from policy. |
| `CostEnforcer.tracker -> CostTracker` | Perform the tracker execution service operation. |


## FEAT-EXEC-21: Execution idempotency helpers (app.services.execution.idempotency)

| Function | Purpose |
|----------|---------|
| `generate_execution_idempotency_key(*, proposal: TradeProposal, risk_decision: RiskAssessmentDecision, broker_action_type: str, order_type: str) -> str` | Generate a stable uniqueness key for one execution request shape. |


## FEAT-EXEC-22: Agent-facing execution kill-switch tools (app.services.execution.kill_switch_tools)

| Function | Purpose |
|----------|---------|
| `trigger_global_kill_switch(**kwargs: Any) -> dict[str, Any]` | Trigger the global trading kill switch after approval gates. |
| `trigger_strategy_kill_switch(**kwargs: Any) -> dict[str, Any]` | Trigger a strategy-level kill switch after approval gates. |
| `trigger_symbol_kill_switch(**kwargs: Any) -> dict[str, Any]` | Trigger a symbol-level kill switch after approval gates. |
| `check_kill_switch_conditions(**kwargs: Any) -> dict[str, Any]` | Evaluate kill-switch trigger conditions after approval gates. |
| `disable_new_orders(**kwargs: Any) -> dict[str, Any]` | Disable new order submission after approval gates. |
| `close_all_positions(**kwargs: Any) -> dict[str, Any]` | Close all positions after approval gates. |
| `cancel_all_orders(**kwargs: Any) -> dict[str, Any]` | Cancel all pending orders after approval gates. |
| `record_kill_switch_event(**kwargs: Any) -> dict[str, Any]` | Record a kill-switch event after approval gates. |
| `require_reenable_approval(**kwargs: Any) -> dict[str, Any]` | Require approval before re-enabling trading. |
| `clear_kill_switch_after_approval(**kwargs: Any) -> dict[str, Any]` | Clear a kill switch only after approval gates. |


## FEAT-EXEC-23: Bar Monitor (app.services.execution.live.bar_monitor)

| Function | Purpose |
|----------|---------|
| `BarMonitor.__init__(client: 'MT5Client', symbol: str, timeframe: str) -> None` | Initialize bar monitor. |
| `BarMonitor.get_historical_data(count: int) -> pd.DataFrame \| None` | Fetch historical bars for strategy initialization. |
| `BarMonitor.check_new_bar() -> bool` | Check if a new bar has opened since last check. |
| `BarMonitor.get_last_closed_bar() -> pd.Series \| None` | Get the last CLOSED bar (not current forming bar). |
| `BarMonitor.get_current_bar_time() -> datetime \| None` | Get timestamp of the last closed bar. |


## FEAT-EXEC-24: Typed configuration management for live trading (app.services.execution.live.config)

| Function | Purpose |
|----------|---------|
| `ConfigError` (model) | Configuration error. |
| `MT5Config` (model) | Represent MT5Config behavior in execution service workflows. |
| `StrategyConfig` (model) | Represent StrategyConfig behavior in execution service workflows. |
| `TradingConfig` (model) | Represent TradingConfig behavior in execution service workflows. |
| `SafetyConfig` (model) | Represent SafetyConfig behavior in execution service workflows. |
| `NotificationConfig` (model) | Represent NotificationConfig behavior in execution service workflows. |
| `LoggingConfig` (model) | Represent LoggingConfig behavior in execution service workflows. |
| `StateConfig` (model) | Represent StateConfig behavior in execution service workflows. |
| `LiveConfigModel` (model) | Represent LiveConfigModel behavior in execution service workflows. |
| `get_schema_spec() -> dict[str, dict[str, str]]` | Return self-documenting schema metadata. |
| `load_config_mapping(config_path: str \| Path, *, profile: str \| None = None, runtime_overrides: dict[str, Any] \| None = None) -> dict[str, Any]` | Load raw config mapping from TOML/JSON with precedence layers. |
| `parse_live_config(data: dict[str, Any]) -> LiveConfigModel` | Validate and parse mapping into typed live config model. |
| `Config.__init__(config_path: str, *, profile: str \| None = None, runtime_overrides: dict[str, Any] \| None = None) -> None` | Typed configuration loader for single-strategy live runtime. |
| `Config.reload() -> None` | Reload entire config with current profile/env/runtime precedence. |
| `Config.set_runtime_override(key: str, value: Any) -> None` | Set runtime override using dotted-path key syntax. |
| `Config.clear_runtime_override(key: str \| None = None) -> None` | Clear one runtime override by key, or all when key is None. |
| `Config.apply_privileged_mutation(key: str, value: Any, *, authorization_token: str, reason: str, actor: str \| None = None, audit_log_path: str \| Path = DEFAULT_AUDIT_LOG_PATH) -> None` | Apply a runtime config mutation under privileged controls. |
| `Config.apply_risk_override(key: str, value: Any, *, authorization_token: str, reason: str, actor: str \| None = None, audit_log_path: str \| Path = DEFAULT_AUDIT_LOG_PATH) -> None` | Apply a role-bound risk override and emit immutable audit metadata. |
| `Config.reload_non_critical() -> list[str]` | Reload only non-critical config keys (logging levels, safety/risk limits). |
| `Config.schema_version -> str` | Perform the schema_version execution service operation. |
| `Config.active_profile -> str \| None` | Perform the active_profile execution service operation. |
| `Config.mt5_login -> int` | Perform the mt5_login execution service operation. |
| `Config.mt5_password -> str` | Perform the mt5_password execution service operation. |
| `Config.mt5_server -> str` | Perform the mt5_server execution service operation. |
| `Config.mt5_path -> str` | Perform the mt5_path execution service operation. |
| `Config.strategy_symbol -> str` | Perform the strategy_symbol execution service operation. |
| `Config.strategy_params -> dict[str, Any]` | Perform the strategy_params execution service operation. |
| `Config.trading_timeframe -> str` | Perform the trading_timeframe execution service operation. |
| `Config.trading_volume -> float` | Perform the trading_volume execution service operation. |
| `Config.trading_magic_number -> int` | Perform the trading_magic_number execution service operation. |
| `Config.trading_initial_bars -> int` | Perform the trading_initial_bars execution service operation. |
| `Config.trading_deviation -> int` | Perform the trading_deviation execution service operation. |
| `Config.safety_min_balance -> float` | Perform the safety_min_balance execution service operation. |
| `Config.safety_min_margin_level -> float` | Perform the safety_min_margin_level execution service operation. |
| `Config.safety_max_positions -> int` | Perform the safety_max_positions execution service operation. |
| `Config.safety_max_daily_trades -> int` | Perform the safety_max_daily_trades execution service operation. |
| `Config.notifications_enabled -> bool` | Perform the notifications_enabled execution service operation. |
| `Config.smtp_host -> str` | Perform the smtp_host execution service operation. |
| `Config.smtp_port -> int` | Perform the smtp_port execution service operation. |
| `Config.smtp_user -> str` | Perform the smtp_user execution service operation. |
| `Config.smtp_password -> str` | Perform the smtp_password execution service operation. |
| `Config.email_recipients -> list[str]` | Perform the email_recipients execution service operation. |
| `Config.logging_dir -> str` | Perform the logging_dir execution service operation. |
| `Config.logging_level -> str` | Perform the logging_level execution service operation. |
| `Config.state_file -> str` | Perform the state_file execution service operation. |
| `Config.get(key: str, default: Any = None) -> Any` | Perform the get execution service operation. |


## FEAT-EXEC-25: Live Trading Dashboard (app.services.execution.live.dashboard)

| Function | Purpose |
|----------|---------|
| `Dashboard.__init__(log_file: str = 'data/logs/multi_strategy/multi_strategy.log', state_file: str = 'multi_strategy_state.json', refresh_interval: int = 5) -> None` | Initialize dashboard. |
| `Dashboard.run() -> None` | Run the dashboard. |
| `main() -> None` | Run dashboard. |


## FEAT-EXEC-26: Multi-Strategy Live Trading Engine (app.services.execution.live.engine)

| Function | Purpose |
|----------|---------|
| `StrategyInstance.__init__(name: str, symbol: str, timeframe: str, strategy: Any, bar_monitor: BarMonitor, signal_processor: SignalProcessor, trade_executor: TradeExecutor, safety_checker: SafetyChecker, position_manager: PositionManager, config: dict) -> None` | Initialize strategy instance. |
| `MultiStrategyEngine.__init__(config_path: str \| None = None, config: dict \| None = None, client: Optional['MT5Client'] = None) -> None` | Initialize multi-strategy engine. |
| `MultiStrategyEngine.initialize() -> bool` | Initialize all strategies and shared components. |
| `MultiStrategyEngine.run() -> None` | Run main trading loop. |
| `MultiStrategyEngine.stop() -> None` | Stop the trading engine. |
| `MultiStrategyEngine.get_status() -> dict` | Get current status of all strategies. |


## FEAT-EXEC-27: Live Trading Domain Models (app.services.execution.live.models)

| Function | Purpose |
|----------|---------|
| `SignalType` (model) | Signal types. |
| `Signal` (model) | Standardized Trading Signal. |


## FEAT-EXEC-28: Helpers to read MT5 client/account/symbol objects with wrapper compatibility (app.services.execution.live.mt5_compat)

| Function | Purpose |
|----------|---------|
| `account_balance(account: Any) -> float` | Perform the account_balance execution service operation. |
| `account_equity(account: Any) -> float` | Perform the account_equity execution service operation. |
| `account_margin(account: Any) -> float` | Perform the account_margin execution service operation. |
| `account_free_margin(account: Any) -> float` | Perform the account_free_margin execution service operation. |
| `account_margin_level(account: Any) -> float` | Perform the account_margin_level execution service operation. |
| `account_profit(account: Any) -> float` | Perform the account_profit execution service operation. |
| `account_currency(account: Any) -> str` | Perform the account_currency execution service operation. |
| `account_leverage(account: Any) -> int` | Perform the account_leverage execution service operation. |
| `account_trade_allowed(account: Any) -> bool` | Perform the account_trade_allowed execution service operation. |
| `account_trade_expert(account: Any) -> bool` | Perform the account_trade_expert execution service operation. |
| `symbol_bid(symbol_info: Any) -> float` | Perform the symbol_bid execution service operation. |
| `symbol_ask(symbol_info: Any) -> float` | Perform the symbol_ask execution service operation. |
| `symbol_name(symbol_info: Any) -> str` | Perform the symbol_name execution service operation. |
| `symbol_trade_mode_description(symbol_info: Any) -> str` | Perform the symbol_trade_mode_description execution service operation. |
| `symbol_volume_min(symbol_info: Any) -> float` | Perform the symbol_volume_min execution service operation. |
| `symbol_volume_max(symbol_info: Any) -> float` | Perform the symbol_volume_max execution service operation. |
| `symbol_volume_step(symbol_info: Any) -> float` | Perform the symbol_volume_step execution service operation. |


## FEAT-EXEC-29: Notification Adapter for Live Trading (app.services.execution.live.notification_adapter)

| Function | Purpose |
|----------|---------|
| `LiveTradingNotifier.__init__(enabled: bool, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, recipients: list[str], max_retries: int = 3) -> None` | Initialize live trading notifier. |
| `LiveTradingNotifier.notify_startup(symbol: str, timeframe: str, volume: float) -> None` | Send startup notification. |
| `LiveTradingNotifier.notify_shutdown(reason: str = 'Normal shutdown') -> None` | Send shutdown notification. |
| `LiveTradingNotifier.notify_signal(signal: dict, executed: bool, error: str \| None = None) -> None` | Send signal notification. |
| `LiveTradingNotifier.notify_safety_violation(reason: str) -> None` | Send safety check violation notification. |
| `LiveTradingNotifier.notify_connection_error(error: str) -> None` | Send connection error notification. |
| `LiveTradingNotifier.notify_daily_summary(trades: int, profit: float, positions: int) -> None` | Send daily summary notification. |
| `LiveTradingNotifier.test_connection() -> bool` | Test notification tools. |
| `LiveTradingNotifier.from_database(user_id: int, db_path: str = 'data/database/haruquant.db') -> 'LiveTradingNotifier'` | Create LiveTradingNotifier from database credentials. |


## FEAT-EXEC-30: Position Manager (app.services.execution.live.position_manager)

| Function | Purpose |
|----------|---------|
| `PositionManager.__init__(client: 'MT5Client', magic_number: int) -> None` | Initialize position manager. |
| `PositionManager.refresh_positions() -> None` | Query MT5 for all positions with our magic number. |
| `PositionManager.get_positions_by_type(position_type: str) -> list[dict]` | Get all positions of specified type. |
| `PositionManager.should_allow_entry(max_positions: int) -> bool` | Check if new position allowed based on position limit. |
| `PositionManager.get_positions_to_close(signal_type: str) -> list[int]` | Get position tickets to close based on exit signal. |
| `PositionManager.close_position(ticket: int) -> bool` | Close a specific position by ticket using Trade module. |
| `PositionManager.close_all_positions(position_type: str \| None = None) -> int` | Close all positions, optionally filtered by type. |
| `PositionManager.close_positions_by_symbol(symbol: str) -> int` | Close all positions for a specific symbol. |
| `PositionManager.total_positions() -> int` | Get total number of open positions. |
| `PositionManager.get_all_positions() -> list[dict]` | Get all open positions. |
| `PositionManager.has_position_for_symbol(symbol: str) -> bool` | Check if any position exists for given symbol. |
| `PositionManager.get_position_summary() -> dict[str, int]` | Get summary of positions by type. |


## FEAT-EXEC-31: Live Trading Entry Point (app.services.execution.live.run)

| Function | Purpose |
|----------|---------|
| `parse_arguments()` | Parse command-line arguments. |
| `validate_config_path(config_path: str) -> bool` | Validate configuration file exists. |
| `setup_engine(config_path: str) -> MultiStrategyEngine \| None` | Initialize and setup the trading engine. |
| `register_signal_handlers(engine: MultiStrategyEngine) -> None` | Register signal handlers for graceful shutdown. |
| `print_startup_info(engine: MultiStrategyEngine) -> None` | Print engine startup information. |
| `main() -> int` | Execute main entry point logic. |


## FEAT-EXEC-32: Secret-provider helpers for live configuration (app.services.execution.live.secrets)

| Function | Purpose |
|----------|---------|
| `SecretProviderError` (model) | Raised when a secret cannot be resolved from configured providers. |
| `SecretReference` (model) | Represent SecretReference behavior in execution service workflows. |
| `parse_secret_reference(value: str) -> SecretReference \| None` | Parse secret references of format: keyring://<service>/<account> |
| `resolve_secret_reference(value: str) -> str` | Perform the resolve_secret_reference execution service operation. |
| `get_secret(provider: str, service: str, account: str) -> str` | Perform the get_secret execution service operation. |


## FEAT-EXEC-33: Live Trading Session Manager (app.services.execution.live.session)

| Function | Purpose |
|----------|---------|
| `ExecutionEngineWrapper.__init__(engine: 'MultiStrategyEngine') -> None` | Initialize wrapper with engine instance. |
| `ExecutionEngineWrapper.close_position(position: Any, reason: str = 'manual') -> bool` | Close a specific position. |
| `LiveTradingSession.__init__(session_id: int, mt5_client: 'MT5Client', db: 'DatabaseManager') -> None` | Initialize session. |
| `LiveTradingSession.execution_engine` | Expose execution engine for API calls. |
| `LiveTradingSession.start() -> None` | Start the live trading session. |
| `LiveTradingSession.stop() -> None` | Stop the session. |
| `LiveTradingSession.pause() -> None` | Pause the session (disable trading, keep monitoring). |
| `LiveTradingSession.resume() -> None` | Resume the session. |
| `LiveTradingSession.get_status() -> dict[str, Any]` | Get lightweight real-time status. |
| `LiveTradingSession.get_statistics() -> dict[str, Any]` | Get comprehensive statistics. |


## FEAT-EXEC-34: Signal Processor (app.services.execution.live.signal_processor)

| Function | Purpose |
|----------|---------|
| `SignalProcessor.__init__(strategy: BaseStrategy, max_bars: int = 500) -> None` | Initialize signal processor. |
| `SignalProcessor.initialize(historical_data: pd.DataFrame) -> bool` | Initialize with historical data. |
| `SignalProcessor.update_with_new_bar(new_bar: pd.Series) -> SignalDict \| None` | Update rolling window with new bar and check for signals. |
| `SignalProcessor.get_current_data() -> pd.DataFrame \| None` | Get current rolling window of data. |
| `SignalProcessor.get_last_signal() -> SignalDict \| None` | Get signal from the last bar in current data. |
| `SignalProcessor.is_initialized() -> bool` | Check if processor is initialized. |


## FEAT-EXEC-35: State Management (app.services.execution.live.state_manager)

| Function | Purpose |
|----------|---------|
| `StateManager.__init__(state_file: str) -> None` | Initialize state manager. |
| `StateManager.is_enabled() -> bool` | Check if trading is enabled. |
| `StateManager.is_paused() -> bool` | Check if trading is paused. |
| `StateManager.pause() -> None` | Pause trading temporarily. |
| `StateManager.resume() -> None` | Resume trading from pause. |
| `StateManager.enable() -> None` | Enable trading. |
| `StateManager.disable() -> None` | Disable trading completely. |
| `StateManager.update_last_run(timestamp: datetime \| None = None) -> None` | Update last run timestamp. |
| `StateManager.get_last_run() -> datetime \| None` | Get last run timestamp. |
| `StateManager.increment_trade_count() -> int` | Increment daily trade count and return new count. |
| `StateManager.get_trade_count_today() -> int` | Get today's trade count. |
| `StateManager.reset_daily_counter() -> None` | Manually reset daily trade counter. |
| `StateManager.get_state_summary() -> dict` | Get summary of current state. |


## FEAT-EXEC-36: Trade Executor (app.services.execution.live.trade_executor)

| Function | Purpose |
|----------|---------|
| `TradeExecutor.__init__(trade: Trade, symbol_info: object, position_manager: PositionManager, symbol: str, volume: float, filling_mode: int \| None = None, max_retries: int = 3) -> None` | Initialize trade executor. |
| `TradeExecutor.execute_signal(signal: dict) -> tuple[bool, str]` | Execute trade based on signal. |


## FEAT-EXEC-37: Agent-facing live execution tools (app.services.execution.live_execution_tools)

| Function | Purpose |
|----------|---------|
| `submit_live_order(**kwargs: Any) -> dict[str, Any]` | Submit a live order request after approval gates. |
| `modify_live_order(**kwargs: Any) -> dict[str, Any]` | Modify a live broker order after approval gates. |
| `close_live_position(**kwargs: Any) -> dict[str, Any]` | Close a live broker position after approval gates. |
| `cancel_live_order(**kwargs: Any) -> dict[str, Any]` | Cancel a live pending order after approval gates. |
| `reduce_live_exposure(**kwargs: Any) -> dict[str, Any]` | Reduce live broker exposure after approval gates. |
| `pause_live_strategy(**kwargs: Any) -> dict[str, Any]` | Pause a live strategy after approval gates. |
| `resume_live_strategy(**kwargs: Any) -> dict[str, Any]` | Resume a live strategy after approval gates. |
| `sync_live_positions(**kwargs: Any) -> dict[str, Any]` | Synchronize live positions from broker state. |
| `reconcile_broker_state(**kwargs: Any) -> dict[str, Any]` | Reconcile internal execution state against broker state. |
| `build_live_execution_report(**kwargs: Any) -> dict[str, Any]` | Build a live execution result report request. |


## FEAT-EXEC-38: Symbol metadata cache models for pre-submit execution validation (app.services.execution.metadata_cache)

| Function | Purpose |
|----------|---------|
| `SymbolMetadataCacheEntry` (model) | Cached symbol metadata required by execution readiness checks. |
| `SymbolMetadataCache.__init__() -> None` | Small in-memory metadata cache keyed by symbol. |
| `SymbolMetadataCache.put(entry: SymbolMetadataCacheEntry) -> SymbolMetadataCacheEntry` | Perform the put execution service operation. |
| `SymbolMetadataCache.get(symbol: str) -> SymbolMetadataCacheEntry \| None` | Perform the get execution service operation. |
| `SymbolMetadataCache.get_many(symbols: tuple[str, ...]) -> dict[str, SymbolMetadataCacheEntry]` | Perform the get_many execution service operation. |


## FEAT-EXEC-39: Alert classification helpers for ingested observations (app.services.execution.monitoring.classification)

| Function | Purpose |
|----------|---------|
| `AlertClassification` (model) | Normalized alert routing decision from one observation event. |
| `classify_alert(observation: ObservationEvent) -> AlertClassification` | Classify an observation into warning, incident, or kill-switch severity. |


## FEAT-EXEC-40: Incident creation and lifecycle helpers (app.services.execution.monitoring.incidents)

| Function | Purpose |
|----------|---------|
| `IncidentLifecycleService.create(*, severity: str, alert_type: str, source: str, summary: str, recommended_action: str \| None = None, metadata_json: str = '{}') -> IncidentRecord` | Perform the create execution service operation. |
| `IncidentLifecycleService.transition(*, incident_id: str, next_state: str, resolved_at: str \| None = None, recommended_action: str \| None = None) -> IncidentRecord` | Perform the transition execution service operation. |


## FEAT-EXEC-41: Observation ingestion pipeline for control-plane monitoring (app.services.execution.monitoring.ingestion)

| Function | Purpose |
|----------|---------|
| `ObservationRecord` (model) | Represent ObservationRecord behavior in execution service workflows. |
| `ObservationIngestionService.__init__(db_path: str \| Path) -> None` | Persist canonical observation events into the core observation table. |
| `ObservationIngestionService.ingest(observation: ObservationEvent) -> ObservationRecord` | Perform the ingest execution service operation. |


## FEAT-EXEC-42: Stale-state detection helpers (app.services.execution.monitoring.stale_state)

| Function | Purpose |
|----------|---------|
| `StaleStateDetection` (model) | Result of stale-state monitoring. |
| `detect_stale_state(*, observed_at: datetime, max_age_seconds: int, clock: Clock \| None = None) -> StaleStateDetection` | Escalate stale snapshots into incident-grade monitoring signals. |


## FEAT-EXEC-43: Downstream tool-health monitoring helpers (app.services.execution.monitoring.tool_health)

| Function | Purpose |
|----------|---------|
| `ToolHealthResult` (model) | Aggregated health status for one downstream tool group. |
| `evaluate_tool_health(tool_statuses: dict[str, str]) -> ToolHealthResult` | Collapse downstream tool states into a stable degraded/healthy result. |


## FEAT-EXEC-44: Workflow-timeout detection helpers (app.services.execution.monitoring.workflow_timeout)

| Function | Purpose |
|----------|---------|
| `WorkflowTimeoutResult` (model) | Result of workflow timeout detection and transition. |
| `WorkflowTimeoutService.__init__(repository: WorkflowRepository) -> None` | Detect and apply workflow timeout transitions. |
| `WorkflowTimeoutService.evaluate(workflow: WorkflowRecord, *, clock: Clock \| None = None) -> WorkflowTimeoutResult` | Perform the evaluate execution service operation. |


## FEAT-EXEC-45: Broker response normalization for execution receipts (app.services.execution.normalization)

| Function | Purpose |
|----------|---------|
| `normalize_broker_response(response: Any) -> dict[str, Any]` | Normalize MT5 order-send style responses into a stable receipt shape. |


## FEAT-EXEC-46: Deterministic order router for guarded live execution (app.services.execution.order_router)

| Function | Purpose |
|----------|---------|
| `OrderRouter.route_order(*, order: dict[str, Any], approval_token: dict[str, Any] \| None, live_config: dict[str, Any], broker_status: dict[str, Any], kill_switch_status: str) -> dict[str, Any]` | Perform the route_order execution service operation. |


## FEAT-EXEC-47: Agent-facing paper trading execution tools (app.services.execution.paper_trading_tools)

| Function | Purpose |
|----------|---------|
| `start_paper_strategy(**kwargs: Any) -> dict[str, Any]` | Enable a strategy in paper trading mode. |
| `stop_paper_strategy(**kwargs: Any) -> dict[str, Any]` | Disable a strategy in paper trading mode. |
| `submit_paper_order(**kwargs: Any) -> dict[str, Any]` | Submit a simulated paper order request. |
| `modify_paper_order(**kwargs: Any) -> dict[str, Any]` | Modify a simulated paper order request. |
| `close_paper_position(**kwargs: Any) -> dict[str, Any]` | Close a simulated paper position. |
| `record_paper_fill(**kwargs: Any) -> dict[str, Any]` | Record a simulated paper fill. |
| `calculate_paper_slippage(**kwargs: Any) -> dict[str, Any]` | Calculate simulated or observed paper slippage. |
| `compare_paper_vs_backtest(**kwargs: Any) -> dict[str, Any]` | Compare paper trading behavior against backtest expectations. |
| `build_paper_trading_report(**kwargs: Any) -> dict[str, Any]` | Build a paper trading graduation report request. |


## FEAT-EXEC-48: Latency budget monitoring helpers (app.services.execution.performance.latency)

| Function | Purpose |
|----------|---------|
| `LatencySample` (model) | Represent LatencySample behavior in execution service workflows. |
| `LatencyAlert` (model) | Represent LatencyAlert behavior in execution service workflows. |
| `LatencyBudgetMonitor.__init__(*, threshold_ms: int) -> None` | Raise alerts when observed latency exceeds a configured budget. |
| `LatencyBudgetMonitor.evaluate(sample: LatencySample) -> LatencyAlert \| None` | Perform the evaluate execution service operation. |
| `LatencyBudgetMonitor.evaluate_many(samples: tuple[LatencySample, ...]) -> tuple[LatencyAlert, ...]` | Perform the evaluate_many execution service operation. |


## FEAT-EXEC-49: Hot snapshot caching with freshness metadata (app.services.execution.performance.snapshot_cache)

| Function | Purpose |
|----------|---------|
| `SnapshotCacheEntry.freshness(*, clock: Clock \| None = None) -> FreshnessWindow` | Perform the freshness execution service operation. |
| `HotSnapshotCache.__init__(*, clock: Clock \| None = None) -> None` | Small in-memory stand-in for a Redis-backed hot snapshot cache. |
| `HotSnapshotCache.put(entry: SnapshotCacheEntry[SnapshotT]) -> SnapshotCacheEntry[SnapshotT]` | Perform the put execution service operation. |
| `HotSnapshotCache.get(key: str) -> SnapshotCacheEntry[SnapshotT] \| None` | Perform the get execution service operation. |


## FEAT-EXEC-50: Pre-send validation orchestration (app.services.execution.pre_send)

| Function | Purpose |
|----------|---------|
| `PreSendValidationRequest` (model) | Inputs required to orchestrate the execution readiness chain. |
| `run_pre_send_validation(request: PreSendValidationRequest, *, metadata_cache: SymbolMetadataCache, clock: Clock \| None = None) -> ReadinessAggregateResult` | Run the full fail-closed readiness chain before broker send. |


## FEAT-EXEC-51: Execution readiness validators for pre-submit broker safety checks (app.services.execution.readiness)

| Function | Purpose |
|----------|---------|
| `ReadinessCheckResult` (model) | Simple allow/deny result for one readiness validator. |
| `ReadinessAggregateResult` (model) | Combined readiness verdict across all pre-send validators. |
| `validate_market_open(metadata: SymbolMetadataCacheEntry) -> ReadinessCheckResult` | Reject execution when the market is closed for the target symbol. |
| `validate_symbol_tradability(metadata: SymbolMetadataCacheEntry) -> ReadinessCheckResult` | Reject execution when the symbol is currently not tradable. |
| `validate_price_freshness(metadata: SymbolMetadataCacheEntry, *, clock: Clock \| None = None) -> ReadinessCheckResult` | Reject execution when the cached price/metadata snapshot is stale. |
| `validate_stop_and_freeze_levels(metadata: SymbolMetadataCacheEntry, *, stop_distance_points: float \| None = None, modify_distance_points: float \| None = None) -> ReadinessCheckResult` | Reject execution when requested stop or modification distances violate broker rules. |
| `validate_fill_mode_compatibility(metadata: SymbolMetadataCacheEntry, *, requested_fill_mode: str) -> ReadinessCheckResult` | Reject execution when the requested fill mode is unsupported for the symbol. |
| `validate_terminal_connectivity(*, connected: bool) -> ReadinessCheckResult` | Reject execution when terminal connectivity is unavailable. |
| `validate_risk_decision_for_execution(risk_decision: RiskAssessmentDecision, *, approved_proposal: TradeProposal, current_proposal: TradeProposal, clock: Clock \| None = None) -> ReadinessCheckResult` | Reject execution when the risk decision is stale or no longer matches the proposal. |
| `aggregate_readiness_results(checks: tuple[ReadinessCheckResult, ...]) -> ReadinessAggregateResult` | Fail closed when any readiness validator rejects execution. |


## FEAT-EXEC-52: Agent-facing execution readiness tools (app.services.execution.readiness_tools)

| Function | Purpose |
|----------|---------|
| `validate_order_request(**kwargs: Any) -> dict[str, Any]` | Validate a proposed order request before execution planning. |
| `validate_execution_environment(**kwargs: Any) -> dict[str, Any]` | Validate that execution is targeting an allowed environment. |
| `validate_order_size(**kwargs: Any) -> dict[str, Any]` | Validate that proposed order volume is positive. |
| `validate_order_price(**kwargs: Any) -> dict[str, Any]` | Validate that proposed order price is positive. |
| `validate_stop_loss_take_profit(**kwargs: Any) -> dict[str, Any]` | Validate stop-loss and take-profit placement relative to side and price. |
| `estimate_transaction_cost(**kwargs: Any) -> dict[str, Any]` | Estimate spread, commission, and slippage cost. |
| `estimate_slippage(**kwargs: Any) -> dict[str, Any]` | Estimate expected slippage from spread and volatility. |
| `build_execution_plan(**kwargs: Any) -> dict[str, Any]` | Build a deterministic execution plan from a validated order request. |
| `run_execution_readiness_check(**kwargs: Any) -> dict[str, Any]` | Evaluate a list of readiness checks before execution. |
| `validate_strategy_runtime_config(**kwargs: Any) -> dict[str, Any]` | Validate a strategy runtime config request. |
| `validate_broker_symbol_mapping(**kwargs: Any) -> dict[str, Any]` | Validate internal symbol to broker symbol mapping. |


## FEAT-EXEC-53: Execution receipt normalization and persistence helpers (app.services.execution.receipts)

| Function | Purpose |
|----------|---------|
| `NormalizedExecutionReceipt` (model) | Normalized broker receipt plus persisted execution record. |
| `ExecutionReceiptService.__init__(repository: ExecutionRepository) -> None` | Normalize broker responses and persist canonical execution receipts. |
| `ExecutionReceiptService.persist_receipt(*, execution_intent_id: str, broker_response: Any, raw_receipt_ref: str \| None = None) -> NormalizedExecutionReceipt` | Perform the persist_receipt execution service operation. |


## FEAT-EXEC-54: Broker truth fetch helpers for reconciliation (app.services.execution.reconciliation.broker_truth)

| Function | Purpose |
|----------|---------|
| `BrokerReadTools.get_account_info() -> dict[str, Any]` | Perform the get_account_info execution service operation. |
| `BrokerReadTools.list_orders() -> list[dict[str, Any]]` | Perform the list_orders execution service operation. |
| `BrokerReadTools.list_positions() -> list[dict[str, Any]]` | Perform the list_positions execution service operation. |
| `BrokerTruthSnapshot` (model) | Represent BrokerTruthSnapshot behavior in execution service workflows. |
| `BrokerTruthFetcher.__init__(read_tools: BrokerReadTools) -> None` | Fetches current broker truth for a pending client order reference. |
| `BrokerTruthFetcher.fetch_for_client_order_id(client_order_id: str, *, account_state: dict[str, Any] \| None = None) -> BrokerTruthSnapshot` | Perform the fetch_for_client_order_id execution service operation. |


## FEAT-EXEC-55: Local-vs-broker truth comparison for reconciliation (app.services.execution.reconciliation.comparison)

| Function | Purpose |
|----------|---------|
| `ReconciliationResultState` (model) | Represent ReconciliationResultState behavior in execution service workflows. |
| `LocalExecutionTruth` (model) | Represent LocalExecutionTruth behavior in execution service workflows. |
| `ReconciliationComparison` (model) | Represent ReconciliationComparison behavior in execution service workflows. |
| `build_local_execution_truth(intent: ExecutionIntentRecord, latest_receipt: ExecutionReceiptRecord \| None = None) -> LocalExecutionTruth` | Perform the build_local_execution_truth execution service operation. |
| `compare_execution_truth(*, local_truth: LocalExecutionTruth, broker_truth: BrokerTruthSnapshot) -> ReconciliationComparison` | Perform the compare_execution_truth execution service operation. |


## FEAT-EXEC-56: Incident raising for unresolved reconciliation divergence (app.services.execution.reconciliation.incidents)

| Function | Purpose |
|----------|---------|
| `ReconciliationIncidentService.__init__(db_path: str \| Path) -> None` | Raises operator-visible incidents for unresolved broker divergence. |
| `ReconciliationIncidentService.raise_for_unresolved_divergence(*, execution_intent_id: str, comparison: ReconciliationComparison) -> IncidentRecord` | Perform the raise_for_unresolved_divergence execution service operation. |


## FEAT-EXEC-57: Persistence helpers for reconciliation runs (app.services.execution.reconciliation.persistence)

| Function | Purpose |
|----------|---------|
| `ReconciliationPersistenceService.__init__(db_path: str \| Path) -> None` | Persist append-only reconciliation results. |
| `ReconciliationPersistenceService.save(*, execution_intent_id: str, run_reason: str, comparison: ReconciliationComparison, incident_id: str \| None = None, completed_at: str \| None = None) -> ReconciliationRunRecord` | Perform the save execution service operation. |


## FEAT-EXEC-58: Retry guard rules for uncertain execution state (app.services.execution.reconciliation.retry_guard)

| Function | Purpose |
|----------|---------|
| `RetryGuardDecision` (model) | Represent RetryGuardDecision behavior in execution service workflows. |
| `evaluate_retry_guard(comparison: ReconciliationComparison) -> RetryGuardDecision` | Fail closed when broker acknowledgement or reconciliation remains uncertain. |


## FEAT-EXEC-59: Startup-time reconciliation loading helpers (app.services.execution.reconciliation.startup)

| Function | Purpose |
|----------|---------|
| `ReconciliationStartupLoader.__init__(execution_repository: ExecutionRepository, *, in_flight_statuses: Iterable[str] = DEFAULT_IN_FLIGHT_EXECUTION_STATUSES) -> None` | Loads execution intents that must be reconciled before live recovery. |
| `ReconciliationStartupLoader.load_in_flight_execution_intents() -> list[ExecutionIntentRecord]` | Perform the load_in_flight_execution_intents execution service operation. |


## FEAT-EXEC-60: Execution send service over the MT5 MCP boundary (app.services.execution.send_service)

| Function | Purpose |
|----------|---------|
| `BrokerSendGateway.place_order(request: dict[str, Any]) -> Any` | Place an order through the broker gateway. |
| `BrokerSendGateway.modify_position(request: dict[str, Any]) -> Any` | Modify a position through the broker gateway. |
| `BrokerSendGateway.partial_close(request: dict[str, Any]) -> Any` | Partially close a position through the broker gateway. |
| `BrokerSendGateway.full_close(request: dict[str, Any]) -> Any` | Fully close a position through the broker gateway. |
| `BrokerSendGateway.cancel_order(request: dict[str, Any]) -> Any` | Cancel an order through the broker gateway. |
| `BrokerSendResult` (model) | Raw broker send result with the submitted payload echo. |
| `ExecutionSendService.__init__(gateway: BrokerSendGateway) -> None` | Submit execution intents through the MT5 MCP mutating tool boundary. |
| `ExecutionSendService.send(intent: ExecutionIntent) -> BrokerSendResult` | Perform the send execution service operation. |


## FEAT-EXEC-61: Shadow-mode execution gating (app.services.execution.shadow.execution)

| Function | Purpose |
|----------|---------|
| `ShadowExecutionRequest` (model) | Execution request with an explicit shadow-mode flag. |
| `ShadowExecutionDecision` (model) | Stable shadow execution outcome. |
| `ShadowExecutionService.__init__(send_service: ExecutionSendService) -> None` | Fail-closed execution gate for production-like shadow workflows. |
| `ShadowExecutionService.execute(request: ShadowExecutionRequest) -> ShadowExecutionDecision` | Perform the execute execution service operation. |


## FEAT-EXEC-62: Production-like snapshot feed assembly for shadow workflows (app.services.execution.shadow.feeds)

| Function | Purpose |
|----------|---------|
| `ShadowDataFeed` (model) | Normalized shadow workflow feed built from live-shaped snapshots. |
| `build_shadow_data_feed(*, account_snapshot: AccountSnapshot, portfolio_snapshot: PortfolioSnapshot, market_snapshot: MarketSnapshot, environment: str = 'shadow') -> ShadowDataFeed` | Package production-like snapshots into one shadow workflow feed payload. |


## FEAT-EXEC-63: Expected-versus-realized comparison reporting for shadow workflows (app.services.execution.shadow.reporting)

| Function | Purpose |
|----------|---------|
| `ShadowComparisonReport` (model) | Stable shadow comparison summary. |
| `build_shadow_comparison_report(*, expected_fill_price: float, realized_fill_price: float, expected_pnl: float, realized_pnl: float) -> ShadowComparisonReport` | Compare expected shadow outcomes with realized market outcomes. |


## FEAT-EXEC-64: Governed paper-execution path for AI chat action drafts (app.services.execution.trade_action_governor)

| Function | Purpose |
|----------|---------|
| `GovernorApprovalState` (model) | Represent GovernorApprovalState behavior in execution service workflows. |
| `GovernedPaperExecutionResult` (model) | Represent GovernedPaperExecutionResult behavior in execution service workflows. |
| `TradeActionGovernor.__init__(db_path: str, *, broker_gateway: Any \| None = None) -> None` | Convert approved AI chat order drafts into governed paper execution. |
| `TradeActionGovernor.execute_paper_action_draft(*, user_id: int \| str, draft_id: str, terminal_connected: bool = True) -> GovernedPaperExecutionResult` | Perform the execute_paper_action_draft execution service operation. |


## FEAT-EXEC-65: FILE: src/util/validators.py (app.services.execution.trade_validators)

| Function | Purpose |
|----------|---------|
| `ENUM_ORDER_TYPE` (model) | Represent ENUM_ORDER_TYPE behavior in execution service workflows. |
| `ENUM_TRADE_REQUEST_ACTIONS` (model) | Represent ENUM_TRADE_REQUEST_ACTIONS behavior in execution service workflows. |
| `RuleValidationResult` (model) | Represent RuleValidationResult behavior in execution service workflows. |
| `TradeValidationResult` (model) | Represent TradeValidationResult behavior in execution service workflows. |
| `SymbolTickData` (model) | Represent SymbolTickData behavior in execution service workflows. |
| `ValidationRules` (model) | Represent ValidationRules behavior in execution service workflows. |
| `ValidationContext` (model) | Represent ValidationContext behavior in execution service workflows. |
| `TradeRequestPayload` (model) | Represent TradeRequestPayload behavior in execution service workflows. |
| `CredentialsPayload` (model) | Represent CredentialsPayload behavior in execution service workflows. |
| `BacktestState` (model) | Represent BacktestState behavior in execution service workflows. |
| `validate_action_type(action: int, order_type: int) -> TradeValidationResult` | Perform the validate_action_type execution service operation. |
| `validate_submission_inputs(symbol: str, volume: float, symbol_info: Any \| None, bid: float, ask: float) -> TradeValidationResult` | Perform the validate_submission_inputs execution service operation. |
| `validate_trade_request(request: Any, account: Any, symbol_info: Any \| None) -> TradeValidationResult` | Perform the validate_trade_request execution service operation. |
| `validate_symbol(symbol: str, ctx: ValidationContext) -> RuleValidationResult` | Perform the validate_symbol execution service operation. |
| `validate_volume_basic(volume: float) -> RuleValidationResult` | Perform the validate_volume_basic execution service operation. |
| `validate_volume_symbol_limits(volume: float, symbol_info: Any) -> RuleValidationResult` | Perform the validate_volume_symbol_limits execution service operation. |
| `validate_volume_step(volume: float, symbol_info: Any) -> RuleValidationResult` | Perform the validate_volume_step execution service operation. |
| `validate_volume_format(volume_text: str, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_volume_format execution service operation. |
| `validate_price_format(price_text: str, ctx: ValidationContext) -> RuleValidationResult` | Perform the validate_price_format execution service operation. |
| `validate_volume(volume: float, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_volume execution service operation. |
| `validate_price(price: float, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_price execution service operation. |
| `validate_order_type(order_type: Any) -> RuleValidationResult` | Perform the validate_order_type execution service operation. |
| `validate_magic(magic: int, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_magic execution service operation. |
| `validate_slippage(slippage_points: int, requested_price: float, order_type: int, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_slippage execution service operation. |
| `validate_expiration_unix(expiration_unix_sec: int, now_unix_sec: int) -> RuleValidationResult` | Perform the validate_expiration_unix execution service operation. |
| `validate_expiration_mode(expiration_mode: str) -> RuleValidationResult` | Perform the validate_expiration_mode execution service operation. |
| `validate_timeframe(timeframe: Any) -> RuleValidationResult` | Perform the validate_timeframe execution service operation. |
| `validate_date_range_unix(start_unix_sec: int, end_unix_sec: int \| None, now_unix_sec: int) -> RuleValidationResult` | Perform the validate_date_range_unix execution service operation. |
| `validate_stop_loss(stop_loss: float, entry_price: float \| None, order_type: int \| None, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_stop_loss execution service operation. |
| `validate_take_profit(take_profit: float, entry_price: float \| None, order_type: int \| None, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_take_profit execution service operation. |
| `validate_trade_request_payload(request: TradeRequestPayload, ctx: ValidationContext, rules: ValidationRules) -> RuleValidationResult` | Perform the validate_trade_request_payload execution service operation. |
| `validate_credentials(credentials: CredentialsPayload) -> RuleValidationResult` | Perform the validate_credentials execution service operation. |
| `validate_margin(margin_required: float, ctx: ValidationContext) -> RuleValidationResult` | Perform the validate_margin execution service operation. |
| `validate_ticket(ticket: int) -> RuleValidationResult` | Perform the validate_ticket execution service operation. |
| `validate_max_orders(open_orders: int, account_limit: int \| None, ctx: ValidationContext) -> RuleValidationResult` | Perform the validate_max_orders execution service operation. |
| `validate_symbol_volume(symbol_volume: float, volume_limit: float \| None, ctx: ValidationContext) -> RuleValidationResult` | Perform the validate_symbol_volume execution service operation. |
| `open_position_validations(request: Any, account: Any, symbol_info: Any \| None) -> TradeValidationResult` | Perform the open_position_validations execution service operation. |
| `modify_position_validations(symbol: str, ticket: int, state: BacktestState \| None, sl: float = 0.0, tp: float = 0.0, symbol_info: Any \| None = None) -> TradeValidationResult` | Perform the modify_position_validations execution service operation. |
| `open_pending_order_validations(request: Any, account: Any, symbol_info: Any \| None) -> TradeValidationResult` | Perform the open_pending_order_validations execution service operation. |
| `modify_pending_order_validations(ticket: int, price: float, sl: float, tp: float, expiration: int, state: BacktestState \| None, symbol_info: Any \| None) -> TradeValidationResult` | Perform the modify_pending_order_validations execution service operation. |
| `delete_pending_order_validations(ticket: int, state: BacktestState \| None) -> TradeValidationResult` | Perform the delete_pending_order_validations execution service operation. |
| `close_position_validations(symbol: str, ticket: int, state: BacktestState \| None) -> TradeValidationResult` | Perform the close_position_validations execution service operation. |
| `close_partial_position_validations(symbol: str, ticket: int, volume: float, state: BacktestState \| None) -> TradeValidationResult` | Perform the close_partial_position_validations execution service operation. |


## FEAT-EXEC-66: Flat public trading tools (app.services.execution.trading)

| Function | Purpose |
|----------|---------|
| `TradeResult` (model) | Small result object returned by low-level trading operations. |
| `Trade.__init__(api: Any \| None = None) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetExpertMagicNumber(magic: int) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.LogLevel(level: int \| None = None) -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetDeviationInPoints(deviation: int) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetTypeFilling(filling: Any) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetTypeFillingBySymbol(symbol: str) -> bool` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetTypeTime(type_time: Any) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetAsyncMode(mode: bool) -> None` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SetMarginMode() -> bool` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.PositionOpen(symbol: str, order_type: Any, volume: float, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.OrderOpen(symbol: str, order_type: Any, volume: float, price: float, sl: float = 0.0, tp: float = 0.0, stoplimit: float = 0.0, type_time: Any \| None = None, expiration: datetime \| None = None, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.OrderModify(ticket: int, price: float, sl: float = 0.0, tp: float = 0.0, stoplimit: float = 0.0, type_time: Any \| None = None, expiration: datetime \| None = None) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.OrderDelete(ticket: int) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.PositionModify(symbol: str \| None = None, ticket: int \| None = None, sl: float = 0.0, tp: float = 0.0) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.PositionClose(symbol: str \| None = None, ticket: int \| None = None) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.PositionClosePartial(symbol: str \| None = None, ticket: int \| None = None, volume: float = 0.0) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.PositionCloseBy(ticket: int, ticket_by: int) -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.Buy(volume: float, symbol: str, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.Sell(volume: float, symbol: str, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.BuyLimit(volume: float, symbol: str, price: float, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.BuyStop(volume: float, symbol: str, price: float, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SellLimit(volume: float, symbol: str, price: float, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.SellStop(volume: float, symbol: str, price: float, sl: float = 0.0, tp: float = 0.0, comment: str = '') -> TradeResult` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.Request() -> dict[str, Any]` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.RequestAction() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.RequestOrder() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.RequestSymbol() -> str` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.RequestVolume() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.RequestPrice() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.CheckResult() -> dict[str, Any]` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.CheckResultRetcode() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.Result() -> dict[str, Any]` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultRetcode() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultRetcodeDescription() -> str` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultOrder() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultDeal() -> int` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultVolume() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultPrice() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultBid() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultAsk() -> float` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `Trade.ResultComment() -> str` | Low-level MT5/simulator trade adapter retained inside trading.py. |
| `trading_connect(provider: str = 'mt5', user_id: int = 1, mt5_login: int \| None = None, live_enabled: bool = False, url: str \| None = None) -> dict[str, Any]` | Connect and hold one active trading/data bridge. |
| `trading_disconnect() -> dict[str, Any]` | Disconnect and clear the active trading/data bridge. |
| `trading_is_connected() -> dict[str, Any]` | Return the currently active trading/data bridge connection status. |
| `trading_place_order(provider: str \| None = None, symbol: str = 'EURUSD', order_type: str = 'BUY', volume: float = 0.01, price: float = 0.0, sl: float = 0.0, tp: float = 0.0, live_enabled: bool = False) -> dict[str, Any]` | Submit a broker order through a fail-closed execution bridge. |
| `place_market_order(provider: str \| None = None, symbol: str = 'EURUSD', side: str = 'BUY', volume: float = 0.01, sl: float = 0.0, tp: float = 0.0, comment: str = '', live_enabled: bool = False) -> dict[str, Any]` | Place a market order through the active broker bridge. |
| `modify_pending_order(provider: str \| None = None, order_id: str = '', price: float = 0.0, sl: float = 0.0, tp: float = 0.0, expiration: str \| None = None, live_enabled: bool = False) -> dict[str, Any]` | Modify price/SL/TP/expiration on a pending order. |
| `place_pending_order(*args: Any, mode: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Place pending order operation. |
| `modify_position(*args: Any, mode: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Modify position operation. |
| `close_position(*args: Any, mode: str \| None = None, **kwargs: Any) -> dict[str, Any]` | Close position. |
| `execute_trade(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Execute trade operation. |
| `preview_trade(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Preview trade operation. |
| `evaluate_what_if(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Evaluate what if. |
| `partial_close_position(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Partial close position operation. |
| `modify_order(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Modify order operation. |
| `delete_order(*args: Any, mode: str \| None = 'sim', **kwargs: Any) -> dict[str, Any]` | Delete order. |
| `cancel_pending_order(provider: str \| None = None, order_id: str = '', live_enabled: bool = False) -> dict[str, Any]` | Cancel a pending order through the active broker bridge. |
| `trading_position_info(provider: str \| None = None, symbol: str \| None = None, group: str \| None = None, ticket: int \| None = None, limit: int = 100, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe open positions for a trading provider. |
| `trading_order_info(provider: str \| None = None, symbol: str \| None = None, group: str \| None = None, ticket: int \| None = None, limit: int = 100, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe active or pending orders for a trading provider. |
| `trading_history_order_info(provider: str \| None = None, days: int = 30, group: str \| None = None, ticket: int \| None = None, symbol: str \| None = None, limit: int = 100, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe historical orders for a trading provider. |
| `trading_symbol_info(provider: str \| None = None, symbols: str = 'EURUSD', user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe symbol metadata for a trading provider. |
| `trading_terminal_info(provider: str \| None = None, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe terminal information for a trading provider. |
| `trading_order_calc_margin(provider: str \| None = None, order_type: int = 0, symbol: str = 'EURUSD', volume: float = 0.01, price: float = 0.0, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Calculate required margin for a provider order request. |
| `trading_order_calc_profit(provider: str \| None = None, order_type: int = 0, symbol: str = 'EURUSD', volume: float = 0.01, price_open: float = 0.0, price_close: float = 0.0, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Calculate projected profit for a provider order request. |
| `trading_deal_history(provider: str \| None = None, days: int = 30, group: str \| None = None, ticket: int \| None = None, symbol: str \| None = None, limit: int = 100, user_id: int = 1, mt5_login: int \| None = None, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe historical deal rows for a trading provider. |
| `trading_account_info(provider: str \| None = None, user_id: int = 1, mt5_login: int \| None = None, live_enabled: bool = False, shutdown: bool = True) -> dict[str, Any]` | Retrieve JSON-safe trading account information for a broker provider. |

