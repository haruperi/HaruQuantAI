# Partitioned Parquet Market Data Store

**Feature ID:** `FEAT-DATA-MARKET_DATA_STORE`

## Domain

`data`

## Purpose

Provide the `data.market-data-store@1` capability for canonical historical market data storage using partitioned Apache Parquet datasets with Zstandard (ZSTD level 6) compression, fixed-point integer pricing, PyArrow batched immutable append writers, Polars lazy scans, DuckDB SQL analytics, and DuckDB manifest state tracking.

## Provides

`data.market-data-store@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `storage_root` | string | No | Canonical root directory for market data partitions (default: `data/market_data`). |
| `compression` | string | No | Parquet compression codec (default: `zstd`). |
| `compression_level` | integer | No | Zstandard compression level (default: `6`). |
| `min_rows_per_group` | integer | No | Minimum rows per Parquet row group (default: `100_000`). |
| `max_rows_per_group` | integer | No | Maximum rows per Parquet row group (default: `500_000`). |
| `max_rows_per_file` | integer | No | Target maximum rows per Parquet part file (default: `2_000_000`). |
| `manifest_database_path` | string or null | No | Path to DuckDB catalog database; null for in-memory (default: `data/market_data/catalog.duckdb`). |
| `staging_dir_name` | string | No | Transient staging directory name (default: `.staging`). |

## Persistent State

`data.market_data_store` schema version 1 retains immutable `.parquet` part files under `storage_root` (`ticks/` and `bars/`) and manifest metadata in DuckDB. Retention policy is `retain`: unmounting the feature preserves all historical data and catalog records.

## Directory Layout

- **Ticks:**
  `{storage_root}/ticks/source={source}/symbol={symbol}/year={year}/month={month}/part-{uuid4().hex}-{i}.parquet`
- **M1 Bars:**
  `{storage_root}/bars/source={source}/timeframe={timeframe}/symbol={symbol}/year={year}/part-{uuid4().hex}-{i}.parquet`

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `data.market-data-store@1`. DuckDB connections are opened for the manifest catalog and closed upon unmount.

## Operations

- `APPEND_TICKS`: Validate, stage, and atomically append an immutable batch of ticks using PyArrow with ZSTD level 6 compression and register part in DuckDB catalog.
- `APPEND_BARS`: Validate, stage, and atomically append an immutable batch of bars using PyArrow with ZSTD level 6 compression and register part in DuckDB catalog.
- `SCAN_TICKS`: Return a Polars LazyFrame with predicate pushdown (source, symbol, datetime range) and optional price restoration.
- `SCAN_BARS`: Return a Polars LazyFrame with predicate pushdown (source, timeframe, symbol, datetime range).
- `QUERY_SQL`: Execute analytical SQL directly over Parquet partitions using DuckDB.
- `GET_LATEST_TIMESTAMP`: Query the high-watermark timestamp from the DuckDB catalog without scanning files.
- `RESAMPLE_BARS` (`MarketDataReferenceRepository`): Dynamic multi-timeframe resampling (M1..MN) using Polars `group_by_dynamic` over partitioned historical Parquet files.
- `INSPECT_QUALITY` (`MarketDataReferenceRepository`): Automated anomaly detection engine evaluating price gaps (>4x bar duration in active sessions), price spikes (>5x rolling ATR), and invalid bar geometry (High < Low, Close > High, Open < Low).
- `CLONE_TIMEZONE` (`MarketDataReferenceRepository`): Non-destructive timestamp shift engine writing new timezone-offset Parquet partitions.
- `EXPORT_CSV` (`MarketDataReferenceRepository`): High-throughput formatted CSV export with configurable date/time layouts, delimiters, and column mappings.
- `EXPORT_MT4` (`MT4Exporter`): Generation of binary MetaTrader 4 `.hst` (History Header v400) and `.fxt` (Testing Header v405) files from resampled historical Parquet datasets.

## Failure Behavior

- Empty or invalid tables raise appropriate validation errors.
- Corrupted or non-conforming inputs fail in staging prior to promotion.

## Removal Behavior

Removing this feature withdraws its scoped `data.market-data-store@1` provider. Existing immutable Parquet files and DuckDB catalog records remain intact on disk.

## Evidence

Automated tests live in `tests/services/data/market_data_store/`.
