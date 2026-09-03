# Historical Data Ingestion

**Feature ID:** `FEAT-DATA-INGEST_HISTORY`

## Domain

`data`

## Purpose

Provide the `data.ingest-history@1` capability for registering data sources, importing files, staging, atomically publishing data series versions, pinning data provenance, and accounting for row ingestion.

## Provides

`data.ingest-history@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `auto_migrate` | boolean | No | Whether to automatically apply database schema migrations (default: true). |
| `database_path` | string or null | No | Optional SQLite database path for persistent storage; defaults to in-memory SQLite. |

## Persistent State

`data.historical_ingestion` schema version 1 retains `data_connections`, `data_import_receipts`, `data_series_versions`, and `staged_artifacts` in SQLite. Retention policy is `retain`: feature unloading preserves immutable published series versions and receipts.

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `data.ingest-history@1`. SQLite connections are opened per operation and closed in all execution paths.

## Operations

- `REGISTER_CONNECTION`: Register data connection references with declared capabilities (CSV, Parquet, Connectors).
- `IMPORT`: Execute a deterministic `DataImportPlan` on staged CSV/file content, enforce malformed-row policies (`ABORT_IMPORT` or `REJECT_ROW`), compute quality findings and SHA-256 hashes, validate counter reconciliation, and atomically publish a new `DataSeriesVersion` and `DataImportReceipt`.
- `EXPORT`: Retrieve published series version and serialize to CSV or Parquet format.

## Failure Behavior

- Unstaged or missing source artifacts return `DATA_NOT_FOUND`.
- Malformed rows under `ABORT_IMPORT` or invalid mappings return `DATA_VALIDATION_FAILED`.
- Unsupported connection or export formats return `DATA_CONNECTION_UNSUPPORTED`.

## Removal Behavior

Removing this feature withdraws its scoped `data.ingest-history@1` provider. Committed series remain opaque artifacts; subsequent import requests return `CAPABILITY_UNAVAILABLE`.

## Evidence

Run `uv run python -m app.services.data.historical_data_ingestion.historical_data_ingestion` for the executable scenario harness. Automated tests live in `tests/services/data/historical_data_ingestion/`.
