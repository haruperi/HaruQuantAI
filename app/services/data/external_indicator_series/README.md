# External Indicator Series

**Feature ID:** `FEAT-DATA-IMPORT_INDICATORS`

## Domain

`data`

## Purpose

Import immutable external indicator values and align with series.

## Provides

`data.import-indicators@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `allow_future_timestamps` | boolean | No | Whether timestamps past decision point are permitted (default: false). |
| `default_missing_policy` | string | No | Default missing-value alignment policy strategy (default: "FORWARD_FILL"). |
| `default_timezone` | string | No | Default IANA timezone name for imported series timestamps (default: "UTC"). |
| `max_points_per_series` | integer | No | Maximum allowable points per imported indicator series (default: 1,000,000). |
| `require_deterministic_reimport` | boolean | No | Whether reimport must yield deterministic version hashes (default: true). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.import-indicators@1`. External indicator series versions are parsed, validated, and aligned in-memory.

## Operations

- `IMPORT`: Import external indicator values with strict validation of source artifacts, definition hashes, and lookahead prohibition.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Lookahead bias violations return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.import-indicators@1` provider. External indicator ingestion and alignment become unavailable, while core market data series remain functional.

## Evidence

Run `uv run python -m app.services.data.external_indicator_series.external_indicator_series` for the executable scenario harness. Automated tests live in `tests/services/data/external_indicator_series/`.
