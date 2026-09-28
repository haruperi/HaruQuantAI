# Dukascopy data source

Package ID: `plugin.data_manager.dukascopy`; owner: `workspace.data_manager`;
attachment: `data_source.acquisition@1.0.0`.
Its existing UI view attaches to the same owner through
`data_source.presentation@1.0.0`; neither slot grants peer access.

The backend contains a bounded independent BI5 decoder for FX tick and bid-side
M1 records. Tick volume is the checked sum of ask and bid volumes after
converting provider millions to base-currency units. SQX's own decoder uses
bid volume only, so this target policy is intentionally different.

Current state: **offline direct-acquisition candidate**. An isolated catalog,
host job and fixture transport can register a definition, download one UTC
day and publish a yearly M1 or monthly Tick Parquet file. The active market
catalog has not received an approved migration, so the UI reports acquisition
unavailable. A limited live provider probe returned 429. A partial tick day
with an HTTP 404 hour fails rather than claiming coverage. Job state is held
in host memory and is not resumable after a restart. Publication does not yet
have a crash-recovery journal, so it is not qualified for live writes.

The Add dialog reads enabled market-data broker profiles directly from the
existing unified SQLite `datamgr_broker` table through read-only host custody.
Selection fills the database postfix; users may edit it. Broker listing works
without the unapproved market-file migration. The database currently has no
broker-specific instrument rows. The batch `definitions.add` operation saves
selected symbols with broker/postfix and explicit Default instrument mapping in
one host-owned transaction. Dataset saving requires only the existing definition
table; price acquisition remains separately gated. Provider identity is retained
in `underlying`, with UTC storage and no broker conversion. Duplicate or invalid
rows reject the entire batch. Unverified asset categories remain empty.

The standard StrategyQuant CDN and Hong Kong modes are disabled. SQX contains
base URLs for two CDN endpoints, but package transport, mapping of endpoint to
region, third-party reuse terms and independent package verification are not
established. The UI must not report a completed download or local coverage
from this candidate.

No claim of SQX parity is made. Higher timeframes are read-time views of M1;
this package stores neither higher timeframe files nor SQX `.dat` files.
