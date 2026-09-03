# Data Inspection, Export, and Retention

**Feature ID:** `FEAT-DATA-MANAGE_RETENTION`

## Domain

`data`

## Purpose

Preview, export, and garbage-collect data versions safely without memory exhaustion or data loss.

## Provides

`data.manage-retention@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `default_preview_limit` | integer | No | Default maximum rows returned in a preview (default: 100). |
| `max_preview_limit` | integer | No | Upper bound limit on preview rows to keep memory within budget (default: 10,000). |
| `default_quarantine_days` | integer | No | Default quarantine period in days before unreachable artifacts can be collected (default: 30). |
| `supported_export_formats` | tuple of string | No | Supported export formats (default: ("CSV", "PARQUET")). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.manage-retention@1`. Preview and export calculations are performed in memory; garbage collection operates on manifest reachability graphs.

## Operations

- `DEFINE_POLICY`: Defines retention and quarantine policy parameters for the domain.
- `COLLECT`: Performs reachability analysis against committed manifests and garbage collects unreferenced artifacts past the quarantine threshold.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.manage-retention@1` provider. Inspection, export, and collection become unavailable, while committed data artifacts remain preserved in storage.

## Evidence

Run `uv run python -m app.services.data.data_inspection_retention.data_inspection_retention` for the executable scenario harness. Automated tests live in `tests/services/data/data_inspection_retention/`.
