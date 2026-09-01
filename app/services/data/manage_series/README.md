# FEAT-DATA-MANAGE_SERIES — Immutable Series Store

## Purpose
Own immutable Data-series payloads and exact run-binding pins so focused Data features collaborate through a declared capability instead of sibling implementation imports or shared private tables.

## Domain
data

## Provides
- `data.series-store@1`

## Required Capabilities
None.

## Optional Capabilities
None.

## Configuration
- `database_path` — SQLite file owned by this feature. Default: `.haruquant/data-series.sqlite3`.

## Runtime Effects
Explicit capability calls may create the configured SQLite file, create the feature-owned schema, perform bounded transactions, and offload blocking SQLite work to a worker thread. Mount itself performs no I/O and starts no background task.

## Persistent State
`data.series_store` schema version 1 is retained. It owns immutable stored payload rows and exact binding-to-version pins. No other Data feature may access its tables directly.

## Functional Requirements
- Store immutable tick, bar, scenario, indicator, and opaque Data evidence under UUIDv7 version identities.
- Reject identity reuse when the payload or content hash differs.
- Expose typed reads through `data.series-store@1` only.
- Pin versions referenced by immutable run bindings.
- Collect only unpinned versions and only through an explicit bounded operation.

## Failure Behavior
Invalid configuration, immutable identity conflicts, unknown versions referenced by a pin, invalid collection bounds, SQLite errors, and malformed stored payloads propagate deterministically; no partial capability bundle is published if mount fails.

## Removal Behavior
Removing the feature withdraws `data.series-store@1`; dependent Data features become blocked or remount according to their manifests. Retained SQLite state remains opaque and untouched, and unrelated domains/features stay active.
