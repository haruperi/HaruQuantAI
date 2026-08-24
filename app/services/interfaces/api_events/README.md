# HTTP and Event Contracts

> **Feature ID:** `FEAT-IFACE-SERVE_API_EVENTS`
> **Status:** `Implemented`

## Domain

`interfaces`

## Provides

- `interfaces.serve-api-events@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Setting | Type | Default | Description |
|---|---|---|---|
| `title` | string | `HaruQuantAI API` | OpenAPI documentation title |
| `api_version` | string | `v1` | Default served API version label |
| `event_buffer_size` | integer | `1000` | Maximum retained SSE events in buffer |
| `max_artifact_download_bytes` | integer | `104857600` | Maximum single artifact download size in bytes |

## Purpose

Expose versioned, idempotent, paged, bounded HTTP/SSE resources.

## Runtime Effects

- Generates and serves OpenAPI 3.1 contract specifications for `/api/v1` routes across workspace, catalogue, data, strategies, simulations, jobs, databanks, results, artifacts, plugins, and code generation.
- Validates optimistic concurrency tokens against object versions to prevent lost updates on mutating routes.
- Enforces scoped idempotency deduplication for retryable create and action mutations.
- Manages an in-memory ring buffer for streaming and replaying retained SSE interface events with cursor tracking and resync markers.
- Tracks lifecycle states and progress for long-running asynchronous jobs with immediate handle return.
- Validates committed artifact file downloads, byte range requests, and strict filesystem root containment.
- Enforces semantic version compatibility and manages machine-readable deprecation notices.

## Failure Behavior

- If concurrency token validation fails on a mutating request, `VersionConflictError` (`VERSION_CONFLICT`) is raised and no mutation occurs.
- If a concurrent mutation with the same idempotency key is already executing, `IdempotencyConflictError` (`IDEMPOTENCY_CONFLICT`) is raised.
- If an SSE cursor requested is older than the retention buffer window, a resync batch is returned with `is_resync_required=True`.
- If an asynchronous job ID is not found, `JobNotFoundError` (`JOB_NOT_FOUND`) is raised.
- If an artifact download is uncommitted, missing, or attempts path traversal outside the storage root, `ArtifactAccessDeniedError` (`ARTIFACT_ACCESS_DENIED`) is raised.
- If an incompatible API version is requested, `ApiIncompatibleError` (`UPGRADE_REQUIRED`) is raised.

## Removal Behavior

Removing `api_events` makes all HTTP, OpenAPI, and SSE interface access unavailable (`CAPABILITY_UNAVAILABLE`). Underlying application domain services remain intact and operable via direct capability ports or alternative adapters.

## Persistent State

None

## Functional Requirements

- `FR-IFACE-SERVE_VERSIONED_API`: Expose `/api/v1` OpenAPI contracts for workspace, catalogue, data, strategies, simulations, jobs, databanks, results, artifacts, plugins, and code generation.
- `FR-IFACE-ENFORCE_CONCURRENCY_TOKENS`: Mutating routes shall require expected object version where conflicts are possible.
- `FR-IFACE-DEDUPLICATE_MUTATIONS`: Retryable create/action routes shall accept an idempotency key scoped to local session and command type.
- `FR-IFACE-REPLAY_INTERFACE_EVENTS`: The SSE endpoint shall replay retained events after `Last-Event-ID` and emit a resync marker when retention no longer covers the cursor.
- `FR-IFACE-TRACK_ASYNC_JOBS`: Every long-running action shall return a job ID immediately and shall not hold the HTTP request open for computation.
- `FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS`: Artifact downloads shall validate artifact state, requested filename, range, and path containment.
- `FR-IFACE-EVOLVE_API_COMPATIBLY`: API schema evolution shall preserve published compatibility within a major version and publish machine-readable deprecations.
