# D-IFACE + D-UI Composability Migration — Phase 0 Baseline and Architecture Reconciliation

> **Scope:** Phase 0 audit and decision record for re-establishing the backend
> boundary for `app/ui` as capability-aware D-IFACE features under
> `app/services/interfaces/`, and migrating UI widgets to the D-UI feature model
> defined by `docs/dev/feature_implementation_pipeline.md` §4.8.
> **Status:** Completed — documentation-only. **No production code changed.**
> **Recorded:** 2026-09-03. Baseline: clean `main` at `325f3015`.

---

## 1. Task 0.3 decision record (ratified before production migration)

These decisions unblock Phases 1–5. They were taken because the repository's
documentation and the newer feature pipeline disagreed.

| ID | Decision | Rationale |
| --- | --- | --- |
| D1 | **Keep the existing `FEAT-UI-01`…`FEAT-UI-32` numeric feature IDs.** `FEAT-UI-07` stays withdrawn; retired identifiers are never reused. New UI features continue this registry. | Feature IDs are permanent runtime/configuration identities under the pipeline. No separate feature-ID migration is approved; the semantic-ID examples in pipeline §3.1 are illustrative, not a mandate for this package. |
| D2 | **The D-UI target shape is pipeline §4.8**: `app/ui/src/widgets/<widget_slug>/` owning `README.md`, `manifest.ts`, `config.ts`, `feature.tsx`, focused modules, and a deliberate `index.ts`. The `src/features/…` target tree previously recorded in `app/ui/README.md` is retired; the README structure tree now agrees with its own feature registry and the code. | The registry table and the actual code already use `src/widgets/`; only the structure tree had drifted to `src/features/`. |
| D3 | **The external boundary owner is the Interfaces (D-IFACE) domain** under `app/services/interfaces/`. The deleted monolithic `app/services/api` (commit `4fef8b61`, 2026-09-02) is **not** restored wholesale. The seven `interfaces.*@1` capabilities in `app/contracts/interfaces/` are the ratified boundary contract set. | Pipeline §6.3 makes external surfaces registered D-IFACE features; root `README.md` and `docs/templates/README.md` already state this ownership. |
| D4 | **The existing typed client infrastructure is migration evidence and is preserved, not deleted and rebuilt**: the 169-operation route inventory (`app/ui/src/clients/routes.ts`), the `ApiResponse.v1`/`ApiError.v1`/`ApiMetadata.v1`/`StreamEvent.v1` envelope mirrors (`app/ui/src/clients/contracts.ts`), and the generated TypeScript contracts (`app/ui/src/contracts/generated/`, including `interfaces.ts`). Envelope record ownership formally moves to the Interfaces domain when the transport feature (`FEAT-IFACE-SERVE_API_EVENTS`) lands in Phase 2; existing v1 semantics are preserved as the frozen observed contract. Route naming is preserved per the adopted public contract in each vertical slice (first: Market Ticks, Phase 3). | The clients are typed, drift-tested, and behavior-complete; rebuilding them would discard validated evidence. |
| D5 | **Provisional `FEAT-IFACE-*` family for Phases 1–3**: `FEAT-IFACE-SERVE_API_EVENTS`, `FEAT-IFACE-OPERATE_TRADING`, `FEAT-IFACE-OPERATE_RESEARCH`, `FEAT-IFACE-OPERATE_PORTFOLIOS`, `FEAT-IFACE-ADMINISTER_CAPABILITIES`, `FEAT-IFACE-AUTOMATE_COMMANDS`, plus `FEAT-IFACE-OBSERVE_MARKET_DATA` for the Phase 3 vertical slice. Additional features are added only when the audit proves a distinct cohesive responsibility (see §3.3 gap G5 for `EDIT_PROJECTS`). | Matches the ratified migration plan; each maps to an existing `interfaces.*@1` capability except the Market Ticks gateway (see G1). |

**Ratified sequence:** Phase 0 (this record) → 1 D-IFACE domain foundation →
2 HTTP/SSE transport feature → 3 Market Ticks backend gateway → 4 Market Ticks
D-UI migration → 5 end-to-end removal proof → **stop and review** → 6 read-only
widgets → 7 stateful/governed widgets → 8 workbenches → 9 legacy cleanup →
10 full CI/removal gate. **Critical rule: Phase 6 must not begin until Phase 5
passes.** Market Ticks is the architectural reference implementation.

---

## 2. Task 0.1 — Backend/UI boundary audit

### 2.1 Client layer inventory

`app/ui/src/clients/` contains 24 client modules plus 4 infrastructure modules
(`routes.ts`, `request.ts`, `stream.ts`, `contracts.ts`) and the barrel
(`index.ts`) exporting the `apiClients` catalog. All HTTP flows through the
single `request` transport; all SSE through the single `openStream` transport.

| Module | Operations | Route group | Backend domain (authoritative) | Domain implemented today |
| --- | ---: | --- | --- | --- |
| `auth.ts` | 4 | `authRoutes` | Identity/session — **no owner** (was deleted API `api.identity@1`) | No |
| `health.ts` | 2 | `healthRoutes` | Boundary observability — D-IFACE transport responsibility | No |
| `settings.ts` | 7 | `settingsRoutes` | Settings/runtime profile — was API-owned tables on Data persistence; **owner decision pending** | No |
| `watchlists.ts` | 4 | `watchlistsRoutes` | Account watchlists — was deleted `FEAT-API-25`; **owner decision pending** | No |
| `data.ts` | 19 | `dataRoutes` | Data (+ Brokers providers) | **Yes** (14 data + 6 broker features registered) |
| `indicators.ts` | 4 | `indicatorsRoutes` | Indicators | Contracts only |
| `strategies.ts` | 4 | `strategiesRoutes` | Strategy | Contracts only |
| `research.ts` | 22 | `researchRoutes` | Research (gateway: `interfaces.operate-research@1`) | Contracts only |
| `dashboards.ts` | 6 | `dashboardRoutes` | Analytics dashboards | Contracts only |
| `operator.ts` | 3 | `operatorRoutes` | Operator audit/events/approvals — was API machinery; **owner decision pending** | No |
| `metrics.ts` | 1 | `metricsRoutes` | Prometheus exposition — was API telemetry; **owner decision pending** | No |
| `simulation.ts` | 3 | `simulationRoutes` | Simulator | Contracts only |
| `simulator.ts` | 5 | `simulatorRoutes` | Simulator | Contracts only |
| `simulationWorkbench.ts` | 18 | `simulationWorkbenchRoutes` | Simulator workbench | Contracts only |
| `liveSimulation.ts` | 5 | `liveSimulationRoutes` | Simulator recovery/what-if | Contracts only |
| `simulationSessions.ts` | 2 | `simulationSessionRoutes` | Simulator journal playback | Contracts only |
| `analyticsWorkbench.ts` | 13 | `analyticsWorkbenchRoutes` | Analytics workbench | Contracts only |
| `risk.ts` | 3 | `riskRoutes` | Risk | Contracts only |
| `trading.ts` | 17 | `tradingRoutes` | Trading (gateway: `interfaces.operate-trading@1`) | Contracts only |
| `portfolio.ts` | 10 | `portfolioRoutes` | Portfolio (gateway: `interfaces.operate-portfolios@1`) | Contracts only |
| `optimization.ts` | 11 | `optimizationRoutes` | Optimization — **no contract family exists** (see G3) | No |
| `agentic.ts` | 7 | `agenticRoutes` | Agentic operations — **no contract family exists** (see G3) | No |
| `workstation.ts` | 2 | `workstationRoutes` | Composite workstation projection — deleted API machinery; **retire, do not recreate** (Phase 8 replaces with focused gateways) | No |

Registered entry points today: brokers (6), catalogue (3), data (14).
`app/services/plugins` and `app/services/workspace` packages also exist with
owning READMEs.

### 2.2 HTTP endpoint inventory

`ROUTE_CONTRACTS` registers **169 backend-v1 operations** across 23 route
groups (`routes.ts:1438–1611`), each with method, path, permission string,
side-effect class, and governed/idempotency/pagination/stream/text flags.
The drift test (`clients.contract.test.ts:20–1067`) pins all 169 against a
checked-in `EXPECTED` literal, so the inventory remains enforceable even
though the backend is deleted — it is now self-referential (frontend-only)
until D-IFACE features re-anchor it.

**Defect found (must fix in Phase 2 reconciliation):** `dataRoutes` defines
19 routes but only 12 are aggregated into `ROUTE_CONTRACTS`. Seven routes
consumed by `data.ts` — `api.data.series`, `api.data.instruments`,
`api.data.brokers`, `api.data.instrument`, `api.data.series_update`,
`api.data.reference_sync`, `api.data.instrument_update` — are invisible to
the drift test. Also `routes.ts:2` still says "138 registered" and
`routes.ts:1416` says "74 route contracts" while `ROUTE_CONTRACT_COUNT = 169`.

### 2.3 SSE/stream endpoints (8)

`api.data.stream`, `api.data.snapshot_stream`, `api.data.depth_stream`
(bounded to 1–200 symbols), `api.research.run_events`,
`api.simulator.run_stream`, `api.simulator.workbench.batch_stream`,
`api.trading.execution_session_activity`, `api.simulation.session_frames`.
All serve `StreamEvent.v1` frames (`sequence`, `request_id`, `trace_id`,
`route`, `event_type` ∈ `heartbeat|payload|error`, `timestamp`, `payload`,
`error`, `cursor`). The consumer (`context/streams.ts`) enforces monotonic
sequence, filters heartbeats, surfaces terminal errors, reconnects up to 3
times with `Last-Event-ID` resume, and raises `StreamGapError` on
unrecoverable gaps after an `onGap` authoritative refresh hook. This is
exactly the temporal contract Phase 2/3 must preserve.

### 2.4 Authentication/session dependencies

- Session cookie `hq_session` (opaque, HttpOnly) + CSRF cookie `hq_csrf`
  double-submitted as `X-CSRF-Token` on every non-GET
  (`request.ts:67–80, 449–454`).
- `Authorization: Bearer` service-account transport exists
  (`RequestOptions.authToken`, `stream.ts:26`) but no UI caller uses it;
  cookie auth is the only transport in use.
- Identity truth: `GET /api/v1/auth/me` probed by `AuthProvider` on mount;
  failure fails closed to `unauthenticated` (`context/auth.tsx:110–155`).
  Register/login/logout complete the lifecycle; logout is 204-bodyless.
- Headers on every call: `X-Request-Id` (`req-<uuid4>`), optional
  `X-Trace-Id`, auto `Idempotency-Key` (UUID) on idempotency-required
  routes, `credentials: "include"` throughout.
- Dev transport: Next.js rewrite `/api/:path*` → `BACKEND_URL`
  (default `http://127.0.0.1:8000`, 600 s proxy timeout) in
  `next.config.mjs`; base URL overridable via `NEXT_PUBLIC_API_URL`.
- Governed-write preflight (`context/governed.ts`): requires
  workflow/permission/actorId/evidenceId, generates the idempotency key,
  enforces a 30 s freshness window mirroring backend
  `GovernedRequestContext.v1`; advisory only — backend gates stay
  authoritative.

### 2.5 Mutation requirements observed

- **30 governed routes** (`governed: true` — idempotency + governance
  evidence + CSRF): trading order/cancel/close/cancel-all, risk kill-switch,
  operator approvals, research expectancy/stress, strategy register/update,
  data governed writes, portfolio lifecycle (6), agentic (5), live-session
  create/branch, journal session create, workstation command.
- **Optimistic concurrency** in bodies: settings `expected_version`;
  trading sessions `expected_version` (from `ExecutionSession.version`);
  portfolio `expected_revision` + `expected_predecessor`. The interfaces
  contracts also define `If-Match`/ETag semantics
  (`ConcurrencyTokenWire`, 412 `VERSION_CONFLICT`).
- **Idempotency-only routes** additionally: settings update/credential,
  research createRun/createAutomation, simulation/simulator runs, most
  workbench lifecycle writes. `api.simulation.live_session_step` is
  deliberately un-keyed (cumulative; reconcile on returned cursor).
- **Confirmation** is a UI presentation concern only (workspace
  confirmation mode never satisfies backend governance).
- **Error envelope**: 22 stable `ApiErrorCode` values; `ApiError.v1`
  (`code`, `message`, bounded `details`, `request_id`, `trace_id`,
  `retryable`); `ApiMetadata.v1` carries route/operation/side-effect,
  `stale`+`stale_reason`, `next_cursor`/`page_size` (0–200), and
  `idempotency_replayed`. `/api/v1/metrics` bypasses JSON for Prometheus
  text. Single opt-in GET retry only (NFR-API-013 posture: never blind-retry
  governed writes or unknown broker outcomes).

### 2.6 API behavior that belonged only to the deleted legacy API

Not restored wholesale; each item gets a disposition in later phases:

| Deleted-API mechanism | Disposition |
| --- | --- |
| FastAPI app/middleware stack, route registration, 169-route catalog registry | Re-created minimally as the Phase 2 transport feature's mounting surface; the frozen route inventory becomes the per-vertical-slice re-exposure checklist (Phases 3–8). |
| Identity, password hashing, sessions, CSRF, rate limits, deadlines | Boundary security is D-IFACE transport responsibility (Phase 2); identity/session storage ownership is a Phase 1/2 design decision recorded as gap G2. |
| Credential vault, MT5 snapshot bridge settings, provider enablement flags | Owner decisions deferred to the vertical slices that need them (Phase 7 trading); never embedded in the transport feature. |
| User/session/settings/idempotency tables on shared persistence | Re-homed only when an owning feature requires them (Phase 7 System Settings). |
| Prometheus telemetry exposition | Phase 2 transport decision (keep or retire `/api/v1/metrics`). |
| Workstation composite read/command surface | Retired; Phase 8 replaces it with focused per-workbench gateways (no `workstation_backend.py` monolith). |
| Dashboards ad-hoc snapshot routes | Replaced by owning-domain projections (Analytics) in Phase 6+. |
| Approval attestation production, critical alert delivery | Belong to Risk/Trading capabilities via gateways, not to the transport (Phase 7). |

### 2.7 Client-layer defects recorded for later phases

1. Seven shadow data routes outside `ROUTE_CONTRACTS`/drift test (§2.2) — fix
   in Phase 2 reconciliation.
2. `routes.ts` header counts stale (138/74 vs 169) — Phase 9.
3. `context/auth.tsx:11–15` docstring cites `/health/readiness` as the
   session probe; code uses `/auth/me` — Phase 9.
4. `context/index.ts:5–6` claims the stream consumer is "intentionally
   absent" while exporting `consumeStream` — Phase 9.
5. `workstation.ts:1` stray empty statement — retire with the workstation
   surface in Phase 8.

---

## 3. Task 0.2 — Interfaces contracts audit

### 3.1 Contracts that remain valid (all seven)

`app/contracts/interfaces/` is a live, machine-reconciled contract family
(`app/contracts/README.md` §4.10; enforced by
`tests/contracts/test_contract_inventory.py`; generated TypeScript mirror at
`app/ui/src/contracts/generated/interfaces.ts`). Nothing in it describes the
deleted FastAPI gateway — it is the ratified D-IFACE boundary contract set:

| Capability key | Protocol purpose | Wire records (R1–R16 family) |
| --- | --- | --- |
| `interfaces.serve-api-events@1` | Versioned HTTP/OpenAPI + SSE serving, `If-Match` concurrency, mutation deduplication, event publish/replay with cursor semantics, async jobs, artifact download validation, compatibility/deprecation reporting | `ApiVersionWire`, `ConcurrencyTokenWire`, `EventCursorWire`, `EventReplayBatchWire`, `AsyncJobRefWire`, `ArtifactDownloadRequestWire` |
| `interfaces.automate-commands@1` | Presentation-neutral CLI/MCP/API command delegation, durable command tracking/cancellation | `AutomationCommand`, `AutomationSchema`, `McpOperation` |
| `interfaces.operate-research@1` | Research preview/admission gateway (`PREVIEW`) | `ResearchPreview` |
| `interfaces.edit-projects@1` | Project graph gateway (`PROJECT_GRAPH`/`VALIDATE`/`COMPARE`), delegating to Orchestration | `ProjectGraphProjection` |
| `interfaces.operate-portfolios@1` | Portfolio operations gateway (`VIEW`/`VALIDATE`/`COMPARE`) | `PortfolioBuilderProjection` |
| `interfaces.administer-capabilities@1` | Capability administration projection (no secrets) | `CapabilityAdministrationProjection` |
| `interfaces.operate-trading@1` | Governed trading gateway (`MANAGE_SESSION`/`READINESS`/`PREVIEW_ACTION`/`EMERGENCY`/`MARKET_DATA`/`OPERATOR_ANALYTICS`) + ordered event subscription with resume/replay bounds | `TradingActionPreview`, `TradingReadinessProjection`, `OperateTradingEventSubscription` |

Shared failure envelope: `InterfaceFailure` with the closed 10-code
`InterfaceFailureCode` union, including the pipeline-mandated
`CAPABILITY_UNAVAILABLE` no-mutation result. Wire schemas:
`app/contracts/interfaces/wire/schema.json`.

### 3.2 Capability → `FEAT-IFACE-*` mapping

| Capability | Feature ID | Phase |
| --- | --- | --- |
| `interfaces.serve-api-events@1` | `FEAT-IFACE-SERVE_API_EVENTS` | 2 |
| `interfaces.automate-commands@1` | `FEAT-IFACE-AUTOMATE_COMMANDS` | later (deferred until a CLI/MCP consumer is ratified) |
| `interfaces.operate-research@1` | `FEAT-IFACE-OPERATE_RESEARCH` | 6–8 (with Research migration) |
| `interfaces.edit-projects@1` | **unmapped — see G5** | — |
| `interfaces.operate-portfolios@1` | `FEAT-IFACE-OPERATE_PORTFOLIOS` | 7–8 (with Portfolio migration) |
| `interfaces.administer-capabilities@1` | `FEAT-IFACE-ADMINISTER_CAPABILITIES` | after Phase 5 (system surfaces) |
| `interfaces.operate-trading@1` | `FEAT-IFACE-OPERATE_TRADING` | 7 (with Trading migration) |
| *(new, see G1)* | `FEAT-IFACE-OBSERVE_MARKET_DATA` | 3 (Market Ticks slice) |

### 3.3 Contract gaps identified before D-IFACE production code

- **G1 — Market-data observation capability.** No `interfaces.*` capability
  exposes market snapshots/ticks. Phase 3's gateway resolves existing public
  providers — Data/broker tick streaming exists
  (`app/contracts/data/tick_stream/v1.py`, `TickStreamCapabilityV1`, and the
  realtime-market-events data feature) — so the gap is an *interface
  projection contract* over those providers, added only if genuinely absent
  per the ratified rule (no MT5 imports; capability resolution only).
- **G2 — Identity/session and boundary security contracts.** The UI's
  auth/session/CSRF surface (`/api/v1/auth/*`, `hq_session`, `hq_csrf`) has
  no owner in `app/contracts/interfaces/`. Phase 1/2 must decide whether
  identity is a dedicated `FEAT-IFACE-*` feature or a transport-owned
  boundary concern, and record it in the domain README before Phase 7
  (Session/Auth UI migration) begins.
- **G3 — Consumed domains with no contract family.** `optimization` and
  `agentic` clients (11 + 7 operations) have no `app/contracts/<domain>/`
  family at all. These surfaces stay frozen UI evidence until owning domains
  are ratified; they are not D-IFACE scope today.
- **G4 — HTTP envelope family ownership.** `ApiResponse.v1`, `ApiError.v1`,
  `ApiMetadata.v1`, `StreamEvent.v1`, `RouteContract`,
  `GovernedRequestContext`, `PageContext` were owned by the deleted domain
  and are mirrored only client-side. Phase 2 (`FEAT-IFACE-SERVE_API_EVENTS`)
  ratifies their canonical records (preserving the frozen v1 semantics) or
  their explicit successor, together with API versioning, OpenAPI manifest,
  compatibility/deprecation reporting, and bounded SSE replay retention.
- **G5 — `interfaces.edit-projects@1` has no provisional feature.** Either
  ratify `FEAT-IFACE-EDIT_PROJECTS` in Phase 1's registry or record the
  capability as declared-but-unimplemented (permitted by
  `app/contracts/README.md`: "Defined contracts do not imply that every
  owning runtime feature is implemented").
- **G6 — Watchlists/settings/operator/metrics/health ownership.** No
  surviving domain owns these former-API surfaces; each vertical slice that
  needs one must first record the owning capability decision.

### 3.4 Legacy-API mechanisms explicitly **not** valid as future behavior

The 28-feature `FEAT-API-*` registry, its `api.*@1` capability keys, and the
`[tool.haruquantai.domain.api]` pyproject domain section describe a deleted
implementation. They are not requirements input for D-IFACE; the frozen UI
client contracts (D4) are the behavior evidence, and the pipeline +
`app/contracts/interfaces/` are the architecture authority.

---

## 4. Authoritative-document drift register

Recorded so later phases fix each item at its owning moment. Phase 0 itself
changed only `app/ui/README.md` and added this record.

| Artifact | Drift | Owning phase |
| --- | --- | --- |
| `docs/PROJECT.md` | Domain index §2.1.14 "API" (lines ~335–345), dependency diagrams, §5 "UI/API" counterparty column (~108 uses), package registry row 14, feature counts (253/245, 243/234), citations of deleted `app/services/api/...` files; no mention of the Interfaces domain | Phase 1 (domain landing) + Phase 10 (final counts) |
| `docs/ARCHITECTURE.md` | Lines ~7, 36, 412, 463, 469–473, 486, 2411 still define the deleted gateway and its `CAPABILITY_UNAVAILABLE` synthesis; no D-IFACE section | Phase 1 |
| `app/services/README.md` | Full stale registry: 12 domains / "184 service features" incl. 28 `FEAT-API-*` rows and `api/README.md` link; composition-root reference to deleted path; no Interfaces row | Phase 1 |
| `docs/CHANGELOG.md` | Deletion of `app/services/api` (commit `4fef8b61`) unrecorded; [Unreleased] still narrates route additions under the deleted gateway | Phase 1 commit note |
| `pyproject.toml` | `[tool.haruquantai.domain.api]` still configured (lines ~593–618); no `domain.interfaces` | Phase 1 |
| `scripts/migrate_env_settings.py`, `scripts/refresh_openapi_snapshot.py` | Broken imports of `app.services.api` | Phase 9 |
| `app/ui/src/clients/routes.ts`, `contracts.ts`, `request.ts`, `clients.contract.test.ts` | Comment-only references to deleted backend paths as "source of truth" | Phase 2/9 |
| `app/ui/src/widgets/research/README.md`, `chart/README.md` | Cite deleted `FEAT-API-26` and `/api/v1` owners | Phase 9 |
| `app/ui/README.md` FR rows citing `FR-API-*` provenance and `/api/v1` paths | Frozen observed contracts; keep as evidence until each slice re-anchors them | Per-slice (3–8), residue in 9 |

---

## 5. Phase 0 changes made

1. Added this record: `docs/dev/iface-ui-migration/phase-0-baseline-reconciliation.md`.
2. `app/ui/README.md`: corrected the header feature/status counts (31
   registered; 23 Completed / 8 Pending; `FEAT-UI-07` withdrawn); re-anchored
   the consumed-contracts owner table from the deleted API domain to the
   Interfaces (D-IFACE) domain with the frozen-evidence note (D4); replaced
   the stale `src/features/…` target tree with the pipeline §4.8
   `src/widgets/<slug>` shape plus documented support folders; added the
   feature-identity decision (D1/D2); updated the `FEAT-API-11/12`
   consumption note (D3).

## 6. Verification

Documentation-only change: no production behavior changes; no backend or
frontend test surface touched. README references inside UI tests are
comment-only citations (verified — no test machine-validates
`app/ui/README.md`). The machine-reconciled contract inventory
(`tests/contracts/test_contract_inventory.py`) is unaffected because no
contract file changed.

## 7. Proposed commit

```text
docs: reconcile interfaces and ui composability migration
```
