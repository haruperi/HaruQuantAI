# FEAT-SYS-PERSIST_STORAGE — Persistent Storage Engine

## Purpose

Provide durable partitioned key-value storage through `system.storage@1`, backed by SQLite or the filesystem.

## Domain

`system`

## Provides

- `system.storage@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `driver` | `str` | `"sqlite"` | Storage driver: `sqlite` or `disk` |
| `db_path` | `str` | `"data/db/haruquantai.db"` | SQLite database path |
| `base_path` | `str` | `"data/storage"` | Root filesystem directory for the disk driver |

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `StorageEngine` service binding | `FEAT-SYS-PERSIST_STORAGE` | Generation-safe registry revocation |

The current implementations open SQLite connections per operation and close them before returning, so there is no long-lived connection pool to dispose during unmount.

## Persistent State

- Namespace: `system.storage`
- Schema version: `1`
- Retention policy: `retain`
- Unmount policy: retain files and database rows
- Purge policy: explicit caller/admin action only

Feature consumers should request isolated sub-partitions via `storage.partition("<feature-namespace>")` rather than querying another feature's state directly.

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-SYS-VALIDATE_STORAGE_CONFIG` | Validate driver and paths | `StorageConfig.from_dict()` | `config.py` |
| `FR-SYS-STORE_PERSISTENT_DATA` | Store binary payloads | `SqliteStorageEngine.set()`, `DiskStorageEngine.set()` | `sqlite_engine.py`, `engine.py` |
| `FR-SYS-RETRIEVE_PERSISTENT_DATA` | Retrieve binary payloads | `SqliteStorageEngine.get()`, `DiskStorageEngine.get()` | `sqlite_engine.py`, `engine.py` |
| `FR-SYS-PURGE_NAMESPACE_DATA` | Delete keys in an owned partition | `SqliteStorageEngine.delete()`, `DiskStorageEngine.delete()` | `sqlite_engine.py`, `engine.py` |

## Failure Behavior

Invalid storage configuration fails feature mount and triggers transactional scope rollback. Durable data is never automatically purged by unmount.

## Removal Behavior

Removing this feature makes `system.storage@1` unavailable while retained data remains on disk. Features that require persistent storage become `BLOCKED`; optional consumers degrade according to their own manifest.
