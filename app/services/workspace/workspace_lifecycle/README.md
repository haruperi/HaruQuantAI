# Workspace Lifecycle

> **Feature ID:** `FEAT-WS-MANAGE_WORKSPACES`
> **Status:** `Implemented`

## Domain

`workspace`

## Provides

- `workspace.manage-workspaces@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

None

## Purpose

Initialize, migrate, lock, recover, and back up a workspace.

## Runtime Effects

- Manages local workspace filesystem hierarchy (`metadata/`, `artifacts/`, `staging/`, `logs/`, `cache/`, `exports/`, `backups/`).
- Creates and migrates SQLite database schemas in WAL mode with transactional migration tracking.
- Implements writer fencing using atomic process locks to protect workspaces against concurrent write mutations.
- Recovers uncommitted staging artifacts and nonterminal jobs during system startup.
- Produces consistent verified backups and performs verified restore into empty workspaces.

## Failure Behavior

- If initialization fails or is interrupted, any partial files are cleaned up or left in a resumable state without corrupting existing workspaces.
- If schema migration fails, transactions are rolled back and the previous usable schema is preserved.
- If writer lock acquisition detects another active writer, `WorkspaceAlreadyOpenError` (`WORKSPACE_ALREADY_OPEN`) is raised.
- If backup or restore checksum verification fails, `WorkspaceCorruptionError` is raised and target workspace is not corrupted.

## Removal Behavior

Removing `workspace_lifecycle` makes workspace initialization, migration, fencing, recovery, and backup operations unavailable (`CAPABILITY_UNAVAILABLE`). Existing persisted workspaces remain unchanged on disk.

## Persistent State

- **Namespace:** `workspace`
- **Schema version:** 1
- **Retention policy:** `retain`
- **Description:** SQLite metadata tables (`workspace`, `schema_migrations`, `writer_leases`, `artifacts`) and filesystem directory tree.
