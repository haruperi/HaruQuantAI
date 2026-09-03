# Profile Source Preparation

**Feature ID:** `FEAT-DATA-PREPARE_PROFILES`

## Domain

`data`

## Purpose

Prepare and validate session and price-bin source declarations for profiles.

## Provides

`data.prepare-profiles@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `default_bin_count` | integer or null | No | Default target number of price bins (default: null). |
| `default_price_step` | decimal | No | Default price step increment if unspecified (default: 0.01). |
| `max_bin_count` | integer | No | Maximum allowable number of price bins (default: 10,000). |
| `min_price_step` | decimal | No | Minimum allowable price step (default: 0.00000001). |
| `require_session_alignment` | boolean | No | Whether session boundary alignment is required (default: true). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.prepare-profiles@1`. Session boundaries and price-bin distributions are evaluated in-memory.

## Operations

- `VALIDATE_SOURCE`: Validates declared profile source series against session alignments and bin configurations.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Non-positive price steps return `DATA_VALIDATION_FAILED`.
- Excessive bin counts return `DATA_VALIDATION_FAILED`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.prepare-profiles@1` provider. Volume profile and TPO source validation become unavailable, while raw underlying series data remain unaffected.

## Evidence

Run `uv run python -m app.services.data.profile_source_preparation.profile_source_preparation` for the executable scenario harness. Automated tests live in `tests/services/data/profile_source_preparation/`.
