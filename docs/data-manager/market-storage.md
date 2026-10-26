# Canonical historical storage

Provider frames contain real prices. The shared encoder validates UTC timestamps,
OHLC/quote ordering, finite prices on the instrument tick grid, signed int64 price
range, integer unsigned volume, and uint16 flags. Encoding happens once, using
`tick_size` (not pip size). Integer units and tick size are recorded in both
Parquet schema metadata and the dataset's `lineage_json`.

## Partition layout and publication

Each M1 year and each tick month has exactly one canonical Parquet file:

```text
data/market/dukascopy/m1/eurusd/2026.parquet
data/market/dukascopy/ticks/eurusd/2026/08-aug.parquet
```

The dataset symbol, including any postfix, owns its directory. `underlying` selects
the remote instrument. Tick paths consistently use `ticks`.

PyArrow streams batches into row groups of at most 65,536 rows in a single file,
using ZSTD level 6. DuckDB merges existing and incoming records through Arrow
batches. M1 identity is DateTime; tick identity is DateTime/Bid/Ask/Flags, preserving
different quotes at the same timestamp. Without overwrite, existing M1 observations
win. Overwrite replaces only the requested interval.

A per-dataset operating-system lock serializes writers across processes. File
preparation and compression happen outside SQLite. Each replacement is staged
beside its target, then atomically renamed. A short persistence transaction checks
the catalog snapshot and updates the active paths, counts, bounds and tick units.
Undo copies and a durable journal restore the old files on a failed commit. Backend
startup and the next dataset write resolve journals left by terminated processes.
A concurrent catalog change causes preparation to retry, up to three attempts.

Verified network ranges are stored in `lineage_json.covered_ranges` with the file
manifest commit. Missing-only downloads combine this coverage with actual bar
slots, rather than treating catalog minimum/maximum dates as continuous history.
Missing files invalidate coverage; clearing data removes it. Legacy tick files
without verified coverage must be checked against the provider once.

## Readers and retirement

`lineage_json.partitions` is authoritative. Polars lazy scans and DuckDB queries
retain integer units for research. Broker DataFrames and chart reads decode prices
once. Chart pagination applies before materialization. Canonical files are replaced
as new data arrives; a saved lazy scan is not a version-pinned snapshot.

Earlier part-file layouts remain readable through their catalog manifests and are
consolidated into canonical files when updated. Logical clear/delete retires
catalog visibility; physical cleanup is deferred to dataset lifecycle operations.

## Dukascopy jobs

`POST /api/v1/data/providers/download` accepts `provider: dukascopy`, registered
`targets` (symbol/timeframe), `date_from`, `date_to`, `overwrite`, and
`download_type` (`standard` or `cdn`). It returns an accepted host job ID.

- `GET /api/v1/data/download-jobs/{id}` reads actual persisted job status.
- `POST /api/v1/data/download-jobs/{id}/{pause|resume|stop}` controls the worker.

The worker traverses M1 month intervals and tick hour intervals, with checkpoints
around network and publication work. Each completed interval is independently
durable. Cancellation prevents an uncommitted publication; earlier committed
intervals remain available. Network errors fail jobs; genuine missing-market
intervals can be empty. Logs use the backend-owned Logs service.

The UI submits and polls the same job, forwards overwrite/mode choices, restores
its ID after reload, and never invents progress or completion. Transport failures
remain visible. The unconfigured Hong Kong mode is disabled. The existing CLI
remains synchronous and shares the same encoder, publisher and catalog contract.
