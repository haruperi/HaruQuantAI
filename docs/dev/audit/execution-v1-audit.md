# Execution — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `execution`
* **Repository:** `haruperi/HaruQuant`
* **Audited branch:** `main`
* **Audited commit:** `a39d26498e14772c571d75fa9a5f0e477a1dd912` — `refactor: remove unused and deprecated helper modules`
* **Package path:** `app/services/execution`
* **Tests searched:** current repository test tree, commit-associated execution tests, `tests/integration/backend`, `tests/unit/app/services`, and usage/example references
* **Files represented:** 48 Python files:
  * 20 package-root files;
  * 6 files under `approval/`;
  * 7 files under `reconciliation/`;
  * 15 files under `live/`.
* **Related packages searched:**
  * `app/api/routes/live.py`
  * `app/api/routes/ai_chat.py`
  * `app/services/brokers`
  * `app/services/trading`
  * `app/services/risk`
  * `app/services/governance`
  * `app/services/conversation`
  * `app/services/strategy`
  * `app/services/simulation`
  * `app/services/utils`
  * `app/agentic/contracts`
  * `data/database`
  * repository commit history for execution-service additions and associated tests

### Files inspected

#### Package root

`__init__.py`, `_common.py`, `assembler.py`, `attempts.py`, `authority.py`, `broker_connectivity.py`, `core.py`, `idempotency.py`, `kill_switch_tools.py`, `live_execution_tools.py`, `metadata_cache.py`, `normalization.py`, `paper_trading_tools.py`, `pre_send.py`, `readiness.py`, `readiness_tools.py`, `receipts.py`, `send_service.py`, `trade_action_governor.py`, `trading.py`.

#### `approval/`

`__init__.py`, `models.py`, `override.py`, `packet_builder.py`, `services.py`, `state_machine.py`.

#### `reconciliation/`

`__init__.py`, `broker_truth.py`, `comparison.py`, `incidents.py`, `persistence.py`, `retry_guard.py`, `startup.py`.

#### `live/`

`__init__.py`, `bar_monitor.py`, `config.py`, `dashboard.py`, `engine.py`, `models.py`, `mt5_compat.py`, `notification_adapter.py`, `position_manager.py`, `run.py`, `secrets.py`, `session.py`, `signal_processor.py`, `state_manager.py`, `trade_executor.py`.

### Registration and entry points checked

* `app/services/execution/__init__.py::__all__`
* `standardize_domain_exports(...)`
* `app/services/execution/_common.py::__getattr__`
* `app/services.service_modules(...)`
* `app/services.resolve_service_attr(...)`
* FastAPI route imports in `app/api/routes/live.py`
* AI-chat action-draft route in `app/api/routes/ai_chat.py`
* lazy exports in `app/services/execution/live/__init__.py`
* direct imports from `app.services.execution.trading`
* repository commit-associated unit and integration tests

### Audit limitations

1. The repository could not be cloned or executed in the audit environment. Imports, tests, broker calls, database migrations, thread behaviour, and live MT5 interactions were not run.
2. GitHub file retrieval was available, but an independent recursive current-tree API and reliable repository-wide code-search index were not available. Package completeness was reconstructed from direct file retrieval, package registries, internal imports, route imports, commit diffs, and prior current-ref audits.
3. Negative caller findings are therefore generally **Medium confidence**, not High, unless the conclusion is based on a directly missing file or a confirmed import/export mismatch.
4. Dynamic invocation by an external deployment, plugin, agent runtime, configuration string, or uncommitted local code cannot be ruled out.
5. Test files associated with many execution commits were visible in commit evidence, but the complete current test directory could not be independently enumerated. Tests are not treated as production callers.
6. Public methods in the very large compatibility modules `core.py`, `trading.py`, and the live engine are grouped by behaviour where listing every trivial alias would obscure the actual externally useful surface.
7. No Version 2 requirement, redesign, or code change is included.

---

## 2. Executive Summary

The Version 1 execution domain contains **four substantially different systems inside one package**:

1. **Agent-facing tool wrappers**
   Fifty-three root exports present broker checks, readiness checks, paper operations, live operations, and kill-switch actions. Most wrappers either perform small deterministic validation or merely package a request into a standard response. They do **not** perform the broker or persistence side effects implied by their names.

2. **A deterministic execution-governance service set**
   Approval, readiness, intent assembly, idempotency, send dispatch, send-attempt persistence, receipt normalization, authority state, and reconciliation are implemented as separate services. These components provide real isolated value, but their intended end-to-end paper workflow is not operational through the current package facade.

3. **An active live-trading runtime**
   `app.services.execution.live` is used by `app/api/routes/live.py`. It manages live sessions, strategy loading, bar monitoring, signal generation, position tracking, direct MT5-oriented trade execution, local state files, notifications, and status output. This is the clearest confirmed production/runtime value in the domain.

4. **Legacy broker/simulator compatibility implementations**
   `trading.py` provides a large MQL5-style `Trade` API and flat broker functions. `core.py` provides a broker-like in-memory simulation core. These overlap with `app/services/trading`, the live runtime, simulation code, and the newer send-service pipeline.

### Operational workflows

* **Confirmed working or substantially operational**
  * FastAPI live-session control through `LiveTradingSession`.
  * Live strategy loop through `MultiStrategyEngine`.
  * Signal-to-order execution through `TradeExecutor` and `execution.trading.Trade`.
  * Deterministic agent readiness calculations that do not require the disconnected governance chain.
  * Local approval creation/voting primitives when called directly with repositories.

* **Partial or unverified**
  * Pre-send readiness aggregation.
  * Receipt persistence and authority-state propagation.
  * Broker/local reconciliation.
  * Root agent-tool discovery and invocation.
  * File-based live pause/resume and status persistence.

* **Broken or disconnected**
  * `TradeActionGovernor` imports eight symbols from `app.services.execution`, but the root package exports none of them. `standardize_domain_exports` is a no-op, so a clean import is expected to fail.
  * The AI-chat `paper-execute` route does not call `TradeActionGovernor`; it only updates action-draft fields.
  * Reconciliation parses `ExecutionReceiptRecord.authoritative_state` as JSON, while receipt persistence writes the plain string `PROVISIONAL`.
  * `_common.execution_monitoring_module()` and `_common.execution_performance_module()` target files that do not exist.
  * Live execution bypasses the newer approval/readiness/intent/send/receipt/reconciliation chain and calls `execution.trading.Trade` directly.

### Most important structural problems

* The root public facade exposes request packagers rather than the services that perform real execution.
* Function names and docstrings imply live mutation, but wrappers return “No live side effects executed by default.”
* The approval check for critical wrappers only verifies that an `approval_id` value is present; it does not verify state, scope, expiry, approver count, or token authenticity.
* The domain contains multiple order-send paths with different validation, result, retry, and persistence behaviour.
* Live execution and governed execution are separate, incompatible call paths.
* `core.py` and `trading.py` contain broad, mixed responsibilities.
* Receipt status conventions are inconsistent (`accepted`, `ACCEPTED`, `FILLED`, `DONE`, `OK`).
* Several modules appear implemented primarily for tests or future wiring rather than current production use.

### Evidence trustworthiness

Evidence is **High** for directly inspected source, package exports, route imports, and the identified import/export defects. Evidence is **Medium** for “no caller found” findings because a fully indexed recursive caller search and runtime execution were unavailable. No item is labelled dead production code solely from a missing static caller.

```text
Module folders: 3 | Files: 48 | Public symbols: 207 represented (conservative grouped count) | Symbols with confirmed runtime/internal callers: 72 (34.8%) | Workflows found: 8
```

The public-symbol count includes 53 root exports and directly useful public classes, functions, methods, and constants in submodules. Large compatibility alias families are grouped, so the count is conservative rather than an AST-exact census.

---

## 3. Actual Package Structure

```text
app.services.execution
├── __init__.py
│   └── 53 agent-facing tool functions
├── _common.py
│   ├── execution_approval_module()
│   ├── execution_live_module()
│   ├── execution_monitoring_module()
│   ├── execution_performance_module()
│   ├── execution_reconciliation_module()
│   ├── execution_trade_governor_module()
│   ├── execution_tool_result()
│   ├── execution_tool_context()
│   ├── package_execution_request()
│   └── __getattr__()
├── assembler.py
│   ├── ExecutionIntentAssemblyConfig
│   └── assemble_execution_intent()
├── attempts.py
│   └── ExecutionAttemptPersistenceService.persist_attempt()
├── authority.py
│   ├── AuthorityStateView
│   └── propagate_authority_state()
├── broker_connectivity.py
│   └── 13 broker/account/symbol request-packaging functions
├── core.py
│   ├── broker-style information classes
│   ├── simulation result/state classes
│   ├── in-memory query functions
│   ├── monitor_* functions
│   └── order_send()
├── idempotency.py
│   └── generate_execution_idempotency_key()
├── kill_switch_tools.py
│   └── 10 kill-switch request-packaging functions
├── live_execution_tools.py
│   └── 10 live-execution request-packaging functions
├── metadata_cache.py
│   ├── SymbolMetadataCacheEntry
│   └── SymbolMetadataCache
├── normalization.py
│   └── normalize_broker_response()
├── paper_trading_tools.py
│   └── 9 paper-operation request-packaging functions
├── pre_send.py
│   ├── PreSendValidationRequest
│   └── run_pre_send_validation()
├── readiness.py
│   ├── ReadinessCheckResult
│   ├── ReadinessAggregateResult
│   └── 8 deterministic readiness functions
├── readiness_tools.py
│   └── 11 agent-facing validation/planning functions
├── receipts.py
│   ├── NormalizedExecutionReceipt
│   └── ExecutionReceiptService.persist_receipt()
├── send_service.py
│   ├── BrokerSendGateway
│   ├── BrokerSendResult
│   └── ExecutionSendService.send()
├── trade_action_governor.py
│   ├── GovernorApprovalState
│   ├── GovernedPaperExecutionResult
│   └── TradeActionGovernor.execute_paper_action_draft()
├── trading.py
│   ├── TradeResult
│   ├── Trade
│   └── flat broker connect/read/mutate functions
├── approval
│   ├── __init__.py
│   ├── models.py
│   │   ├── ApprovalState
│   │   ├── RiskClass
│   │   ├── ApprovalPacket
│   │   └── ApprovalRequest
│   ├── override.py
│   │   ├── OverrideRequestDraft
│   │   └── OverrideRequestService
│   ├── packet_builder.py
│   │   └── ApprovalPacketBuilder
│   ├── services.py
│   │   ├── ApprovalCreateRequest
│   │   ├── ApprovalCreationService
│   │   ├── ApprovalVoteRequest
│   │   └── ApprovalVoteService
│   └── state_machine.py
│       ├── APPROVAL_TRANSITIONS
│       └── ApprovalStateMachine
├── reconciliation
│   ├── __init__.py
│   ├── broker_truth.py
│   │   ├── BrokerTruthSnapshot
│   │   └── BrokerTruthFetcher
│   ├── comparison.py
│   │   ├── ReconciliationResultState
│   │   ├── LocalExecutionTruth
│   │   ├── ReconciliationComparison
│   │   ├── build_local_execution_truth()
│   │   └── compare_execution_truth()
│   ├── incidents.py
│   │   └── ReconciliationIncidentService
│   ├── persistence.py
│   │   └── ReconciliationPersistenceService
│   ├── retry_guard.py
│   │   ├── RetryGuardDecision
│   │   └── evaluate_retry_guard()
│   └── startup.py
│       ├── DEFAULT_IN_FLIGHT_EXECUTION_STATUSES
│       └── ReconciliationStartupLoader
└── live
    ├── __init__.py
    │   └── lazy exports for 10 live-runtime classes
    ├── bar_monitor.py
    │   └── BarMonitor
    ├── config.py
    │   ├── ConfigError
    │   ├── MT5Config
    │   ├── StrategyConfig
    │   ├── TradingConfig
    │   ├── SafetyConfig
    │   ├── NotificationConfig
    │   ├── LoggingConfig
    │   ├── StateConfig
    │   ├── LiveConfigModel
    │   ├── Config
    │   ├── get_schema_spec()
    │   ├── load_config_mapping()
    │   └── parse_live_config()
    ├── dashboard.py
    │   ├── Dashboard
    │   └── main()
    ├── engine.py
    │   ├── StrategyInstance
    │   └── MultiStrategyEngine
    ├── models.py
    │   ├── SignalType
    │   └── Signal
    ├── mt5_compat.py
    │   └── MT5 compatibility accessors
    ├── notification_adapter.py
    │   └── LiveTradingNotifier
    ├── position_manager.py
    │   └── PositionManager
    ├── run.py
    │   └── main()
    ├── secrets.py
    │   ├── SecretProviderError
    │   ├── SecretReference
    │   ├── parse_secret_reference()
    │   ├── resolve_secret_reference()
    │   └── get_secret()
    ├── session.py
    │   ├── ExecutionEngineWrapper
    │   └── LiveTradingSession
    ├── signal_processor.py
    │   └── SignalProcessor
    ├── state_manager.py
    │   └── StateManager
    └── trade_executor.py
        └── TradeExecutor
```

---

## 4. Module and File Inventory

Dependencies are listed in the requested order: standard library; required third-party; local modules.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| root | `__init__.py` | Public agent-tool facade | 53 tool functions | stdlib annotations; none; tool modules, `Trade`, standardizer | **Possibly used** | **Questionable** |
| root | `_common.py` | Tool envelopes, request packaging, lazy service access | 9 exported helpers + `__getattr__` | datetime, uuid, import helpers; none; `app.services`, utils standard | **Used internally** | **Supporting** |
| root | `assembler.py` | Construct validated execution intent | config, assembler | dataclasses/time; Pydantic-backed contracts; agentic contracts, ids | **Internally referenced by broken workflow** | **Useful** |
| root | `attempts.py` | Hash and persist send attempts | persistence service | hashlib; none; DB repository, canonical JSON | **Internally referenced by broken workflow** | **Useful** |
| root | `authority.py` | Resolve provisional/authoritative/reconciling display state | view, resolver | dataclasses; none; none | **Internally referenced** | **Supporting** |
| root | `broker_connectivity.py` | Package broker-read/check requests | 13 wrappers | typing; none; `_common` | **Possibly used** | **Questionable** |
| root | `core.py` | In-memory broker/simulation compatibility core | information/state/result classes; query/monitor/send functions | dataclasses, enum, math/time; pandas/numpy as applicable; simulator-local state | **Possibly used / no confirmed production caller** | **Questionable** |
| root | `idempotency.py` | Stable execution-request fingerprint | key generator | hashlib; none; agentic contracts, canonical JSON | **Internally referenced by broken workflow** | **Useful** |
| root | `kill_switch_tools.py` | Package critical safety requests | 10 wrappers | typing; none; `_common` | **Possibly used** | **Questionable** |
| root | `live_execution_tools.py` | Package live-capital requests | 10 wrappers | typing; none; `_common` | **Possibly used** | **Questionable** |
| root | `metadata_cache.py` | Store symbol metadata with timestamps | cache entry/cache | datetime; Pydantic; logger | **Internally referenced by readiness/governor** | **Supporting** |
| root | `normalization.py` | Normalize MT5-style response | `normalize_broker_response` | dataclasses/typing; none; none | **Used by receipt service** | **Supporting** |
| root | `paper_trading_tools.py` | Package paper operations | 9 wrappers | typing; none; `_common` | **Possibly used** | **Questionable** |
| root | `pre_send.py` | Coordinate readiness checks | request model, runner | datetime; none; readiness/cache/contracts | **Internally referenced by broken workflow** | **Useful** |
| root | `readiness.py` | Deterministic fail-closed execution checks | 2 results + 8 validators | dataclasses/time; none; risk validity, contracts | **Used internally** | **Essential support** |
| root | `readiness_tools.py` | Agent-facing lightweight checks/calculations | 11 functions | typing; none; `_common` | **Possibly used** | **Useful/Questionable** |
| root | `receipts.py` | Normalize and persist execution receipts | receipt record/service | dataclasses/typing; none; DB, normalizer, identity | **Internally referenced by broken workflow** | **Useful** |
| root | `send_service.py` | Dispatch typed intents to broker gateway | protocol/result/service | dataclasses/typing; none; execution contract, logger | **Internally referenced by broken workflow** | **Essential if connected** |
| root | `trade_action_governor.py` | Intended governed AI-chat paper workflow | approval/result/governor | dataclasses/time; none; six repositories, contracts, risk, conversation, execution facade | **Unused/broken in clean import** | **Questionable** |
| root | `trading.py` | Large MQL5-style broker and simulator adapter | `TradeResult`, `Trade`, flat functions | threading/time/dataclasses; provider APIs; brokers/logger | **Used by live runtime** | **Essential but overbroad** |
| approval | `__init__.py` | Approval package facade | 14 exports | none; none; approval submodules | **Possibly used** | **Supporting** |
| approval | `models.py` | Approval and risk classification records | 4 types | dataclasses/enum; none; none | **Used internally** | **Supporting** |
| approval | `override.py` | Validate override draft fields | draft/service | dataclasses; none; utils errors | **No confirmed caller** | **Questionable** |
| approval | `packet_builder.py` | Fluent approval packet construction | builder | typing; none; approval models | **No confirmed production caller** | **Useful** |
| approval | `services.py` | Persist approval creation and votes | 4 public types | sqlite/datetime; none; governance repository, utils | **Possibly used** | **Useful** |
| approval | `state_machine.py` | Validate allowed approval transitions | transition map/state machine | none; none; utils errors, models | **No confirmed production caller** | **Useful** |
| reconciliation | `__init__.py` | Reconciliation facade | 12 exports | none; none; reconciliation submodules | **Possibly used** | **Supporting** |
| reconciliation | `broker_truth.py` | Fetch broker order/position truth | snapshot/fetcher | dataclasses/typing; none; broker gateway | **No confirmed production caller** | **Useful** |
| reconciliation | `comparison.py` | Compare local intent/receipt against broker truth | 3 types + 2 functions | json/dataclasses/enum; none; DB records, broker truth | **No confirmed production caller** | **Useful but defective** |
| reconciliation | `incidents.py` | Persist reconciliation incidents | service | datetime/typing; none; incident repository/logger | **No confirmed production caller** | **Useful** |
| reconciliation | `persistence.py` | Persist reconciliation run/results | service | datetime/typing; none; execution repository | **No confirmed production caller** | **Useful** |
| reconciliation | `retry_guard.py` | Decide whether execution retry is safe | decision/evaluator | dataclasses; none; execution records/comparison | **No confirmed production caller** | **Useful** |
| reconciliation | `startup.py` | Load in-flight intents for startup reconciliation | status constant/loader | typing; none; execution repository | **No confirmed production caller** | **Useful** |
| live | `__init__.py` | Lazy live-runtime facade | 10 exported classes | importlib; none; live submodules | **Used** | **Essential** |
| live | `bar_monitor.py` | Detect new bars and fetch closed/historical bars | `BarMonitor` | datetime; pandas; MT5 client/logger | **Used by engine** | **Essential support** |
| live | `config.py` | Parse, overlay, validate, redact live config | 10 classes, 3 functions, schema constants | json/os/path/time; TOML/keyring optional; secrets/security | **Used by runner/runtime** | **Useful** |
| live | `dashboard.py` | Read and render runtime status | `Dashboard`, `main` | json/time/path; terminal display libs as available; status file | **Script/operational** | **Useful** |
| live | `engine.py` | Orchestrate multi-strategy live loop | `StrategyInstance`, `MultiStrategyEngine` | json/time/path; pandas; broker, risk, trading, strategy, live components | **Used** | **Essential** |
| live | `models.py` | Signal model | `SignalType`, `Signal` | enum/typing; Pydantic; none | **Used internally** | **Supporting** |
| live | `mt5_compat.py` | Normalize MT5 object/property access | compatibility functions | typing; none; broker objects | **Used internally** | **Supporting** |
| live | `notification_adapter.py` | Send live-event notifications | `LiveTradingNotifier` | typing; notification provider; logger | **Used internally** | **Useful** |
| live | `position_manager.py` | Query/filter positions and enforce count gate | `PositionManager` | typing; none; MT5 client, `execution.trading.Trade` | **Used by trade executor/engine** | **Essential support** |
| live | `run.py` | CLI/runtime launch | `main` | argparse/asyncio; none; config/engine | **Entry point** | **Useful** |
| live | `secrets.py` | Resolve `keyring://` references | 2 types + 3 functions | dataclasses; optional keyring; none | **Used by config** | **Supporting** |
| live | `session.py` | API-controlled session lifecycle | wrapper/session | asyncio/concurrency; none; DB, engine, logger | **Used by FastAPI** | **Essential** |
| live | `signal_processor.py` | Maintain rolling data and call strategy | `SignalProcessor` | none; pandas; strategy base/logger | **Used by engine** | **Essential support** |
| live | `state_manager.py` | Persist pause/enable/trade-count state to JSON | `StateManager` | json/threading/path/time; none; none | **Used internally** | **Useful** |
| live | `trade_executor.py` | Convert signals to retried `Trade` calls | `TradeExecutor` | time; none; position manager, MT5 compatibility, `Trade` | **Used by engine** | **Essential** |

---

## 5. Public Behaviour Inventory

### `__init__.py` — root execution facade

**File responsibility:** Import and expose agent-facing tool wrappers.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Broker exports: `check_broker_connection`, `check_free_margin`, `check_lot_step`, `check_market_open`, `check_max_lot`, `check_min_lot`, `check_stop_distance`, `get_account_info`, `get_broker_time`, `get_current_bid_ask`, `get_current_spread`, `get_symbol_info`, `get_trade_permissions` | Functions | Package broker read/check request | `**kwargs → dict` | None | Envelope helper errors | Root facade/dynamic consumers unconfirmed | Not executed | **Possibly used** | **Questionable** |
| Readiness exports: `build_execution_plan`, `estimate_slippage`, `estimate_transaction_cost`, `run_execution_readiness_check`, `validate_broker_symbol_mapping`, `validate_execution_environment`, `validate_order_price`, `validate_order_request`, `validate_order_size`, `validate_stop_loss_take_profit`, `validate_strategy_runtime_config` | Functions | Small deterministic checks/calculations or request packaging | `**kwargs → dict` | None | Numeric conversion may raise in some functions | Root facade/dynamic consumers unconfirmed | Not executed | **Possibly used** | **Useful** |
| Paper exports: `build_paper_trading_report`, `calculate_paper_slippage`, `close_paper_position`, `compare_paper_vs_backtest`, `modify_paper_order`, `record_paper_fill`, `start_paper_strategy`, `stop_paper_strategy`, `submit_paper_order` | Functions | Package paper request | `**kwargs → dict` | None in current function | Envelope helper errors | Root facade/dynamic consumers unconfirmed | Not executed | **Possibly used** | **Questionable** |
| Live exports: `build_live_execution_report`, `cancel_live_order`, `close_live_position`, `modify_live_order`, `pause_live_strategy`, `reconcile_broker_state`, `reduce_live_exposure`, `resume_live_strategy`, `submit_live_order`, `sync_live_positions` | Functions | Require presence of `approval_id`, then package live request | `**kwargs → dict` | None in current function | Envelope helper errors | Root facade/dynamic consumers unconfirmed | Not executed | **Possibly used** | **Questionable** |
| Kill-switch exports: `cancel_all_orders`, `check_kill_switch_conditions`, `clear_kill_switch_after_approval`, `close_all_positions`, `disable_new_orders`, `record_kill_switch_event`, `require_reenable_approval`, `trigger_global_kill_switch`, `trigger_strategy_kill_switch`, `trigger_symbol_kill_switch` | Functions | Require presence of `approval_id`, then package safety request | `**kwargs → dict` | None in current function | Envelope helper errors | Root facade/dynamic consumers unconfirmed | Not executed | **Possibly used** | **Questionable** |
| `Trade`, `TradeResult` | Imported classes | Compatibility trading implementation | class APIs | Broker mutation/read | Provider errors | Direct submodule callers; not in `__all__` | Not executed | **Used through submodule** | **Essential/Supporting** |

**Confirmed export defect:** `Trade` and `TradeResult` are imported into the package namespace but omitted from `__all__`. Conversely, the intent, send, receipt, metadata, authority, and attempt services are not imported at all.

### `_common.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `execution_approval_module()` | Function | Import approval package | none → module | Import/cache mutation | Import errors | Dynamic consumers | Not executed | **Possibly used** | **Supporting** |
| `execution_live_module()` | Function | Import live package | none → module | Import/cache mutation | Import errors | Dynamic consumers | Not executed | **Possibly used** | **Supporting** |
| `execution_monitoring_module()` | Function | Import nonexistent `execution.monitoring` | none → module | Import attempt | `ModuleNotFoundError` | No caller confirmed | Not executed | **Unused/defective** | **No demonstrated value** |
| `execution_performance_module()` | Function | Import nonexistent `execution.performance` | none → module | Import attempt | `ModuleNotFoundError` | No caller confirmed | Not executed | **Unused/defective** | **No demonstrated value** |
| `execution_reconciliation_module()` | Function | Import reconciliation package | none → module | Import/cache mutation | Import errors | Dynamic consumers | Not executed | **Possibly used** | **Supporting** |
| `execution_trade_governor_module()` | Function | Import governor module | none → module | Import attempt | Expected package-root import failure | No confirmed successful caller | Not executed | **Broken** | **Questionable** |
| `execution_tool_result(...)` | Function | Build standard tool envelope | fields → dict | None | Downstream standardizer errors | All root wrappers | Not executed | **Used internally** | **Supporting** |
| `execution_tool_context(kwargs)` | Function | Extract request context | dict → dict | None | None expected | Wrapper functions | Not executed | **Used internally** | **Supporting** |
| `package_execution_request(name, kwargs, critical=False)` | Function | Presence-check approval for critical request and package it | name/payload → dict | None | Envelope errors | 42 wrapper functions | Not executed | **Used internally** | **Supporting but weak gate** |
| `__getattr__(name)` | Dynamic resolver | Search execution modules for attribute | name → object | Imports/cache mutation | `AttributeError`, nested import errors | Dynamic `_common` consumers only | Not executed | **Possibly used** | **Questionable** |

### `readiness_tools.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `validate_order_request(**kwargs)` | Function | Validate required fields, side, and positive volume | kwargs → envelope | None | `ValueError`/`TypeError` during float conversion | `build_execution_plan`; facade consumers | Not executed | **Used internally / possibly external** | **Useful** |
| `validate_execution_environment(**kwargs)` | Function | Allow `test`, `paper`, `live` | kwargs → envelope | None | None expected | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `validate_order_size`, `validate_order_price` | Functions | Positive numeric check | kwargs → envelope | None | Numeric conversion errors | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `validate_stop_loss_take_profit` | Function | Directional SL/TP geometry | kwargs → envelope | None | Numeric conversion errors | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `estimate_transaction_cost` | Function | Sum spread, commission, slippage | kwargs → envelope | None | Numeric conversion errors | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `estimate_slippage` | Function | Heuristic spread/volatility estimate | kwargs → envelope | None | Numeric conversion errors | Facade consumers | Not executed | **Possibly used** | **Questionable** |
| `build_execution_plan` | Function | Return selected order fields after basic validation | kwargs → envelope | None | Nested validation conversion errors | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `run_execution_readiness_check` | Function | Fail if any supplied check has false `passed` | checks → envelope | None | Malformed check errors | Facade consumers | Not executed | **Possibly used** | **Useful** |
| `validate_strategy_runtime_config`, `validate_broker_symbol_mapping` | Functions | Package request only | kwargs → envelope | None | Envelope errors | Facade consumers | Not executed | **Possibly used** | **Questionable** |

### Deterministic execution core

| File / Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Confirmed caller | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|
| `assembler.py::ExecutionIntentAssemblyConfig` | Dataclass | Default action/order-type assembly settings | fields → config | None | None | assembler | **Used internally** | **Supporting** |
| `assemble_execution_intent(...)` | Function | Verify proposal/decision alignment and build intent | proposal, risk decision, key, config → contract | None | `ValueError` for mismatch/ineligible decision | governor source | **Disconnected** | **Useful** |
| `generate_execution_idempotency_key(...)` | Function | Hash stable execution shape | proposal, decision, action, order type → string | None | serialization errors | governor source | **Disconnected** | **Useful** |
| `SymbolMetadataCacheEntry` | Model | Symbol trade metadata and freshness timestamp | fields → model | None | Pydantic validation errors | cache/governor | **Used internally** | **Supporting** |
| `SymbolMetadataCache.put/get/get_many` | Methods | Mutate/read in-memory metadata | metadata keys → entry/list | Local state mutation/read | Key/type errors | pre-send/governor | **Used internally** | **Supporting** |
| `ReadinessCheckResult`, `ReadinessAggregateResult` | Dataclasses | Represent individual and aggregate checks | fields → records | None | None | readiness/pre-send | **Used internally** | **Supporting** |
| `validate_market_open` | Function | Block closed market | boolean/context → result | Read-only | None expected | pre-send | **Used internally** | **Supporting** |
| `validate_symbol_tradability` | Function | Block disabled symbol | metadata → result | Read-only | attribute/type errors | pre-send | **Used internally** | **Supporting** |
| `validate_price_freshness` | Function | Block stale price | timestamp/threshold → result | Reads current clock | datetime errors | pre-send | **Used internally** | **Supporting** |
| `validate_stop_and_freeze_levels` | Function | Validate distances against metadata | request/metadata → result | Read-only | numeric/type errors | pre-send | **Used internally** | **Supporting** |
| `validate_fill_mode_compatibility` | Function | Validate requested fill mode | request/metadata → result | Read-only | malformed metadata errors | pre-send | **Used internally** | **Supporting** |
| `validate_terminal_connectivity` | Function | Fail if terminal disconnected | bool → result | Read-only | None expected | pre-send | **Used internally** | **Supporting** |
| `validate_risk_decision_for_execution` | Function | Delegate risk-decision freshness/validity | decision/time → result | Read-only | risk-module import/validation errors | pre-send | **Used internally** | **Essential support** |
| `aggregate_readiness_results` | Function | Fail closed if any check fails | list → aggregate | None | None expected | pre-send | **Used internally** | **Supporting** |
| `PreSendValidationRequest` | Dataclass/model | Collect pre-send data | fields → request | None | construction errors | governor | **Disconnected** | **Supporting** |
| `run_pre_send_validation(...)` | Function | Fetch metadata and run all checks | request/cache/decision → aggregate | Read-only/logging | `LookupError` when metadata absent; nested errors | governor source | **Disconnected** | **Useful** |
| `BrokerSendGateway` | Protocol | Define mutating gateway methods | request → provider result | Broker mutation contract | implementation-specific | send service | **Used internally** | **Essential boundary** |
| `ExecutionSendService.send(intent)` | Method | Convert intent to request and dispatch action | intent → `BrokerSendResult` | Broker mutation/external API through gateway | `ValueError` unsupported action; provider errors | governor source | **Disconnected from current route** | **Essential if connected** |
| `ExecutionAttemptPersistenceService.persist_attempt(...)` | Method | Increment attempt number and persist hash/status | intent id/payload/status → record | Persistence write | repository/serialization errors | governor source | **Disconnected** | **Useful** |
| `normalize_broker_response(response)` | Function | Normalize dict/dataclass/object response | any → dict | None | conversion errors | receipt service | **Used internally** | **Supporting** |
| `ExecutionReceiptService.persist_receipt(...)` | Method | Normalize and persist receipt | intent id/response → receipt | Persistence write | repository/normalization errors | governor source | **Disconnected** | **Useful** |
| `propagate_authority_state(...)` | Function | Resolve authority badge | receipt/reconciliation states → view | None | None expected | governor source | **Disconnected** | **Supporting** |

### Approval package

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
|---|---|---|---|---|---|---|---|
| `ApprovalState` | Enum | Pending/partial/approved/rejected/expired states | enum values | None | invalid enum value | **Used internally** | **Supporting** |
| `RiskClass` | Enum | A–E risk classification | enum values | None | invalid enum value | **Used internally** | **Supporting** |
| `ApprovalPacket.is_complete`, `missing_fields` | Methods | Validate minimum packet fields | packet → bool/list | None | None expected | **No confirmed external caller** | **Useful** |
| `ApprovalRequest` | Dataclass | Represent approval record | fields → object | None | None | **No confirmed caller** | **Supporting** |
| `ApprovalPacketBuilder` fluent methods and `build`, `from_dict` | Methods | Construct packet | values/dict → builder/packet | Local builder mutation | `ValueError` for invalid risk class; type errors | **No confirmed production caller** | **Useful** |
| `ApprovalCreateRequest` | Dataclass | Creation command | fields → object | None | None | **Service input** | **Supporting** |
| `ApprovalCreationService.create` | Method | Validate and persist approval | request → DB record | Persistence write | `ValidationError`, repository errors | **Possibly used** | **Useful** |
| `ApprovalVoteRequest` | Dataclass | Vote command | fields → object | None | None | **Service input** | **Supporting** |
| `ApprovalVoteService.vote` | Method | Reject duplicate voter, persist vote, refresh state | request → DB vote | Persistence write/read | `ValidationError`, SQLite/repository errors | **Possibly used** | **Useful** |
| `APPROVAL_TRANSITIONS` | Constant | Allowed state transitions | state → target set | Mutable module dictionary | N/A | **State machine** | **Supporting** |
| `ApprovalStateMachine.validate` | Method | Reject forbidden transition | from/to → None | None | `PolicyError` | **No confirmed production caller** | **Useful** |
| `OverrideRequestDraft` | Dataclass | Override request data | fields → object | None | None | **No confirmed caller** | **Questionable** |
| `OverrideRequestService.validate` | Method | Require reason code/rationale | draft → draft | None | `ValidationError` | **No confirmed caller** | **Questionable** |

### Reconciliation package

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
|---|---|---|---|---|---|---|---|
| `BrokerTruthSnapshot` | Dataclass | Broker order/position evidence | fields → record | None | None | **Internal** | **Supporting** |
| `BrokerTruthFetcher` public fetch methods | Class/methods | Query broker using IDs/reference data | local refs → snapshot | External API read | provider errors | **No confirmed production caller** | **Useful** |
| `LocalExecutionTruth` | Dataclass | Local intent/receipt evidence | fields → record | None | None | **Internal** | **Supporting** |
| `ReconciliationResultState` | Enum | `MATCHED`, `ABSENT`, `CONFLICTING` | enum values | None | invalid enum | **Internal** | **Supporting** |
| `ReconciliationComparison` | Dataclass | Comparison result | fields → record | None | None | **Internal** | **Supporting** |
| `build_local_execution_truth` | Function | Convert DB records to local truth | intent, receipt → record | Read-only | `JSONDecodeError` on plain authority state | **No confirmed production caller** | **Defective** |
| `compare_execution_truth` | Function | Classify broker/local state | local/broker truth → comparison | Read-only | malformed data errors | **No confirmed production caller** | **Useful** |
| `ReconciliationPersistenceService` public methods | Class/methods | Persist run and comparison | comparison/context → records | Persistence write | repository errors | **No confirmed caller** | **Useful** |
| `ReconciliationIncidentService` public methods | Class/methods | Create incident for conflict | comparison/context → incident | Persistence write | repository errors | **No confirmed caller** | **Useful** |
| `RetryGuardDecision` | Dataclass | Retry allow/block decision | fields → record | None | None | **Internal** | **Supporting** |
| `evaluate_retry_guard` | Function | Decide if retry risks duplicate execution | local/broker/comparison → decision | Read-only | malformed state errors | **No confirmed caller** | **Useful** |
| `DEFAULT_IN_FLIGHT_EXECUTION_STATUSES` | Constant | Startup query status set | N/A | None | N/A | **Startup loader** | **Supporting** |
| `ReconciliationStartupLoader` public methods | Class/methods | Load in-flight intents and truth | repository → records | Persistence reads | repository errors | **No confirmed production caller** | **Useful** |

### `trade_action_governor.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|
| `GovernorApprovalState` | Dataclass | Approval eligibility snapshot | fields → record | None | None | governor internals | **Internal only** | **Supporting** |
| `GovernedPaperExecutionResult` | Dataclass | End-to-end paper execution result | fields → record | None | None | intended API consumer | **Disconnected** | **Supporting** |
| `TradeActionGovernor.__init__` | Method | Construct six repositories, conversation service, gateway | DB path/gateway → instance | DB object creation | import/repository errors | No current route caller | **Broken import boundary** | **Questionable** |
| `execute_paper_action_draft` | Method | Approval → kill switch → workflow/proposal/risk/readiness → intent/send/attempt/receipt/status | user/draft/terminal flag → result | Multiple persistence writes; broker/paper mutation | `ValueError`, `PermissionError`, DB/provider errors | No current route caller | **Broken/disconnected** | **Potentially essential, no current value** |

### `trading.py` and `core.py`

**File responsibility:** compatibility execution and simulation surfaces.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|
| `TradeResult` | Dataclass | Normalize last broker result | fields → object/dict access | None | conversion errors | `Trade` | **Used internally** | **Supporting** |
| `Trade` configuration methods: `SetExpertMagicNumber`, `LogLevel`, `SetDeviationInPoints`, `SetTypeFilling`, `SetTypeFillingBySymbol`, `SetTypeTime`, `SetAsyncMode`, `SetMarginMode` | Methods | Mutate request defaults/compatibility settings | scalar values → bool/None | Local state mutation; some provider reads | provider errors | live engine/executor | **Used** | **Useful, with no-op methods** |
| `Trade` result methods: `Result*` family | Methods | Read normalized result values | none → scalar/text | Read-only | conversion errors | live trade executor | **Used** | **Supporting** |
| `Trade` order methods: buy/sell/pending/open/modify/close/delete families | Methods | Build MT5 request and call `order_send` | order values → bool | External API call; broker mutation | provider errors; many failures normalized to false | live engine/executor/session | **Used** | **Essential** |
| Flat lifecycle: `trading_connect`, `trading_disconnect`, `trading_is_connected` | Functions | Manage module-level broker connection | credentials/API → bool | External API call/global state mutation | provider errors | No confirmed runtime caller | **Possibly used** | **Useful** |
| Flat mutation: `trading_place_order`, `place_market_order`, `place_pending_order`, `modify_position`, `modify_pending_order`, `close_position`, `cancel_pending_order` | Functions | Broker order operations | request fields → result | Broker mutation/external API | provider/validation errors | No confirmed caller outside file | **Possibly used** | **Questionable due overlap** |
| Flat reads/calculations: `trading_position_info`, `trading_order_info`, `trading_history_order_info`, `trading_symbol_info`, `trading_terminal_info`, `trading_order_calc_margin`, `trading_order_calc_profit`, `trading_deal_history`, `trading_account_info` | Functions | Query provider state or calculate values | filters → provider result | External API read | provider errors | No confirmed caller outside file | **Possibly used** | **Useful but overlapping** |
| `core.py` info wrappers: `TerminalInfo`, `DealInfo`, `PositionInfo`, `OrderInfo`, `HistoryOrderInfo`, `SymbolInfo` | Classes | MQL5-like property access over simulation data | state/object → properties | Read-only | missing-field/type errors | core functions/simulator callers unconfirmed | **Possibly used** | **Supporting** |
| `TradeRecord`, `TradeTracker`, `CloseType`, `ExitReason`, `BacktestResult`, `EquityPoint`, `RunResult`, `SimulatorState` | Types/classes | Hold simulation execution state/results | fields → records | Local state mutation in tracker/state | type/state errors | no confirmed production caller | **Possibly used** | **Questionable in execution domain** |
| Query functions: `history_deals_get/total`, `positions_get/total`, `orders_get/total`, `history_orders_get/total`, `symbols_get/total`, `symbol_info` | Functions | Read in-memory simulated broker state | filters → collection/count/info | Read-only | malformed filter/state errors | core/simulation callers unconfirmed | **Possibly used** | **Supporting** |
| Monitor functions: `monitor_positions`, `monitor_pending_orders`, `monitor_account` | Functions | Advance simulated order/position/account state | state + market bar → mutations | Local state mutation | state/math errors | core execution loop unconfirmed | **Possibly used** | **Useful** |
| `core.order_send` | Function | Simulate broker request | request/state → result | Local state mutation | validation/state errors | no confirmed production caller | **Possibly used** | **Questionable due overlap** |

### `live/` public behaviour

| File / Symbol | Responsibility | Inputs → Return | Side effects | Raises/failure behaviour | Caller | Usage | Value |
|---|---|---|---|---|---|---|---|
| `live.__init__` lazy exports | Resolve `Config`, `StateManager`, `BarMonitor`, `SignalProcessor`, `PositionManager`, `TradeExecutor`, `LiveTradingNotifier`, `MultiStrategyEngine`, `StrategyInstance`, `LiveTradingSession`, `ExecutionEngineWrapper` | attribute → class | Import/cache mutation | import errors | FastAPI and internal consumers | **Used** | **Essential facade** |
| `BarMonitor.get_historical_data` | Fetch bars and initialize last closed bar | count → DataFrame/None | External broker read | catches broad exceptions and returns None | engine | **Used** | **Essential support** |
| `BarMonitor.check_new_bar`, closed-bar accessors | Detect new bar without using forming bar | none → bool/bar | External broker read; local timestamp mutation | broad exception fallback | engine | **Used** | **Essential support** |
| Config models/constants/functions | Parse TOML/JSON, overlays, schema, profiles, secrets | path/mapping/overrides → config | File reads; environment reads; optional secret-store read; audit write | `ConfigError`, secret/provider errors | runner/runtime | **Used/entry path** | **Useful** |
| `Dashboard`, `main` | Read status JSON and display terminal dashboard | status path → display loop | File reads, console output | file/JSON errors handled | operator script | **Script/operational** | **Useful** |
| `StrategyInstance` | Hold per-strategy live components | fields → object | Local state | constructor errors | engine | **Used internally** | **Supporting** |
| `MultiStrategyEngine.initialize/start/stop/pause/resume/status methods` | Build broker/risk/strategy components and run loop | config/client → lifecycle/status | External API reads/mutations; threads/timing; file/log writes; notifications | broad runtime exceptions logged | session/runner | **Used** | **Essential** |
| `SignalType`, `Signal` | Standard signal values/payload | fields → model | None | Pydantic errors | live components | **Used internally** | **Supporting** |
| MT5 compatibility accessors | Read bid/ask/ticket/field values across dict/object forms | object → scalar | Read-only | conversion/default behaviour | position/executor | **Used internally** | **Supporting** |
| `LiveTradingNotifier` methods | Adapt engine events to notification service | event → provider call | External notification call | provider errors generally logged | engine | **Used internally** | **Useful** |
| `PositionManager.refresh_positions` | Query and magic-filter positions | none → None | External broker read; local cache mutation | catches broad exceptions | engine/executor | **Used** | **Essential support** |
| `PositionManager.get_positions_by_type`, `should_allow_entry`, `get_positions_to_close` | Filter cached positions and enforce count | criteria → list/bool | Read-only | invalid type returns empty | trade executor | **Used** | **Essential support** |
| `run.main` | Parse config and launch engine | CLI → process lifecycle | all live side effects | config/runtime errors | command line | **Entry point** | **Useful** |
| Secret functions | Parse and resolve `keyring://service/account` | string/provider → string | Optional external secret-store read | `SecretProviderError` | config | **Used internally** | **Supporting** |
| `ExecutionEngineWrapper.close_position` | Adapt async session call to `Trade.PositionClose` | ticket → bool | Broker mutation via thread executor | broad errors logged/false | session/API | **Used** | **Essential support** |
| `LiveTradingSession.start/stop/pause/resume/get_status` | API session lifecycle and DB status | session id/user/client → status | DB writes, engine lifecycle, broker calls | broad exceptions mapped/logged | FastAPI route | **Used** | **Essential** |
| `SignalProcessor.initialize/update_with_new_bar` | Maintain rolling bars and invoke strategy | DataFrame/Series → bool/signal | Local state mutation; strategy execution | catches broad exceptions | engine | **Used** | **Essential support** |
| `StateManager.is_enabled/is_paused/pause/resume/enable/disable/update_last_run/get_last_run/increment_trade_count/...` | File-backed external control and counters | values → state/scalars | File reads/writes, local lock/state mutation | catches file/JSON errors, prints | engine | **Used internally** | **Useful** |
| `TradeExecutor.execute_signal` | Dispatch entry/exit signal | dict → `(bool, message)` | Broker mutation | catches entry errors; retry failures returned | engine | **Used** | **Essential** |

---

## 6. Actual Workflows

### `V1-WF-EXECUTION-001` — Live Session Lifecycle

* **Scope:** Cross-domain
* **Trigger:** FastAPI live-session endpoint.
* **Input boundary:** Authenticated user, session ID, stored live-session/strategy configuration, MT5 client.
* **Functions and methods used:** route handler → `LiveTradingSession.start()` / `stop()` / `pause()` / `resume()` → `MultiStrategyEngine`.
* **Files involved:** `app/api/routes/live.py`, `live/session.py`, `live/engine.py`, `live/__init__.py`.
* **External dependencies:** FastAPI, database manager, MT5 client, strategy storage, risk live services.
* **Output boundary:** API response and live-session database status.
* **Failure behaviour:** Route maps missing/invalid state to HTTP errors; session and engine catch/log broad exceptions; partial initialization can leave external state uncertain.
* **Operational status:** **Working**, based on current import and call path; runtime not executed.
* **Evidence:** `app/api/routes/live.py` directly imports `LiveTradingSession`; active session instances are stored in the route module.

```text
HTTP live-session request
→ app.api.routes.live
→ LiveTradingSession
→ MultiStrategyEngine
→ broker/risk/strategy/live components
→ DB status + API response
```

### `V1-WF-EXECUTION-002` — Live Bar-to-Trade Loop

* **Scope:** Cross-domain
* **Trigger:** Running `MultiStrategyEngine` polling loop detects a newly opened bar.
* **Input boundary:** Closed market bars from MT5, strategy configuration, account/portfolio state.
* **Functions and methods used:** `BarMonitor.check_new_bar()` → closed-bar fetch → `SignalProcessor.update_with_new_bar()` → engine validation/safety → `TradeExecutor.execute_signal()` → `execution.trading.Trade`.
* **Files involved:** `live/engine.py`, `bar_monitor.py`, `signal_processor.py`, `position_manager.py`, `trade_executor.py`, `trading.py`, notification/state files.
* **External dependencies:** MT5 client, `app.services.strategy`, `app.services.risk.live`, strategy-permission checks, filesystem, notification service.
* **Output boundary:** Broker order/position mutation, cached position state, logs, notifications, JSON status.
* **Failure behaviour:** Many components catch broad exceptions, log, and continue/return false. Retry exists in `TradeExecutor`, but no execution-intent/attempt/receipt persistence is on this path.
* **Operational status:** **Working/Unverified**.
* **Evidence:** `live/engine.py` constructs `Trade(api=self.client)` and live components; `trade_executor.py` imports `app.services.execution.trading.Trade`.

```text
new closed bar
→ BarMonitor
→ SignalProcessor
→ engine safety/portfolio checks
→ TradeExecutor
→ execution.trading.Trade
→ MT5 order_send
→ local status/notification
```

### `V1-WF-EXECUTION-003` — Agent-Facing Execution Request Packaging

* **Scope:** Internal
* **Trigger:** Direct call to one of 53 root exports.
* **Input boundary:** Arbitrary keyword arguments plus optional request context.
* **Functions and methods used:** wrapper → `package_execution_request()` or lightweight validator → `execution_tool_result()` → `standard_tool_response()`.
* **Files involved:** `__init__.py`, wrapper module, `_common.py`, `app/services/utils/standard.py`.
* **External dependencies:** None for the current wrapper execution.
* **Output boundary:** Standard response dictionary.
* **Failure behaviour:** Critical functions block when `approval_id` is missing. A present but invalid approval ID passes. Requested “blocked”/“rejected” statuses are normalized to generic `error`.
* **Operational status:** **Working as packaging only; external caller unverified**.
* **Evidence:** All broker, paper, live, and kill-switch wrappers call the common packager; returned message explicitly states no live side effects are executed.

```text
agent/tool call
→ wrapper(**kwargs)
→ optional approval_id presence check
→ standard response
→ no broker/persistence action
```

### `V1-WF-EXECUTION-004` — Deterministic Pre-Send Readiness

* **Scope:** Internal
* **Trigger:** A caller supplies a `PreSendValidationRequest`, symbol cache, and risk decision.
* **Input boundary:** Order parameters, symbol metadata, terminal state, market/price timestamps, risk decision.
* **Functions and methods used:** `run_pre_send_validation()` → eight readiness functions → `aggregate_readiness_results()`.
* **Files involved:** `pre_send.py`, `readiness.py`, `metadata_cache.py`, risk validity module.
* **External dependencies:** Risk-governance validity logic; current clock.
* **Output boundary:** `ReadinessAggregateResult`.
* **Failure behaviour:** Missing symbol metadata raises `LookupError`; invalid/stale conditions return fail-closed results; nested type/import errors can propagate.
* **Operational status:** **Working in isolation; disconnected from confirmed live send path**.
* **Evidence:** Source call chain is complete, but the active live runtime does not invoke it.

```text
execution request + symbol cache + risk decision
→ run_pre_send_validation
→ market/symbol/price/stops/fill/terminal/risk checks
→ aggregate
→ allowed or blocked
```

### `V1-WF-EXECUTION-005` — Intended Governed AI-Chat Paper Execution

* **Scope:** Cross-domain
* **Trigger:** Intended call to `TradeActionGovernor.execute_paper_action_draft`.
* **Input boundary:** User ID, action-draft ID, database, optional paper/broker gateway.
* **Functions and methods used:** approval evaluation → kill-switch check → workflow/proposal/risk persistence → readiness → idempotency → intent assembly → send → attempt → receipt → status updates.
* **Files involved:** `trade_action_governor.py`, assembler, idempotency, pre-send/readiness/cache, send, attempts, receipts, authority; conversation/risk/governance/database packages.
* **External dependencies:** Multiple repositories, conversation service, risk kill switch, execution contracts.
* **Output boundary:** `GovernedPaperExecutionResult` plus multiple persisted records.
* **Failure behaviour:** A clean import is expected to fail because eight imported names are absent from `app.services.execution`. Even if imported by unusual module-order side effects, no current API route invokes the governor.
* **Operational status:** **Broken and disconnected**.
* **Evidence:** Governor imports from the root package; root `__init__.py` exposes only 53 wrappers and imports `Trade`/`TradeResult`. `standardize_domain_exports` is a no-op.

```text
intended AI-chat paper request
→ import TradeActionGovernor
→ root execution imports missing service names
→ import failure
→ no governed execution
```

### `V1-WF-EXECUTION-006` — Current AI-Chat “Paper Execute” Route

* **Scope:** Cross-domain
* **Trigger:** `POST /threads/{thread_id}/action-drafts/{draft_id}/paper-execute`.
* **Input boundary:** User, draft ID, `terminal_connected` flag.
* **Functions and methods used:** repository get/update only.
* **Files involved:** `app/api/routes/ai_chat.py`, conversation repository.
* **External dependencies:** Database.
* **Output boundary:** Updated action-draft response.
* **Failure behaviour:** HTTP 404/409 for missing draft, wrong type/status, or missing risk precheck.
* **Operational status:** **Working as a status update, not execution**.
* **Evidence:** The route never imports or calls the execution governor, send service, broker gateway, receipt service, or `Trade`.

```text
AI-chat paper-execute HTTP request
→ validate stored draft flags
→ set side_effect_status based on terminal_connected boolean
→ return updated row
→ no order, attempt, or receipt
```

### `V1-WF-EXECUTION-007` — Approval Creation and Voting

* **Scope:** Internal/cross-domain service
* **Trigger:** Direct service call with governance repository.
* **Input boundary:** Approval creation request or vote request.
* **Functions and methods used:** `ApprovalCreationService.create()`; `ApprovalVoteService.vote()`; repository methods; state refresh.
* **Files involved:** `approval/services.py`, `approval/models.py`, governance repository.
* **External dependencies:** SQLite repository.
* **Output boundary:** Approval/vote DB records and updated state.
* **Failure behaviour:** Validation errors for invalid count, missing expiry, duplicate voter, or absent approval; repository errors propagate.
* **Operational status:** **Working in isolation; runtime caller unverified**.
* **Evidence:** Complete persistence call chain exists.

```text
create approval
→ validate count/expiry
→ persist PENDING record
→ votes
→ reject / partial / approve state refresh
```

### `V1-WF-EXECUTION-008` — Broker Truth Reconciliation

* **Scope:** Internal/cross-domain
* **Trigger:** Intended startup, post-send, or retry reconciliation.
* **Input boundary:** In-flight intent, latest receipt, broker orders/positions.
* **Functions and methods used:** startup loader → local truth builder → broker truth fetcher → comparison → retry guard → persistence/incident service.
* **Files involved:** all `reconciliation/*` files plus execution repository.
* **External dependencies:** Broker read gateway and database.
* **Output boundary:** comparison, reconciliation run, possible incident/retry decision.
* **Failure behaviour:** `build_local_execution_truth()` calls `json.loads()` on `authoritative_state`; receipts are persisted with plain `PROVISIONAL`, causing likely `JSONDecodeError`. No confirmed live caller exists.
* **Operational status:** **Partial/Broken**.
* **Evidence:** Direct source mismatch between `receipts.py` and `reconciliation/comparison.py`.

```text
in-flight intent + receipt
→ build_local_execution_truth
→ json.loads("PROVISIONAL")
→ likely JSONDecodeError
→ no broker comparison
```

---

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `LiveTradingSession` | `app/api/routes/live.py` | Direct import, construction, lifecycle calls | Runtime | Route import and `active_sessions` mapping |
| `MultiStrategyEngine` | `live/session.py`, `live/run.py` | Direct construction/calls | Runtime/script | Session/runtime composition |
| `Trade` from `execution.trading` | `live/engine.py`, `live/position_manager.py`, `live/trade_executor.py`, `live/session.py` | Direct import/instantiation/method calls | Runtime | Current source imports |
| `BarMonitor` | `live/engine.py` | Construction/method calls | Runtime | Engine composition |
| `SignalProcessor` | `live/engine.py` | Construction/method calls | Runtime | Engine composition |
| `PositionManager` | `live/engine.py`, `live/trade_executor.py` | Construction/method calls | Runtime | Direct imports |
| `TradeExecutor` | `live/engine.py` | Construction/method calls | Runtime | Engine composition |
| `StateManager` | live engine/runtime | Construction/control calls | Runtime | live package composition |
| `LiveTradingNotifier` | live engine | Construction/event calls | Runtime | live package imports |
| live config functions/classes | `live/run.py`, engine setup | Direct calls | Script/runtime | package exports and runner |
| secret functions | `live/config.py` | Direct calls | Runtime config | Direct import |
| 53 root wrappers | root package facade | Import/export only; caller not confirmed | Unknown | `__all__`; standardizer no-op |
| readiness-tool validators | `build_execution_plan` and facade | Internal/direct | Unknown | source call |
| `package_execution_request` | broker/paper/live/kill wrapper modules | Direct function call | Internal | all wrapper sources |
| `run_pre_send_validation` and readiness functions | `trade_action_governor.py` | Direct call | Broken intended runtime | source call |
| `assemble_execution_intent` | `trade_action_governor.py` | Direct call | Broken intended runtime | source call |
| `generate_execution_idempotency_key` | `trade_action_governor.py` | Direct call | Broken intended runtime | source call |
| `ExecutionSendService` | `trade_action_governor.py` | Construction/call | Broken intended runtime | source call |
| `ExecutionAttemptPersistenceService` | `trade_action_governor.py` | Construction/call | Broken intended runtime | source call |
| `ExecutionReceiptService` | `trade_action_governor.py` | Construction/call | Broken intended runtime | source call |
| `propagate_authority_state` | `trade_action_governor.py` | Direct call | Broken intended runtime | source call |
| `TradeActionGovernor` | No current API route caller found | None confirmed | None | AI-chat route performs repository update directly |
| approval services | No confirmed route/runtime caller | Possible direct service usage | Unknown | exports and service source |
| reconciliation services | No confirmed live/runtime caller | None confirmed | Unknown | exports and internal coherence only |
| `core.py` compatibility surface | No confirmed production caller found | Possible dynamic/simulation use | Unknown | package discovery can scan modules |
| `execution_monitoring_module` | No caller; target missing | Dynamic import | None | direct 404 for target module |
| `execution_performance_module` | No caller; target missing | Dynamic import | None | direct 404 for target module |

---

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols/capabilities consumed | Where used | Evidence |
|---|---|---|---|
| `app.services.brokers.mt5` | MT5 client/API, bars, positions, orders, account/symbol reads, `order_send` | `trading.py`, `live/*`, route composition | direct imports/provider calls |
| `app.services.trading.permissions` | Strategy lifecycle permission checks | live engine and live route | direct imports |
| `app.services.risk.live` | Portfolio manager and safety checks | live engine | direct imports |
| `app.services.risk.governance.validity` | Risk-decision execution validity | `readiness.py` | dynamic/direct import in validator |
| `app.services.risk.safety.kill_switch` | New-entry blocking | governor | direct import |
| `app.services.governance.workflow` | `KillSwitchState` | governor | direct import |
| `app.services.conversation` | Action drafts and conversation service | governor | direct imports |
| `app.services.strategy` | Base strategy and stored strategy execution | live engine/signal processor | direct imports |
| `app.agentic.contracts` | Trade proposal, risk decision, execution intent, serialization | assembler/idempotency/send/governor | direct imports |
| `data.database` | Execution, approval, workflow, proposal, risk, chat repositories | attempts/receipts/approval/reconciliation/governor/live session | direct imports |
| `app.services.utils` | logging, errors, IDs, standard responses, security/redaction | almost all clusters | direct imports |
| Filesystem/environment/keyring | status, pause/resume, config, logs, secrets | live config/state/dashboard/engine | direct standard/optional dependency use |
| `pandas`, `pydantic` | market-bar frames and typed models | live/core/metadata | direct imports |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| `app.api.routes.live` | `LiveTradingSession` | Manage current live sessions | direct import |
| `app.services.execution.live` internal files | `execution.trading.Trade` | Execute live broker actions | direct imports |
| Operators/scripts | `live.run.main`, `Dashboard` | Start and monitor runtime | script entry points |
| Potential agent runtime | 53 root exports | Execution-related tool calls | package `__all__`; actual registry caller unconfirmed |
| Governor source | intent/readiness/send/receipt services | Intended governed paper path | direct imports, but root import defect |
| Tests associated with feature commits | core services and approval/reconciliation primitives | Unit verification | commit evidence; tests not production callers |

---

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `execution.trading.Trade` | `app/services/trading/trade.py::Trade` | MQL5-style order placement, modification, closure, result access | live engine imports execution version; trading-domain audit found parallel class | Divergent safety and behaviour |
| `ExecutionSendService` | `execution.trading.Trade` | Broker mutation dispatch | both convert internal requests to provider calls | Live path bypasses intent/receipt pipeline |
| `live.trade_executor.TradeExecutor` | `ExecutionSendService` | Action dispatch, retries, provider call | both sit immediately before broker mutation | Retry/persistence semantics differ |
| `core.order_send` | `Trade._send_request` | Execute broker-like request | in-memory versus provider-backed | Ambiguous simulation ownership |
| `core.py` simulation state | `app.services.simulation` | positions/orders/account/results over simulated bars | core contains backtest/run models and monitors | Execution domain owns unrelated simulation logic |
| Root `readiness_tools.py` | `readiness.py` + `pre_send.py` | Execution validation/readiness | lightweight envelopes versus typed metadata/risk checks | Two different meanings of “ready” |
| Root live wrappers | `live/` runtime | submit/modify/close/pause/resume/reconcile/report concepts | wrappers only package; runtime performs actual work | Names imply integration that does not exist |
| Root kill-switch wrappers | risk/governance kill-switch implementation | trigger/block/clear safety controls | wrappers only presence-check approval and package | False sense of enforcement |
| `paper_trading_tools.submit_paper_order` | `TradeActionGovernor` | Paper order intent | packager versus full persisted workflow | Neither is connected to current paper-execute route |
| `TradeActionGovernor` | AI-chat paper-execute route | Governed paper execution status | governor performs full chain; route only flips fields | UI/API can claim execution without execution record |
| `ApprovalVoteService` state refresh | `ApprovalStateMachine` | Approval transitions | service computes states directly and does not call state machine | Transition rules can drift |
| `authority.propagate_authority_state` | reconciliation result state | Authority presentation | separate string conventions | Inconsistent state values and parsing |
| `PositionManager.trade` | engine/executor `Trade` instances | Broker mutation object ownership | multiple `Trade` instances can be created | Inconsistent magic/config/result state |

---

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `execution_monitoring_module()` | Targets missing `app.services.execution.monitoring` | direct file lookup; accessor inspection | **High** | target file returned not found |
| `execution_performance_module()` | Targets missing `app.services.execution.performance` | direct file lookup; accessor inspection | **High** | target file returned not found |
| `TradeActionGovernor` | Intended workflow has no current API caller and imports missing root names | root export inspection; governor import inspection; AI-chat route inspection | **High** for import/caller defect | package root lacks imported symbols; route only updates DB |
| 42 broker/paper/live/kill request wrappers | No confirmed runtime caller; add no domain action beyond packaging | package exports; helper inspection; available caller searches | **Medium** | all call common packager |
| Approval ID “gate” | Presence check only, despite security-sensitive names | wrapper and `_common` inspection | **High** | `if critical and not kwargs.get("approval_id")` |
| `ApprovalPacketBuilder` | Useful constructor but no confirmed production caller | exports/import searches available | **Medium** | package export only |
| `OverrideRequestService` | Validates two fields but has no persistence or confirmed caller | source/caller search | **Medium** | file describes later persistence wiring |
| `ApprovalStateMachine` | Not used by vote service that changes approval states | source call-path comparison | **High** for non-use in service | `ApprovalVoteService` computes next state directly |
| reconciliation package | Coherent but no confirmed live startup/send integration | live engine/session and governor inspection | **Medium** | no call from active live path |
| `core.py` | Large simulation/broker compatibility implementation without confirmed production caller | package/import/caller searches | **Medium** | no active route/engine import found |
| Flat functions in `trading.py` | Overlap with `Trade`; no confirmed caller outside file | live imports target class; available searches | **Medium** | class is active path |
| `Trade.SetAsyncMode` | Compatibility no-op | direct source inspection | **High** | method does not enable async execution |
| `Trade.SetMarginMode` | Compatibility method always reports success | direct source inspection | **High** | no meaningful enforcement |
| Root standardization call | Suggests registration, but standardizer only logs | root and utils source inspection | **High** | `standardize_domain_exports` is a placeholder |
| `StateManager` exception handling | Broad catch includes `Exception` together with `JSONDecodeError`; uses `print` | direct source | **High** | state file errors are swallowed |
| `LiveTradingSession` closed-position count | Reported as fixed/unfinished value | session source inspection | **High** | TODO/default zero path |
| Agent tool status metadata | Several supplied context fields are ignored | `_common.execution_tool_result` inspection | **High** | warnings, side effects, environment, agent name discarded |

No item is labelled dead code unless a missing target is directly confirmed. All “no caller found” production conclusions remain Medium confidence.

---

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Governed paper execution | Root facade does not export governor dependencies | Governor import fails before execution | `trade_action_governor.py` imports vs root `__init__.py` |
| AI-chat paper execute | Route does not call governor or broker | `paper_executed` can mean only a DB flag update | `app/api/routes/ai_chat.py::execute_paper_action_draft` |
| Live governance | Active live engine does not use assembler/readiness/send/receipt/reconciliation chain | Live orders lack the newer persisted governance path | engine/trade executor imports |
| Agent live wrappers | No downstream dispatcher connects packaged request to runtime | Tool call cannot place/modify/close trade | wrapper/common source |
| Kill-switch wrappers | No validation or downstream enforcement | Critical-looking calls only return a dict | common packager |
| Approval state machine | Vote service bypasses it | Transition policy is duplicated and may diverge | approval services/state machine |
| Reconciliation local truth | Authority state storage format mismatches parser | Reconciliation may fail before comparison | receipts vs comparison |
| Startup reconciliation | Loader not called by current live engine/session | In-flight intents are not confirmed before live start through this package | no call in active path |
| Send-attempt persistence | Count-then-insert attempt number is not atomic at service level | Concurrent sends can choose same attempt number | `attempts.py::persist_attempt` |
| Receipt status | Successful `accepted` response is logged as non-success | Misleading operations telemetry | normalizer + receipt service |
| Live result persistence | Current `Trade` path does not create execution intent, attempt, or receipt records | Broker truth and local governance records can diverge | live executor path |
| Monitoring/performance module access | Accessors target absent modules | Dynamic consumers fail | `_common.py` and missing files |
| State/status truth | File state, DB session state, engine memory, and broker state are separate | Operator view may not be authoritative | live state/session/engine/dashboard |
| Simulation core ownership | Core is isolated from canonical simulation service | Valuable logic may be unreachable or duplicated | `core.py` versus simulation package |

---

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-EXECUTION-001` | Root facade exports wrappers but not real execution services | `app/services/execution/__init__.py` | Intended consumers cannot import assembler/send/receipt services from documented root | `__all__` and imports |
| `V1-ISSUE-EXECUTION-002` | Governor imports unavailable root symbols | `trade_action_governor.py:37-47` | Clean import and governed paper workflow fail | root lacks eight names |
| `V1-ISSUE-EXECUTION-003` | Export standardizer is a no-op | `utils/standard.py::standardize_domain_exports` | Missing exports/registration are not repaired dynamically | placeholder implementation |
| `V1-ISSUE-EXECUTION-004` | Agent tools imply side effects they never perform | broker/paper/live/kill wrapper files | Callers can mistake packaged intent for executed action | common return message |
| `V1-ISSUE-EXECUTION-005` | Critical approval gate validates only presence | `_common.package_execution_request` | Any nonempty approval ID passes wrapper gate | direct condition |
| `V1-ISSUE-EXECUTION-006` | Current AI-chat paper route records execution without executing | `app/api/routes/ai_chat.py::execute_paper_action_draft` | False execution status and no receipt/attempt | route code |
| `V1-ISSUE-EXECUTION-007` | Active live path bypasses governed send pipeline | `live/engine.py`, `live/trade_executor.py` | No intent/readiness/attempt/receipt/reconciliation guarantees | direct `Trade` usage |
| `V1-ISSUE-EXECUTION-008` | Multiple competing broker mutation paths | `trading.py`, `send_service.py`, `live/trade_executor.py`, `core.py`, trading domain | Behavioural drift and ambiguous ownership | overlapping methods |
| `V1-ISSUE-EXECUTION-009` | Receipt authority format mismatch | `receipts.py`, `reconciliation/comparison.py` | Likely `JSONDecodeError` during reconciliation | plain string write vs `json.loads` |
| `V1-ISSUE-EXECUTION-010` | Receipt success-state conventions conflict | `normalization.py`, `receipts.py`, governor | Accepted orders generate warning and mixed state checks | lowercase normalization then uppercase handling |
| `V1-ISSUE-EXECUTION-011` | Attempt numbering has service-level race | `attempts.py::persist_attempt` | Concurrent attempts can duplicate sequence number | list length then insert |
| `V1-ISSUE-EXECUTION-012` | Approval transition logic duplicated | `approval/services.py`, `approval/state_machine.py` | Rules can diverge; state machine provides no current guarantee | vote service does not call validator |
| `V1-ISSUE-EXECUTION-013` | Missing monitoring/performance modules remain in public helper surface | `_common.py` | Dynamic runtime failures | confirmed missing targets |
| `V1-ISSUE-EXECUTION-014` | `core.py` mixes simulation, broker facade, monitoring, accounting, and result models | `core.py` | Hard to identify ownership and actual callers | broad symbol set |
| `V1-ISSUE-EXECUTION-015` | `trading.py` is an oversized provider-coupled compatibility layer | `trading.py::Trade` and flat functions | Safety, provider, result, state, and convenience behaviour are coupled | file/class surface |
| `V1-ISSUE-EXECUTION-016` | Duplicate trading implementation exists in another domain | execution `trading.py` and `app/services/trading/trade.py` | Different live callers can use different guarantees | current live imports execution version |
| `V1-ISSUE-EXECUTION-017` | Broad exception swallowing is common in live runtime | bar monitor, signal processor, position manager, session, state manager | Failures can appear as None/False/empty state and allow loop continuation | direct source |
| `V1-ISSUE-EXECUTION-018` | Tool result helper discards declared metadata | `_common.execution_tool_result` | Warnings, actual side effects, approval mode, agent, and environment are not represented | ignored parameter tuple |
| `V1-ISSUE-EXECUTION-019` | “Blocked” and “rejected” collapse to generic error | `_common.execution_tool_result` | Consumers lose policy-state semantics | normalized status logic |
| `V1-ISSUE-EXECUTION-020` | Live state has multiple authorities | DB, JSON state, status JSON, engine memory, broker | Pause/status/position truth can diverge | session/state/engine/dashboard |
| `V1-ISSUE-EXECUTION-021` | Live retry path lacks idempotency/attempt persistence | `live/trade_executor.py` | Retried transient errors can create unknown duplicate outcomes | direct retries around `Trade` |
| `V1-ISSUE-EXECUTION-022` | Position manager creates its own `Trade` instance | `live/position_manager.py` | Request defaults and last-result state can differ from executor/engine instance | constructor source |
| `V1-ISSUE-EXECUTION-023` | Configuration contains security and runtime responsibilities together | `live/config.py` | Large mixed file and privileged audit behaviour are hard to verify | models, overlays, secrets, audit |
| `V1-ISSUE-EXECUTION-024` | Package public API and actual runtime API do not match | root wrappers versus direct `execution.live`/`execution.trading` imports | External callers cannot infer canonical execution path | route and package imports |

---

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-EXECUTION-001` | Live session lifecycle | `live/session.py`, `live/engine.py` | WF-001 | **Used** | **Essential** | Confirmed API caller |
| `V1-CAP-EXECUTION-002` | Live bar monitoring | `live/bar_monitor.py` | WF-002 | **Used** | **Essential support** | Uses closed bars |
| `V1-CAP-EXECUTION-003` | Live signal processing | `live/signal_processor.py` | WF-002 | **Used** | **Essential support** | Calls strategy directly |
| `V1-CAP-EXECUTION-004` | Live position tracking | `live/position_manager.py` | WF-002 | **Used** | **Essential support** | Magic-number filtered |
| `V1-CAP-EXECUTION-005` | Live broker order execution | `live/trade_executor.py`, `trading.py::Trade` | WF-002 | **Used** | **Essential** | Direct MT5-oriented path |
| `V1-CAP-EXECUTION-006` | Live runtime state/control | `live/state_manager.py`, session/engine | WF-001, WF-002 | **Used internally** | **Useful** | JSON + DB + memory |
| `V1-CAP-EXECUTION-007` | Live notification/status/dashboard | notifier, engine, dashboard | WF-001, WF-002 | **Used internally/script** | **Useful** | Non-authoritative operator surface |
| `V1-CAP-EXECUTION-008` | Live configuration/secrets | config/secrets/run | WF-001 | **Used/script** | **Useful** | TOML/JSON/env/keyring |
| `V1-CAP-EXECUTION-009` | Agent execution request packaging | root wrappers + `_common` | WF-003 | **Possibly used** | **Questionable** | No downstream action |
| `V1-CAP-EXECUTION-010` | Lightweight order validation/planning | `readiness_tools.py` | WF-003 | **Possibly used** | **Useful** | Independent of typed readiness |
| `V1-CAP-EXECUTION-011` | Typed pre-send readiness | `readiness.py`, `pre_send.py`, metadata cache | WF-004 | **Disconnected** | **Useful** | Not on live path |
| `V1-CAP-EXECUTION-012` | Execution intent assembly | `assembler.py` | WF-005 | **Disconnected** | **Useful** | Broken governor import |
| `V1-CAP-EXECUTION-013` | Stable idempotency fingerprint | `idempotency.py` | WF-005 | **Disconnected** | **Useful** | Not used by live retries |
| `V1-CAP-EXECUTION-014` | Broker gateway dispatch | `send_service.py` | WF-005 | **Disconnected** | **Essential if connected** | Protocol supports five actions |
| `V1-CAP-EXECUTION-015` | Send-attempt persistence | `attempts.py` | WF-005 | **Disconnected** | **Useful** | Race risk |
| `V1-CAP-EXECUTION-016` | Receipt normalization/persistence | normalization/receipts | WF-005 | **Disconnected** | **Useful** | State convention mismatch |
| `V1-CAP-EXECUTION-017` | Authority-state display | `authority.py` | WF-005, WF-008 | **Disconnected** | **Supporting** | String-based state |
| `V1-CAP-EXECUTION-018` | Approval creation/voting | `approval/services.py` | WF-007 | **Possibly used** | **Useful** | Direct repository services |
| `V1-CAP-EXECUTION-019` | Approval packet/state/override helpers | approval models/builder/state/override | WF-007 | **No confirmed caller** | **Questionable/Useful** | State machine bypassed |
| `V1-CAP-EXECUTION-020` | Broker/local reconciliation | `reconciliation/*` | WF-008 | **Disconnected/defective** | **Useful** | Authority parse defect |
| `V1-CAP-EXECUTION-021` | Governed AI-chat paper execution | `trade_action_governor.py` | WF-005 | **Broken** | **No current demonstrated value** | Intended comprehensive path |
| `V1-CAP-EXECUTION-022` | AI-chat paper status update | `app/api/routes/ai_chat.py` | WF-006 | **Used** | **Questionable** | No actual execution |
| `V1-CAP-EXECUTION-023` | MQL5 compatibility API | `trading.py` | WF-002 | **Used** | **Essential but duplicated** | Current live mutation layer |
| `V1-CAP-EXECUTION-024` | In-memory broker/simulation core | `core.py` | none confirmed | **Possibly used** | **Questionable** | Ownership overlap |
| `V1-CAP-EXECUTION-025` | Broker/account/symbol flat reads | `trading.py`, broker wrapper tools | none confirmed | **Possibly used** | **Useful/Questionable** | Multiple surfaces |
| `V1-CAP-EXECUTION-026` | Kill-switch request vocabulary | `kill_switch_tools.py` | WF-003 | **Possibly used** | **No demonstrated enforcement value** | Packaging only |

---

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* The active `LiveTradingSession` and `MultiStrategyEngine` call path provides real system value and has a confirmed API consumer.
* Closed-bar monitoring, rolling signal processing, position filtering, trade execution, state controls, and runtime notifications form a coherent live loop.
* The typed readiness functions are deterministic and fail closed at the result level.
* Execution-intent assembly, stable idempotency hashing, gateway dispatch, attempt records, receipt normalization, approval records, and reconciliation concepts provide concrete isolated value.
* The `BrokerSendGateway` protocol is a meaningful explicit mutation boundary.
* Approval creation and distinct-voter enforcement are substantive behaviours.
* Secret references and live configuration overlays provide operational value.
* The `Trade` class is currently essential because the live runtime calls it directly.

### Behaviour that exists but is disconnected

* The complete governed paper workflow.
* Typed pre-send readiness from the live engine.
* Execution-intent, attempt, and receipt persistence from actual live trades.
* Startup and post-send reconciliation.
* Retry guarding based on broker truth.
* Approval packet, transition-machine, and override helpers.
* Most root package wrappers.
* The in-memory simulation core.

### Likely dead weight or no demonstrated current value

These are not labelled definitive dead code because runtime search was incomplete:

* missing-module accessors for monitoring and performance are confirmed defective;
* request wrappers that only rename the same common packager;
* compatibility no-op methods;
* unused flat trading functions that duplicate the active `Trade` class;
* approval override skeleton without persistence/caller;
* an isolated simulation core inside execution;
* a governor that cannot import through its own chosen facade and is bypassed by the API route.

### Duplicated responsibilities

* Broker mutation exists in at least four execution-related paths.
* Two separate `Trade` implementations exist across domains.
* Two readiness systems exist.
* Paper execution exists as wrappers, a broken governor, and a non-executing API status route.
* Approval state progression exists in both a state machine and direct vote-service logic.
* Live pause/status/truth exists in database state, JSON state, engine memory, status JSON, and broker state.

### Important uncertainties

1. Whether deployed processes import additional execution services from external code.
2. Whether an agent/tool loader invokes the 53 root exports despite the no-op standardizer.
3. Whether package import order in a long-running process accidentally injects missing root attributes before the governor import.
4. Whether the current database schema stores authority state in a different serialized form than the service call suggests.
5. Whether any current tests patch the root package to make the governor import succeed.
6. Whether `core.py` is dynamically loaded through broker configuration.
7. Whether live MT5 retries can be guaranteed idempotent by the provider.
8. Whether multiple `Trade` instances intentionally share or isolate magic/filling/result state.
9. Whether filesystem-backed state is treated as control truth or merely a convenience surface.
10. Whether current deployment commands use `live/run.py` or only the FastAPI session route.

### Areas requiring manual confirmation

* Run a clean `python -c "import app.services.execution.trade_action_governor"` against the audited commit.
* Run the execution and live unit/integration tests and collect actual coverage.
* Trace the deployed agent tool registry and list registered execution callables.
* Inspect production/live logs for calls to root wrappers, governor, approval, and reconciliation services.
* Confirm the authoritative paper-execution endpoint and whether any order is expected.
* Confirm receipt and `authoritative_state` database values.
* Simulate concurrent send attempts to validate attempt numbering.
* Trace a live order from signal to broker and verify whether any execution-intent, attempt, receipt, or reconciliation row is written.
* Confirm current broker retry/idempotency guarantees.
* Confirm whether `core.py` is selected by configuration or only retained compatibility code.

### Final Validation

* Every identified current Python file under `app/services/execution` is represented: **Yes, 48 files reconstructed and represented.**
* Every root `__init__.py` export was checked: **Yes, 53 exports.**
* Additional imported-but-not-exported `Trade` and `TradeResult` were checked: **Yes.**
* Approval, reconciliation, and live package exports were checked: **Yes.**
* Public behaviour is represented at file level: **Yes; trivial compatibility aliases are grouped.**
* Callers were searched across available routes, internal imports, package registries, commit-associated tests, and prior current-ref audits: **Yes, within stated tooling limits.**
* Production usage is distinguished from test-only, dynamic, and intended usage: **Yes.**
* Inbound and outbound cross-domain usage is summarized: **Yes.**
* Workflows are based on actual source call paths: **Yes.**
* Uncertain findings are labelled: **Yes.**
* No Version 2 design or requirements were invented: **Yes.**
* No repository code was changed: **Yes.**

---

## Evidence Not Accessible

* A local checkout capable of executing imports or tests.
* A complete recursive current-ref directory response independent of package/import reconstruction.
* Reliable repository-wide indexed code search for every symbol and string-based reference.
* Current production logs, process commands, environment variables, broker traces, database contents, scheduler state, and agent registry state.
* A complete independently enumerated current test-file list and current test results.
* Uncommitted, ignored, local-only, or deployment-only source.
