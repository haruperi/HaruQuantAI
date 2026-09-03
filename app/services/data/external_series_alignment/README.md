# External Series Alignment

**Feature ID:** `FEAT-DATA-ALIGN_SERIES`

## Domain

`data`

## Purpose

Align external numeric series without future visibility.

## Provides

`data.align-series@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `max_series_points_per_request` | integer | No | Maximum allowed number of points per alignment request (default: 100,000). |
| `default_timezone` | string | No | Default timezone string when unspecified (default: "UTC"). |
| `default_max_age_seconds` | integer | No | Default maximum lookback age in seconds (default: 86,400). |
| `default_missing_policy` | string | No | Default missing value policy: NULL, CARRY_FORWARD, or FAIL (default: "NULL"). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.align-series@1`. Alignment computations and zero-future-visibility filtering are performed deterministically in memory.

## Operations

- `ALIGN`: Aligns external numeric series against target decision timestamps under point-in-time policies.
- `DEFINE_POLICY`: Validates and declares alignment direction, maximum lookback age, missing-value policy, timezone, and look-ahead prohibition.

## Failure Behavior

- Look-ahead violations or incompatible alignment policies return `DATA_ALIGNMENT_INCOMPATIBLE`.
- Missing required fields or unparseable timestamps return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.align-series@1` provider. Strategies requiring external series alignment become inactive while native price series remain accessible.

## Evidence

Run `uv run python -m app.services.data.external_series_alignment.external_series_alignment` for the executable scenario harness. Automated tests live in `tests/services/data/external_series_alignment/`.
