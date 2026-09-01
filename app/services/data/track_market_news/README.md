# FEAT-DATA-TRACK_MARKET_NEWS — Track Market News

## Purpose
Record immutable economic-calendar/news observations and revisions, then answer point-in-time queries without exposing information before it was observed.

## Domain
data

## Provides
- `data.track-market-news@1`

## Required Capabilities
None.

## Optional Capabilities
None.

## Configuration
- `database_path` — feature-owned SQLite path. Default: `.haruquant/data-market-news.sqlite3`.

## Runtime Effects
RECORD and REVISE perform bounded feature-owned SQLite transactions. QUERY performs a bounded point-in-time read. Mount performs no I/O and starts no background task.

## Persistent State
`data.market_news` schema version 1 is retained. It owns immutable observations plus revision/cancellation records whose visibility begins at their exact `visible_from` timestamps.

## Functional Requirements
- Preserve first-seen, retrieved, scheduled/published, scope, impact, source, and payload-hash evidence.
- Keep revisions append-only and visible only from their declared observation time.
- Exclude an item only after a visible cancellation revision exists.
- Enforce optional freshness limits against the query `as_of` instant.
- Fail closed when complete source coverage is requested but cannot be proven from the v1 contract.
- Never decide whether trading is allowed around an event; Risk owns that policy.

## Failure Behavior
Unknown revision parents return `DATA_NOT_FOUND`; unprovable complete coverage or stale evidence returns `DATA_COVERAGE_INCOMPLETE`; immutable identity conflicts and SQLite failures propagate explicitly.

## Removal Behavior
Removing the feature withdraws `data.track-market-news@1` and retains its point-in-time evidence. Research, Risk, and Agentic consumers requiring the capability become unavailable without changing unrelated Data features.
