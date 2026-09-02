# Service-Level Broker Resolver

**Feature ID:** `FEAT-BRK-RESOLVE`

## Domain

`broker`

## Purpose

Centralizes active broker module selection so API routes, trading execution
workers, and market data ingestion pipelines do not own broker adapter policy.

## Provides

`broker.resolver@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Optional SQLite database path for broker table queries. |

Unknown keys and non-string values are rejected during configuration parsing.

## Persistent State

`broker.resolve` schema version 1 retains `broker` records in the central `haruquantai.db` SQLite database via internal feature persistence. Retention policy is `retain`: removing the feature leaves configured broker profiles intact.

## Runtime Effects

Mount stages the `broker.resolver@1` capability provider into the feature scope. Database queries open bounded connections and close in all execution paths.

## Functional Requirements

- `FR-BRK-RESOLVE_BROKER`: Resolve and return active broker module configuration dictionary containing `id`, `name`, `platform`, `desc`, `active`, and `timezone` from runtime settings and database state.
- Manage and initialize `broker` table with SQLite schema and default seeds via internal `_persistence.py`.

## Failure Behavior

If no active broker record exists and no runtime setting is found, the resolver falls back deterministically to safe default configuration without raising unhandled exceptions.

## Removal Behavior

Removing this feature withdraws the `broker.resolver@1` capability. Active broker records remain stored in `haruquantai.db`; consumers requiring dynamic broker resolution must supply explicit fallback adapter configurations.
