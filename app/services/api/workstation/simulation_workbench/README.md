# Simulation Workbench — `app/services/api/workstation/simulation_workbench/`

Feature ID: `FEAT-API-27` — Status: **Completed**.

Owns the durable principal-scoped Simulation run catalogue, typed
live-session projections, and batch coordination behind
`/api/v1/simulator`.

## Feature Registry

| Status | Feature | Module ownership | Public API | Contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|---|
| Completed | `FEAT-API-27` Simulation Workbench gateway | `schemas.py` (contracts), `migrations/` (schema), `persistence/` (CRUD), `registry.py` (coordination), `completion.py` (catalogue retention), `batching.py` (bounded batch execution), `reproduction.py` (canonical reproduction), `provenance.py` (gateway run origin), `orchestration.py` (composition), `routes.py` (HTTP) | Routes under `/api/v1/simulator`; `build_simulation_workbench_source`, `build_simulation_workbench_live_authority`, `build_simulation_workbench_registry` re-exported from `app.services.api` | `RunCatalogueEntry v1`, `BatchCreateRequest v1`, live-session projection `v1`, command discriminators | `FR-API-165`, `FR-API-167`–`FR-API-169` | `tests/api/usage/27_simulation_workbench.py`; `tests/api/unit/test_simulation_workbench_runtime.py` |

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
