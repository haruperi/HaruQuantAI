# Data Manager backend

Status: resource/attachment boundary candidate; Dukascopy direct acquisition
passes offline fixture tests, with live acquisition unavailable.
The workspace owns workflow semantics, not host resource custody or plugin logic.
`workspace.py` declares `data_source.presentation@1.0.0` and
`data_source.acquisition@1.0.0` slots and prepares `resources.list`,
`resources.read`, `capabilities`, and source operation forwarding. With no providers,
retained authorized resources remain inspectable; acquisition stays unavailable.

Preparation requires `host.resources@1.0.0`; there are no peer imports or raw SQL.
The host validates packaging and literal metadata before loading `prepare` and
injects immutable child bindings. Shutdown drops local handles, never stored data.
The corresponding UI migration/removal qualification is pending. This README does
not claim full workspace qualification, market-data ingestion or live persistence
migration. See the current ownership-removal task walkthrough for actual evidence.

## Feature registry

| Feature | Requirement | Contract | Current implementation and qualification |
| --- | --- | --- | --- |
| `FEAT-DM-DUKASCOPY_ACQUISITION` | `FR-DATA-001` | `plugin.data_manager.dukascopy` in `data_source.acquisition@1.0.0`; host owns network, jobs and market storage | Isolated fixture direct M1 and Tick jobs pass tests. Adaptive rate throttling, Sunday 19:00 UTC start, and StrategyQuant CDN transport (global and Hong Kong) with fallback to direct download are qualified. Active catalog migration remains required before live downloads execute. |
| `FEAT-DM-ACTIONS` | `FR-DATA-002` | `actions.*` operations in `app/workspace/DataManager/actions.py` invoked through workspace dispatcher and CLI | 1:1 parity with SQX donor `DataManagerActions` for all 12 actions: `brokerData`, `brokerDataUpdate`, `cloneToTimezone`, `delete`, `exportToCsv`, `exportToMT4`, `exportToMT5`, `load`, `review` (data/chart/quality), `save`, `updateAll`, and `updateSelected`, plus `listDatasets` (`actions.list_datasets`) loading real records directly from `datamgr_datasets`. Fully qualified via offline unit tests, UI integration, and CLI subcommands. |

Canonical target storage is `data/market/dukascopy/` with only `m1/` and
`ticks/` immediately below that source; current files are one M1 year or Tick
month each. The active database has not been migrated to the market file catalog.
The Dukascopy Add dialog lists eligible `datamgr_broker` rows through a
read-only host catalog and fills the selected broker's postfix. Dataset definitions can now be saved atomically with broker/postfix and explicit
Default instrument mapping, independently of file-catalog provisioning. This
neither downloads data nor performs broker-specific conversion. Definition
registration passes isolated persistence and browser tests; live Save readiness
is verified without inserting test records into the active database.
The approved plan is under `.agents/logs/2026-09-28T093858_dukascopy-acquisition/`.
