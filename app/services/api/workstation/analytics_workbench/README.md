# Analytics Workbench — `app/services/api/workstation/analytics_workbench/`

Feature ID: `FEAT-API-28` — Status: **In Progress** (Phase 0 backend build).

Owns the read-mostly Analytics gateway behind `/api/v1/analytics`.

## Feature Registry

| Status | Feature | Module ownership | Public API | Contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|---|
| In Progress | `FEAT-API-28` Analytics Workbench gateway | `schemas.py` (contracts), `orchestration.py` (composition), `routes.py` (HTTP) | Routes under `/api/v1/analytics` (§3.6 of the work orders) | Compare/period/trade query enums (§3.6) | Work orders P0-T09, P0-T10 | Pending `tests/api/usage/28_analytics_workbench.py` |

## Persistence - Database

No Analytics tables. All durable state lives in the Simulation Workbench
catalogue (`api_simulation_results`); the serialized Analytics report is
attached as an immutable Simulation run artifact.

## Stage Notes

- Reads: `simulation:read`. Annotation/archive writes: `simulation:run`
  plus an idempotency key.
- Every metric and comparison is delegated to Analytics; the gateway
  computes nothing.
