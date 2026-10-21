# HaruQuantAI Authoritative Data Manager Workspace (Stage 2B)

Authoritative backend domain registry, catalog governance, and REST endpoints
for the Data Manager workspace (`app/workspace/data_manager/`), implementing
StrategyQuant X parity for market data acquisition, inspection, transformation,
and multi-format export.

---

## 1. Domain Registry (`FEAT-DATAMGR-*`, `FR-DATAMGR-*`, `DEC-DATAMGR-*`)

### 1.1 Architectural Decisions
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
- `FR-DATAMGR-DATA-CATALOG-CRUD`: Dataset catalog management in `datamgr_datasets`.
- `FR-DATAMGR-DATA-PARQUET-IO`: OHLCV and tick Parquet read/write operations.
- `FR-DATAMGR-DATA-REVIEW-AND-EDIT`: Chart slice inspection, row review, and manual bar editing.
- `FR-DATAMGR-DATA-EXPORT-ENGINE`: CSV, MetaTrader 4, and MetaTrader 5 multi-format export.

#### Module 3: Instruments Catalog (`instruments.py`)
- `FEAT-DATAMGR-INSTRUMENTS`: InstrumentInfo specifications, trading costs, aliases, and SQX XML.
- `FR-DATAMGR-INSTRUMENTS-MODEL`: Specification model with tick rounding and SymbolSpec conversion.
- `FR-DATAMGR-INSTRUMENTS-CATALOG-CRUD`: Instrument catalog management in `datamgr_instruments`.
- `FR-DATAMGR-INSTRUMENTS-XML-AND-ALIASES`: SQX XML import/export and symbol alias mapping.

#### Module 4: Trading Sessions & Calendars (`sessions.py`)
- `FEAT-DATAMGR-SESSIONS`: TradingSession calendar engine, schedules, holidays, and NT8 import.
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
- `FEAT-DATAMGR-HELP`: Contextual workflow guides and searchable FAQ items.
- `FR-DATAMGR-HELP-TOPICS`: Structured help topics for every Data Manager view.
- `FR-DATAMGR-HELP-FAQ-SEARCH`: Full-text and tag search across Data Manager FAQs.

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
