# Broker Provider Gateway

**Feature ID:** `FEAT-BRK-DISPATCH_PROVIDERS`

## Domain

`brokers`

## Purpose

Provide the public Broker business capabilities (`broker.manage-sessions@1`, `broker.read-provider-state@1`, and `broker.transport-orders@1`) by dispatching explicitly addressed operations to mounted provider backends without cross-provider ranking, selection, fallback, or retry policy.

## Provides

- `broker.manage-sessions@1`
- `broker.read-provider-state@1`
- `broker.transport-orders@1`

## Required Capabilities

None.

## Optional Capabilities

- `broker.provider.metatrader@1`
- `broker.provider.ctrader@1`
- `broker.provider.binance@1`
- `broker.provider.dukascopy@1`
- `broker.provider.yahoo@1`

## Configuration

None.

## Persistent State

None.

## Runtime Effects

Mount resolves optional provider-backend capabilities dynamically through `FeatureContext` and stages `broker.manage-sessions@1`, `broker.read-provider-state@1`, and `broker.transport-orders@1`. No background tasks or network sockets are acquired by the gateway directly.

## Operations

- `manage_sessions`: Dispatches session lifecycle operations (`OPEN`, `TRANSITION`, `RECONNECT`, `ASSESS_READINESS`, `CLOSE`) to the provider backend explicitly bound to the session.
- `read_provider_state`: Dispatches provider-truth read operations (`READ_ACCOUNT`, `READ_TRADING_STATE`, `READ_MARKET`, `PAGE_HISTORY`, `NORMALIZE_EVENT`) to the provider backend explicitly bound to the session.
- `transport_orders`: Dispatches execution transport operations (`VALIDATE_REQUEST`, `SUBMIT`, `CANCEL`, `MODIFY`, `JOURNAL`) to the provider backend explicitly bound to the session or operation reference.

## Failure Behavior

- Unmapped session or profile references return `CAPABILITY_UNAVAILABLE`.
- Absent or unmounted provider capabilities return `CAPABILITY_UNAVAILABLE`.
- Provider-reported rejections and unknown outcomes are returned directly to the caller without fallback or cross-provider retry.

## Removal Behavior

Removing this feature withdraws `broker.manage-sessions@1`, `broker.read-provider-state@1`, and `broker.transport-orders@1` from the runtime registry; subsequent requests fail closed with `CAPABILITY_UNAVAILABLE`.

## Evidence

Run `uv run python -m app.services.brokers.provider_gateway.provider_gateway` for the executable scenario harness. Automated tests live in `tests/brokers/unit/test_provider_gateway.py`.
