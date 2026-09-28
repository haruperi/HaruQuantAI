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
| `FEAT-DM-DUKASCOPY_ACQUISITION` | `FR-DATA-001` | `plugin.data_manager.dukascopy` in `data_source.acquisition@1.0.0`; host owns network, jobs and market storage | Isolated fixture direct M1 job and canonical file publication pass tests. Live direct and both CDN modes are unavailable. Active catalog migration, crash recovery, independent provider comparison and SQX parity remain unqualified. |

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
