# FEAT-DATA-AGGREGATE_BARS — Aggregate Bars

## Purpose
Derive coarser closed-bar versions from committed bar evidence without lookahead, silent gap filling, or inferred session authority.

## Domain
data

## Provides
- `data.aggregate-bars@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
- `max_output_bars` — hard result bound, default `500000`, allowed `1..2000000`.

## Runtime Effects
AGGREGATE performs bounded series-store reads, deterministic in-memory aggregation, and one immutable derived-version write. Mount performs no I/O or background work.

## Persistent State
None. Derived bar payloads are owned by `FEAT-DATA-MANAGE_SERIES`.

## Functional Requirements
- Require an explicit stored source timeframe.
- Require the target timeframe to be an exact coarser multiple of the source timeframe.
- Aggregate only complete UTC-aligned source buckets; incomplete buckets remain absent.
- Preserve first open, highest high, lowest low, last close, summed volume, and close spread evidence when present.
- Reject synthetic gap emission because the current Bar contract lacks explicit synthetic-gap provenance.
- Fail closed for session-boundary aggregation until Data and Catalogue share an unambiguous session identity contract.

## Failure Behavior
Missing source versions return `DATA_NOT_FOUND`; missing source cadence returns `DATA_PRECISION_UNAVAILABLE`; unsupported or incompatible timeframe/session requests fail explicitly without publishing a derived version.

## Removal Behavior
Removing the feature withdraws `data.aggregate-bars@1`; source and already-derived immutable versions remain owned by the series store and unrelated Data features stay active.
