# Simulator — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `simulator`
* **Repository:** `haruperi/HaruQuant`
* **Audited branch:** `main`
* **Audited commit:** `a39d26498e14772c571d75fa9a5f0e477a1dd912` — `refactor: remove unused and deprecated helper modules`
* **Requested package path:** `app/services/simulator`
* **Actual package state:** The requested package directory and its Python modules are not present at the audited commit.
* **Requested tests path:** `ttests/unit/app/services/simulator`
* **Actual tests path:** `tests/unit/app/services/simulator`
* **Files inspected:**
  * `tests/unit/app/services/simulator/test_simulator.py`
  * `tests/unit/app/services/simulator/test_simulator_coverage.py`
  * `tests/usage/app/services/08_simulator.py`
  * `app/services/brokers/router.py`
  * `app/services/utils/settings.py`
  * `app/services/__init__.py`
  * `app/services/trading/account_info.py`
  * `app/services/trading/trade.py`
  * `tests/unit/app/services/brokers/test_router.py`
  * `tests/unit/app/services/optimization/test_optimization.py`
  * `app/services/optimization/execution.py`
  * Current parallel package `app/services/simulation/*` was inspected only to establish overlap and current call-path ownership; it was not treated as the requested domain.
  * The immediate parent commit `cae1f33690a4b49c6bca5718237e2b354f2f6fb7` was inspected only for provenance of the deleted `app/services/NEW/simulator` tree.
* **Related packages searched:**
  * `app/services/brokers`
  * `app/services/trading`
  * `app/services/optimization`
  * `app/services/simulation`
  * `app/services/strategy`
  * `app/services/data`
  * `app/api/routes`
  * `tests/unit`
  * `tests/usage`
* **Usage searches completed:**
  * direct imports of `app.services.simulator`;
  * exact searches for `TradeSimulator` and `SimulatorConfig`;
  * imports of `app.services.simulator.engine`;
  * dynamic `import_module("app.services.simulator")` references;
  * configuration references to the `simulator` broker;
  * broker-router consumers;
  * unit tests, usage examples, optimization fixtures, and package exports;
  * current and immediate-parent commit file changes.
* **Audit limitations:**
  * The audit used the GitHub repository state, indexed code search, exact file retrieval, and commit comparison. A local checkout was not available for running imports or tests.
  * Uncommitted, ignored, generated, or machine-local files cannot be observed.
  * Runtime environment values were unavailable, so it could not be confirmed whether any deployed environment currently sets `active_broker="simulator"`.
  * Historical files under `app/services/NEW/simulator` are deleted at the audited commit and are not counted as current implementation.
  * The separate current package `app/services/simulation` is outside this audit boundary.

## 2. Executive Summary

At the audited commit, the requested Version 1 domain **does not provide an importable `app.services.simulator` package**. There are no current implementation files, `__init__.py` exports, public classes, functions, methods, constants, entry points, or registrations inside that package.

Evidence of the former or intended API remains in tests and examples. Those files expect `SimulatorConfig`, `TradeSimulator`, `TradeSimulator.run()`, result objects, and several private engine helpers. The known usage example retrieves OHLCV data, loads a strategy, instantiates `TradeSimulator`, and calls `run()`. The two unit-test files exercise the same absent API. Because the implementation package is missing, these artifacts do not demonstrate current working behavior.

A conditional production path also remains: `app.services.brokers.router.get_broker_module()` dynamically imports `app.services.simulator` when `active_broker` is set to `simulator`. The setting is still documented as supported. Trading account, symbol, position, order, deal, terminal, and trade services resolve their broker through that router. Therefore, the simulator-broker branch appears **conditionally broken** in a clean checkout.

The repository currently contains a distinct `app.services.simulation` package used by the FastAPI backtest and optimization flows. That package is operationally relevant but is not the requested `app.services.simulator` domain and cannot be silently substituted in this audit.

The evidence is **high confidence** for the package-absence, stale-import, and conditional-router findings. It is **medium confidence** regarding deployed impact because runtime configuration and local/uncommitted files were unavailable.

```text
Module folders: 0 | Files: 0 | Public symbols: 0 | Symbols with confirmed callers: 0 (N/A) | Workflows found: 3
```

Operational workflows from this domain: **0**.

## 3. Actual Package Structure

### Current repository structure

```text
app/
└── services/
    └── simulator/                         [NOT PRESENT]
```

There is no current package root, module folder, Python file, `__init__.py`, public export, configuration file, script, registry, decorator, or entry point under `app/services/simulator`.

### Referencing test and example artifacts

```text
tests/
├── unit/
│   └── app/
│       └── services/
│           └── simulator/
│               ├── test_simulator.py
│               └── test_simulator_coverage.py
└── usage/
    └── app/
        └── services/
            └── 08_simulator.py
```

### Related but excluded structures

```text
app/services/simulation/                    [CURRENT, DIFFERENT PACKAGE]
├── __init__.py
├── common.py
├── config.py
├── data_preparation.py
├── engine.py
├── event_driven.py
├── results.py
├── runner.py
└── vectorized.py

app/services/NEW/simulator/                 [HISTORICAL, DELETED ON CURRENT MAIN]
├── README.md
├── __init__.py
├── engine.py
└── models.py
```

The deleted `app/services/NEW/simulator/__init__.py` imported from `app.services.simulator.engine` and `app.services.simulator.models`, not from its own `app.services.NEW.simulator` path. This is provenance evidence for an incomplete or transitional move, not current functionality.

## 4. Module and File Inventory

No implementation modules or files exist inside the requested package boundary.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `app.services.simulator` | — | Requested package root is absent | None | None available | **Unused** as a current package; referenced by stale/conditional callers | **No demonstrated value** in current code |

### Evidence-only artifacts outside the package

| Artifact | Actual responsibility | Referenced simulator surface | Status |
| -------- | --------------------- | ---------------------------- | ------ |
| `tests/unit/app/services/simulator/test_simulator.py` | Unit tests for a deterministic bar simulator and auxiliary-chart context slicing | `SimulatorConfig`, `TradeSimulator`, `TradeSimulator.run()`, private `_make_context()` | Test target missing |
| `tests/unit/app/services/simulator/test_simulator_coverage.py` | Validation and edge-case tests for the former simulator | `SimulatorConfig`, `TradeSimulator`, `_timeframe_duration`, `_gross_pnl`, `_find_position`, pending orders, time exits | Test target missing |
| `tests/usage/app/services/08_simulator.py` | Manual usage example using MT5 OHLCV and a bundled strategy | `SimulatorConfig`, `TradeSimulator`, `run()`, result `to_dict()` | Example target missing |
| `app/services/brokers/router.py` | Select active broker module | Dynamic import of `app.services.simulator` | Conditional runtime path is unresolved |
| `app/services/utils/settings.py` | Runtime settings | Documents `simulator` as an allowed active broker name | Configuration is stale or disconnected |
| `tests/unit/app/services/optimization/test_optimization.py` | Optimization tests | Inserts mocked `app.services.simulator`, `.engine`, and `.orchestrator` modules because they do not exist on disk | Test-only substitution |

## 5. Public Behaviour Inventory

There is no current public behavior to inventory because no Python implementation file exists under `app/services/simulator`.

### Referenced but absent API

The following symbols are **not current public symbols**. They are listed only because repository callers or tests refer to them.

| Referenced symbol | Expected type | Evidence of expected responsibility | Current definition | Usage evidence | Audit classification |
| ----------------- | ------------- | ----------------------------------- | ------------------ | -------------- | -------------------- |
| `SimulatorConfig` | Class/dataclass | Configure initial balance, point size, spread, slippage, quantity, contract size, volume constraints, and end-of-run behavior | Not found | Imported by both simulator unit-test files and the usage example | Missing referenced API |
| `TradeSimulator` | Class | Execute a strategy against canonical bars | Not found | Instantiated by both simulator unit-test files and the usage example | Missing referenced API |
| `TradeSimulator.run()` | Method | Run a bar simulation and return trades, equity, metrics, positions, and serialized results | Not found | Called by simulator tests and usage example | Missing referenced API |
| `TradeSimulator._make_context()` | Private method | Build point-in-time multi-timeframe strategy context | Not found | Called directly by `test_simulator.py` | Missing private implementation detail |
| `_timeframe_duration()` | Private function | Convert timeframe labels to timedeltas | Not found | Imported directly by coverage tests | Missing private implementation detail |
| `_gross_pnl()` | Private function | Calculate long/short gross P&L | Not found | Imported directly by coverage tests | Missing private implementation detail |
| `_find_position()` | Private function | Find a simulated position by ID | Not found | Imported directly by coverage tests | Missing private implementation detail |
| `app.services.simulator` broker module | Module | Provide broker-compatible account, terminal, symbol, position, order, deal, and trade operations | Not found | Dynamically imported by `get_broker_module()` | Missing runtime module |

### Expected inputs, outputs, side effects, and failures

Because there is no implementation, these properties cannot be confirmed from code:

| Aspect | Confirmed finding |
| ------ | ----------------- |
| Signatures | Only call shapes in tests/examples are observable; no authoritative implementation signature exists. |
| Return types | Tests expect a result with fields such as `strategy_id`, `symbol`, `timeframe`, `equity_curve`, `metrics`, `trades`, `closed_trades`, `open_positions`, and `to_dict()`. No implementation verifies this contract. |
| Exceptions | Tests expect configuration `ValueError`s and unsupported-timeframe errors. No current code confirms the exact conditions or messages. |
| Side effects | The usage example performs an external MT5 data read before invoking the missing simulator. Simulator-side mutation, persistence, event publication, or broker mutation cannot be confirmed. |
| Dependencies | Tests imply dependencies on contracts, strategy, analytics, and data packages. No current package imports establish an authoritative dependency list. |
| Real system value | No current working caller can receive value from the absent package. |

## 6. Actual Workflows

### `V1-WF-SIMULATOR-001` — Strategy Bar Simulation from Tests or Usage Example

* **Scope:** Cross-domain
* **Trigger:** Direct execution of `tests/usage/app/services/08_simulator.py` or collection/execution of the simulator unit tests.
* **Input boundary:** Canonical strategy object plus a sequence of OHLCV `Bar` objects; the usage example first requests MT5 OHLCV through `app.services.data.get_data`.
* **Functions and methods used:**
  * expected import of `SimulatorConfig`;
  * expected import and construction of `TradeSimulator`;
  * expected call to `TradeSimulator.run(strategy, bars, symbol=..., timeframe=...)`;
  * expected result inspection through fields and `to_dict()`.
* **Files involved:**
  * `tests/usage/app/services/08_simulator.py`
  * `tests/unit/app/services/simulator/test_simulator.py`
  * `tests/unit/app/services/simulator/test_simulator_coverage.py`
  * missing `app/services/simulator/__init__.py`
  * missing `app/services/simulator/engine.py`
  * missing `app/services/simulator/models.py`
* **External dependencies:** Data service, strategy service, contracts, pandas, pytest, and MT5 for the usage example.
* **Output boundary:** Expected simulated trades, equity curve, metrics, open/closed positions, and a serializable result.
* **Failure behaviour:** On a clean repository checkout, the first `from app.services.simulator ...` import has no repository-backed module to resolve.
* **Operational status:** **Broken**
* **Evidence:**
  * `tests/usage/app/services/08_simulator.py:17-19, 52-65`
  * `tests/unit/app/services/simulator/test_simulator.py:9-16, 117-176`
  * `tests/unit/app/services/simulator/test_simulator_coverage.py:19-27`
  * Exact current package file lookup returned no `app/services/simulator/__init__.py`.

```text
Usage script or unit test
→ import app.services.simulator
→ [module missing]
→ workflow stops before configuration or simulation
```

### `V1-WF-SIMULATOR-002` — Simulator as the Active Trading Broker

* **Scope:** Cross-domain
* **Trigger:** Runtime setting `active_broker="simulator"` followed by any trading service call that resolves the active broker.
* **Input boundary:** Trading service request or read operation.
* **Functions and methods used:**
  * `app.services.brokers.router.get_active_broker_name()`;
  * `app.services.brokers.router.get_broker_module()`;
  * `import_module("app.services.simulator")`;
  * trading consumers then expect broker functions such as `get_account_info()` and trade operations.
* **Files involved:**
  * `app/services/utils/settings.py`
  * `app/services/brokers/router.py`
  * `app/services/trading/account_info.py`
  * `app/services/trading/terminal_info.py`
  * `app/services/trading/symbol_info.py`
  * `app/services/trading/position_info.py`
  * `app/services/trading/order_info.py`
  * `app/services/trading/history_order_info.py`
  * `app/services/trading/deal_info.py`
  * `app/services/trading/trade.py`
* **External dependencies:** Runtime settings and the trading service.
* **Output boundary:** Expected broker-compatible snapshots or mutation results returned to trading callers.
* **Failure behaviour:** Dynamic import cannot resolve a repository-backed `app.services.simulator` module. Default `active_broker="mt5"` prevents the failure until the simulator option is selected.
* **Operational status:** **Broken when selected; dormant under the default setting**
* **Evidence:**
  * `app/services/utils/settings.py:61-64, 88`
  * `app/services/brokers/router.py:get_active_broker_name`
  * `app/services/brokers/router.py:get_broker_module`, especially the `active == "simulator"` branch
  * `app/services/trading/account_info.py:AccountInfo._refresh`
  * `app/services/trading/trade.py:Trade._send_request`
  * repository-wide callers of `get_broker_module()` across the trading information and mutation modules.

```text
Trading read or mutation request
→ get_active_broker_name()
→ "simulator"
→ get_broker_module()
→ import_module("app.services.simulator")
→ ModuleNotFoundError / unresolved broker
```

### `V1-WF-SIMULATOR-003` — Optimization Tests with a Synthetic Simulator Module

* **Scope:** Internal to tests
* **Trigger:** Collection/execution of optimization unit tests.
* **Input boundary:** Optimization test cases.
* **Functions and methods used:**
  * creation of `MockEngine` and `MockOrchestrator`;
  * insertion of fake modules into `sys.modules` under:
    * `app.services.simulator`;
    * `app.services.simulator.engine`;
    * `app.services.simulator.orchestrator`.
* **Files involved:**
  * `tests/unit/app/services/optimization/test_optimization.py`
  * `tests/unit/app/services/optimization/test_optimization_coverage.py`
* **External dependencies:** pytest and `unittest.mock`.
* **Output boundary:** Optimization tests receive synthetic success data rather than real simulator behavior.
* **Failure behaviour:** The fixture can conceal missing legacy imports inside the tested path; it cannot validate simulator correctness.
* **Operational status:** **Partial — test scaffolding works independently of a real simulator, but no simulator workflow executes**
* **Evidence:**
  * `tests/unit/app/services/optimization/test_optimization.py:16-42`
  * `tests/unit/app/services/optimization/test_optimization.py:mock_simulator_modules`
  * The test comment explicitly states that the simulator module “does not exist on disk.”

```text
Optimization test collection
→ inject fake app.services.simulator modules into sys.modules
→ run optimization tests against mocks
→ no real simulator code executed
```

## 7. Usage and Caller Map

Because no public symbols exist, this map records references to the absent module or expected symbols.

| Public symbol / module reference | Called from | Call type | Runtime or test | Evidence |
| -------------------------------- | ----------- | --------- | --------------- | -------- |
| `app.services.simulator` | `app.services.brokers.router.get_broker_module()` | Dynamic string-based import | Runtime, conditional | `app/services/brokers/router.py:64-68` |
| Expected broker module methods | `app.services.trading.account_info.AccountInfo._refresh()` | Module method call after broker resolution | Runtime | `app/services/trading/account_info.py:22-26` |
| Expected broker module methods | Trading terminal, symbol, position, order, history-order, deal, and trade modules | Module method calls after broker resolution | Runtime | repository-wide `get_broker_module` search |
| `SimulatorConfig` | `tests/unit/app/services/simulator/test_simulator.py` | Direct import and construction | Test | `test_simulator.py:14, 149-158` |
| `TradeSimulator` | `tests/unit/app/services/simulator/test_simulator.py` | Direct import, construction, method call | Test | `test_simulator.py:14, 149-160` |
| `TradeSimulator._make_context()` | `tests/unit/app/services/simulator/test_simulator.py` | Direct private-method call | Test | `test_simulator.py:215-228, 237-250` |
| `SimulatorConfig` | `tests/unit/app/services/simulator/test_simulator_coverage.py` | Direct import and validation construction | Test | `test_simulator_coverage.py:19-22, 47-74` |
| `TradeSimulator` | `tests/unit/app/services/simulator/test_simulator_coverage.py` | Direct import and behavior tests | Test | `test_simulator_coverage.py:19-22` |
| `_timeframe_duration`, `_gross_pnl`, `_find_position` | `tests/unit/app/services/simulator/test_simulator_coverage.py` | Direct import of private helpers | Test | `test_simulator_coverage.py:23-27` |
| `SimulatorConfig`, `TradeSimulator` | `tests/usage/app/services/08_simulator.py` | Direct import and example execution | Example | `08_simulator.py:17-19, 52-65` |
| `app.services.simulator` | `tests/unit/app/services/brokers/test_router.py` | Direct import for router assertion | Test | `test_router.py:29-33` |
| `app.services.simulator*` | `tests/unit/app/services/optimization/test_optimization.py` | `sys.modules` mock injection | Test | `test_optimization.py:16-42` |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

There is no current implementation, so no outbound imports or calls can be confirmed from the requested package.

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --------------------------- | -------------------------------- | ------------------------- | -------- |
| None confirmed | No implementation exists | — | Missing package root |

Historical and test artifacts suggest dependencies on strategy, contracts, data validation, and analytics, but those are not current code dependencies and are not counted here.

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| `app.services.brokers` | Entire `app.services.simulator` module | Resolve simulator as the configured broker | `app/services/brokers/router.py:get_broker_module` |
| `app.services.trading` | Expected broker-compatible module functions | Account, terminal, symbol, position, order, deal, history, and trade operations | `get_broker_module()` callers; `AccountInfo._refresh`; `Trade._send_request` |
| Simulator unit tests | `SimulatorConfig`, `TradeSimulator`, private engine helpers | Validate deterministic simulation behavior | `tests/unit/app/services/simulator/*` |
| Usage examples | `SimulatorConfig`, `TradeSimulator` | Demonstrate one strategy simulation | `tests/usage/app/services/08_simulator.py` |
| Optimization tests | Fake simulator module, engine, and orchestrator | Preserve tests despite missing modules | `tests/unit/app/services/optimization/test_optimization.py` |

### Boundary observation

The current API backtest and optimization implementation uses `app.services.simulation.Engine` and `app.api.routes.backtest.portfolio_run`, not this domain. That is evidence that active backtest ownership has moved elsewhere, while some legacy `simulator` references remain disconnected.

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| Missing `app.services.simulator` | Current `app.services.simulation` | Both names represent simulation/backtesting concepts; only `simulation` currently contains executable code | Current package files and `app/api/routes/backtest.py` imports; stale tests import `simulator` | Callers can target the wrong package name; migration status is ambiguous |
| Deleted `app/services/NEW/simulator` | Current `app/services/simulation` | Historical deterministic bar simulation versus current vectorized/event-driven simulation | Immediate-parent file tree and current simulation package | Historical intent may be mistaken for current capability |
| Deleted `app/services/NEW/simulator/__init__.py` | Missing `app.services.simulator` | The deleted package re-exported symbols from the missing target path | Historical `app/services/NEW/simulator/__init__.py` | The transitional package was not self-contained and could not establish a stable boundary |
| Legacy simulator tests | Current simulation tests/callers | Both concern backtesting but exercise different APIs and result contracts | `tests/unit/app/services/simulator/*` versus `app.services.simulation` callers | Test coverage can appear broad while covering an API that no longer exists |

No current duplicate implementation exists inside the requested package because it contains no files.

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| `tests/unit/app/services/simulator/test_simulator.py` | Targets an absent implementation and appears unable to collect in a clean checkout | Exact package fetch, direct-import search, `TradeSimulator` search, test inspection | **High** | Direct import at file start; no current package |
| `tests/unit/app/services/simulator/test_simulator_coverage.py` | Targets absent public and private symbols | Exact symbol searches, package fetch, test inspection | **High** | Imports missing `engine.py` helpers and missing classes |
| `tests/usage/app/services/08_simulator.py` | Stale usage example for a missing API | Exact path fetch, import search, symbol search | **High** | Direct import of `app.services.simulator` |
| `app.services.brokers.router` simulator branch | Runtime branch resolves a missing module | Dynamic import search, broker-router caller search, settings search | **High** for missing target; **Medium** for deployed impact | `import_module("app.services.simulator")`; runtime setting unknown |
| `Settings.active_broker` comment listing `simulator` | Advertises a broker option with no current provider module | Configuration search and router inspection | **High** | `app/services/utils/settings.py:88` |
| `tests/unit/app/services/brokers/test_router.py::test_get_broker_module_simulator` | Test assumes `from app.services import simulator` succeeds, but no subpackage exists | Package export inspection, exact package search, test inspection | **High** | Test lines 29-33; `app/services/__init__.py` does not re-export it |
| Optimization simulator mocks | Test harness explicitly masks missing modules | `sys.modules` search, optimization test inspection, current optimization implementation inspection | **High** | Test comment and fixture explicitly state module absent |
| Historical `app/services/NEW/simulator` | Deleted at current commit; not a current caller or capability | Commit comparison, parent-file inspection, current-tree search | **High** | Removed-file list in current commit comparison |
| Current `app.services.simulation` | Not unused; it is a separate active package and should not be classified as this domain | API, optimization, and package import searches | **High** | `app/api/routes/backtest.py`, `app/services/optimization/execution.py` |

No item is labelled “dead code” inside `app/services/simulator` because there is no current code to evaluate.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Deterministic bar simulation | Missing `app.services.simulator` implementation | Unit tests and usage example cannot reach a simulator | Direct imports in all three artifacts |
| Simulator broker mode | Broker router has no target module | Trading reads/mutations fail when simulator broker is selected | Router dynamic import and settings option |
| Simulator package export | Missing package `__init__.py` and symbol definitions | `from app.services.simulator import ...` is unresolved | Exact package lookup and repository search |
| Optimization compatibility | Tests rely on synthetic modules rather than a real implementation | Optimization tests cannot prove simulator integration | `mock_simulator_modules` fixture |
| Migration from `simulator` to `simulation` | Legacy references were not consistently updated or removed | Split terminology and incompatible APIs remain | Current backtest route uses `simulation`; tests/router use `simulator` |
| Historical `NEW/simulator` placement | Historical files imported from a different, missing path | The historical tree did not establish a self-contained package at its stored location | Parent `NEW/simulator/__init__.py` and `engine.py` imports |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-SIMULATOR-001` | Requested package root is absent | `app/services/simulator` | No current simulator implementation or public API exists | Exact file lookup and repository-wide search |
| `V1-ISSUE-SIMULATOR-002` | Unit tests target missing classes and modules | `tests/unit/app/services/simulator/*` | Test collection or execution is disconnected from repository code | Direct imports of missing package |
| `V1-ISSUE-SIMULATOR-003` | Usage example targets a missing API | `tests/usage/app/services/08_simulator.py` | Example cannot demonstrate real system value | Direct imports and calls |
| `V1-ISSUE-SIMULATOR-004` | Runtime broker router advertises and imports a missing provider | `app/services/brokers/router.py:get_broker_module` | Conditional production/runtime failure when simulator is selected | Dynamic import branch |
| `V1-ISSUE-SIMULATOR-005` | Runtime settings still list simulator as supported | `app/services/utils/settings.py:Settings.active_broker` | Configuration permits a route that has no implementation | Field documentation/default comment |
| `V1-ISSUE-SIMULATOR-006` | Naming and ownership are split between `simulator` and `simulation` | service packages, API routes, tests | Callers cannot infer the authoritative simulation boundary from names alone | Active API imports `simulation`; stale artifacts import `simulator` |
| `V1-ISSUE-SIMULATOR-007` | Optimization tests mask missing modules with `sys.modules` injection | `tests/unit/app/services/optimization/test_optimization.py` | Tests may pass without exercising an actual simulator dependency | Explicit mock fixture |
| `V1-ISSUE-SIMULATOR-008` | Broker-router simulator test assumes a package that does not exist | `tests/unit/app/services/brokers/test_router.py` | Test does not reflect current repository structure | `from app.services import simulator` |
| `V1-ISSUE-SIMULATOR-009` | Historical transitional tree imported from a different path | deleted `app/services/NEW/simulator/*` | Historical code was structurally disconnected even before deletion unless another local package supplied the imports | Parent-file imports |
| `V1-ISSUE-SIMULATOR-010` | No current `__init__.py`, exports, registration, or entry point | `app/services/simulator` | No discoverable public contract can be audited or consumed | Missing package |

## 13. V1 Capability Catalogue

The catalogue below distinguishes **referenced intent** from **current implementation**. None of these rows represents a confirmed working capability of the requested package.

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-SIMULATOR-001` | Importable simulator service | None | `V1-WF-SIMULATOR-001`, `002` | **Unused** as current code | **No demonstrated value** | Package root absent |
| `V1-CAP-SIMULATOR-002` | Simulator configuration | None; `SimulatorConfig` referenced only | `V1-WF-SIMULATOR-001` | **Test-only** reference | **No demonstrated value** | Validation expectations exist only in tests |
| `V1-CAP-SIMULATOR-003` | Bar-by-bar strategy execution | None; `TradeSimulator.run()` referenced only | `V1-WF-SIMULATOR-001` | **Test-only** reference | **No demonstrated value** | No executable implementation |
| `V1-CAP-SIMULATOR-004` | Pending, stop, limit, protective, and time-exit handling | None; behavior asserted in coverage tests | `V1-WF-SIMULATOR-001` | **Test-only** reference | **No demonstrated value** | Tests describe intent, not current behavior |
| `V1-CAP-SIMULATOR-005` | Multi-timeframe strategy context | None; private `_make_context()` referenced by tests | `V1-WF-SIMULATOR-001` | **Test-only** reference | **No demonstrated value** | Direct test of a missing private method |
| `V1-CAP-SIMULATOR-006` | Simulation result, trades, equity, and analytics | None; expected result fields appear in tests/example | `V1-WF-SIMULATOR-001` | **Test-only** reference | **No demonstrated value** | Return contract cannot be verified |
| `V1-CAP-SIMULATOR-007` | Broker-compatible simulator provider | None | `V1-WF-SIMULATOR-002` | **Possibly used** configuration path, but unresolved | **Questionable** | Runtime selection exists; deployment use unknown |
| `V1-CAP-SIMULATOR-008` | Optimization integration through legacy simulator engine/orchestrator | Mock-only test modules | `V1-WF-SIMULATOR-003` | **Test-only** | **No demonstrated value** | Current optimization uses a different backtest path |
| `V1-CAP-SIMULATOR-009` | Historical deterministic simulator implementation | Deleted `app/services/NEW/simulator/*` at parent commit | None current | **Unused** at audited commit | **No demonstrated value** in current code | Historical provenance only |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

No behavior can be confirmed as valuable **from the current `app.services.simulator` package**, because the package contains no code.

The tests and deleted historical files express potentially valuable intent—deterministic bar simulation, no-lookahead execution, pending-order activation, time exits, auxiliary timeframes, trade/equity results, and broker-neutral strategy execution—but those intentions are not current working behavior and therefore cannot be classified as Essential, Useful, or Supporting in this audit.

### Behaviour that exists but is disconnected

* Simulator unit tests and the usage example still describe and invoke a legacy `TradeSimulator` API.
* The broker router and settings still expose a simulator broker option.
* Optimization tests still install synthetic simulator modules to preserve legacy test imports.
* A deleted historical implementation existed under `app/services/NEW/simulator`, but its internal imports targeted the missing `app.services.simulator` path.

### Likely dead weight

There is no implementation code inside the requested package to classify as dead code. The strongest dead-weight candidates are the stale references surrounding it:

* simulator-specific unit tests whose target package is absent;
* the usage example importing the absent API;
* the simulator branch in the broker router unless a local/generated provider exists outside Git;
* the `simulator` setting documentation;
* test fixtures that retain compatibility with nonexistent module names.

These are classified as stale or questionable references rather than dead code because runtime deployment configuration and local files were unavailable.

### Duplicated responsibilities

No current code duplication exists inside the requested package. There is, however, a domain-name and ownership overlap with the current `app.services.simulation` package. The active FastAPI backtest and optimization flows use `simulation`, while legacy tests and broker selection use `simulator`.

### Important uncertainties

* A developer machine may contain an uncommitted or ignored `app/services/simulator` directory.
* A deployment may inject or install a module at that path.
* It is unknown whether any environment currently selects `active_broker="simulator"`.
* The intended audit target may have been the current `app/services/simulation` package or the deleted `app/services/NEW/simulator` tree rather than the literal requested path.

### Areas requiring manual confirmation

1. Confirm whether the authoritative V1 audit target is:
   * current `app/services/simulation`;
   * deleted historical `app/services/NEW/simulator`; or
   * a local/uncommitted `app/services/simulator` package.
2. Confirm whether `active_broker="simulator"` is used in any deployment or local workflow.
3. Confirm whether simulator unit tests are expected to remain runnable in a clean checkout.
4. Confirm whether the historical `TradeSimulator` result contract still has consumers outside the repository.

## Evidence Not Accessible

* Uncommitted, ignored, generated, or local-only simulator files.
* A clean dependency installation and pytest run for the audited commit.
* Deployed environment variables and actual runtime selection of the simulator broker.
* Any compiled extension or external package that might inject `app.services.simulator` at runtime.
