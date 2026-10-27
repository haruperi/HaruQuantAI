# Data Manager functional coverage review

Reviewed: 2026-10-27

Implementation update: 2026-10-27. The functionality-first implementation is now present. Historical names and paths were disregarded; working storage, codecs, provider adapters, host connections and job infrastructure were reused.

**Coverage: 71 implemented; 3 partial pending external acceptance (11, 44, 62).** “Implemented” means repository behavior is present and exercised by automated checks; it does not certify a paid account or a terminal version we cannot access. No live provider account, subscription or running trading terminal was supplied.

## Validation

- Backend: 428 tests passed across Data Manager, broker adapters, host transport, application startup and credential-vault boundaries.
- Frontend: TypeScript check passed; 642 unit tests passed across the frontend.
- Browser: 13 Playwright checks passed for workspace selection, broker persistence contracts and dataset property editing. Browser transport fixtures verify UI contracts; separate HTTP/worker integration tests verify actual Parquet persistence, review and artifact delivery.
- Windows Credential Vault: real store/read/revoke round trip and repeated deletion passed, using a generated disposable secret.
- New integration checks cover uploaded content, custom time parsing, canonical prices, review pagination/resampling/edit/deletion, saved-session gap analysis, cache removal, binary HST layout, CSV/MT5 prices, persistent clone timestamps, broker imports and credential rotation.
- MT5 bridge tests exercise asynchronous history publication on its owning event loop. A physical terminal was not connected. MT4 binary layout is checked independently, but terminal/tester import is not certified.

## Implementation boundaries

- Exactly eight new runtime files and eight new test files; no new dependencies, second storage engine, MT4 codec facade, provider-specific import facade or second MT5 transport.
- XML import accepts the versioned application schema; arbitrary vendor XML is rejected. BMF/B3 registration uses existing symbol and file/terminal ingestion rather than inventing an exchange feed.
- Public history reads never count as proof of authenticated paid subscription access. Connection tests return separate authentication, access and observed-history outcomes, including unknown states.
- Native review pages are read lazily. Resampling, session filtering, edits, cloning and exports currently materialize the selected history; restrict selected date ranges for very large histories. Uploaded inputs are bounded to 25 MB per request.
- Canonical cache removal only deletes retired manifest files within their dataset root when no current catalog references them. Legacy user-owned input files are preserved.
- MT5 bar exports accept fixed spread in points. Pips require a configured conversion and remain visibly unavailable; real spread requires stored bid/ask ticks. Stored bar history cannot manufacture it.
- Local CSV format preferences remain local, as previously supported. Offline fallback is a labelled read-only dashboard/catalog snapshot, scoped to host and session; it is not an offline price database.

## Functional checklist

### DataManagerInstruments

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 01 | list all configured instruments with point/pip sizes, contract sizes, and margins | Implemented | Catalog lists pricing, contract and margin specifications. |
| 02 | add new instrument specifications to SQLite database | Implemented | SQLite creation and duplicate handling. |
| 03 | edit one or more existing instrument definitions in bulk | Implemented | Single and transactional bulk editing. |
| 04 | clone an existing instrument to create a new specification | Implemented | Clone with new identity and specification overrides. |

### DataManagerSessions

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 05 | list all trading session profiles and holiday calendars | Implemented | Profiles include timezone, intervals and full-day holidays. |
| 06 | create, clone, and delete trading sessions with timezone shifts | Implemented | Create, clone and delete; cloning supports a fixed schedule shift in minutes, not timezone conversion of holidays. |
| 07 | add and configure session time intervals (daily open, close, lunch pauses) | Implemented | Multiple recurring intervals represent opening, closing and lunch gaps. |
| 08 | configure and save reusable session templates | Implemented | Named profiles are reusable and support JSON save/load. |

### DataManagerConnections

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 09 | list all external market data provider connections | Implemented | One provider connection editor lists host-owned connection metadata and selects it for provider operations. |
| 10 | add or edit external market data provider credentials | Implemented | Host connection create/update rotates OS-vault credentials; browser metadata contains references only. Stored credentials reach existing provider clients. |
| 11 | test real-time connectivity and authenticate data subscription feeds | Partial | Real endpoint status and bounded provider-history reads distinguish denial, unknown authentication and verified history access. Live paid subscription authentication remains unverified without provider accounts. |

### DataManagerBroker

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 12 | list all broker profiles configured in the system | Implemented | Persistent broker profile listing. |
| 13 | add or edit broker profiles with custom spread and commission models | Implemented | Broker profiles persist validated inherited/fixed spread and existing commission-model shapes; UI edits defaults. |
| 14 | edit stock symbols assigned to a broker profile | Implemented | Persistent stock membership read/write with validation. |
| 15 | import instrument definitions from external XML/JSON files | Implemented | Shared JSON/versioned-XML parsing and transactional per-record imports reuse symbol validators and report confirmed outcomes. |
| 16 | import trading session definitions from external XML/JSON files | Implemented | Shared JSON/versioned-XML imports preserve session intervals, timezone and holidays with confirmed per-record results. |

### DataManagerBasket

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 17 | list all stock baskets and symbol groupings | Implemented | Persistent group and membership listing. |
| 18 | create new stock basket groups (e.g. S&P 500, Tech, Forex Majors) | Implemented | Create named baskets. |
| 19 | edit and maintain symbol membership in selected baskets | Implemented | Edit membership, including membership transfer operations. |

### DataManagerData

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 20 | list all imported price data symbols with timeframes, date ranges, and bar counts | Implemented | Persistent dataset catalog includes timeframe, coverage dates and bar counts. |
| 21 | edit symbol properties, associated broker profile, and session template | Implemented | Dataset properties persist symbol, broker, specification/session links, category and display zone. Nonempty rename republishes actual prices and keeps the stable dataset identity. |
| 22 | confirm and delete selected price data symbols and clear cached bar files | Implemented | Confirmation and catalog clear/delete now remove unreferenced owned canonical cache files; legacy input and shared files are preserved. |
| 23 | add BMF futures data symbols to the database | Implemented | Generic symbol/dataset registration persists BMF/B3 exchange and contract expiry without a redundant registration API. |

### DataSourceFiles

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 24 | add new symbol definition from local historical data file | Implemented | Uploaded CSV/TXT/TSV content and custom formats are parsed, validated and published to canonical storage by real jobs. |
| 25 | import price data from local files into Parquet storage | Implemented | Existing symbol-definition persistence is used by the local-file add flow; dataset links are validated. |
| 26 | import price data directly from external trading applications | Implemented | Existing HST/FXT readers import actual MT4 local history through the shared importer. MT5 uses its existing connected terminal bridge; live acceptance is tracked under 44. |
| 27 | define and save custom text/CSV file delimiter and column formats | Implemented | Custom delimiter and column formats can be saved in browser storage; not a backend format registry. |
| 28 | perform bulk mass import of multiple data files across directories | Implemented | Mass file import submits actual contents and overwrite policy to the shared worker with bounded input and real progress. |

### DataSourceYahoo

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 29 | add Yahoo Finance data symbols to the database | Implemented | Persistent registration via generic historical source service. |
| 30 | download historical OHLCV price bars from Yahoo Finance | Implemented | Historical OHLCV download uses provider client and canonical storage pipeline. |

### DataSourceDukascopy

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 31 | add Dukascopy data symbols to the database | Implemented | Persistent source registration. |
| 32 | identify and select instruments for Dukascopy data | Implemented | Provider catalog and selection UI. |
| 33 | display provider CDN data disclaimer | Implemented | CDN/provider information UI exists. |
| 34 | display Dukascopy data disclaimer | Implemented | Data disclaimer UI exists. |
| 35 | download and import Dukascopy tick and minute price data | Implemented | Tick and minute ingestion pipeline, background jobs and canonical storage. |

### DataSourceCrypto

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 36 | add cryptocurrency data symbols and exchange pairs to database | Implemented | Persistent exchange and pair registration for supported exchanges. |
| 37 | download and import historical crypto candlestick data | Implemented | Candlestick ingestion through exchange adapters and canonical storage. |

### DataSourceTD

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 38 | import historical tick and minute price data generated by TickDownloader | Implemented | TickDownloader selected files/archives flow through the actual parser, canonical publisher and existing job controls. |

### DataSourceDarwinex

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 39 | add Darwinex data symbols to the database | Implemented | Persistent registration via generic historical source service. |
| 40 | display Darwinex data disclaimer | Implemented | Active source dialog displays provider-specific Darwinex conditions alongside the existing provider flow. |
| 41 | download data from Darwinex | Implemented | Provider download and canonical storage pipeline. |
| 42 | import data downloaded from Darwinex | Implemented | Selected Darwinex DAT/CSV/archive content is ingested through existing decoders and the shared file worker. |
| 43 | identify and select instruments for Darwinex data | Implemented | Active provider catalog requests use the existing adapter and chosen connection; unavailable catalogs return an explicit error. |

### DataSourceMt5Api

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 44 | import price data directly from MetaTrader 5 terminal via Python API | Partial | Existing MT5 bridge history is exercised by event-loop/publication tests and disconnected-state checks. A connected live terminal remains required for external acceptance; no second adapter was created. |

### DataSourceEquities

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 45 | add US equities data symbols to database | Implemented | Persistent SQ equity registration. |
| 46 | display equities data usage terms and conditions | Implemented | Active source dialog presents equity usage conditions. |
| 47 | update existing equity historical data with latest trading sessions | Implemented | Existing saved equity datasets can download additional requested date ranges through real jobs; native data resolution is daily. |

### DataSourceFutures

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 48 | add futures data symbols to database | Implemented | Persistent SQ futures registration. |
| 49 | display futures data usage conditions | Implemented | Active source dialog presents futures usage conditions. |
| 50 | update existing futures historical data with latest session bars | Implemented | Existing saved futures datasets can download additional requested date ranges through real jobs; native data resolution is daily. |

### DataManagerCustomData

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 51 | list all custom and external data series | Implemented | Persistent definitions and observations listing. |
| 52 | add external indicators and non-price custom data to database | Implemented | Create indicator and non-price series definitions. |
| 53 | update Commitments of Traders (COT) historical data reports | Implemented | Existing COT retrieval/parsing/persistence is retained and uses shared real job tracking with surfaced failures. Live provider availability is not certified. |
| 54 | import custom indicator and macro series from files | Implemented | Custom indicator import submits actual file content to backend jobs, confirms persistence and surfaces failures. |
| 55 | create new data format definitions for custom data import | Implemented | Custom import format services and UI exist. |
| 56 | recognize custom data structure and delimiters automatically from file | Implemented | Delimiter and structure recognition service and UI exist. |
| 57 | view custom data records in table and interactive chart | Implemented | Custom observations have real pagination and an interactive chart of the displayed page. |
| 58 | confirm deletion of custom data series | Implemented | Confirmation UI and persistent delete/clear operations. |

### DataManagerActions

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 59 | clone price data to a specified timezone offset with bar timestamp shifts | Implemented | A real clone worker publishes copied history with explicit fixed timestamp shifts or named-zone display metadata, source revision lineage and weekend policy. |
| 60 | export price data to CSV format with custom headers and delimiters | Implemented | Actual historical queries produce CSV artifacts with custom headers/tokens/delimiters, chosen range/session/zone and file prefix; authenticated download delivers completed files. |
| 61 | create new CSV export format configurations | Implemented | Custom CSV templates can be saved locally; remote format registry methods target absent routes. |
| 62 | export price data to MetaTrader 4 FXT and HST files | Partial | Actual recorded bars reach existing HST/FXT encoders directly and completed binary artifacts download. HST layout is checked independently. Live MT4 tester compatibility remains an external acceptance gate. |
| 63 | export price data to MetaTrader 5 format | Implemented | Actual recorded bars/ticks produce downloadable MT5 import CSV. Fixed bar spreads are in points; unsupported real bar spread is rejected. |
| 64 | open data review modal to view data details and summary statistics | Implemented | Real stored observations, count/range/extrema and revision-backed edits replace generated review data. |
| 65 | display interactive candlestick price chart in data review | Implemented | Interactive candlestick chart receives the same stored price query as the review table. |
| 66 | display raw bar table in data review | Implemented | Paginated stored-price table uses stable timestamp identities and revision-checked edit/delete publication. |
| 67 | perform data quality audit and gap analysis across timeframes | Implemented | Actual-history audit reports invalid bars/quotes, duplicates, spikes and timeframe gaps using saved session calendars and holidays; no synthetic tick-gap expectation. |

### AppDataManager

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 68 | host dockable tabs for Instruments, Sessions, Brokers, Data, and Custom Data | Implemented | Dockview workspace exposes the required catalog panels. |
| 69 | coordinate active symbol selections and synchronize data tables with charts | Implemented | Workspace tab activation returns the selected dataset and actual preview prices, preserving linked table/chart context. |

### DataManagerLog

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 70 | stream live data download, import, and export logs via WebSocket | Implemented | Import, export, clone, custom and source operations reuse existing backend jobs and Logs publication; existing host subscriptions receive progress/error events. |
| 71 | display progress bars, error highlights, and cancellation controls | Implemented | Production import/export/clone/custom paths track real backend jobs and pause/resume/stop outcomes; no timer-based completion claims. |

### DataManagerHome

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 72 | display Data Manager overview with disk storage usage and symbol counts | Implemented | One home snapshot reports actual catalog counts, bars, active providers, deduplicated published file bytes/count, missing files and disk free space. |
| 73 | provide offline fallback view when internet connectivity is lost | Implemented | Host/session-scoped last-known dashboard and catalog snapshots survive reload, carry capture time and display explicit stale/offline status; reconnect refreshes. |

### DataManagerHelp

| ID | Functionality | Status | Finding |
|---|---|---|---|
| 74 | display contextual documentation and tutorials for data management operations | Implemented | Contextual topics, articles, tutorials and search services/UI exist. |

## External acceptance still open

1. **11:** use each intended paid provider account to verify authentication and entitlement. The UI reports unknown states until evidence exists; public history success does not close this gate.
2. **44:** connect the actual MT5 terminal EA/bridge, import a known interval and compare persisted timestamps/prices with that terminal.
3. **62:** import produced HST/FXT files into the intended MT4 terminal/tester version and compare history/model behavior. Existing codec presence and a passing round trip do not prove tester compatibility.

The application changes are implemented and regression-tested; these three external acceptance gates remain explicit rather than being marked complete without evidence.
