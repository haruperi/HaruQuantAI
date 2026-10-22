# HaruQuantAI Authoritative Data Manager Workspace (Stage 2B)

Authoritative backend domain registry, catalog governance, and REST endpoints
for the Data Manager workspace (`app/workspace/data_manager/`), covering target
market data acquisition, inspection, transformation and multi-format export.
Registered target scope does not establish independently verified donor parity.

---

## 1. Domain Registry (`FEAT-DATAMGR-*`, `FR-DATAMGR-*`, `DEC-DATAMGR-*`)

### 1.1 Architectural Decisions
- `DEC-DATAMGR-SESS-PROFILE-TEMPLATES`: Saved `datamgr_sessions` rows are
  reusable profiles/templates; no duplicate browser or entity catalog. Explicit
  IDs update existing profiles; an absent ID creates one. Intervals and holidays
  commit atomically through HostPersistence. Missing IDs never become inserts.
- `DEC-DATAMGR-SESS-WALL-CLOCK-SHIFT`: Clone offsets are integer minutes within
  +/-1440, shifting both interval endpoints with weekday/week rollover while
  preserving seconds, duration, EOD/type, broker and timezone. Holiday civil
  dates stay unchanged. This is a deliberate local-schedule adjustment, not an
  instant-preserving zone conversion or automatic DST correction.
- `DEC-DATAMGR-SESS-INTERVALS`: Each configured window is one continuous weekly
  interval with explicit start/end weekdays and HH:MM or HH:MM:SS times. Profile
  validation uses half-open intervals, permits adjacency and lunch gaps, and
  rejects overlap/zero duration. Empty profiles are unconfigured/closed. Full-day
  holidays use real unique ISO dates in the profile timezone. These configuration
  rules do not certify or change the shared TradingSession runtime evaluator.
- `DEC-DATAMGR-INSTR-SPEC-EXTENSIONS`: Instrument columns remain authoritative in
  `datamgr_instruments`. Version-1 `host_entities` payloads of type
  `datamgr_instrument_specs`, keyed by immutable symbol, hold independent
  `contract_size`, `pip_size` and full `swap_settings`; all associated writes use
  `HostPersistence.apply_batch()`. Legacy absent values return null. Monetary
  `point_value` never establishes contract size; computed `point_size` is only
  the decimal price quantum `10 ** (-decimals)`. Commission settings use versioned
  JSON in the existing TEXT column, preserving legacy numeric strings on unrelated
  edits. No schema migration or automatic browser catalog import is performed.
- `DEC-DATAMGR-DOCKABLE-SHELL`: AppDataManager supplies stable panel IDs and
  Dockview hosts the five core catalog panels with group headers hidden so the
  existing top tabs serve as the single navigation row; top-bar Arrange actions
  move, split, return or close panels programmatically and top tabs reopen them
  with retained ID identity. Browser-only layout state is not persisted in this slice.

- `DEC-DATAMGR-SELECTION-CONTEXT`: Dataset IDs resolve selection through Home's
  authoritative catalog. Backend methods return independent snapshots; no global
  active-user selection or broadcast. The browser cancels superseded requests
  and clears linked selection when the host session or catalog identity changes.
- `DEC-DATAMGR-RECORDED-PREVIEW`: Linked charts and raw-bar tables share one
  recorded OHLCV array and selected UTC timestamp. Preview is read-only, at most
  500 rows from a catalog-supplied Parquet path inside the configured data root,
  with a 32 MiB source-file limit. No generated bars, path guessing or downloads.
  Ticks, absent paths and missing files are explicitly unavailable; invalid files
  report an error. The existing decoder reads eligible files before trimming.
- `DEC-DATAMGR-SQLITE-ISOLATION`: All Data Manager modules and routes interact
  with relational persistence strictly via `app.host.persistence` helper functions
  and `resolve_connection(db_path)`. Direct `sqlite3` imports outside
  `app/host/persistence/` are strictly prohibited.
- `DEC-DATAMGR-DUAL-STORAGE`: Metadata, catalogs, profiles, sessions, quality
  audit reports, and operational logs are stored in SQLite (`datamgr_*` and
  `host_entities`), while high-volume time-series bars, ticks, and external
  indicator vectors are persisted in partitioned Parquet files under
  `{data_dir}/history/{source}/{symbol}/{timeframe}.parquet` and
  `{data_dir}/custom_data/{name}.parquet`.
- `DEC-DATAMGR-SAFE-XML`: All XML document ingestion (SQX Instruments XML,
  Sessions XML, NinjaTrader 8 TradingHours XML, Stock Groups XML, Broker XML)
  is performed safely using `defusedxml.ElementTree.fromstring` to prevent
  XXE and XML entity expansion attacks (`S314` compliant).
- `DEC-DATAMGR-ENVELOPE-PARITY`: Every HTTP endpoint in `routes.py` returns a
  standardized `ApiResponse` JSON envelope (`{"status": "success", "data": ...}`)
  matching the UI transport layer (`createDomainClient('/data')`).

### 1.2 Feature and Functional Requirements

#### Module 1: Home Dashboard (`home.py`)
- `FEAT-DATAMGR-HOME`: Dashboard metrics, storage health, entity counts, and doc links.
- `FR-DATAMGR-HOME-OVERVIEW`: Aggregate dataset, instrument, session, and provider metrics.
- `FR-DATAMGR-HOME-DATASETS-CATALOG`: Read-only saved dataset projection from
  `datamgr_datasets` through `Home.get_saved_datasets()`, shared by CLI and GET
  `/data/home/datasets`. Historical data displays this server snapshot, including
  elapsed `total_days` and stored path. Bar type uses DataInfo's `start` default
  when absent (the current dataset schema has no bar-type column). Successful
  empty results clear stale rows; loading and errors are explicit, with retry. Browser definitions
  and simulated jobs do not establish saved catalog membership. A failed refresh
  may retain the previous server snapshot only with a visible stale-data warning.
- `FR-DATAMGR-HOME-DOC-LINKS`: Curated documentation links for the Data Manager workspace.
- `FR-DATAMGR-HOME-STORAGE-AUDIT`: Parquet storage footprint and file audit.

#### Module 2: Datasets & Parquet Storage (`data.py`)
- `FEAT-DATAMGR-DATA`: Dataset catalog CRUD, Parquet bar I/O, chart review, and export.
- `FR-DATAMGR-DATA-EDIT`: `Data.edit(dataset_id: str, updates: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]`;
  updates editable columns in `datamgr_datasets` with strict type validation, UTC timestamp tracking, and structured requirement logging.
- `FR-DATAMGR-DATA-CATALOG-CRUD`: Dataset catalog management in `datamgr_datasets`.
- `FR-DATAMGR-DATA-PARQUET-IO`: OHLCV and tick Parquet read/write operations.
- `FR-DATAMGR-DATA-REVIEW-AND-EDIT`: Chart slice inspection, row review, and manual bar editing.
- `FR-DATAMGR-DATA-EXPORT-ENGINE`: CSV, MetaTrader 4, and MetaTrader 5 multi-format export.

#### Module 3: Instruments Catalog (`instruments.py`)
- `FEAT-DATAMGR-INSTRUMENTS`: InstrumentInfo specifications, trading costs, aliases, and SQX XML.
- `FR-DATAMGR-INSTR-LIST`: `Instruments.instruments(filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]`;
  lists all saved instruments via GET `/data/instruments`, with optional search,
  broker_id, connection and data_type filters. The Instruments top tab renders
  only this server catalog, with loading, empty, stale/error and retry states.
- `FR-DATAMGR-INSTR-ADD`: `Instruments.add_instrument(instrument: Mapping[str, Any]) -> dict[str, Any]`;
  POST `/data/instruments` creates a unique symbol, requiring independent positive
  contract/pip sizes, validating specifications and returning the created record.
- `FR-DATAMGR-INSTR-MASS-EDIT`: `Instruments.mass_edit_instruments(instrument_ids: Sequence[str], updates: Mapping[str, Any]) -> dict[str, Any]`;
  POST `/data/instruments/mass-edit` validates selected string IDs and changed
  fields, then atomically patches only supplied mutable fields. Single-record
  edit uses the same operation. Returns updated_count and instruments.
- `FR-DATAMGR-INSTR-CLONE`: `Instruments.clone_instrument(source_id: str, new_symbol: str) -> dict[str, Any]`;
  POST `/data/instruments/clone` copies the saved specification and extension,
  retaining broker/cost metadata with fresh identity and UTC timestamps.
- These four operations are implemented. `InstrumentsModal.tsx` awaits confirmed
  writes and preserves failed forms; no optimistic browser-only success.
  Add/clone return 201, duplicates 409, missing IDs 404, invalid input 422, and
  unavailable storage 503 through authenticated ApiResponse envelopes.
  Legacy missing contract/pip/swap settings remain explicitly unconfigured.
  Delete, import/XML, aliases, broker retargeting during clone and cross-client
  version conflict detection remain outside this slice. Unsupported Load/Delete
  workspace actions are disabled; existing JSON export is read-only.
- `FR-DATAMGR-INSTRUMENTS-MODEL`: Specification model with tick rounding and SymbolSpec conversion.
- `FR-DATAMGR-INSTRUMENTS-CATALOG-CRUD`: Instrument catalog management in `datamgr_instruments`.
- `FR-DATAMGR-INSTRUMENTS-XML-AND-ALIASES`: SQX XML import/export and symbol alias mapping.

#### Module 4: Trading Sessions & Calendars (`sessions.py`)
- `FEAT-DATAMGR-SESSIONS`: TradingSession calendar engine, schedules, holidays, and NT8 import.
- `FR-DATAMGR-SESS-LIST`: `Sessions.sessions(filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]`;
  GET `/data/sessions` lists every saved profile, including timezone, complete
  windows, holiday calendar, description, default flag and broker identity.
  Optional search/broker_id/timezone filters do not use browser seeds or caches.
- Stored-window compatibility: reads accept `day_of_week` with either
  `open_time`/`close_time` or `start_time`/`end_time`. Numeric days use the historical
  zero-based contract (0 Monday, 6 Sunday); missing EOD uses the historical target
  default False. `normalization_warnings` reports applied aliases/defaults to the
  edit form; absent EOD is not an explicitly stored False. Reads never rewrite
  rows. Explicit saves may materialize canonical fields. New API writes remain
  canonical and strict; conflicting aliases and malformed schedules fail visibly.
- `FR-DATAMGR-SESS-CLONE`: `Sessions.clone_session(session_id: str, new_name: str, *, timezone_offset: int = 0, delete: bool = False) -> dict[str, Any]`;
  POST `/data/sessions/clone` copies a saved profile to a new ID/name with an
  explicit minute shift and is_default=False. An explicitly empty source ID
  creates a UTC unconfigured draft with zero shift; an unknown nonempty ID fails.
  DELETE `/data/sessions/{id}` invokes delete=True with empty name/zero offset.
- `FR-DATAMGR-SESS-ELEMENT`: `Sessions.session_element(session_id: str, element: Mapping[str, Any]) -> dict[str, Any]`;
  POST `/data/sessions/{id}/elements` accepts add/update/remove commands, an
  optional index and window as required, and validates the full resulting
  schedule before saving. Removing all intervals leaves an explicitly closed profile.
- `FR-DATAMGR-SESS-TEMPLATE`: `Sessions.session_template(template: Mapping[str, Any]) -> dict[str, Any]`;
  POST `/data/sessions` creates or edits complete reusable profiles, including
  interval and holiday arrays, with immutable name/ID on edit. Rejects invalid
  zones/dates, unknown fields, nonconfigured broker IDs and duplicate names.
- These four methods and SessionsModal.tsx are implemented. Forms wait for
  confirmation and retain errors; existing-profile interval commands save
  immediately, with this behavior stated in the form. New profiles remain drafts
  until Save. Multi-selection deletion reports confirmed and failed IDs separately;
  it does not claim batch atomicity. Read-only JSON exports preserve all metadata.
- HTTP creation/clone returns 201; edits/delete 200, invalid input 422, missing
  IDs 404, conflicts 409 and sanitized unavailable-storage failures 503, with
  authenticated ApiResponse envelopes. Malformed stored calendars fail explicitly.
- Remaining scope: shared runtime evaluator integration/certification, automatic
  timezone conversion, partial holidays, conflict resolution across concurrent
  editors, XML/NT8/broker-session imports and instrument-session foreign keys.
  Unsupported import entry points are disabled. No schema migration or live
  exchange-calendar synchronization is part of this slice.
- `FR-DATAMGR-SESSIONS-CALENDAR-MODEL`: Day-of-week windows, RTH/ETH schedules, and holiday evaluation.
- `FR-DATAMGR-SESSIONS-CATALOG-CRUD`: Session calendar management in `datamgr_sessions`.
- `FR-DATAMGR-SESSIONS-SQX-XML`: Native SQX Sessions XML serialization and deserialization.
- `FR-DATAMGR-SESSIONS-NT8-IMPORT`: NinjaTrader 8 TradingHours template discovery and XML import.

#### Module 5: Stock Groups & Baskets (`baskets.py`)
- `FEAT-DATAMGR-BASKETS`: Stock groups, survivorship-bias-free membership, and readiness evaluation.
- `FR-DATAMGR-BASKETS-CRUD`: Stock group and constituent management in `datamgr_stock_group` / `datamgr_stock`.
- `FR-DATAMGR-BASKETS-OVERVIEW-READINESS`: 8-column overview with downloaded dataset readiness cross-referencing.
- `FR-DATAMGR-BASKETS-CSV-AND-XML`: Constituent CSV and SQX Groups XML import/export.
- `FR-DATAMGR-BASKETS-DATA-UPDATE`: Batch dataset provisioning for basket constituents.

#### Module 6: Broker Profiles (`broker.py`)
- `FEAT-DATAMGR-BROKER`: Broker profiles, stock ticker lists, and selective instrument/session import.
- `FR-DATAMGR-BROKER-PROFILE-CRUD`: Broker profile governance in `datamgr_broker`.
- `FR-DATAMGR-BROKER-STOCKS-MANAGEMENT`: Broker stock ticker lists in `datamgr_broker_stock`.
- `FR-DATAMGR-BROKER-XML-TRANSFER`: SQX Broker XML transfer and selective component import.

#### Module 7: Data Provider Connections (`connections.py`)
- `FEAT-DATAMGR-CONNECTIONS`: BaseDataProvider protocol, connection health, and download jobs.
- `FR-DATAMGR-CONNECTIONS-PROVIDER-PROTOCOL`: BaseDataProvider plugin protocol for data sources.
- `FR-DATAMGR-CONNECTIONS-HEALTH-CHECK`: Connection probing and status reporting.
- `FR-DATAMGR-CONNECTIONS-DOWNLOAD-ORCHESTRATOR`: Historical bar and tick download orchestration.
- `FR-DATAMGR-CONNECTIONS-EVENT-BROADCAST`: EventBus publication for dataset updates.

#### Module 8: Custom Data & External Indicators (`custom_data.py`)
- `FEAT-DATAMGR-CUSTOM-DATA`: External indicators, macroeconomic series, and .mq4 recognition.
- `FR-DATAMGR-CUSTOM-DATA-CRUD`: Custom indicator definitions in `host_entities`.
- `FR-DATAMGR-CUSTOM-DATA-CSV-IMPORT`: Time-series CSV parsing and timeframe inference.
- `FR-DATAMGR-CUSTOM-DATA-MQ4-RECOGNIZER`: MetaTrader 4 .mq4 buffer recognition.

#### Module 9: Audit & Operation Logging (`log.py`)
- `FEAT-DATAMGR-LOG`: Real-time WebSocket log viewer and operation progress/cancellation controls for Data Manager data operations.
- `FR-DATAMGR-LOG-STREAM`: `DataLog.data_log(limit: int = 100) -> list[dict[str, Any]]`; reads and normalizes persisted download, import, and export records from `datamgr_logs` and `datamgr_operation_log`, and streams live log/progress payloads over the host `EventBus` `"logs"` channel (`GET /data/logs`, `POST /data/logs`, `/api/v1/ws?channels=logs,jobs`).
- `FR-DATAMGR-LOG-CLEAR`: `DataLog.clear_log() -> dict[str, Any]`; clears persisted operation/audit logs in `datamgr_logs` and `datamgr_operation_log`, resets operation progress/cancellation state, and broadcasts `"datamgr.log.cleared"` (`POST /data/logs/clear`).

#### Module 10: Help & FAQ Catalog (`help.py`)
- `FEAT-DATAMGR-HELP`: Built-in contextual documentation and interactive tutorial guides for Data Manager operations.
- `FR-DATAMGR-HELP-GUIDE`: `DMHelp.help(topic: str = "overview") -> dict[str, Any]`; returns deterministic contextual documentation summaries, supported topic catalog, and step-by-step data management tutorials (`GET /data/help`).

#### Module 11A: Data Quality Inspection (`actions/review/quality.py`)
- `FEAT-DATAMGR-QUALITY`: Gap detection, weekend checks, OHLC envelope verification, and quality reports.
- `FR-DATAMGR-QUALITY-INSPECTION`: Anomaly scanning for gaps, spikes, envelopes, and weekends.
- `FR-DATAMGR-QUALITY-SCORE-AND-PERSISTENCE`: Deterministic quality scoring and `datamgr_quality` persistence.
- `FR-DATAMGR-QUALITY-SUMMARY-AND-DETAILS`: Summary metrics and paginated anomaly inspection.

#### Module 11B: Series Transforms (`actions/transform/transforms.py`)
- `FEAT-DATAMGR-TRANSFORMS`: Timeframe resampling, timezone cloning, and session filtering.
- `FR-DATAMGR-TRANSFORMS-RESAMPLE`: Bar and tick resampling into higher timeframe series.
- `FR-DATAMGR-TRANSFORMS-TIMEZONE-CLONE`: Timezone shifting and weekend bar removal.
- `FR-DATAMGR-TRANSFORMS-SESSION-ALIGNMENT`: Calendar-based session schedule filtering.

#### Unified Workspace Router (`routes.py`)
- `FEAT-DATAMGR-SHELL`: Data Manager workspace Dockview container. Implemented
  scope: core dockable Instruments, Sessions, Brokers, Data and Custom Data
  panels, auxiliary Home/Stock groups/Log/Chart panels, and linked recorded preview.
- `FR-DATAMGR-SHELL-INIT`: `AppDataManager.init_workspace() -> dict[str, Any]`;
  returns deterministic panel descriptors and default layout through GET
  `/data/workspace`. Core panels open in one group, with Chart available as a split.
- `FR-DATAMGR-SHELL-TAB`: `AppDataManager.open_tab(tab_id: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]`;
  validates tab/context, resolves an optional `dataset_id`, and returns selection
  plus bounded recorded preview through POST `/data/workspace/tabs/{tab_id}`.
  Unsupported context is 422; unknown dataset is 404. Existing authentication
  applies. The frontend synchronizes dataset identity and chart/table cursors.
- Remaining scope: layout persistence/popouts, tick preview, history reconciliation,
  missing backend domain CRUD/provider services and replacement of existing
  simulated provider flows. Shell integration does not establish those behaviors.
- `FEAT-DATAMGR-ROUTES`: Workspace coordination and unified FastAPI gateway endpoints.
- `FR-DATAMGR-ROUTES-WORKSPACE-FACADE`: Host composition of AppDataManager and the
  retained Home catalog service; no claim that absent domain services are bound.
- `FR-DATAMGR-ROUTES-FASTAPI-GATEWAY`: REST router exposing endpoints under `/data`.

---

## 2. Relational Schema & Persistence Mapping

All tables reside in the SQLite database and are accessed via `app.host.persistence` without direct `sqlite3` calls:

| Table Name | Entity Type | Primary Key | Key Columns |
| :--- | :--- | :--- | :--- |
| `datamgr_broker` | Broker Profiles | `(id,)` | `name`, `server_timezone`, `postfix`, `is_system`, `enabled` |
| `datamgr_broker_stock` | Broker Stocks | `(ID,)` | `TICKER`, `BROKER_ID` |
| `datamgr_commodities` | Commodities | `(id,)` | `code`, `name`, `point_value`, `tick_size`, `tick_step` |
| `datamgr_crypto_catalog` | Crypto Catalog | `(exchange, symbol)` | `point_value`, `tick_size`, `default_spread`, `price_precision` |
| `datamgr_datasets` | Datasets | `(id,)` | `source`, `symbol`, `timeframe`, `broker`, `bars`, `date_from`, `date_to` |
| `datamgr_instruments` | Instruments | `(id,)` | `symbol`, `tick_size`, `point_value`, `decimals`, `margin_rate` |
| `datamgr_logs` | Audit Logs | `(id,)` | `timestamp_utc`, `action`, `message`, `symbol`, `details` |
| `datamgr_operation_log` | Operation Logs | `(id,)` | `timestamp_utc`, `symbol`, `operation`, `status`, `message` |
| `datamgr_quality` | Quality Reports | `(report_id,)` | `dataset_id`, `quality_score`, `total_records`, `anomalies_json` |
| `datamgr_sessions` | Trading Sessions| `(id,)` | `name`, `timezone`, `windows_json`, `holidays_json`, `is_default` |
| `datamgr_stock` | Basket Stocks | `(ID,)` | `TICKER`, `BASKET_ID`, `DATE_FROM`, `DATE_TO` |
| `datamgr_stock_group` | Basket Groups | `(ID,)` | `NAME`, `SYSTEM`, `DESC`, `description` |
| `datamgr_tickers` | Tickers | `(id,)` | `ticker`, `name`, `exchange`, `timeframe` |
| `host_entities` | Custom Data/Formats | `(entity_id, entity_type)` | Custom indicators, CSV formats, symbol aliases |

---

## 3. Partitioned Parquet Storage Layout

High-frequency bars and ticks are stored as Apache Parquet files:
- Datasets: `{data_dir}/history/{source}/{symbol}/{timeframe}.parquet`
- Custom Data: `{data_dir}/custom_data/{name}.parquet`
- Parquet columns: `timestamp` (UTC ISO string or int ms), `open`, `high`, `low`, `close`, `volume`, `spread`.
