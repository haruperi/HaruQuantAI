# cTrader Direct Broker Channel

**Feature ID:** `FEAT-BRK-CONNECT_CTRADER`

## Domain

`brokers`

## Purpose

Provide direct cTrader Open API connection lifecycle, session management, genuine bounded market data, account state, and streams without cross-feature dependencies or persistence.

## Provides

- `broker.provider.ctrader@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `access_token` | string or null | No | Optional cTrader Open API OAuth access token. |
| `account_id` | string or null | No | Optional cTrader account reference identifier. |
| `circuit_failure_threshold` | integer | No | Consecutive failures before opening transport circuit. |
| `circuit_half_open_max_calls` | integer | No | Trial probes allowed in half-open circuit state. |
| `circuit_recovery_timeout_sec` | float | No | Seconds before half-open retry after circuit trip. |
| `client_id` | string or null | No | Optional cTrader Open API client application ID. |
| `client_secret` | string or null | No | Optional cTrader Open API client secret. |
| `connect_timeout_sec` | float | No | Timeout in seconds for connection probes. |
| `environment` | string | No | Operating environment (DEMO, LIVE, SANDBOX, TESTNET). |
| `probe_symbol` | string or null | No | Symbol used to verify connectivity during session handshake. |
| `request_timeout_sec` | float | No | Timeout in seconds for cTrader protobuf requests. |
| `stream_buffer_size` | integer | No | In-memory message buffer limit for active streams. |

## Persistent State

None.

## Runtime Effects

Mount publishes `broker.provider.ctrader@1` to `FeatureContext`. Protobuf TCP transport and Twisted network clients are initialized with circuit-breaker protection; all background streams and tasks are tracked and cancelled cleanly upon unmount or close.

## Operations

- `manage_sessions`: Validates session environment (`DEMO`, `LIVE`, `SANDBOX`, `TESTNET`), executes probe verification on connect/reconnect, reports session readiness, and handles clean disconnection.
- `read_provider_state`: Executes genuine bounded reads for account state (`READ_ACCOUNT`), trading state (`READ_TRADING_STATE`), market state (`READ_MARKET`), historical bars/ticks (`PAGE_HISTORY`), and normalizes live event payloads (`NORMALIZE_EVENT`).
- `transport_orders`: All order transport operations (`VALIDATE_REQUEST`, `SUBMIT`, `CANCEL`, `MODIFY`, `JOURNAL`) fail closed with `BROKER_PROFILE_UNSUPPORTED` in accordance with the unreleased write policy.

## Failure Behavior

- Environment mismatches fail closed with `BROKER_ENVIRONMENT_MISMATCH`.
- Transport or probe failures return `BROKER_SESSION_NOT_READY` or `BROKER_VALIDATION_FAILED`.
- Unreleased operations fail closed with `BROKER_PROFILE_UNSUPPORTED`.

## Removal Behavior

Unmounting this feature closes active client transport sessions, cancels all running background tasks, and withdraws `broker.provider.ctrader@1` from the registry.

## Evidence

Run `uv run python -m app.services.brokers.ctrader.ctrader` for the executable scenario harness. Automated tests live in `tests/brokers/unit/test_ctrader_feature.py`.
