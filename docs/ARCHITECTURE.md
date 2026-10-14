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

### 4.1 Bootstrap & Lifecycle Management (`app/host/bootstrap.py`, `app/main.py`, `app/cli.py`)
The host boot sequence executes sequentially through 7 ordered stages (`CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES -> READY`) for both the UI/FastAPI server entrypoint (`app/main.py`) and the headless CLI entrypoint (`app/cli.py`):
1. **CONFIGURING:** Validates host bind address, port, debug flags, and runtime thresholds.
2. **PATHS:** Creates and inspects workspace directories (`database`, `logs`, `scratch`, `plugins`, `resources`).
3. **LOGGING:** Initializes asynchronous multi-sink telemetry (`app.log`, `access.log`, `errors.log`), SHA-256 secret redaction, and the 2000-record ring buffer.
4. **PERSISTENCE:** Configures SQLite WAL mode (`busy_timeout=5000`), initializes all 25 operational tables via `app/host/persistence/create.py`, and reloads `settings`.
5. **SERVICES:** Starts `SessionManager`, `ResourceManager` (`MemoryWatchdog`), `JobManager` (reconciling orphan `RUNNING` jobs to `INTERRUPTED`), `PluginLifecycleManager` (scanning and attaching dynamic plugins), and `TransportGatewayService`.
6. **ROUTES:** Mounts FastAPI gateway & discovery REST/SSE/WebSocket routers (or headless CLI command dispatchers).
7. **READY & Reverse LIFO Teardown:** Transitions to `READY` and guarantees reverse-order (LIFO) teardown (`READY -> ROUTES -> SERVICES -> PERSISTENCE -> LOGGING -> PATHS -> CONFIGURING`) on stop or failure.

### 4.2 Dynamic Plugin Discovery Engine (`app/host/discovery.py`)
* **Manifest Verification:** Inspects each plugin directory for a valid `plugin.json` declaring `id`, `name`, `version`, `slot`, `entry_point`, and `capabilities`.
* **Dynamic Import Isolation:** Loads plugin modules dynamically using `importlib.util.spec_from_file_location` without hard-coded package dependencies.
* **Instance Registry:** Provides `get_instance(plugin_id)` and `get_instances_for_slot(slot_id)` with lazy instantiation and thread-safe caching.

### 4.3 Persistence & Storage Custody (`app/host/persistence/`)
* **SQLite Import Isolation:** Enforces strict isolation: `sqlite3` must NEVER be imported anywhere outside `app/host/persistence/`. Violations trigger immediate test failures.
* **WAL Mode & Concurrency:** Configured with `journal_mode=WAL`, `synchronous=NORMAL`, and `busy_timeout=5000` for robust concurrent read/write operations.
* **Single DDL Ownership & Functional CRUD Modules:** `app/host/persistence/create.py` is the sole owner of canonical table creation (`create_schema`) and connection configuration (`get_connection`), paired with typed functional CRUD operations in `read.py`, `update.py`, and `delete.py`.
* **CRUD-only Boundary:** Functional CRUD helpers (`list_host_settings`, `batch_save_host_settings`, `save_host_session`, `get_host_session_by_token_hash`, `save_host_job`, `list_host_jobs`, `reconcile_running_host_jobs`) group related row operations without redundant `*Store` wrapper classes. No application module outside `app/host/persistence/` may execute SQL or borrow connections/cursors. Settings batches acquire `BEGIN IMMEDIATE` before reading the revision, then validate and mutate in one transaction. Empty batches retain their revision; caller connections with an active transaction are rejected without committing or rolling it back.
* **Business Owners:** `settings.py` owns configuration retrieval, revision tracking, and atomic batch updates; `jobs.py` owns job lifecycle and worker leases; `session.py` owns scope binding/authorization, password authentication, local credential provisioning, and ephemeral session invalidation; `bootstrap.py` sequences recovery; `resources.py` owns database/workspace path inspection, hardware/storage diagnostics, worker sizing, memory watchdogs, scratch sandboxing, and their HTTP/CLI access. Persistence remains CRUD and its required database infrastructure only.
* **Regression Guard:** AST architecture tests enforce database-driver/SQL/handle isolation and prohibit service/transport dependencies in persistence.
* **Default Ownership:** Workspace models/services supply business defaults, complete creation records, domain timestamps and dataset conflict-update columns. Persistence does not invent trading values, session definitions, dataset IDs or quality scores. Existing schema defaults, storage audit timestamps, serialization limits and revision checks remain database infrastructure.

### 4.4 System Diagnostics, Resource Governance & Memory Watchdog (`app/host/resources.py`)
* **Hardware, Storage & Database Inspection:** Inspects CPU cores, RAM headroom, disk space, and host process metrics via `psutil`, alongside read-only SQLite database and workspace directory health probes.
* **Core Allocation Policy:** Derives worker concurrency limits using $\text{workers} = \max(1, \text{cpu\_cores} - 2)$ by default (plus explicit `single`, `reserve-one`, `maximum`, and `custom` modes), CPU core affinity, GPU qualification, and computational benchmarking.
* **Active Memory Watchdog:** Monitors live system RAM headroom and rejects or pauses tasks if available system RAM drops below 15%, alongside data-frame (`warn`/`stop`/`off`) and periodic memory cleanup guards.
* **Temporary Storage Sandboxing:** Allocates isolated scratch directories per task/job with automatic cleanup.

### 4.5 Transports & Uniform Response Envelope (`app/host/transport.py`, `app/host/response.py`)
* **Uniform Envelopes:** Standard API responses follow `StandardResponse`, guaranteeing consistent formatting (`status`, `message`, `data`, `error`, `metadata`).
* **Error Handling:** RFC 7807 / structured error schemas (`StandardError`) prevent leaked stack traces or sensitive internals.
* **Telemetry Delivery & Lifecycle:** Log entries are automatically fingerprinted and forwarded from the asynchronous telemetry listener to the `logs` channel; subscriber delivery runs on its owning event loop with bounded pending callbacks and recursive broker diagnostics excluded. Configured authentication and capability scopes protect settings, diagnostics/resources, and job reads/cancellation. All three file sinks share the asynchronous queue. Partial service acquisition is registered for cleanup before initialization, and telemetry is drained and stopped after final teardown diagnostics.
* **Event Bus & Gateway Routes:** In-memory asynchronous pub/sub event distribution (`EventBus`) and FastAPI REST/SSE/WS endpoints (`/api/v1/auth/login`, `/api/v1/sessions/me`, `/api/v1/settings`, `/api/v1/diagnostics`, `/api/v1/resources`, `/api/v1/jobs`, `/api/v1/events`, `/api/v1/ws`).

### 4.6 Multiprocessing Background Job Coordinator (`app/host/jobs.py`)
* **Multiprocessing Worker Pool:** Executes compute-intensive and long-running tasks via an OS process pool (`concurrent.futures.ProcessPoolExecutor`) to bypass Python's Global Interpreter Lock (GIL), gated by the `resources.py` memory watchdog.
* **Cooperative Cancellation (`JobContext`):** Provides cooperative cancellation tokens (`JobContext`) and isolated scratch paths allowing safe termination when task code next checks its cancellation token; arbitrary code without checkpoints cannot be interrupted immediately.
* **Job States & Restart Reconciliation:** Manages `QUEUED`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, and `INTERRUPTED` states; on system boot, orphan jobs left in `RUNNING` state are marked `INTERRUPTED`.

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

`_HostSettings` (`settings` in `app/host/settings.py`) directly composes `app/host/persistence/read.py` (`list_host_settings`) and `app/host/persistence/update.py` (`batch_save_host_settings`) for retrieval and revision-checked atomic batch updates. The global `settings` instance is lazy and bootstrap binds it to the database path rather than a borrowed connection; scoped dot access uses cached values, `update_batch()` serializes cache refresh, and `reload()` observes other writers. Read failures propagate and preserve the last successful snapshot. Filesystem probes belong in `resources.py`. Authenticated UI reads and writes use this `settings -> app/host/persistence/` path, and `transport.py` publishes `settings.changed` notifications to the `EventBus` after committed HTTP writes. Open dialogs submit against their opening revision; stale drafts are rejected (`RevisionConflictError` / HTTP 409), and failed saves retain drafts. Host settings are not stored in browser local storage. Remote/SMTP preferences do not activate their services or persist passwords.


Browser host sessions retain their opaque token and server-issued 24-hour expiry
in host-scoped versioned local storage. HostConnection validates /sessions/me on
reload before loading settings and resuming SSE; it does not mint a new session.
Passwords are not stored, and expiry/revocation/credential changes remove the
saved session when rejected. Network outages and component cleanup preserve it.
Server sessions still reside in the shared runtime SessionManager; backend
restart invalidates them. Browser storage failures are surfaced explicitly.

The seven-tab Configuration UI follows SQX reference presentation while retaining
HaruQuantAI settings storage contracts. `settings.py` validates preference types
and modes; `app/host/persistence/update.py` owns all SQL and atomic row writes. The
data-frame guard is a warn/stop/off preference; memory cleanup uses 0 minutes for
never. Default databank sync uses null for never and 0 for immediately. CPU count
is runtime status, not a database preference. Java/engine/browser execution
effects belong to their capability owners. Applying defaults to all existing
databanks requires a future backend databank capability; settings must not invent
that operation or claim it succeeded after saving a global default.
### Host settings UI catalogue and account boundary

Host settings forms use a settings-owned field catalogue with an HTTP allowlist,
primitive/list validation and recursive secret redaction. Nested application
records are the sole persisted preferences/account source; dotted HTTP names are
in-memory aliases. Explicit revision-checked saves merge JSON leaves atomically through
`settings.update_batch() -> batch_save_host_settings()`. No startup migration or ad-hoc SQL
is introduced. Unknown metadata and system-owned revision/bound port are read-only.

Notification, broker and AI credentials use write-only replacement/clear controls;
secret values are never returned to the browser or persisted in its UI store.
Account password verification/hashing and all-session revocation belong to
`session.py`; settings.py owns configuration retrieval/validation/update. The
User access form cannot disable authentication or reduce sessions below 24 hours.
Saving preferences does not implement or activate their owning runtime capability.

The stored backend port is the `backend_port` JSON leaf in the existing
`application/app_general` settings record. Runtime catalogue metadata must not
duplicate it. The obsolete `host_sessions` table is removed only through explicit
backed-up maintenance. The retained `host_session` table is not used to resurrect
tokens; `SessionManager` remains the in-memory login authority.

Host session issuance from UI or CLI/Python persists lifecycle metadata through
`persistence.HostSessionStore` into the existing `host_session` table. Token hashing,
IDs, timestamps and lifecycle policy belong to `session.py`; SQL and transactions
remain exclusive to `persistence.py`. Database records contain no bearer tokens,
roles or elevated grants and cannot restore authority after restart. Revocation
updates are issuer-scoped, and failed persistence cannot issue a usable token.
