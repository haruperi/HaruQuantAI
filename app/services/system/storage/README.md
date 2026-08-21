# FEAT-SYS-PERSIST_STORAGE — Persistent Storage Engine

## Purpose

Durable, disk-backed, and SQLite-backed partitioned key-value storage engine providing the `system.storage@1` infrastructure capability for persistent state across unmount and remount cycles.

## Domain

`system`

## Provides

- `system.storage@1`

## Required Capabilities

None (root infrastructure provider)

## Optional Capabilities

None

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `driver` | `str` | `"sqlite"` | Storage driver (`"sqlite"` or `"disk"`) |
| `db_path` | `str` | `"data/db/haruquantai.db"` | SQLite database file path (when driver is sqlite) |
| `root_dir` | `str` | `"data/storage"` | Root filesystem directory (when driver is disk) |

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `StorageEngine` service binding | `FEAT-SYS-PERSIST_STORAGE` | Revoke `system.storage@1` registration from registry |

## Persistent State

- Namespace: `system.storage` (and sub-partitions like `data.historical_bars`, `risk.limits`)
- Schema Version: `1`
- Retention Policy: `retain` (state remains on disk and inside SQLite database across unmount and remount cycles)
- Purge Policy: `explicit`

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-SYS-VALIDATE_STORAGE_CONFIG` | Validates root directory path and SQLite db path | `StorageConfig.from_dict()` | `config.py` |
| `FR-SYS-STORE_PERSISTENT_DATA` | Atomic binary persistence to SQLite and disk | `SqliteStorageEngine.set()`, `DiskStorageEngine.set()` | `sqlite_engine.py`, `engine.py` |
| `FR-SYS-RETRIEVE_PERSISTENT_DATA` | Retrieve stored binary by key and namespace | `SqliteStorageEngine.get()`, `DiskStorageEngine.get()` | `sqlite_engine.py`, `engine.py` |
| `FR-SYS-PURGE_NAMESPACE_DATA` | Remove keys and isolate partitions | `SqliteStorageEngine.delete()`, `DiskStorageEngine.delete()` | `sqlite_engine.py`, `engine.py` |

## Failure Behavior

- Unwritable path or invalid directory $\rightarrow$ Mount raises `ValueError` $\rightarrow$ transitions to `FAILED_START` with full scope rollback.

## Removal Behavior

Removing this feature unbinds `system.storage@1`. Features requiring persistent storage gracefully degrade or transition to `BLOCKED`.
