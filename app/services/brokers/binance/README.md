# Binance Direct Broker Channel

**Feature ID:** `FEAT-BRK-CONNECT_BINANCE`

## Domain

`brokers`

## Purpose

Provide direct market data reads (quotes, order books, ticks, and historical klines) and live WebSocket event normalization for Binance Spot through the ProviderBackend protocol without cross-feature dependencies or persistence.

## Provides

- `broker.provider.binance@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `api_key` | string or null | No | Optional Binance API key for authenticated endpoints. |
| `api_secret` | string or null | No | Optional Binance API secret for authenticated endpoints. |
| `circuit_failure_threshold` | integer | No | Consecutive failures before opening transport circuit. |
| `circuit_half_open_max_calls` | integer | No | Trial probes allowed in half-open circuit state. |
| `circuit_recovery_timeout_sec` | float | No | Seconds before half-open retry after circuit trip. |
| `connect_timeout_sec` | float | No | Timeout in seconds for connection probes. |
| `environment` | string | No | Operating environment (TESTNET, SANDBOX, LIVE). |
| `probe_symbol` | string or null | No | Symbol used to verify connectivity during session handshake. |
| `request_timeout_sec` | float | No | Timeout in seconds for REST and WebSocket requests. |
| `stream_buffer_size` | integer | No | In-memory message buffer limit for active streams. |

## Persistent State

None.

## Runtime Effects

Mount publishes `broker.provider.binance@1` to `FeatureContext`. REST and WebSocket transports are initialized with circuit-breaker protection; all background streams and tasks are tracked and cancelled cleanly upon unmount or close.

## Operations

- `manage_sessions`: Validates session environment (`TESTNET`, `SANDBOX`, `LIVE`), executes probe verification on connect/reconnect, reports session readiness, and handles clean disconnection.
- `read_provider_state`: Executes genuine bounded reads for Spot market state (`READ_MARKET`), historical klines (`PAGE_HISTORY`), and normalizes live WebSocket events (`NORMALIZE_EVENT`). Private reads (`READ_ACCOUNT`, `READ_TRADING_STATE`) fail closed with `BROKER_PROFILE_UNSUPPORTED`.
- `transport_orders`: All order transport operations (`VALIDATE_REQUEST`, `SUBMIT`, `CANCEL`, `MODIFY`, `JOURNAL`) fail closed with `BROKER_PROFILE_UNSUPPORTED`.

## Failure Behavior

- Environment mismatches fail closed with `BROKER_ENVIRONMENT_MISMATCH`.
- Transport or probe failures return `BROKER_SESSION_NOT_READY` or `BROKER_VALIDATION_FAILED`.
- Unreleased operations fail closed with `BROKER_PROFILE_UNSUPPORTED`.

## Removal Behavior

Unmounting this feature closes active client transport sessions, cancels all running background tasks, and withdraws `broker.provider.binance@1` from the registry.

## Evidence

Run `uv run python -m app.services.brokers.binance.binance` for the executable scenario harness. Automated tests live in `tests/brokers/unit/test_binance_feature.py`.
