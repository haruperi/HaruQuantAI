# MetaTrader 5 source

## Original broker-time acquisition candidate (2026-10-02)

Downloads retain MT5's original timestamp coordinates and show Exchange/Broker.
An absent, unverified or out-of-range broker clock policy does not block download.
Terminal, storage, request and job failures retain correlated host diagnostics.
No live import or SQX parity is qualified by this change.

Owner: `plugin.data_manager.meta_trader`, Data Manager acquisition slot 1.0.0.
Feature: `FEAT-DM-MT5_ACQUISITION`; requirements: `FR-MT5-HISTORY`, `FR-MT5-PUBLISH`.

Candidate implementation. The owner script supplies canonical conversion,
resampling and batch-window rules. Its synthetic failure fallback is excluded by
the owner's explicit real-data-only requirement. Host terminal custody uses a
historical-only subprocess; cancellation kills/reaps that worker. No order API
is exposed. Terminal connection occurs only on an explicit operation.

Catalog, definitions, history jobs and immutable partitions are implemented.
Frontend symbol discovery calls the connected terminal. Terminal executable path
is optional: when omitted, host custody uses the current enabled
`application/config.metatrader5` saved `terminal_path` and `portable` flag.
Missing, disabled, malformed or invalid saved settings fail explicitly. Manual
executable paths override the saved selection; invalid overrides also fail without
fallback. No installation scan or library auto-discovery occurs in this dialog's
connection path. The UI action `Use global settings` clears the manual override;
Fetch symbols initiates the connection. No account credentials are copied,
persisted or used by this connection path. Existing terminal authentication is
required. The legacy standalone script helper's discovery is separate from the
host-backed dialog and remains unchanged.

Bounded original/adapted conversion comparisons passed. A real terminal connected,
returned 1,732 symbols and published one historical daily bar. Isolated removal
and UI rebuild checks passed; complete browser/release qualification remains
pending. Broker timezone transforms, persistent job recovery, full instrument
specification overrides and file import require remaining integration work.

## Clock and instrument metadata candidate

`FR-MT5-HISTORY` and `FR-MT5-PUBLISH` cover original broker-time acquisition.
`add` registers an Exchange/Broker identity with broker_reported timestamp basis.
Downloads preserve naive broker-calendar DateTime and original record identities,
plus immutable hashed raw timestamp sidecars. No tick estimate or clock policy is
read at admission. Existing UTC/legacy identities remain unchanged; their next
MT5 download resolves a separate original-time collection and returns its ID.
Exact complete native records are deduplicated; distinct records at the same
wall-clock timestamp survive, including repeated seasonal times. Partitioning
and date selection use broker-calendar coordinates, without a UTC assertion.
Numeric request bounds use the requested calendar window; this does not verify
broker-specific API semantics or historical coverage. Empty history and native
failures remain explicit failures.

`FR-MT5-HISTORICAL-CLOCK-NORMALIZATION` remains a target for a separately qualified
conversion workflow, not the default acquisition behavior. Its standalone helper
and UTC custody tests retain assessed-policy validation. Policies remain in
`datamgr_broker`; no automatic policy write or historical transition inference
occurs. Review and Original exports retain broker time. UTC conversion requires
separate qualification; no historical repair is performed.

`dataset_metadata` reads captured symbol information offline. Recognized
`trade_calc_mode` supplies Forex/CFD/Futures/Stock/Bonds/Collateral labels;
unambiguous broker folders provide a bounded fallback, otherwise Unknown.
These describe calculation models, not a regulatory asset classification.
Candles show Start of Bar; ticks have no bar convention. Metadata may become
unavailable after provider removal; retained data/provenance reads remain usable.

`detect_timezone` samples one owned symbol after explicit connection. Three paired
UTC/monotonic samples over four seconds must advance and agree within the
six-second deadline, one-second read budget and thirty-second residual limit.
Whole-hour estimates range from UTC-12 to UTC+14 and expire after five minutes.
Connection/failure clears cached evidence. Estimates are per dataset, never
copied across profiles. Closed/stale markets, fractional zones, uncertain clocks
or inconsistent samples return Unknown. An advancing feed delayed by an exact
hour can still mimic an offset; results are always labelled estimated.

Live tick observations supported current UTC+3 for the inspected installation;
they did not verify historical bars, request bounds or transition instants.
The host activated the shared clock schema on 2026-10-02 without writing a policy
or changing retained data. Additional read-only EURUSD observations found advancing
current ticks near UTC+3 and bars within numeric request bounds in sampled
2021/2026 windows. They do not independently establish historical UTC event times
or transition instants. See `.agents/logs/20261002_090258_clock_activation/`.
No existing-data repair or normalized live acquisition qualification is claimed.
Original-time downloads do not require assessed policy coverage. Current global
terminal selection behavior remains unchanged.

## Canonical market data persistence and workspace parity (2026-10-02)

MT5 is unified with the canonical market data storage layout established by Dukascopy:
- M1 bars: `data/market/mt5/m1/{symbol}/{year}.parquet`
- Ticks: `data/market/mt5/ticks/{symbol}/{year}/{month_num}-{month_name}.parquet`

All persistence routes through host `MarketAccess` and `replace_interval()`.
Direct SQLite queries and connections (`sqlite3.connect`, ad-hoc tables) are completely eliminated
from `app/plugin/DataSource/mt5.py`.

The plugin achieves full DataManager workspace operation parity:
- `definitions.add`: Batch registration of canonical definitions (`kind="m1" | "ticks"`).
- `files.list`: Enumeration of committed partition files with checksums and row counts.
- `rows.read`: Bounded reading of Parquet records via host catalog custody.
- `clear`: Eviction of committed Parquet partition files while retaining definitions.
- `delete`: Complete purge of partition files and metadata definitions.
