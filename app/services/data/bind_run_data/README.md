# FEAT-DATA-BIND_RUN_DATA — Bind Run Data

## Purpose
Pin exact immutable Data versions and precision evidence to a run manifest before Simulation, Research, or Optimization begins.

## Domain
data

## Provides
- `data.bind-run-data@1`

## Required Capabilities
- `data.series-store@1`

## Optional Capabilities
None.

## Configuration
- `database_path` — feature-owned SQLite path. Default: `.haruquant/data-run-bindings.sqlite3`.

## Runtime Effects
Validation performs bounded metadata reads through `data.series-store@1`. BIND persists one immutable binding and pins its exact series versions through the store capability. Mount performs no I/O or background work.

## Persistent State
`data.run_bindings` schema version 1 is retained. It owns immutable run-to-series bindings and their requested precision evidence.

## Functional Requirements
- Refuse missing series versions before run admission.
- Require tick-shaped evidence for real-tick precision modes.
- Persist one immutable binding per run manifest.
- Pin every bound version so retention cannot collect an active historical input.
- Later imports or feature replacement never rewrite a prior binding.

## Failure Behavior
Missing versions return `DATA_NOT_FOUND`; incompatible real-tick precision returns `DATA_PRECISION_UNAVAILABLE`; immutable binding conflicts and pin failures propagate without partial success.

## Removal Behavior
Removing the feature withdraws `data.bind-run-data@1`. Retained binding evidence and series-store pins remain intact; unrelated Data ingestion/streaming capabilities remain available.
