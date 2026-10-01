# MetaTrader 5 source

Owner: `plugin.data_manager.meta_trader`, Data Manager acquisition slot 1.0.0.
Feature: `FEAT-DM-MT5_ACQUISITION`; requirements: `FR-MT5-HISTORY`, `FR-MT5-PUBLISH`.

Candidate implementation. The owner script supplies canonical conversion,
resampling and batch-window rules. Its synthetic failure fallback is excluded by
the owner's explicit real-data-only requirement. Host terminal custody uses a
historical-only subprocess; cancellation kills/reaps that worker. No order API
is exposed. Terminal connection occurs only on an explicit operation.

Catalog, definitions, history jobs and immutable partitions are implemented.
Frontend symbol discovery calls the connected terminal. Terminal executable path
is optional, with library auto-discovery when omitted. No account credentials
are copied or persisted. Existing terminal authentication is required.

Bounded original/adapted conversion comparisons passed. A real terminal connected,
returned 1,732 symbols and published one historical daily bar. Isolated removal
and UI rebuild checks passed; complete browser/release qualification remains
pending. Broker timezone transforms, persistent job recovery, full instrument
specification overrides and file import require remaining integration work.
