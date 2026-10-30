# HaruQuantAI Spatial Architecture & System Design

**Status:** Ratified 4-Tier Spatial Architecture (AppCore, Workspaces, Web Shell, Extensions).
**Baseline Roadmap:** [`docs/dev/full-reimplementation/`](dev/full-reimplementation/00-README.md).
**Authorities:** [docs/PROJECT.md](PROJECT.md) governs scope and delivery milestones; [AGENTS.md](../AGENTS.md) governs constitutional rules and contributor gates.

---

## 1. Executive Summary & Architectural Vision

HaruQuantAI is a high-performance quantitative research, strategy generation, and backtesting workstation engineered in Python 3.14 and TypeScript. It replaces the legacy StrategyQuant X (SQX-145) monolithic Java/Swing/Electron desktop architecture with an elegant, modern **4-Tier Spatial Architecture**:

1. **Tier 1: AppCore (`app/core/`):** The foundational engine layer. Houses both the host platform services (lifecycle, persistence, logging, telemetry, resources, async event transports, background multiprocessing job coordinator) and pure quantitative domain primitives (columnar time series, trading order models, distributed grid protocols, wizard code transforms, and standard error/response envelopes).
2. **Tier 2: Domain Workspaces (`app/workspace/`):** Independent business domain centers housing domain logic, data models, and REST routers (mounted under `/api/v2/<domain>/...`). Key workspaces include the **Home Workspace** (`app/workspace/home/`), the **Data Manager Workspace** (`app/workspace/data_manager/`), and future workspaces for Strategy Building, Retesting, Optimization, and Project Automation.
3. **Tier 3: Frontend Web Shell (`app/web/`):** A unified single-page application engineered in React 19, TypeScript, and Vite. Served directly by FastAPI via `install_web_build` in [`app/main.py`](../app/main.py), completely eliminating Electron and JVM desktop dependencies.
4. **Tier 4: Extensions & Dynamic Plugins (`app/extend/` & `app/plugins/`):** User-defined and donor building blocks: custom indicators, signals, stop-loss/take-profit rules, money management algorithms, export code templates (`ctemplate/`), and dynamically loaded provider plugins declaring typed extension slots.

```
+-----------------------------------------------------------------------------------+
|                        Tier 3: Frontend Web Shell (app/web/)                      |
|                  React 19 + TypeScript + Vite Single-Page App                     |
+-----------------------------------------------------------------------------------+
                                         |
                       HTTP REST / SSE / WebSocket Gateway
                                         v
+-----------------------------------------------------------------------------------+
|                        Tier 1: Host Subsystems (app/core/host/)                   |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | Bootstrap/Lifecycle|  | Discovery Engine   |  | Persistence (SQLite WAL)    |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | Resource Custody   |  | Transport / Events |  | Background Jobs Coordinator |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
                        Registers & Mounts Domain Routers
                                         v
+-----------------------------------------------------------------------------------+
|                     Tier 2: Domain Workspaces (app/workspace/)                    |
|                                                                                   |
|  +--------------------------------+  +-----------------------------------------+  |
|  | Home Workspace (home/)         |  | Data Manager Workspace (data_manager/)  |  |
|  |  * Project Registry            |  |  * Storage Health & Symbol Catalog      |  |
|  |  * Dashboard Panels            |  |  * Instruments & Trading Sessions       |  |
|  |  * ATM Visibility Rules        |  |  * Baskets & Broker Profiles            |  |
|  |  * Application Settings        |  |  * Quality Review & Bar Transforms      |  |
|  +--------------------------------+  +-----------------------------------------+  |
|                                                                                   |
|  [Future Workspaces: Code Editor | AlgoWizard | Results | Retester | Builder ...]  |
+-----------------------------------------------------------------------------------+
                                         ^
                        Attaches via Slot: "data.provider"
                                         |
+-----------------------------------------------------------------------------------+
|              Tier 4: Extensions & Dynamic Plugins (app/plugins/ & app/extend/)    |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Market Data Providers (app/plugins/data_source/)                            |  |
|  |  * dukascopy        * darwinex        * metatrader        * sq_equity       |  |
|  |  * sq_futures       * crypto          * files             * yahoo           |  |
|  +-----------------------------------------------------------------------------+  |
|  | Custom Indicators, Signals & Building Blocks (app/extend/)                   |  |
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

## 3. Spatial Ownership Matrix

| Tier | Backend Path | UI Counterpart | Architectural Responsibility |
| :--- | :--- | :--- | :--- |
| **Tier 1: Core (Host)** | `app/core/host/` | `app/web/workspaces/host/` | Universal lifecycle, session auth, persistence isolation, multiprocessing jobs, diagnostics, resources, event bus. Zero trading/financial algorithms. |
| **Tier 1: Core (Quant)** | `app/core/{data,trading,grid,wizard,lib}/` | Shared TS models | Columnar bar/tick series, order matching primitives, grid protocols, multi-target code AST transforms, standard response/error envelopes. |
| **Tier 2: Workspaces** | `app/workspace/<domain>/` | `app/web/workspaces/<domain>/` | Complete business domain workflow coordinators, domain models, REST routers (e.g. `home`, `data_manager`, `retester`). |
| **Tier 3: Web Shell** | `app/main.py` (`install_web_build`) | `app/web/` | React 19 / Vite single-page application shell, client-side routing, theme management, and UI component hierarchy. |
| **Tier 4: Extensions** | `app/plugins/` & `app/extend/` | Dynamic UI slots | User/donor building blocks, custom indicators, signals, and dynamic plugins declaring explicit extension slots (`data.provider`). |

---

## 4. Tier 1: AppCore Architecture (`app/core/`)

AppCore contains the engine foundations across pure host infrastructure and quantitative domain primitives:

### 4.1 Host Platform Subsystems (`app/core/host/`)

#### 4.1.1 Bootstrap & Lifecycle Management (`bootstrap.py`, `app/main.py`, `app/cli.py`)
The host boot sequence runs sequentially through 7 ordered stages for both the web server (`app/main.py`) and headless CLI (`app/cli.py`):
```
CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES -> READY
```
1. **CONFIGURING:** Validates host bind address, port, debug flags, and runtime thresholds.
2. **PATHS:** Verifies and provisions workspace directories (`database`, `logs`, `scratch`, `plugins`, `resources`).
3. **LOGGING:** Initializes asynchronous multi-sink telemetry (`app.log`, `access.log`, `errors.log`), SHA-256 secret redaction, and a 2000-record ring buffer.
4. **PERSISTENCE:** Configures SQLite WAL mode (`busy_timeout=5000`), verifies schema integrity, and loads `settings`.
5. **SERVICES:** Starts `SessionManager`, `ResourceManager` (`MemoryWatchdog`), `JobManager` (reconciling orphan `RUNNING` jobs to `INTERRUPTED`), and `TransportGatewayService`.
6. **ROUTES:** Mounts FastAPI gateway, static web assets, and domain workspace REST routers.
7. **READY & Reverse LIFO Teardown:** Transitions to `READY`. Guarantees reverse-order (LIFO) teardown (`READY -> ROUTES -> SERVICES -> PERSISTENCE -> LOGGING -> PATHS -> CONFIGURING`) on shutdown or failure.

#### 4.1.2 Persistence & Database Isolation (`persistence.py`)
* **SQLite Import Isolation:** Enforces strict isolation: `sqlite3` must NEVER be imported anywhere outside `app/core/host/persistence.py`. Violations trigger immediate architectural test failures.
* **WAL Mode & Concurrency:** Configured with `journal_mode=WAL`, `synchronous=NORMAL`, and `busy_timeout=5000` for high-throughput concurrent reads and serialized writes.
* **CRUD-Only Boundary:** Encapsulates all SQL creation and table mutations within `HostPersistence`. Domain workspaces cannot execute ad-hoc SQL. Settings updates use revision-checked atomic batch transactions (`apply_batch`).

#### 4.1.3 System Diagnostics & Memory Watchdog (`resources.py`)
* **Hardware Diagnostics:** Monitors CPU cores, RAM headroom, disk space, and process metrics via `psutil`.
* **Worker Sizing Policy:** Computes default worker concurrency via $\text{workers} = \max(1, \text{cpu\_cores} - 2)$.
* **Active Memory Watchdog:** Samples available system RAM and pauses or rejects incoming tasks if available RAM drops below 15%.

#### 4.1.4 Multiprocessing Background Job Coordinator (`jobs.py`)
* **ProcessPoolExecutor Pool:** Runs heavy compute tasks in dedicated OS processes to bypass the Python GIL.
* **Cooperative Cancellation (`JobContext`):** Propagates cooperative cancellation tokens to child processes.
* **Lifecycle States:** Governs `QUEUED`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, and `INTERRUPTED`. Orphan running tasks from previous crashes are automatically reconciled to `INTERRUPTED` on startup.

#### 4.1.5 Transports, Responses & Event Bus (`transport.py`, `app/core/lib/`)
* **Uniform Envelopes:** Standard API responses use `StandardResponse[T]` (`status`, `message`, `data`, `error`, `metadata`). Errors use typed `DomainError` hierarchies.
* **Event Streaming:** In-memory asynchronous pub/sub event distribution (`EventBus`) with Server-Sent Events (`/api/v1/events`) and WebSocket gateways.

### 4.2 Quantitative Engine Subsystems (`app/core/`)

* **`app/core/data/`:** High-performance time series data structures, columnar bar/tick storage (Arrow/Polars/DuckDB), and resamplers.
* **`app/core/trading/`:** Core order models (`Market`, `Limit`, `Stop`), position lifecycle, fill simulation, cash/margin accounting, and slippage/commission models.
* **`app/core/grid/`:** Distributed grid compute protocol, worker node discovery, message serialization, and task slicing.
* **`app/core/wizard/`:** Multi-platform strategy AST normalizer and Jinja2 code generator supporting MQL5, MQL4, EasyLanguage, cTrader C#, and Python.

---

## 5. Tier 2: Domain Workspaces Architecture (`app/workspace/`)

Domain Workspaces encapsulate business logic, domain models, and REST endpoints under `/api/v2/<domain>/...`:

### 5.1 Authoritative Data Manager Workspace (`app/workspace/data_manager/`)
Re-architected from StrategyQuant X (SQX-145) reference donors into cohesive Python modules:

| Module | SQX Donor Component | Functional Responsibility |
| :--- | :--- | :--- |
| [`home.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/home.py) | `DataManagerHome` | Storage health metrics, total bar count, disk usage, symbol inventory. |
| [`data.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/data.py) | `DataManagerData` | Bar and tick catalog, ingestion pipeline, historical bar storage and retrieval. |
| [`instruments.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/instruments.py) | `DataManagerInstruments` | Instrument definitions: tick sizes, point values, contract specifications, margins. |
| [`sessions.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/sessions.py) | `DataManagerSessions` | Trading session schedules, day-of-week windows, NinjaTrader XML import/export. |
| [`baskets.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/baskets.py) | `DataManagerBasket` | Synthetic/composite instruments, custom weightings, index creation. |
| [`broker.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/broker.py) | `DataManagerBroker` | Broker profiles: spread models, commission rates, slippage models, margin rules. |
| [`connections.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/connections.py) | `DataManagerConnections` | `ProviderManager` coordinating data feeds, download queues, provider registration. |
| [`custom_data.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/custom_data.py) | `DataManagerCustomData` | COT (Commitment of Traders) reports and macroeconomic data series. |
| [`log.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/log.py) | `DataManagerLog` | Audit log of data operations, import history, and adjustments. |
| [`help.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/help.py) | `DataManagerHelp` | Contextual help registry, documentation topics, data guides. |
| [`actions/review/quality.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/actions/review/quality.py) | `DataManagerActions` (Review) | `DataQualityInspector`: gap detection, bad tick filtering, price spike detection. |
| [`actions/transform/transforms.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/actions/transform/transforms.py) | `DataManagerActions` (Transform) | `SeriesTransformer`: resampling timeframes (M1 to H1/D1), session alignment. |
| [`routes.py`](file:///c:/Users/rharu/AppDev/HaruQuantAI/app/workspace/data_manager/routes.py) | Data Manager REST API | REST router exposing endpoints under `/api/v2/data/...`. |

### 5.2 Home Workspace (`app/workspace/home/` & `app/web/workspaces/home/`)
Coordinates workstation entry, project registry, dashboard configuration (`dashboardPanels.ts`), and advanced money-management ATM visibility rules (`atmVisibility.ts`).

### 5.3 Planned Workspaces
* **`app/workspace/code_editor/`:** Multi-language algorithmic code authoring.
* **`app/workspace/wizard/`:** AlgoWizard visual strategy rule trees and condition blocks.
* **`app/workspace/results/`:** Databank management, trade analysis, and report generation.
* **`app/workspace/retester/`:** Multi-market historical backtesting and stress simulation.
* **`app/workspace/builder/`:** Genetic programming and random strategy evolution.
* **`app/workspace/optimizer/`:** Parameter search, Walk-Forward Analysis, and Monte Carlo.
* **`app/workspace/custom_projects/`:** DAG-based research automation workflows.

---

## 6. Tier 3: Frontend Web Shell (`app/web/`)

The user interface is an integrated single-page application built with React 19, TypeScript, and Vite:

* **Direct Backend Serving (`install_web_build`):** Packaged frontend assets in `app/web/dist` are mounted directly by FastAPI in [`app/main.py`](../app/main.py). Static files (`/assets/*`) are served with immutable caching headers (`Cache-Control: public, max-age=31536000, immutable`).
* **Path Traversal & API Isolation:** All incoming asset requests are canonicalized to block path traversal outside `app/web/dist`. Reserved system routes (`/api`, `/events`, `/health`) bypass static handlers. Non-asset navigation requests fall back cleanly to `index.html` for client-side routing.
* **Graceful Degradation:** If the frontend build is absent, `app/main.py` yields an informative HTTP 503 response detailing build instructions (`npm --prefix app/web run build`).
* **State Management & Telemetry:** Workspace stores consume backend endpoints via typed API clients and listen to server push events via the SSE event stream.

---

## 7. Tier 4: Extensions & Dynamic Plugins (`app/plugins/` & `app/extend/`)

Extensions provide pluggable capabilities through typed slots:

### 7.1 Extension Slot Contract: `data.provider`
Market data provider plugins declare compliance with `slot: "data.provider"` in `plugin.json` and implement `BaseDataProvider` (`app/workspace/data_manager/connections.py`):
```python
class BaseDataProvider(ABC):
    provider_id: str

    @abstractmethod
    def get_available_symbols(self) -> list[str]: ...

    @abstractmethod
    def fetch_bars(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> list[Bar]: ...

    @abstractmethod
    def fetch_ticks(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[Tick]: ...

    @abstractmethod
    def test_connection(self) -> bool: ...
```

### 7.2 Active Dynamic Data Providers (`app/plugins/data_source/`)
1. **`dukascopy`:** Historical Forex and CFD tick and minute data.
2. **`darwinex`:** Institutional tick data with true bid/ask spreads.
3. **`metatrader`:** MetaTrader 4 / 5 CSV and binary history parser.
4. **`sq_equity`:** StrategyQuant stock/equity historical data.
5. **`sq_futures`:** StrategyQuant futures historical data.
6. **`crypto`:** Binance and cryptocurrency exchange feeds.
7. **`files`:** Generic local file importer (CSV, Parquet, TSV).
8. **`yahoo`:** Yahoo Finance daily and intraday bar provider.
9. **`tick_downloader`:** High-precision tick downloader engine.

---

## 8. Quality, Invariants & Verification Gates

HaruQuantAI maintains uncompromising quality standards verified by automated CI gates:

1. **Standardized Docstrings:** Every Python module begins with a standardized 5-section docstring (`Description:`, `Purpose:` with `FEAT-*`, `Key Capabilities:` with descriptive kebab-case `FR-*` tags, `Python API Usage:`, and `CLI Usage:`).
2. **Zero Silent Failures:** No bare `except:` or swallowed errors. Every operation logs explicit requirement tags.
3. **Strict Static Typing:** Python code passes `mypy --strict` and `pyright` with zero warnings.
4. **Formatting:** Enforced by `ruff` (88-character lines, PEP 604 union types, organized imports).
5. **Line Ceilings:** Physical files are capped at $\le 1000$ lines. Module docstrings are capped at $\le 100$ lines.
6. **Branch Coverage:** Minimum 80% branch coverage across retained application Python code.
7. **Architecture Gate (`scripts/check_architecture.py`):** Automatically validates AST imports, one-way layering DAG, docstring lengths, file size limits, and persistence isolation.
