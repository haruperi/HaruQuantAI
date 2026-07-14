# Strategy — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** Strategy
* **Repository:** `haruperi/HaruQuant`
* **Repository snapshot:** `main` at commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/strategy`
* **Requested tests path:** `ttests/unit/app/services/strategy`
* **Actual tests path:** `tests/unit/app/services/strategy`
* **Requested known caller:** `tests/usage/app/services/04_strategy.py`
* **Actual usage-example paths found:**
  * `tests/usage/app/services/strategy/registry.py`
  * `tests/usage/app/services/strategy/stateful_common.py`
* **Current package files inspected:**
  * `app/services/strategy/__init__.py`
  * `app/services/strategy/base.py`
  * `app/services/strategy/registry.py`
  * `app/services/strategy/stateful_common.py`
  * `app/services/strategy/storage.py`
  * `app/services/strategy/template_strategy.py`
* **Tests inspected:**
  * `tests/unit/app/services/strategy/test_strategy_standard.py`
  * `tests/unit/app/services/strategy/test_strategy.py`
  * `tests/unit/app/services/strategy/test_strategy_service.py`
  * `tests/unit/app/services/strategy/test_pybots_coverage.py`
  * `tests/unit/app/services/strategy/pybots/test_pybots_extra.py`
  * Additional strategy-test references were searched repository-wide.
* **Related packages searched:**
  * `data/strategies`
  * `app/services/simulation`
  * `app/services/execution/live`
  * `app/services/optimization`
  * `app/services/trading`
  * `app/api/routes`
  * `app/api/session`
  * `app/services/data`
  * `tests/usage`
* **Generated files, caches, environments, and unrelated services:** Excluded.
* **Audit limitations:**
  * The GitHub connector permitted exact file reads and repository-wide code search but did not provide a raw recursive directory listing. The six-file current package boundary was reconstructed from exact file fetches, package exports, module searches, and negative exact-path checks for removed modules.
  * The repository could not be cloned into the execution environment, so tests were not run.
  * Dynamic imports created from arbitrary stored strategy files cannot be exhaustively traced statically.
  * Agent/tool discovery outside the checked `__all__`, standardization hooks, and repository call sites could not be proven at runtime.
  * The requested `tests/usage/app/services/04_strategy.py` does not exist at the audited snapshot.
  * Several existing tests import removed paths such as `app.services.strategy.pybots`, `app.services.strategy.config`, and `app.services.strategy.state`. These tests describe an older strategy implementation and are not evidence of current production behavior.

### Counting convention

The comparable public-symbol count includes externally meaningful classes, typed contracts, functions, class methods, schema constants, and global service instances. Repeated module-level tool-manifest constants such as `TOOL_NAME`, `READ_ONLY`, and `PLACES_TRADE` are documented but excluded from the public-behavior metric because they describe every tool module rather than provide domain behavior. Private helpers and dunder methods are excluded.

## 2. Executive Summary

The current Version 1 strategy package provides four primary capabilities:

1. A minimal abstract strategy contract based on pandas `DataFrame` signal columns.
2. A process-local registry that resolves nine hard-coded built-in strategy classes.
3. Shared helpers for signal-column preparation and portfolio-aware stateful strategies.
4. File-based storage, versioning, archive import/export, and dynamic loading of custom strategy classes.

The strongest operational workflow is simulation. `SimulationDataPreparer._run_strategy()` resolves a strategy through `get_strategy_class()`, instantiates it, runs `on_init()`, then runs `on_bar()` to produce signal-ready bars. Stateful strategies are subsequently invoked through `on_event()` by the event-driven simulator, using helpers from `stateful_common.py`. A second confirmed workflow uses `BaseStrategy.on_bar()` and `get_signal()` through `app/services/execution/live/signal_processor.py` for rolling-bar signal detection. File-backed custom strategies are also consumed by API, backtest, optimization, session, and live-execution code.

The most important structural problems are:

* The package-level API returns standardized response envelopes, while direct module imports return raw Python values under the same symbol names.
* The actual stateful lifecycle is split between `BaseStrategy` and `app/services/trading/stateful.py`; `on_event()` is not part of `BaseStrategy`, while several base lifecycle hooks have no confirmed caller.
* `TemplateStrategy` duplicates the canonical signal-column schema instead of using `ensure_signal_columns()`.
* File storage combines path migration, version storage, archive handling, code execution, and strategy discovery in one class.
* Database, governance, and filesystem updates are not transactional.
* Existing tests partly target a removed, incompatible strategy framework, reducing confidence that the full current test directory collects successfully.

The evidence is strong for static structure and the main call paths, medium for dynamic/custom strategy use, and limited for runtime success because the test suite was not executed.

```text
Module folders: 0 current subfolders | Files: 6 | Public symbols: 56 | Symbols with confirmed callers: 39 (70%) | Workflows found: 5
```

> Note: Current tests still reference a removed `strategy/pybots` subtree, but exact current-path fetches for that subtree return no files. It is therefore not counted as current package structure.

## 3. Actual Package Structure

```text
app/services/strategy
├── __init__.py
│   ├── Package exports
│   │   ├── BaseStrategy
│   │   ├── SignalDict
│   │   ├── SignalIntent
│   │   ├── StrategyEvent
│   │   ├── StrategyClass
│   │   ├── StrategyRegistryError
│   │   ├── StrategyStorage
│   │   ├── TemplateStrategy
│   │   └── storage
│   └── Standardized AI-tool exports
│       ├── basket_pnl
│       ├── current_mid_price
│       ├── ensure_no_signal_columns
│       ├── ensure_signal_columns
│       ├── historical_mid_prices
│       ├── is_bar_close
│       ├── oldest_position
│       ├── positions_for_side
│       ├── rolling_rsi
│       ├── rolling_sma
│       ├── weighted_average_price
│       ├── get_strategy_class
│       ├── list_strategy_names
│       ├── register_builtin_strategies
│       ├── register_strategy
│       └── registered_strategies
├── base.py
│   ├── SignalDict
│   ├── StrategyEvent
│   ├── SignalIntent
│   └── BaseStrategy
│       ├── on_init
│       ├── on_tick
│       ├── on_trade
│       ├── on_order_update
│       ├── on_timer
│       ├── on_shutdown
│       ├── on_bar
│       ├── get_signal
│       ├── get_indicator_value
│       ├── crossover
│       └── crossunder
├── registry.py
│   ├── StrategyRegistryError
│   ├── StrategyClass
│   ├── register_strategy
│   ├── get_strategy_class
│   ├── list_strategy_names
│   ├── registered_strategies
│   └── register_builtin_strategies
├── stateful_common.py
│   ├── SIGNAL_COLUMN_DEFAULTS
│   ├── ACTIVATOR_COLUMN_DEFAULTS
│   ├── ensure_signal_columns
│   ├── ensure_no_signal_columns
│   ├── is_bar_close
│   ├── current_mid_price
│   ├── historical_mid_prices
│   ├── rolling_rsi
│   ├── rolling_sma
│   ├── positions_for_side
│   ├── basket_pnl
│   ├── weighted_average_price
│   └── oldest_position
├── storage.py
│   ├── StrategyStorage
│   │   ├── save_strategy
│   │   ├── load_strategy_code
│   │   ├── load_strategy_metadata
│   │   ├── load_strategy_class
│   │   ├── delete_strategy
│   │   ├── delete_strategy_version
│   │   ├── export_strategy
│   │   ├── import_strategy
│   │   ├── list_versions
│   │   ├── get_strategy_path
│   │   └── get_strategy_artifact_root
│   └── storage
└── template_strategy.py
    └── TemplateStrategy
        ├── strategy_name
        ├── strategy_type
        ├── signal_schema_version
        ├── action_schema_version
        ├── on_init
        ├── on_bar
        └── get_signal
```

### Package entry points and registration mechanisms

* `app/services/strategy/__init__.py` is the package entry point.
* `standardize_domain_exports(globals(), __all__, tool_category="strategy")` wraps the 16 names in `__all__`.
* `__getattr__()` lazily exposes stateful helpers and storage objects and wraps lazy callable tools through `standardize_tool_callable()`.
* `registry.py` uses an in-memory dictionary, `_STRATEGIES`, and lazy hard-coded built-in registration.
* `storage.py` dynamically imports saved `strategy.py` files with `importlib.util.spec_from_file_location()`.
* `data/strategies/__init__.py` re-exports `StrategyStorage` and the global `storage` instance.
* No command-line entry point or scheduler owned by this package was found.

## 4. Module and File Inventory

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| Package API | `__init__.py` | Re-export compatibility types and expose standardized strategy tools | Sixteen tools plus base, registry, storage, and template compatibility exports | **Standard library:** `importlib` lazily. **Required third-party:** None. **Local:** `utils.logger`, `utils.standard`, all strategy modules | Used | Essential |
| Core contract | `base.py` | Define the DataFrame-based strategy lifecycle, signal contracts, and common signal extraction helpers | `BaseStrategy`, `SignalDict`, `StrategyEvent`, `SignalIntent` | **Standard library:** `abc`, `typing`. **Required third-party:** `pandas`. **Local:** `utils.logger`; execution types under `TYPE_CHECKING` | Used | Essential |
| Registry | `registry.py` | Register and resolve built-in or process-local strategy classes by name | `get_strategy_class`, registration/listing functions, `StrategyRegistryError` | **Standard library:** `collections.abc`. **Required third-party:** None. **Local:** `BaseStrategy`, logger, nine `data.strategies.baselines` classes | Used | Essential |
| Shared strategy helpers | `stateful_common.py` | Prepare signal schemas and calculate stateful strategy values from market/portfolio context | Two schema constants and eleven helpers | **Standard library:** `math`, `numbers`, `collections.abc`, `typing`. **Required third-party:** `pandas`. **Local:** `trading.stateful.PositionSnapshot`, `StrategyContext`, logger | Used | Essential |
| File storage | `storage.py` | Store, version, load, delete, archive, and dynamically execute custom strategy artifacts | `StrategyStorage`, `storage` | **Standard library:** `importlib.util`, `json`, `shutil`, `datetime`, `pathlib`, `typing`. **Required third-party:** None. **Local:** `BaseStrategy`, logger | Used | Essential |
| Concrete template | `template_strategy.py` | Provide a basic moving-average crossover strategy and authoring template | `TemplateStrategy` | **Standard library:** `typing`. **Required third-party:** `pandas`. **Local:** `BaseStrategy`, `SignalDict`, logger | Test-only / inherited by old stored artifacts | Useful |

### Files with multiple responsibilities

* `storage.py` combines artifact persistence, path compatibility/migration, archive import/export, dynamic Python loading, class discovery, and global service construction.
* `__init__.py` combines compatibility re-exports with AI-tool response transformation.
* `base.py` combines contracts, lifecycle methods, signal decoding, indicator lookup, and crossover helpers, although these responsibilities remain closely related.

## 5. Public Behaviour Inventory

### `app/services/strategy/__init__.py`

**File responsibility:** Define the public package surface and transform selected raw functions into standardized AI-tool responses.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `__all__` tool exports | Package export set | Publish 16 approved strategy tools | Raw tool call plus wrapper metadata → standard response envelope | Local state mutation during wrapping | Wrapper-dependent | Tests, usage examples, possible agents | `test_strategy_standard.py`; usage examples | Used | Essential |
| Compatibility exports | Re-exports | Preserve direct access to base, registry, storage, and template symbols | Import → Python symbol | Module import side effects | Import errors | Strategies, simulation, execution, tests | Multiple | Used | Supporting |
| `__getattr__(name)` | Lazy package hook | Resolve stateful/storage compatibility exports and wrap callable tools | Name → object or wrapped callable | Local state mutation: caches resolved value in module globals; storage import can create directories | `AttributeError`, import errors | Python attribute access | Indirect | Used | Supporting |

**Important contract distinction:** Calling `app.services.strategy.ensure_signal_columns(...)` returns a standardized response envelope. Calling `app.services.strategy.stateful_common.ensure_signal_columns(...)` returns a raw `DataFrame`. The same applies to registry and other stateful helpers.

### `app/services/strategy/base.py`

**File responsibility:** Define the current strategy abstraction and convert strategy-generated DataFrame columns into canonical signal dictionaries.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SignalDict` | `TypedDict` | Shape of signal payloads emitted from DataFrame rows | Typed fields only | None | None | `TemplateStrategy`, `SignalProcessor`, type annotations | Indirect | Used | Essential |
| `StrategyEvent` | `TypedDict` | Intended lifecycle event payload | Typed fields only | None | None | Only `BaseStrategy` annotations and package export found | None specific | Unused | Questionable |
| `SignalIntent` | `TypedDict` | Intended execution-facing signal intent | Typed fields only | None | None | No caller or producer found | None | Unused | No demonstrated value |
| `BaseStrategy` | Abstract class | Common parent for built-in and stored strategies | `params` at construction | Local state mutation; logging | `TypeError` if instantiated abstractly | `data/strategies`, simulation, execution, storage | `test_strategy.py`; many indirect tests | Used | Essential |
| `on_init()` | Abstract method | Initialize concrete strategy state | None → `None` | Subclass-defined | Subclass-defined | `SimulationDataPreparer`, `Engine._build_runtime_strategy`, tests | Yes | Used | Essential |
| `on_tick(data)` | Method | Optional tick callback; default returns input unchanged | `DataFrame` → same `DataFrame` | None | None documented | No current runtime caller found | Older removed-framework tests reference unrelated methods | Unused | Questionable |
| `on_trade(event)` | Method | Intended trade lifecycle callback; default no-op | `StrategyEvent` → `None` | None | None | No caller found | None | Unused | No demonstrated value |
| `on_order_update(event)` | Method | Intended order lifecycle callback; default no-op | `StrategyEvent` → `None` | None | None | No confirmed caller matching this signature | Stale tests target a different signature | Possibly used | Questionable |
| `on_timer(event)` | Method | Intended timer callback; default no-op | `StrategyEvent` → `None` | None | None | No caller found | None | Unused | No demonstrated value |
| `on_shutdown(event=None)` | Method | Intended shutdown callback; default no-op | Optional event → `None` | None | None | No caller found | None | Unused | No demonstrated value |
| `on_bar(data)` | Abstract method | Calculate indicators and signal columns | OHLCV `DataFrame` → enriched `DataFrame` | Usually local DataFrame mutation/copy | Subclass-defined | Simulation preparation, live `SignalProcessor`, concrete strategies | `test_strategy.py` and cross-domain tests | Used | Essential |
| `get_signal(data, index)` | Method | Decode one row into a `SignalDict`; return `None` when neutral | `DataFrame`, integer index → `SignalDict \| None` | Read-only | Uncaught index/conversion errors possible | `SignalProcessor`, several baseline overrides delegate to it | Indirect | Used | Essential |
| `get_indicator_value(data, column, offset=0)` | Method | Retrieve recent indicator value with missing/NaN fallback | `DataFrame`, column, offset → value or `None` | Read-only | Generally suppressed for missing columns/index | No caller found | No focused test | Unused | Questionable |
| `crossover(series1, series2)` | Method | Detect latest two-bar bullish cross | Two series → `bool` | Read-only | Pandas comparison errors may propagate | No caller found | No focused test | Unused | No demonstrated value |
| `crossunder(series1, series2)` | Method | Detect latest two-bar bearish cross | Two series → `bool` | Read-only | Pandas comparison errors may propagate | No caller found | No focused test | Unused | No demonstrated value |

**Observed behavior notes:**

* The constructor inserts `symbol="UNKNOWN"` when absent.
* `get_signal()` checks entry, exit, pending, cancellation, and optional second-leg columns.
* `price` falls back to `close`; `stop_loss` falls back to `sl`; `take_profit` falls back to `tp`.
* Invalid row indexes and invalid numeric signal values are not normalized into a domain exception.

### `app/services/strategy/registry.py`

**File responsibility:** Maintain a process-local name-to-class registry and lazily register nine built-in strategies.

**Tool metadata constants:** `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_RISK_LEVEL`, `REQUIRES_APPROVAL`, `READ_ONLY`, `WRITES_FILE`, `MODIFIES_DATABASE`, `PLACES_TRADE`, and `REQUIRES_NETWORK`. They identify this as a low-risk, read-only, local strategy tool. These constants have no direct business workflow.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `StrategyRegistryError` | Exception | Report invalid or unknown strategy names | Raised only | None | N/A | Registry and simulation engine | Unit tests indirectly | Used | Supporting |
| `StrategyClass` | Type alias | Type strategies as `type[BaseStrategy]` | Type annotation | None | None | Registry annotations/package export | None | Possibly used | Supporting |
| `register_strategy(name, strategy_cls)` | Function | Validate and store a class under a normalized name | Name/class → `None` | Local state mutation | `StrategyRegistryError`, `TypeError` | Built-in registration, tests, possible dynamic agent use | `test_strategy_standard.py` | Used | Supporting |
| `get_strategy_class(name)` | Function | Resolve process-local or built-in class | Name → class | May trigger lazy registration | `StrategyRegistryError` | Simulation data preparation and engine | `test_strategy_standard.py` | Used | Essential |
| `list_strategy_names()` | Function | Return sorted registered names | None → tuple | May trigger registration | Import/registration errors | Usage example, unit test, simulation package export | `test_strategy_standard.py` | Test-only / exposed | Useful |
| `registered_strategies()` | Function | Return shallow registry copy | None → dict | May trigger registration | Import/registration errors | Unit test and possible diagnostics | `test_strategy_standard.py` | Test-only / exposed | Useful |
| `register_builtin_strategies()` | Function | Import and register nine baseline classes | None → `None` | Local state mutation and imports | Import/type errors | Internal lazy registration; package tool exposure | Indirect | Used | Essential |

**Built-in class dependencies:**

* `TrendFollowingStrategy`
* `CloseBreakoutStrategy`
* `RsiMartingaleStrategy`
* `PyramidingStrategy`
* `TradeDecompositionStrategy`
* `RsiAveragingPyramidStrategy`
* `StructureHedgeTrailStrategy`
* `RsiDecomposingReentryStrategy`
* `MarketStructureHedgeGridStrategy`

### `app/services/strategy/stateful_common.py`

**File responsibility:** Provide a shared signal schema and read-only calculations for DataFrame-based and stateful strategies.

**Tool metadata constants:** Same ten manifest fields as `registry.py`, declaring a low-risk, read-only, local tool module.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SIGNAL_COLUMN_DEFAULTS` | Constant dict | Canonical signal, price, protection, reason, setup, and group defaults | N/A | Mutable global object | None | `ensure_signal_columns()` | Indirect | Used | Essential |
| `ACTIVATOR_COLUMN_DEFAULTS` | Constant dict | Canonical stateful event-activator defaults | N/A | Mutable global object | None | Both schema functions | Indirect | Used | Essential |
| `ensure_signal_columns(data, include_activators=False, include_compat_columns=True)` | Function | Copy data and add missing canonical columns | `DataFrame` → copied `DataFrame` | None | Attribute/type errors for invalid input | Baseline strategies; data generation; template-equivalent behavior | Standard and usage tests | Used | Essential |
| `ensure_no_signal_columns(data)` | Function | Force all strategy fields to neutral values | `DataFrame` → copied neutral `DataFrame` | None | Propagated DataFrame errors | Seven stateful baseline strategies | Standard tests | Used | Essential |
| `is_bar_close(context)` | Function | Decode boolean, numeric bitmask, or pipe-delimited close phase | `StrategyContext` → `bool` | Read-only | Conversion errors unlikely but possible | Stateful baseline strategies | Standard tests | Used | Essential |
| `current_mid_price(context)` | Function | Calculate bid/ask midpoint with one-sided fallback | Context → `float` | Read-only | Numeric conversion errors | Stateful baseline strategies | Standard tests | Used | Essential |
| `historical_mid_prices(context)` | Function | Build midpoint history through current tick index | Context → `Series` | Read-only | Index/type conversion errors | Stateful baseline strategies | Standard tests | Used | Essential |
| `rolling_rsi(prices, period)` | Function | Calculate latest EWM RSI | Series/period → float or `None` | Read-only | Invalid period/pandas errors | RSI stateful strategies | Standard tests | Used | Essential |
| `rolling_sma(prices, period)` | Function | Calculate latest rolling mean | Series/period → float or `None` | Read-only | Invalid period/pandas errors | Tests/usage and baseline imports | Standard and usage tests | Used | Useful |
| `positions_for_side(context, side)` | Function | Filter current-symbol positions by side | Context/side → list | Read-only | Context contract errors | Stateful baseline strategies | Standard tests | Used | Essential |
| `basket_pnl(positions)` | Function | Sum basket profit/loss | Iterable → float | Read-only | Attribute/conversion errors | `RsiMartingaleStrategy` and other basket strategies | Standard tests | Used | Essential |
| `weighted_average_price(positions)` | Function | Volume-weight average entry prices | Iterable → float or `None` | Read-only | Attribute/conversion errors | Basket/stateful strategies; tests | Standard tests | Used | Useful |
| `oldest_position(positions)` | Function | Select earliest position by stringified `opened_at` | Iterable → position or `None` | Read-only | Attribute errors | Tests and potential stateful strategies | Standard tests | Used | Useful |

### `app/services/strategy/storage.py`

**File responsibility:** Persist versioned strategy source and metadata, resolve legacy/stable paths, import/export archives, and dynamically load a `BaseStrategy` subclass.

**Tool metadata constants:** Same ten manifest fields, declaring medium risk, filesystem writes, no direct database or broker mutation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `StrategyStorage` | Class | Coordinate file-backed strategy artifacts | Optional base directory → instance | Persistence write: creates base directory | Filesystem errors | API, optimization, backtest, live/session code | No current focused storage test found | Used | Essential |
| `save_strategy(...)` | Method | Write `strategy.py` and `metadata.json` for a version | Identity, version, code, metadata → file path | Persistence write | Filesystem/serialization errors | `StrategyCatalogService` | No focused test found | Used | Essential |
| `load_strategy_code(...)` | Method | Read stored Python source | Identity/version/path fields → string | Read-only | `FileNotFoundError`, filesystem errors | Strategy API | No focused test found | Used | Essential |
| `load_strategy_metadata(...)` | Method | Read metadata or return empty dict when absent | Identity/version/path fields → dict | Read-only | JSON/filesystem errors | Strategy API/import flow | No focused test found | Used | Supporting |
| `load_strategy_class(...)` | Method | Execute stored Python module and find first `BaseStrategy` subclass | Identity/version/path fields → class | Read-only filesystem access plus dynamic code execution and module-state mutation | `FileNotFoundError`, `ImportError`, `ValueError`, arbitrary import-time exceptions | Session, simulator, backtest, optimization, live execution | No focused current test found | Used | Essential |
| `delete_strategy(...)` | Method | Remove all stable/legacy directories for one strategy | Identity/path fields → `None` | Persistence write | Filesystem errors | Strategy API | No focused test found | Used | Essential |
| `delete_strategy_version(...)` | Method | Remove one version directory | Identity/version/path fields → `None` | Persistence write | Filesystem errors | No confirmed `StrategyStorage` caller | None | Unused | Questionable |
| `export_strategy(...)` | Method | Zip one version directory | Identity/version/export path → zip path | Persistence write | `FileNotFoundError`, archive errors | Strategy API | No focused test found | Used | Useful |
| `import_strategy(...)` | Method | Unpack archive into a new version and require `strategy.py` | Identity/version/archive path → strategy path | Persistence write | `FileNotFoundError`, archive errors | Strategy API | No focused test found | Used | Useful |
| `list_versions(username="", strategy_name="")` | Method | Scan stable-name and legacy directories for version folders | Username/name → list of strings | Read-only | Path/validation errors | No confirmed caller of this storage method | None | Unused | Questionable |
| `get_strategy_path(...)` | Method | Resolve absolute source path | Identity/version/path fields → path string | Read-only | Path validation errors | Optimization | No focused test found | Used | Supporting |
| `get_strategy_artifact_root(...)` | Method | Resolve preferred strategy root | Identity/path fields → path string | Read-only | Path validation errors | Strategy API/catalog | No focused test found | Used | Supporting |
| `storage` | Global instance | Shared storage service | Import → initialized instance | Persistence write at import: creates `data/strategies` | Filesystem errors | `data.strategies`, strategy API | Indirect | Used | Essential |

### `app/services/strategy/template_strategy.py`

**File responsibility:** Provide a concrete moving-average crossover template compatible with the current DataFrame signal contract.

**Tool metadata constants:** Same ten manifest fields, declaring a low-risk, read-only strategy component.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TemplateStrategy` | Class | Basic SMA crossover example/template | Params → strategy instance | Local state mutation | Parameter validation errors | Unit test; older saved strategy artifacts inherit it | `test_strategy.py` | Test-only / stored-artifact dependency | Useful |
| `strategy_name` | Class constant | Human-readable identity | N/A | None | None | Internal logging | Indirect | Used internally | Supporting |
| `strategy_type` | Class constant | Mark template as `simple` | N/A | None | None | No external caller found | None | Possibly used | Supporting |
| `signal_schema_version` | Class constant | Declare signal schema version | N/A | None | None | No external caller found | None | Possibly used | Supporting |
| `action_schema_version` | Class constant | Declare action schema version | N/A | None | None | No external caller found | None | Possibly used | Supporting |
| `on_init()` | Method | Log selected symbol and periods | None → `None` | Logging | None | Unit test; inherited artifact workflows | `test_strategy.py` | Test-only / indirect | Useful |
| `on_bar(data)` | Method | Calculate lagged SMAs, create signals, and activators | OHLCV `DataFrame` → enriched copy | Local DataFrame mutation | Missing-column/pandas errors | Unit test; inherited artifact workflows | `test_strategy.py` | Test-only / indirect | Useful |
| `get_signal(data, index)` | Method | Delegate row decoding to `BaseStrategy` | Data/index → signal or `None` | Read-only | Base errors | Inherited use; no template-specific caller | Indirect | Possibly used | Supporting |

**Observed validation gap:** omitted `symbol` becomes `"UNKNOWN"` in `BaseStrategy`, so `TemplateStrategy._validate_params()` does not actually enforce a meaningful symbol despite the error text saying that a symbol must be provided.

## 6. Actual Workflows

### `V1-WF-STRATEGY-001` — Built-in Strategy Signal Preparation for Simulation

* **Scope:** Cross-domain
* **Trigger:** `SimulationRunner`/`Engine.run()` receives a simulation configuration.
* **Input boundary:** Strategy name and parameters from `SimulationConfig`, plus OHLCV bars.
* **Functions and methods used:**
  * `registry.get_strategy_class()`
  * concrete `BaseStrategy` constructor
  * `BaseStrategy.on_init()` override
  * `BaseStrategy.on_bar()` override
* **Files involved:**
  * `app/services/strategy/registry.py`
  * `app/services/strategy/base.py`
  * one of nine `data/strategies/baselines/*.py`
  * `app/services/simulation/data_preparation.py`
* **External dependencies:** pandas; market-data source selected by simulation.
* **Output boundary:** Signal-enriched bars passed to `TicksGenerator`, then to the selected simulation engine.
* **Failure behaviour:**
  * Unknown names raise `StrategyRegistryError`.
  * Import failures can escape from built-in registration.
  * Empty strategy output raises `SimulationDataPreparationError`.
* **Operational status:** Working code path; runtime execution not independently verified during this audit.
* **Evidence:**
  * `SimulationDataPreparer._run_strategy()` in `app/services/simulation/data_preparation.py`
  * `get_strategy_class()` in `app/services/strategy/registry.py`

```text
SimulationConfig
→ SimulationDataPreparer.prepare_symbol()
→ get_strategy_class(config.strategy.name)
→ strategy_cls(params)
→ strategy.on_init()
→ strategy.on_bar(bars)
→ signal-ready bars
→ tick generation
→ simulation engine
```

### `V1-WF-STRATEGY-002` — Stateful Portfolio-Aware Strategy Execution

* **Scope:** Cross-domain
* **Trigger:** Each eligible tick/bar phase in the event-driven simulator.
* **Input boundary:** `StrategyContext` containing current tick, market history, positions, orders, account state, and metadata.
* **Functions and methods used:**
  * `Engine._build_runtime_strategy()`
  * registry resolution and `on_init()`
  * stateful strategy `on_event(context)`
  * helpers such as `is_bar_close()`, `historical_mid_prices()`, `rolling_rsi()`, `current_mid_price()`, `positions_for_side()`, and `basket_pnl()`
* **Files involved:**
  * `app/services/strategy/registry.py`
  * `app/services/strategy/stateful_common.py`
  * `app/services/trading/stateful.py`
  * `app/services/simulation/engine.py`
  * `app/services/simulation/event_driven.py`
  * stateful classes in `data/strategies/baselines`
* **External dependencies:** pandas; simulation trading state.
* **Output boundary:** `TradeAction` objects passed to `Engine._apply_trade_actions()`.
* **Failure behaviour:**
  * `Engine._build_runtime_strategy()` catches `ImportError` and `StrategyRegistryError` and returns `None`.
  * Strategy helper errors and `on_event()` errors are not converted into a strategy-domain exception in the shown loop.
* **Operational status:** Working code path; not executed during audit.
* **Evidence:**
  * `RsiMartingaleStrategy.on_event()` in `data/strategies/baselines/rsi_martingale.py`
  * stateful branch in `app/services/simulation/event_driven.py`

```text
Configured stateful strategy
→ registry resolution
→ strategy.on_init()
→ event-driven tick loop
→ Engine._build_strategy_context()
→ strategy.on_event(context)
→ stateful_common helper calculations
→ list[TradeAction]
→ Engine._apply_trade_actions()
→ simulated order/position changes
```

### `V1-WF-STRATEGY-003` — Rolling-Bar Live Signal Detection

* **Scope:** Cross-domain
* **Trigger:** Live signal processor initialization or receipt of a new completed bar.
* **Input boundary:** Concrete `BaseStrategy` instance and historical/new OHLCV bars.
* **Functions and methods used:**
  * `strategy.on_bar()`
  * `strategy.get_signal()`
* **Files involved:**
  * `app/services/strategy/base.py`
  * a concrete strategy class
  * `app/services/execution/live/signal_processor.py`
* **External dependencies:** pandas; caller-provided market bars.
* **Output boundary:** `SignalDict` returned to the live execution layer.
* **Failure behaviour:** `SignalProcessor` broadly catches exceptions, logs them, and returns `False` or `None`.
* **Operational status:** Working code path; downstream order routing was outside this workflow slice.
* **Evidence:** `SignalProcessor.initialize()`, `update_with_new_bar()`, and `get_last_signal()`.

```text
Historical bars + strategy
→ SignalProcessor.initialize()
→ strategy.on_bar()
→ new bar arrives
→ strategy.on_bar(updated window)
→ strategy.get_signal(last row)
→ SignalDict or None
→ live execution caller
```

### `V1-WF-STRATEGY-004` — Strategy Catalog and Versioned Artifact Management

* **Scope:** Cross-domain
* **Trigger:** Strategy API create, edit, read-version, delete, export, or import operation.
* **Input boundary:** User identity, strategy metadata, Python source, parameters, or archive.
* **Functions and methods used:**
  * `storage.save_strategy()`
  * `load_strategy_code()`
  * `load_strategy_metadata()`
  * `delete_strategy()`
  * `export_strategy()`
  * `import_strategy()`
  * `get_strategy_artifact_root()`
* **Files involved:**
  * `app/services/strategy/storage.py`
  * `data/strategies/__init__.py`
  * `app/api/routes/strategies.py`
  * database and governance repositories
* **External dependencies:** Local filesystem, SQLite/database service, governance repository, FastAPI.
* **Output boundary:** Versioned source/metadata files, database version rows, governance metadata, API responses/files.
* **Failure behaviour:**
  * Storage methods log and re-raise.
  * Cross-store operations have no visible transaction/compensation boundary.
  * A database or governance failure can leave filesystem artifacts, and a filesystem failure can leave database rows.
* **Operational status:** Partial: the full feature path exists, but atomicity is incomplete.
* **Evidence:** `StrategyCatalogService.create_strategy()`, `create_strategy_version()`, `delete_strategy()`, `get_version_code()`, `export_strategy()`, and `import_strategy()`.

```text
API request
→ database ownership/catalog operation
→ StrategyStorage filesystem operation
→ database version operation
→ governance update
→ API response
```

### `V1-WF-STRATEGY-005` — Dynamic Custom Strategy Loading for Runtime and Optimization

* **Scope:** Cross-domain
* **Trigger:** Backtest, simulator, optimization, live-session, or live-engine request for a stored strategy version.
* **Input boundary:** User/strategy/version identity and stored `strategy.py`.
* **Functions and methods used:**
  * `StrategyStorage.load_strategy_class()`
  * `StrategyStorage.get_strategy_path()` for optimization
  * dynamically discovered `BaseStrategy` subclass
* **Files involved:**
  * `app/services/strategy/storage.py`
  * `app/services/optimization/core.py`
  * `app/api/routes/backtest.py`
  * `app/api/routes/simulator.py`
  * `app/api/session/session_service.py`
  * `app/services/execution/live/engine.py`
* **External dependencies:** Local filesystem, dynamic Python imports, database-provided active version and username.
* **Output boundary:** Concrete class used by optimization or execution workflows.
* **Failure behaviour:**
  * Missing source raises `FileNotFoundError`.
  * Invalid module spec raises `ImportError`.
  * No subclass raises `ValueError`.
  * Arbitrary import-time errors from stored code propagate.
  * If more than one subclass exists, the first class encountered in `dir(module)` is selected.
* **Operational status:** Working code path; dynamic behavior is unverified.
* **Evidence:** `run_optimization_task()` in `app/services/optimization/core.py` and repository-wide callers of `load_strategy_class()`.

```text
Catalog active version
→ resolve filesystem path
→ importlib executes strategy.py
→ scan module members
→ first BaseStrategy subclass
→ instantiate/use in backtest, optimization, session, or live runtime
```

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `BaseStrategy` | Numerous `data/strategies/baselines` and saved strategies; `SignalProcessor`; registry/storage type checks | Inheritance/type contract | Runtime | Imports and subclass definitions |
| `SignalDict` | `TemplateStrategy`, live `SignalProcessor` | Type contract | Runtime | Direct imports |
| `StrategyEvent` | Base lifecycle annotations only | Annotation | Internal only | No repository caller found |
| `SignalIntent` | No caller found | None | None | Exact symbol search found only definition/export |
| `on_init()` | Simulation preparer, engine runtime strategy builder | Direct method call | Runtime | `_run_strategy()`, `_build_runtime_strategy()` |
| `on_tick()` | No current runtime call found | None | None | Repository call search returned no runtime hit |
| `on_trade()` | No call found | None | None | Repository call search returned no hit |
| `on_order_update()` | Stateful protocol has a differently defined method; no confirmed matching call | Possible callback | Unknown | Contract mismatch |
| `on_timer()` | No call found | None | None | Static search |
| `on_shutdown()` | No call found | None | None | Static search |
| `on_bar()` | Simulation preparer; live `SignalProcessor` | Direct method call | Runtime | Cross-domain files |
| `get_signal()` | Live `SignalProcessor`; baseline overrides delegate to base | Direct/override | Runtime | Repository call search |
| `get_indicator_value()` | No caller found | None | None | Exact call search |
| `crossover()` | No caller found | None | None | Exact call search |
| `crossunder()` | No caller found | None | None | Exact call search |
| `StrategyRegistryError` | Registry and simulation engine | Raise/catch | Runtime | `registry.py`, `engine.py` |
| `StrategyClass` | Registry annotations/package compatibility export | Type annotation | Internal | Definition/imports |
| `register_strategy()` | Built-in loader; standard test | Direct call | Runtime + test | `registry.py`, `test_strategy_standard.py` |
| `get_strategy_class()` | Simulation data preparation and engine | Direct call | Runtime | `data_preparation.py`, `engine.py` |
| `list_strategy_names()` | Usage example, unit test, simulation package export | Direct/package-wrapped | Test/example; possibly dynamic | `tests/usage/.../registry.py` |
| `registered_strategies()` | Unit test | Package-wrapped | Test | `test_strategy_standard.py` |
| `register_builtin_strategies()` | Internal lazy loader | Direct call | Runtime | `_ensure_builtin_strategies_registered()` |
| `SIGNAL_COLUMN_DEFAULTS` | `ensure_signal_columns()` | Constant read/copy | Runtime | `stateful_common.py` |
| `ACTIVATOR_COLUMN_DEFAULTS` | Both schema functions | Constant read | Runtime | `stateful_common.py` |
| `ensure_signal_columns()` | Baseline strategies and data generation | Direct raw call | Runtime | `data/strategies/baselines`, `app/services/data/generators.py` |
| `ensure_no_signal_columns()` | Stateful baseline strategies | Direct raw call | Runtime | Seven baseline files |
| `is_bar_close()` | Stateful baseline strategies | Direct raw call | Runtime | `rsi_martingale.py` and others |
| `current_mid_price()` | Stateful baseline strategies | Direct raw call | Runtime | `rsi_martingale.py` and others |
| `historical_mid_prices()` | Stateful baseline strategies | Direct raw call | Runtime | `rsi_martingale.py` and others |
| `rolling_rsi()` | RSI stateful strategies | Direct raw call | Runtime | `rsi_martingale.py` |
| `rolling_sma()` | Usage example/tests and baseline imports | Direct/package-wrapped | Runtime/test | Search/import evidence |
| `positions_for_side()` | Stateful baseline strategies | Direct raw call | Runtime | `rsi_martingale.py` |
| `basket_pnl()` | Basket strategies | Direct raw call | Runtime | `rsi_martingale.py` |
| `weighted_average_price()` | Stateful/basket code and tests | Direct raw/package-wrapped | Runtime/test | Import/test evidence |
| `oldest_position()` | Tests and possible stateful callers | Package-wrapped/raw | Test / possibly runtime | Standard test and import search |
| `StrategyStorage` | Optimization; `data.strategies` export | Instantiation/export | Runtime | `optimization/core.py`, `data/strategies/__init__.py` |
| `save_strategy()` | Strategy catalog service | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `load_strategy_code()` | Strategy catalog version retrieval | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `load_strategy_metadata()` | Strategy catalog version/import retrieval | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `load_strategy_class()` | Session, simulator, backtest, optimization, live engine | Direct method call | Runtime | Repository-wide exact call search |
| `delete_strategy()` | Strategy catalog delete | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `delete_strategy_version()` | No confirmed storage caller | None | None | Exact call search only found definition and similarly named DB method |
| `export_strategy()` | Strategy catalog export | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `import_strategy()` | Strategy catalog import | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `list_versions()` | No confirmed call to `StrategyStorage.list_versions()` | None | None | Hits refer to API/DB methods, not storage method |
| `get_strategy_path()` | Optimization | Direct method call | Runtime | `optimization/core.py` |
| `get_strategy_artifact_root()` | Strategy catalog | Direct method call | Runtime | `app/api/routes/strategies.py` |
| `storage` | `data.strategies`, strategy route service | Shared instance | Runtime | Direct import |
| `TemplateStrategy` | Unit test and older stored strategy artifacts | Instantiation/inheritance | Test and dynamically loaded artifacts | `test_strategy.py`; stored files |
| Template class constants | Internal/template metadata | Attribute reads not confirmed externally | Internal/unknown | Definition only |
| `TemplateStrategy.on_init()` | Unit test and inherited artifact flow | Direct/virtual call | Test/dynamic | `test_strategy.py` |
| `TemplateStrategy.on_bar()` | Unit test and inherited artifact flow | Direct/virtual call | Test/dynamic | `test_strategy.py` |
| `TemplateStrategy.get_signal()` | Delegation path | Virtual method | Possible runtime | Definition/indirect |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.services.utils` | Logger and standard response wrappers | All files; package API | Direct imports |
| `pandas` | DataFrames, Series, rolling/EWM indicators, NaN handling | `base.py`, `stateful_common.py`, `template_strategy.py` | Direct imports |
| `app.services.trading.stateful` | `StrategyContext`, `PositionSnapshot` | `stateful_common.py` | Direct imports |
| `app.services.execution` | Execution information/trade types under `TYPE_CHECKING` | `base.py` | Type-only imports |
| `data.strategies.baselines` | Nine built-in strategy classes | `registry.py` | `_builtin_strategy_classes()` |
| Local filesystem | Strategy source, metadata, archives, path discovery | `storage.py` | `Path`, `open`, `shutil`, `importlib` |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| `data.strategies.baselines` | `BaseStrategy`, stateful helpers | Implement built-in signal and stateful strategies | Direct imports |
| Simulation | `get_strategy_class`, base lifecycle | Produce signals and run stateful strategies | `simulation/data_preparation.py`, `simulation/engine.py`, `simulation/event_driven.py` |
| Live execution | `BaseStrategy`, `SignalDict`; stored class loader | Rolling signal detection and custom strategy runtime | `execution/live/signal_processor.py`, `execution/live/engine.py` |
| Optimization | `StrategyStorage` | Load custom class/path for parameter optimization | `optimization/core.py` |
| API strategy catalog | global `storage` and storage methods | Create/update/read/delete/import/export versioned artifacts | `api/routes/strategies.py` |
| Backtest/simulator routes | `load_strategy_class()` | Load selected stored strategy | Repository call search |
| Session service | `load_strategy_class()` | Build session strategy runtime | Repository call search |
| Data generation | `ensure_signal_columns()` | Ensure strategy signal schema during tick generation | `services/data/generators.py` |
| Tests and usage examples | Package-wrapped tools and compatibility classes | Standard-response contract and examples | `tests/unit/...`, `tests/usage/...` |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `stateful_common.ensure_signal_columns()` | `TemplateStrategy._ensure_signal_columns()` | Both create nearly the same signal and activator columns | Defaults in both files | Schema drift; template omits default `sl`/`tp` compatibility columns |
| Package-level strategy tools | Direct module-level functions | Same names expose different return contracts: standard envelope versus raw object | `__init__.py` wrapping; baseline raw imports; standard tests | Callers can silently receive incompatible types based only on import path |
| `BaseStrategy` lifecycle | `StatefulStrategyMixin/Protocol` in trading domain | Both define strategy lifecycle concepts; actual stateful execution uses `on_event()` not declared by `BaseStrategy` | `base.py`, `trading/stateful.py`, `simulation/event_driven.py` | Fragmented contracts and unclear required interface |
| Registry-built strategies | File-backed dynamically loaded strategies | Two separate strategy discovery/activation mechanisms | `registry.py` versus `storage.py` | A strategy may be available in one workflow but not another |
| Stable path resolution | Legacy path resolution | Multiple directory naming schemes are searched for the same strategy | `storage.py` candidate path helpers | Ambiguity and migration complexity |
| `stop_loss`/`take_profit` | Compatibility `sl`/`tp` | Two field pairs represent the same protections | `BaseStrategy.get_signal()`, schema helpers | Inconsistent producer/consumer expectations |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `SignalIntent` | Defined and exported, but no producer or consumer found | Exact symbol search across repository | High | Only `base.py` and `__init__.py` hits |
| `StrategyEvent` | Only used as annotations for no-op base hooks | Exact symbol search, lifecycle call searches | High | No runtime event producer/consumer |
| `BaseStrategy.on_tick()` | No current runtime call found | Method-call search and runtime file inspection | Medium | No hit; dynamic callers cannot be fully excluded |
| `BaseStrategy.on_trade()` | No caller found | Exact method-call search | High | No repository hit |
| `BaseStrategy.on_timer()` | No caller found | Lifecycle searches | Medium | No repository hit |
| `BaseStrategy.on_shutdown()` | No caller found | Lifecycle searches | Medium | No repository hit |
| `get_indicator_value()` | No caller found | Exact call search | High | Definition only |
| `crossover()` | No caller found | Exact call search | High | Definition only |
| `crossunder()` | No caller found | Exact call search | High | Definition only |
| `registered_strategies()` | Current evidence is test/diagnostic only | Exact symbol search | Medium | Standard unit test; package exposure |
| `list_strategy_names()` | Current evidence is test/usage plus public exposure | Exact symbol search | Medium | Usage example and test |
| `delete_strategy_version()` | No confirmed storage caller | Exact method search, distinguish DB method | High | Definition only for storage class |
| `StrategyStorage.list_versions()` | No confirmed caller; similarly named API method uses database | Exact method search and route inspection | High | API `list_versions()` returns DB rows |
| `TemplateStrategy` | Not one of registry built-ins; direct current use is unit test, while older stored artifacts inherit it | Exact symbol search, registry inspection | Medium | `test_strategy.py`, stored strategy files |
| Template schema/action version constants | No external reader found | Exact symbol/context search | Medium | Class definitions only |
| `oldest_position()` timestamp ordering | Sorts stringified values; empty/mixed formats can produce misleading order | Source inspection | High | `sorted(..., key=str(opened_at or ""))` |
| `rolling_rsi()` and `rolling_sma()` periods | No explicit validation for non-positive periods | Source inspection and tests | High | Period passed directly to division/rolling |

### Confidence scale

* **High:** Relevant static search categories were completed and no dynamic route is plausible or a clear source-level property was observed.
* **Medium:** Static searches were completed, but dynamic imports, package-tool discovery, callbacks, or external callers cannot be fully excluded.
* **Low:** Evidence was partial or inaccessible.

No item is labelled dead code solely from missing production calls. Items with dynamic or compatibility potential remain `Questionable`, `Possibly used`, or `Test-only`.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Base lifecycle events | No runtime connection found for `on_trade`, `on_timer`, or `on_shutdown` | Public lifecycle surface overstates actual executed lifecycle | Source and call searches |
| Stateful strategy lifecycle | `on_event()` is required by runtime but absent from `BaseStrategy` | A `BaseStrategy` subclass alone does not describe full stateful compatibility | `trading/stateful.py`, event-driven simulator |
| Strategy intent contract | `SignalIntent` is never produced from `SignalDict` and not consumed by execution | Intended routing contract is disconnected | Exact symbol search |
| Template registration | `TemplateStrategy` is not registered as a built-in | Cannot be selected by registry name unless manually registered | Registry built-in list |
| File version deletion | `delete_strategy_version()` has no confirmed service/API caller | Individual version artifacts may only be managed in the database layer or not removed from disk | Call search |
| Storage version listing | `StrategyStorage.list_versions()` is bypassed by database-backed API listing | Filesystem and database version views can diverge | `StrategyCatalogService.list_versions()` |
| Test suite continuity | Multiple tests import removed strategy modules | Full strategy test directory likely cannot collect without exclusions or historical files | Static imports; exact removed-path fetches |
| Custom strategy discovery | Dynamic loader chooses first subclass rather than a declared export | Multi-class files can load an unintended class | `load_strategy_class()` loop over `dir(module)` |
| Catalog consistency | DB, filesystem, and governance updates have no common transaction | Partial state can remain after mid-workflow failure | `StrategyCatalogService` operation order |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-STRATEGY-001` | Same tool name has raw and enveloped return contracts | Package `__init__.py` versus `registry.py`/`stateful_common.py` | Import-path-dependent type incompatibility | Standard wrapper tests versus raw baseline imports |
| `V1-ISSUE-STRATEGY-002` | Strategy lifecycle is split across strategy and trading domains | `base.py`; `trading/stateful.py` | No single authoritative strategy interface | Runtime calls `on_event()` from mixin/protocol |
| `V1-ISSUE-STRATEGY-003` | Unused lifecycle hooks and intent/event contracts remain public | `base.py` | Larger and misleading public surface | No callers for several symbols |
| `V1-ISSUE-STRATEGY-004` | Template duplicates canonical schema logic | `template_strategy.py` | Schema drift and compatibility differences | Local `_ensure_signal_columns()` |
| `V1-ISSUE-STRATEGY-005` | Registry directly imports a fixed list of data-layer strategies | `registry._builtin_strategy_classes()` | Tight coupling; adding/removing built-ins requires registry edits | Nine explicit imports |
| `V1-ISSUE-STRATEGY-006` | Direct `register_builtin_strategies()` does not set `_BUILTINS_REGISTERED` | `registry.py` | Later lazy check repeats registration and logging | Flag is only set in `_ensure_builtin_strategies_registered()` |
| `V1-ISSUE-STRATEGY-007` | Registry and file storage are separate activation systems | `registry.py`, `storage.py` | Availability differs between simulation config and stored custom workflows | Separate lookup paths |
| `V1-ISSUE-STRATEGY-008` | Storage class has several unrelated responsibilities | `storage.py` | High change coupling and broad failure surface | Persistence, migration, archives, dynamic imports, discovery |
| `V1-ISSUE-STRATEGY-009` | `user_id` parameters do not control path resolution or authorization | Most `StrategyStorage` public methods | Signatures imply isolation that storage itself does not enforce | Paths are based on caller-provided username/name/id |
| `V1-ISSUE-STRATEGY-010` | Global storage construction writes to disk during import | `storage = StrategyStorage()` | Import can fail or mutate filesystem before an operation is requested | Constructor calls `mkdir()` |
| `V1-ISSUE-STRATEGY-011` | Dynamic loader executes arbitrary stored Python and picks first subclass | `load_strategy_class()` | Import-time side effects; ambiguous selection in multi-class modules | `exec_module()` and first matching object |
| `V1-ISSUE-STRATEGY-012` | Archive import validates only presence of `strategy.py` | `import_strategy()` | Invalid or incomplete strategy artifacts can be accepted into filesystem flow | No class/schema validation before return |
| `V1-ISSUE-STRATEGY-013` | Catalog operations are not atomic across DB/files/governance | `app/api/routes/strategies.py` | Orphaned rows/files or governance mismatch after failures | Sequential operations without compensation |
| `V1-ISSUE-STRATEGY-014` | `list_versions()` documentation and identity model are stale | `storage.py` | Signature omits documented identifiers and can merge same-name directories | Doc mentions absent args; name-based glob |
| `V1-ISSUE-STRATEGY-015` | Broad catch-log-rethrow wrappers add little error meaning | Most storage methods | Callers receive low-level exceptions without domain classification | `except Exception` then `raise` |
| `V1-ISSUE-STRATEGY-016` | State helper edge cases are weakly validated | `rolling_rsi`, `rolling_sma`, `oldest_position` | Invalid periods or heterogeneous timestamps can produce errors/wrong selection | Source inspection |
| `V1-ISSUE-STRATEGY-017` | Current tests include removed framework imports | Strategy tests | Full current test path may fail during collection and can misrepresent current capability | Imports of missing `pybots`, `config`, `state`, `StrategyPermissionError` |
| `V1-ISSUE-STRATEGY-018` | Storage has little direct current unit coverage | `storage.py` and tests | Critical filesystem/dynamic-loading behavior has lower regression confidence | No focused current storage test found |
| `V1-ISSUE-STRATEGY-019` | Template symbol default contradicts validation intent | `BaseStrategy.__init__`, `TemplateStrategy._validate_params()` | Missing symbol silently becomes `"UNKNOWN"` | Validation only rejects empty string |
| `V1-ISSUE-STRATEGY-020` | Stateful strategy resolution can silently fall back to non-stateful path | `Engine._build_runtime_strategy()` | Registry/import errors are converted to `None`, potentially obscuring configuration failure | Catch of `ImportError`/`StrategyRegistryError` |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-STRATEGY-001` | Abstract DataFrame strategy contract | `base.BaseStrategy` | 001, 003, 005 | Used | Essential | Central inheritance boundary |
| `V1-CAP-STRATEGY-002` | Canonical row-level signal extraction | `BaseStrategy.get_signal()` | 003 | Used | Essential | Handles primary and second pending legs |
| `V1-CAP-STRATEGY-003` | Signal schema preparation | `ensure_signal_columns()` | 001, 002 | Used | Essential | Raw internal function; package wrapper differs |
| `V1-CAP-STRATEGY-004` | Explicit neutral/no-signal frames | `ensure_no_signal_columns()` | 002 | Used | Essential | Used by stateful strategies |
| `V1-CAP-STRATEGY-005` | Built-in strategy registration and lookup | `registry.py` | 001, 002 | Used | Essential | Nine hard-coded built-ins |
| `V1-CAP-STRATEGY-006` | Registry diagnostics | `list_strategy_names()`, `registered_strategies()` | None confirmed in production | Test-only / exposed | Useful | Useful for tools/diagnostics |
| `V1-CAP-STRATEGY-007` | Stateful market-price history helpers | midpoint and rolling-indicator helpers | 002 | Used | Essential | Read-only |
| `V1-CAP-STRATEGY-008` | Position basket calculations | side filter, PnL, weighted price, oldest position | 002 | Used | Essential/Useful | Supports martingale/pyramid/grid behavior |
| `V1-CAP-STRATEGY-009` | Strategy source and metadata version storage | `save_strategy`, load methods | 004 | Used | Essential | Filesystem-backed |
| `V1-CAP-STRATEGY-010` | Dynamic custom strategy loading | `load_strategy_class()` | 005 | Used | Essential | Executes stored Python |
| `V1-CAP-STRATEGY-011` | Strategy archive export/import | `export_strategy`, `import_strategy` | 004 | Used | Useful | Minimal import validation |
| `V1-CAP-STRATEGY-012` | Strategy artifact deletion | `delete_strategy()` | 004 | Used | Essential | Full-strategy deletion |
| `V1-CAP-STRATEGY-013` | Per-version artifact deletion | `delete_strategy_version()` | None | Unused | Questionable | No confirmed caller |
| `V1-CAP-STRATEGY-014` | Filesystem version discovery | `list_versions()` | None | Unused | Questionable | API uses DB list instead |
| `V1-CAP-STRATEGY-015` | Basic authoring template | `TemplateStrategy` | Dynamic artifact use/test | Test-only / indirect | Useful | Not a registry built-in |
| `V1-CAP-STRATEGY-016` | Standardized AI-tool surface | package `__all__` and standard wrappers | Diagnostic/tool invocation | Possibly used | Useful | Different contract from raw imports |
| `V1-CAP-STRATEGY-017` | Live rolling-bar signal processing support | Base `on_bar`/`get_signal` consumed by `SignalProcessor` | 003 | Used | Essential | Processor itself belongs to execution |
| `V1-CAP-STRATEGY-018` | Lifecycle event contracts | `StrategyEvent`, no-op hooks, `SignalIntent` | None complete | Unused/disconnected | No demonstrated value | Not connected to actual stateful runtime |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* The minimal `BaseStrategy` contract used by simulation and live signal processing.
* Registry name resolution for known built-in strategies.
* Canonical signal-column preparation.
* Stateful midpoint, indicator, position-filter, basket-PnL, and weighted-price calculations.
* File-backed source/version storage and dynamic class loading where custom user strategies are required.
* The row-to-`SignalDict` conversion used by live signal processing.
* Existing API integration for save/load/import/export workflows, while recognizing its consistency limitations.

### Behaviour that exists but is disconnected

* `SignalIntent`.
* `StrategyEvent` as a real runtime event contract.
* `on_trade()`, `on_timer()`, and `on_shutdown()`.
* `get_indicator_value()`, `crossover()`, and `crossunder()`.
* Per-version filesystem deletion.
* Filesystem version listing.
* Template schema/action version metadata.
* `TemplateStrategy` as a registry-selectable built-in.

### Likely dead weight

No item is conclusively labelled dead code where dynamic use remains plausible. The highest-confidence no-value candidates in the current repository are:

* `SignalIntent`
* `BaseStrategy.on_trade()`
* `BaseStrategy.on_timer()`
* `get_indicator_value()`
* `crossover()`
* `crossunder()`

These have high-confidence static no-caller findings but should still be manually checked against external consumers before removal.

### Duplicated responsibilities

* Signal schema creation exists in both `stateful_common.py` and `TemplateStrategy`.
* Strategy discovery occurs through both the built-in registry and dynamic file loading.
* Protection fields exist under both canonical and compatibility names.
* Lifecycle ownership is split between strategy and trading packages.

### Important uncertainties

* Whether external agents dynamically invoke every package-level standardized tool.
* Whether external callers outside the repository import compatibility exports.
* Whether stored custom strategies depend on current `TemplateStrategy` or removed modules.
* Whether any deployment excludes the stale strategy tests.
* Whether all filesystem, database, and governance operations are protected by orchestration not visible in the inspected routes.
* Whether arbitrary stored code is trusted or sandboxed before `load_strategy_class()` executes it.

### Areas requiring manual confirmation

1. Run test collection for `tests/unit/app/services/strategy` at the audited commit.
2. Confirm whether removed `strategy.pybots`, `strategy.config`, and `strategy.state` tests are intentionally retained.
3. Confirm the intended authoritative lifecycle: `BaseStrategy`, `StatefulStrategyProtocol`, or both.
4. Confirm whether AI agents call package-level wrapped tools and expect envelopes.
5. Inspect deployed custom strategy artifacts for dependencies on compatibility exports or removed modules.
6. Confirm whether database/filesystem/governance consistency is repaired by an outer transaction or background reconciliation process.

## Final Validation

* Every current Python file discovered in `app/services/strategy` is represented.
* Every export in the current `__init__.py` was checked.
* Raw versus package-wrapped callable behavior was distinguished.
* Repository-wide imports, calls, inheritance, dynamic loading, tests, usage examples, API routes, simulation, optimization, and live execution were searched.
* Production/runtime usage is separated from tests and examples.
* Inbound and outbound cross-domain dependencies are summarized.
* Workflows are based on concrete call paths.
* Uncertainty is labelled.
* No Version 2 requirements or redesign were introduced.
* No repository code was modified.
