# FEAT-DATA-GENERATE_SCENARIOS — Generate Scenarios

## Purpose
Generate deterministic synthetic/scenario Data versions with structural provenance so generated evidence can never masquerade as observed provider history.

## Domain
data

## Provides
- `data.generate-scenarios@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
- `max_points` — hard generation bound, default `100000`, allowed `1..1000000`.

## Runtime Effects
Generation performs bounded CPU work and writes one immutable scenario payload through the required series-store capability. Transform operations read one committed bar-shaped source version and publish a distinct version. Mount performs no I/O or background work.

## Persistent State
None. Generated immutable payloads are owned by `FEAT-DATA-MANAGE_SERIES`.

## Functional Requirements
- Preserve the proven seeded GBM baseline as the supported synthetic model.
- Pin model version, parameters, timeframe, interval, instrument, seed streams, and content hash.
- Reject unsupported calendar-month generation rather than approximating it silently.
- Apply pinned shock/gap/volatility/liquidity/outage/missingness transforms without mutating the source version.
- Store generated output under a distinct immutable UUIDv7 version classified as scenario evidence.

## Failure Behavior
Invalid model parameters return `DATA_VALIDATION_FAILED`; unsupported timeframe semantics return `DATA_TIMEFRAME_UNSUPPORTED`; missing or hash-mismatched transform sources fail explicitly. Store errors propagate.

## Removal Behavior
Removing the feature withdraws `data.generate-scenarios@1`; previously generated immutable scenario evidence remains retained by the series-store owner and cannot become provider history through removal.
