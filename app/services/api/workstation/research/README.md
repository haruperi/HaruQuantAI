# Research Gateway

Focused workstation API feature. It authenticates and authorizes requests,
delegates through verified owner-domain public contracts, translates bounded
errors, and performs no owner-domain or presentation calculations.

Two features live in this folder:

- `FEAT-API-21` — the original synchronous `POST /api/v1/research/run` boundary,
  which accepts already-serialized owner contracts.
- `FEAT-API-26` — the Research Workbench Gateway: browser-safe request DTOs,
  server-owned presets, background run lifecycle, stage projections, history,
  comparison, artifacts, automation, expectancy/drift reads, and governed
  expectancy transitions.

## Files

- `routes.py`: thin FastAPI transport boundary.
- `schemas.py`: feature-local request schemas, browser-safe and legacy.
- `presets.py`: server-owned presets, approved overrides, artifact root, and
  resource ceilings. A browser never supplies any of these.
- `registry.py`: principal-scoped experiment, run, and batch lifecycle with
  ordered progress events, cooperative cancellation, and lazy recovery from
  the Research-owned durable ledger.
- `projections.py`: API-owned read models over the registered
  `ResearchReport v1`. No scientific value is recomputed here.
- `views.py`: browser-facing read models composed from run records and
  projections.
- `orchestration.py`: dependency composition — dataset resolution through Data,
  Research delegation, artifact persistence, point-in-time intelligence, and
  expectancy/drift/stress reads.

## Ownership boundaries

- Research owns every score, readiness verdict, classification, statistic, and
  warning. The gateway reshapes them and never recomputes them.
- Data owns dataset acquisition. A run request names a symbol, timeframe, and
  window; the gateway resolves the canonical `MarketDataset` server-side.
- Data owns `data_research_sources`. The intelligence view queries eligible
  records at the persisted dataset `available_at` instant and scopes them to the
  run symbol. Research alone builds and projects fundamental and deterministic
  `lexicon-v1` sentiment evidence; missing or invalid decision time and source
  coverage remain explicit unavailable states.
- The gateway owns the artifact root and the resource ceilings. Neither is
  accepted from, nor echoed back to, a browser.
- Expectancy transitions require `research:govern`, durable HTTP idempotency,
  and Research-owned lifecycle validation and atomic persistence. Drift
  suspensions remain advisory and are never enacted here.
- Run and automation-batch creation require durable HTTP idempotency before a
  job identity is queued. Reusing an identical terminal key returns the shared
  bounded `IDEMPOTENCY_CONFLICT` and never queues the owner operation twice.
- Expectancy creation binds explicit operator-supplied measurements to an owned
  completed run and persists only a draft. Stress creation accepts only a
  Research-registered scenario key. Both require `research:govern` and durable
  idempotency; neither approves evidence nor applies a shock.

## Execution model

A complete Research pass exceeds the endpoint deadline, so the run surface is a
job, following the canonical Simulator pattern: submission returns `202` with an
identity, execution happens on a worker thread, and progress is read by polling
`GET /runs/{run_id}` or by consuming the ordered SSE stream at
`GET /runs/{run_id}/events`. Cancellation is cooperative — a queued run never
starts, and a running stage sequence is marked cancelled as soon as the in-flight
Research call returns.

The run request identity includes its experiment path scope, while automation
uses the complete validated batch request. Both reserve through the shared
asynchronous API idempotency cycle before their synchronous registry mutation
runs on a worker thread.

Experiments, batches, and every queued, running, and terminal run transition are
persisted through Research's package-root boundary. Reads hydrate a principal's
ledger lazily so application startup does not load every account. Store failures
are logged and leave valid in-memory Research evidence available to the caller.

## Requirements

- `FR-API-031` (`FEAT-API-21`).
- `FR-API-157`–`FR-API-164` (`FEAT-API-26`).

## Dependencies

Shared API contracts, Identity authorization, canonical Composition, the Data
package-root public API for dataset resolution, and the Research package-root
public API.

## Evidence

- `tests/api/unit/test_research_routes.py`
- `tests/api/unit/test_research_workbench_routes.py`
- `tests/api/unit/test_route_catalog.py`
