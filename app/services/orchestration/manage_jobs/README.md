# Manage Jobs (`FEAT-ORCH-MANAGE_JOBS`)

## Purpose

Persist jobs and publish isolated progress observations: idempotent job acceptance,
optimistic lifecycle transitions, monotonic progress, and isolated asynchronous
progress callbacks. SQLite operations are confined to `_persistence.py`.

## Domain

`orchestration`

## Provides

- `orchestration.manage-jobs@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string | `:memory:` | SQLite database path holding job and progress records. |
| `callback_queue_capacity` | int | `128` | Maximum capacity of the isolated progress callback queue. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Persists jobs and lifecycle state in SQLite.
- Manages an isolated queue and executor for progress callbacks.
- Closes SQLite connection and background queue handles upon scope teardown.

## Persistent State

Namespace `orchestration.manage_jobs` retaining jobs, versions, progress,
and idempotency identities in SQLite.

## Failure Behavior

- Invalid job states or non-monotonic progress updates fail with validation errors.
- Disconnected observers do not corrupt or block the job persistence state.

## Removal Behavior

Unmounting the feature withdraws `orchestration.manage-jobs@1`. In-flight observer
callbacks are drained and job records are retained.

## Evidence

Run the bounded executable demonstration with:

```console
uv run python -m app.services.orchestration.manage_jobs._usage
```
