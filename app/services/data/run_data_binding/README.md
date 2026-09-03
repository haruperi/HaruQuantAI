# Run Data Binding

**Feature ID:** `FEAT-DATA-BIND_RUN_DATA`

## Domain

`data`

## Purpose

Bind committed market data versions to execution runs and validate prerequisites.

## Provides

`data.bind-run-data@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `allow_synthetic_sources` | boolean | No | Whether synthetic/scenario data versions can be bound (default: true). |
| `require_committed_status` | boolean | No | Whether only committed versions may be bound (default: true). |
| `strict_precision_check` | boolean | No | Whether precision requirements are strictly enforced (default: true). |
| `supported_precisions` | tuple of string | No | Tuple of supported simulation precision identifiers. |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.bind-run-data@1`. Run bindings and precision prerequisites are validated in-memory.

## Operations

- `BIND`: Bind immutable committed market data versions to execution run manifests.
- `VALIDATE_PRECISION`: Verify required data source resolutions and tick/spread prerequisites without silent fallback.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Uncommitted data version binding returns `DATA_VALIDATION_FAILED`.
- Missing precision prerequisites return `DATA_PRECISION_UNAVAILABLE`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.bind-run-data@1` provider. Execution run manifest data binding and precision validation become unavailable, while raw underlying series data remain unaffected.

## Evidence

Run `uv run python -m app.services.data.run_data_binding.run_data_binding` for the executable scenario harness. Automated tests live in `tests/services/data/run_data_binding/`.
