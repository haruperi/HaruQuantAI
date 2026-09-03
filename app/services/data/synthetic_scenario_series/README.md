# Synthetic and Scenario Series

**Feature ID:** `FEAT-DATA-GENERATE_SCENARIOS`

## Domain

`data`

## Purpose

Create seeded synthetic bars, ticks, and bounded scenario series with complete provenance.

## Provides

`data.generate-scenarios@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `max_records` | integer | No | Maximum allowable generated records per request (default: 250,000). |
| `default_model` | string | No | Default synthetic generator model algorithm (default: "gbm"). |
| `default_rounding` | string | No | Rounding mode applied to generated prices and volumes (default: "ROUND_HALF_EVEN"). |
| `supported_transform_types` | set | No | Set of supported scenario transformation kinds (default: SHOCK, GAP, VOLATILITY, LIQUIDITY, OUTAGE, MISSINGNESS). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.generate-scenarios@1`. Generation and scenario transformation computations are performed deterministically in memory.

## Operations

- `CONFIGURE_MODEL`: Validates model parameters, timeframe, time window, and content hashes.
- `GENERATE`: Generates reproducible, seeded synthetic OHLCV bars or ticks enforcing price/volume/time invariants.
- `TRANSFORM`: Applies declared shocks, gaps, volatility shifts, and missingness to immutable source data.

## Failure Behavior

- Invalid or inverted time windows return `DATA_VALIDATION_FAILED`.
- Non-finite or negative model parameters return `DATA_VALIDATION_FAILED`.
- Generation requests exceeding `max_records` return `DATA_VALIDATION_FAILED`.
- Invalid content hashes or malformed UUIDs return `DATA_VALIDATION_FAILED`.

## Removal Behavior

Removing this feature withdraws its scoped `data.generate-scenarios@1` provider. Synthetic and scenario generation becomes unavailable while real historical and streaming market data remains unaffected.

## Evidence

Run `uv run python -m app.services.data.synthetic_scenario_series.synthetic_scenario_series` for the executable scenario harness. Automated unit tests live in `tests/services/data/synthetic_scenario_series/`.
