# Execute Persistence

> **Feature ID:** `FEAT-WS-EXECUTE_PERSISTENCE`
> **Status:** `Implemented and verified`
> **Capability:** `workspace.persistence@1`

Provides bounded transaction execution, ordered additive migrations, and append-only
evidence custody for stateful features across the HaruQuantAI platform.

## Public API

The canonical public contract is `app/contracts/workspace/persistence.py`.
It defines:
- `PersistenceCapability`: protocol providing `execute_transaction`, `apply_migrations`, `append_evidence`, `export_evidence`, and `register_namespace`.
- `PersistenceTransactionRequest` / `PersistenceTransactionResult`: atomic namespace-bound transaction execution with idempotency and expected revision.
- `FeatureMigrationManifest` / `FeatureMigration` / `MigrationResult`: ordered additive migrations with strict checksum verification and rollback.
- `EvidenceRecord` / `ExportEvidenceRequest` / `ExportEvidenceResult`: immutable evidence custody and stable-ordered paged export.

The package registers through the `haruquantai.features` entry-point group as
`workspace-execute-persistence`. It requires `workspace.manage-workspaces@1`.
Mount registers the capability and registers one scope-owned close callback.

## Configuration

| Key | Type | Default | Bounds |
| --- | --- | --- | --- |
| `busy_timeout_seconds` | `float` | `5.0` | 0.1–60.0 |
| `max_export_limit` | `int` | `1000` | 1–10000 |
| `max_statements_per_tx` | `int` | `100` | 1–1000 |

Unknown keys, wrong types, and out-of-range values fail closed. Manifest and configuration key parity is tested.

## Persistence and Safety

`ExecutePersistenceService` executes against `haruquantai.db` in SQLite WAL mode.
All tables are partitioned strictly by feature namespace.
Transactions targeting tables outside the registered namespace are denied.
Append-only evidence tables reject `UPDATE` and `DELETE` attempts.
Expected-revision checks guarantee optimistic concurrency control.

## Traceability

- `FR-TRC-WS-EXECUTE_PERSISTENCE-001` -> `AT-WS-EXECUTE_PERSISTENCE-001` in `tests/services/workspace/execute_persistence/test_traceability.py`
- `FR-TRC-WS-EXECUTE_PERSISTENCE-002` -> `AT-WS-EXECUTE_PERSISTENCE-002` in `tests/services/workspace/execute_persistence/test_traceability.py`
- `FR-TRC-WS-EXECUTE_PERSISTENCE-003` -> `AT-WS-EXECUTE_PERSISTENCE-003` in `tests/services/workspace/execute_persistence/test_traceability.py`
- `NFR-TRC-WS-EXECUTE_PERSISTENCE-001` -> `ATN-WS-EXECUTE_PERSISTENCE-001` in `tests/services/workspace/execute_persistence/test_lifecycle.py`

## Domain

`workspace`

## Provides

`workspace.persistence@1`

## Required Capabilities

`workspace.manage-workspaces@1`

## Optional Capabilities

None.

## Purpose

Execute namespace-fenced transactions, additive migrations, and append-only
evidence operations through the public Workspace persistence contract.

## Runtime Effects

Mount registers `workspace.persistence@1` and one scope-owned close callback. The
provider opens bounded SQLite resources only for admitted operations and closes them
at the operation or scope boundary.

## Failure Behavior

Unknown namespaces, unauthorized tables, stale revisions, invalid statements,
checksum drift, non-additive migrations, and append-only mutations fail closed with
typed contract errors and no partial commit.

## Removal Behavior

Removal withdraws only `workspace.persistence@1`, closes provider-owned resources,
and retains all committed feature tables, migration records, revisions, idempotency
receipts, and evidence.

## Persistent State

Namespace `workspace_persistence`, schema version 1, retention policy `RETAIN`:
registered feature namespaces, ordered migrations, revisions, idempotency receipts,
and append-only evidence custody.
