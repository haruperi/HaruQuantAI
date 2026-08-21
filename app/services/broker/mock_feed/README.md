# FEAT-BROKER-FEED_MOCK — Mock Broker Feed

## Purpose

Provide deterministic raw historical bar generation for local research, simulation, and unit testing without external network or broker dependencies.

## Domain

`broker`

## Provides

- `broker.market-data@1`

## Required Capabilities

None (root provider)

## Optional Capabilities

None

## Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `base_price` | `float` | `1.1000` | Center price level for synthetic price waves |

## Supported Timeframes

- `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`

## Runtime Effects

| Effect | Owner | Disposal |
| :--- | :--- | :--- |
| `BrokerMarketData` service binding | `FEAT-BROKER-FEED_MOCK` | Revoke service binding from registry |

## Persistent State

None

## Functional Requirements

| Requirement ID | Responsibility | Implementing Symbol | Source File |
| :--- | :--- | :--- | :--- |
| `FR-BROKER-VALIDATE_FEED_CONFIG` | Validate base price constraint | `MockFeedConfig.from_dict()` | `config.py` |
| `FR-BROKER-GENERATE_RAW_BARS` | Generate deterministic raw OHLCV price bars | `MockBrokerMarketData.retrieve_bars()` | `feed.py` |

## Failure Behavior

- Non-positive `base_price` $\rightarrow$ Mount raises `ValueError` $\rightarrow$ transitions to `FAILED_START` with complete rollback.
- Unsupported query timeframe $\rightarrow$ `retrieve_bars()` raises `ValueError`.

## Removal Behavior

Removing or deleting this feature unbinds `broker.market-data@1`. Any dependent features requiring `broker.market-data@1` gracefully unmount and transition to `BLOCKED`.
