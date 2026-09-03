# QuantDataManager Source

**Feature ID:** `FEAT-DATA-IMPORT_QUANTDATA`

## Domain

`data`

## Purpose

Discover and decode governed StrategyQuant QuantDataManager M1/tick files, synchronize reference metadata with Catalogue, and track immutable lineage.

## Provides

`data.import-quantdata@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `allowed_root` | string or null | No | Allowed base root directory for QuantDataManager file access. |
| `auto_migrate` | boolean | No | Whether to automatically apply database schema migrations (default: true). |
| `database_path` | string or null | No | Optional SQLite database path for persistent storage; defaults to in-memory SQLite. |

## Persistent State

`data.quantdata_manager_source` schema version 1 retains `quantdata_lineage` and `quantdata_specs` in SQLite. Retention policy is `retain`: feature unloading preserves immutable lineage records.

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `data.import-quantdata@1`. Path containment is strictly enforced against `allowed_root`. SQLite connections are opened per operation and closed in all execution paths.

## Operations

- `DISCOVER`: Discovers QuantDataManager instruments and series files from the allowed root.
- `DECODE`: Version-pinned (v4.2) binary decoding of `.dat` M1 and tick history files without heuristics.
- `SYNC`: Reference synchronization with Catalogue and publishing immutable `DataSeriesVersion` records.

## Failure Behavior

- Non-existent or escaping root directories return `DATA_QUANTDATA_INVALID`.
- Malformed, truncated, or unsupported binary records return `DATA_QUANTDATA_INVALID` with bounded diagnostic offsets.
- Unsupported operations return `DATA_VALIDATION_FAILED`.

## Removal Behavior

Removing this feature withdraws its scoped `data.import-quantdata@1` provider. Existing lineage records and published series versions remain immutable in storage.

## Evidence

Run `uv run python -m app.services.data.quantdata_manager_source.quantdata_manager_source` for the executable scenario harness. Automated tests live in `tests/services/data/quantdata_manager_source/`.
