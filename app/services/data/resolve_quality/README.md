# FEAT-DATA-RESOLVE_QUALITY — Resolve Quality

## Purpose
Detect quality anomalies against immutable Data evidence and persist explicit resolution decisions without mutating the source version.

## Domain
data

## Provides
- `data.resolve-quality@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
- `database_path` — feature-owned SQLite path. Default: `.haruquant/data-quality.sqlite3`.

## Runtime Effects
DETECT performs bounded reads through the series-store capability and persists deterministic findings in the feature-owned quality database. RESOLVE appends an explicit quality decision. Mount performs no I/O or background task creation.

## Persistent State
`data.quality` schema version 1 is retained. It contains deterministic findings and immutable explicit quality decisions only.

## Functional Requirements
- Detect ordering, duplicate-key, crossed-quote, and zero-volume evidence from stored public bar/tick records.
- Never silently transform source evidence during detection.
- Persist findings by immutable source version.
- Persist explicit caller-authored decisions without overwriting a different decision under the same identity.

## Failure Behavior
Unknown source versions return `DATA_NOT_FOUND`. Missing `data.series-store@1` blocks activation. Immutable decision conflicts and persistence failures propagate rather than being converted to success.

## Removal Behavior
Removing the feature withdraws `data.resolve-quality@1`, retains its evidence database, and does not delete or modify source series stored by another feature.
