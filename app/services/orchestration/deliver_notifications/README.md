# Deliver Notifications (`FEAT-ORCH-DELIVER_NOTIFICATIONS`)

## Purpose

Coordinate policy-gated notification delivery and durable receipts: master and
channel enablement gates, bounded rate policy, pre-transport redaction, and
uncertain-outcome disclosure. Transport providers implement `notification.delivery@1`;
they do not own orchestration policy or receipt persistence.

## Domain

`orchestration`

## Provides

- `orchestration.deliver-notifications@1`

## Required Capabilities

- `orchestration.manage-jobs@1`
- `workspace.manage-accounts@1`

## Optional Capabilities

- `notification.delivery@1`

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string | `:memory:` | SQLite database path holding notification idempotency and receipt records. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Manages durable notification receipts and idempotency keys in SQLite.
- Dispatches delivery requests across configured notification transports.
- Starts no detached background listeners outside the managed feature scope.

## Persistent State

Namespace `orchestration.deliver_notifications` retaining idempotency identities,
delivery attempts, and delivery receipts in SQLite.

## Failure Behavior

- Delivery failures return structured failure models.
- Rate limits, channel disablement, or validation errors reject requests deterministically.
- Transport timeout or uncertain delivery records an explicit unconfirmed receipt status.

## Removal Behavior

Unmounting the feature withdraws `orchestration.deliver-notifications@1`. In-flight
notifications complete or abort; stored receipts and idempotency rows are retained.

## Evidence

Run the bounded executable demonstration with:

```console
uv run python -m app.services.orchestration.deliver_notifications._usage
```
