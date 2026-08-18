# `FEAT-API-25` — Canonical Backtest Simulator Gateway

> **Owning module:** `app/services/api/workstation/simulator/`
> **Requirements:** `FR-API-151`–`FR-API-156`
> **Status:** `Completed`

## Purpose

Expose the Simulation domain's canonical backtest recipe over HTTP. The gateway
authenticates, validates a bounded operator configuration, and delegates once.
It owns no part of the backtest: no hash, provider revision, tick lineage,
strategy evaluation, or metric is produced here.

## Why runs are jobs, not requests

A canonical run over a year of bars takes minutes, far exceeding the boundary's
30-second endpoint deadline (`API_ENDPOINT_TIMEOUT_SECONDS`). Submission
therefore returns `202 Accepted` with a run identity, and progress is observed
by polling the run or consuming its ordered event stream. The run itself
executes on a worker thread owned by the Simulation domain's registry, so the
event loop stays responsive.

## What this feature composes

Two things the Simulation domain deliberately does not own:

| Composed value | Why the gateway owns it |
|---|---|
| Provider-fact loading | Reading an MT5 specification and account snapshot requires Brokers, which Simulation must not import. |
| Data runtime context | `RuntimeSettingsMiddleware` establishes Data's ContextVars per request task. A background run executes outside that task and must re-enter them. |

## Files

| File | Responsibility | Key exports |
|---|---|---|
| `routes.py` | Six thin authenticated endpoints | `router` |
| `schemas.py` | Bounded operator run configuration | `SimulatorRunRequest`, `BarTimeframe` |
| `orchestration.py` | Provider-fact loader, runtime-context factory, and run dispatcher | `build_api_backtest_registry`, `build_data_runtime_context`, `build_simulator_run_source`, `build_simulator_strategy_source` |

## Routes

| Method | Path | Permission | Side effect |
|---|---|---|---|
| `GET` | `/api/v1/simulator/strategies` | `simulation:read` | read |
| `POST` | `/api/v1/simulator/runs` | `simulation:run` | write (idempotency required) |
| `GET` | `/api/v1/simulator/runs` | `simulation:read` | read |
| `GET` | `/api/v1/simulator/runs/{run_id}` | `simulation:read` | read |
| `DELETE` | `/api/v1/simulator/runs/{run_id}` | `simulation:run` | write |
| `GET` | `/api/v1/simulator/runs/{run_id}/stream` | `simulation:read` | stream |

## Failure behaviour

- An uncomposed runtime fails every operation closed with
  `SIMULATOR_RUNTIME_UNAVAILABLE` (HTTP 503).
- An unregistered or unrunnable strategy is refused at submission with its
  declared reason (HTTP 422), before any provider is contacted.
- A run is scoped to its submitting principal; another principal's run is
  `SIMULATOR_RUN_NOT_FOUND` (HTTP 404), never a permission hint.
- A provider or evidence failure becomes a terminal `failed` run carrying its
  reason. The gateway never converts a failure into a successful report.

## Tests

`tests/api/unit/test_simulator_routes.py`; `tests/api/unit/test_route_catalog.py`;
`tests/simulator/unit/test_backtest_recipe.py`.
