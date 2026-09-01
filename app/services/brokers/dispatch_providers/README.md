# FEAT-BRK-DISPATCH_PROVIDERS — Explicit Provider Dispatch

## Responsibility

Expose the three public Broker runtime capabilities and route every request to
exactly one installed provider feature by immutable `profile_id`.

The dispatcher does **not** own provider SDKs, credentials, instrument mappings,
trading permission, environment admission, conformance certification, or read/write
fallback policy. Missing and ambiguous routes fail closed. It never retries a request
against another provider.

## Provides

- `broker.manage-sessions@1`
- `broker.read-provider-state@1`
- `broker.transport-orders@1`

## Optional provider gateways

- `broker.provider.mt5@1`
- `broker.provider.ctrader@1`
- `broker.provider.binance@1`
- `broker.provider.dukascopy@1`
- `broker.provider.yahoo@1`

Provider gateways are internal feature-to-feature contracts and are not UI/API wire
surfaces.
