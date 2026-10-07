# HaruQuantAI Architecture

Status: Ratified 3-Tier Architecture (Host, Workspaces, Dynamic Plugins), 2026-10-07.
Baseline: Phase 1 (Host Platform) and Phase 2 (Data Manager Workspace + Dynamic Plugins) operational at Commit `dd12535`.
Authorities: [PROJECT.md](PROJECT.md) governs scope and delivery milestones; [AGENTS.md](../AGENTS.md) governs constitutional rules and contributor gates.

---

## 1. Executive Summary & Architectural Vision

HaruQuantAI is a high-performance quantitative research, strategy generation, and backtesting workstation engineered in Python. It faithfully mirrors the robust, modular 3-tier architecture of **StrategyQuant X (SQX-145)**:

1. **Host Platform (`app/host/`):** The pure platform foundation. Contains zero quantitative or trading logic. Governs the application lifecycle, settings, unified logging, resource custody, persistence, async transports, job coordination, and dynamic plugin discovery.
2. **Domain Workspaces (`app/workspace/`):** Domain-specific operation centers that house business logic, quantitative pipelines, and domain REST routers. The initial authoritative workspace is the **Data Manager** (`app/workspace/data_manager/`), mirroring all 11 SQX Data Manager donor components. Future workspaces (Strategy Builder, Retester, Optimizer, Custom Projects) plug into this tier without altering the host.
3. **Dynamic Plugins (`app/plugins/`):** Fully decoupled, modular add-on packages declaring explicit extension slots (such as `slot: "data.provider"`). Plugins are dynamically scanned, verified, and loaded at runtime by the Host's discovery engine and attached to the appropriate workspace manager.

```
+-----------------------------------------------------------------------------------+
|                               UI Layer (React)                                    |
+-----------------------------------------------------------------------------------+
                                         |
                                  REST API / Events
                                         v
+-----------------------------------------------------------------------------------+
|                        Tier 1: Host Platform (app/host)                           |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | Bootstrap/Lifecycle|  | Discovery Engine   |  | Persistence (SQLite WAL)    |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | Resource Custody   |  | Transport / Events |  | Background Jobs Coordinator |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
                       Registers & Mounts Workspace Routers
                                         v
+-----------------------------------------------------------------------------------+
|                      Tier 2: Workspaces (app/workspace)                           |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Data Manager Workspace (app/workspace/data_manager)                         |  |
|  |  * Home & Storage Health (home.py)        * Data Ingestion & Catalog (data.py)|  |
|  |  * Instruments & Specs (instruments.py)   * Sessions & Windows (sessions.py)  |  |
|  |  * Baskets & Weighting (baskets.py)       * Broker Profiles (broker.py)       |  |
|  |  * Connections & Queue (connections.py)   * Custom Data & COT (custom_data.py)|  |
|  |  * Audit Log (log.py)                     * Documentation Index (help.py)     |  |
|  |  * Quality Review (actions/review/)       * Bar Transforms (actions/transform)|  |
|  |  * REST Router: /api/v2/data/... (routes.py)                                |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  [Future Workspaces: Strategy Builder | Retester/Backtest | Optimizer | Projects] |
+-----------------------------------------------------------------------------------+
                                         ^
                        Attaches via Slot: "data.provider"
                                         |
+-----------------------------------------------------------------------------------+
|                      Tier 3: Dynamic Plugins (app/plugins)                        |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Market Data Providers (app/plugins/data_source/)                            |  |
|  |  * dukascopy        * darwinex        * metatrader        * sq_equity       |  |
|  |  * sq_futures       * crypto          * files             * yahoo           |  |
|  |  * tick_downloader                                                          |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Five Laws of Spatial Composability

Every module, workspace, and plugin in HaruQuantAI strictly complies with the **Five Laws of Spatial Composability**:

* **SC-01 Locality:** One quantitative concept has one cohesive owner. Its calculation, configuration, defaults, typed schema, bounds, units, metadata, and lowering hooks remain together. Universal primitives do not centralize domain business semantics.
* **SC-02 Orthogonality:** Adding, disabling, or removing a package cannot require editing unrelated peer modules or a central registry. Failures block only declared consumers; retained artifacts remain inspectable with an explicit unavailable producer.
* **SC-03 Explicit Typed Slots:** Components collaborate exclusively through declared, versioned capabilities and immutable documents. No private sibling imports, ambient global state, implicit singletons, fixture substitutes, or import-time side effects.
* **SC-04 Hierarchical/Algebraic Composition:** Typed primitives compose pinned trees, pipelines, workspaces, and finite project tasks. Editors, generators, simulators, and exporters share semantic documents; UI labels cannot redefine algorithms.
* **SC-05 Schema-Driven Description:** Package-owned identity, compatibility, schemas, defaults, constraints, units, slots, and presentation metadata drive discovery and UI rendering. The host does not maintain hard-coded catalogs of domain concepts.

---

## 3. Spatial Ownership

| Tier | Backend Path | UI Counterpart | Architectural Responsibility |
| :--- | :--- | :--- | :--- |
| **Host** | `app/host/` | `ui/app/host/` | Universal lifecycle, session authentication, plugin discovery, envelopes, background jobs, telemetry, resource custody, and persistence isolation. Zero domain/trading algorithms. |
| **Workspace** | `app/workspace/<domain>/` | `ui/app/workspace/<domain>/` | Complete business domain workflow, typed slot management, fallback behavior, and REST routing (e.g. `data_manager`). |
| **Dynamic Plugin** | `app/plugins/<slot_family>/<name>/` | `ui/app/plugins/<family>/<name>/` | Modular add-on declaring a concrete extension slot (e.g. `data.provider`) and providing self-contained adapter logic. |
| **Primitives** | `app/kernel/` | `ui/app/components/` | Reusable mathematical algorithms, numerical routines, and shared UI presentation primitives. |

---

## 4. Tier 1: Host Platform Architecture (`app/host/`)

The Host platform provides universal infrastructure to workspaces and plugins:

### 4.1 Bootstrap & Lifecycle Management (`app/host/bootstrap.py`)
The host boot sequence executes sequentially through well-defined stages:
1. **Config & Logging:** Loads settings, sets log levels, initializes secret redaction.
2. **Persistence:** Starts `DatabaseManager`, verifies schema migrations, configures SQLite WAL mode.
3. **Resource Governance:** Sets memory and CPU limits via `ResourceManager`.
4. **Job Coordination:** Initializes `JobManager` thread pool.
5. **Plugin Discovery & Registration:** Asynchronously scans plugin directories, validates manifests, dynamically imports adapters, and registers them into workspace managers.
6. **Router Mounting:** Mounts workspace REST routers onto the FastAPI application.
7. **Graceful Teardown:** Shuts down jobs, drains queues, releases plugin adapters in reverse order, and closes database connections.

### 4.2 Dynamic Plugin Discovery Engine (`app/host/discovery.py`)
* **Manifest Verification:** Inspects each plugin directory for a valid `plugin.json` declaring `id`, `name`, `version`, `slot`, `entry_point`, and `capabilities`.
* **Dynamic Import Isolation:** Loads plugin modules dynamically using `importlib.util.spec_from_file_location` without hard-coded package dependencies.
* **Instance Registry:** Provides `get_instance(plugin_id)` and `get_instances_for_slot(slot_id)` with lazy instantiation and thread-safe caching.

### 4.3 Persistence & Storage Custody (`app/host/persistence.py`)
* **SQLite Import Isolation:** Enforces strict isolation: `sqlite3` must NEVER be imported anywhere outside `app/host/persistence.py`. Violations trigger immediate test failures.
* **WAL Mode & Concurrency:** Configured with `journal_mode=WAL`, `synchronous=NORMAL`, and busy timeout handling for robust concurrent read/write operations.
* **Transactions & Migrations:** Centralizes schema creation, migrations, and transactional execution.

### 4.4 Resource Management (`app/host/resources.py`)
* **Process & Memory Quotas:** Tracks active memory and process limits.
* **Temporary Storage Sandboxing:** Allocates isolated scratch directories per task/job with automatic cleanup.

### 4.5 Transports & Uniform Response Envelope (`app/host/transport.py`, `app/host/response.py`)
* **Uniform Envelopes:** Standard API responses follow `ApiResponse[T]`, guaranteeing consistent formatting (`data`, `error`, `timestamp`, `version`).
* **Error Handling:** RFC 7807 compliant error schemas (`StandardError`) prevent leaked stack traces or sensitive internals.
* **Event Bus:** In-memory asynchronous pub/sub event distribution (`EventBus`) for decoupling system events from direct callers.

### 4.6 Background Job Coordinator (`app/host/jobs.py`)
* **Non-blocking Execution:** Executes long-running tasks (historical data downloads, transform jobs, quality audits) via thread pools.
* **Job States:** Lifecycle states: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`.

---

## 5. Tier 2: Workspaces Architecture (`app/workspace/`)

Workspaces encapsulate functional areas of the workstation. Each workspace acts as an authoritative domain coordinator.

### 5.1 Authoritative Data Manager Workspace (`app/workspace/data_manager/`)
Faithfully re-architected from StrategyQuant X (SQX-145) reference donors into cohesive Python modules:

| Module | StrategyQuant X Donor | Functional Responsibility |
| :--- | :--- | :--- |
| [`home.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/home.py) | `DataManagerHome` | Storage health metrics, total bar count, disk usage, symbol inventory overview. |
| [`data.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/data.py) | `DataManagerData` | Bar and tick catalog, ingestion pipeline, historical bar storage and retrieval. |
| [`instruments.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/instruments.py) | `DataManagerInstruments` | Instrument definitions: tick sizes, point values, pip values, contract specifications, margins. |
| [`sessions.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/sessions.py) | `DataManagerSessions` | Trading session schedules, day-of-week windows, NinjaTrader XML session import/export. |
| [`baskets.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/baskets.py) | `DataManagerBasket` | Synthetic/composite instruments, custom weightings, index creation. |
| [`broker.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/broker.py) | `DataManagerBroker` | Broker profiles: spread models, commission rates, slippage models, margin requirements. |
| [`connections.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/connections.py) | `DataManagerConnections` | `ProviderManager` coordinating data feeds, download queues, provider registration. |
| [`custom_data.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/custom_data.py) | `DataManagerCustomData` | COT (Commitment of Traders) reports and generic macroeconomic/custom series. |
| [`log.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/log.py) | `DataManagerLog` | Audit log of data operations, import history, and user adjustments. |
| [`help.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/help.py) | `DataManagerHelp` | Contextual help registry, documentation topics, data guides. |
| [`actions/review/quality.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/actions/review/quality.py) | `DataManagerActions` (Review) | `DataQualityInspector`: gap detection, bad tick filtering, price spike detection. |
| [`actions/transform/transforms.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/actions/transform/transforms.py) | `DataManagerActions` (Transform) | `SeriesTransformer`: resampling timeframes (M1 to H1/D1), session alignment, adjustments. |
| [`routes.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/routes.py) | Data Manager REST API | REST router exposing endpoints under `/api/v2/data/...`. |

### 5.2 Workspace Extensibility Pattern (Future Workspaces)
The workspace architecture is designed to accommodate additional SQX workspaces without cross-coupling:
* **Strategy Builder (`app/workspace/strategy_builder/`):** Genetic generation, building blocks, rule trees, and candidate evaluation.
* **Retester / Backtester (`app/workspace/retester/`):** Multi-market backtesting, historical simulations, slippage and spread stress-testing.
* **Optimizer (`app/workspace/optimizer/`):** Walk-Forward Matrix (WFM), parameter optimization, Monte Carlo permutation analysis.
* **Custom Projects (`app/workspace/custom_projects/`):** Automated quantitative workflow pipelines, acyclic/cyclic step execution graphs.

---

## 6. Tier 3: Dynamic Plugins (`app/plugins/`)

Plugins are autonomous add-on packages that extend HaruQuantAI through typed extension slots.

### 6.1 Extension Slot Contract: `data.provider`
Market data providers declare compliance with `slot: "data.provider"` in `plugin.json` and implement `BaseDataProvider` (`app/workspace/data_manager/connections.py`):
* `provider_id`: Unique identifier matching manifest.
* `get_available_symbols()`: Query available instruments from provider feed.
* `fetch_bars(symbol, timeframe, start, end)`: Ingest historical OHLCV bars.
* `fetch_ticks(symbol, start, end)`: Ingest high-resolution tick data.
* `test_connection()`: Verify connectivity and credentials.

### 6.2 Plugin Manifest Specification (`plugin.json`)
```json
{
  "id": "dukascopy",
  "name": "Dukascopy Data Provider",
  "version": "1.0.0",
  "author": "HaruQuantAI",
  "slot": "data.provider",
  "entry_point": "adapter:DukascopyDataProvider",
  "capabilities": ["ticks", "bars", "fx", "cfd"]
}
```

### 6.3 Active Dynamic Data Providers (`app/plugins/data_source/`)
1. **`dukascopy`:** Dukascopy Forex and CFD historical tick and minute data.
2. **`darwinex`:** Darwinex tick data with true institutional bid/ask spreads.
3. **`metatrader`:** MetaTrader 4 / 5 CSV and binary history file parser.
4. **`sq_equity`:** StrategyQuant proprietary stock/equity historical data provider.
5. **`sq_futures`:** StrategyQuant proprietary futures historical data provider.
6. **`crypto`:** Binance and cryptocurrency exchange historical feeds.
7. **`files`:** Generic multi-format local file importer (CSV, Parquet, TSV).
8. **`yahoo`:** Yahoo Finance free daily and intraday bar provider.
9. **`tick_downloader`:** High-precision tick downloader provider.

---

## 7. Quality, Verification & Constitutional Baseline

All HaruQuantAI modules adhere to the strict quality baseline enforced by CI and pre-commit hooks:

* **Standardized 5-Section Docstrings:** Every Python file must start with a docstring defining `Description:`, `Purpose:` (`FEAT-*`), `Key Capabilities:` (descriptive kebab-case `FR-*` tags), `Python API Usage:`, and `CLI Usage:`.
* **Zero Silent Failures:** No bare `except:`, no unhandled errors, no silent executions. Every critical operation emits an explicit log entry with its corresponding `FR-*` capability tag.
* **Strict Typing:** Python code passes `mypy --strict` and `pyright` without warnings or any-type leaks.
* **Ruff Formatting & Linting:** 88-character line limit, Google-style docstrings, organized imports (I001), and PEP 604 modern typing syntax.
* **Branch-Aware Coverage:** Focused, change-scoped pytest verification with a minimum of 80% branch coverage required for production releases.
