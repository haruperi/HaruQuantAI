# Simulation Workbench — `app/services/api/workstation/simulation_workbench/`

Feature ID: `FEAT-API-27` — Status: **In Progress** (Phase 0 backend build).

Owns the durable principal-scoped Simulation run catalogue, typed
live-session projections, and batch coordination behind
`/api/v1/simulator`.

## Feature Registry

| Status | Feature | Module ownership | Public API | Contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|---|
| In Progress | `FEAT-API-27` Simulation Workbench gateway | `schemas.py` (contracts), `migrations/` (schema), `persistence/` (CRUD), `registry.py` (coordination), `orchestration.py` (composition), `routes.py` (HTTP) | Routes under `/api/v1/simulator` (P0-T08) | `RunCatalogueEntry v1`, live-session projection `v1`, command discriminators (§3.3–3.5 of the work orders) | Work orders P0-T05–P0-T08, P4-T01–P4-T02 | Pending `tests/api/usage/27_simulation_workbench.py` |

## Persistence - Database

Target model (migration `api-0011`, additive and forward-only):

- `api_simulation_results`: immutable evidence references plus mutable
  annotations/archive state, principal-scoped, `(created_at, run_id)`
  descending index.
- `api_simulation_sessions`: principal ownership and resumable-session
  metadata.
- `api_simulation_batches`: group identity, status, concurrency, counts.
- `api_simulation_batch_items`: ordered batch membership and per-job state.

No table stores calculated metrics, trade ledgers, full reports, or full
Simulation results.

## Stage Notes

- P0-T05 delivered frozen contracts and migration definitions.
- Persistence, registry, and route handlers land in P0-T06–P0-T08.
