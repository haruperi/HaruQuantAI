# FEAT-BROKER-FEED_MOCK — Mock Broker Feed

## Purpose

Provide deterministic raw historical OHLCV bars for local research, simulation, and unit testing without external network or broker dependencies.

## Domain

`broker`

## Provides

- `broker.market-data@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `base_price` | `float` | `1.1000` | Center price level for deterministic synthetic bars |

Supported timeframes: `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, and `MN1`. Unknown timeframe identifiers raise `ValueError`; they are never silently treated as another interval.

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `BrokerMarketData` service binding | `FEAT-BROKER-FEED_MOCK` | Generation-safe registry revocation |

## Persistent State

None.

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-BROKER-VALIDATE_FEED_CONFIG` | Validate synthetic base price | `MockFeedConfig.from_dict()` | `config.py` |
| `FR-BROKER-GENERATE_RAW_BARS` | Generate deterministic raw OHLCV bars | `MockBrokerMarketData.retrieve_bars()` | `feed.py` |
| `FR-BROKER-RESOLVE_TIMEFRAME` | Resolve supported bar interval and reject unknown identifiers | `MockBrokerMarketData._resolve_timeframe_step()` | `feed.py` |

## Failure Behavior

- Invalid base price → mount raises `ValueError` → `FAILED_START` with scope rollback.
- Unknown timeframe → request raises `ValueError` without changing feature lifecycle state.

## Removal Behavior

Removing this feature unbinds `broker.market-data@1`. Required consumers such as Historical Bars stop and transition to `BLOCKED`; unrelated capabilities remain active.
