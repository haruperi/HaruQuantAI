# Real-Time Market Events

**Feature ID:** `FEAT-DATA-STREAM_MARKET_EVENTS`

## Domain

`data`

## Purpose

Normalize genuine live quotes, ticks, depth, status events, feed lifecycle, bounded buffering, gaps, and reconnect evidence.

## Provides

`data.stream-market-events@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string / Path | No | SQLite database storage path or `:memory:` (default: `:memory:`). |
| `buffer_capacity` | integer | No | Maximum buffered events per market feed (default: 1,000). |
| `max_subscriptions` | integer | No | Maximum concurrent event subscriptions (default: 100). |
| `max_instruments_per_subscription` | integer | No | Maximum instruments per subscription filter (default: 500). |
| `stale_timeout_seconds` | integer | No | Timeout threshold in seconds to classify a live feed as STALE (default: 30). |
| `heartbeat_timeout_seconds` | integer | No | Heartbeat interval threshold in seconds (default: 15). |
| `max_replay_limit` | integer | No | Maximum replayable historical events per subscription (default: 10,000). |
| `default_ordering_mode` | string | No | Default ordering mode (`RECEIPT_ORDER` or `PROVIDER_SEQUENCE`). |
| `backpressure_policy` | string | No | Backpressure policy upon buffer saturation (default: `DROP_AND_GAP`). |
| `snapshot_bridge_enabled` | boolean | No | Bind the authenticated MT5 snapshot bridge listener (default: `false`). |
| `snapshot_bridge_host` | string | No | Bridge listener bind host (default: `127.0.0.1`). |
| `snapshot_bridge_port` | integer | No | Bridge listener bind port (default: 9001). |
| `snapshot_bridge_source_id` | string | No | Exact source identity the bridge requires from the EA hello (default: `mt5-terminal-1`). |
| `snapshot_bridge_auth_token` | string | No | Shared secret the bridge requires from the EA hello; enabling without a token keeps the listener off (default: empty). |
| `snapshot_bridge_symbols` | string | No | Comma-separated symbol set commanded to the EA on authentication (default: `EURUSD,GBPUSD,USDJPY,XAUUSD`). |

## Persistent State

Namespace `data.realtime_market_events` retaining real-time market event records, feed states, and replay partitions.

## Runtime Effects

Mount registers `data.stream-market-events@1` in `FeatureContext`. Operations govern provider feed binding, feed state observation, gap/staleness detection, reconnect lifecycles, bounded live event subscriptions, and immutable replay partitions. When `snapshot_bridge_enabled` is set with an authentication token, mount additionally binds the `haruquant.mt5.snapshot.v2` TCP listener for the MetaTrader 5 TickBridge EA; accepted snapshots are normalized into ingested `MarketEvent` records. A bind failure logs a warning and leaves the feature serving without live snapshots.

## Operations

- `BIND_FEED`: Registers or binds a live market feed for an authorized provider, initializing generation and connecting state.
- `FEED_STATE`: Observes feed readiness state ladder (`CONNECTING`, `LIVE`, `DELAYED`, `STALE`, `GAP`, `RECONNECTING`, `FAILED`, `STOPPED`) with freshness evidence.
- `REPLAY`: Produces an immutable bounded event partition reference (`MarketReplayRef`) for a specified interval with content hash and artifact ID.

## Subscriptions

`subscribe_stream_market_events_events`: Asynchronously streams normalized `DomainEvent` envelopes with optional provider, feed, instrument filtering, and bounded replay limits.

## Failure Behavior

- Unknown feed lookup returns `DATA_NOT_FOUND`.
- Missing required fields or inverted intervals returns `DATA_VALIDATION_FAILED`.
- Feed gap / overflow conditions emit explicit gap findings and update feed state without silent drops.

## Removal Behavior

Removing this feature withdraws `data.stream-market-events@1`. Operational consumers relying on real-time market events degrade; historical market data remains accessible.

## Evidence

Run `uv run python -m app.services.data.realtime_market_events.realtime_market_events` for the executable scenario harness. Automated unit tests live in `tests/services/data/realtime_market_events/`.
