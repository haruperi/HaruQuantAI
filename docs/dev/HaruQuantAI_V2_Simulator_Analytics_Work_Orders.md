# Implementation Plan — Simulator and Analytics Workbenches

Source documents:

- `docs/dev/HaruQuantAI_V2_Simulator_Performance_Frontend_Implementation_Plan.md`, SHA-256 `C28E76181CF62E0D9C609BE533344A781F0559EDD2E81099D5E75E8794B0C07A`
- `AGENTS.md`, SHA-256 `45EBA7118ACA9AE80E7379E8217639A5AF593A55F3E6449BFC09D4FA2B11135B`
- `docs/PROJECT.md`, SHA-256 `2CE5C80E4E8170E446CC9571D98CC3EB7EB4FD0510956183F54706EEEE021532`
- `docs/ARCHITECTURE.md`, SHA-256 `DACEF1DDC9BD91ED6FF9C3B0088B31DD629D8F768B7999489764129369B30552`
- `docs/CHANGELOG.md`, SHA-256 `56CEF869CACF7C0696FCB2B01015F2919973938554D41E71BB13BCA6DF75E961`

Repository state: `main`, commit `a10d764cdaadd901abe8d21b333219a534e3a399`, ahead of `origin/main` by 3 commits. The source document is an owner-created untracked file and must not be modified or committed by these tasks.

Generated: 2026-08-18 | Target executor: low-reasoning coding agent

## 0. EXECUTOR OPERATING RULES

You are implementing ONE task from this plan. Follow these rules without exception.
1. Implement ONLY the current task. Do not start the next task.
2. Do not modify any file not listed in "Files to Create/Modify". If you believe another file
   must change, STOP and report it instead.
3. Use the exact names, signatures, types, paths and message strings given. Do not rename,
   reorder parameters, or "improve" the API.
4. Do not add features, options, parameters, abstractions, caching, or threading that the task
   does not explicitly request.
5. Do not add a new third-party dependency. If one seems required, STOP and report.
6. Read only the files listed in "Context to Read". Do not scan the repository.
7. Write the tests exactly as specified, then make them pass. Do not weaken, skip, xfail, or
   delete a test to make it pass.
8. Run every command in "Quality Gates" and paste the real output. Never claim a command passed
   without running it.
9. STOP CONDITIONS — stop and report instead of improvising if:
   - a gate still fails after 2 fix attempts;
   - the spec contradicts existing code;
   - a file you must modify does not exist, or already contains conflicting logic;
   - an existing signature differs from the one quoted in the task;
   - the task would require touching a file listed under "DO NOT";
   - you cannot satisfy the task without inventing an unspecified decision.
10. Finish with exactly one git commit using the message given in the task.
11. Report at the end: files changed, test results, gate output, and anything you could not do.

## 1. ENVIRONMENT & COMMANDS

Run from `C:\Users\rharu\AppDev\HaruQuantAI` unless a command starts with `cd app/ui`.

```powershell
uv sync --locked
uv run --locked ruff format <python-files>
uv run --locked ruff check <python-files>
uv run --locked mypy <python-files>
uv run --locked pytest <test-files> -q --no-cov
uv run --locked pytest -q
uv run --locked python <usage-program>

cd app/ui
npm ci
npm run typecheck
npm run lint
npm test -- <test-file>
npm test -- --run
npm run build
```

Verified baseline on 2026-08-18:

- `uv run --locked pytest -q`: 6,250 passed, 21 skipped, 1 warning, 86.54% coverage, exit 0.
- Focused API/Analytics/Simulator tests: 47 passed in 4.04 seconds.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0 with five pre-existing warnings and a Next.js `next lint` deprecation notice.
- `npm test -- --run`: 57 files and 424 tests passed; existing React `act(...)` and local-storage warnings remain.
- No baseline test failure exists.
- Existing skip count is 21; no task may increase it.

After P8-T01:

```powershell
cd app/ui
npx playwright install chromium
npm run e2e
npm run e2e:visual
```

## 2. CURRENT-STATE INVENTORY

### Ownership and layout

- `app/services/simulator/`: 19 completed features. `FEAT-SIM-02` owns live sessions; `FEAT-SIM-09` owns canonical artifacts; `FEAT-SIM-19` owns the canonical backtest recipe.
- `app/services/analytics/`: 10 completed features. It is calculation-owning but deliberately database-read-only. `FEAT-ANLT-05` exposes only summary and equity dashboard projections.
- `app/services/api/workstation/simulation/`: `FEAT-API-17`, existing synchronous run, playback, and five live-session routes under `/api/v1/simulation`.
- `app/services/api/workstation/simulator/`: `FEAT-API-25`, six canonical-job operations under `/api/v1/simulator`.
- `app/ui/src/features/simulator/`: `FEAT-UI-27`, the completed `SimulatorWidget`.
- `app/ui/src/features/research/` and `app/services/api/workstation/research/`: completed `FEAT-UI-28` and `FEAT-API-26`.
- No Simulation Workbench, Analytics Workbench, run catalogue, batch resource, typed live-session projection, or workbench projection exists.

### Existing contracts

```python
# app.services.simulator
def get_simulation_result(run_id: str, **values: object) -> object | None: ...
def create_simulation_session(run_id: str, *, request_id: str) -> StandardResponse[object]: ...
def create_live_simulation_session(
    request: object,
    dependencies: object,
    *,
    request_id: str,
    durable: bool = False,
) -> StandardResponse[object]: ...
def read_live_simulation_state(session_id: str) -> StandardResponse[object]: ...
def step_live_simulation(session_id: str, ticks: int) -> StandardResponse[object]: ...
def branch_live_simulation(
    session_id: str,
    overrides: Mapping[str, object],
) -> StandardResponse[object]: ...
def restore_live_simulation_session(
    session_id: str,
    dependencies: object,
    *,
    request_id: str,
) -> StandardResponse[object]: ...
def rearm_live_simulation_session(
    session_id: str,
    *,
    approved: bool,
    request_id: str,
) -> StandardResponse[object]: ...
async def submit_live_simulation_order(
    session_id: str,
    intent: object,
) -> StandardResponse[object]: ...
def close_live_simulation_session(session_id: str) -> StandardResponse[object]: ...
```

`SimulationResult v1` currently contains `run_id`, request/config/data hashes, engine version, status, journal and manifest references, fills, closed trades, initial balance, currency, accounting, diagnostics, and realism.

`PerformanceReport v1` contains report identity, sections, caveats, quality flags, lineage, reproducibility hashes, precision metadata, and `non_binding=True`.

`DashboardPayload v1` currently completes `summary_table` and `equity_curve`; `drawdown_chart` and `monthly_returns_table` are explicitly skipped.

The canonical job retains only a compact dictionary. It discards the full `PerformanceReport` after projecting calculated metric strings. Terminal evidence therefore cannot currently survive job-registry eviction through the job API.

The frontend `liveSessionSchema` and `simulationResultSchema` are both `z.record(z.string(), z.unknown())`.

### Existing route and client conventions

- Backend route catalogue: 138 operations in `app/services/api/contracts/catalog.py`.
- Frontend route catalogue mirrors all 138 in `app/ui/src/clients/routes.ts`.
- Authenticated writes use API idempotency; governed writes use the existing permission, CSRF, and approval machinery.
- FastAPI routers are internal. Domain package roots export standalone functions only.
- UI clients validate every response with Zod before returning it.
- Page files compose features and contain no domain calculations.

### Existing tests and examples

- Python tests: `tests/<domain>/{unit,integration,contracts,usage}/`.
- API feature usage programs: `tests/api/usage/NN_<feature>.py`.
- Analytics feature usage programs: `tests/analytics/usage/features/NN_<feature>.py`.
- UI features use component/client/contract tests instead of usage programs.
- Existing `SimulatorWidget` evidence is `SimulatorWidget.test.tsx` plus client contract tests.

### Behaviour that must remain unchanged

- Existing `/api/v1/simulation/*` and `/api/v1/simulator/runs*` contracts.
- `SimulatorWidget` run submission, progress, cancellation, compact result presentation, and tests.
- Research Workbench routes and features.
- Simulation determinism, journal immutability, playback read-only behaviour, recovery rearm gate, and advisory branch identity.
- Analytics ownership of every metric and comparison.
- The 21 credential/opt-in skips.

## 3. SHARED CONTRACTS (INTERFACE FREEZE)

### 3.1 Target package tree

```text
app/services/analytics/workbench/                 # CREATE, FEAT-ANLT-11
├── __init__.py
├── contracts.py                                  # internal immutable payload types
└── projections.py                                # owner-produced finite projections

app/services/api/workstation/simulation_workbench/ # CREATE, FEAT-API-27
├── __init__.py
├── schemas.py
├── registry.py
├── orchestration.py
├── routes.py
├── migrations/
│   ├── __init__.py
│   └── definitions.py
└── persistence/
    ├── __init__.py
    ├── create.py
    ├── read.py
    ├── update.py
    └── delete.py

app/services/api/workstation/analytics_workbench/  # CREATE, FEAT-API-28
├── __init__.py
├── schemas.py
├── orchestration.py
└── routes.py

app/ui/src/features/simulation-workbench/          # CREATE, FEAT-UI-31
app/ui/src/features/analytics-workbench/           # CREATE, FEAT-UI-32
```

### 3.2 Analytics projection

`CREATE AnalyticsWorkbenchSection`:

```python
@dataclass(frozen=True, slots=True)
class AnalyticsWorkbenchSection:
    key: str
    status: Literal["completed", "unavailable"]
    unit: str | None
    source_context: str
    sample_count: int
    reason: str | None
    truncated: bool
    total_count: int
    items: tuple[Mapping[str, object], ...]
```

`CREATE AnalyticsWorkbenchPayload`:

```python
@dataclass(frozen=True, slots=True)
class AnalyticsWorkbenchPayload:
    contract_version: Literal["v1"]
    schema_id: Literal["analytics.workbench_payload.v1"]
    payload_id: str
    report_id: str
    generated_at: datetime
    summary: AnalyticsWorkbenchSection
    equity_curve: AnalyticsWorkbenchSection
    drawdown_curve: AnalyticsWorkbenchSection
    returns_series: AnalyticsWorkbenchSection
    vami: AnalyticsWorkbenchSection
    monthly_returns: AnalyticsWorkbenchSection
    period_tables: AnalyticsWorkbenchSection
    trade_calendar: AnalyticsWorkbenchSection
    streaks: AnalyticsWorkbenchSection
    distribution: AnalyticsWorkbenchSection
    histogram: AnalyticsWorkbenchSection
    outliers: AnalyticsWorkbenchSection
    excursions: AnalyticsWorkbenchSection
    duration: AnalyticsWorkbenchSection
    grouped_performance: AnalyticsWorkbenchSection
    benchmark: AnalyticsWorkbenchSection
    costs: AnalyticsWorkbenchSection
    warnings: tuple[Mapping[str, object], ...]
    quality_flags: tuple[Mapping[str, object], ...]
    lineage: Mapping[str, object]
    truncation: tuple[Mapping[str, object], ...]
    non_binding: Literal[True] = True
```

Public Analytics export:

```python
def build_analytics_workbench_payload(
    report: object,
    simulation_result: Mapping[str, object],
    *,
    max_points: int = 5_000,
) -> StandardResponse[object]: ...
```

Rules:

- Accept only a validated `PerformanceReport` and canonical Simulation result mapping.
- Perform calculations only inside Analytics.
- Return unavailable sections with exact reason `"authoritative_evidence_unavailable"`.
- Never substitute zero for missing evidence.
- Preserve all/long/short source contexts where present.
- Maximum section items: 5,000.

### 3.3 Durable catalogue

Tables:

- `api_simulation_results`: immutable evidence references plus mutable annotations/archive state.
- `api_simulation_sessions`: principal ownership and resumable-session metadata.
- `api_simulation_batches`: group identity, status, concurrency, and counts.
- `api_simulation_batch_items`: ordered batch membership and per-job state.

No table stores calculated metrics, trade ledgers, full reports, or full Simulation results.

`RunCatalogueEntry v1` fields:

```text
run_id, principal_id, origin_kind, origin_id, job_id, batch_id, session_id,
strategy_id, strategy_version, strategy_label, symbols, timeframe,
measurement_start, measurement_end, status, result_ref, report_id, report_ref,
artifact_manifest_ref, quality_status, evidence_class, created_at, completed_at,
name, alias, description, tags, run_reason, archive_state
```

Allowed values:

```text
origin_kind = canonical_job | batch | practice | reproduction | portfolio
status = queued | running | completed | failed | cancelled
evidence_class = canonical | practice | advisory | playback | fast_research
archive_state = active | archived
```

Pagination constants:

```python
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_TRADE_PAGE_SIZE = 500
MAX_BATCH_ITEMS = 100
MAX_BATCH_CONCURRENCY = 8
MAX_TAGS = 16
MAX_TAG_LENGTH = 64
```

### 3.4 Live-session projection

`LiveSessionProjection v1` contains:

```text
contract_version="v1"
schema_id="api.live_session_projection.v1"
session_id, run_id, mode, evidence_class, cursor, timestamp, tick_count,
completed, dataset, branch, account, positions, orders, receipt,
pending_intent_count, recovery, exposure_blocked, state_hash,
state_freshness, permitted_actions
```

Nested fields:

- `dataset`: `dataset_id`, `revision`, `content_hash`.
- `branch`: `parent_session_id`, `divergence_cursor`, `overrides`.
- `account`: `currency`, `balance`, `equity`, `margin`, `free_margin`, `margin_level`.
- Position: `position_id`, `symbol`, `side`, `volume`, `open_price`, `stop_loss`, `take_profit`, `unrealized_pnl`.
- Order: `order_id`, `symbol`, `order_type`, `side`, `volume`, `price`, `stop_loss`, `take_profit`, `status`.
- Receipt: `receipt_id`, `command_type`, `status`, `reason`, `order_id`, `position_id`.
- Recovery: `status`, `persisted_state_hash`, `integrity_status`, `recovery_generation`, `recovery_run_id`, `last_checkpoint_at`.
- `state_freshness`: `fresh | stale | unknown`.

Viewport constants:

```python
DEFAULT_VIEWPORT_BEFORE = 300
MAX_VIEWPORT_BEFORE = 5_000
VIEWPORT_AFTER = 0
MAX_STEP_TICKS = 10_000
MAX_SEEK_TICKS = 100_000
```

Viewport rows contain only `timestamp`, OHLC, volume, forming flag, and visible order/fill/position markers at or before the server cursor.

### 3.5 Commands

Exact discriminators:

```text
submit_order
modify_pending_order
cancel_pending_order
close_position
reduce_position
close_all_practice_exposure
```

Every command response contains `receipt` and refreshed `session`. No command response may invent a fill.

New Simulator public operations:

```python
def list_live_simulation_sessions() -> StandardResponse[object]: ...
def seek_live_simulation(
    session_id: str,
    target_cursor: int,
) -> StandardResponse[object]: ...
def execute_live_simulation_command(
    session_id: str,
    command: object,
) -> StandardResponse[object]: ...
def finalize_live_simulation_session(
    session_id: str,
    *,
    request_id: str,
) -> StandardResponse[object]: ...
def attach_analytics_report_artifact(
    run_id: str,
    report_json: str,
    *,
    request_id: str,
) -> StandardResponse[object]: ...
```

Seek is forward-only. A target behind the current cursor fails with `"SIMULATION_SEEK_REWIND_FORBIDDEN"`; a delta above 100,000 fails with `"SIMULATION_SEEK_LIMIT_EXCEEDED"`.

### 3.6 Routes

`FEAT-API-27`:

```text
POST   /api/v1/simulator/live-sessions
GET    /api/v1/simulator/live-sessions
GET    /api/v1/simulator/live-sessions/{session_id}
GET    /api/v1/simulator/live-sessions/{session_id}/viewport
POST   /api/v1/simulator/live-sessions/{session_id}/step
POST   /api/v1/simulator/live-sessions/{session_id}/seek
POST   /api/v1/simulator/live-sessions/{session_id}/commands
POST   /api/v1/simulator/live-sessions/{session_id}/branch
POST   /api/v1/simulator/live-sessions/{session_id}/restore
POST   /api/v1/simulator/live-sessions/{session_id}/rearm
POST   /api/v1/simulator/live-sessions/{session_id}/finalize
POST   /api/v1/simulator/live-sessions/{session_id}/reproduce
DELETE /api/v1/simulator/live-sessions/{session_id}

POST   /api/v1/simulator/batches
GET    /api/v1/simulator/batches/{batch_id}
GET    /api/v1/simulator/batches/{batch_id}/stream
POST   /api/v1/simulator/batches/{batch_id}/cancel
POST   /api/v1/simulator/batches/{batch_id}/retry-failed
```

`FEAT-API-28`:

```text
GET  /api/v1/analytics/runs
GET  /api/v1/analytics/runs/{run_id}
GET  /api/v1/analytics/runs/{run_id}/simulation-result
GET  /api/v1/analytics/runs/{run_id}/report
GET  /api/v1/analytics/runs/{run_id}/workbench
GET  /api/v1/analytics/runs/{run_id}/trades
GET  /api/v1/analytics/runs/{run_id}/trades/{ticket}
GET  /api/v1/analytics/runs/{run_id}/periods
GET  /api/v1/analytics/runs/{run_id}/artifacts
GET  /api/v1/analytics/runs/{run_id}/replay-anchors
POST /api/v1/analytics/compare
POST /api/v1/analytics/runs/{run_id}/annotations
POST /api/v1/analytics/runs/{run_id}/archive
```

Permissions:

- Reads: `simulation:read`.
- Session/run/batch writes: `simulation:run`.
- Annotation/archive writes: `simulation:run`.
- Every create, retry, finalize, reproduce, annotation, and archive request requires an idempotency key.
- Restore and rearm remain separate operations.
- Unknown or foreign-owned resources return 404, never 403.

### 3.7 Public exports

Add to `app.services.analytics.__all__`:

```python
"build_analytics_workbench_payload"
```

Add to `app.services.api.__all__`:

```python
"build_analytics_workbench_source"
"build_simulation_workbench_source"
```

Add to `app.services.simulator.__all__`:

```python
"attach_analytics_report_artifact"
"execute_live_simulation_command"
"finalize_live_simulation_session"
"list_live_simulation_sessions"
"seek_live_simulation"
```

No class or constant is exported from a domain package root.

## 4. NAMING & LAYOUT CONVENTIONS

- Python modules/functions/constants: `snake_case`, `snake_case`, `UPPER_SNAKE_CASE`.
- Internal Python types: `PascalCase`; private types/functions start with `_`.
- TypeScript files: feature components `PascalCase.tsx`; clients/stores `camelCase.ts` or repository-established kebab names.
- Tests: Python `test_*.py`; UI `*.test.ts(x)`; browser `*.spec.ts`.
- Python imports are absolute. Cross-domain imports use package roots only.
- UI features export through their own `index.ts`; clients export through `src/clients/index.ts`.
- Python docstrings follow Google style and document arguments, returns, and raised exceptions.
- Library logging uses `from app.utils import get_logger`; no library `print`.
- UI component files remain composition-focused; selectors perform presentation projection only.
- Changelog policy: only P8-T02 adds the consolidated `## [Unreleased]` entries after all implementation and evidence pass. Intermediate tasks do not touch `docs/CHANGELOG.md`.

## 5. SCOPE & PROTECTED AREAS

**In scope:** `FEAT-API-27`, `FEAT-API-28`, `FEAT-UI-31`, `FEAT-UI-32`, and `FEAT-ANLT-11`; required compatible seams in `FEAT-SIM-02`, `FEAT-SIM-09`, `FEAT-SIM-19`, `FEAT-API-25`, and `FEAT-UI-27`.

**Out of scope:**

- New metric formulae absent from Analytics.
- Risk-of-ruin, SQN, Deflated Sharpe, DSR p-value, and strategy scorecards.
- Browser Monte Carlo.
- Production or live broker mutation.
- V1 modification.
- Replacing the existing chart implementation.
- Authentication, navigation-shell, or Research Workbench redesign.
- Deleting immutable run artifacts.

**PROTECTED paths — no task may modify these:**

| Path | Reason |
|---|---|
| `C:\Users\rharu\AppDev\Haruquant\` | V1 is read-only product reference |
| `docs/dev/HaruQuantAI_V2_Simulator_Performance_Frontend_Implementation_Plan.md` | Owner-created source document |
| `app/services/api/workstation/research/` | Existing `FEAT-API-26` |
| `app/ui/src/features/research/` | Existing `FEAT-UI-28` |
| `app/services/analytics/dashboards/` | Existing `FEAT-ANLT-05`; new work belongs in `workbench/` |
| `app/services/api/workstation/simulation/` | Existing routes remain unchanged |
| Applied migration steps | Immutable ledger checksums |

Permitted narrow changes:

- `app/services/api/workstation/simulator/orchestration.py`: completion-sink parameter only.
- `app/ui/src/features/simulator/SimulatorWidget.tsx`: canonical Analytics handoff link only.
- Simulator state/reporting/backtest-recipe files explicitly listed in tasks.

**Forbidden changes (repo-wide, apply to every task):**

- No unrelated refactoring or cleanup.
- No unlisted public API change.
- No unlisted dependency.
- No weakening, skipping, xfailing, or deleting tests.
- No lint/type suppression unless a task names the exact line and reason.
- No placeholder, `TODO`, or `FIXME`.
- No secrets or local configuration.
- No live broker call.
- No client-side metric, fill, cursor, or canonical-status calculation.

## 6. DEPENDENCY AUTHORIZATION

| Package | Version constraint | Runtime/Dev | Justification | Task | Files | Command |
|---|---:|---|---|---|---|---|
| `@playwright/test` | `1.61.1` | Dev | Required for the accepted real-browser journeys and screenshot comparisons; existing Vitest/jsdom cannot prove routing, SSE reconnection, focus restoration, or visual snapshots. The official package provides the test runner and screenshot assertions. [Installation](https://playwright.dev/docs/intro), [visual comparisons](https://playwright.dev/docs/test-snapshots), [version](https://www.npmjs.com/package/%40playwright/test) | P8-T01 | `app/ui/package.json`, `app/ui/package-lock.json` | `npm install --save-dev --save-exact @playwright/test@1.61.1` |

No production dependency is authorized.

## 7. SOURCE CONFLICTS

### CF-01 — Live-session route family

Sources: approved source §§3.4, 11.2 versus existing `FEAT-API-17`.

Claim A: existing operations use `/api/v1/simulation/live-sessions`.

Claim B: the new workbench contract requires `/api/v1/simulator/live-sessions`.

Precedence: approved source design, while preserving existing public contracts.

Decision: add the typed `/api/v1/simulator/live-sessions` workbench family under `FEAT-API-27`; do not change or remove `/api/v1/simulation/live-sessions`.

Affected tasks: P0-T08, P0-T10, P1-T01.

### CF-02 — Analytics feature placement

Sources: source §5 versus `AGENTS.md` focused-feature rule.

Claim A: extend `FEAT-ANLT-05` or register `FEAT-ANLT-11`.

Claim B: one capability must own one module folder and one usage program.

Precedence: source permits either; repository architecture selects the focused option.

Decision: register `FEAT-ANLT-11` in `app/services/analytics/workbench/`; leave `FEAT-ANLT-05` unchanged.

Affected tasks: P0-T04, P0-T11.

### CF-03 — Durable Analytics evidence

Sources: source §11.2.I versus `docs/ARCHITECTURE.md`.

Claim A: Analytics needs durable run/report discovery.

Claim B: Analytics is database-read-only.

Precedence: both are satisfied.

Decision: API persists only principal-scoped catalogue metadata and immutable owner references. The serialized Analytics report is attached as an immutable Simulation run artifact. No Analytics table is created.

Affected tasks: P0-T03, P0-T05–P0-T09.

### CF-04 — Proposed UI folder

Sources: source §12 versus existing `FEAT-UI-27`.

Claim A: place the broad workbench in `features/simulator/`.

Claim B: `features/simulator/` already owns `FEAT-UI-27`; one feature cannot share an owning folder.

Decision: create `features/simulation-workbench/` for `FEAT-UI-31`; embed the existing widget through its barrel.

Affected tasks: P1-T02 onward.

### CF-05 — FEAT-UI-29/30 ordinals

Sources: this plan's interface freeze versus concurrent owner work registering
`FEAT-UI-29` as the Articles Online News Widget (uncommitted
`app/ui/src/features/articles/`).

Claim A: this plan froze `FEAT-UI-29` (Simulation Workbench UI) and
`FEAT-UI-30` (Analytics Workbench UI).

Claim B: the owner's concurrent work already occupies `FEAT-UI-29`.

Precedence: owner-created concurrent work; the plan renumbers rather than
editing in-flight owner files.

Decision: the workbench UI features are renumbered to `FEAT-UI-31`
(Simulation Workbench shell, formerly `FEAT-UI-29`) and `FEAT-UI-32`
(Analytics Workbench shell, formerly `FEAT-UI-30`). Every other frozen
name, route, contract, and export is unchanged.

Affected tasks: P1-T01 through P8-T02 (UI feature references only).

## 8. OPEN QUESTIONS (BLOCKING)

None.

## 9. PLANNER OBSERVATIONS (NON-BLOCKING)

- The source contains feature IDs but no new `FR-*` identifiers. Tasks therefore trace to the exact source feature IDs and do not invent FR identifiers.
- The Next 15 `next lint` command is deprecated but currently passes. Migrating ESLint invocation is not required by this plan.
- Existing React `act(...)`, local-storage, and Starlette deprecation warnings are baseline noise. New tests must introduce no additional warning class.
- `FEAT-API-26`, `FEAT-UI-28`, `FEAT-ANLT-05`, and `FEAT-UI-27` are already registered and cannot be reassigned.
- `FEAT-API-27`, `FEAT-API-28`, `FEAT-UI-31`, `FEAT-UI-32`, and `FEAT-ANLT-11` are free at the inspected commit.

## 10. PROGRESS DASHBOARD

- [x] Phase 0 — P0-T01 through P0-T11
- [ ] Phase 1 — P1-T01 through P1-T06
- [ ] Phase 2 — P2-T01 through P2-T02
- [ ] Phase 3 — P3-T01 through P3-T04
- [ ] Phase 4 — P4-T01 through P4-T05
- [ ] Phase 5 — P5-T01
- [ ] Phase 6 — P6-T01 through P6-T03
- [ ] Phase 7 — P7-T01 through P7-T02
- [ ] Phase 8 — P8-T01 through P8-T02

## 11. PHASES

### Phase 0 — Contract and read-model readiness

**Goal:** Make canonical, interactive, and analytical evidence durably addressable through typed contracts.

**Why now:** Every UI phase depends on stable owner projections and routes.

**Deliverable:** Registered backend capabilities with migrations, catalogue, full report artifact, workbench projection, route catalogue, and usage evidence.

#### - [x] Task `P0-T01` — Record workbench baseline

**Traces to:** `FEAT-API-27`, `FEAT-API-28`, `FEAT-UI-31`, `FEAT-UI-32`, `FEAT-ANLT-11`
**Depends on:** none
**Estimated size:** S (<50 LOC)

**Goal.** Record the verified pre-change state so later failures can be classified.

**Context to Read (and nothing else):** `pyproject.toml`, `app/ui/package.json`, Shared Contracts §3.

**Files to Create/Modify:** `docs/dev/baselines/simulator_analytics_workbench.md` (CREATE).

**Specification.** Record the exact baseline values from §1 and state that the source document is untracked owner material.

**Behaviour Rules:** Do not run live integration; do not call warnings failures; record 6,250/21/86.54% and 424 UI tests exactly.

**Implementation Steps:** Create the baseline file; include commands/exit codes; include protected paths and rollback.

**DO NOT:** Modify source/tests, add coverage output, or touch a PROTECTED path.

**Unit Tests:** No new unit test; re-run both complete baseline suites.

**Usage Example:** The baseline file is the execution record.

**Quality Gates:** `uv run --locked pytest -q`; UI typecheck, lint, and full tests.

**Documentation Updates:** Only the baseline file.

**Git Commit:** `chore(workbench): record implementation baseline`

**Re-run safety:** Safe only when commit/hash and real output match.

#### - [x] Task `P0-T02` — Retain canonical evidence

**Traces to:** `FEAT-API-27`, `FEAT-API-28`
**Depends on:** P0-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Retain the exact `SimulationResult`, `PerformanceReport`, and compact projection until the API completion sink persists their references.

**Context to Read:** `backtest_recipe/pipeline.py`, `backtest_recipe/jobs.py`, Shared Contracts §§3.2–3.3.

**Files:** `backtest_recipe/evidence.py` CREATE; `pipeline.py` MODIFY; `jobs.py` MODIFY.

**Specification:** Create frozen `BacktestRunEvidence(projection, simulation_result, performance_report)` and optional `CompletionSink`. Existing snapshots remain compact.

**Behaviour Rules:** Sink once after both owners succeed; sink failure becomes `BACKTEST_EVIDENCE_PERSISTENCE_FAILED`; cancellation skips sink; no full object enters HTTP snapshot.

**Unit Tests:** Completion once, sink failure, cancelled job.

**Regression Tests:** `tests/simulator/unit/test_backtest_recipe.py`.

**Usage Example:** Existing official FX backtest workflow.

**Logging:** Sink start/success/failure without payloads.

**Quality Gates:** Ruff, mypy, targeted pytest.

**Documentation Updates:** Deferred to P0-T11.

**Git Commit:** `feat(simulator): retain complete backtest evidence`

**Re-run safety:** Safe; sink is once per job.

#### - [x] Task `P0-T03` — Attach Analytics report artifact

**Traces to:** `FEAT-API-27`, `FEAT-API-28`
**Depends on:** P0-T02
**Estimated size:** M (50–120 LOC)

**Files:** `reporting/artifacts.py`, `reporting/contracts.py`, `app/services/simulator/__init__.py` (MODIFY).

**Specification:** Atomically attach immutable `analytics-report.json`; preserve the three existing artifact entries.

**Behaviour Rules:** Exact failures `SIMULATION_RESULT_NOT_FOUND`, `ANALYTICS_REPORT_INVALID`, `ANALYTICS_REPORT_CONFLICT`; identical bytes idempotent.

**Unit Tests:** Absent run, invalid JSON, first write, identical write, conflict.

**Usage Example:** Update `tests/simulator/usage/features/09_reporting.py`.

**Logging:** Run ID and content hash only.

**Rollback:** Revert code; retain written artifacts.

**Quality Gates:** Ruff, mypy, targeted pytest, direct usage execution.

**Git Commit:** `feat(simulator): attach Analytics report artifact`

**Re-run safety:** Safe for identical content.

#### - [x] Task `P0-T04` — Build Analytics projection

**Traces to:** `FEAT-ANLT-11`
**Depends on:** P0-T02
**Estimated size:** L

**Files:** `analytics/workbench/contracts.py` CREATE; `projections.py` CREATE; `analytics/__init__.py` MODIFY.

**Specification:** Implement §3.2 exactly with 18 stable sections, independent 5,000-item bounds, Decimal preservation, unavailable reasons, and no persistence.

**Unit Tests:** Deterministic two-trade input, drawdown, monthly periods, truncation, unavailable evidence, contexts.

**Usage Example:** Create `tests/analytics/usage/features/11_workbench.py`.

**Logging:** Report ID, section status, counts only.

**Quality Gates:** Ruff, mypy, targeted pytest, usage execution.

**Git Commit:** `feat(analytics): add workbench projection`

**Re-run safety:** Pure and deterministic.

#### - [x] Task `P0-T05` — Create workbench schema

**Traces to:** `FEAT-API-27`
**Depends on:** P0-T01
**Estimated size:** L

**Files:** `simulation_workbench/schemas.py`, `migrations/__init__.py`, `migrations/definitions.py` (CREATE).

**Specification:** Frozen extra-forbid DTOs and four additive API tables from §§3.3–3.5.

**Behaviour Rules:** Bound every identifier/collection; viewport `after=0`; immutable migration IDs/checksums; `api_` prefixes and required timestamps.

**Unit Tests:** Contract validation and migration structure/checksum tests.

**Usage Example:** P0-T08 owns the feature usage program.

**Rollback:** Never drop applied tables.

**Quality Gates:** Ruff, mypy, targeted tests.

**Git Commit:** `feat(api): define Simulation workbench contracts`

**Re-run safety:** Ledger makes apply idempotent.

#### - [x] Task `P0-T06` — Implement catalogue persistence

**Traces to:** `FEAT-API-27`
**Depends on:** P0-T05
**Estimated size:** L

**Files:** `persistence/__init__.py`, `persistence/create.py`, `persistence/read.py` (CREATE).

**Specification:** Build statements and delegate through `app.services.data`.

**Behaviour Rules:** Filter every read by principal; immutable evidence references; `(created_at, run_id)` descending cursor; no calculated-payload columns.

**Unit Tests:** SQL parameters, ownership, pagination, duplicate identity.

**Logging:** Operation, safe trace, row count.

**Rollback:** Preserve rows/tables.

**Quality Gates:** Ruff, mypy, targeted tests.

**Git Commit:** `feat(api): persist Simulation workbench catalogue`

**Re-run safety:** Identity-idempotent inserts.

#### - [x] Task `P0-T07` — Implement workbench registry

**Traces to:** `FEAT-API-27`
**Depends on:** P0-T06
**Estimated size:** L

**Files:** `persistence/update.py`, `persistence/delete.py`, `registry.py` (CREATE).

**Behaviour Rules:** Batch 1–100/concurrency 1–8; cancel non-terminal jobs once; retry failed only; attach report before completion; archive never deletes; delete module has empty `__all__`.

**Unit Tests:** Fixed clock, partial failure, cancellation, retry, completion conflict, ownership.

**Logging:** Transitions and counts only.

**Rollback:** Preserve catalogue/artifacts.

**Git Commit:** `feat(api): coordinate Simulation workbench resources`

**Re-run safety:** Idempotency prevents duplicates.

#### - [x] Task `P0-T08` — Expose Simulation gateway

**Traces to:** `FEAT-API-27`
**Depends on:** P0-T03, P0-T07
**Estimated size:** L

**Files:** `simulation_workbench/__init__.py`, `orchestration.py`, `routes.py` (CREATE).

**Behaviour Rules:** Authorize before access; foreign resources 404; reject future viewport; receipt plus refreshed state; finalize stays advisory; reproduce creates separate job.

**Unit Tests:** Auth, ownership, viewport, commands, finalize/reproduce, batch.

**Usage Example:** `tests/api/usage/27_simulation_workbench.py`.

**Logging:** Route, resource, transition, error code.

**Quality Gates:** Ruff, mypy, route tests, direct usage.

**Git Commit:** `feat(api): expose Simulation workbench gateway`

**Re-run safety:** Safe under idempotency.

#### - [x] Task `P0-T09` — Expose Analytics gateway

**Traces to:** `FEAT-API-28`
**Depends on:** P0-T04, P0-T07
**Estimated size:** L

**Files:** `analytics_workbench/schemas.py`, `orchestration.py`, `routes.py` (CREATE).

**Behaviour Rules:** Read attached report; delegate projection once; paginate Simulation trades; delegate comparison; exact period query enums; annotation/archive affect metadata only.

**Unit Tests:** Pagination, missing evidence, trade detail, comparison, annotations, archive.

**Usage Example:** `tests/api/usage/28_analytics_workbench.py`.

**Logging:** Run ID, page count, action, state.

**Quality Gates:** Ruff, mypy, route tests, direct usage.

**Git Commit:** `feat(api): expose Analytics workbench gateway`

**Re-run safety:** Reads safe; writes idempotent.

#### - [x] Task `P0-T10` — Compose workbench routes

**Traces to:** `FEAT-API-27`, `FEAT-API-28`
**Depends on:** P0-T08, P0-T09
**Estimated size:** M

**Files:** `api/contracts/catalog.py`, `composition/application.py`, `composition/migrations.py` (MODIFY).

**Behaviour Rules:** Route IDs `api.simulator.workbench.*` and `api.analytics.workbench.*`; count 138→170; preserve provider/router order; migration failure leaves readiness false.

**Unit Tests:** Route catalogue, application, composition, migrations, OpenAPI snapshot.

**Rollback:** Revert code; retain additive tables.

**Quality Gates:** Ruff, mypy, API contract tests.

**Git Commit:** `feat(api): compose workbench routes`

**Re-run safety:** Deterministic registration.

#### - [ ] Task `P0-T11` — Register backend capabilities

**Traces to:** `FEAT-ANLT-11`, `FEAT-API-27`, `FEAT-API-28`
**Depends on:** P0-T10
**Estimated size:** S

**Files:** API, Analytics, and Simulator owning READMEs (MODIFY).

**Unit Tests:** Structural registry and usage-parity tests.

**Usage Example:** Run API 27/28, Analytics 11, Simulator 09 programs.

**Git Commit:** `docs(workbench): register backend capabilities`

**Re-run safety:** Update exact registry rows; do not duplicate them.

**Phase Exit Gate:** `uv run --locked pytest tests/api tests/analytics tests/simulator -q`; no added skips; report survives forced job eviction.

### Phase 1 — Route shells and workspace handoff

**Goal:** Deliver refresh-safe Simulator and Analytics routes.

**Why now:** Typed backend contracts are available.

**Deliverable:** Two runnable workspaces with canonical/advisory status and existing widget preservation.

#### - [ ] Task `P1-T01` — Add typed workbench clients

**Traces to:** `FEAT-UI-31`, `FEAT-UI-32`
**Depends on:** P0-T10
**Estimated size:** L

**Files:** `clients/routes.ts` MODIFY; `simulationWorkbench.ts` CREATE; `analyticsWorkbench.ts` CREATE.

Use strict Zod objects; no generic top-level record. Mirror 170 routes.

Tests: malformed response, permissions, idempotency, cursors, encoding.

Usage Example: UI verification exception; tests are evidence.

Quality Gates: typecheck, lint, targeted tests.

Git Commit: `feat(ui): add typed workbench clients`

Re-run safety: Stateless.

#### - [ ] Task `P1-T02` — Build Simulation shell

**Files:** `SimulationWorkbench.tsx`, `SimulationStatusBadge.tsx`, `index.ts` (CREATE).

Render exact status badges, embed `SimulatorWidget` for canonical mode, and distinguish loading/empty/stale/unavailable/error.

Tests: every state and non-colour badge text.

Git Commit: `feat(ui): build Simulation workbench shell`

#### - [ ] Task `P1-T03` — Add Simulator routes

**Files:** simulator root page MODIFY; `new/page.tsx` CREATE; `[...segments]/page.tsx` CREATE.

Resolve home/new/runs/sessions/replay and call `notFound()` for unknown shapes.

Tests: exact paths, refresh identity, invalid path, protected layout.

Git Commit: `feat(ui): add Simulator workspace routes`

#### - [ ] Task `P1-T04` — Build Analytics shell

**Files:** `AnalyticsWorkspace.tsx`, `AnalyticsNav.tsx`, `index.ts` (CREATE).

Route props exclusively own run ID/section. Render the ten section links.

Tests: selected route, unavailable section, keyboard navigation, evidence badge.

Git Commit: `feat(ui): build Analytics workbench shell`

#### - [ ] Task `P1-T05` — Add Analytics routes

**Files:** analytics root page, compare page, `[runId]/[[...segments]]/page.tsx` (CREATE).

Resolve overview, ten sections, and `trades/{ticket}`; unknown shapes call `notFound()`.

Git Commit: `feat(ui): add Analytics workspace routes`

#### - [ ] Task `P1-T06` — Link canonical Analytics

**Files:** `SimulatorWidget.tsx`, its test, and `app/ui/README.md` (MODIFY).

Add `/workstation/analytics/{run_id}/overview` only after canonical success. Register UI29/30 as Partial.

Git Commit: `feat(ui): link canonical Analytics handoff`

**Phase Exit Gate:** UI build and all tests pass.

### Phase 2 — Canonical batch end to end

#### - [ ] Task `P2-T01` — Build canonical run views

**Files:** `SimulationHome.tsx`, `SimulationRunBuilder.tsx`, `CanonicalRunMonitor.tsx` (CREATE).

Implement eight builder stages, exact request defaults, ordered SSE, reconnect, cancel, and handoff. Never supply internal hashes.

Tests: mode, parameters, validation, idempotency, ordered progress, disconnect-not-success.

Git Commit: `feat(ui): build canonical run workflow`

#### - [ ] Task `P2-T02` — Build batch monitor

**Files:** `BatchRunMonitor.tsx`, `simulation-store.ts`, `simulation-selectors.ts` (CREATE).

Store drafts/display state only. Test partial failure, cancellation, retry-failed, compare-successful, and no portfolio inference.

Git Commit: `feat(ui): build batch run monitor`

**Phase Exit Gate:** Real FastAPI partial-failure batch opens a successful Analytics route.

### Phase 3 — Analytics MVP

#### - [ ] Task `P3-T01` — Build library overview

**Files:** `AnalyticsLibrary.tsx`, `OverviewPanel.tsx`, `AnalyticsEvidenceState.tsx` (CREATE).

Render source §§14.1–14.2 only from server fields. Test pagination, archive, unavailable metrics, units, flags, caveats, contexts.

Git Commit: `feat(ui): build Analytics library overview`

#### - [ ] Task `P3-T02` — Build trade analysis

**Files:** `TradesPanel.tsx`, `TradeDetailPanel.tsx`, `AnalyticsArtifactDrawer.tsx` (CREATE).

Use server pagination/filters. Replay URL carries exact encoded return context.

Git Commit: `feat(ui): build Analytics trade analysis`

#### - [ ] Task `P3-T03` — Build Analytics charts

**Files:** `TimeSeriesChart.tsx`, `CalendarHeatmap.tsx`, `DistributionChart.tsx` (CREATE).

Render owner series only; expose unit, count, truncation, unavailable reason, and table alternative.

Git Commit: `feat(ui): build Analytics chart primitives`

#### - [ ] Task `P3-T04` — Build evidence context

**Files:** `RealismPanel.tsx`, `ProvenancePanel.tsx` (CREATE).

Render source §§14.10–14.11 including exact hashes, assumptions, limitations, diagnostics, and manifest metadata.

Git Commit: `feat(ui): build Analytics evidence context`

**Phase Exit Gate:** Canonical run → Overview → Trade Detail passes against real FastAPI.

### Phase 4 — Interactive visual and manual simulation

#### - [ ] Task `P4-T01` — Extend live-session authority

**Files:** Simulator live-session implementation, state barrel, package root (MODIFY).

Implement §3.5 operations through Trading-owned intents. Finalization seals advisory journal.

Tests: list, seek bounds, command discriminators, receipt truth, finalization, post-finalization rejection.

Rollback: New actions disappear; existing records remain readable.

Git Commit: `feat(simulator): extend live-session authority`

#### - [ ] Task `P4-T02` — Complete session routes

**Files:** simulation-workbench schemas, orchestration, routes (MODIFY).

Wire all session routes. Reproduction creates a distinct canonical job only after finalized evidence validation.

Git Commit: `feat(api): complete interactive session routes`

#### - [ ] Task `P4-T03` — Build interactive workspace

**Files:** `InteractiveSimulationWorkspace.tsx`, `SimulationSessionHeader.tsx`, `MarketViewport.tsx` (CREATE).

Pause stops scheduler; visibility loss pauses; reconnect reads first; failures never advance cursor.

Git Commit: `feat(ui): build interactive Simulation workspace`

#### - [ ] Task `P4-T04` — Build manual command panels

**Files:** `ManualCommandPanel.tsx`, `SessionStatePanels.tsx`, `WhatIfPanel.tsx` (CREATE).

Render authoritative state and receipts; never optimistically mutate or invent fills.

Git Commit: `feat(ui): build manual Simulation controls`

#### - [ ] Task `P4-T05` — Build recovery finalization

**Files:** `SimulationRecoveryPanel.tsx`, `SimulationFinalizeDialog.tsx` (CREATE).

Implement restore→verify→rearm and session-class-specific actions. Integrity failure disables rearm.

Git Commit: `feat(ui): build recovery finalization flow`

**Phase Exit Gate:** Practice restore/rearm and manual receipt/close integrations pass.

### Phase 5 — Replay and round-trip review

#### - [ ] Task `P5-T01` — Build immutable playback

**Files:** `SimulationPlaybackWorkspace.tsx` CREATE; playback client MODIFY; simulator catch-all page MODIFY.

Use ordered journal SSE, `Last-Event-ID`, trade anchor, hashes, reconstructed read-only state, and exact return URL. Never show an order ticket.

Git Commit: `feat(ui): build immutable trade playback`

**Phase Exit Gate:** Trade Detail → Replay → Return passes.

### Phase 6 — Advanced Analytics parity

#### - [ ] Task `P6-T01` — Build returns risk statistics

**Files:** `ReturnsPanel.tsx`, `RiskPanel.tsx`, `DistributionPanel.tsx` (CREATE).

Unsupported metrics render exactly `Not available in the current authoritative V2 metric catalogue.`

Git Commit: `feat(ui): build advanced Analytics evidence`

#### - [ ] Task `P6-T02` — Build period benchmark views

**Files:** `PeriodsPanel.tsx`, `BenchmarkPanel.tsx`, `ChartsPanel.tsx` (CREATE).

Encode all period dimensions in query parameters; do not duplicate routes.

Git Commit: `feat(ui): build period benchmark views`

#### - [ ] Task `P6-T03` — Build run comparison

**Files:** `AnalyticsComparison.tsx`, `analytics-store.ts`, `analytics-selectors.ts` (CREATE).

Store selected IDs/presentation only; render owner comparison without arbitrary JSON subtraction.

Git Commit: `feat(ui): build Analytics run comparison`

**Phase Exit Gate:** Every substantive V1 Performance destination has component evidence.

### Phase 7 — V2-only operational depth

#### - [ ] Task `P7-T01` — Build scenario mission panels

**Files:** scenario, checklist, and mission panels (CREATE).

Render owner catalogue, faults, emergency steps, assistance, completion, and qualification links.

Git Commit: `feat(ui): build scenario mission panels`

#### - [ ] Task `P7-T02` — Build portfolio destination

**Files:** `PortfolioSimulationPanel.tsx` CREATE; run builder and overview MODIFY.

Require explicit portfolio components, weights, risk budgets, window, currency, and FX evidence. Never infer portfolio from multi-symbol batch.

Git Commit: `feat(ui): add portfolio Simulation destination`

**Phase Exit Gate:** V2-only scenario, recovery, lineage, emergency, qualification, and portfolio evidence passes.

### Phase 8 — Hardening

#### - [ ] Task `P8-T01` — Install browser test runner

**Files:** `package.json`, `package-lock.json` MODIFY; `playwright.config.ts` CREATE.

Install exact `@playwright/test@1.61.1`; add `e2e` and `e2e:visual`; Chromium only; trace first retry; committed snapshots.

Create all ten source §18.4 browser journeys with fixed fixtures/clock and no live provider.

Rollback: Revert package/config; optional `npx playwright uninstall` for local cache.

Git Commit: `test(ui): add workbench browser coverage`

#### - [ ] Task `P8-T02` — Publish completed workbenches

**Files:** `app/ui/README.md`, `docs/PROJECT.md`, `docs/CHANGELOG.md` (MODIFY).

Mark UI29/30 Completed with exact evidence; index the handoff; add concise Unreleased entries. If backend registry statuses still need modification, STOP for scope delta.

Quality Gates: full Ruff, mypy, Python, UI, build, Playwright, visual tests.

Git Commit: `docs(workbench): publish completed Simulation Analytics journey`

**Phase Exit Gate:** All commands exit 0; Python skips remain 21; routes match 170; no new warning class.

## 12. TRACEABILITY MAP

| Requirement ID | Tasks |
|---|---|
| `FEAT-ANLT-05` | Protected existing dependency; P0-T04 proves no modification |
| `FEAT-ANLT-11` | P0-T04, P0-T11, P8-T02 |
| `FEAT-API-26` | Protected reserved ordinal; no implementation task |
| `FEAT-API-27` | P0-T02–P0-T03, P0-T05–P0-T08, P0-T10–P0-T11, P4-T01–P4-T02 |
| `FEAT-API-28` | P0-T02–P0-T04, P0-T07, P0-T09–P0-T11 |
| `FEAT-UI-27` | P1-T02, P1-T06 |
| `FEAT-UI-28` | Protected reserved ordinal; no implementation task |
| `FEAT-UI-31` | P1-T01–P1-T03, P1-T06, P2-T01–P2-T02, P4-T03–P5-T01, P7-T01–P8-T02 |
| `FEAT-UI-32` | P1-T01, P1-T04–P1-T06, P3-T01–P3-T04, P5-T01, P6-T01–P8-T02 |

## 13. COMMIT SEQUENCE

| Order | Task | Commit message |
|---:|---|---|
| 1 | P0-T01 | `chore(workbench): record implementation baseline` |
| 2 | P0-T02 | `feat(simulator): retain complete backtest evidence` |
| 3 | P0-T03 | `feat(simulator): attach Analytics report artifact` |
| 4 | P0-T04 | `feat(analytics): add workbench projection` |
| 5 | P0-T05 | `feat(api): define Simulation workbench contracts` |
| 6 | P0-T06 | `feat(api): persist Simulation workbench catalogue` |
| 7 | P0-T07 | `feat(api): coordinate Simulation workbench resources` |
| 8 | P0-T08 | `feat(api): expose Simulation workbench gateway` |
| 9 | P0-T09 | `feat(api): expose Analytics workbench gateway` |
| 10 | P0-T10 | `feat(api): compose workbench routes` |
| 11 | P0-T11 | `docs(workbench): register backend capabilities` |
| 12 | P1-T01 | `feat(ui): add typed workbench clients` |
| 13 | P1-T02 | `feat(ui): build Simulation workbench shell` |
| 14 | P1-T03 | `feat(ui): add Simulator workspace routes` |
| 15 | P1-T04 | `feat(ui): build Analytics workbench shell` |
| 16 | P1-T05 | `feat(ui): add Analytics workspace routes` |
| 17 | P1-T06 | `feat(ui): link canonical Analytics handoff` |
| 18 | P2-T01 | `feat(ui): build canonical run workflow` |
| 19 | P2-T02 | `feat(ui): build batch run monitor` |
| 20 | P3-T01 | `feat(ui): build Analytics library overview` |
| 21 | P3-T02 | `feat(ui): build Analytics trade analysis` |
| 22 | P3-T03 | `feat(ui): build Analytics chart primitives` |
| 23 | P3-T04 | `feat(ui): build Analytics evidence context` |
| 24 | P4-T01 | `feat(simulator): extend live-session authority` |
| 25 | P4-T02 | `feat(api): complete interactive session routes` |
| 26 | P4-T03 | `feat(ui): build interactive Simulation workspace` |
| 27 | P4-T04 | `feat(ui): build manual Simulation controls` |
| 28 | P4-T05 | `feat(ui): build recovery finalization flow` |
| 29 | P5-T01 | `feat(ui): build immutable trade playback` |
| 30 | P6-T01 | `feat(ui): build advanced Analytics evidence` |
| 31 | P6-T02 | `feat(ui): build period benchmark views` |
| 32 | P6-T03 | `feat(ui): build Analytics run comparison` |
| 33 | P7-T01 | `feat(ui): build scenario mission panels` |
| 34 | P7-T02 | `feat(ui): add portfolio Simulation destination` |
| 35 | P8-T01 | `test(ui): add workbench browser coverage` |
| 36 | P8-T02 | `docs(workbench): publish completed Simulation Analytics journey` |

## 14. RISK REGISTER

| Risk | Effect | Mitigation |
|---|---|---|
| Full report is discarded before persistence | Analytics routes fail after job eviction | P0-T02 and P0-T03 |
| API stores calculated evidence | Violates Analytics ownership/read-only model | P0-T05–P0-T07 permit references only |
| New routes break existing clients | Backward incompatibility | P0-T10 preserves old routes; contract drift tests |
| Session ownership leaks | Cross-principal evidence exposure | Principal-scoped reads and 404 |
| Viewport exposes future data | Invalid interactive simulation | P4-T02 future-row rejection |
| Browser advances cursor locally | State divergence | P4-T03 reconciles every response |
| Practice result appears canonical | Unsafe evidence classification | Frozen classes and badge tests |
| Report attachment conflicts | Silent artifact mutation | P0-T03 fails on different bytes |
| Batch retry duplicates successful jobs | Extra execution | Retry failed items only under idempotency |
| Charts recompute metrics | Competing Analytics engine | Owner projection and UI tests |
| Large ledgers exhaust browser | UI freeze | Pagination, 5,000-point caps, bounded tables |
| Screenshot instability | Noisy CI | Chromium-only fixed viewport/clock/fonts/fixtures |
| New dependency drifts | Reproducibility loss | Exact lock and committed lockfile |
| Migration rollback loses data | Catalogue loss | Additive forward-only tables; no drop task |
| Existing warnings obscure regressions | False green | Baseline warning classes; no new class |

## SELF-VERIFICATION REPORT

Checks 1–16: PASS. Shared contracts freeze all cross-task names, fields, limits, routes, errors, ownership, and public exports. Tasks are dependency-ordered, touch at most three production/documentation files each excluding tests and usage evidence, and contain no unresolved placeholder.

Tasks: 36 across 9 phases
Requirements covered: 9/9
Unconfirmed requirement IDs: none
Material conflicts resolved: 4 | Blocking open questions: 0
New dependencies authorized: 1
