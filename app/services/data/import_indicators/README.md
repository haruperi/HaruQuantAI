# FEAT-DATA-IMPORT_INDICATORS — Import Indicators

## Purpose

Import externally calculated indicator series as immutable Data evidence without confusing external values with calculations owned by the Indicators domain.

## Domain

data

## Provides

- `data.import-indicators@1`

## Required Capabilities

- `data.series-store@1`

## Optional Capabilities

None.

## Configuration

None.

## Runtime Effects

Each import writes one immutable provenance record through the required Data series-store capability. Mount performs no I/O and creates no background work.

## Persistent State

None. Immutable imported evidence is retained by `FEAT-DATA-MANAGE_SERIES`.

## Functional Requirements

- Pin external definition identity/version, instrument, timeframe, timezone, source artifact/hash, and alignment policy.
- Preserve explicit `EXTERNAL_INDICATOR` provenance.
- Allocate a distinct immutable version identity for every accepted import.
- Never calculate an indicator or represent imported values as Indicators-domain calculations.

## Failure Behavior

Strict public contract validation rejects malformed requests before invocation. Series-store failures propagate rather than fabricating a successful import.

## Removal Behavior

Removing the feature withdraws `data.import-indicators@1`; previously imported immutable evidence remains owned by the series-store provider.
