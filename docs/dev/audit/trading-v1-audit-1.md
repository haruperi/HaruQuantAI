# Trading — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** trading
* **Repository:** `haruperi/HaruQuantAI`
* **Repository snapshot:** `main` at commit `68851eb6898b229f49f1295c37748c63eefed3d3`
* **Package path:** `app/services/trading`
* **Tests path:** `tests/trading/unit/`
* **Integration tests:** `tests/trading/integration/`
* **Usage/examples path:** `tests/trading/usage/07_trading.py`
* **Files inspected:** 72 Python files in the package; package README; public `__init__.py` gates; key implementation files; current trading tests/usage file; relevant commit history; confirmed inbound analytics adapter; broker-router boundary files.
* **Related packages searched:** `app/services/brokers`, `app/services/analytics/adapters`, `app/services/risk` references, retired `app/services/live` and `app/services/trader` history, and shared `app/utils`.
* **Excluded:** generated files, caches, virtual environments, unrelated domains, and Version 2 requirements.
* **Audit limitations:**
  * GitHub repository code search returned no symbol/path hits for this repository, even for known exact symbols. Therefore, full repository-wide static caller searches, decorator/registry searches, and string-based import searches could not be completed through the search index.
  * A local clone could not be obtained because the execution environment could not resolve `github.com`. The package could not be executed and the test suite could not be run.
  * Commit comparisons and direct file fetches were available and were used to reconstruct the complete package file boundary, public export gates, tests, usage examples, migration history and major call paths.
  * Because production composition and deployment configuration were not available, this audit does **not** classify any item as dead code with High confidence. Items lacking an internal or non-test caller are marked **Test-only**, **Possibly used**, or **Unknown**.

## 2. Executive Summary

The Version 1 trading domain is not merely a broker wrapper. It provides a broker-neutral contract boundary, validated order and position actions, a sixteen-step live safety pipeline, a single broker mutation boundary, idempotency and state persistence, reconciliation, emergency controls, session coordination, promotion checks, monitoring utilities, read-only broker facades, security/redaction, and packaged-only AI tool metadata.

The strongest confirmed workflows are:

1. validating and packaging non-live or fail-closed requests without touching a broker;
2. reading broker account/symbol/order/position/history state through neutral facades;
3. evaluating a live request through the implemented gate chain and dispatching through the one broker mutation module;
4. reserving idempotency, journaling events and maintaining trade projections;
5. blocking retries after unknown broker outcomes until reconciliation.

The most important gap is explicit: Gate 7 can use `passthrough_risk_evaluator`, which passes every live request without a real pre-trade risk decision. `SignalProcessor` checks that a `risk_decision_id` string is present, but the passthrough evaluator does not verify that decision. The implementation therefore contains a complete-looking live path whose risk connection is optional and unconfirmed.

The most important structural problems are duplicate error hierarchies/mappers, duplicate `OrderIntent` concepts, inconsistent error-code registries, two competing base contract families, direct wall-clock/random use despite an injected determinism policy, a very large mixed-responsibility `contracts.py`, stale README example paths, import-time logging in subpackage facades, and a large amount of test/usage-covered functionality with no confirmed production composition root.

**Audit evidence quality:** High for package structure, public export surfaces, internal live call path and component behavior; Medium for cross-domain imports confirmed by direct file fetch; Low-to-Medium for production caller status and dynamic registrations because repository-wide indexed search and local execution were unavailable.

```text
Module folders: 11 | Files: 72 Python files | Public symbols: 316 explicit qualified facade exports (includes re-exports) | Symbols with confirmed callers: ≥123 (≥38.9%; confirmed in the usage file, mostly test/example rather than production) | Workflows found: 10
```

## 3. Actual Package Structure

```text
app/services/trading/
├── __init__.py — public facade; registry accessors
├── contracts.py — canonical contracts/enums/events/envelopes
├── errors.py — domain exceptions, retcode classification, retry delay
├── tool_registry.py — packaged-only AI tool metadata
├── actions/
│   ├── __init__.py
│   ├── _common.py — LiveGatePipeline, TradingActionDependencies, package/dispatch
│   ├── validation.py — validation models and validate_order_request
│   ├── orders.py — buy/sell/pending/modify/delete/OCO
│   ├── positions.py — position_open/close/modify/reduce_exposure
│   ├── controls.py — pause/resume/sync/shutdown/kill switches
│   └── emergency.py — cancel/close/flatten scopes
├── config/
│   ├── __init__.py
│   ├── models.py
│   ├── loader.py
│   ├── notifications.py
│   ├── secrets.py
│   └── security_profile.py
├── execution/
│   ├── __init__.py
│   ├── broker_capability_validation.py
│   ├── broker_dispatch.py
│   ├── coordinator.py
│   ├── rate_limiter.py
│   ├── reporting.py
│   ├── response_classifier.py
│   ├── shadow.py
│   └── state_machine.py
├── gates/
│   ├── __init__.py
│   ├── _common.py
│   ├── approval.py
│   ├── audit_and_compensation.py
│   ├── kill_switch.py
│   ├── live_pipeline.py
│   ├── pipeline.py
│   ├── policy_matrix.py
│   └── readiness.py
├── info/
│   ├── __init__.py
│   ├── _common.py
│   ├── _ticket.py
│   ├── account.py
│   ├── deal.py
│   ├── history_order.py
│   ├── order.py
│   ├── position.py
│   ├── symbol.py
│   └── terminal.py
├── security/
│   ├── __init__.py
│   ├── error_mapping.py
│   └── redaction_boundary.py
├── state/
│   ├── __init__.py
│   ├── ports.py
│   ├── event_journal.py
│   ├── idempotency.py
│   ├── manager.py
│   └── trade_store.py
├── reconciliation/
│   ├── __init__.py
│   ├── snapshots_and_compare.py
│   ├── authority_and_retry_guard.py
│   └── service.py
├── monitoring/
│   ├── __init__.py
│   ├── heartbeat_watchdog.py
│   ├── operational_signals.py
│   ├── service.py
│   ├── timeouts_and_staleness.py
│   └── tool_health.py
├── promotion/
│   ├── __init__.py
│   ├── ladder.py
│   └── preconditions.py
└── runtime/
    ├── __init__.py
    ├── coordination.py
    ├── cost_control.py
    ├── session_manager.py
    └── signal_processor.py
```

### Public export gates checked

**`app.services.trading` (39):**

`AccountInfo`, `AllocationVector`, `BrokerAcknowledgementEvent`, `BrokerDispatchEvent`, `DealInfo`, `ExecutionCoordinator`, `ExecutionReportEvent`, `FixExecutionState`, `HistoryOrderInfo`, `JsonObject`, `JsonValue`, `MutationCapability`, `NormalizedTradeResult`, `OrderInfo`, `OrderState`, `PositionInfo`, `PositionState`, `PromotionStage`, `QuoteSnapshot`, `ReconciliationResolutionEvent`, `RegulatoryTags`, `RetrySafety`, `SideEffectMode`, `SymbolInfo`, `TerminalInfo`, `TimeInForce`, `TradingAction`, `TradingCommandAccepted`, `TradingCommandRejected`, `TradingError`, `TradingMetadata`, `TradingRequestEnvelope`, `TradingResponseEnvelope`, `TradingRoute`, `TradingStatus`, `TradingToolDefinition`, `TradingToolRegistry`, `get_trading_public_catalog`, `get_trading_tool_registry`

**`app.services.trading.actions` (40):**

`AccountMarginContext`, `ConversionRateEvidence`, `DailyRailState`, `DefenseInDepthRailLimits`, `LiveGatePipeline`, `LocateSnapshot`, `MarketSessionEvidence`, `OrderIntent`, `OrderSide`, `OrderType`, `OrderValidationContext`, `OrderValidationResult`, `SymbolTradingConstraints`, `TradingActionDependencies`, `buy`, `buy_limit`, `buy_stop`, `cancel_all_orders`, `close_all_positions`, `flatten_account`, `flatten_strategy`, `flatten_symbol`, `order_delete`, `order_modify`, `pause_strategy`, `position_close`, `position_modify`, `position_open`, `reduce_exposure`, `resume_strategy`, `sell`, `sell_limit`, `sell_stop`, `shutdown`, `submit_oco_group`, `sync_positions`, `trigger_global_kill_switch`, `trigger_strategy_kill_switch`, `trigger_symbol_kill_switch`, `validate_order_request`

**`app.services.trading.execution` (87):**

`SUCCESS_RETCODES`, `UNKNOWN_OUTCOME_RETCODE`, `AllocationDispatchPlan`, `AmendmentKind`, `AmendmentOutcome`, `AmendmentResult`, `AsyncDispatchExecutor`, `BrokerCapabilityProfile`, `BrokerInitiatedEventKind`, `BrokerInitiatedExecutionEvent`, `BrokerOutcomeClassification`, `BrokerOutcomeStatus`, `CapabilityCheckResult`, `ClientOrderIdMapping`, `CorporateActionEvent`, `CorporateActionKind`, `CostAdjustmentEvent`, `ExecutionCoordinator`, `ExecutionLatencyEntry`, `ExecutionQualityEvent`, `InFlightRequestCounter`, `LifecycleKind`, `MultiLegDecision`, `MultiLegExecutionCoordinator`, `NonAtomicModifyResolution`, `NonAtomicModifyStage`, `NonAtomicModifyState`, `OcoExecutionMode`, `OcoWatchdog`, `ProviderRateLimiterRegistry`, `RateLimitDecision`, `ReconciliationDiscrepancyEntry`, `ResidualHandlingDecision`, `ResidualPolicy`, `ShadowFillComparison`, `ShadowIntentRecord`, `StateTransitionEvent`, `TokenBucketRateLimiter`, `TradingReport`, `TransactionCostFacts`, `TransitionApplyResult`, `TransitionRecord`, `TwoStepProtectionResult`, `active_broker_name`, `apply_execution_report`, `apply_residual_policy`, `begin_non_atomic_modify`, `build_broker_dispatch_callable`, `build_client_order_id_mapping`, `build_execution_quality_event`, `build_trading_report`, `capture_transaction_cost`, `classify_broker_initiated_event`, `classify_broker_outcome`, `classify_corporate_action`, `classify_stream_event`, `compare_shadow_fill`, `compute_implementation_shortfall`, `compute_realized_slippage_bps`, `evaluate_amendment`, `evaluate_oco_sibling_cancellation`, `evaluate_two_step_protection_outcome`, `finalize_dispatch_outcome`, `generate_client_order_id`, `initialize_transition_record`, `is_success_retcode`, `is_terminal_state`, `normalize_broker_response`, `plan_allocation_dispatch`, `record_cancel_confirmed`, `record_cancel_dispatched`, `record_replace_dispatched`, `record_shadow_intent`, `require_oco_submission_allowed`, `requires_cancel_on_disconnect_failsafe`, `requires_two_step_protection`, `resolve_dispatch_target`, `resolve_oco_execution_mode`, `resolve_replace_outcome`, `snapshot_broker_state`, `truncate_client_order_id`, `validate_broker_capabilities`, `validate_filling_mode_capability`, `validate_order_type_capability`, `validate_precision_capability`, `validate_rate_limit_capability`, `validate_transition`

**`app.services.trading.gates` (48):**

`CLOCK_DRIFT_THRESHOLD_MS`, `HARD_DUAL_APPROVAL_ACTION_IDS`, `ApprovalScope`, `BrokerReadinessEvidence`, `ClockDriftEvidence`, `ComplianceEvidence`, `DispatchOutcome`, `GateName`, `GatePipelineDecision`, `GateStep`, `GateStepResult`, `GateStepStatus`, `KillSwitchEvaluation`, `KillSwitchScope`, `KillSwitchState`, `LiveGateEvidence`, `LiveGatePipelineImpl`, `MarketTurbulenceMonitor`, `OperationalMode`, `OperatorApprovalToken`, `PolicyMatrix`, `PolicyMatrixEntry`, `ReadinessCheckResult`, `RiskDecisionEvidence`, `blocked_step`, `build_live_gate_pipeline`, `clear_kill_switch_after_approval`, `compute_canonical_request_hash`, `compute_effective_deadline`, `diagnostic_skipped_step`, `evaluate_adapter_permission_gate`, `evaluate_compliance_gate`, `evaluate_kill_switches`, `evaluate_seam_gate`, `passed_step`, `passthrough_risk_evaluator`, `persist_kill_switch_state`, `record_pre_mutation_audit`, `requires_dual_approval`, `resolve_policy`, `restore_kill_switch_state`, `run_gate_pipeline`, `run_live_readiness_dry_run`, `validate_broker_readiness`, `validate_clock_drift`, `validate_dual_operator_approval`, `validate_operator_approval`, `validate_risk_decision`

**`app.services.trading.config` (25):**

`BrokerCapabilityEvidence`, `BrokerSecurityProfile`, `ConfigChangeEvent`, `CostBudgetSettings`, `CredentialRotationResult`, `NotificationChannel`, `NotificationConfig`, `RateLimitSettings`, `ReauthenticationAdapter`, `RouteSettings`, `SecretReference`, `SecretResolutionResult`, `SecretResolver`, `StalenessSettings`, `StoreConnectionTargets`, `TimeoutSettings`, `TradingRuntimeConfig`, `apply_trading_config_reload`, `build_config_change_event`, `build_notification_payload`, `handle_credential_rotation`, `hash_effective_config`, `load_trading_config`, `resolve_secret_reference`, `validate_live_security_profile`

**`app.services.trading.info` (7):**

`AccountInfo`, `DealInfo`, `HistoryOrderInfo`, `OrderInfo`, `PositionInfo`, `SymbolInfo`, `TerminalInfo`

**`app.services.trading.security` (12):**

`DeadLetterRecord`, `DeadLetterWriteResult`, `ManualReviewRecord`, `RedactionBoundaryResult`, `TradingMappedError`, `TradingPermissionError`, `TradingServiceUnavailableError`, `TradingTimeoutError`, `TradingValidationError`, `WriteAheadDeadLetterQueue`, `map_exception_to_trading_error`, `redact_for_boundary`

**`app.services.trading.reconciliation` (5):**

`AuthorityAndRetryGuard`, `ReconciliationReport`, `ReconciliationService`, `compare_snapshots`, `evaluate_reconciliation_authority_gate`

**`app.services.trading.state` (30):**

`IDEMPOTENCY_MATERIAL_FIELDS`, `RNG`, `AppendOnlyEventJournal`, `AuditSink`, `Clock`, `EncryptionProvider`, `EventJournal`, `IdempotencyDecision`, `IdempotencyMaterial`, `IdempotencyRecord`, `IdempotencyReservation`, `IdempotencyStatus`, `IdempotencyStore`, `InMemoryTradeStore`, `JournalBuildMetadata`, `JournalEvent`, `JournalIntegrityResult`, `JournalRetentionPolicy`, `JsonlIdempotencyStore`, `JsonlTradeStore`, `LocalStateManager`, `ReconciliationLock`, `SegmentSeal`, `StateSnapshot`, `StateUpdateResult`, `TradeStore`, `TradingStateStore`, `compute_idempotency_key`, `compute_material_hash`, `replay_builder`

**`app.services.trading.monitoring` (7):**

`HeartbeatEmitter`, `IncidentSignal`, `LatencyTracker`, `LostOrderWatchdog`, `MonitoringService`, `OperationalSignalsManager`, `ToolHealthMonitor`

**`app.services.trading.promotion` (8):**

`PROMOTION_SEQUENCE`, `ROUTE_CAPABILITY_MATRIX`, `compute_canonical_promotion_hash`, `evaluate_promotion_stage_gate`, `validate_preactivation_conditions`, `validate_promotion_transition`, `validate_route_stage_capability`, `validate_sim_metadata_lookup`

**`app.services.trading.runtime` (8):**

`ConcurrencyLockManager`, `CostController`, `CrossStrategyPolicyEvaluator`, `OperationalMode`, `SessionManager`, `SessionState`, `SignalProcessor`, `StrategyOwnershipValidator`


**Entry points and registrations found:**

* Root registry accessors: `get_trading_tool_registry`, `get_trading_public_catalog`.
* AI registry contains one metadata-only tool: `create_trading_action_draft`, whose side-effect ceiling is `packaged_only`.
* Live mutation entry: an action call with `TradingActionDependencies.gate_pipeline` set to `LiveGatePipelineImpl`.
* Broker mutation entry: only `execution/broker_dispatch.py::build_broker_dispatch_callable` calls `broker.trade`.
* Usage script: `tests/trading/usage/07_trading.py`; its later examples explicitly warn that they can mutate a real account.
* No command-line entry point, web/API route, scheduler registration, agent-tool binding, or deployment composition root was confirmed.

## 4. Module and File Inventory

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `root` | `__init__.py` | Public facade and pure registry accessors. | Root exports; get_trading_tool_registry; get_trading_public_catalog | Std: future annotations; 3P: none; Local: contracts, execution, info, tool_registry, logger | **Used** | **Supporting** |
| `root` | `contracts.py` | Canonical request, response, state, event, tool and compatibility contracts. | Contract families, enums, envelopes, journal/execution DTOs | Std: datetime, Decimal, enum, hashlib, typing; 3P: pydantic; Local: trading.errors, utils normalization/standard/logger | **Used** | **Essential** |
| `root` | `errors.py` | Trading-domain exceptions, retcode classification, boundary payloads and retry delay. | TradingError hierarchy; classify_broker_error; to_trading_error_payload; trading_retry_delay | Std: Mapping, random, TypedDict; 3P: none; Local: utils logger/security | **Possibly used** | **Questionable** |
| `root` | `tool_registry.py` | Side-effect-free AI tool metadata registry. | build_trading_tool_registry; list_trading_tools; get_trading_tool_definition | Std: future annotations; 3P: none; Local: contracts, logger | **Used** | **Useful** |
| `actions` | `__init__.py` | Re-export gate for action and validation surface. | 40 explicit exports | Std: future annotations; 3P: none; Local: actions submodules | **Used** | **Supporting** |
| `actions` | `_common.py` | Dependency bag, envelope packaging, and live-pipeline dispatch seam. | LiveGatePipeline; TradingActionDependencies; package_request; dispatch_or_package | Std: Protocol/typing; 3P: none; Local: contracts, ExecutionCoordinator, state ports, logger | **Used** | **Essential** |
| `actions` | `validation.py` | Broker-independent Decimal normalization and order-safety validation. | Validation evidence models; OrderIntent; validate_order_request | Std: Decimal, enum; 3P: pydantic; Local: contracts, security errors, logger | **Used** | **Essential** |
| `actions` | `orders.py` | Market/pending/OCO order actions and order modify/delete packaging. | buy/sell; pending-order actions; order_modify/delete; submit_oco_group | Std: Decimal; 3P: none; Local: action common/validation, contracts, security errors, logger | **Used** | **Essential** |
| `actions` | `positions.py` | Position open/close/modify and approved exposure reduction. | NettingMode; PositionCloseMode; ReduceExposureScope; position_*; reduce_exposure | Std: Decimal, StrEnum; 3P: none; Local: orders, validation, contracts, security errors | **Used** | **Essential** |
| `actions` | `controls.py` | Strategy controls, synchronization, shutdown, and kill-switch activation. | ShutdownResult; pause/resume; sync_positions; shutdown; trigger_*_kill_switch | Std: timedelta, typing; 3P: none; Local: broker info helpers, contracts, state, redaction | **Used** | **Essential** |
| `actions` | `emergency.py` | Account/strategy/symbol emergency cancel, close and flatten workflows. | cancel_all_orders; close_all_positions; flatten_account/strategy/symbol | Std: typing; 3P: none; Local: action common, broker info, contracts, redaction/logger | **Possibly used** | **Essential** |
| `config` | `__init__.py` | Configuration public export gate. | 25 explicit exports | Std: none; 3P: none; Local: config submodules | **Used** | **Supporting** |
| `config` | `models.py` | Immutable runtime, route, timeout, budget, staleness, store and secret-reference models. | TradingRuntimeConfig and settings/evidence models | Std: typing/enum; 3P: pydantic; Local: contracts/logger | **Used** | **Supporting** |
| `config` | `loader.py` | Load, hash, diff and apply guarded configuration reloads. | ConfigChangeEvent; load/apply/hash/build functions | Std: hashlib/json; 3P: pydantic; Local: config models, contracts, redaction/logger | **Possibly used** | **Supporting** |
| `config` | `notifications.py` | Approved notification-channel contracts and redacted payload builder. | NotificationChannel; NotificationConfig; build_notification_payload | Std: none; 3P: pydantic; Local: contracts, redaction/logger | **Test-only** | **Useful** |
| `config` | `secrets.py` | Secret-reference resolution and credential-rotation coordination. | SecretResolver protocols/results; resolve_secret_reference; handle_credential_rotation | Std: Protocol; 3P: pydantic; Local: config models, security/logger | **Test-only** | **Supporting** |
| `config` | `security_profile.py` | Broker live-security profile validation. | BrokerSecurityProfile; validate_live_security_profile | Std: none; 3P: pydantic; Local: security errors/logger | **Test-only** | **Supporting** |
| `execution` | `__init__.py` | Execution public export gate. | 87 explicit exports | Std: none; 3P: none; Local: execution submodules | **Used** | **Supporting** |
| `execution` | `broker_capability_validation.py` | Adapter order/filling/precision/rate and cancel-on-disconnect capability checks. | BrokerCapabilityProfile; CapabilityCheckResult; validate_*; requires_* | Std: Decimal; 3P: pydantic; Local: contracts/security/logger | **Used** | **Essential** |
| `execution` | `broker_dispatch.py` | Single broker mutation boundary plus reconciliation snapshot helper. | SUCCESS_RETCODES; active_broker_name; build_broker_dispatch_callable; is_success_retcode; snapshot_broker_state | Std: typing; 3P: none; Local: brokers.router, response_classifier, contracts/logger | **Used** | **Essential** |
| `execution` | `coordinator.py` | Dispatch payloads, async dispatch, identifiers, allocations, OCO/multi-leg, modify and finalization coordination. | ExecutionCoordinator and 30+ coordination types/functions | Std: concurrency/threading/hash/Decimal; 3P: pydantic; Local: contracts, state ports, logger | **Used** | **Essential** |
| `execution` | `rate_limiter.py` | Injected-clock token-bucket provider rate limiting. | TokenBucketRateLimiter; ProviderRateLimiterRegistry; RateLimitDecision | Std: threading; 3P: pydantic; Local: Clock, security/logger | **Possibly used** | **Supporting** |
| `execution` | `reporting.py` | Trading report and execution-quality event construction. | TradingReport/event models; build_*; slippage/shortfall computations | Std: Decimal; 3P: pydantic; Local: contracts/logger | **Test-only** | **Useful** |
| `execution` | `response_classifier.py` | Normalize broker responses and classify command, stream, broker-initiated and corporate-action outcomes. | Outcome/event models; normalize_broker_response; classify_* | Std: enum/typing; 3P: pydantic; Local: contracts, trading.errors, logger | **Used** | **Essential** |
| `execution` | `shadow.py` | Record shadow intents and compare expected versus live fills. | ShadowIntentRecord; ShadowFillComparison; record_shadow_intent; compare_shadow_fill | Std: Decimal; 3P: pydantic; Local: contracts/logger | **Test-only** | **Useful** |
| `execution` | `state_machine.py` | Order/position lifecycle transitions, amendments and execution-report deduplication. | Lifecycle/amendment/transition models; initialize/validate/apply/evaluate functions | Std: enum/collections; 3P: pydantic; Local: contracts/security/logger | **Possibly used** | **Essential** |
| `gates` | `__init__.py` | Live-gate public export gate. | 48 explicit exports | Std: none; 3P: none; Local: gate submodules | **Used** | **Supporting** |
| `gates` | `_common.py` | Canonical gate names, statuses and result constructors. | GateName; GateStepStatus; GateStepResult; passed/blocked/skipped helpers | Std: enum; 3P: pydantic; Local: contracts/logger | **Used** | **Essential** |
| `gates` | `approval.py` | Approval-token/request-hash, dual-control and risk-evidence validation. | ApprovalScope; OperatorApprovalToken; RiskDecisionEvidence; compute/validate functions | Std: hashlib/datetime; 3P: pydantic; Local: contracts/security/logger | **Used** | **Essential** |
| `gates` | `audit_and_compensation.py` | Fail-closed pre-mutation audit write. | record_pre_mutation_audit | Std: none; 3P: none; Local: AuditSink, gate common, security/logger | **Used** | **Essential** |
| `gates` | `kill_switch.py` | Kill-switch evaluation, persistence, restoration and approved clearing. | KillSwitch*; OperationalMode; evaluate/persist/restore/clear | Std: enum/typing; 3P: pydantic; Local: contracts, approval, state store, security/logger | **Used** | **Essential** |
| `gates` | `pipeline.py` | Generic ordered gate runner, compliance and turbulence gates, deadline/quote checks. | GateStep; GatePipelineDecision; MarketTurbulenceMonitor; run/evaluate functions | Std: collections/Decimal; 3P: pydantic; Local: contracts, execution capability validation, gate common | **Used** | **Essential** |
| `gates` | `live_pipeline.py` | Composition root for the 16 live gates and timed broker dispatch. | DispatchOutcome; LiveGateEvidence; LiveGatePipelineImpl; build_live_gate_pipeline; passthrough_risk_evaluator | Std: futures/dataclass/Decimal; 3P: none; Local: execution/gates/promotion/reconciliation/runtime/state/security | **Used** | **Essential** |
| `gates` | `policy_matrix.py` | Resolve governed action permissions and fail closed on missing policy. | PolicyMatrixEntry; PolicyMatrix; resolve_policy | Std: none; 3P: pydantic; Local: contracts/security/logger | **Used** | **Essential** |
| `gates` | `readiness.py` | Broker connection/permission/rate readiness and clock drift checks. | Evidence/result models; validate_*; run_live_readiness_dry_run | Std: none; 3P: pydantic; Local: security/logger | **Used** | **Essential** |
| `info` | `__init__.py` | Read-only facade export gate; logs when imported. | Seven facade classes | Std: future annotations; 3P: none; Local: info classes, logger | **Used** | **Supporting** |
| `info` | `_common.py` | Dynamic read-only broker calls, neutral coercion and boundary redaction. | broker_call; first_or_none; iter_or_empty; safe_attr; redacted_info_payload | Std: collections/typing; 3P: none; Local: brokers, contracts, security, logger | **Used** | **Supporting** |
| `info` | `_ticket.py` | Shared ticket-selection and common accessor base. | TicketInfoFacade and public selection/accessor/payload methods | Std: none; 3P: none; Local: info common, contracts/logger | **Used** | **Supporting** |
| `info` | `account.py` | Read-only account facade. | AccountInfo; REAL_TRADE_MODE | Std: none; 3P: none; Local: info common, contracts/logger | **Used** | **Useful** |
| `info` | `deal.py` | Historical deal facade extending ticket base. | DealInfo | Std: none; 3P: none; Local: ticket base/info common/logger | **Used** | **Useful** |
| `info` | `history_order.py` | Historical order facade extending OrderInfo. | HistoryOrderInfo | Std: none; 3P: none; Local: OrderInfo/logger | **Used** | **Useful** |
| `info` | `order.py` | Active pending-order facade. | OrderInfo | Std: none; 3P: none; Local: ticket base/info common/logger | **Used** | **Useful** |
| `info` | `position.py` | Active position facade with symbol/ticket selection. | PositionInfo | Std: none; 3P: none; Local: ticket base/info common/logger | **Used** | **Useful** |
| `info` | `symbol.py` | Read-only symbol metadata, quotes, volume, stop and margin/profit calculations. | SymbolInfo | Std: Decimal; 3P: none; Local: broker info common/logger | **Used** | **Useful** |
| `info` | `terminal.py` | Read-only terminal connection/build/path facade. | TerminalInfo | Std: none; 3P: none; Local: broker info common/logger | **Used** | **Useful** |
| `security` | `__init__.py` | Security export gate; logs when imported. | 12 explicit exports | Std: future annotations; 3P: none; Local: security modules, logger | **Used** | **Supporting** |
| `security` | `error_mapping.py` | Stable public error contracts and redacted exception mapping. | TradingMappedError hierarchy; map_exception_to_trading_error | Std: Mapping; 3P: pydantic; Local: contracts, root errors, utils security/logger | **Used** | **Essential** |
| `security` | `redaction_boundary.py` | Recursive boundary redaction and durable write-ahead dead-letter/manual-review handling. | Redaction/DLQ records; WriteAheadDeadLetterQueue; redact_for_boundary | Std: json/path/dataclass; 3P: pydantic; Local: contracts, Clock, utils security/logger | **Used** | **Essential** |
| `state` | `__init__.py` | State and persistence export gate. | 30 explicit exports | Std: none; 3P: none; Local: state modules | **Used** | **Supporting** |
| `state` | `ports.py` | Injected protocols for stores, audit, journal, clock, RNG and encryption. | TradeStore; TradingStateStore; AuditSink; IdempotencyStore; EventJournal; Clock; RNG; EncryptionProvider | Std: Protocol/datetime; 3P: none; Local: contracts | **Used** | **Essential** |
| `state` | `event_journal.py` | Encrypted append-only hash-chained journal, snapshots, replay, seals and signatures. | AppendOnlyEventJournal and journal models; replay_builder | Std: json/hash/path; 3P: pydantic; Local: contracts, Clock/EncryptionProvider, logger | **Possibly used** | **Essential** |
| `state` | `idempotency.py` | Canonical idempotency material, durable leases, duplicate/cached completion and expiry handling. | Idempotency models; JsonlIdempotencyStore; compute_* | Std: hashlib/json/path/datetime; 3P: pydantic; Local: contracts, Clock, security/logger | **Used** | **Essential** |
| `state` | `manager.py` | Persist local state snapshots and journal state updates. | LocalStateManager; StateUpdateResult | Std: none; 3P: pydantic; Local: state ports/contracts/logger | **Test-only** | **Supporting** |
| `state` | `trade_store.py` | In-memory and JSONL order/position projections with optimistic concurrency and fill deduplication. | InMemoryTradeStore; JsonlTradeStore | Std: json/path/threading/Decimal; 3P: none; Local: contracts/security/logger | **Used** | **Essential** |
| `reconciliation` | `__init__.py` | Reconciliation export gate. | Five explicit exports | Std: none; 3P: none; Local: reconciliation modules | **Used** | **Supporting** |
| `reconciliation` | `snapshots_and_compare.py` | Canonical broker/local snapshot models and discrepancy comparison. | Snapshot/discrepancy types; compare_snapshots | Std: dataclass/Decimal; 3P: pydantic; Local: contracts/logger | **Used** | **Essential** |
| `reconciliation` | `authority_and_retry_guard.py` | Unknown-outcome authority locks and retry gating. | AuthorityAndRetryGuard; evaluate_reconciliation_authority_gate | Std: threading; 3P: none; Local: gates/state/security/logger | **Used** | **Essential** |
| `reconciliation` | `service.py` | Startup/periodic/manual reconciliation orchestration and reports. | ReconciliationReport; ReconciliationService | Std: typing; 3P: pydantic; Local: snapshots, state ports, contracts/logger | **Possibly used** | **Essential** |
| `monitoring` | `__init__.py` | Monitoring export gate. | Seven explicit exports | Std: none; 3P: none; Local: monitoring modules | **Used** | **Supporting** |
| `monitoring` | `heartbeat_watchdog.py` | Injected-clock dead-man heartbeat emission. | HeartbeatEmitter | Std: none; 3P: none; Local: Clock/logger | **Test-only** | **Supporting** |
| `monitoring` | `operational_signals.py` | Incident model, dispatch throttling and escalation. | IncidentSignal; OperationalSignalsManager | Std: collections; 3P: pydantic; Local: config notifications/Clock/logger | **Test-only** | **Supporting** |
| `monitoring` | `service.py` | Root monitoring orchestration, operational metrics and circuit-breaker decisions. | MonitoringService | Std: collections; 3P: none; Local: monitoring components/config/logger | **Possibly used** | **Supporting** |
| `monitoring` | `timeouts_and_staleness.py` | Bounded latency tracking and stale/lost-order detection. | LatencyTracker; LostOrderWatchdog | Std: collections; 3P: pydantic; Local: Clock/logger | **Test-only** | **Supporting** |
| `monitoring` | `tool_health.py` | Consecutive tool-failure health tracking. | ToolHealthMonitor | Std: collections; 3P: none; Local: logger | **Test-only** | **Supporting** |
| `promotion` | `__init__.py` | Promotion export gate. | Eight explicit exports | Std: none; 3P: none; Local: promotion modules | **Used** | **Supporting** |
| `promotion` | `ladder.py` | Linear stage/capability matrix, promotion hash, gate and transition validation. | PROMOTION_SEQUENCE; ROUTE_CAPABILITY_MATRIX; compute/evaluate/validate functions | Std: hashlib; 3P: pydantic; Local: contracts, approval/security/logger | **Used** | **Essential** |
| `promotion` | `preconditions.py` | Preactivation evidence and simulation metadata lookup validation. | validate_preactivation_conditions; validate_sim_metadata_lookup | Std: none; 3P: none; Local: contracts/security/logger | **Used** | **Supporting** |
| `runtime` | `__init__.py` | Runtime coordination export gate. | Eight explicit exports | Std: future annotations; 3P: none; Local: runtime/gates modules | **Used** | **Supporting** |
| `runtime` | `coordination.py` | Per-account/symbol locks, strategy ownership and cross-strategy policy. | ConcurrencyLockManager; StrategyOwnershipValidator; CrossStrategyPolicyEvaluator | Std: threading/collections; 3P: pydantic; Local: security/logger | **Used** | **Essential** |
| `runtime` | `cost_control.py` | Pre-dispatch budget checks and actual-cost tracking by request/workflow/strategy/account/session. | CostController | Std: Decimal/collections; 3P: pydantic; Local: config/security/logger | **Possibly used** | **Supporting** |
| `runtime` | `session_manager.py` | Session state/mode, singleton live scope, reconnect, CoD/GTD/DAY watchdog and halted symbols. | SessionManager; SessionState | Std: threading/datetime; 3P: pydantic; Local: gates/state/execution/logger | **Used** | **Essential** |
| `runtime` | `signal_processor.py` | Translate raw strategy signal dictionaries into request envelopes and invoke a supplied gate runner. | SignalProcessor.process_strategy_signal | Std: Callable/typing; 3P: none; Local: contracts, security errors/logger | **Test-only** | **Questionable** |

## 5. Public Behaviour Inventory

### Interpretation

* Public symbols are those exported through a package `__all__` or defined without a leading underscore and used/imported externally.
* Re-export-only `__init__.py` files are represented in Sections 3 and 4; their only additional behavior is import-time logging in `info/__init__.py` and `security/__init__.py`.
* Closely related models/enums are grouped in one row to keep this audit usable. Every explicit facade export is listed in Section 3.
* Side-effect labels use the requested vocabulary. “Delegated” means the exact effect depends on an injected pipeline/store/callback.

### `__init__.py`

**File responsibility:** Import-safe public facade plus two registry accessors.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `get_trading_tool_registry` | Function | Build the official packaged-only AI tool registry. | none → `TradingToolRegistry` | None, except logging | Contract validation errors | `get_trading_public_catalog`; usage example | `tests/trading/unit/test_tool_registry.py`; usage | Used | Useful |
| `get_trading_public_catalog` | Function | Return deterministically sorted tool definitions. | none → tuple of `TradingToolDefinition` | None, except logging | Registry/model validation errors | usage example | `tests/trading/unit/test_tool_registry.py`; usage | Used | Useful |
| Re-exported contracts/facades/coordinator | Re-exports | Stable package import surface. | import → symbol | Import-time logging occurs in `info` and `security` subpackages | Import errors | tests/usage and any external importer | broad unit coverage | Used | Supporting |

### `contracts.py`

**File responsibility:** Canonical broker-neutral contracts shared across actions, gates, execution, persistence, reconciliation, analytics adapters and tools.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `Contract`; `TradingContract` | Pydantic bases | Validation, deterministic serialization/hash and schema compatibility. | model fields → immutable/validated model | None; `Contract.created_at` reads wall clock | `ValueError`; `TradingValidationError` | contract subclasses; analytics journal adapters | `test_contracts.py` | Used | Essential |
| `TradingRoute`, `TradingAction`, `SideEffectMode`, `RetrySafety`, `TradingStatus`, `PromotionStage`, `MutationCapability`, `TimeInForce`, `FixExecutionState`, `OrderState`, `PositionState` | Enums | Canonical route/action/lifecycle vocabulary. | enum value → enum member | None | `ValueError` | throughout package | broad tests/usage | Used | Essential |
| `TradingRequestEnvelope`, `TradingResponseEnvelope`, `TradingCommandAccepted`, `TradingCommandRejected`, `TradingError`, `TradingMetadata` | Models | Public request/response and accepted/rejected/error envelopes. | validated fields → model | None | Pydantic validation errors | actions, gates, execution, tools | broad tests/integration | Used | Essential |
| `QuoteSnapshot`, `AllocationVector`, `RegulatoryTags` | Models | Evidence and optional order-allocation/regulatory context. | validated fields → model | None | Pydantic validation errors | actions, live pipeline, coordinator | tests/usage | Used | Essential |
| `NormalizedTradeResult`, `BrokerAcknowledgementEvent`, `BrokerDispatchEvent`, `ExecutionReportEvent`, `ReconciliationResolutionEvent` | Models | Normalized execution and journal event contracts. | provider/event fields → model | None | Pydantic validation errors | classifier, coordinator, stores, reconciliation | execution/state tests | Used | Essential |
| `TradingToolDefinition`, `TradingToolRegistry` | Models | Restrict AI-facing tools to `none` or `packaged_only` side-effect ceilings. | metadata/maps → validated registry | None | `ValueError` | tool registry | tool registry tests | Used | Useful |
| `OrderIntent`, `TradeRequest`, `TradeResult`, `Fill`, `ExecutionReport`, `BrokerCapabilities` | Compatibility models | Cross-domain journal/analytics and provider-neutral execution compatibility. | model fields → model | None; timestamp normalization | validation errors | `analytics/adapters/journal_adapters.py`; tests | Used | Useful |
| `validate_redacted_json_value` | Function | Reject obvious sensitive keys/values in JSON-safe data. | `JsonValue`, path → `None` | None, except logging | `ValueError` | contracts/exports | contract tests | Possibly used | Supporting |

### `errors.py`

**File responsibility:** Domain exception definitions, retcode classification, public payload mapping, and retry-delay calculation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `TradingError`, `TradingValidationError`, `TradingExternalServiceError`, `TradingTimeoutError`, `UnknownOutcomeError` | Exceptions | Domain failures with stable-ish codes. | message/code → exception | None | N/A | contracts, response classifier, other domains may import | contract/execution tests | Possibly used | Supporting |
| `TRADING_ERROR_CODES`, `ERROR_MESSAGES`, `TRADING_RETCODE_ERROR_MAP`, `TRANSIENT_TRADING_RETCODES` | Constants | Error-code allowlist/messages and provider retcode mappings. | N/A | None | N/A | classifier/helpers | tests | Possibly used | Questionable |
| `to_trading_error_payload` | Function | Redact an exception into `{code, details}`. | exception, optional request ID → mapping | None, except logging | none expected | official/tool boundaries not confirmed | tests | Possibly used | Useful |
| `classify_broker_error` | Function | Map exception/response retcode to code, transient/permanent classification and redacted details. | error-like object → dict | None | none expected | `execution/response_classifier.py` | execution tests | Used | Essential |
| `trading_retry_delay` | Function | Exponential backoff with random jitter for idempotent retries. | attempt/base/max/jitter → seconds | Reads global random source | `TradingValidationError` | no production caller confirmed | tests, if present | Test-only | Questionable |

### `tool_registry.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `build_trading_tool_registry` | Function | Build one approved `create_trading_action_draft` definition. | none → registry | None, except logging | model validation errors | root accessor | tool registry tests/usage | Used | Useful |
| `list_trading_tools` | Function | Deterministically sort registry definitions. | registry → tuple | None, except logging | none expected | root catalog accessor | tests/usage | Used | Useful |
| `get_trading_tool_definition` | Function | Resolve a named definition. | name, registry → definition | None, except logging | `KeyError` | no non-test caller confirmed | tests | Test-only | Useful |

### `actions/_common.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `LiveGatePipeline.evaluate` | Protocol method | Seam from action packaging into live gate evaluation. | request → response | Depends on implementation | `NotImplementedError` in protocol body | `dispatch_or_package`; implemented by `LiveGatePipelineImpl` | actions/gate integration tests | Used | Essential |
| `TradingActionDependencies` | Class | Hold injected clock/RNG, tenant, pipeline and stores. | keyword dependencies → instance | Local state mutation | `ValueError` for blank tenant | all actions | action tests/usage | Used | Essential |
| `package_request` | Function | Construct `TradingRequestEnvelope`. | action/route/stage/capability/IDs/payload/evidence → envelope | None | model validation errors | orders/positions/emergency | action tests | Used | Supporting |
| `dispatch_or_package` | Function | Evaluate live pipeline when injected; otherwise return fail-closed packaged response. | request, dependencies → response | None or delegated broker/persistence side effects | delegated errors | action modules | action/integration tests/usage | Used | Essential |

### `actions/validation.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `OrderSide`, `OrderType` and validation constants | Enums/constants | Classify order direction/type and validation sets. | value → enum | None | `ValueError` | orders/positions/validation | validation tests | Used | Supporting |
| `SymbolTradingConstraints`, `AccountMarginContext`, `ConversionRateEvidence`, `MarketSessionEvidence`, `LocateSnapshot`, `DefenseInDepthRailLimits`, `DailyRailState`, `OrderIntent`, `OrderValidationContext`, `OrderValidationResult` | Models | Explicit evidence and normalized validation input/output. | fields → validated models | None | Pydantic/`ValueError` | `orders._validate_and_package`; usage | validation/order tests | Used | Essential |
| Evidence methods such as `is_fresh` | Methods | Check caller-supplied evidence TTL. | instance → bool | None | none expected | validation pipeline | validation tests | Used | Supporting |
| `validate_order_request` | Function | Normalize volume/price/stops and enforce session, TIF, margin, locate, slippage, price collar, fat-finger and static rail checks. | `OrderIntent`, `OrderValidationContext` → `OrderValidationResult` | None, except logging | `TradingValidationError`/`TradingMappedError` | all order actions | `test_validation.py`, `test_orders.py` | Used | Essential |

### `actions/orders.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `buy`, `sell` | Functions | Validate and package market-order intents. | symbol, Decimal volume/stops/slippage, route/stage/capability/IDs/context/deps/quote → response | Packaged-only, or delegated broker mutation | validation/mapped errors | `position_open`; usage; external callers | order/action/integration tests | Used | Essential |
| `buy_limit`, `sell_limit`, `buy_stop`, `sell_stop` | Functions | Validate and package pending orders with price/TIF/expiration. | order fields/evidence/deps → response | Packaged-only, or delegated broker mutation | validation/mapped errors | usage/external callers | order tests | Used | Essential |
| `order_modify`, `order_delete` | Functions | Package pending-order mutation/cancel with optional expected state version. | order ID/mutation fields/context → response | Packaged-only, or delegated broker mutation | invalid input/mapped errors | usage/external callers | order tests | Used | Essential |
| `submit_oco_group` | Function | Validate and package at least two linked OCO/bracket order intents. | group ID, child intents/context/deps → response | Packaged-only, or delegated broker mutation | invalid group/validation errors | no production caller confirmed | order/coordinator tests | Test-only | Useful |
| `MIN_OCO_GROUP_SIZE` | Constant | Minimum child count for OCO submission. | N/A | None | N/A | `submit_oco_group` | order tests | Used | Supporting |

### `actions/positions.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `NettingMode`, `PositionCloseMode`, `ReduceExposureScope` | Enums | Addressing/accounting/reduction scope. | value → enum | None | `ValueError` | position functions; usage | position tests | Used | Supporting |
| `position_open` | Function | Delegate to validated `buy`/`sell`. | side/order parameters → response | Delegated | validation errors | external/usage | position tests | Used | Essential |
| `position_close` | Function | Package close by ticket or symbol; enforce hedging ticket rule. | mode/ticket/symbol/volume/etc. → response | Packaged-only or broker mutation | `TradingMappedError` | usage/external | position tests | Used | Essential |
| `position_modify` | Function | Package SL/TP mutation and expected state version. | position ID/stops/version/etc. → response | Packaged-only or broker mutation | `TradingMappedError` | usage/external | position tests | Used | Essential |
| `reduce_exposure` | Function | Package a pre-approved risk reduction; does not size risk. | scope/target/volume/risk decision ID/etc. → response | Packaged-only or broker mutation | `TradingMappedError` | no production caller confirmed | position tests | Possibly used | Essential |

### `actions/controls.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ShutdownResult` | Model | Report drain/flush/reconciliation outcome. | fields → model | None | model validation | `shutdown` | control tests/usage | Used | Supporting |
| `pause_strategy`, `resume_strategy` | Functions | Return local control response and optionally append journal event. | strategy/reason/route/stage/capability/IDs/deps → response | Local state/audit journal mutation | `TradingMappedError` | usage/external | control tests | Used | Useful |
| `sync_positions` | Function | Read broker positions/orders and optionally persist minimal projections. | route/IDs/deps → response | Read-only; optional persistence write | broker failures are neutralized by `broker_call`; store errors may propagate | external/runtime not confirmed | control tests | Possibly used | Essential |
| `shutdown` | Function | Drain, flush, reconcile and journal graceful shutdown outcome. | count/deps/callbacks/timeout → `ShutdownResult` | Local state mutation, persistence callbacks, read-only reconciliation | negative count mapped error; reconciliation exceptions swallowed/logged | README usage; external caller not confirmed | control tests/usage | Possibly used | Essential |
| `trigger_global_kill_switch`, `trigger_strategy_kill_switch`, `trigger_symbol_kill_switch` | Functions | Reserve scope idempotency, append journal event and return activation response. | scope/reason/actor/route/stage/IDs/deps/stores → response | Persistence write, event publication/journal | mapped input/store errors | usage; gate state consumes resulting state through separate path | control/kill-switch tests | Used | Essential |

### `actions/emergency.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `cancel_all_orders`, `close_all_positions` | Functions | Snapshot current broker state and issue child cancel/close actions with partial-completion detail. | scope/route/stage/capability/IDs/deps/quote → response | Read-only snapshots; packaged-only or broker mutations | mapped/delegated errors | flatten functions; usage | emergency/integration tests | Used | Essential |
| `flatten_account`, `flatten_strategy`, `flatten_symbol` | Functions | Compose cancel + close across requested scope. | scope/evidence/deps → response | Multiple broker mutations possible; persistence/audit via pipeline | delegated errors; partial completion represented | usage/external not confirmed | emergency tests/usage | Possibly used | Essential |

### `config/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `models.py`: settings/evidence models | Models | Immutable configuration and route/store/security evidence. | fields → validated models | None | Pydantic errors | loader, gates, runtime | config/runtime tests | Used | Supporting |
| `loader.py`: `load_trading_config`, `hash_effective_config`, `build_config_change_event`, `apply_trading_config_reload` | Functions/models | Parse, redact/hash, report and guard reloads. | mapping/config/current state → config/event | Local config state mutation only when caller applies result | validation/mapped errors | usage; production caller unconfirmed | config tests/usage | Possibly used | Supporting |
| `notifications.py`: channel/config models and `build_notification_payload` | Models/function | Build approved redacted notification payloads. | config/channel/event/payload → JSON | None | validation/key errors | monitoring/usage | config/monitoring tests | Used | Useful |
| `secrets.py`: resolver protocols/results/functions | Protocols/models/functions | Resolve references and coordinate reauthentication during rotation. | reference/resolver/adapter → result | External secret/API call through injected ports | mapped errors | no production composition found | config tests | Test-only | Supporting |
| `security_profile.py`: profile and validator | Model/function | Validate minimum live broker security controls. | profile → validated/none | None | mapped validation errors | preactivation/config tests | Test-only | Supporting |

### `execution/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `broker_capability_validation.py` exports | Models/functions | Fail closed on order type, filling, precision or rate-capacity mismatch; indicate CoD fallback need. | profile/request evidence → `CapabilityCheckResult`/bool | None | mapped errors for aggregate validator | gate 15; session manager | capability/gate tests | Used | Essential |
| `broker_dispatch.py` exports | Constant/functions | Resolve active broker; bind `broker.trade`; classify success; read positions/orders for reconciliation. | payload/request/provider → callable/result; none → snapshots | **Broker mutation** in returned callable; read-only snapshot | broker/provider errors | live pipeline | integration tests/usage | Used | Essential |
| `coordinator.py`: `ExecutionCoordinator`, dispatch/in-flight/ID/allocation/OCO/multi-leg/non-atomic/cost/finalization exports | Classes/functions/models | Coordinate broker-independent execution mechanics and post-response persistence. | envelopes/results/policies/stores/callbacks → payloads, decisions or accepted response | Local state mutation, asynchronous execution, persistence write | validation/mapped/store errors | action common, live pipeline, tests/usage | extensive coordinator/integration tests | Used | Essential |
| `rate_limiter.py` exports | Classes/model | Deterministic token-bucket decisions by provider. | capacity/refill/time/request → decision | Local state mutation | validation errors | readiness/runtime composition unconfirmed | rate-limiter tests/usage | Possibly used | Supporting |
| `reporting.py` exports | Models/functions | Build trading report and execution-quality events; calculate slippage/shortfall. | position/order/latency/cost/reconciliation data → report/event/Decimal | None | validation errors | analytics boundary intended; no production caller found | reporting tests/usage | Test-only | Useful |
| `response_classifier.py` exports | Enums/models/functions | Normalize raw broker responses and classify unknown/rejected/stream/external/corporate outcomes. | provider/raw event/response → normalized result/classification | None | mapped errors | broker dispatch/live pipeline | response tests/integration | Used | Essential |
| `shadow.py` exports | Models/functions | Record non-mutating intent and compare expected/live fills. | expected/live evidence → record/comparison | None | validation errors | usage only confirmed | shadow tests/usage | Test-only | Useful |
| `state_machine.py` exports | Enums/models/functions | Validate lifecycle transitions, amendments and deduplicate broker event IDs. | transition/report/version → decision/record | Local state mutation through returned records | mapped validation errors | coordinator/store integration not fully confirmed | state-machine tests/usage | Possibly used | Essential |

### `gates/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `_common.py` exports | Enums/model/functions | Canonical sixteen gate names and result constructors. | gate/status/reason → result | None | model validation | all gate modules | gate tests | Used | Essential |
| `approval.py` exports | Models/constants/functions | Bind approvals to request hash/scope; require dual operators for hard actions; validate risk evidence shape. | tokens/evidence/time/hash/scope → validation/bool | Local token state checks only | `TradingMappedError` | live pipeline, kill-switch clear, promotion | approval tests/integration | Used | Essential |
| `audit_and_compensation.py::record_pre_mutation_audit` | Function | Write audit record and block when sink fails. | sink/request/time → gate result/reference | Persistence write | sink errors converted to blocked result | gate 14 | gate tests/integration | Used | Essential |
| `kill_switch.py` exports | Models/enums/functions | Evaluate scope switches, persist/restore state, clear global switch after dual approval. | switches/action/policy/store/approvals → evaluation/state | Persistence write/read, local state mutation | mapped errors | gate 5/runtime | kill-switch tests/integration | Used | Essential |
| `pipeline.py` exports | Models/classes/functions | Ordered short-circuit runner; compliance, turbulence, adapter, seam, deadline and quote freshness. | request/steps/clock/deadline → decision | Local monitor mutation | catches/records blocking failures | `LiveGatePipelineImpl`; usage | pipeline tests/integration | Used | Essential |
| `live_pipeline.py` exports | Dataclasses/class/functions | Assemble gates 1–16, run timed broker dispatch, classify timeout unknown outcome, reconcile, finalize and release lease. | injected evidence/services + request → response | Broker mutation, persistence write, read-only reconciliation, local state mutation | construction `ValueError`; mapped/delegated errors become response/gate results | action dispatch seam | live-pipeline unit/integration/usage | Used | Essential |
| `policy_matrix.py` exports | Models/function | Resolve per-action permission/approval/emergency policy. | matrix/action → entry | None | `TradingMappedError(TRADING_POLICY_UNDEFINED)` | live pipeline/kill switch | policy tests | Used | Essential |
| `readiness.py` exports | Models/constant/functions | Check connection, trade permissions, rate capacity, local drift/PTP latency; dry run. | evidence → check/result | Read-only | mapped errors | gates 9–10, usage | readiness tests | Used | Essential |

### `info/*`

**Shared methods:** `TicketInfoFacade.select`, `ticket`, `time`, `time_msc`, `type`, `type_description`, `magic`, `position_id`, `volume`, `price`, `symbol`, `comment`, `info_integer`, `info_double`, `info_string`, and `payload`.

| File / symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `_common.py` helpers | Functions | Dynamic read-only broker function lookup, neutral fallback, iterable coercion and redaction. | function name/value/object → object/tuple/value/payload | External API **read-only** | broker exceptions are caught and converted to `None`; cast errors neutralized | all info facades; sync controls | info/control tests | Used | Supporting |
| `TicketInfoFacade` | Base class | Select broker record by ticket and expose common properties. | optional ticket / property ID → bool/scalar/payload | External API read-only on `select` | broker failures neutralized | deal/order/history/position classes | info tests | Used | Supporting |
| `AccountInfo` | Class | Account login, mode, leverage, permissions, balance/equity/margin, identity and redacted payload. | no constructor args; accessor calls → scalar/payload | External API read-only on most accessors | broker errors neutralized | usage/external callers | info tests/usage | Used | Useful |
| `AccountInfo.margin_so_mode`, `free_margin_mode` | Methods | Return compatibility constants. | none → `0` | None | none | no production caller confirmed | info tests | Test-only | Questionable |
| `AccountInfo.trade_mode` | Method | Infer real/demo from broker server name. | none → int | External API read-only | neutral fallback | usage | info tests/usage | Used | Questionable |
| `DealInfo` | Class | Add order, entry description, commission, swap and profit to ticket base. | ticket/accessor → scalar | External API read-only on selection | neutral fallback | usage | info tests/usage | Used | Useful |
| `OrderInfo` | Class | Pending-order times, TIF/filling/state descriptions, volumes, prices and stops. | ticket/accessor → scalar | External API read-only on selection | neutral fallback | usage/snapshot workflows | info tests/usage | Used | Useful |
| `HistoryOrderInfo` | Class | Same surface as `OrderInfo`, backed by historical-order query. | ticket → bool; inherited accessors | External API read-only | neutral fallback | usage | info tests/usage | Used | Useful |
| `PositionInfo` | Class | Select by symbol/ticket and expose update time, ID, prices, stops, swap and profit. | symbol/ticket/accessor → bool/scalar | External API read-only | neutral fallback | usage/reconciliation | info tests/usage | Used | Useful |
| `SymbolInfo` | Class | Refresh symbol, quote/precision/volume/stop properties and margin/profit calculations. | symbol + calculation args → scalar/bool/payload | External API read-only | neutral fallback | validation evidence callers/usage | info tests/usage | Used | Useful |
| `TerminalInfo` | Class | Connection, trade allowance, build/path and terminal metadata. | no args/accessor → scalar/payload | External API read-only | neutral fallback | readiness/usage | info tests/usage | Used | Useful |

### `security/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `error_mapping.py` exception hierarchy | Exceptions | Runtime-specific mapped validation/timeout/permission/unavailable errors. | message/details → exception | None | N/A | actions/gates/runtime | security and broad tests | Used | Essential |
| `map_exception_to_trading_error` | Function | Classify and redact exceptions into public `contracts.TradingError`. | error + request/correlation/provider → model | None | `ValueError` for blank IDs | live pipeline/usage | security/integration tests | Used | Essential |
| `redaction_boundary.py` records and `redact_for_boundary` | Models/function | Recursively redact logs/events/reports/chat payloads and expose blocked scopes. | arbitrary payload/context → redacted result | None | validation errors | config/info/actions/security | security tests/usage | Used | Essential |
| `WriteAheadDeadLetterQueue` and records | Class/models | Persist failed critical events before recovery; isolate poison events for manual review. | paths/clock/retry policy + failed event → write result | Persistence write | filesystem/validation errors | usage; production caller not confirmed | security tests/usage | Possibly used | Essential |

### `state/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ports.py` protocols | Protocols | Abstract audit/state/trade/idempotency/journal/time/random/encryption dependencies. | implementation-defined | None in protocol | `NotImplementedError` or protocol-only | all runtime components | port tests | Used | Essential |
| `event_journal.py` exports | Models/class/function | Encrypted append-only JSONL, hash chain, sequences, snapshots, replay, retention seals and signatures. | path/ports/metadata + events → records/snapshots/integrity | Persistence write/read | filesystem/integrity/encryption errors | controls/usage; production composition unconfirmed | journal tests/usage | Possibly used | Essential |
| `idempotency.py` exports | Constants/models/class/functions | Canonical key/material hash; durable reservation, duplicate, completion cache and expiry decisions. | material/route/tenant/TTL/result → key/reservation/record | Persistence write/read | mapped validation/version errors | live gate, kill-switch controls, coordinator | idempotency/integration tests/usage | Used | Essential |
| `manager.py` exports | Class/model | Coordinate snapshot persistence and event journaling. | stores + update → result | Persistence write/event publication | store/journal errors | no production caller confirmed | manager tests | Test-only | Supporting |
| `trade_store.py` exports | Classes | Save/load versioned order/position state and deduplicate fills. | route/tenant/state/version/event ID → projection/version | Local state mutation; persistence write for JSONL | version conflict/mapped errors | live finalization, sync, reconciliation | store/integration tests | Used | Essential |

### `reconciliation/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `snapshots_and_compare.py` models/functions | Models/function | Normalize and compare broker versus local positions/orders/balances. | two snapshots/tolerances → discrepancies | None | validation errors | ReconciliationService | reconciliation tests | Used | Essential |
| `AuthorityAndRetryGuard` | Class | Lock unresolved scopes, force reconcile-before-retry and expose gate result. | scope/outcome/resolution → state/bool/result | Local state mutation | mapped errors | live gate 13; reconciliation service | reconciliation/integration tests | Used | Essential |
| `ReconciliationService`, `ReconciliationReport` | Class/model | Execute startup/periodic/manual comparison, persist resolution and release/retain authority. | snapshot providers/stores/guard → report | External API read-only, persistence write, local state mutation | provider/store errors | live timeout hook intended; explicit production composition unconfirmed | reconciliation tests/usage | Possibly used | Essential |

### `monitoring/*`

| File / symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `HeartbeatEmitter` | Class | Emit periodic dead-man heartbeat through injected callback. | clock/emitter/interval → emission decision | Event publication | callback errors | MonitoringService | monitoring tests/usage | Test-only | Supporting |
| `IncidentSignal`, `OperationalSignalsManager` | Model/class | Rate-limit, dispatch and escalate incident signals with runbook binding. | incident/config/callbacks → dispatch result | Event publication/external notification via injected callback | callback/config errors | MonitoringService | monitoring tests/usage | Test-only | Supporting |
| `LatencyTracker`, `LostOrderWatchdog` | Classes | Bounded latency history and stale order detection. | samples/orders/time → statistics/incidents | Local state mutation | validation errors | MonitoringService | monitoring tests | Test-only | Supporting |
| `ToolHealthMonitor` | Class | Track consecutive tool failures/recovery. | tool outcome → health state | Local state mutation | validation errors | MonitoringService | monitoring tests | Test-only | Supporting |
| `MonitoringService` | Class | Aggregate metrics, watchdogs, circuit-breaker and incident outputs. | monitoring components/events → state/signals | Local state mutation/event publication | delegated errors | no production composition found | monitoring tests/usage | Possibly used | Supporting |

### `promotion/*`

| File / symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ladder.py` constants/functions | Constants/functions | Define linear stage order, route/capability compatibility, request hash and transition approval checks. | route/stage/capability/current/target/approvals → decision/none/hash | None | mapped validation/approval errors | live gate 3, config/usage | promotion/gate tests | Used | Essential |
| `preconditions.py` functions | Functions | Block activation when evidence or simulation metadata is absent/incompatible. | preactivation evidence / metadata lookup → validation result | Read-only | mapped errors | promotion workflow/usage | promotion tests | Used | Supporting |

### `runtime/*`

| File / symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ConcurrencyLockManager` | Class | Queue/acquire/release bounded `(account_id, symbol)` leases. | scope/timeout → lease/decision | Local state mutation, blocking wait | timeout/mapped errors | live gate 12 | runtime/integration tests | Used | Essential |
| `StrategyOwnershipValidator`, `CrossStrategyPolicyEvaluator` | Classes | Enforce ownership and cross-strategy counter policy. | strategy/position/order policy → validation/decision | None/local state | mapped errors | no production caller confirmed | coordination tests | Test-only | Supporting |
| `CostController` | Class | Check configured budget ceilings and record actual costs. | request/workflow/strategy/account/session/cost → decision/state | Local state mutation | budget breach/mapped errors | no link from `LiveGatePipelineImpl` confirmed | cost tests/usage | Test-only | Supporting |
| `SessionManager`, `SessionState` | Class/enum | Manage state/mode, singleton live scope, reconnect lockout, CoD heartbeat, order expiry and halted symbols. | injected stores/clock/callbacks + commands → state/results | Local state mutation, persistence write, event publication, read-only reconciliation callbacks | mapped/state errors | live gate 4 and runtime tests | Used | Essential |
| `SignalProcessor.process_strategy_signal` | Class method | Parse a raw dictionary, require live references/evidence, build envelope and call supplied gate runner. | signal + callback → `(envelope, decision)` | Delegated gate side effects | `TradingValidationError` | usage/tests only; no strategy-domain caller found | signal tests/usage | Test-only | Questionable |

## 6. Actual Workflows

### `V1-WF-TRADING-001` — Validate and Package an Order Without Broker Mutation

* **Scope:** Internal
* **Trigger:** Caller invokes `buy`, `sell`, a pending-order action, `position_open`, or another action with no live pipeline injected, or with a non-live route.
* **Input boundary:** Explicit `OrderValidationContext`, route/stage/capability, trace IDs, action parameters and `TradingActionDependencies`.
* **Functions and methods used:** `validate_order_request` → `package_request` → `dispatch_or_package` → `ExecutionCoordinator.build_broker_dispatch_payload`.
* **Files involved:** `actions/validation.py`, `actions/orders.py`, `actions/positions.py`, `actions/_common.py`, `execution/coordinator.py`, `contracts.py`.
* **External dependencies:** None beyond injected evidence; no broker call.
* **Output boundary:** `TradingResponseEnvelope(status=accepted, side_effect_mode=packaged_only)` containing a dispatch payload.
* **Failure behaviour:** Validation raises mapped/validation errors. Missing live pipeline fails closed to packaged-only rather than silently dispatching.
* **Operational status:** **Working**
* **Evidence:** `actions/_common.py::dispatch_or_package`; `actions/orders.py::_validate_and_package`; `tests/trading/usage/07_trading.py::example_07_actions_and_validation`.

```text
Action parameters + explicit evidence
→ validate_order_request()
→ package_request()
→ dispatch_or_package()
→ packaged-only TradingResponseEnvelope
```

### `V1-WF-TRADING-002` — Live Order Mutation Through Sixteen Gates

* **Scope:** Cross-domain
* **Trigger:** A live action is invoked with `TradingActionDependencies.gate_pipeline=LiveGatePipelineImpl`.
* **Input boundary:** Validated `TradingRequestEnvelope`, policy/evidence, session manager, stores, lock manager, audit sink, broker-dispatch factory and explicit risk evaluator.
* **Functions and methods used:** action → `dispatch_or_package` → `LiveGatePipelineImpl.evaluate` → `run_gate_pipeline` → `build_broker_dispatch_callable`/`broker.trade` → `normalize_broker_response` → `finalize_dispatch_outcome`.
* **Files involved:** actions, `gates/live_pipeline.py`, all gate modules, `execution/broker_dispatch.py`, `execution/response_classifier.py`, `execution/coordinator.py`, state stores.
* **External dependencies:** `app.services.brokers.router` and active broker adapter; injected persistence/audit implementations.
* **Output boundary:** Success/rejection/unknown-outcome `TradingResponseEnvelope`; state/idempotency finalized; lease released.
* **Failure behaviour:** First blocking gate short-circuits and records downstream steps as skipped. Broker timeout is unknown outcome, not ordinary failure. Audit failure blocks before dispatch.
* **Operational status:** **Partial**
* **Evidence:** Implemented call path in `gates/live_pipeline.py`; single mutation call in `execution/broker_dispatch.py::build_broker_dispatch_callable`; integration tests and real-account usage examples. Production composition was not found. Gate 7 can be intentionally passed by `passthrough_risk_evaluator`.

```text
Validated live action
→ gates 1–15
→ broker dispatch (gate 16)
→ normalize response
→ finalize TradeStore/idempotency
→ release concurrency lease
→ response
```

### `V1-WF-TRADING-003` — Unknown Broker Outcome and Forced Reconciliation

* **Scope:** Cross-domain
* **Trigger:** Broker dispatch exceeds the configured synchronous timeout or returns an outcome classified as unknown.
* **Input boundary:** In-flight request, broker callable, local projections and broker snapshot provider.
* **Functions and methods used:** timed dispatch → unknown classification → `snapshot_broker_state`/reconciliation hook → `ReconciliationService`/`compare_snapshots` → `AuthorityAndRetryGuard`.
* **Files involved:** `gates/live_pipeline.py`, `execution/response_classifier.py`, `execution/broker_dispatch.py`, `reconciliation/*`, `state/trade_store.py`.
* **External dependencies:** Active broker read-only order/position APIs and injected stores.
* **Output boundary:** Unknown-outcome response with reconcile-before-retry semantics; scope remains blocked until resolved.
* **Failure behaviour:** No automatic blind retry. Snapshot/reconciliation failure keeps authority locked.
* **Operational status:** **Partial**
* **Evidence:** README execution lifecycle; `broker_dispatch.py::snapshot_broker_state`; reconciliation exports/tests. Default pipeline hook only snapshots; a full `ReconciliationService` production hook was not confirmed.

```text
Broker timeout
→ UNKNOWN_OUTCOME
→ broker/local snapshots
→ compare_snapshots()
→ retain or release authority lock
→ retry allowed only after resolution
```

### `V1-WF-TRADING-004` — Read-Only Account, Symbol, Order, Position and History Queries

* **Scope:** Cross-domain
* **Trigger:** Caller instantiates a facade and invokes selection/accessor methods.
* **Input boundary:** Optional symbol or ticket.
* **Functions and methods used:** facade method → `info._common.broker_call` → `app.services.brokers.get_broker_module` → adapter read method → `safe_attr`/redaction.
* **Files involved:** `info/*`, `security/redaction_boundary.py`, broker router.
* **External dependencies:** Active broker read APIs.
* **Output boundary:** Neutral scalar/default or redacted JSON payload.
* **Failure behaviour:** Missing broker method, provider exception or cast failure is logged and converted to `None`/neutral default.
* **Operational status:** **Working**
* **Evidence:** `info/_common.py`; all facade classes; `tests/trading/unit/info/test_info_facades.py`; usage example 06.

```text
symbol/ticket/property request
→ broker_call()
→ broker read API
→ safe_attr()/redact_for_boundary()
→ neutral broker-independent value
```

### `V1-WF-TRADING-005` — Activate and Enforce Kill Switches

* **Scope:** Internal and cross-domain
* **Trigger:** Operator/system invokes a global, strategy or symbol kill-switch action.
* **Input boundary:** Scope, reason, actor, route/stage, IDs, injected idempotency store and event journal.
* **Functions and methods used:** `trigger_*_kill_switch` → idempotency key/hash/reserve → journal append. Later, `evaluate_kill_switches` blocks/permits an action according to policy. Clearing global state uses dual approval.
* **Files involved:** `actions/controls.py`, `state/idempotency.py`, `state/event_journal.py`, `gates/kill_switch.py`, `gates/approval.py`, `gates/policy_matrix.py`.
* **External dependencies:** Injected persistence; operator approval source.
* **Output boundary:** Audited activation response; subsequent live mutations blocked except policy-approved emergency/protective actions.
* **Failure behaviour:** Blank scope/reason/actor raises mapped error; persistence failure prevents reliable activation record. Clearing global switch fails without two distinct valid operators.
* **Operational status:** **Working at component level; production wiring unverified**
* **Evidence:** controls and gate implementations; unit/integration/usage tests.

```text
trigger scope
→ reserve idempotency
→ journal activation
→ gate 5 evaluates switch + policy
→ block or continue
```

### `V1-WF-TRADING-006` — Durable Idempotency, Journal and Projection Recovery

* **Scope:** Internal
* **Trigger:** Command reservation, state update, fill/report finalization, snapshot, replay or restart.
* **Input boundary:** Canonical command material, tenant/route namespace, event/state payload and expected version.
* **Functions and methods used:** `compute_idempotency_key`/`reserve`/`complete`; `AppendOnlyEventJournal.append_event`/snapshot/seal/replay; `TradeStore.save_*`; `LocalStateManager`.
* **Files involved:** `state/idempotency.py`, `state/event_journal.py`, `state/trade_store.py`, `state/manager.py`, `state/ports.py`.
* **External dependencies:** Filesystem or injected store/encryption implementations.
* **Output boundary:** Durable lease/event/projection/snapshot or reconstructed state.
* **Failure behaviour:** Active duplicate is rejected/cached; expired live lease requires reconciliation; version conflict fails closed; journal integrity errors prevent trusted replay.
* **Operational status:** **Working in unit/usage paths; deployment wiring unverified**
* **Evidence:** state implementations and focused unit tests; usage example 05.

```text
canonical command/event
→ hash/reserve
→ append journal + save projection
→ snapshot/seal
→ replay/reconcile after restart
```

### `V1-WF-TRADING-007` — Process Strategy Signal Into a Trading Request

* **Scope:** Cross-domain
* **Trigger:** A strategy or orchestration layer calls `SignalProcessor.process_strategy_signal`.
* **Input boundary:** Raw signal dictionary plus a gate-runner callback.
* **Functions and methods used:** enum parsing → live quote/risk-reference/approval presence checks → `TradingRequestEnvelope` construction → callback invocation.
* **Files involved:** `runtime/signal_processor.py`, `contracts.py`, supplied gate runner.
* **External dependencies:** Upstream strategy signal producer and downstream gate runner.
* **Output boundary:** `(TradingRequestEnvelope, GatePipelineDecision)`.
* **Failure behaviour:** Missing or malformed route/stage/capability/action/IDs/live evidence raises `TradingValidationError`.
* **Operational status:** **Unverified**
* **Evidence:** implementation and unit/usage tests only; no production strategy-domain caller was confirmed.

```text
strategy signal dict
→ validate enums/IDs/live references
→ build TradingRequestEnvelope
→ supplied gate runner
→ envelope + gate decision
```

### `V1-WF-TRADING-008` — Emergency Cancel, Close or Flatten

* **Scope:** Cross-domain
* **Trigger:** Incident/operator invokes cancel-all, close-all, or flatten by account/strategy/symbol.
* **Input boundary:** Scope, route/stage/capability, trace IDs, dependencies and optional quote.
* **Functions and methods used:** broker pre-snapshot → child cancel/close action packaging → pipeline dispatch per child → broker post-snapshot → aggregate details.
* **Files involved:** `actions/emergency.py`, order/position actions, info helpers, live pipeline and broker dispatch.
* **External dependencies:** Active broker read and mutation APIs.
* **Output boundary:** Aggregate response with per-child success/failure and partial completion.
* **Failure behaviour:** Individual child failures do not erase successful children; outcome remains explicit and auditable.
* **Operational status:** **Partial**
* **Evidence:** emergency implementation/tests and usage example; production incident caller not found.

```text
emergency scope
→ pre-action snapshot
→ cancel child orders
→ close child positions
→ post-action snapshot
→ aggregate partial/full result
```

### `V1-WF-TRADING-009` — Session Lifecycle, Reconnect and Symbol Halt Control

* **Scope:** Internal
* **Trigger:** Runtime starts/pauses/stops/recovers a session, loses/re-establishes connection, or turbulence halts a symbol.
* **Input boundary:** Account/session scope, operational mode, clock, state store, heartbeat/expiry/reconciliation callbacks.
* **Functions and methods used:** `SessionManager` state transitions; local heartbeat where CoD is absent; halted-symbol set; reconnect reconciliation lock; gate 4 session check.
* **Files involved:** `runtime/session_manager.py`, `gates/live_pipeline.py`, `gates/pipeline.py`, `execution/broker_capability_validation.py`, reconciliation.
* **External dependencies:** Injected state persistence, adapter capability evidence and callbacks.
* **Output boundary:** Authoritative session state/mode and admission decision.
* **Failure behaviour:** Ambiguous restored state fails closed to paused/read-only; reconnect blocks mutation until reconciliation.
* **Operational status:** **Working at component level; production host unverified**
* **Evidence:** session manager implementation, live gate integration and runtime tests.

```text
session command/connectivity event
→ state/mode update
→ heartbeat/expiry/reconciliation controls
→ gate 4 admission or block
```

### `V1-WF-TRADING-010` — Promotion and Runtime Configuration Readiness

* **Scope:** Internal
* **Trigger:** Configuration load/reload, promotion request or live readiness dry run.
* **Input boundary:** Config mapping, route/stage/capability, security profile, simulation metadata, approvals and readiness evidence.
* **Functions and methods used:** `load_trading_config`/reload validation → `validate_preactivation_conditions` → `validate_promotion_transition`/`validate_route_stage_capability` → readiness validators.
* **Files involved:** `config/*`, `promotion/*`, `gates/readiness.py`, `gates/approval.py`.
* **External dependencies:** Injected secret resolver/reauthentication and evidence producers when used.
* **Output boundary:** Validated config/change event, allowed transition or blocking error/readiness report.
* **Failure behaviour:** Unknown matrix entry, missing precondition, invalid security profile, stale evidence or excessive drift fails closed.
* **Operational status:** **Working at component level; host orchestration unverified**
* **Evidence:** config/promotion/readiness implementations and unit/usage tests.

```text
config + promotion/readiness evidence
→ parse/hash/redact
→ precondition + matrix + approval checks
→ readiness dry run
→ activate or block
```

## 7. Usage and Caller Map

| Public symbol / group | Called from | Call type | Runtime or test | Evidence |
| --------------------- | ----------- | --------- | --------------- | -------- |
| `get_trading_public_catalog` | `tests/trading/usage/07_trading.py::example_01_contracts` | direct call | Test/usage | usage file import and call |
| Contract enums/envelopes | actions, gates, execution, state, analytics journal adapter | import/construct/validate | Runtime + tests | imports in implementation files; `analytics/adapters/journal_adapters.py` imports `ExecutionReport`, `Fill`, `TradeResult` |
| `validate_order_request` | `actions/orders.py::_validate_and_package` | direct call | Runtime | explicit call in orders module |
| `buy`, `sell` | `actions/positions.py::position_open`; usage | direct call | Runtime + usage | explicit imports/call |
| Pending-order and order mutation functions | usage; unit tests | direct call | Test/usage | `tests/trading/usage/07_trading.py` and order tests |
| `position_close`, `position_modify` | usage; unit tests | direct call | Test/usage | usage imports and calls |
| `pause_strategy`, `trigger_symbol_kill_switch`, `flatten_symbol` | usage; unit tests | direct call | Test/usage | usage imports and calls |
| `dispatch_or_package` | orders/positions/emergency | direct call | Runtime | implementation imports/calls |
| `LiveGatePipelineImpl.evaluate` | `dispatch_or_package` through protocol | dynamic method call | Runtime path | `actions/_common.py`; integration tests |
| `run_gate_pipeline` | `LiveGatePipelineImpl` | direct call | Runtime | live pipeline imports/calls |
| Policy, approval, kill-switch, readiness, audit and reconciliation gate functions | `LiveGatePipelineImpl` | direct calls/adapters | Runtime | imports and gate adapter methods |
| `build_broker_dispatch_callable` | live pipeline factory supplied by composition/usage | callback factory | Runtime path, composition unconfirmed | broker dispatch module and usage builder |
| `broker.trade` | closure returned by `build_broker_dispatch_callable` | dynamic provider call | Runtime | `execution/broker_dispatch.py` |
| `normalize_broker_response` | broker dispatch closure | direct call | Runtime | broker dispatch module |
| `finalize_dispatch_outcome` | live pipeline | direct call | Runtime | live pipeline imports/calls |
| `snapshot_broker_state` | live pipeline unknown-outcome default reconciliation hook | direct callback | Runtime | live pipeline import/default behavior |
| `TradeStore` implementations | live finalization, sync and reconciliation | protocol calls | Runtime | coordinator/live pipeline/controls |
| Idempotency store/functions | live gate 11, kill-switch activation, usage | protocol/direct calls | Runtime + usage | gates, controls, usage |
| `AccountInfo`, `SymbolInfo`, `OrderInfo`, `PositionInfo`, `DealInfo`, `HistoryOrderInfo`, `TerminalInfo` | usage; validation/readiness callers may construct | class instantiation/method calls | Usage + possible runtime | usage example 06 |
| `broker_call` | all info facades; `sync_positions` | dynamic string-based method lookup | Runtime | `info/_common.py`; controls |
| Reconciliation classes/functions | live gate 13, usage/tests | direct/protocol calls | Runtime path + usage | live pipeline imports; reconciliation tests |
| Monitoring classes | usage and `MonitoringService` internal composition | instantiation/method calls | Test/usage | usage and monitoring tests |
| Promotion functions | live gate 3, usage/tests | direct calls | Runtime + usage | live pipeline import; promotion tests |
| `SessionManager` | live gate 4; usage/tests | injected object/method/property calls | Runtime + usage | live pipeline constructor and gate step |
| `ConcurrencyLockManager` | live gate 12; usage/tests | injected object/method calls | Runtime + usage | live pipeline constructor |
| `SignalProcessor` | signal unit tests and usage | class instantiation/direct call | Test/usage | no production strategy caller confirmed |
| Security mapping/redaction/DLQ | actions/gates/info/config/usage | direct call/class use | Runtime + usage | implementation imports and usage |
| Reporting/shadow/OCO/multi-leg helpers | usage and unit tests | direct call | Test/usage | no external production caller confirmed |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --------------------------- | -------------------------------- | ------------------------- | -------- |
| `app.services.brokers` / `app.services.brokers.router` | Active broker resolver, `trade`, account/symbol/order/position/history/terminal read APIs | `execution/broker_dispatch.py`; `info/_common.py`; `actions/controls.py` via info helper | direct imports and dynamic method names |
| `app.utils.logger` | Operational logging | nearly every file | direct imports |
| `app.utils.security` | `redact_text`, `redact_value` and related redaction helpers | root/security error mapping and boundary code | direct imports |
| `app.utils.standard` | canonical JSON and sensitive key/value patterns | `contracts.py` | direct imports |
| `app.utils.normalization` | timestamp normalization | compatibility contracts | direct import |
| `app.utils.settings` | runtime settings in usage/composition | usage file; any production use not confirmed | direct usage import |
| `pydantic` | models, validators, immutability and serialization | contracts/config/gates/state/etc. | direct third-party imports |
| Filesystem | JSONL idempotency, journal, trade store and DLQ persistence | `state/*`, `security/redaction_boundary.py` | implementation responsibilities |
| External risk domain | **No actual evaluator consumed by default path.** Only risk evidence IDs/types/seams are present. | `SignalProcessor`, gate approval evidence, `LiveGatePipelineImpl.risk_evaluator` callback | passthrough evaluator and README warning |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| `app.services.analytics.adapters.journal_adapters` | `ExecutionReport`, `Fill`, `TradeResult` | Convert trading journals into analytics `TradingResult` | direct current import |
| `tests/trading/unit` | Broad public and internal surface | Unit verification | reorganized current test tree and imports |
| `tests/trading/integration` | Live pipeline composition | End-to-end gate/dispatch behavior | `test_live_pipeline_integration.py` |
| `tests/trading/usage/07_trading.py` | At least 123 distinct trading symbols | Runnable examples, including real broker mutation examples | direct imports |
| Upstream strategy/orchestration | `SignalProcessor` is intended to receive signal dictionaries | Build request envelope and run supplied gate callback | implementation contract only; no caller confirmed |
| AI/agent layer | Registry metadata for `create_trading_action_draft` | Discover a non-mutating draft tool | registry exists; actual agent registration not found |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| `contracts.py::OrderIntent` | `actions/validation.py::OrderIntent` | Same name for different trade-intent stages and numeric models; compatibility model uses floats while action validation uses `Decimal`. | both definitions and imports | Ambiguous imports, conversion loss and incorrect stage usage |
| `errors.py::TradingError` hierarchy | `security/error_mapping.py::TradingMappedError` hierarchy | Two public exception hierarchies and two validation/timeout types. | direct definitions/imports | Callers can catch/map the wrong type; code drift |
| `errors.py::to_trading_error_payload` | `security/error_mapping.py::map_exception_to_trading_error` | Both expose redacted public error mapping, but one returns a dict and one a contract. | function implementations | Inconsistent return type at boundaries |
| `errors.py::TRADING_ERROR_CODES` | `security/error_mapping.py::_classify_exception` and text mappings | Competing code sources; mapper emits codes not present in the root allowlist. | `DATABASE_ERROR`, `CIRCUIT_OPEN`, `DATA_NOT_FOUND` examples | Unrecognized or undocumented public errors |
| `Contract` | `TradingContract` | Two local base model families with different configuration, trace fields and serialization behavior. | both in `contracts.py` | Inconsistent mutability, schema and trace semantics |
| `AccountInfo.info_*` / `TicketInfoFacade.info_*` | Named accessor methods | Numeric property-ID compatibility wrappers duplicate named accessors. | facade implementations | Larger API and mapping maintenance burden; useful only for MQL-style compatibility |
| `snapshot_broker_state` | Info facades / `sync_positions` | Multiple read-only broker snapshot paths with different projections. | broker dispatch, info, controls | Divergent fields and reconciliation interpretation |
| `reporting.py` execution-quality event | Analytics adapters/metrics | Trading constructs an event while analytics owns aggregation. | README and reporting exports | Boundary can blur if both domains evolve event semantics independently |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| `runtime/signal_processor.py::SignalProcessor` | Only unit/usage callers confirmed. No strategy-domain or runtime-host caller found. | Direct known-file fetches, commit history, unavailable GitHub code search | **Low** | implementation plus signal tests/usage |
| `runtime/cost_control.py::CostController` | Budget controller exists, but `LiveGatePipelineImpl` constructor/gates do not include it. | Live pipeline imports/constructor reviewed; runtime exports/tests reviewed | **Medium** | absent from live pipeline dependencies |
| Monitoring classes | Rich component suite, but no production root composition found. | package README, exports, usage/tests, unavailable repo search | **Low** | monitoring tests/usage only confirmed |
| `state/manager.py::LocalStateManager` | No internal runtime caller confirmed; stores are used directly elsewhere. | state exports and known internal imports reviewed | **Medium** | manager tests only confirmed |
| `execution/reporting.py` | No inbound production caller confirmed; analytics imports compatibility contracts, not the report builder. | analytics journal adapter fetched; usage/tests reviewed | **Medium** | usage/reporting tests |
| `execution/shadow.py` | No live runtime caller confirmed. | live pipeline/coordinator exports and usage reviewed | **Medium** | shadow tests/usage |
| OCO/multi-leg/non-atomic coordinator helpers | Implemented and tested; top-level action exposure exists for OCO only. External runtime callers not confirmed. | execution/action imports and usage reviewed | **Medium** | coordinator tests/usage |
| `tool_registry.py::get_trading_tool_definition` | Public by naming but not exported from root or subpackage `__all__`; only tests likely use it. | root/tool registry exports reviewed | **Medium** | omitted from `__all__` |
| `AccountInfo.margin_so_mode`, `free_margin_mode` | Always return `0`; no broker evidence read. | direct source review | **High for behavior; Low for usage** | explicit method bodies |
| `AccountInfo.trade_mode` | Infers live/real from server-name text rather than broker trade-mode field. | direct source review | **High for behavior** | method implementation |
| `errors.py::trading_retry_delay` | Uses global random despite package determinism policy; no confirmed caller. | direct source review and public imports | **Medium** | direct `random()` call |
| Compatibility contracts `TradeRequest`, `TradeResult`, `Fill`, `ExecutionReport`, `BrokerCapabilities` | Some are genuinely used by analytics; others may be legacy compatibility. Per-symbol caller completeness is unknown. | direct analytics import confirms three; repo search unavailable | **Low-to-Medium** | analytics imports `TradeResult`, `Fill`, `ExecutionReport` |
| Notification/secret/security-profile helpers | Tested and usable, but production configuration host not found. | config exports, usage/tests, repo search unavailable | **Low** | config tests/usage |

No item is declared dead code because the required full static and dynamic searches could not be completed.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Live pre-trade risk gate | Real `app.services.risk` evaluator is not wired; `passthrough_risk_evaluator` unconditionally passes. | A live order can traverse all gates without a validated risk decision. | `gates/live_pipeline.py::passthrough_risk_evaluator`; README Risk Gate section |
| Strategy signal → live action | `SignalProcessor` builds an envelope and runs a generic callback, but no production strategy caller/composition is confirmed. | Signal processing may remain isolated from the action/live dispatch path. | `runtime/signal_processor.py`; tests/usage only |
| Cost controls → live gate path | `CostController` is not a constructor dependency or gate in `LiveGatePipelineImpl`. | Budget ceilings may not block actual broker dispatch. | runtime exports versus live pipeline constructor |
| Monitoring → session/kill switch | Monitoring components exist, but no confirmed production wiring to trigger session halt or kill switches. | Incidents may be observable in tests without enforcing runtime action. | monitoring package and absent composition |
| Unknown outcome → full reconciliation | Default hook snapshots broker state; a `ReconciliationService` hook is optional and not confirmed. | Timeout may collect evidence without completing authority resolution. | live pipeline constructor/default hook; reconciliation service |
| Kill-switch trigger → durable gate state | Trigger functions journal/reserve activation, while gate evaluation reads `KillSwitchState` supplied separately. Automatic projection from trigger event to the gate state was not confirmed. | A trigger response alone may not update the state object used by gate 5. | `actions/controls.py` versus `gates/kill_switch.py` |
| AI registry → executable tool | Registry exposes metadata for a draft tool but no callable implementation/agent registration was found. | Tool discovery may not lead to an executable draft workflow. | `tool_registry.py`; no agent binding found |
| Promotion/config → runtime host | Validators and models exist, but no host process was confirmed to apply them before session activation. | Component tests do not prove deployment enforcement. | config/promotion packages |
| Read-only facade accuracy | Several compatibility fields are inferred or constant. | Callers can receive neutral/approximate values that appear authoritative. | `info/account.py` methods |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-TRADING-001` | Live risk gate can be an unconditional passthrough. | `gates/live_pipeline.py::passthrough_risk_evaluator` | Critical live safety gap; presence of a risk reference is not risk validation. | explicit warning and unconditional `passed_step` |
| `V1-ISSUE-TRADING-002` | Duplicate exception hierarchies and boundary mappers. | `errors.py`; `security/error_mapping.py` | Inconsistent catching, codes and response types. | parallel classes/functions |
| `V1-ISSUE-TRADING-003` | Error-code registry is internally inconsistent. | `errors.py` and security mapper | Public errors such as `CIRCUIT_OPEN`, `DATA_NOT_FOUND`, `DATABASE_ERROR` may bypass the declared set; `LIVE_POLICY_UNDEFINED` conflicts with `TRADING_POLICY_UNDEFINED`. | constants and mappings |
| `V1-ISSUE-TRADING-004` | Duplicate `OrderIntent` names represent different stages/types. | `contracts.py`; `actions/validation.py` | Import ambiguity and float/Decimal conversion risk. | both public classes |
| `V1-ISSUE-TRADING-005` | Determinism policy is violated by direct wall-clock and random use. | `contracts.py::Contract.created_at`; `errors.py::trading_retry_delay` | Replay/tests can differ despite injected `Clock`/`RNG` policy. | `datetime.now(UTC)` and `random()` |
| `V1-ISSUE-TRADING-006` | `contracts.py` contains many unrelated contract families and two base-model systems. | `contracts.py` | High cognitive load, broad coupling and inconsistent semantics. | file responsibilities and definitions |
| `V1-ISSUE-TRADING-007` | Cost controller is disconnected from live dispatch. | `runtime/cost_control.py`; `gates/live_pipeline.py` | Budget checks may never protect broker mutation. | absent live pipeline dependency/gate |
| `V1-ISSUE-TRADING-008` | Kill-switch activation and gate-state projection are separate with no confirmed bridge. | `actions/controls.py`; `gates/kill_switch.py` | Activation may be journaled without changing the supplied gate state. | separate persistence/evidence paths |
| `V1-ISSUE-TRADING-009` | Read-only broker failures are converted to neutral defaults. | `info/_common.py::broker_call`; facades | “Zero/false/empty” can be indistinguishable from real broker values, hiding outages. | broad exception catch and fallback |
| `V1-ISSUE-TRADING-010` | Account facade includes hard-coded/inferred compatibility values. | `info/account.py` | Limited fidelity for stop-out/free-margin/trade-mode semantics. | constant `0` and server-string inference |
| `V1-ISSUE-TRADING-011` | Package “import side-effect free” claim conflicts with import-time logging. | `info/__init__.py`; `security/__init__.py` | Import behavior is not strictly pure, although it does not connect to brokers. | logger calls at module import |
| `V1-ISSUE-TRADING-012` | README usage path is stale after tests were reorganized. | `app/services/trading/README.md` | Developers are directed to `tests/usage/07_trading.py` instead of `tests/trading/usage/07_trading.py`. | README versus current tree |
| `V1-ISSUE-TRADING-013` | Public API is fragmented across root, subpackage exports and unexported public names. | root/subpackage `__init__.py`; `get_trading_tool_definition`; position enums | Callers must know implementation modules; discoverability and compatibility are inconsistent. | export lists and usage direct imports |
| `V1-ISSUE-TRADING-014` | Broker mutation and read-only reconciliation snapshot share one file. | `execution/broker_dispatch.py` | The “single mutation boundary” file also owns read concerns, weakening its single responsibility. | `build_broker_dispatch_callable` and `snapshot_broker_state` |
| `V1-ISSUE-TRADING-015` | Extensive test/usage coverage does not establish production usage. | most execution/monitoring/runtime helpers | High implementation volume may be disconnected from actual runtime value. | no production composition root found |
| `V1-ISSUE-TRADING-016` | `SignalProcessor` checks only the presence of risk/approval references before invoking a generic gate callback. | `runtime/signal_processor.py` | Callers may interpret syntactic references as validated authorization. | `_parse_quote` and process method |
| `V1-ISSUE-TRADING-017` | Root compatibility contracts use float fields for execution values while newer action contracts use `Decimal`. | `contracts.py` versus `actions/validation.py` | Precision and serialization inconsistencies at cross-domain boundaries. | model field types |
| `V1-ISSUE-TRADING-018` | Broad catches in read-only and shutdown paths suppress failures. | `info/_common.py`; `actions/controls.py::shutdown` | Operational failure can be reduced to neutral data or logged-only reconciliation failure. | exception handling bodies |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-TRADING-001` | Canonical trading contracts | `contracts.py`; root facade | 001–010 | Used | Essential | Shared with analytics journal adapters |
| `V1-CAP-TRADING-002` | Local order validation and normalization | `actions/validation.py::validate_order_request` | 001, 002 | Used | Essential | Explicit evidence; Decimal-based |
| `V1-CAP-TRADING-003` | Market and pending order actions | `actions/orders.py` | 001, 002 | Used | Essential | Packaged-only by default |
| `V1-CAP-TRADING-004` | Position lifecycle actions | `actions/positions.py` | 001, 002 | Used | Essential | Netting/hedging addressing |
| `V1-CAP-TRADING-005` | Strategy/session controls | `actions/controls.py` | 005, 009 | Used | Useful | Pause/resume mostly local response + journal |
| `V1-CAP-TRADING-006` | Emergency cancel/close/flatten | `actions/emergency.py` | 008 | Possibly used | Essential | Partial completion supported |
| `V1-CAP-TRADING-007` | Sixteen-gate live preflight | `gates/*`; `LiveGatePipelineImpl` | 002 | Used | Essential | Risk can be passthrough |
| `V1-CAP-TRADING-008` | Single broker mutation boundary | `execution/broker_dispatch.py` | 002, 008 | Used | Essential | Calls broker resolver, not SDK |
| `V1-CAP-TRADING-009` | Broker response normalization | `execution/response_classifier.py` | 002, 003 | Used | Essential | Distinguishes rejection and unknown outcome |
| `V1-CAP-TRADING-010` | Async dispatch and execution coordination | `execution/coordinator.py` | 002, 008 | Used | Essential | Includes IDs, allocations, OCO, multi-leg and finalization |
| `V1-CAP-TRADING-011` | Lifecycle state machine | `execution/state_machine.py` | 002, 006 | Possibly used | Essential | Unit-tested; runtime caller incomplete |
| `V1-CAP-TRADING-012` | Rate limiting | `execution/rate_limiter.py` | 002, 009 | Possibly used | Supporting | Readiness evidence integration not fully confirmed |
| `V1-CAP-TRADING-013` | Broker capability validation | `execution/broker_capability_validation.py` | 002, 009 | Used | Essential | Gate 15 and CoD fallback evidence |
| `V1-CAP-TRADING-014` | Execution reporting/TCA events | `execution/reporting.py` | 002 | Test-only | Useful | Analytics aggregation remains external |
| `V1-CAP-TRADING-015` | Shadow intent/fill comparison | `execution/shadow.py` | none confirmed | Test-only | Useful | No runtime caller confirmed |
| `V1-CAP-TRADING-016` | Read-only broker facades | `info/*` | 004 | Used | Useful | Neutral fallback can hide outages |
| `V1-CAP-TRADING-017` | Configuration load/reload/hash | `config/loader.py`, `config/models.py` | 010 | Possibly used | Supporting | Production host not found |
| `V1-CAP-TRADING-018` | Secret-reference and credential rotation | `config/secrets.py` | 010 | Test-only | Supporting | Injected interfaces only |
| `V1-CAP-TRADING-019` | Live security profile validation | `config/security_profile.py` | 010 | Test-only | Supporting | No activation host confirmed |
| `V1-CAP-TRADING-020` | Boundary error mapping/redaction | `security/*`, `errors.py` | all | Used | Essential | Duplicated implementations |
| `V1-CAP-TRADING-021` | Dead-letter/manual-review persistence | `WriteAheadDeadLetterQueue` | 003, 006 | Possibly used | Essential | Production caller not confirmed |
| `V1-CAP-TRADING-022` | Idempotency leases and completion cache | `state/idempotency.py` | 002, 005, 006 | Used | Essential | Live expiry requires reconciliation |
| `V1-CAP-TRADING-023` | Append-only encrypted journal and replay | `state/event_journal.py` | 005, 006 | Possibly used | Essential | Usage/tests confirm component behavior |
| `V1-CAP-TRADING-024` | Versioned trade projection store | `state/trade_store.py` | 002, 003, 006 | Used | Essential | In-memory and JSONL |
| `V1-CAP-TRADING-025` | Reconciliation comparison and authority guard | `reconciliation/*` | 003 | Used | Essential | Full timeout hook composition unconfirmed |
| `V1-CAP-TRADING-026` | Monitoring, heartbeat and incident signals | `monitoring/*` | 009 | Possibly used | Supporting | Production composition not found |
| `V1-CAP-TRADING-027` | Promotion ladder and preconditions | `promotion/*` | 002, 010 | Used | Essential | Gate 3 integration confirmed |
| `V1-CAP-TRADING-028` | Session lifecycle and operational modes | `runtime/session_manager.py` | 002, 009 | Used | Essential | Gate 4 integration confirmed |
| `V1-CAP-TRADING-029` | Per-scope concurrency coordination | `runtime/coordination.py` | 002 | Used | Essential | Gate 12 integration confirmed |
| `V1-CAP-TRADING-030` | Cost budget control | `runtime/cost_control.py` | none confirmed | Test-only | Supporting | Disconnected from live pipeline |
| `V1-CAP-TRADING-031` | Strategy signal translation | `runtime/signal_processor.py` | 007 | Test-only | Questionable | No upstream caller confirmed |
| `V1-CAP-TRADING-032` | Packaged-only AI tool catalog | `tool_registry.py` | 001 | Used | Useful | Metadata only; no callable binding found |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The evidence supports real value in the broker-neutral request/response contracts, Decimal-based order validation, fail-closed packaged-only default, explicit live gate ordering, single broker mutation boundary, unknown-outcome handling, idempotency, trade projections, reconciliation authority, emergency scope actions, session admission controls, read-only broker facades, and security redaction.

### Behaviour that exists but is disconnected or only partially connected

The strongest examples are `CostController`, monitoring orchestration, `SignalProcessor`, full reconciliation service hookup, notification/secret rotation hosts, AI registry execution binding, and automatic propagation from kill-switch trigger events into the `KillSwitchState` evidence consumed by gate 5. These are implemented and tested, but their production call paths were not confirmed.

### Likely dead weight

No item can be labelled dead code at High confidence because full repository-wide search and runtime execution were unavailable. The most questionable candidates are duplicate error utilities, hard-coded account compatibility methods, unexported public registry lookup, disconnected cost/monitoring services, and test-only shadow/reporting/coordinator extensions. They should remain “questionable” rather than “dead.”

### Duplicated responsibilities

The main duplication is the pair of error systems, the two `OrderIntent` classes, two base contract families, repeated broker snapshot projections, and compatibility property-ID wrappers duplicating named accessors.

### Important uncertainties

* Whether a production application constructs `LiveGatePipelineImpl`.
* Whether production callers choose a real risk evaluator or the passthrough.
* Whether `ReconciliationService`, `MonitoringService`, `CostController`, and `SignalProcessor` are wired by configuration, dependency injection, decorators or string-based loading outside the files that could be searched.
* Whether JSONL stores are production persistence or only local/test implementations.
* Whether the usage script’s real-account examples are executed operationally.

### Areas requiring manual confirmation

1. Search a local clone for imports/calls of `app.services.trading`, all direct submodule imports, `LiveGatePipelineImpl`, `build_live_gate_pipeline`, `SignalProcessor`, `CostController`, `MonitoringService`, `ReconciliationService`, `create_trading_action_draft`, and the old `app.services.trader`/`app.services.live` names.
2. Inspect application startup, API routes, agents, schedulers and dependency-injection/configuration wiring.
3. Run `tests/trading/unit`, `tests/trading/integration`, and the safe non-mutating portions of `tests/trading/usage/07_trading.py`.
4. Confirm the actual evaluator passed to `LiveGatePipelineImpl.risk_evaluator` in every live composition.
5. Confirm how kill-switch activation events become the `KillSwitchState` tuple supplied to live gate evidence.

---

## Evidence Not Accessible

* A complete local repository clone and executable test environment.
* Reliable GitHub indexed code search results for repository-wide caller tracing.
* Deployment/startup configuration, runtime dependency injection, agent registrations, scheduled tasks and live operator configuration.
* Broker credentials or a safe demo account for executing the real-mutation usage examples.
