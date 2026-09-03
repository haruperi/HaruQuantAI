# Bar Aggregation and Timeframes

**Feature ID:** `FEAT-DATA-AGGREGATE_BARS`

## Domain

`data`

## Purpose

Aggregate lower-resolution series into higher-timeframe OHLCV bars and define timeframe semantics without crossing effective session boundaries.

## Provides

`data.aggregate-bars@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `max_bars_per_request` | integer | No | Maximum allowed number of source bars per request (default: 100,000). |
| `default_timezone` | string | No | Default timezone string for bucket alignment when unspecified (default: "UTC"). |
| `allow_custom_timeframes` | boolean | No | Whether custom positive intervals (e.g. M10, H2) are enabled (default: true). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.aggregate-bars@1`. Aggregation and lineage computations are performed deterministically in memory.

## Operations

- `AGGREGATE`: Aggregates series into target timeframes and records deterministic lineage hashes.
- `VALIDATE_TIMEFRAME`: Validates positive standard presets and custom timeframe specifications.

## Failure Behavior

- Invalid or non-positive timeframe intervals return `DATA_VALIDATION_FAILED`.
- Missing required fields return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.aggregate-bars@1` provider. Derived timeframe construction becomes unavailable, while existing committed data versions remain accessible.

## Evidence

Run `uv run python -m app.services.data.bar_aggregation.bar_aggregation` for the executable scenario harness. Automated tests live in `tests/services/data/bar_aggregation/`.
