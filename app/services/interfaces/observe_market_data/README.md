# Observe Market Data — FEAT-IFACE-OBSERVE_MARKET_DATA

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Expose the Market Ticks vertical slice: project the Data-owned live market
event stream into bounded market tick snapshots with source identity,
monotonic sequence, gap counting, and honest staleness, plus resumable,
symbol-filtered observation event delivery. The gateway owns presentation
of transport observations only: it never imports a Data or broker
implementation, never invents quotes, and reports provider absence or loss
truthfully through the stable `CAPABILITY_UNAVAILABLE` result or explicit
stale snapshots. This is the Phase 3 reference slice of the D-IFACE
migration recorded in
`docs/dev/iface-ui-migration/phase-0-baseline-reconciliation.md`.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| ObserveMarketDataCapability | `interfaces.observe-market-data@1` |

## Required Capabilities

| Capability bundle | Runtime identifier |
| --- | --- |
| StreamMarketEventsCapability | `data.stream-market-events@1` |

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `stale_after_seconds` | number > 0 | `5.0` | Seconds without provider events after which snapshots report stale. |
| `max_symbols` | integer 1..200 | `50` | Maximum accepted symbol-filter size per snapshot request. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Resolves the required `data.stream-market-events@1` provider through
  `FeatureContext`; absence fails the mount closed (`BLOCKED`).
- Spawns exactly one supervised consumer task
  (`observe-market-data:consume`) that applies provider events to the
  in-memory latest-quote buffer; the task is cancelled and awaited on
  feature disposal.
- Registers exactly one scope cleanup callback (`gateway.close`) clearing
  the buffer and failing later use closed.
- Publishes exactly the `interfaces.observe-market-data@1` capability
  bundle; no durable state, no sockets, no import-time effects.

## Persistent State

None. The latest-quote buffer is process-local and cleared on disposal;
retention and replay truth remain owned by the Data provider.

## Functional Requirements

| Requirement | Requirement statement | Usage-harness scenario |
| --- | --- | --- |
| FR-IFACE-OMD-001 | Project the latest quote per observed symbol without inventing values. | quote projection |
| FR-IFACE-OMD-002 | Carry the provider identity and monotonic event sequence in every snapshot. | source identity + sequence |
| FR-IFACE-OMD-003 | Count provider sequence discontinuities as snapshot gaps. | gap counting |
| FR-IFACE-OMD-004 | Report staleness with an explicit reason, including before the first event and after provider loss. | honest staleness |
| FR-IFACE-OMD-005 | Filter snapshots by a bounded symbol set and reject oversized filters. | symbol filter |
| FR-IFACE-OMD-006 | Deliver resumable, symbol-filtered observation events by delegating to the provider subscription. | event delivery |
| FR-IFACE-OMD-007 | Fail closed with CAPABILITY_UNAVAILABLE when the gateway is disposed. | disposal failure |
| FR-IFACE-OMD-008 | Degrade truthfully when the provider stream ends while keeping the last known snapshot available as stale. | provider loss |
| FR-IFACE-OMD-009 | Serve the observations on the wire through the transport mounting surface: JSON snapshots at `GET /api/v1/market/ticks` and SSE `StreamEvent` frames at `GET /api/v1/market/ticks/stream` and the adopted alias `GET /api/v1/data/snapshot-stream`. | served boundary |

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.observe_market_data.gateway
```

## Failure Behavior

- Missing `data.stream-market-events@1` provider blocks activation
  (`CapabilityUnavailableError` during mount); the feature provides
  nothing.
- Provider stream ending degrades the gateway: snapshots keep serving the
  last known truth marked stale with the recorded reason.
- Provider stream failure records the degraded reason and re-raises so
  kernel runtime-failure reconciliation owns the withdrawal.
- Oversized symbol filters return `INTERFACE_VALIDATION_FAILED`; malformed
  provider payloads advance the sequence without projecting a quote and
  never fabricate values.
- Use after disposal returns `CAPABILITY_UNAVAILABLE` `InterfaceFailure`;
  repeated disposal is a no-op.

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`interfaces.observe-market-data@1` capability: Python consumers receive
`CapabilityUnavailableError` and external surfaces translate it to the
stable `CAPABILITY_UNAVAILABLE` failure. Scope disposal cancels the
supervised consumer task, clears the quote buffer, and closes open
subscriptions; unrelated features (including other Interfaces features
such as `FEAT-IFACE-SERVE_API_EVENTS`) remain active. The Data provider
and its durable state are unaffected.
