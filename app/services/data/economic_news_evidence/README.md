# Economic Calendar and News Evidence

**Feature ID:** `FEAT-DATA-TRACK_MARKET_NEWS`

## Domain

`data`

## Purpose

Preserve point-in-time economic/news observations, revisions, coverage, freshness, and restriction evidence.

## Provides

`data.track-market-news@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string / Path | No | SQLite database storage path or `:memory:` (default: `:memory:`). |
| `max_query_results` | integer | No | Maximum returned observations per query (default: 10,000). |
| `default_rate_limit_per_minute` | integer | No | Rate limit per source provider per minute (default: 60). |
| `max_payload_size_bytes` | integer | No | Maximum allowed payload size in bytes (default: 5,000,000). |
| `default_freshness_limit_seconds` | integer | No | Default maximum age in seconds for freshness evaluation (default: 86,400). |
| `allowed_sources` | set | No | Set of authorized provider source IDs. |

## Persistent State

Namespace `data.economic_news` retaining observation versions, revisions, and coverage evidence.

## Runtime Effects

Mount registers `data.track-market-news@1` in `FeatureContext`. Operations govern observation recording, revision tracking, point-in-time lookahead-safe queries, non-authorizing restriction projections, and network ingestion validation.

## Operations

- `RECORD`: Records newly observed economic/news items with provider event ID, timestamps, impact, currencies, and payload hash.
- `REVISE`: Versions event revisions, cancellations, reschedules, and value updates without lookahead bias.
- `QUERY`: Executes point-in-time queries declaring `as_of`, interval, and filters. Excludes unobserved future data and revisions strictly.

## Failure Behavior

- Unregistered observation during revision returns `DATA_NOT_FOUND`.
- Conflicting revision sequence returns `DATA_VERSION_CONFLICT`.
- Stale or incomplete coverage under `require_complete_coverage` returns `DATA_COVERAGE_INCOMPLETE`.
- Malformed timestamps, negative intervals, or invalid hashes return `DATA_VALIDATION_FAILED`.

## Removal Behavior

Removing this feature withdraws `data.track-market-news@1`. Research, Trading, or Risk features requiring news evidence fail closed; other market data remains available.

## Evidence

Run `uv run python -m app.services.data.economic_news_evidence.economic_news_evidence` for the executable scenario harness. Automated unit tests live in `tests/services/data/economic_news_evidence/`.
