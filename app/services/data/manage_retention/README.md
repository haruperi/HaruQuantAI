# FEAT-DATA-MANAGE_RETENTION — Manage Retention

## Purpose

Define durable Data retention/quarantine policy and collect only unreachable immutable Data series after the configured age boundary.

## Domain

data

## Provides

- `data.manage-retention@1`

## Required Capabilities

- `data.series-retention-collector@1`

## Optional Capabilities

None.

## Configuration

- `database_path`: feature-owned retention-policy SQLite path.
- `collection_limit`: bounded 1–10000 maximum series versions per collection pass; default 100.

## Runtime Effects

Explicit policy writes and collection requests perform bounded SQLite work. Physical series deletion is delegated to the owning series feature; mount performs no database I/O.

## Persistent State

Namespace `data.retention_policy`, schema version 1, retained on uninstall. Policy definitions are immutable.

## Functional Requirements

- Persist immutable retention policies.
- Treat `retention_days + quarantine_days` as the minimum age before unreachable collection; when retention days are absent, the quarantine period still applies.
- Preserve every run-pinned series version.
- Bound each physical collection pass.
- Never query or mutate another feature's private tables.

## Failure Behavior

Collection without a defined policy fails with `DATA_NOT_FOUND`. Immutable policy-ID reuse with different content fails closed. Physical collection failures propagate.

## Removal Behavior

Removing this feature withdraws retention administration and garbage collection. Immutable Data series remain available because their physical storage is owned independently by `FEAT-DATA-MANAGE_SERIES`.
