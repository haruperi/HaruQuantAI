# Tick Normalization

**Feature ID:** `FEAT-DATA-NORMALIZE_TICKS`

## Domain

`data`

## Purpose

Preserve and normalize complete tick semantics across market data sources without losing sub-millisecond sequencing, duplicate timestamps, or broker quote flags.

## Provides

`data.normalize-ticks@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `max_batch_size` | integer | No | Maximum allowed number of ticks in a single batch. |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.normalize-ticks@1`. Ticks are validated and deterministically sorted in memory by timestamp and sequence without reordering equal timestamps.

## Operations

- `NORMALIZE`: Preserves raw bid, ask, last, volume, flags, and source sequence, and checks for inverted spreads and non-positive prices.

## Failure Behavior

- Exceeding `max_batch_size` returns `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.normalize-ticks@1` provider. Tick precision modes become unavailable, while bar modes remain operational if installed.

## Evidence

Run `uv run python -m app.services.data.tick_normalization.tick_normalization` for the executable scenario harness. Automated tests live in `tests/services/data/tick_normalization/`.
