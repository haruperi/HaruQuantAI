# Reserve Resources (`FEAT-ORCH-RESERVE_RESOURCES`)

## Purpose

Admit finite work under one authoritative resource ledger. Enforce hierarchical resource budgets, workstation defaults (70% memory envelope, 85%/95% pressure transitions, reserved control CPUs, 256 ready descriptors, two prefetch chunks, 64 MiB buffers, 20% cache ceiling, one compile job), temporary disk headroom (`min(16 GiB, 25% free)` with >=10% free space preserved), fair queues, and dedicated safety/control priority without double-counting parent capacity.

## Domain

`orchestration`

## Provides

- `orchestration.resource-admission@1`

## Required Capabilities

- `workspace.persistence@1`

## Optional Capabilities

- `workspace.administer-settings@1`

## Configuration

Strict configuration without ad-hoc keys. Unknown configuration keys fail closed with `ValueError`.

## Runtime Effects

- Manages active leases, hierarchical parent/child allocations, and priority queues.
- Synchronizes durable lease records and idempotency keys through local persistence.
- Registers lifecycle cleanup callbacks to release resources and close database connections on scope disposal.

## Persistent State

Namespace `orchestration.reserve_resources` retaining admitted leases, allocation profiles, and audit receipts in SQLite.

## Failure Behavior

- Oversized or conflicting requests are refused deterministically with typed `ResourceAdmissionDecision`.
- Temporary capacity saturation queues requests according to workload priority (SAFETY > CONTROL > BULK).
- Expired or cancelled requests are dequeued without granting leases.

## Removal Behavior

Disabling or unmounting the feature withdraws `orchestration.resource-admission@1`. In-flight leases are quiesced and underlying database handles closed; durable audit records are retained.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.orchestration.reserve_resources._usage
```

Acceptance evidence manifest:
`docs/dev/evidence/features/FEAT-ORCH-RESERVE_RESOURCES/acceptance.json`
