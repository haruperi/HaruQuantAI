# Operate Trading Gateway (`FEAT-IFACE-OPERATE_TRADING`)

> **Package:** `app/services/interfaces/operate_trading/`
> **System role:** External boundary gateway exposing governed trading operations, readiness preflights, session controls, and ordered event streams.
> **Status:** `Completed` — Phase 7

## Purpose

Translates external boundary requests for trading operations (`MANAGE_SESSION`, `READINESS`, `PREVIEW_ACTION`, `EMERGENCY`, `MARKET_DATA`, `OPERATOR_ANALYTICS`) into typed `OperateTradingRequest` records and serves their results through the D-IFACE transport.

The gateway never imports broker implementations and never queries MT5/cTrader/Binance directly. It resolves upstream trading capabilities through `FeatureContext` and translates absence into the canonical `CAPABILITY_UNAVAILABLE` failure without inventing execution fills or trading outcomes.

## Domain

`interfaces`

## Provides

- `interfaces.operate-trading@1`

## Required Capabilities

None

## Optional Capabilities

- `trading.account-operations@1`
- `trading.dispatch-orders@1`
- `trading.manage-trading-sessions@1`

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `default_account_id` | `str` | `"default"` | Account identity used when a request carries none. |
| `max_order_quantity` | `float` | `1000.0` | Upper bound accepted for order quantities. |

Unknown configuration keys fail closed at mount.

## Runtime Effects

- Registers one `OperateTradingCapability` provider for the feature's lifetime.
- Opens no sockets, files, or background tasks; request-scoped work only.
- Registers the gateway's cleanup callback for deterministic teardown.

## Persistent State

None

## Functional Requirements

- **FR-IFACE-OT-001** Serve execution-session lifecycle reads and actions (`start`, `stop`, `default`) from the session store.
- **FR-IFACE-OT-002** Serve the trading account profile projection with `api.trading.account_profile.v1` semantics.
- **FR-IFACE-OT-003** Serve per-instrument trading constraints (`api.trading.instrument_constraints.v1`).
- **FR-IFACE-OT-004** Translate unmounted upstream capabilities to the stable `CAPABILITY_UNAVAILABLE` envelope.
- **FR-IFACE-OT-005** Reject malformed operation payloads with typed validation failures.

## Failure Behavior

- Unmounted upstream capability: canonical `CAPABILITY_UNAVAILABLE` error envelope; no fallback execution path.
- Invalid configuration: mount fails closed with a typed error.
- Unknown operation or malformed payload: typed validation failure envelope.

## Removal Behavior

- Unmounting the feature withdraws the `interfaces.operate-trading@1` provider; boundary routes answer `CAPABILITY_UNAVAILABLE`.
- No persisted state is owned, so removal leaves no residue.
