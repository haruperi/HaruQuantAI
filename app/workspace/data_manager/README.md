# HaruQuantAI Authoritative Data Manager Workspace (Stage 2B)

Authoritative backend domain registry, catalog governance, and REST endpoints
for the Data Manager workspace (`app/workspace/data_manager/`), implementing
StrategyQuant X parity for market data acquisition, inspection, transformation,
and multi-format export.

---

## 1. Domain Registry (`FEAT-DATAMGR-*`, `FR-DATAMGR-*`, `DEC-DATAMGR-*`)

### 1.1 Architectural Decisions
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
- `FEAT-DATAMGR-LOG`: Audit trail and operation logging with SQX log line formatting.
- `FR-DATAMGR-LOG-AUDIT-ENTRIES`: Append, filter, and format audit records in `datamgr_logs`.
- `FR-DATAMGR-LOG-CLEAR`: Global and symbol-filtered log clearing.
- `FR-DATAMGR-LOG-OPERATION-TRACKING`: Structured operation tracking in `datamgr_operation_log`.

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
- `FEAT-DATAMGR-ROUTES`: Workspace coordination and unified FastAPI gateway endpoints.
- `FR-DATAMGR-ROUTES-WORKSPACE-FACADE`: Domain service coordinator binding all 11 modules.
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
