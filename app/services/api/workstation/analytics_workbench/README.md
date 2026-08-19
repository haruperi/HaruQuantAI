# Analytics Workbench — `app/services/api/workstation/analytics_workbench/`

Feature ID: `FEAT-API-28` — Status: **Completed**.

Owns the read-mostly Analytics gateway behind `/api/v1/analytics`.

## Feature Registry

| Status | Feature | Module ownership | Public API | Contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|---|
| Completed | `FEAT-API-28` Analytics Workbench gateway | `schemas.py` (contracts), `orchestration.py` (composition), `routes.py` (HTTP) | Routes under `/api/v1/analytics`; `build_analytics_workbench_source`, `build_analytics_workbench_composition` re-exported from `app.services.api` | Compare/period/trade query enums | `FR-API-166`, `FR-API-170` | `tests/api/usage/28_analytics_workbench.py`; `tests/api/unit/test_analytics_workbench_routes.py` |

## Persistence - Database

No Analytics tables. All durable state lives in the Simulation Workbench
catalogue (`api_simulation_results`); the serialized Analytics report is
attached as an immutable Simulation run artifact.

## Stage Notes

- Reads: `simulation:read`. Annotation/archive writes: `simulation:run`
  plus an idempotency key.
- Every metric and comparison is delegated to Analytics; the gateway
  computes nothing.
