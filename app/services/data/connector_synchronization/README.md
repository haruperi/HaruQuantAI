# Connector Synchronization

**Feature ID:** `FEAT-DATA-SYNC_CONNECTORS`

## Domain

`data`

## Purpose

Coordinate idempotent connector synchronization and manage provider sessions.

## Provides

`data.sync-connectors@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `default_deduplication_policy` | string | No | Default policy for deduplication (default: "KEEP_FIRST"). |
| `default_overlap_window_seconds` | integer | No | Default overlap seconds (default: 300). |
| `default_revision_policy` | string | No | Default revision detection strategy (default: "COMPARE_OVERLAP"). |
| `max_rate_limit_per_window` | integer | No | Default max requests per window (default: 100). |
| `max_records_per_page` | integer | No | Maximum records allowed per sync request (default: 50,000). |
| `rate_limit_window_seconds` | integer | No | Default rate limit window in seconds (default: 60). |
| `strict_secret_isolation` | boolean | No | Whether secret isolation is enforced (default: true). |

## Persistent State

None.

## Runtime Effects

Mount resolves no external runtime dependencies through `FeatureContext` and stages `data.sync-connectors@1`. Connector plans, fetches, and commits are executed with secret-isolated credential references.

## Operations

- `PLAN`: Calculate explicit requested ranges, overlap windows, and deduplication keys.
- `FETCH`: Fetch records through throttled, resumable cursors.
- `COMMIT`: Commit synchronized data batches without partial publications.

## Failure Behavior

- Missing required fields return `DATA_VALIDATION_FAILED`.
- Rate limit violations return `DATA_RATE_LIMIT_EXCEEDED`.
- Secret exposure violations return `DATA_SECURITY_VIOLATION`.
- Unsupported operations return `DATA_VALIDATION_FAILED`.
- Requests requiring uninstalled capabilities return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws its scoped `data.sync-connectors@1` provider. Automatic provider synchronization becomes unavailable, while file-based data ingestion remains functional.

## Evidence

Run `uv run python -m app.services.data.connector_synchronization.connector_synchronization` for the executable scenario harness. Automated tests live in `tests/services/data/connector_synchronization/`.
