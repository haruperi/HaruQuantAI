# Trading — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `trading`
* **Repository:** `haruperi/HaruQuant`
* **Repository snapshot inspected:** `main` as indexed at commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/trading`
* **Requested tests path:** `ttests\unit\app\services\trading`
* **Actual tests path found:** `tests/unit/app/services/trading`
* **Known usage/example path:** `tests/usage/app/services/07_trading.py`
* **Files inspected:** 20 Python files and 1 package README.
* **Related packages searched:** `app/api`, `app/services/execution`, `app/services/simulation`, `app/services/optimization`, `app/services/strategy`, `app/services/brokers`, `data/strategies`, `tests/unit`, `tests/usage`, and repository documentation references.
* **Search categories completed:** direct imports, qualified imports, class instantiation, method calls, inheritance, package exports, runtime route callers, strategy inheritance, simulation callbacks, tests, and usage examples.
* **Registration mechanisms checked:** `app/services/trading/__init__.py::__all__` and `standardize_domain_exports(...)`.
* **Excluded:** generated files, caches, environments, unrelated packages, and Version 2 requirements.
* **Audit limitations:**
  * The GitHub connector exposed file contents and indexed code search, but not an independent recursive tree listing. Package completeness was therefore established by reconciling `__init__.py`, the package README, internal imports, and repository-wide symbol/path searches.
  * The repository could not be cloned or executed in this environment. Test results, runtime configuration, broker connectivity, decorator side effects, and dynamic imports were not executed.
  * Dynamic discovery through `standardize_domain_exports(...)` could not be observed at runtime. Symbols with no static caller but exported through that mechanism are marked **Possibly used** or **Test-only**, not definitively dead.
  * No production logs, deployment manifests, scheduler state, or live broker traces were available.
  * The requested path begins with `ttests`; the repository evidence found `tests/unit/app/services/trading`.

## 2. Executive Summary

The Version 1 trading package contains **three distinct capability clusters**:

1. **Strategy runtime permission gating** — a production-used database-backed check that allows a strategy to run only when its lifecycle/governance state is permitted for backtest, optimization, paper, or live contexts.
2. **Stateful strategy contracts** — production-used dataclasses, type contracts, snapshots, and action objects consumed by the simulation engine and multiple stateful strategy implementations.
3. **Broker-facing trading gateway and MQL5-style facades** — account, terminal, symbol, order, position, deal, validation, readiness, idempotency, rate limiting, reconciliation, reporting, and a large `Trade` orchestrator.

The first two clusters have confirmed production/runtime callers. The third cluster is internally coherent enough to execute in mocked tests and the usage script, but **no indexed production caller imports this package's `Trade` class**. Live execution instead imports a separate `Trade` implementation from `app/services/execution/trading.py`. Consequently, most of the package's broker mutation and safety pipeline is currently **test/example-only in the available codebase**, even though it models important behaviour.

The most important structural findings are:

* Two separate trading implementations overlap substantially:
  * `app/services/trading/trade.py::Trade`
  * `app/services/execution/trading.py::Trade` plus flat trading functions.
* `OrderInfo` and `HistoryOrderInfo` duplicate almost all property access logic.
* `Trade` combines request construction, provider introspection, idempotency, locking, readiness, validation, rate limiting, timeout management, result normalization, local state persistence, reconciliation, kill-switch handling, and shutdown.
* Reconciliation is incomplete: stale pending orders are detected but not removed, mismatched records are reported but not corrected, and `is_reconciled` is set to `True` despite unresolved differences.
* A broker call that exceeds the five-second timeout may continue executing after the method returns an unknown-outcome failure; immediate reconciliation can occur before that late mutation completes.
* The package README references the old path `app/services/trader` and documents a test path that does not match the current package.
* `tests/unit/app/services/trading/test_trader_extra.py` targets obsolete/nonexistent names and suppresses every exception, so it provides almost no behavioural assurance.
* The usage script demonstrates a missing public partial-close operation by directly calling private `Trade._send_request(...)`, and it reads private `SymbolInfo._data`.

**Evidence trustworthiness:** High for file contents, static imports, package exports, and explicit call paths. Medium for “unused” conclusions because runtime dynamic export discovery and deployed configuration could not be executed.

```text
Module folders: 0 | Files: 21 | Public symbols: 39 top-level / 295 including public methods and members | Symbols with confirmed production callers: 11/39 (28%) | Workflows found: 6
```

## 3. Actual Package Structure

```text
app.services.trading
├── README.md
├── __init__.py
│   └── Package export gate: 38 names in __all__
├── permissions.py
│   ├── StrategyRuntimeContext
│   ├── StrategyPermissionError
│   ├── StrategyRuntimePermissionService
│   │   └── assert_strategy_allowed()
│   └── assert_strategy_allowed()
├── stateful.py
│   ├── TradeActionType
│   ├── TradeSide
│   ├── OrderType
│   ├── TimeInForce
│   ├── PositionType
│   │   ├── BUY
│   │   └── SELL
│   ├── PositionSnapshot
│   ├── OrderSnapshot
│   ├── TradeSnapshot
│   ├── StrategyRuntimeState
│   ├── StrategyContext
│   │   ├── positions_for_symbol()
│   │   └── orders_for_symbol()
│   ├── TradeAction
│   │   └── hold()
│   ├── StatefulStrategyProtocol
│   │   ├── on_event()
│   │   ├── on_order_update()
│   │   └── on_trade_update()
│   └── StatefulStrategyMixin
│       ├── requires_portfolio_state
│       ├── on_event()
│       ├── on_order_update()
│       └── on_trade_update()
├── store.py
│   ├── TradeStore
│   │   ├── get_idempotency_record()
│   │   ├── save_idempotency_record()
│   │   ├── get_order()
│   │   ├── save_order()
│   │   ├── get_orders()
│   │   ├── get_position()
│   │   ├── save_position()
│   │   ├── delete_position()
│   │   ├── get_positions()
│   │   ├── get_execution()
│   │   ├── save_execution()
│   │   └── get_executions()
│   ├── InMemoryTradeStore
│   │   └── Implements all TradeStore methods
│   └── get_default_store()
├── result.py
│   ├── NormalizedTradeResult
│   │   └── to_dict()
│   ├── BrokerResponseNormalizer
│   │   └── normalize_response()
│   └── ResultBuilder
│       ├── success()
│       └── failure()
├── concurrency.py
│   └── ConcurrencyQueue
│       ├── get_instance()
│       ├── lock()
│       └── lock_sync()
├── rate_limiter.py
│   ├── RateLimiter
│   │   ├── check_rate_limit()
│   │   ├── acquire()
│   │   └── get_status()
│   └── get_rate_limiter()
├── account_info.py
│   └── AccountInfo
│       └── MQL5-style account property methods
├── terminal_info.py
│   └── TerminalInfo
│       └── MQL5-style terminal property methods
├── symbol_info.py
│   └── SymbolInfo
│       └── Symbol selection, refresh, price and specification methods
├── position_info.py
│   └── PositionInfo
│       └── Position selection and property methods
├── order_info.py
│   └── OrderInfo
│       └── Active pending-order selection and property methods
├── history_order_info.py
│   └── HistoryOrderInfo
│       └── Historical-order selection and property methods
├── deal_info.py
│   └── DealInfo
│       └── Historical-deal selection and property methods
├── idempotency.py
│   └── IdempotencyService
│       ├── generate_key()
│       ├── check_duplicate()
│       ├── register_in_progress()
│       └── register_completed()
├── readiness.py
│   └── ReadinessService
│       └── run_execution_readiness_check()
├── validation.py
│   └── ValidationService
│       ├── normalize_precision()
│       ├── validate_volume()
│       ├── validate_price()
│       ├── validate_stops()
│       ├── validate_margin()
│       ├── validate_slippage()
│       ├── validate_dealing_mode_compatibility()
│       ├── validate_market_session()
│       └── validate_order_request()
├── reconciliation.py
│   └── ReconciliationService
│       ├── set_block_trading_on_startup()
│       └── reconcile()
├── reporting.py
│   └── ReportingService
│       └── build_report()
└── trade.py
    └── Trade
        ├── Configuration setters
        ├── Last-result accessors
        ├── buy() / sell()
        ├── buy_limit() / sell_limit()
        ├── buy_stop() / sell_stop()
        ├── position_open() / position_close() / position_modify()
        ├── order_modify() / order_delete()
        ├── set_kill_switch()
        └── shutdown()
```

### Package exports

`app/services/trading/__init__.py` exports 38 symbols:

```text
AccountInfo
BrokerResponseNormalizer
ConcurrencyQueue
DealInfo
HistoryOrderInfo
IdempotencyService
InMemoryTradeStore
NormalizedTradeResult
OrderInfo
OrderSnapshot
OrderType
PositionInfo
PositionSnapshot
PositionType
RateLimiter
ReadinessService
ReconciliationService
ReportingService
ResultBuilder
StatefulStrategyMixin
StatefulStrategyProtocol
StrategyContext
StrategyPermissionError
StrategyRuntimePermissionService
StrategyRuntimeState
SymbolInfo
TerminalInfo
TimeInForce
Trade
TradeAction
TradeActionType
TradeSide
TradeSnapshot
TradeStore
ValidationService
assert_strategy_allowed
get_default_store
get_rate_limiter
```

`StrategyRuntimeContext` is public in `permissions.py` but is not exported by the package gate.

`standardize_domain_exports(globals(), __all__, tool_category="trading")` is executed at package import. Its runtime registration effect could not be observed.

## 4. Module and File Inventory

Files are ordered by their actual dependency role rather than alphabetically.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| package | `README.md` | Describes intended guarded trading gateway | None | None | Documentation only; stale paths | Questionable |
| contracts | `stateful.py` | Defines state snapshots, strategy context, runtime state, and emitted trade actions | Snapshot dataclasses, `StrategyContext`, `TradeAction`, mixin/protocol | Standard library; required third-party: `pandas`; local: none | **Used** | **Essential** |
| persistence contract | `store.py` | Repository contract and process-local in-memory implementation | `TradeStore`, `InMemoryTradeStore`, `get_default_store` | Standard library; local logger | Test-only through the disconnected `Trade` pipeline | Supporting |
| result contract | `result.py` | Normalizes broker responses and builds failure results | `NormalizedTradeResult`, `BrokerResponseNormalizer`, `ResultBuilder` | Standard library; local logger | Test-only through `Trade` | Supporting |
| concurrency | `concurrency.py` | Per-account/per-symbol async and sync locks | `ConcurrencyQueue` | Standard library; local logger | Test-only through `Trade` | Supporting |
| throttling | `rate_limiter.py` | Per-provider token-bucket throttling | `RateLimiter`, `get_rate_limiter` | Standard library; local logger | Test-only through `Trade` and readiness tests | Supporting |
| broker read facade | `account_info.py` | Reads active account properties through broker router | `AccountInfo` | Standard library; local broker router, logger | Test-only in available callers | Questionable |
| broker read facade | `terminal_info.py` | Reads terminal connection/environment properties | `TerminalInfo` | Standard library; local broker router, logger | Test-only in available callers | Questionable |
| broker read facade | `symbol_info.py` | Reads symbol specifications/prices and performs market-data subscription selection | `SymbolInfo` | Standard library; local broker router, logger | Test/example-only in available callers | Questionable |
| broker read facade | `position_info.py` | Selects and exposes an open position | `PositionInfo` | Standard library; local broker router, logger | Test-only through `Trade`, validation, usage | Supporting |
| broker read facade | `order_info.py` | Selects and exposes an active pending order | `OrderInfo` | Standard library; local broker router, logger | Test-only through `Trade`, validation, usage | Supporting |
| broker read facade | `history_order_info.py` | Selects and exposes a historical order | `HistoryOrderInfo` | Standard library; local broker router, logger | Test/example-only | Questionable |
| broker read facade | `deal_info.py` | Selects and exposes a historical deal | `DealInfo` | Standard library; local broker router, logger | Test/example-only | Questionable |
| request safety | `idempotency.py` | Generates request fingerprints and stores in-progress/completed records | `IdempotencyService` | Standard library; local `TradeStore`, logger | Test-only through `Trade` | Supporting |
| request safety | `readiness.py` | Aggregates connection, terminal permission, account permission, and token availability checks | `ReadinessService` | Standard library; local account/terminal/rate-limiter/logger | Test-only through `Trade` | Supporting |
| request safety | `validation.py` | Normalizes and validates request volume, price, stops, slippage, margin, dealing mode, and market session | `ValidationService` | Standard library; local account/symbol/position/order wrappers, errors, logger | Test-only through `Trade` | Supporting |
| state consistency | `reconciliation.py` | Compares local store with broker position/order snapshots and partially synchronizes differences | `ReconciliationService` | Standard library; local `TradeStore`, logger | Test-only through `Trade` | Supporting |
| reporting | `reporting.py` | Builds summary from local store and optional reconciliation warnings | `ReportingService` | Standard library; local `TradeStore`, logger | **Test-only** | No demonstrated value |
| strategy governance | `permissions.py` | Enforces strategy lifecycle state by runtime context | Permission exception, service, convenience function | Standard library; local database manager, governance repository, logger | **Used** | **Essential** |
| execution orchestrator | `trade.py` | Builds and sends broker mutations with safety gates and local state tracking | `Trade` | Standard library; local broker router and nearly every trading support file | **Test-only** | Questionable |
| package gate | `__init__.py` | Re-exports 38 names and invokes domain export standardization | Entire package surface | Local utils standardization and all package modules | Possibly used dynamically; explicit production users import submodules | Supporting |

## 5. Public Behaviour Inventory

The tables below explicitly name every public method or member. Methods with identical read-through behaviour are grouped in one row, but every name is listed.

### `permissions.py`

**File responsibility:** Database-backed strategy lifecycle/governance admission.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `StrategyRuntimeContext` | Type alias | Restricts runtime context strings | Literal value | None | None | Type annotations | Indirect | Supporting only | Supporting |
| `StrategyPermissionError` | Exception | Signals a lifecycle state that is not allowed for the requested runtime | Message | None | N/A | `app/api/routes/live.py`; raised by service | `tests/unit/app/services/strategy/test_strategy_service.py` | **Used** | **Essential** |
| `StrategyRuntimePermissionService` | Class | Owns database and governance lookups | Optional injected database/repository → service | Read-only database access; object construction | Configuration/database exceptions | Module-level wrapper | Strategy service tests | **Used** | **Essential** |
| `StrategyRuntimePermissionService.assert_strategy_allowed(...)` | Method | Loads strategy, resolves governance identity/state, and checks allowed state set for context | `strategy_id`, `context` → `None` | Read-only database access; logging | `LookupError`, `StrategyPermissionError`, underlying DB errors | Module-level `assert_strategy_allowed` | Strategy service tests | **Used** | **Essential** |
| `assert_strategy_allowed(...)` | Function | Convenience entry point that constructs service and enforces permission | `strategy_id`, context, optional DB/repository → `None` | Read-only database access; logging | Same as service | Backtest route, optimization core, live route/engine, session service | Strategy service tests | **Used** | **Essential** |

### `stateful.py`

**File responsibility:** Provider-independent contracts shared by simulation and stateful strategies.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TradeActionType` | Type alias | Enumerates action tokens: OPEN, CLOSE, MODIFY_SL, MODIFY_TP, CANCEL_ORDER, HOLD | String literal | None | None | `TradeAction` annotations | Strategy tests | Supporting | Supporting |
| `TradeSide` | Type alias | BUY/SELL side contract | String literal | None | None | Snapshot/action annotations | Strategy tests | Supporting | Supporting |
| `OrderType` | Type alias | MARKET/LIMIT/STOP order contract | String literal | None | None | Snapshot/action annotations | Strategy tests | Supporting | Supporting |
| `TimeInForce` | Type alias | GTC/DAY/IOC/FOK contract | String literal | None | None | `TradeAction` annotation | Strategy tests | Supporting | Supporting |
| `PositionType` | `IntEnum` | Legacy numeric BUY/SELL values | `BUY=0`, `SELL=1` | None | None | Multiple baseline and stored strategies | Strategy tests | **Used** | Useful |
| `PositionSnapshot` | Dataclass | Immutable-style current position data supplied to a strategy | Ticket, symbol, side, volume, prices, P/L, metadata | Local state mutation during construction | Dataclass/type errors | Simulation engine; strategy helpers | Strategy tests | **Used** | **Essential** |
| `OrderSnapshot` | Dataclass | Current pending-order data supplied to a strategy | Ticket, symbol, side, type, volume, price, stops, state | Local state mutation during construction | Dataclass/type errors | Simulation engine | Strategy tests | **Used** | **Essential** |
| `TradeSnapshot` | Dataclass | Completed trade update supplied to strategy callbacks | Ticket, symbol, side, volume, prices, P/L, timestamps | Local state mutation during construction | Dataclass/type errors | Simulation engine | Strategy tests | **Used** | Useful |
| `StrategyRuntimeState` | Dataclass | Mutable strategy-specific state and last-seen event data | `values`, snapshots, metadata | Local state mutation | None documented | Simulation engine | Strategy tests | **Used** | **Essential** |
| `StrategyContext` | Dataclass | Per-event strategy input boundary | Symbol, current tick, portfolio snapshots, market data, runtime state, metadata | Local state mutation | None documented | Simulation engine, stateful helpers, baseline strategies | Strategy tests and usage | **Used** | **Essential** |
| `StrategyContext.positions_for_symbol(...)` | Method | Filters positions by supplied symbol or context symbol | Optional symbol → list | None | None | `stateful_common.positions_for_side` and strategies | Strategy tests | **Used** | Useful |
| `StrategyContext.orders_for_symbol(...)` | Method | Filters orders by supplied symbol or context symbol | Optional symbol → list | None | None | Available to strategies; no explicit external call found | Strategy tests | Possibly used | Useful |
| `TradeAction` | Dataclass | Describes a requested strategy action without executing it | Action, symbol, side, volume, order fields, identifiers, metadata | Local state mutation | Dataclass/type errors | Multiple baseline strategies; simulation engine | Strategy tests | **Used** | **Essential** |
| `TradeAction.hold(...)` | Class method | Creates a HOLD action with optional reason/strategy identity | Symbol and optional values → `TradeAction` | Local state mutation | None documented | No explicit caller found | Indirect | Unused, Medium confidence | Questionable |
| `StatefulStrategyProtocol` | Protocol | Structural typing contract for stateful strategies | `on_event`, update callbacks | None | N/A | No external reference found | Type-oriented tests only | Unused, High static confidence | Supporting |
| `StatefulStrategyProtocol.on_event(...)` | Protocol method | Declares event-to-actions contract | Context → action list | None | Implementer-defined | Structural typing only | Strategy tests | Possibly used | Supporting |
| `StatefulStrategyProtocol.on_order_update(...)` | Protocol method | Declares order update callback | Event → `None` | Implementer-defined | Implementer-defined | Structural typing only | Strategy tests | Possibly used | Supporting |
| `StatefulStrategyProtocol.on_trade_update(...)` | Protocol method | Declares trade update callback | Event → `None` | Implementer-defined | Implementer-defined | Structural typing only | Strategy tests | Possibly used | Supporting |
| `StatefulStrategyMixin` | Class | Supplies default no-op stateful callbacks and opt-in flag | Inherited by strategy classes | None by default | None | Multiple baseline strategies | Strategy tests | **Used** | **Essential** |
| `StatefulStrategyMixin.requires_portfolio_state` | Class constant | Signals simulation engine to use stateful slow path | Boolean `True` | None | None | `simulation/event_driven.py` | Strategy tests | **Used** | **Essential** |
| `StatefulStrategyMixin.on_event(...)` | Method | Default emits no actions | Context → empty list | None | None | Overridden by concrete strategies | Strategy tests | Supporting | Supporting |
| `StatefulStrategyMixin.on_order_update(...)` | Method | Default no-op order callback | Event → `None` | None | None | Simulation callback compatibility | Strategy tests | Supporting | Supporting |
| `StatefulStrategyMixin.on_trade_update(...)` | Method | Default no-op trade callback | Event → `None` | None | None | Simulation callback compatibility | Strategy tests | Supporting | Supporting |

### `store.py`

**File responsibility:** Local repository contract plus in-memory implementation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TradeStore` | Abstract class | Defines local idempotency/order/position/execution storage contract | Repository operations | Depends on implementation | `TypeError` if abstract | Idempotency, reconciliation, reporting, `Trade` | `test_trader.py` | Test-only | Supporting |
| `TradeStore.get_idempotency_record`, `get_order`, `get_orders`, `get_position`, `get_positions`, `get_execution`, `get_executions` | Abstract methods | Read repository records | Key/ticket or none → record/list | Read-only | Implementation-defined | Package services | Unit tests through implementation | Test-only | Supporting |
| `TradeStore.save_idempotency_record`, `save_order`, `save_position`, `save_execution`, `delete_position` | Abstract methods | Persist or delete local records | Record/ticket → `None` | Persistence write | Implementation-defined | Package services | Unit tests through implementation | Test-only | Supporting |
| `InMemoryTradeStore` | Class | Process-local dictionary implementation | None → store | Local state mutation; import-time singleton construction | None documented | `Trade`, tests | `test_trader.py` | Test-only | Supporting |
| `InMemoryTradeStore.get_idempotency_record(...)` | Method | Returns unexpired record and removes expired records | Key → record/`None` | Read-only or local deletion | None documented | `IdempotencyService` | Trade tests | Test-only | Supporting |
| `InMemoryTradeStore.save_idempotency_record(...)` | Method | Saves record with absolute expiry | Key, record, TTL → `None` | Local state mutation | None documented | `IdempotencyService` | Trade tests | Test-only | Supporting |
| `InMemoryTradeStore.get_order`, `get_orders`, `get_position`, `get_positions`, `get_execution`, `get_executions` | Methods | Return dictionary-backed records | Ticket/none → record/list | Read-only | None documented | Reconciliation/reporting | Trade tests | Test-only | Supporting |
| `InMemoryTradeStore.save_order`, `save_position`, `save_execution`, `delete_position` | Methods | Mutate dictionary-backed state | Ticket and record → `None` | Local state mutation | None documented | `Trade`, reconciliation | Trade tests | Test-only | Supporting |
| `get_default_store()` | Function | Returns import-time singleton store | None → `TradeStore` | Read-only after import | None documented | `Trade`, shutdown, tests | `test_trader.py` | Test-only | Supporting |

### `result.py`

**File responsibility:** Provider-agnostic result envelope.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `NormalizedTradeResult` | Class | Holds normalized result, fill and trace fields | Required broker fields plus optional fill/trace values | Local state mutation | Conversion errors occur before construction in normalizer | `Trade`, normalizer, builder | Trade tests | Test-only | Supporting |
| `NormalizedTradeResult.to_dict()` | Method | Serializes all fields | None → dictionary | None | None documented | Store/idempotency | Trade tests | Test-only | Supporting |
| `BrokerResponseNormalizer` | Class | Namespace for normalization | N/A | None | N/A | `Trade`, `ResultBuilder` | Trade tests | Test-only | Supporting |
| `BrokerResponseNormalizer.normalize_response(...)` | Static method | Reads dict/object fields, derives fill quantities, handles `None` | Provider, raw result → normalized result | Logging | Numeric conversion errors | `Trade`, `ResultBuilder.success` | Trade tests | Test-only | Supporting |
| `ResultBuilder` | Class | Namespace for success/failure builders | N/A | None | N/A | `Trade` | Trade tests | Test-only | Supporting |
| `ResultBuilder.success(...)` | Static method | Delegates successful raw result normalization | Provider, raw result → normalized result | Logging via normalizer | Conversion errors | `Trade._send_request` | Trade tests | Test-only | Supporting |
| `ResultBuilder.failure(...)` | Static method | Creates failure envelope without raising | Comment, retcode → normalized result | Local state mutation | None documented | `Trade` gates/errors | Trade tests | Test-only | Supporting |

### `concurrency.py`

**File responsibility:** Serialize requests by account and symbol.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ConcurrencyQueue` | Singleton class | Owns async and sync lock maps | None | Local state mutation; blocking | Lock/runtime errors | `Trade` | Sync and async tests | Test-only | Supporting |
| `ConcurrencyQueue.get_instance()` | Class method | Returns singleton | None → queue | Local state mutation on first call | None documented | `Trade`, tests | Yes | Test-only | Supporting |
| `ConcurrencyQueue.lock(...)` | Async context manager | Acquires per-account/symbol `asyncio.Lock` | Account, symbol → context | Local state mutation; blocking | Cancellation/runtime errors | No production caller found | Yes | Test-only | Supporting |
| `ConcurrencyQueue.lock_sync(...)` | Context manager | Acquires per-account/symbol `threading.Lock` | Account, symbol → context | Local state mutation; blocking | Runtime errors | `Trade._send_request` | Yes | Test-only | Supporting |

### `rate_limiter.py`

**File responsibility:** Per-provider token buckets.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RateLimiter` | Class | Thread-safe token bucket | Capacity/fill rate | Local state mutation | Division by zero if capacity is configured as zero | `get_rate_limiter`, tests | Yes | Test-only | Supporting |
| `RateLimiter.check_rate_limit()` | Method | Refills and checks at least one token without consuming | None → bool | Local state mutation from refill | None documented | Readiness | Yes | Test-only | Supporting |
| `RateLimiter.acquire(...)` | Method | Refills and consumes requested tokens | Token count → bool | Local state mutation; warning logs | None documented | `Trade` | Yes | Test-only | Supporting |
| `RateLimiter.get_status()` | Method | Returns current token and utilization snapshot | None → dict | Local state mutation from refill | None documented | Tests only | Yes | Test-only | Useful |
| `get_rate_limiter(...)` | Function | Returns cached provider-specific limiter | Provider → limiter | Local state mutation on first provider use; logging | None documented | Readiness, `Trade`, tests | Yes | Test-only | Supporting |

### `account_info.py`

**File responsibility:** MQL5-compatible account read facade.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `AccountInfo` | Class | Fetches latest account snapshot for each property read | None | External API call; logging | Broker/router/provider exceptions propagate | `Trade`, readiness, validation, usage | Extensive mocked tests | Test-only | Questionable |
| `login`, `trade_mode`, `leverage`, `limit_orders`, `margin_so_mode`, `margin_mode`, `free_margin_mode`, `info_integer` | Methods | Return integer account properties or compatibility constants | Optional property id → int | External API call except compatibility constants; logging | Broker/attribute/conversion errors | `Trade`, readiness, validation, usage | Yes | Test-only | Supporting |
| `trade_allowed`, `trade_expert` | Methods | Return account permissions | None → bool | External API call; logging | Broker errors | Readiness, usage | Yes | Test-only | Supporting |
| `balance`, `credit`, `profit`, `equity`, `margin`, `free_margin`, `margin_level`, `margin_so_level`, `info_double` | Methods | Return monetary/margin properties | Optional property id → float | External API call; logging | Broker/attribute/conversion errors | `Trade`, validation, usage | Yes | Test-only | Supporting |
| `name`, `server`, `currency`, `company`, `info_string` | Methods | Return account identity strings | Optional property id → str | External API call; logging | Broker errors | Usage | Yes | Test-only | Useful |
| `trade_mode_description`, `margin_mode_description` | Methods | Map numeric/string mode to description | None → str | External API call through underlying getter | Conversion/provider errors | Usage/tests | Yes | Test-only | Useful |

### `terminal_info.py`

**File responsibility:** MQL5-compatible terminal read facade.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TerminalInfo` | Class | Fetches latest terminal snapshot for each property read | None | External API call; logging | Broker/router/provider exceptions propagate | Readiness, usage | Mocked tests | Test-only | Questionable |
| `language`, `company`, `name`, `path`, `data_path`, `common_data_path`, `info_string` | Methods | Return terminal strings | Optional property id → str | External API call; logging | Broker/attribute errors | Usage | Yes | Test-only | Useful |
| `build`, `ping_last`, `info_integer` | Methods | Return terminal numeric values | Optional property id → int | External API call; logging | Conversion/provider errors | Usage | Yes | Test-only | Supporting |
| `connected`, `trade_allowed`, `dlls_allowed` | Methods | Return connection and terminal permission flags | None → bool | External API call; logging | Provider errors | Readiness, usage | Yes | Test-only | Supporting |

### `symbol_info.py`

**File responsibility:** Symbol specification/price facade plus provider-client subscription.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SymbolInfo` | Class | Stores symbol name and broker snapshot | Optional name | Local state mutation | None documented | `Trade`, validation, usage | Mocked tests | Test/example-only | Questionable |
| `name(...)` | Method | Combined setter/getter | Optional name → `True` or string | Local state mutation when setting | None documented | Usage/tests | Yes | Test-only | Questionable |
| `refresh`, `refresh_rates` | Methods | Retrieve symbol snapshot | None → bool | External API call; logging | Provider exceptions propagate | `Trade`, validation, usage | Yes | Test-only | Supporting |
| `select(...)` | Method | Optionally subscribes cTrader spot feed or returns success | Boolean → bool | External API call/subscription | Catches broad exceptions and returns `False` | Usage/tests | Yes | Test-only | Questionable |
| `is_synchronized()` | Method | Always reports synchronized | None → `True` | None | None | Usage/tests only | Yes | Test-only | No demonstrated value |
| `digits`, `trade_mode`, `swap_mode`, `spread`, `info_integer` | Methods | Return integer symbol properties | Optional id → int | External API call per invocation | Provider/attribute errors | Validation, `Trade`, usage | Yes | Test-only | Supporting |
| `point`, `tick_size`, `contract_size`, `volume_min`, `volume_max`, `volume_step`, `swap_long`, `swap_short`, `bid`, `ask`, `last`, `info_double` | Methods | Return price/specification values | Optional id → float | External API call per invocation | Provider/attribute errors | Validation, `Trade`, usage | Yes | Test-only | Supporting |
| `trade_mode_description()` | Method | Always returns `"Full Access"` | None → str | None | None | Usage/tests | Yes | Test-only | Questionable |
| `info_string(...)` | Method | Returns name/description/path | Property id → str | External API call | Provider/attribute errors | Tests | Yes | Test-only | Useful |

### `position_info.py`

**File responsibility:** Select one active position and expose its properties.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `PositionInfo` | Class | Holds selected broker position | Optional ticket | External API call when ticket supplied | Broker errors propagate | `Trade`, validation, usage | Mocked tests | Test-only | Supporting |
| `select`, `select_by_ticket` | Methods | Select first matching position | Symbol/ticket → bool | External API call; local state mutation; logging | Broker errors | `Trade`, validation, usage | Yes | Test-only | Supporting |
| `ticket`, `time`, `time_msc`, `time_update`, `time_update_msc`, `type`, `magic`, `identifier`, `info_integer` | Methods | Return integer properties from selected object | Optional property id → int | Read-only | Conversion errors | `Trade`, usage/tests | Yes | Test-only | Supporting |
| `volume`, `price_open`, `stop_loss`, `take_profit`, `price_current`, `swap`, `profit`, `info_double` | Methods | Return numeric properties | Optional property id → float | Read-only | Conversion errors | `Trade`, validation, usage/tests | Yes | Test-only | Supporting |
| `symbol`, `comment`, `info_string` | Methods | Return string properties | Optional property id → str | Read-only | None documented | `Trade`, usage/tests | Yes | Test-only | Supporting |
| `type_description()` | Method | Maps 0/1 to Buy/Sell | None → str | None | None | Usage/tests | Yes | Test-only | Useful |

### `order_info.py`

**File responsibility:** Select one active pending order and expose MQL5-style properties.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `OrderInfo` | Class | Holds selected active pending order | Optional ticket | External API call when ticket supplied | Broker errors propagate | `Trade`, validation, usage | Mocked tests | Test-only | Supporting |
| `select(...)` | Method | Selects first order returned for ticket | Ticket → bool | External API call; local state mutation; logging | Broker errors | `Trade`, validation, usage | Yes | Test-only | Supporting |
| `ticket`, `time_setup`, `time_setup_msc`, `time_expiration`, `time_done`, `time_done_msc`, `type`, `type_time`, `type_filling`, `state`, `magic`, `position_id`, `position_by_id`, `info_integer` | Methods | Return integer order properties | Optional property id → int | Read-only | Conversion errors | Usage/tests and `Trade` symbol resolution | Yes | Test-only | Supporting |
| `volume_initial`, `volume_current`, `price_open`, `stop_loss`, `take_profit`, `price_current`, `price_stop_limit`, `info_double` | Methods | Return numeric order properties | Optional property id → float | Read-only | Conversion errors | Validation/usage/tests | Yes | Test-only | Supporting |
| `symbol`, `comment`, `info_string` | Methods | Return strings | Optional property id → str | Read-only | None documented | `Trade`, usage/tests | Yes | Test-only | Supporting |
| `type_description`, `type_time_description`, `type_filling_description`, `state_description` | Methods | Map numeric codes to labels | None → str | None | None | Usage/tests | Yes | Test-only | Useful |

### `history_order_info.py`

**File responsibility:** Select one historical order and expose the same property set as active orders.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `HistoryOrderInfo` | Class | Holds selected historical order | Optional ticket | External API call when ticket supplied | Broker errors propagate | Usage script | Mocked tests | Test/example-only | Questionable |
| `select(...)` | Method | Selects first historical order returned for ticket | Ticket → bool | External API call; local state mutation; logging | Broker errors | Usage/tests | Yes | Test-only | Useful |
| `ticket`, `time_setup`, `time_setup_msc`, `time_expiration`, `time_done`, `time_done_msc`, `type`, `type_time`, `type_filling`, `state`, `magic`, `position_id`, `position_by_id`, `info_integer` | Methods | Return integer historical-order properties | Optional property id → int | Read-only | Conversion errors | Usage/tests | Yes | Test-only | Useful |
| `volume_initial`, `volume_current`, `price_open`, `stop_loss`, `take_profit`, `price_current`, `price_stop_limit`, `info_double` | Methods | Return numeric properties | Optional property id → float | Read-only | Conversion errors | Usage/tests | Yes | Test-only | Useful |
| `symbol`, `comment`, `info_string` | Methods | Return strings | Optional property id → str | Read-only | None documented | Usage/tests | Yes | Test-only | Useful |
| `type_description`, `type_time_description`, `type_filling_description`, `state_description` | Methods | Map numeric codes to labels | None → str | None | None | Usage/tests | Yes | Test-only | Useful |

### `deal_info.py`

**File responsibility:** Select one historical execution deal and expose its properties.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `DealInfo` | Class | Holds selected historical deal | Optional ticket | External API call when ticket supplied | Broker errors propagate | Usage script | Mocked tests | Test/example-only | Questionable |
| `select(...)` | Method | Selects first historical deal returned for ticket | Ticket → bool | External API call; local state mutation; logging | Broker errors | Usage/tests | Yes | Test-only | Useful |
| `ticket`, `order`, `time`, `time_msc`, `type`, `entry`, `magic`, `position_id`, `info_integer` | Methods | Return integer deal properties | Optional property id → int | Read-only | Conversion errors | Usage/tests | Yes | Test-only | Useful |
| `volume`, `price`, `commission`, `swap`, `profit`, `info_double` | Methods | Return numeric deal properties | Optional property id → float | Read-only | Conversion errors | Usage/tests | Yes | Test-only | Useful |
| `symbol`, `comment`, `info_string` | Methods | Return strings | Optional property id → str | Read-only | None documented | Usage/tests | Yes | Test-only | Useful |
| `type_description`, `entry_description` | Methods | Map numeric codes to labels | None → str | None | None | Usage/tests | Yes | Test-only | Useful |

### `idempotency.py`

**File responsibility:** Request fingerprinting and replay record lifecycle.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `IdempotencyService` | Class | Coordinates deterministic keys and store records | `TradeStore` | Local state mutation | None documented | `Trade` | Indirect trade tests | Test-only | Supporting |
| `generate_key(...)` | Method | Hashes account, symbol, action, volume, price, slippage, and time bucket | Request fields → `idem_<sha256>` | Reads wall clock | Conversion/format errors | `Trade._send_request` | Indirect | Test-only | Supporting |
| `check_duplicate(...)` | Method | Reads current record | Key → record/`None` | Read-only store access | Store-defined | `Trade._send_request` | Indirect | Test-only | Supporting |
| `register_in_progress(...)` | Method | Saves request with status and timestamp | Key, request, TTL → `None` | Persistence write/local mutation | Store-defined | `Trade._send_request` | Indirect | Test-only | Supporting |
| `register_completed(...)` | Method | Saves result with status and timestamp | Key, result, TTL → `None` | Persistence write/local mutation | Store-defined | `Trade._send_request` | Indirect | Test-only | Supporting |

### `readiness.py`

**File responsibility:** Pre-execution readiness aggregation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ReadinessService` | Class | Namespace for readiness check | None | None | None | `Trade` | Yes | Test-only | Supporting |
| `run_execution_readiness_check(...)` | Method | Checks terminal connection/trading permission, account permission, and token availability | Provider, symbol, terminal facade, account facade → result dict | External API calls through facades; logging; limiter refill | Provider errors propagate | `Trade._send_request` | Failure-path tests | Test-only | Supporting |

### `validation.py`

**File responsibility:** Request validation and normalization.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ValidationService` | Class | Validates broker requests | None | None | N/A | `Trade` | Precision and indirect trade tests | Test-only | Supporting |
| `normalize_precision(...)` | Static method | Decimal quantization by digits or step | Value, precision → `Decimal` | None | Decimal errors; zero step | Other validation methods | Direct test | Test-only | Supporting |
| `validate_volume(...)` | Method | Enforces min/max and step alignment | Symbol, volume, `SymbolInfo` → float | External API calls through symbol facade; logging | `ValidationError` | `validate_order_request` | Indirect | Test-only | Supporting |
| `validate_price(...)` | Method | Requires positive price and rounds to symbol digits | Symbol, price, order type, symbol facade → float | External API call; logging | `ValidationError` | `validate_order_request` | Indirect | Test-only | Supporting |
| `validate_stops(...)` | Method | Normalizes SL/TP and checks buy/sell geometry | Symbol, SL, TP, type, entry, symbol facade → tuple | External API call; logging | `ValidationError` | `validate_order_request` | Indirect | Test-only | Supporting |
| `validate_margin(...)` | Method | Rejects only when free margin is non-positive | Account, symbol, volume, price, type, account facade → `None` | External API call; logging | `ValidationError` | `validate_order_request` | Indirect | Test-only | Questionable |
| `validate_slippage(...)` | Method | Enforces `0 <= slippage <= max_tolerance` | Slippage and optional max → `None` | Logging | `ValidationError` | `validate_order_request` | Indirect | Test-only | Supporting |
| `validate_dealing_mode_compatibility(...)` | Method | Reads margin mode; netting branch is currently a no-op | Action, ticket, account facade → `None` | External API call | Provider errors | `validate_order_request` | No meaningful direct test | Test-only | No demonstrated value |
| `validate_market_session(...)` | Method | Rejects non-crypto symbols on UTC weekends | Symbol → `None` | Reads wall clock; logging | `ValidationError` | `validate_order_request` | Tests force a weekday | Test-only | Questionable |
| `validate_order_request(...)` | Method | Enriches missing type/price from selected order/position, runs validations, returns copy | Request plus facades → sanitized dict | External API calls; logging | `ValidationError`, broker errors | `Trade._send_request` | Indirect | Test-only | Supporting |

### `reconciliation.py`

**File responsibility:** Compare local and broker active state and partially synchronize.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ReconciliationService` | Class | Holds store, gate flag, thresholds, and last reconciliation state | Store | Local state mutation | None documented | `Trade` startup, timeout and shutdown | Divergence test | Test-only | Supporting |
| `set_block_trading_on_startup(...)` | Method | Changes startup gate policy | Boolean → `None` | Local state mutation | None | Tests only | Yes | Test-only | Useful |
| `reconcile(...)` | Method | Compares positions/orders, deletes missing local positions, saves missing local broker records, calculates drift, and returns summary | Live positions, live orders, equity → dict | Persistence writes/local mutation; logging | Key/type/store errors | `Trade` | Yes | Test-only | Supporting |

### `reporting.py`

**File responsibility:** Build a local trading-state report.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ReportingService` | Class | Namespace for report builder | N/A | None | N/A | No production caller found | One unit test | **Test-only** | No demonstrated value |
| `build_report(...)` | Static method | Aggregates counts, local profit/exposure, records, reconciliation and warnings | Store and optional summaries → dict | Read-only; logging | Record shape/type errors | Unit test only | Yes | **Test-only** | Questionable |

### `trade.py`

**File responsibility:** MQL5-style mutation facade and safety orchestrator.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Trade` | Class | Composes all request safety, broker mutation, result and local-state services | Optional store | Local state mutation; import/default singleton use | Constructor dependency errors | Tests and usage script only | Extensive mocked tests | **Test-only** | Questionable |
| `set_symbol`, `set_order_filling`, `set_deviation_in_points`, `set_expert_magic_number` | Methods | Mutate default request settings | Value → `None` | Local state mutation | None documented | Usage/tests | Yes | Test-only | Useful |
| `result_retcode`, `result_deal`, `result_order`, `result_volume`, `result_price`, `result_bid`, `result_ask`, `result_comment` | Methods | Read last normalized result | None → scalar | Read-only | Conversion errors for malformed result | Usage/tests | Yes | Test-only | Useful |
| `buy`, `sell` | Methods | Build market request using current broker constants and bid/ask | Volume and optional order fields → bool | External API calls, broker mutation through `_send_request` | Public method can propagate price/provider setup errors before `_send_request`; pipeline converts many later errors to failure result | Usage/tests | Yes | Test-only | Useful |
| `buy_limit`, `sell_limit`, `buy_stop`, `sell_stop` | Methods | Build pending request using provider constants | Volume, price and optional fields → bool | External API calls, broker mutation | Provider setup errors; pipeline failures normalized | Usage/tests | Yes | Test-only | Useful |
| `position_open(...)` | Method | Dispatches to `buy` or `sell` based on numeric type | Full position request → bool | Broker mutation | Same as buy/sell | Tests | Yes | Test-only | Useful |
| `position_close(...)` | Method | Selects position, constructs opposite market request, closes full volume | Symbol/ticket and deviation → bool | External reads; broker mutation | Provider setup errors; returns false when position absent | Usage/tests | Yes | Test-only | Useful |
| `position_modify(...)` | Method | Selects position and sends SL/TP action | Symbol/ticket, SL, TP → bool | External reads; broker mutation | Provider setup errors | Usage/tests | Yes | Test-only | Useful |
| `order_modify(...)` | Method | Sends modify action for pending order | Ticket, price, SL, TP → bool | External reads; broker mutation | Provider setup errors | Usage/tests | Yes | Test-only | Useful |
| `order_delete(...)` | Method | Sends remove action for pending order | Ticket → bool | External reads; broker mutation | Provider setup errors | Usage/tests | Yes | Test-only | Useful |
| `set_kill_switch(...)` | Class method | Globally blocks new requests, cancels all pending orders, optionally closes all positions | Active flag and flatten flag → `None` | Global state mutation; external reads; broker mutations | Most cleanup errors are swallowed/logged | Tests only | Yes | Test-only | Questionable |
| `shutdown(...)` | Class method | Globally rejects new requests, waits for in-flight count, then attempts final reconciliation | Timeout → `None` | Global state mutation; blocking; external reads; local writes | Most errors swallowed/logged | Tests only | Yes | Test-only | Questionable |

### `__init__.py`

**File responsibility:** Package gate and export standardization.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `__all__` | Export constant | Defines 38 package exports | N/A | None | None | Package consumers, standardization helper | Package imports in tests/usage | Possibly used | Supporting |
| `standardize_domain_exports(...)` invocation | Registration action | Applies trading category metadata/standardization to exported globals | Package globals and names | Dynamic registration/local mutation at import | Helper-defined errors | Potential tool discovery; no explicit caller | Not directly tested here | Possibly used | Supporting |

## 6. Actual Workflows

### `V1-WF-TRADING-001` — Strategy Runtime Permission Gate

* **Scope:** Cross-domain
* **Trigger:** A backtest, optimization, live session, or live strategy loader attempts to load a stored strategy.
* **Input boundary:** Strategy ID plus runtime context.
* **Functions and methods used:** `assert_strategy_allowed()` → `StrategyRuntimePermissionService.assert_strategy_allowed()`.
* **Files involved:** `permissions.py`; caller routes/services; database manager and governance repository.
* **External dependencies:** SQLite/database access through local data packages.
* **Output boundary:** Returns control to caller when allowed; otherwise raises a specific permission or lookup error.
* **Failure behaviour:** Missing strategy raises `LookupError`; disallowed lifecycle state raises `StrategyPermissionError`; callers either reject the request or fall back/skip depending on their own handling.
* **Operational status:** **Working**
* **Evidence:**
  * `app/api/routes/backtest.py::_load_strategy_class`
  * `app/services/execution/live/engine.py::MultiStrategyEngine._load_strategy_class`
  * `app/services/optimization/core.py`
  * `app/api/routes/live.py`
  * `app/api/session/session_service.py`
  * `app/services/trading/permissions.py`

```text
Backtest / optimization / live strategy load
→ assert_strategy_allowed(strategy_id, context)
→ load strategy record
→ resolve governance identity
→ load governance lifecycle state
→ compare against context-specific allowed set
→ allow load OR raise
```

### `V1-WF-TRADING-002` — Stateful Strategy Event Contract in Simulation

* **Scope:** Cross-domain
* **Trigger:** Event-driven simulation reaches an eligible tick/bar phase for a strategy with `requires_portfolio_state=True`.
* **Input boundary:** Current tick, symbol, position/order/trade snapshots, market data, runtime state.
* **Functions and methods used:** Simulation builds `StrategyContext` → strategy `on_event(context)` → returns `TradeAction` objects → simulation applies actions.
* **Files involved:** `stateful.py`, `app/services/simulation/engine.py`, `app/services/simulation/event_driven.py`, `app/services/strategy/stateful_common.py`, multiple `data/strategies/...` files.
* **External dependencies:** `pandas`; simulation state.
* **Output boundary:** Provider-independent trade actions are handed back to the simulation engine.
* **Failure behaviour:** Strategy or engine exceptions are handled by simulation caller logic; contract itself does not add error wrapping.
* **Operational status:** **Working**
* **Evidence:**
  * `simulation/event_driven.py` checks `requires_portfolio_state`, calls `_build_strategy_context`, invokes `on_event`, then `_apply_trade_actions`.
  * `data/strategies/baselines/pyramiding.py::PyramidingStrategy` inherits `StatefulStrategyMixin` and emits `TradeAction`.
  * Many baseline/stored strategies consume `PositionType`, context and action contracts.

```text
Simulation tick/bar phase
→ detect stateful strategy
→ Engine._build_strategy_context(...)
→ concrete_strategy.on_event(context)
→ list[TradeAction]
→ Engine._apply_trade_actions(...)
→ simulated order/position state changes
```

### `V1-WF-TRADING-003` — Broker Information Read Facades

* **Scope:** Internal package workflow with external broker dependency
* **Trigger:** Usage script, test, validation, readiness, or `Trade` requests account/terminal/symbol/order/position/deal data.
* **Input boundary:** Active broker selected by router; optional symbol or ticket.
* **Functions and methods used:** Facade `_refresh`/`select` followed by typed property accessors.
* **Files involved:** `account_info.py`, `terminal_info.py`, `symbol_info.py`, `position_info.py`, `order_info.py`, `history_order_info.py`, `deal_info.py`.
* **External dependencies:** Broker router and provider modules.
* **Output boundary:** Scalar properties or selection success boolean.
* **Failure behaviour:** Most broker exceptions propagate. Missing data generally becomes zero, empty string, or `False`, which can hide “not available” versus legitimate zero values.
* **Operational status:** **Unverified**
* **Evidence:** `tests/usage/app/services/07_trading.py` exercises all seven facades; unit tests use mocked broker records. No indexed production caller for these facades was found outside the disconnected `Trade` pipeline.

```text
Caller
→ get_broker_module()
→ broker get_*_info(...)
→ cache selected snapshot or refresh
→ scalar accessor/default value
```

### `V1-WF-TRADING-004` — Guarded Broker Trade Request

* **Scope:** Internal package workflow
* **Trigger:** `Trade.buy/sell/pending/modify/close/delete`.
* **Input boundary:** MQL5-style method arguments converted to request dictionary.
* **Functions and methods used:** `Trade._send_request`, idempotency, startup reconciliation, lock, readiness, validation, rate limiter, broker `trade`, result normalizer, store updates.
* **Files involved:** `trade.py` and nearly every support file except `permissions.py`, `stateful.py`, `reporting.py`, history/deal wrappers.
* **External dependencies:** Broker router/provider, wall clock, thread pool.
* **Output boundary:** Boolean success plus last-result accessors; local in-memory records.
* **Failure behaviour:** Most pipeline failures are converted into `NormalizedTradeResult`; pre-request provider setup can still raise. Timeout returns retcode `10005`, attempts immediate reconciliation, and does not cancel the underlying broker task.
* **Operational status:** **Unverified / test-only**
* **Evidence:** Complete static call path in `trade.py`; mocked `test_trade_actions`, failure, rate-limit, kill-switch and shutdown tests; usage script. Direct import searches found only tests and usage, not production runtime callers.

```text
Trade public method
→ construct provider-specific request
→ kill-switch / shutdown gate
→ AccountInfo.login()
→ idempotency lookup
→ startup broker/local reconciliation
→ per-account/symbol lock
→ register in-progress
→ readiness checks
→ request validation/normalization
→ consume rate token
→ broker.trade(request) in worker thread
→ normalize result
→ save execution/order/position
→ register completed
→ bool + last-result state
```

### `V1-WF-TRADING-005` — Emergency Kill Switch and Graceful Shutdown

* **Scope:** Internal package workflow
* **Trigger:** Explicit `Trade.set_kill_switch(...)` or `Trade.shutdown(...)`.
* **Input boundary:** Global class-level state.
* **Functions and methods used:** Broker order/position reads, new `Trade` instances, `order_delete`, `position_close`, reconciliation.
* **Files involved:** `trade.py`, broker router, store/reconciliation.
* **External dependencies:** Active broker.
* **Output boundary:** New trades blocked; cleanup attempts performed.
* **Failure behaviour:** Cleanup exceptions are logged and swallowed. Kill-switch temporarily sets a global bypass so its own cleanup requests can pass. Shutdown has no public reset method.
* **Operational status:** **Partial / test-only**
* **Evidence:** `Trade.set_kill_switch`, `Trade.shutdown`, and unit tests.

```text
Activate global state
→ bypass block for cleanup
→ list active pending orders
→ order_delete(each)
→ optionally list positions
→ position_close(each)
→ restore bypass

or

set shutting_down
→ poll in-flight counter
→ broker snapshot
→ final reconciliation
```

### `V1-WF-TRADING-006` — Local Reconciliation and Reporting

* **Scope:** Internal
* **Trigger:** Startup gate, trade timeout, shutdown, or direct unit call.
* **Input boundary:** Broker-derived position/order dictionaries and local `TradeStore`.
* **Functions and methods used:** `ReconciliationService.reconcile`; optionally `ReportingService.build_report`.
* **Files involved:** `reconciliation.py`, `reporting.py`, `store.py`.
* **External dependencies:** None after broker snapshots are supplied.
* **Output boundary:** Updated local position/order records and reconciliation/report dictionary.
* **Failure behaviour:** Dictionary shape errors propagate; stale pending orders are not deleted; mismatches remain unresolved; reconciliation still reports `is_reconciled=True`.
* **Operational status:** **Partial**
* **Evidence:** Static code and unit tests. `ReportingService` has no runtime caller.

```text
Broker snapshots + local store
→ compare tickets
→ delete local positions missing at broker
→ save broker positions/orders missing locally
→ report mismatches and drift
→ mark reconciled
→ optional report builder (currently disconnected)
```

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `assert_strategy_allowed` | Backtest route | Direct function call | Runtime | `app/api/routes/backtest.py::_load_strategy_class` |
| `assert_strategy_allowed` | Live engine | Direct function call | Runtime | `app/services/execution/live/engine.py::_load_strategy_class` |
| `assert_strategy_allowed` | Optimization core | Direct function call | Runtime | `app/services/optimization/core.py` |
| `assert_strategy_allowed` | Live API route | Direct function call | Runtime | `app/api/routes/live.py` |
| `assert_strategy_allowed` | Session service | Direct function call | Runtime | `app/api/session/session_service.py` |
| `StrategyPermissionError` | Live API route | Import/catch | Runtime | `app/api/routes/live.py` |
| `PositionType` | Baseline and stored strategies | Import/reference | Runtime strategy code | `data/strategies/baselines/breakout.py` and multiple `data/strategies/...` |
| `PositionSnapshot`, `StrategyContext` | Stateful helpers | Type/import and method calls | Runtime | `app/services/strategy/stateful_common.py` |
| `OrderSnapshot`, `PositionSnapshot`, `TradeSnapshot`, `StrategyRuntimeState`, `StrategyContext`, `TradeAction` | Simulation engine | Import, construction, action application | Runtime | `app/services/simulation/engine.py` |
| `StatefulStrategyMixin`, `StrategyContext`, `TradeAction` | Stateful strategies | Inheritance, annotations, construction | Runtime strategy code | `data/strategies/baselines/pyramiding.py` and peers |
| `StatefulStrategyMixin.requires_portfolio_state` | Event-driven simulator | Attribute gate | Runtime | `app/services/simulation/event_driven.py` |
| `StrategyContext.positions_for_symbol` | Strategy helper | Method call | Runtime | `app/services/strategy/stateful_common.py::positions_for_side` |
| `Trade` | Trading usage script | Instantiation/method calls | Example | `tests/usage/app/services/07_trading.py` |
| `Trade` | Trading unit tests | Instantiation/method calls | Test | `tests/unit/app/services/trading/test_trader.py` |
| `AccountInfo`, `TerminalInfo`, `SymbolInfo`, `PositionInfo`, `OrderInfo`, `HistoryOrderInfo`, `DealInfo` | Usage script | Instantiation/method calls | Example | `tests/usage/app/services/07_trading.py` |
| `AccountInfo`, `TerminalInfo`, `SymbolInfo`, `PositionInfo`, `OrderInfo`, `HistoryOrderInfo`, `DealInfo` | Unit tests | Instantiation/method calls | Test | `tests/unit/app/services/trading/test_trader.py` |
| `ConcurrencyQueue`, `IdempotencyService`, `ReadinessService`, `ValidationService`, `ReconciliationService`, `RateLimiter`, result/store classes | `Trade` | Internal composition | Test-only call chain | `app/services/trading/trade.py` |
| `ReportingService.build_report` | Unit test | Direct call | Test | `tests/unit/app/services/trading/test_trader.py::test_trader_reporting` |
| `StatefulStrategyProtocol` | Definition/package export only | No caller found | None confirmed | Repository-wide symbol search |
| `TradeAction.hold` | No caller found | No call found | None confirmed | Repository-wide call search |
| Package exports | `standardize_domain_exports` | Dynamic registration | Unknown | `app/services/trading/__init__.py` |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.services.brokers` / router | Active broker name/module; account, terminal, symbol, position, order, history, deal reads; `trade` mutation; provider clients/constants | All broker facades and `Trade` | `get_broker_module`, `get_active_broker_name` imports |
| `app.services.utils.logger` | Structured/debug/error logging | Nearly every file | Module imports |
| `app.services.utils.errors` | `ValidationError` | `validation.py` | Direct import |
| `app.services.utils` standardization | `standardize_domain_exports` | `__init__.py` | Package import gate |
| `data.database.sqlite.database_operations` | `DatabaseManager` | `permissions.py` | Strategy lookup |
| `data.database.sqlite.governance` | `GovernanceRepository` | `permissions.py` | Lifecycle state lookup |
| `pandas` | DataFrame/Series type in strategy context | `stateful.py` | Direct import |
| Standard library concurrency/time | Threads, locks, futures, wall clock, hashing, decimal | Safety and execution files | Direct imports |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| Backtest API | `assert_strategy_allowed` | Block strategies whose state is not eligible for backtest | `app/api/routes/backtest.py` |
| Optimization | `assert_strategy_allowed` | Block strategies not eligible for optimization | `app/services/optimization/core.py` |
| Live execution engine | `assert_strategy_allowed` | Gate stored strategy loading | `app/services/execution/live/engine.py` |
| Live API | `assert_strategy_allowed`, `StrategyPermissionError` | Validate live strategy/session operations and map permission failures | `app/api/routes/live.py` |
| Session service | `assert_strategy_allowed` | Gate session creation/start | `app/api/session/session_service.py` |
| Simulation engine | Stateful snapshots, context, runtime state, actions | Build strategy event boundary and apply emitted actions | `app/services/simulation/engine.py`, `event_driven.py` |
| Strategy helpers | `PositionSnapshot`, `StrategyContext` | Portfolio filtering and calculations | `app/services/strategy/stateful_common.py` |
| Baseline/stored strategies | `PositionType`, `StatefulStrategyMixin`, `StrategyContext`, `TradeAction` | Implement stateful strategy logic | `data/strategies/...` |
| Trading tests/examples | Entire broker facade and `Trade` surface | Mock verification and manual broker demonstration | `tests/unit/.../test_trader.py`, `tests/usage/.../07_trading.py` |
| Dynamic tool discovery | Package `__all__` | Possible standardized export metadata | `__init__.py`; runtime use unverified |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `app/services/trading/trade.py::Trade` | `app/services/execution/trading.py::Trade` | Both construct broker requests, place/modify/close/cancel trades, expose result data, and use MQL5 constants | Both source files; live engine imports the execution-domain version | Divergent safety, result, error and provider behaviour; wrong class may be maintained or called |
| Broker facade files in this package | Flat functions in `app/services/execution/trading.py` | Account, position, order, history order, symbol, terminal and deal information | `execution/trading.py` exports corresponding `trading_*_info` functions | Two public read APIs with different envelopes/defaults |
| `OrderInfo` | `HistoryOrderInfo` | Nearly identical field accessors and code mappings; only selection source differs | `order_info.py`, `history_order_info.py` | Duplicate fixes and mapping drift |
| `Trade.result_*` | `NormalizedTradeResult` attributes / `to_dict` | Multiple ways to access same result | `trade.py`, `result.py` | API surface expansion without distinct value |
| `ReadinessService` rate check | `Trade` rate acquire | Both inspect rate limiter in one request | `readiness.py`, `trade.py` | Check-then-acquire race; readiness may pass but acquire immediately fail |
| `SymbolInfo.refresh()` calls | Individual property accessors | Every property refreshes again even after explicit refresh | `symbol_info.py` | Repeated provider calls, inconsistent snapshots |
| `AccountInfo`/`TerminalInfo` property reads | Their generic `info_*` methods | Same fields exposed by named and numeric APIs | Wrapper files | Larger compatibility surface and duplicated mappings |
| README intended flow | `Trade._send_request` implementation | Similar sequence but not identical in details | README and source | Documentation can imply guarantees not actually delivered |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `app.services.trading.trade.Trade` | Direct imports/instantiations found only in package tests and usage script; production live engine uses `app.services.execution.trading.Trade` | Package import, qualified module import, `Trade()` and caller path searches | **Medium** | Dynamic package export discovery cannot be ruled out |
| `ReportingService` | Only direct caller is its unit test | Class name, method name, qualified module and import searches | **High static / Medium overall** | `test_trader_reporting`; no runtime call |
| `StatefulStrategyProtocol` | Definition and package export only | Symbol/import/inheritance searches | **High static** | No external match |
| `TradeAction.hold` | No call site found | Qualified and method-call searches | **Medium** | Class remains dynamically usable |
| `DealInfo` | No production import found; usage and unit tests demonstrate it | Direct module/import/instantiation searches | **Medium** | Dynamic export use possible |
| `HistoryOrderInfo` | No production import found; usage and unit tests demonstrate it | Direct module/import/instantiation searches | **Medium** | Dynamic export use possible |
| `SymbolInfo.is_synchronized` | Always returns `True` without broker evidence | Source inspection and caller search | **High** | `symbol_info.py::is_synchronized` |
| `SymbolInfo.trade_mode_description` | Always returns `"Full Access"` regardless actual mode | Source inspection | **High** | `symbol_info.py::trade_mode_description` |
| `AccountInfo.margin_so_mode` | Always returns `0` | Source inspection | **High** | `account_info.py::margin_so_mode` |
| `AccountInfo.free_margin_mode` | Always returns `0` | Source inspection | **High** | `account_info.py::free_margin_mode` |
| `ValidationService.validate_dealing_mode_compatibility` | Reads mode but performs no enforcement | Source and call-path inspection | **High** | Netting branch contains only `pass` |
| `test_trader_extra.py` | References obsolete names such as `ConcurrencyManager`, `IdempotencyManager`, `ReadinessManager`, `Reporter`, `TradeResult`, `TraderStore`, `TradeValidator`; catches all exceptions | Full file inspection | **High** | The test can pass while every attempted API call fails |
| Package README | Uses `app/services/trader` and `tests/unit/app/services/trader/test_trader.py`, while actual path is `trading` | Documentation/path search | **High** | `README.md` |
| `StrategyRuntimeContext` package visibility | Public alias exists but is absent from `__all__` | Source/export reconciliation | **High** | `permissions.py`, `__init__.py` |

No item above is labelled dead code because runtime dynamic export invocation could not be executed.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Guarded broker execution | No confirmed production caller for this package's `Trade` | Safety pipeline may not protect actual live execution | Live engine imports `app.services.execution.trading.Trade`; trading `Trade` direct callers are tests/usage |
| Partial position close | No public method accepts partial volume | Usage script calls private `_send_request` directly | `tests/usage/app/services/07_trading.py::example_12_close_partial_position` |
| Reconciliation of stale pending orders | Store lacks `delete_order`; method only records/logs stale order | Local active-order state remains stale | `reconciliation.py` comments and absence of `TradeStore.delete_order` |
| Reconciliation of mismatches | Mismatched positions/orders are reported but not overwritten | Drift persists while result says reconciled | `ReconciliationService.reconcile` |
| Unknown broker timeout | Timed-out future is not cancelled; reconciliation runs immediately | Late broker mutation may occur after reconciliation and returned failure | `Trade._send_request` timeout branch and `executor.shutdown(wait=False)` |
| Reporting | `ReportingService` is not connected to API, scheduler, trade flow, or shutdown | Report capability has no demonstrated runtime value | Caller search |
| Persistent local trade state | Default implementation is only in-memory | Idempotency and state disappear on process restart | `store.py::_default_store` |
| Dealing-mode enforcement | Validation method has no rules | Netting/hedging incompatibilities are not blocked | `validate_dealing_mode_compatibility` |
| Accurate margin validation | Only checks `free_margin > 0`; ignores requested order margin | Orders can pass validation despite insufficient required margin | `validate_margin` |
| Package export registration | Runtime consumer of standardized exports not confirmed | Some otherwise-unused symbols may still be dynamically discoverable | `__init__.py`; no runtime trace |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-TRADING-001` | Main guarded `Trade` implementation is disconnected from confirmed production execution | `app/services/trading/trade.py::Trade` | Important safety features may be unused in live runtime | Caller/import searches; live engine imports execution-domain `Trade` |
| `V1-ISSUE-TRADING-002` | Duplicate trading implementations | `app/services/trading/trade.py`; `app/services/execution/trading.py` | Behavioural drift and ambiguous ownership | Overlapping operations and result contracts |
| `V1-ISSUE-TRADING-003` | `Trade` owns too many unrelated responsibilities | `Trade._send_request`, class methods | Hard to verify, test and reuse individual guarantees | Imports/composes almost entire package and provider details |
| `V1-ISSUE-TRADING-004` | Timeout does not stop broker mutation | `Trade._send_request` | Unknown outcome may become a late actual trade | `future.result(timeout=5)`, no cancellation, `shutdown(wait=False)` |
| `V1-ISSUE-TRADING-005` | Immediate timeout reconciliation can race late broker completion | Timeout branch | False reconciliation result and later state drift | Reconciliation occurs before worker is guaranteed finished |
| `V1-ISSUE-TRADING-006` | Reconciliation always marks itself complete | `ReconciliationService.reconcile` | Startup gate can open with unresolved mismatches | `self.is_reconciled = True` and returned `is_reconciled=True` |
| `V1-ISSUE-TRADING-007` | Stale pending orders cannot be deleted | `TradeStore`; reconciliation order branch | Local active order list can remain wrong | No `delete_order`; source comments acknowledge gap |
| `V1-ISSUE-TRADING-008` | Mismatched records are not corrected | Reconciliation loops | Repeated drift and misleading local reports | Mismatch lists are appended only |
| `V1-ISSUE-TRADING-009` | Local position ticket uses deal ticket on successful open | `Trade._send_request` state update | Store key may not match broker position ticket | `save_position(deal_ticket, ...)` |
| `V1-ISSUE-TRADING-010` | In-memory default store is not thread-safe or durable | `InMemoryTradeStore`, `_default_store` | Concurrent access races and restart data loss | Plain dictionaries and import-time singleton |
| `V1-ISSUE-TRADING-011` | Idempotency key is time-bucket-based and ignores supplied request ID | `IdempotencyService.generate_key`; `Trade._send_request` | Same request crossing bucket boundary can execute twice; caller cannot define stable key | Hash inputs and request-ID assignment order |
| `V1-ISSUE-TRADING-012` | Readiness performs check-then-acquire on token bucket | `ReadinessService`; `Trade` | Race or duplicate checks; readiness result is not a reservation | `check_rate_limit()` then later `acquire()` |
| `V1-ISSUE-TRADING-013` | Validation dealing-mode check is a stub | `ValidationService.validate_dealing_mode_compatibility` | Netting/hedging safety claim not implemented | `pass` branch |
| `V1-ISSUE-TRADING-014` | Margin validation does not calculate required margin | `ValidationService.validate_margin` | Insufficient-margin requests can pass local validation | Only checks free margin positive |
| `V1-ISSUE-TRADING-015` | Market-session validation is a weekend symbol-name heuristic | `validate_market_session` | Incorrect for holidays, sessions, CFDs, crypto naming and provider calendars | UTC weekday plus substring list |
| `V1-ISSUE-TRADING-016` | Broad exception handling hides cleanup failures | `set_kill_switch`, `shutdown`, `SymbolInfo.select` | Emergency actions can partially fail without caller-level failure signal | Exceptions logged/swallowed |
| `V1-ISSUE-TRADING-017` | Global mutable class state controls all Trade instances | `Trade` class attributes | Cross-account/test interference; no scoped ownership | `_kill_switch_active`, `_is_shutting_down`, counters |
| `V1-ISSUE-TRADING-018` | Shutdown state has no public reset | `Trade.shutdown` | Once called, process rejects future requests unless private state is mutated | Unit test resets `_is_shutting_down` directly |
| `V1-ISSUE-TRADING-019` | Lock dictionaries never evict keys | `ConcurrencyQueue` | Long-running multi-account/symbol process can grow lock maps indefinitely | `_async_locks`, `_sync_locks` |
| `V1-ISSUE-TRADING-020` | Wrapper methods repeatedly fetch fresh snapshots | Account/terminal/symbol facades | High call volume and inconsistent multi-field snapshots | Each accessor invokes refresh |
| `V1-ISSUE-TRADING-021` | Missing-data defaults conflate absence with legitimate zero | All information facades | Callers can act on invalid values without knowing data is absent | `getattr(..., 0/0.0/"")` |
| `V1-ISSUE-TRADING-022` | `SymbolInfo` directly selects provider client | `SymbolInfo.select`; all Trade public request builders | Router abstraction is bypassed for provider constants/client features | `hasattr(...get_ctrader_client...) else get_mt5_client()` |
| `V1-ISSUE-TRADING-023` | Result normalizer's provider parameter does not change normalization | `BrokerResponseNormalizer.normalize_response` | Provider-specific semantics are not actually normalized | Same branch for all provider names |
| `V1-ISSUE-TRADING-024` | Retcode `0` is globally treated as success | Result normalizer and `Trade` | A provider/default-zero response may be accepted incorrectly | Success tuple `(10009, 10008, 0)` |
| `V1-ISSUE-TRADING-025` | Order and history-order wrappers duplicate nearly all code | `order_info.py`, `history_order_info.py` | Maintenance and mapping divergence | Matching method sets and mappings |
| `V1-ISSUE-TRADING-026` | Partial close requires private API use | `Trade`; usage script | Public API is incomplete for demonstrated workflow | `trade._send_request(request)` |
| `V1-ISSUE-TRADING-027` | Usage script reads private symbol state | Usage script | Example depends on internal representation | `sym._data` |
| `V1-ISSUE-TRADING-028` | Package README is stale | `README.md` | Misleading imports, paths and verification instructions | Repeated `trader` path |
| `V1-ISSUE-TRADING-029` | Extra coverage test validates obsolete APIs while swallowing all failures | `test_trader_extra.py` | False sense of test coverage | Every block catches `Exception` and has no assertion |
| `V1-ISSUE-TRADING-030` | Package import initializes default store and imports all broker-facing modules | `__init__.py`, `store.py` | Nontrivial import-time mutation/logging and wide dependency loading | `_default_store = InMemoryTradeStore()` |
| `V1-ISSUE-TRADING-031` | `StrategyRuntimeContext` is not re-exported | `permissions.py`, `__init__.py` | Inconsistent public type surface | Alias absent from `__all__` |
| `V1-ISSUE-TRADING-032` | Reporting is isolated | `reporting.py` | Capability exists without runtime value | Only test caller found |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-TRADING-001` | Strategy lifecycle permission gate | `permissions.py::assert_strategy_allowed` | `V1-WF-TRADING-001` | Used | Essential | Confirmed in backtest, optimization and live paths |
| `V1-CAP-TRADING-002` | Stateful strategy context contract | `stateful.py::StrategyContext`, snapshots, runtime state | `V1-WF-TRADING-002` | Used | Essential | Core simulation/strategy boundary |
| `V1-CAP-TRADING-003` | Provider-independent strategy action contract | `stateful.py::TradeAction` | `V1-WF-TRADING-002` | Used | Essential | Concrete strategies emit actions |
| `V1-CAP-TRADING-004` | Stateful strategy opt-in/default callbacks | `StatefulStrategyMixin` | `V1-WF-TRADING-002` | Used | Essential | Engine gates on `requires_portfolio_state` |
| `V1-CAP-TRADING-005` | Account and terminal information facade | `AccountInfo`, `TerminalInfo` | `V1-WF-TRADING-003`, `004` | Test-only | Questionable | Useful behaviour, no production caller found |
| `V1-CAP-TRADING-006` | Symbol specifications and prices | `SymbolInfo` | `V1-WF-TRADING-003`, `004` | Test/example-only | Questionable | Repeated refreshes and hard-coded compatibility values |
| `V1-CAP-TRADING-007` | Active position/order information | `PositionInfo`, `OrderInfo` | `V1-WF-TRADING-003`, `004` | Test-only | Supporting | Used internally by disconnected Trade flow |
| `V1-CAP-TRADING-008` | Historical order/deal information | `HistoryOrderInfo`, `DealInfo` | `V1-WF-TRADING-003` | Test/example-only | Questionable | No production caller found |
| `V1-CAP-TRADING-009` | Request idempotency | `IdempotencyService`, `TradeStore` | `V1-WF-TRADING-004` | Test-only | Supporting | Process-local by default |
| `V1-CAP-TRADING-010` | Per-account/symbol request serialization | `ConcurrencyQueue` | `V1-WF-TRADING-004` | Test-only | Supporting | Sync path used by Trade |
| `V1-CAP-TRADING-011` | Provider rate limiting | `RateLimiter`, `get_rate_limiter` | `V1-WF-TRADING-004` | Test-only | Supporting | Check and acquire are separate |
| `V1-CAP-TRADING-012` | Execution readiness gate | `ReadinessService` | `V1-WF-TRADING-004` | Test-only | Supporting | Connection and permission checks |
| `V1-CAP-TRADING-013` | Trade request validation/normalization | `ValidationService` | `V1-WF-TRADING-004` | Test-only | Supporting | Several checks are partial/stubbed |
| `V1-CAP-TRADING-014` | Broker response normalization | `NormalizedTradeResult`, normalizer, builder | `V1-WF-TRADING-004` | Test-only | Supporting | Provider argument does not alter mapping |
| `V1-CAP-TRADING-015` | Market and pending order operations | `Trade.buy/sell/buy_limit/sell_limit/buy_stop/sell_stop` | `V1-WF-TRADING-004` | Test/example-only | Questionable | No production caller found |
| `V1-CAP-TRADING-016` | Position open/close/modify | `Trade.position_open/close/modify` | `V1-WF-TRADING-004` | Test/example-only | Questionable | No public partial close |
| `V1-CAP-TRADING-017` | Pending order modify/cancel | `Trade.order_modify/order_delete` | `V1-WF-TRADING-004` | Test/example-only | Questionable | No production caller found |
| `V1-CAP-TRADING-018` | Startup and forced reconciliation | `ReconciliationService`, `Trade` | `V1-WF-TRADING-004`, `006` | Test-only | Supporting | Incomplete correction semantics |
| `V1-CAP-TRADING-019` | Emergency kill switch | `Trade.set_kill_switch` | `V1-WF-TRADING-005` | Test-only | Questionable | Cleanup errors not returned |
| `V1-CAP-TRADING-020` | Graceful shutdown gate | `Trade.shutdown` | `V1-WF-TRADING-005` | Test-only | Questionable | Sticky global state |
| `V1-CAP-TRADING-021` | Local trading report | `ReportingService.build_report` | `V1-WF-TRADING-006` | Test-only | No demonstrated value | Isolated from runtime |
| `V1-CAP-TRADING-022` | Package export standardization | `__init__.py` | Dynamic/unknown | Possibly used | Supporting | Runtime registry could not be observed |

## 14. Audit Conclusions

### Valuable behaviour worth preserving in a future comparison

The following Version 1 behaviours have confirmed runtime value:

* **Strategy lifecycle permission enforcement** across backtest, optimization and live loading.
* **Stateful strategy snapshots and context** as the simulation-to-strategy input boundary.
* **Provider-independent trade actions** emitted by strategies and interpreted by simulation.
* **Stateful mixin opt-in flag and default callbacks**, used by multiple strategy implementations.
* The concepts represented by idempotency, serialization, readiness, validation, rate limiting, timeout handling, reconciliation and trace identifiers are materially relevant, although their current implementation is not confirmed in production.

### Behaviour that exists but is disconnected

* The package's `Trade` gateway and its safety pipeline.
* Broker account, terminal, symbol, position, order, history and deal facades.
* The in-memory store and result normalization surface.
* Emergency kill switch and shutdown implementation.
* Local reporting.

These are demonstrated by tests and the usage script, but not by confirmed production call paths.

### Likely dead weight or low-value surface

No item is declared dead code because dynamic export discovery could not be executed. The strongest low-value candidates are:

* `ReportingService`, currently test-only and disconnected.
* `StatefulStrategyProtocol`, with no external static reference.
* `TradeAction.hold`, with no call site.
* Hard-coded compatibility methods such as `SymbolInfo.is_synchronized`, `trade_mode_description`, `AccountInfo.margin_so_mode`, and `free_margin_mode`.
* `test_trader_extra.py`, which is not meaningful verification.
* Stale README paths and examples.

### Duplicated responsibilities

* Full trading mutation and information capabilities overlap with `app/services/execution/trading.py`.
* Active and historical order wrappers duplicate almost all logic.
* Named property accessors duplicate generic numeric property accessors.
* Result access is duplicated between object attributes, `to_dict`, and `Trade.result_*`.

### Important uncertainties

* Whether an agent/tool loader dynamically invokes package exports created by `standardize_domain_exports`.
* Whether deployments import this package indirectly through configuration strings that are not indexed as Python calls.
* Whether a non-repository entry point or external consumer invokes `app.services.trading.Trade`.
* Whether broker adapters guarantee return shapes assumed by the wrappers and normalizer.
* Whether the current tests pass against the repository's installed dependency versions.

### Manual confirmation required

1. Inspect the actual runtime composition root and deployed process command to confirm which `Trade` implementation is instantiated.
2. Inspect tool/agent discovery code at runtime to determine whether standardized class exports are callable.
3. Verify live broker timeout behaviour and whether provider calls can be safely cancelled.
4. Confirm intended ticket semantics for deal, order and position IDs.
5. Confirm whether local store data is intentionally ephemeral.
6. Confirm whether reconciliation is intended to authorize trading despite unresolved mismatches.
7. Run the actual unit suite and collect coverage; do not count `test_trader_extra.py` as meaningful coverage without revision.

### Final validation

* Every Python file identified in the package export/import surface is represented.
* All 38 `__init__.py` exports were checked against code.
* The additional public `StrategyRuntimeContext` alias was identified.
* Callers were searched across available repository code.
* Production callers are distinguished from tests/examples.
* Inbound and outbound dependency surfaces are summarized.
* Workflows are based on actual call paths.
* Uncertain findings are labelled.
* No Version 2 requirement or redesign was introduced.
* No repository code was modified.
