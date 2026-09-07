# Observe Market Reference (`FEAT-IFACE-OBSERVE_MARKET_REFERENCE`)

## Purpose

Translate the ratified Interfaces market reference contract onto the Data-owned
browse-reference capability: capabilities, market series, instruments,
brokers, symbol discovery, quote reads, historical bars, reference sync,
and market directory projections.

## Domain

`interfaces`

## Provides

- `interfaces.observe-market-reference@1`

## Required Capabilities

None

## Optional Capabilities

- `data.browse-reference@1`

## Configuration

None

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Registers one callback to close the gateway on feature unmount.
- Holds an optional reference to the resolved `data.browse-reference@1` provider.
- Allocates no background tasks, threads, or open sockets.

## Persistent State

None

## Operations

Strict pass-through bridge without calculations or state mutations, delegating directly to `data.browse-reference@1`:
- `OBSERVE_SERIES`: Forward series catalogue queries.
- `UPDATE_SERIES`: Forward series and instrument contract specification updates.
- `DELETE_SERIES`: Forward series deletion requests.
- `OBSERVE_INSTRUMENTS` & `OBSERVE_INSTRUMENT`: Forward instrument specification queries.
- `UPDATE_INSTRUMENT`: Forward instrument specification updates.
- `OBSERVE_BROKERS`: Forward broker profile queries.
- `OBSERVE_BARS`: Forward historical bar reads.
- `INSPECT_QUALITY`: Forward data quality anomaly inspection requests.
- `CLONE_SERIES`: Forward timezone series cloning requests.
- `EXPORT_DATA`: Forward CSV and historical data export requests.
- `DOWNLOAD_DUKASCOPY`: Forward Dukascopy download requests.
- `BATCH_ACTION`: Forward batch operations (bulk delete, export, download).

## Failure Behavior

- Returns `CAPABILITY_UNAVAILABLE` (status 503) when the gateway has been closed
  or the upstream `data.browse-reference@1` provider is absent.
- Translates upstream `DataFailure` into the unified `InterfaceFailure` envelope.

## Removal Behavior

Disposing the feature unregisters the capability and fails pending calls closed.
Upstream data reference state and storage remain unaffected.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.observe_market_reference._usage
```
