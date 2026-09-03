# Data Quality and Resolution

**Feature ID:** `FEAT-DATA-RESOLVE_QUALITY`

## Domain

`data`

## Purpose

Detect, resolve, normalize, and serialize conflicting quality operations.

## Provides

`data.resolve-quality@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `auto_migrate` | boolean | No | Whether to automatically apply database schema migrations (default: true). |
| `database_path` | string or null | No | Optional path to SQLite persistence database for lineage and lock state. |
| `max_findings` | integer | No | Maximum number of findings to retain per quality detection run (default: 10,000). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.resolve-quality@1`. Quality findings and resolution records are computed deterministically in-memory or recorded in optional SQLite storage.

## Operations

- `DETECT`: Scan series records for timestamp regressions, anomalous spreads, and data inconsistencies.
- `RESOLVE`: Apply deterministic resolution policies and emit auditable quality decisions.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Findings exceeding configured capacity return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.resolve-quality@1` provider. Automated quality anomaly detection and policy-based conflict resolution become unavailable, while raw underlying series data remain unaffected.

## Evidence

Run `uv run python -m app.services.data.data_quality_resolution.data_quality_resolution` for the executable scenario harness. Automated tests live in `tests/services/data/data_quality_resolution/`.
