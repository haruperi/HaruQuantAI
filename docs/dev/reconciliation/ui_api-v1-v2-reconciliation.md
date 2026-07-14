# UI/API — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** `ui_api`
* **Domain ID:** `ui`
* **V1 audit report:** `docs/dev/audits/api-v1-audit.md`
* **V2 requirements:** `11_ui_api.md`
* **Comparison limitations:** This reconciliation uses the V1 audit as the only V1 evidence and the V2 requirements as proposals. No code was re-audited or modified. The V1 audit was static and could not execute imports, tests, routes, providers, WebSockets, migrations, or deployment configuration. The V2 document supplied 328 unnumbered checklist requirements; this reconciliation assigns stable provisional IDs in source order so every requirement can receive a disposition. Frontend runtime behavior was not confirmed by the V1 audit. Cross-domain alignment is intentionally deferred to pipeline step 05.

## 2. Executive Summary

The final direction is **evolutionary reuse with a boundary reset**, not a full behavioral rewrite. V1 already exposes valuable workflows for authentication, settings, strategies, backtests, simulation, risk, optimization, Edge Lab, AI chat, live sessions, dashboards, documentation, and operator approvals. Those workflows should remain available where they support real users.

The primary correction is structural: the V1 API is an oversized integration layer with two FastAPI roots, three identity models, fail-open route/startup behavior, process-local stream/runtime state, route-local domain algorithms, disconnected routes, and almost no evidenced API quality gates. V2 correctly requires typed contracts, standard errors, authorization, idempotency, stream lifecycle rules, frontend contract validation, and traceability. However, V2 also over-prescribes service-client/orchestrator layers, a second operator app, universal cursor pagination, a very broad frontend surface, and numerous low-evidence Edge Lab endpoints.

Recommended migration direction: create one canonical gateway; unify identity; make routes thin; preserve domain workflows by delegating to approved public domain APIs; merge stream handling and health; add contract/security tests; build only the frontend pages required by approved workflows. Defer advanced Edge automation/calibration/exports, currency strength, broad performance pages, public health streaming, and speculative operator metadata. System-level decisions remain open for package path, token transport, versioning, idempotency storage, permissions, deployment topology, limits, and orchestration boundaries.

## 3. Decision Principles

* Preserve proven workflow behavior, not V1 file structure.
* Use one canonical gateway and one canonical authenticated principal.
* Keep route handlers limited to request validation, authorization, delegation, and DTO/error translation.
* Call approved in-process domain APIs directly; add client or orchestrator layers only when a confirmed deployment/workflow requires them.
* Use classes only for state, dependency ownership, or lifecycle; prefer functions for stateless boundary operations.
* Fail closed for required startup work and governed/live mutations; explicitly degrade only optional capabilities.
* Keep one focused responsibility per file and move domain algorithms out of the UI/API domain.
* Build frontend routes and components from approved workflows rather than from a comprehensive screen catalogue.
* Defer capabilities whose use, owner, source contract, or operational workflow is not demonstrated.
* Require typed contracts, security tests, traceability, and observable failure behavior before Builder handoff.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
|---|---|---|---|---|---|---|---|---|
| CAP-UI-001 | Canonical gateway composition and lifecycle | V1-CAP-API-001, 002, 049, 050 / V1-WF-API-001 | UIAPI-FR-033–042; UIAPI-NFR-009, 011 | Two apps; fail-open startup; placeholder job | Modify | One canonical app, explicit required/optional routes, observable lifecycle, liveness/readiness, no log-only jobs. | Refactor and merge | Preserves proven composition while removing split deployment and hidden degradation. |
| CAP-UI-002 | Boundary contracts, envelopes and errors | All route capabilities; V1-ISSUE-API-014, 020, 021 | UIAPI-CAP-001–005; UIAPI-FR-001–018 | Inconsistent schemas/errors; missing stability metadata | Add | Every approved route/stream/client has a typed contract, classification, standard response/error shape and ownership. | New shared boundary code; refactor routes | Required to make the large V1 surface safe and testable. |
| CAP-UI-003 | Canonical identity and user sessions | V1-CAP-API-003, 005, 031 / V1-WF-API-002, 003, 012 | UIAPI-FR-043–047, 071–100; UIAPI-NFR-001, 015 | Disconnected user/chat/operator identities | Modify | One validated principal/session model used by user, AI-chat and operator routes. | Reuse DB session behavior; replace identity wiring | Removes fallback/development identities while preserving working auth. |
| CAP-UI-004 | Authorization, governed writes and idempotency | V1-CAP-API-004, 017, 033, 035, 042 / V1-WF-API-008, 012–014 | UIAPI-FR-019–025, 048–055, 065–070; UIAPI-NFR-002–004 | Role headers trusted; duplicate-submit behavior missing | Modify | Backend permissions, approvals, audit and idempotency gate every governed/financial mutation; frontend preflight is advisory. | Refactor and add shared policy enforcement | Safety-critical and directly addresses V1 weaknesses. |
| CAP-UI-005 | Request security, context and observability | V1-CAP-API-006, 007 / V1-WF-API-001 | UIAPI-FR-028–030, 038–039, 056–059; UIAPI-NFR-007, 012, 017–018 | Partial redaction; unused metadata; no consistent trace context | Modify | Allowlisted secret-safe logging, request/correlation context, bounded page context and consumed route intent metadata. | Reuse redaction; simplify classifier; add context | Provides traceability without preserving unused abstractions. |
| CAP-UI-006 | Health and readiness | V1-CAP-API-041, 043 / V1-WF-API-001, 014 | UIAPI-FR-040, 061–064; UIAPI-NFR-011 | Constant health and incomplete probes | Merge | Public liveness plus protected readiness/component details for configured dependencies. | Merge and replace | One health model is simpler and truthful. |
| CAP-UI-007 | Operator approvals and events | V1-CAP-API-042–044 / V1-WF-API-014 | UIAPI-FR-060–070 | Useful approvals; insecure/static event stream | Modify | Approvals/votes remain; operator events are protected and sourced from authoritative events; metadata endpoint deferred. | Reuse approvals; replace SSE | Preserves governed value and removes sample behavior. |
| CAP-UI-008 | Settings boundary | V1-CAP-API-005 / V1-WF-API-003 | UIAPI-FR-074–076 | Duplicate auth helper and duplicate path | Modify | One canonical authenticated read/update settings contract. | Refactor | Simple proven workflow. |
| CAP-UI-009 | Market data and prepared datasets | V1-CAP-API-008–009 / V1-WF-API-004 | UIAPI-FR-206–207 | Fallback user and inline data/research orchestration | Modify | Authenticated symbol reads and delegated dataset preparation with bounded typed output. | Reuse provider/result mapping selectively | Preserves core research input workflow. |
| CAP-UI-010 | Strategy catalogue, versions and SQX | V1-CAP-API-010–011, 046–048 / V1-WF-API-005 | UIAPI-FR-101–114 | Mixed DB/filesystem/governance logic; disconnected/missing routes | Split | Thin strategy/SQX boundary; strategy domain owns artifacts/governance; remove disconnected trade import and missing operator-strategy target. | Refactor; remove dead references; add score route if approved | Keeps proven value without route-local service layer. |
| CAP-UI-011 | Backtest API and log stream | V1-CAP-API-012–014 / V1-WF-API-006 | UIAPI-FR-115–123 | Oversized route and upward dependency | Split | Authenticated backtest commands/queries delegate to simulation; log stream follows shared stream contract. | Move orchestration; reuse DTO mapping | Corrects layering while preserving the workflow. |
| CAP-UI-012 | Interactive simulator API | V1-CAP-API-015–019 / V1-WF-API-007–008 | UIAPI-FR-124–146 | Gateway owns runtime/risk/state hub | Split | Gateway exposes lifecycle, frame, replay, mutation and what-if contracts; simulation/risk/execution own implementation. | Move runtime; reuse ownership/lease semantics | V1 workflow is valuable but structurally misplaced. |
| CAP-UI-013 | Risk decision-support API | V1-CAP-API-024–027 / V1-WF-API-010 | UIAPI-FR-147–150 | Route-local adapters/state construction | Modify | Typed authorized risk evaluation routes delegate entirely to risk-domain APIs. | Refactor | Retains valuable decision support with correct ownership. |
| CAP-UI-014 | Live-session API and monitoring | V1-CAP-API-034–037 / V1-WF-API-013 | UIAPI-FR-151–176 | Process-local state; shared broker client; unverified safety | Split | Gateway exposes governed live lifecycle/read/mutation/stream contracts; live domain owns runtime, broker, reconciliation and safety. | Move runtime; replace shared client; reuse DTOs | Required for safe real-capital operation. |
| CAP-UI-015 | Optimization, walk-forward and scenarios | V1-CAP-API-020–023 / V1-WF-API-009 | UIAPI-FR-177–193 | Default user; incomplete cancellation; local stream state | Modify | Authenticated bounded jobs, real cancellation, typed results and documented progress streams. | Refactor; reuse algorithms through domain | Preserves proven analytical workflows. |
| CAP-UI-016 | Edge Lab research boundary | V1-CAP-API-028–030 / V1-WF-API-011 | UIAPI-FR-208–245 | Oversized surface; disconnected automation | Split | Initial core: dataset, run/results, seasonality, core metrics, market structure, unsupervised analysis and scorecard snapshots; defer advanced calibration/automation/exports. | Refactor core; defer/remove placeholders | Smallest research boundary that retains demonstrated value. |
| CAP-UI-017 | AI chat, context and governed drafts | V1-CAP-API-031–033 / V1-WF-API-012 | UIAPI-FR-077–100, 274–275 | Development identity; optional tools fail empty; governed actions mixed | Modify | Canonical user-owned threads/messages/context/streams and proposal/draft delegation with bounded context. | Reuse conversation APIs; replace identity wiring | Preserves strong V1 value and fixes ownership. |
| CAP-UI-018 | Dashboard read models | V1-CAP-API-037–041 / dashboard reads | UIAPI-FR-194–201, 279 | Overlapping status; provider freshness unclear | Modify | Broker/equity/summary/resources/market-hours/calendar snapshots with timestamps and stale/unavailable states; currency strength deferred. | Reuse mappings; merge status | Focuses dashboard on reliable reads. |
| CAP-UI-019 | Documentation browser/editor | V1-CAP-API-045 / V1-WF-API-015 | UIAPI-FR-026, 202–205, 248, 285 | Unauthenticated local-file mutation risk | Modify | Authenticated internal docs tree/read and role-gated audited edit/delete within a safe root. | Reuse path logic after hardening | Keeps useful workflow safely. |
| CAP-UI-020 | Shared streaming transport | V1-CAP-API-014, 023, 036, 044 | UIAPI-CAP-004; UIAPI-FR-015, 070, 099, 123, 176, 193 | Three local managers plus static SSE; no common lifecycle | Merge | One stream contract and small stateful implementations only where stream lifecycle requires them. | Merge/refactor; replace operator SSE | Reduces duplication and supports multi-worker decisions. |
| CAP-UI-021 | Frontend typed request/client layer | No confirmed V1 frontend-client capability in audit | UIAPI-CAP-005; UIAPI-FR-253–273 | Missing evidence and duplicated proposed helpers | Add | One typed request primitive, focused route-group clients, validation, trace IDs, safe retries, stale metadata and governed options. | New | Required to prevent frontend/API drift. |
| CAP-UI-022 | Frontend authentication and protected shell | No confirmed V1 capability in audit | UIAPI-FR-246, 276–278 | Missing confirmed final behavior | Add | Login/register, session recovery, protected layout, navigation and error boundary for approved workflows. | New | Necessary user entry and protection. |
| CAP-UI-023 | Frontend workflow pages | No confirmed V1 capability in audit | UIAPI-FR-247–252, 279–285 | Proposed surface is larger than confirmed workflows | Modify | Build pages/components only for approved dashboard, chat, strategy, backtest, simulator, risk, live, optimization, docs and core Edge Lab workflows; defer the rest. | New, scoped | Avoids rebuilding speculative UI breadth. |
| CAP-UI-024 | Contract, security and workflow tests | V1-ISSUE-API-026–028 | UIAPI-FR-031–032; UIAPI-NFR-016, 028–030; UIAPI-TEST-* | No direct API tests; API excluded from gates | Add | Requirement IDs, route/stream/OpenAPI contracts, backend/frontend tests, security, accessibility and traceability gates. | New | Essential acceptance evidence. |

## 5. V1 Disposition Register

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
|---|---|---|---|---|---|---|
| `V1-CAP-API-001` | General FastAPI composition | `main.py::app` | Essential (Used); Fail-open optional composition | Modify | Gateway composition: Replace broad fail-open startup with one canonical app, explicit required/optional routes, readiness state, and tested lifecycle. | N/A |
| `V1-CAP-API-002` | Operator API composition | `app.py::app` | Useful (Possibly used); Separate deployment entry point | Merge | Gateway composition: Fold protected operator routes into the canonical app; retain a temporary compatibility entry point only during migration. | Confirm no deployment still targets the separate operator app before removal. |
| `V1-CAP-API-003` | User registration/login/logout | `routes/auth.py`, `auth_utils.py`, models | Essential (Used); DB session tokens | Modify | Identity and sessions: Reuse DB-backed sessions and account checks, but unify envelopes, revocation checks, token transport, and dependency injection. | N/A |
| `V1-CAP-API-004` | Operator role gate | `auth.py` | Essential (Used); Token authority not validated | Modify | Identity and authorization: Keep operator role enforcement but derive the principal from a validated authority rather than caller-controlled headers. | N/A |
| `V1-CAP-API-005` | User settings | `routes/settings.py` | Useful (Used); Duplicate auth helper | Modify | Settings boundary: Keep read/update behavior; remove duplicate auth parsing and apply typed contracts, ownership, and standard envelopes. | N/A |
| `V1-CAP-API-006` | Request secret redaction | middleware/security | Useful (Used); Headers/query only | Modify | Request security and observability: Keep redaction; log an allowlisted sanitized metadata set and cover all secret-bearing telemetry paths. | N/A |
| `V1-CAP-API-007` | Intent classification | `router.py`, main middleware | Useful (Used); Metadata only; no dispatcher enforcement | Modify | Request context: Retain lightweight intent metadata only where consumed; remove mutable unused classifier APIs and derive actor/session from authenticated context. | Verify no external caller uses mutable classifier methods. |
| `V1-CAP-API-008` | Market symbol discovery | `routes/data.py` | Useful (Used); MT5 credentials/provider | Modify | Market-data boundary: Keep symbol discovery but remove fallback user `1`, require auth, and delegate provider access to the data/broker domain. | N/A |
| `V1-CAP-API-009` | Prepared research datasets | `routes/data.py` | Essential (Used); Clean/enrich/serialize | Modify | Dataset boundary: Keep prepared-dataset workflow while moving cleaning/enrichment/serialization orchestration behind a data/research capability boundary. | N/A |
| `V1-CAP-API-010` | Strategy catalogue CRUD | `routes/strategies.py` | Essential (Used); DB/filesystem/governance coordination | Split | Strategy boundary: Keep API CRUD; move DB/filesystem/governance coordination into the strategy domain and expose only typed boundary calls. | N/A |
| `V1-CAP-API-011` | Strategy version/import/export | `routes/strategies.py` | Essential (Used); Local artifacts | Modify | Strategy boundary: Preserve version/import/export behavior with transactional or compensating failure rules and bounded upload contracts. | N/A |
| `V1-CAP-API-012` | Backtest execution | `routes/backtest.py` | Essential (Used); Route-local execution adapter | Split | Backtest boundary: Keep the run endpoint; move execution, persistence, and analytics orchestration out of the route layer. | N/A |
| `V1-CAP-API-013` | Backtest CRUD/results/analytics | `routes/backtest.py` | Essential (Used); Persistence and analytics | Modify | Backtest boundary: Preserve CRUD/results/overview with ownership, pagination, typed DTOs, and standard envelopes. | N/A |
| `V1-CAP-API-014` | Backtest log streaming | `websocket.py`, backtest route | Useful (Used); Process-local buffer | Modify | Streams: Preserve log streaming but replace process-local contract-free buffering with a documented stream lifecycle and deployment-appropriate state model. | N/A |
| `V1-CAP-API-015` | Interactive simulator sessions | simulator route/session package | Essential (Used); DB lease + in-memory runtime | Split | Simulator boundary: Keep session lifecycle and ownership semantics; move runtime, lease, risk, and execution behavior into simulation/execution domains. | N/A |
| `V1-CAP-API-016` | Simulator frame/replay control | `SimulatorSession`, simulator routes | Essential (Used); Advance/seek/replay | Modify | Simulator boundary: Preserve advance/seek/replay controls as thin authenticated operations. | N/A |
| `V1-CAP-API-017` | Simulator trade/order mutation | trade service/execution facade/routes | Essential (Used); Governance-aware | Modify | Simulator boundary: Preserve governed simulated mutations; add request identity, authorization, idempotency where durable, and typed errors. | N/A |
| `V1-CAP-API-018` | Simulator what-if analysis | trade service/runtime/risk | Useful (Used); Non-mutating scenario path | Keep | Simulator boundary: Retain non-mutating what-if analysis as a valuable review workflow; expose it through the risk/simulation boundary. | N/A |
| `V1-CAP-API-019` | Simulator risk/governance/recommendations | session runtime/support/serializers | Essential (Used); Large coupling surface | Split | Simulator and risk boundaries: Preserve outputs, but move risk/governance/recommendation computation out of the API session runtime. | N/A |
| `V1-CAP-API-020` | Optimization runs/results | optimization routes/services | Essential (Used); Background tasks | Modify | Optimization boundary: Preserve run/result behavior; require authenticated ownership, true cancellation, bounded jobs, and thin delegation. | N/A |
| `V1-CAP-API-021` | Walk-forward analysis | optimization route/service | Useful (Used); Runtime unverified | Modify | Optimization boundary: Preserve walk-forward analysis behind the optimization domain and contract-test it. | N/A |
| `V1-CAP-API-022` | Monte Carlo/scenario simulation | optimization route/monte-carlo services | Useful (Used); Multiple immediate endpoints | Merge | Optimization scenarios: Keep useful scenario behavior but present it as one coherent scenario capability rather than route-local algorithm implementations. | N/A |
| `V1-CAP-API-023` | Optimization progress WebSocket | WebSocket manager/route | Useful (Used); Process-local | Modify | Streams: Preserve optimization progress streaming with auth, sequence, heartbeat, cleanup, and deployment-safe state. | N/A |
| `V1-CAP-API-024` | Position sizing API | risk route | Useful (Used); Risk service call | Modify | Risk boundary: Keep position-sizing endpoint but delegate all calculation to risk-domain functions/classes. | N/A |
| `V1-CAP-API-025` | Regime detection API | risk route | Useful (Used); MT5/manual modes | Modify | Risk boundary: Keep regime detection; remove route-local state construction where domain APIs can own it. | N/A |
| `V1-CAP-API-026` | Allocation planning API | risk route | Useful (Used); Portfolio decision support | Modify | Risk boundary: Keep allocation decision support with typed inputs and no inline portfolio logic. | N/A |
| `V1-CAP-API-027` | Governance comparison API | risk route | Essential (Used); Current/candidate reports | Modify | Risk boundary: Keep governance comparison as a read/evaluation capability with explicit authorization and contracts. | N/A |
| `V1-CAP-API-028` | Edge Lab analyses | `routes/edge.py` | Essential (Used); Broad research surface | Split | Research boundary: Preserve core Edge Lab analyses but split the oversized route surface into focused boundary capabilities and defer low-evidence extras. | N/A |
| `V1-CAP-API-029` | Edge profile/snapshot persistence | Edge route/DB | Useful (Used); Operational verification unavailable | Modify | Research artifacts: Preserve profile/scorecard snapshot persistence with ownership, versioning, and explicit artifact contracts. | N/A |
| `V1-CAP-API-030` | Edge automation records | Edge route | Useful (Used); Scheduled execution disconnected | Defer | Research automation: Exclude automation records/scheduling from the initial rebuild until an end-to-end scheduled workflow and owner are confirmed. | Confirm no production scheduler or UI depends on the records before disabling migration. |
| `V1-CAP-API-031` | AI-chat thread/message lifecycle | AI-chat route/conversation service | Essential (Used); Development user dependency | Modify | Conversation boundary: Preserve thread/message lifecycle but replace development-user identity with the canonical authenticated principal. | N/A |
| `V1-CAP-API-032` | AI-chat context and read-only tool catalogue | AI-chat route | Useful (Used); Optional tools fall back empty | Modify | Conversation boundary: Preserve bounded page context and read-only tool discovery; fail explicitly when optional capabilities are absent. | N/A |
| `V1-CAP-API-033` | AI signal/action draft lifecycle | AI-chat route/gateway | Essential (Used); Governed proposal surface | Modify | Conversation governance: Preserve proposal/draft lifecycle; paper execution and approval requests must delegate to governed backend workflows. | N/A |
| `V1-CAP-API-034` | Live session management | `routes/live.py` | Essential (Used); Process-local active map | Split | Live boundary: Preserve live-session API behavior but move active runtime ownership and lifecycle into the live domain. | N/A |
| `V1-CAP-API-035` | Live broker reads/mutations | live/dashboard broker routes | Essential (Used); Runtime unverified/high risk | Split | Live boundary: Preserve approved reads/mutations only; broker execution, reconciliation, approvals, and safety gates remain outside the gateway. | N/A |
| `V1-CAP-API-036` | Live WebSocket monitoring | live manager/route | Useful (Used); Process-local subscriptions | Modify | Streams: Preserve live monitoring with authenticated channels, heartbeat, cleanup, sequence, and deployment-safe fan-out. | N/A |
| `V1-CAP-API-037` | Broker dashboard | dashboard broker | Essential (Used); Shared client mutation | Modify | Dashboard boundary: Keep broker status reads; eliminate shared-client mutation and use a read-only broker facade. | N/A |
| `V1-CAP-API-038` | Currency strength | dashboard route | Useful (Used); Computation/provider read | Defer | Dashboard boundary: Postpone currency strength until its source, schema, freshness, and user workflow are approved. | Confirm no critical deployed page depends on it. |
| `V1-CAP-API-039` | Forex calendar | dashboard route | Useful (Used); Provider status unverified | Modify | Dashboard boundary: Keep calendar data only with provider-unavailable and stale-data contracts. | N/A |
| `V1-CAP-API-040` | Market hours | dashboard route | Useful (Used); Time calculation | Modify | Dashboard boundary: Keep market-hours behavior with timezone, DST, holiday, and broker-session tests. | N/A |
| `V1-CAP-API-041` | System/resource status | dashboard route | Useful (Used); Not equivalent to startup health | Merge | Health and dashboard status: Merge overlapping system/resource status into a coherent liveness/readiness/operational-status model. | N/A |
| `V1-CAP-API-042` | Operator approvals and votes | approvals/operator app | Essential (Used); Persistence-backed | Modify | Operator approvals: Preserve approval/vote persistence and role checks; add canonical identity, idempotency, audit, and stable route contracts. | N/A |
| `V1-CAP-API-043` | Operator component health | health/operator app | Useful (Used); Redis incomplete | Merge | Health and readiness: Merge component probes into protected readiness details; implement real probes only for configured dependencies. | N/A |
| `V1-CAP-API-044` | Operator event SSE | events/operator app | Questionable (Used); Static sample events | Remove | Operator event stream: Delete hard-coded public sample events; replace only with a protected stream connected to an authoritative event source. | Verify no demo client depends on the sample payload/path before deletion. |
| `V1-CAP-API-045` | Documentation tree/read/write/delete | docs route | Useful (Used); No auth evidenced | Modify | Documentation boundary: Keep tree/read/write/delete only as authenticated developer/operator capability with strict path, content, size, and audit controls. | N/A |
| `V1-CAP-API-046` | SQX import/inspection | sqx route | Useful (Used); Runtime parser compatibility unverified | Modify | Strategy import boundary: Keep SQX import/inspection after parser compatibility, upload limits, ownership, and cleanup behavior are verified. | N/A |
| `V1-CAP-API-047` | Trade import route | import_trades route | No demonstrated value (Unused); Not registered | Remove | None: No registered workflow or V2 requirement justifies the disconnected trade-import router. | Search deployment-specific mounts and confirm no external client uses it. |
| `V1-CAP-API-048` | Operator strategy API | Missing module | No demonstrated value (Unused/missing); Optional import target absent | Remove | None: Remove the missing optional operator-strategy import target rather than designing around an absent capability. | Confirm there is no planned approved operator-strategy contract. |
| `V1-CAP-API-049` | Background session cleanup | scheduler + simulator cleanup | Supporting (Used); APScheduler and startup cleanup | Modify | Gateway lifecycle: Keep stale-session cleanup, but make failures observable and scheduler usage conditional on real jobs. | N/A |
| `V1-CAP-API-050` | Scheduled Edge refresh | scheduler placeholder | Questionable (Used as log-only job); No analysis invoked | Remove | None: The scheduled Edge refresh is a log-only placeholder and provides no operational behavior. | Confirm no monitoring depends on the placeholder job identifier. |

## 6. V2 Requirement Disposition Register

The V2 source had no individual IDs. The following provisional IDs are assigned in source order and become the traceability baseline for the next documentation step.

### 6.1 Public-Capability Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-CAP-001` | Each public HTTP route, WebSocket/SSE stream, frontend client, and official callable capability shall identify whether it is public API, protected API, internal helper, migration-compatibility surface, official frontend client capability, or optional/deferred capability. | Add | Adopt for every approved public route, stream and frontend client. | V1 lacks complete classification, stability and route/client contract metadata. |
| `UIAPI-CAP-002` | Each public capability shall declare stability as stable, experimental, deprecated, migration-only, or optional/deferred. | Add | Adopt for every approved public route, stream and frontend client. | V1 lacks complete classification, stability and route/client contract metadata. |
| `UIAPI-CAP-003` | Each public HTTP route shall define method, path, auth requirement, role or permission requirement, request schema, response schema, status codes, standard error envelope, side effects, idempotency behavior, audit requirement where applicable, rate-limit class, observability fields, and owning backend/domain service. | Add | Adopt for every approved public route, stream and frontend client. | V1 lacks complete classification, stability and route/client contract metadata. |
| `UIAPI-CAP-004` | Each WebSocket, SSE, or streaming capability shall define auth, event schema, heartbeat interval, reconnect behavior, disconnect cleanup, backpressure behavior, terminal error event, sequence behavior, and maximum connection policy. | Add | Adopt for every approved public route, stream and frontend client. | V1 lacks complete classification, stability and route/client contract metadata. |
| `UIAPI-CAP-005` | Each frontend API client capability shall map to a documented backend route contract or be marked as frontend-only, mocked, optional/deferred, or migration-only. | Add | Adopt for every approved public route, stream and frontend client. | V1 lacks complete classification, stability and route/client contract metadata. |

### 6.2 Functional Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-FR-001` | UI/API requirements define boundary contracts, not domain-service implementation. | Keep | Keep the UI/API document focused on boundary behavior. | This is the correct domain boundary. |
| `UIAPI-FR-002` | API route handlers shall validate path, query, header, and body inputs using boundary schemas before calling domain services. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-003` | API route handlers shall translate validation failures into the standard validation error envelope with HTTP 422. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-004` | API route handlers shall translate authentication failures into the standard 401 error envelope. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-005` | API route handlers shall translate authorization failures into the standard 403 error envelope. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-006` | API route handlers shall translate domain blocks, idempotency conflicts, dependency failures, and internal failures into documented standard envelopes with route-appropriate status codes. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-007` | Domain-facing route handlers shall validate and authorize requests, call the approved owning domain service, translate service results into boundary DTOs, and shall not implement trading, risk, broker, simulation, optimization, research, or persistence algorithms inline. | Modify | Require thin validation/authorization/delegation routes; domain algorithms remain outside the gateway. | Accepted behavior; existing V1 routes violate it and need refactoring. |
| `UIAPI-FR-008` | Domain-facing route handlers shall use an approved service-client interface with explicit service discovery, timeout, auth context forwarding, service-account fallback rules, request/correlation ID propagation, and typed error translation before implementation. | Modify | Use explicit typed domain entry points with timeouts/context/error translation; require network service discovery only for actual remote services. | The safety behavior is valid, but mandatory service-client infrastructure is excessive for an in-process modular monolith. |
| `UIAPI-FR-009` | The gateway shall not call unknown internal service APIs directly from route handlers. Every delegated call shall go through an approved client or orchestrator abstraction. | Modify | Require calls through approved public domain APIs; do not mandate a client/orchestrator object for every in-process call. | Preserves boundary discipline without unnecessary layers. |
| `UIAPI-FR-010` | Delegation shall be serial by default: validate request, authorize actor, call one approved service client, translate result. Multi-service workflows require an approved orchestrator abstraction and must not accumulate business rules in route handlers. | Modify | Keep serial delegation as default; introduce an orchestrator only for a demonstrated multi-domain workflow. | The proposed universal abstraction is premature. |
| `UIAPI-FR-011` | Non-streaming API responses shall use a standard response envelope with `status`, `message`, `data`, `error`, and `metadata` fields. Metadata shall include request id, correlation or trace id, API version, route group or module, operation, side-effect class, execution time, and creation timestamp where available. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-012` | Error envelopes shall include deterministic code, human-readable message, bounded details, request id, trace or correlation id, and retryability where applicable. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-013` | Standard error codes shall include `VALIDATION_FAILED`, `AUTHENTICATION_REQUIRED`, `AUTHORIZATION_FAILED`, `CSRF_REQUIRED`, `CSRF_INVALID`, `RATE_LIMITED`, `IDEMPOTENCY_KEY_REQUIRED`, `DUPLICATE_IDEMPOTENCY_KEY`, `IDEMPOTENCY_CONFLICT`, `GOVERNANCE_REQUIRED`, `STALE_DATA`, `UPSTREAM_UNAVAILABLE`, `UPSTREAM_NON_JSON_RESPONSE`, `UPSTREAM_TIMEOUT`, `CONTRACT_VERSION_MISMATCH`, `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `OPERATOR_STREAM_FORBIDDEN`, `DEPENDENCY_UNAVAILABLE`, `INTERNAL_ERROR`, and `NOT_IMPLEMENTED`. | Modify | Define a compact stable error-code catalogue and add route-specific codes only when needed. | The exhaustive proposed list mixes confirmed and speculative cases. |
| `UIAPI-FR-014` | HTTP 204 responses shall never carry a body. Endpoints that need metadata, warnings, or audit details shall return a standard envelope with a non-204 status. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-015` | Streaming endpoints shall use a documented stream event envelope containing event name or type, data, request id, trace or correlation id, sequence, timestamp, and terminal-error fields where applicable. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-016` | Proposed Decision: List endpoints shall use cursor-based pagination by default, with `limit` defaulting to 50, maximum `limit` 200, opaque cursor strings, stable deterministic ordering, and empty results returned as an empty list plus null next cursor unless a route contract states otherwise. | Modify | Paginate unbounded collections; allow simpler bounded-list semantics where cursor pagination adds no value. | A universal cursor policy is disproportionate. |
| `UIAPI-FR-017` | Proposed Decision: API versioning shall default to `v0-draft` during pre-implementation work. Frontend clients shall send the expected API version when a route contract requires it. Version mismatch shall return `409` with `CONTRACT_VERSION_MISMATCH` for incompatible contracts or a documented warning metadata field for compatible minor changes. | Open Decision | Choose API versioning and mismatch behavior at system level before stable contracts are published. | This affects every domain and cannot be settled from V1/V2 evidence alone. |
| `UIAPI-FR-018` | Proposed Decision: Backward compatibility shall be preserved within an approved stable major API version. Deprecations require documentation, frontend migration notes, and an owner-approved removal window before stable-route removal. | Open Decision | Approve compatibility and deprecation policy at system level. | This is a shared contract decision. |
| `UIAPI-FR-019` | Mutating governed endpoints shall require request id, trace or correlation id, actor identity, required permission, approval context where applicable, audit event type, and an idempotency key for governed or financial mutations. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-020` | Idempotency keys shall be non-empty, string-safe, bounded-length values supplied through a documented header or request field; exact key format remains blocked by UIAPI-BLK-004. | Open Decision | Approve idempotency header name, key constraints, retention, and scope. | The required behavior is valid but format/lifecycle remain unresolved. |
| `UIAPI-FR-021` | Governed and financial mutation endpoints shall store idempotency material, request hash, response status, response headers, response body, actor, route, operation, created timestamp, expiry timestamp, and terminal state where storage is available. | Modify | Persist the minimum material needed to detect conflicts and replay safe results; avoid storing sensitive or unnecessary bodies/headers. | The full proposed record can duplicate audit storage and increase secret exposure. |
| `UIAPI-FR-022` | Proposed Decision: Duplicate idempotency keys for completed successful operations shall return the stored original response, including status, headers, body, and metadata, with `metadata.retryable=false` and `metadata.idempotency_replay=true`. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-023` | Proposed Decision: Duplicate idempotency keys with different material shall return HTTP 409 with `IDEMPOTENCY_CONFLICT`. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-024` | Proposed Decision: Duplicate idempotency keys for an unknown, in-progress, or terminal-failed previous attempt shall return HTTP 409 with `DUPLICATE_IDEMPOTENCY_KEY` unless the route contract defines a safer reconciliation response. | Modify | Return a deterministic conflict for in-progress/unknown attempts; handle terminal failures by route-specific reconciliation policy. | One response rule is not safe for every mutation. |
| `UIAPI-FR-025` | Proposed Decision: Idempotency storage unavailable shall fail closed by default with HTTP 503 and `DEPENDENCY_UNAVAILABLE` for governed and financial mutations. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-026` | Documentation save/delete endpoints shall enforce a configured documentation root, normalize paths, reject traversal, reject symlink escape outside the root, and return explicit validation errors. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-027` | Import endpoints shall define accepted file or content types, maximum size, parse-error behavior, duplicate import behavior, and cleanup behavior after partial failure. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-028` | Frontend page context providers shall redact secrets and bound context payload size before sending context to AI chat or route-aware workflows. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-029` | Frontend stale-warning threshold shall default to 30 seconds for dashboard/governed-decision context unless the route contract defines a stricter or looser threshold. | Modify | Define freshness per data class; use 30 seconds only as an initial dashboard default, not a universal rule. | Freshness varies by workflow. |
| `UIAPI-FR-030` | Governed frontend write preflight shall emit a warning telemetry event when it blocks a request, including sanitized route, required permission, missing context type, request id, trace id, and actor/session metadata where available. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-031` | Requirement IDs shall be added before production handoff for all functional and non-functional requirements, and each requirement shall map to at least one test case or an explicit manual-verification note. | Add | Adopt as a gateway contract requirement. | V1 applies these inconsistently or not at all. |
| `UIAPI-FR-032` | Requirement ID ranges shall use `UIAPI-CAP-*`, `UIAPI-FR-*`, `UIAPI-NFR-*`, `UIAPI-EDGE-*`, `UIAPI-TEST-*`, and `UIAPI-EX-*`. Existing unnumbered checkboxes remain provisional and are not Builder-ready until IDs are assigned. | Keep | Use the proposed requirement ID families in the final documentation. | Supports traceability and the next pipeline steps. |
| `UIAPI-FR-033` | `api.main:app` shall be the canonical backend FastAPI entry point. | Modify | Adopt one canonical FastAPI entry point and migrate to the approved package path; merge operator routes into it. | V1 has two composition roots and a path mismatch. |
| `UIAPI-FR-034` | `lifespan` shall initialize the database, apply pending migrations, clean stale simulator leases when simulator routes are available, start the scheduler, and shut the scheduler down on application shutdown. | Modify | Retain lifecycle initialization/cleanup, but required startup failures must fail readiness or startup; run only approved scheduler jobs. | V1 currently swallows critical failures. |
| `UIAPI-FR-035` | `_optional_import` shall load optional route modules and log startup warnings instead of failing the whole API when an optional route cannot import. | Modify | Allow fail-open import only for explicitly optional/deferred routes; required routes fail startup/readiness. | Broad optional imports hide defects. |
| `UIAPI-FR-036` | `_include_optional_router` shall include a router only when its module was imported successfully. | Modify | Include only successfully imported optional routers and surface their degraded state in readiness metadata. | Keeps optional degradation observable. |
| `UIAPI-FR-037` | The canonical API shall configure CORS for local frontend origins and allow credentials. | Modify | Use a configuration-driven exact-origin allowlist; local origins are development defaults only. | Production CORS must not be hard-coded to local use. |
| `UIAPI-FR-038` | The canonical API shall install `SecretRedactionMiddleware`. | Keep | Install secret-redaction middleware in the canonical app. | V1 already provides valuable behavior. |
| `UIAPI-FR-039` | `IntentClassificationMiddleware` shall classify every request path and attach intent, priority, session id, and user id metadata to request state. | Modify | Attach only consumed routing metadata; actor and session identity come from authenticated context, not optional headers. | Prevents duplicate identity sources. |
| `UIAPI-FR-040` | `GET /api/health` shall be unauthenticated and shall return HTTP 200 with a minimal service status payload when the API process is accepting requests. It shall not expose secrets, credentials, broker account data, or private dependency details. | Modify | Expose public liveness and a separate readiness/degraded view; never claim healthy after failed required startup work. | V1 constant health is misleading. |
| `UIAPI-FR-041` | `api.app.create_app` shall build the migration-era operator API with dependency injection, CORS, operator auth middleware, operator metadata routes, health routes, approval routes, and event-stream routes. | Reject | Do not retain a second operator FastAPI app as the final architecture; merge routes into the canonical app. | V1 split composition creates duplicated auth, health, and deployment behavior. |
| `UIAPI-FR-042` | `get_operator_api_dependencies` shall expose the operator dependency container to route handlers. | Reject | Use normal canonical-app dependency injection instead of a separate operator-app state accessor. | This requirement exists only because of the rejected second app. |
| `UIAPI-FR-043` | `generate_token` shall create a single active user session token, invalidate existing sessions for that user, and set a 24-hour duration. | Modify | Preserve single-session replacement, but make token lifetime configurable and approve the final browser token transport. | The 24-hour literal and token storage policy are security decisions. |
| `UIAPI-FR-044` | `verify_token` shall validate stored sessions, parse expiration timestamps, delete expired sessions, and return the user id only for valid sessions. | Modify | Validate expiry, session revocation, and current user active status; delete expired sessions. | V1 lacks evidence of post-issue account revocation checks. |
| `UIAPI-FR-045` | `invalidate_token` shall delete a stored session token. | Keep | Invalidate the persisted session token on logout. | Proven V1 behavior. |
| `UIAPI-FR-046` | `authenticate_user` shall authenticate username/password, reject invalid or inactive users, distinguish unverified users, update last login for verified users, and return user metadata. | Modify | Preserve credential/account-state checks with normalized errors, rate limits, and secret-safe logging. | V1 behavior is useful but needs boundary hardening. |
| `UIAPI-FR-047` | `get_user_id_from_token` shall require an Authorization header, accept optional Bearer prefix, verify the token, and raise 401 for missing, invalid, or expired tokens. | Modify | Require the standard Bearer scheme and reject raw token values; return the standard 401 envelope. | Optional raw-token acceptance is unnecessary ambiguity. |
| `UIAPI-FR-048` | `OperatorAuthMiddleware` shall protect all `/api/operator` routes except explicitly public documentation and health routes. | Modify | Protect operator routes through the canonical auth/authorization middleware; only explicit liveness/docs routes may be public. | Separate operator middleware is retained only as behavior, not architecture. |
| `UIAPI-FR-049` | `GET /api/operator/events/stream` shall require an authenticated operator principal with an allowed operator role unless a separately documented redacted public health-only stream is explicitly configured. | Add | Require validated operator authentication and role/permission checks for the event stream. | V1 stream is public. |
| `UIAPI-FR-050` | Public operator routes shall be limited to documentation and health endpoints and shall never expose approval, policy, actor, live-execution, broker, incident, or private system data. | Keep | Limit public operator information to coarse liveness/docs metadata. | Valid least-privilege boundary. |
| `UIAPI-FR-051` | A redacted public health-only stream shall not exist unless approved by owner/security decision. If approved, it may expose only static service name, coarse health state, heartbeat timestamp, and public schema version, and must not reuse the protected operator event stream path unless explicitly documented. | Reject | Do not create a public health stream in the initial rebuild. | No confirmed workflow requires it and it adds exposure/maintenance. |
| `UIAPI-FR-052` | `OperatorPrincipal` shall represent token, actor id, and role extracted from operator request headers. | Modify | Represent actor id, roles, permissions, and validated token/session claims in one principal; do not trust caller-supplied role headers. | V1 principal is insecure and too narrow. |
| `UIAPI-FR-053` | `get_operator_principal` shall return the authenticated operator principal or raise 401. | Modify | Return the canonical authenticated principal or 401. | Merge user/operator identity handling. |
| `UIAPI-FR-054` | `require_operator_role` shall enforce allowed operator roles and raise 403 when unauthorized. | Keep | Enforce required roles/permissions and return 403 when unauthorized. | Core authorization behavior is necessary. |
| `UIAPI-FR-055` | Operator roles shall be limited to `operator`, `approver`, and `admin`. | Modify | Approve a permission model; do not hard-code the final system to only three role strings until governance roles are reconciled. | The requirements also reference risk/compliance approval roles. |
| `UIAPI-FR-056` | `SecretRedactionMiddleware` shall redact request headers and query parameters before debug logging. | Modify | Redact sensitive values and log only allowlisted headers/query metadata. | Logging every sanitized header still creates unnecessary data exposure. |
| `UIAPI-FR-057` | API request logs shall include sanitized method, path, headers, and query metadata. | Modify | Log method/path plus allowlisted sanitized metadata, not complete request headers by default. | Minimizes privacy and secret risk. |
| `UIAPI-FR-058` | `IntentClassifier` shall classify request intent from the URL path and optional session header. | Modify | Classify route intent from the route registry; obtain session/actor from authenticated request context. | Avoids header-derived identity duplication. |
| `UIAPI-FR-059` | Routing metadata shall include intent, priority, session id, and user id fields. | Modify | Include request/correlation id, intent, actor and session when available; retain priority only if a real consumer exists. | V1 priority metadata has no demonstrated workflow. |
| `UIAPI-FR-060` | `GET /api/operator` shall return operator API metadata, environment, schema registry contract count, policy bundle count, actor id, and role. | Defer | Defer a dedicated operator metadata endpoint; expose only information required by the operator UI after its contract is approved. | Not essential to the initial rebuild. |
| `UIAPI-FR-061` | `GET /api/operator/health` shall return aggregate app, database, Redis, and schema-registry health. | Modify | Provide protected detailed readiness information under the canonical health capability. | Avoid a second health model. |
| `UIAPI-FR-062` | `GET /api/operator/health/db` shall return database health. | Merge | Merge database health into one protected readiness response with optional component detail. | Separate probe endpoints are unnecessary initially. |
| `UIAPI-FR-063` | `GET /api/operator/health/redis` shall return Redis health. | Merge | Report Redis only when configured and merge it into protected readiness. | V1 probe is a placeholder. |
| `UIAPI-FR-064` | `GET /api/operator/health/schema-registry` shall return schema-registry health. | Merge | Merge schema-registry status into protected readiness using its public API. | Avoid private-field coupling and route proliferation. |
| `UIAPI-FR-065` | `POST /api/operator/live-execution` shall create a live-execution approval request. | Modify | Keep live-execution approval creation under `/api/operator/approvals/live-execution` with canonical auth, audit, and idempotency. | Aligns with V1 route registration and a coherent approval namespace. |
| `UIAPI-FR-066` | `POST /api/operator/policy-change` shall create a policy-change approval request. | Modify | Keep policy-change approval under the approvals namespace with dual authorization. | Preserves V1 value with a consistent contract. |
| `UIAPI-FR-067` | `POST /api/operator/override` shall create an override approval request. | Modify | Keep override approval under the approvals namespace with validated original references and audit. | Preserves governed workflow. |
| `UIAPI-FR-068` | `POST /api/operator/kill-switch-recovery` shall create a kill-switch recovery approval request. | Modify | Keep kill-switch-recovery approval under the approvals namespace with approved permissions and incident linkage. | Safety-critical workflow needs stronger context. |
| `UIAPI-FR-069` | `POST /api/operator/live-execution/{approval_id}/votes` shall record a vote on a live-execution approval. | Modify | Keep voting under the approval resource with canonical identity, duplicate-vote rules, and idempotency. | V1 behavior is valuable but under-specified. |
| `UIAPI-FR-070` | `GET /api/operator/events/stream` shall stream operator events only through the approved operator stream contract, auth policy, redaction policy, heartbeat policy, and disconnect cleanup policy. | Add | Replace sample SSE with a protected authoritative operator event stream and documented lifecycle. | V1 static public events have no final value. |
| `UIAPI-FR-071` | `POST /api/auth/register` shall register a user account. | Modify | Preserve the auth endpoint behavior with canonical identity contracts, standard envelopes, rate limits, and tests. | V1 provides the workflow but not the final contract/security baseline. |
| `UIAPI-FR-072` | `POST /api/auth/login` shall authenticate a user and return an auth response. | Modify | Preserve the auth endpoint behavior with canonical identity contracts, standard envelopes, rate limits, and tests. | V1 provides the workflow but not the final contract/security baseline. |
| `UIAPI-FR-073` | `POST /api/auth/logout` shall invalidate the caller's session token. | Modify | Preserve the auth endpoint behavior with canonical identity contracts, standard envelopes, rate limits, and tests. | V1 provides the workflow but not the final contract/security baseline. |
| `UIAPI-FR-074` | `GET /api/settings/` shall return settings for the authenticated user. | Modify | Preserve authenticated settings read/update with ownership, standard envelopes, and no duplicate token parser. | V1 behavior is useful but duplicated and inconsistent. |
| `UIAPI-FR-075` | `GET /api/settings` shall return settings without requiring a trailing slash. | Reject | Publish one canonical settings path and rely on an explicit redirect policy if compatibility is needed. | Duplicate slash/no-slash handlers add no business value. |
| `UIAPI-FR-076` | `PUT /api/settings/` shall update settings for the authenticated user. | Modify | Preserve authenticated settings read/update with ownership, standard envelopes, and no duplicate token parser. | V1 behavior is useful but duplicated and inconsistent. |
| `UIAPI-FR-077` | `GET /api/ai-chat/threads` shall list AI chat threads. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-078` | `POST /api/ai-chat/threads` shall create an AI chat thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-079` | `GET /api/ai-chat/threads/{thread_id}` shall return thread detail. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-080` | `PATCH /api/ai-chat/threads/{thread_id}` shall rename a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-081` | `PATCH /api/ai-chat/threads/{thread_id}/context` shall update thread page context. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-082` | `DELETE /api/ai-chat/threads/{thread_id}` shall delete a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-083` | `POST /api/ai-chat/threads/{thread_id}/archive` shall archive a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-084` | `POST /api/ai-chat/threads/{thread_id}/restore` shall restore a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-085` | `POST /api/ai-chat/threads/{thread_id}/purge` shall purge a thread where allowed. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-086` | `GET /api/ai-chat/threads/{thread_id}/retention` shall return thread retention detail. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-087` | `PATCH /api/ai-chat/threads/{thread_id}/retention` shall update thread retention class. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-088` | `POST /api/ai-chat/retention/lifecycle-run` shall run retention lifecycle processing. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-089` | `GET /api/ai-chat/threads/{thread_id}/export` shall export a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-090` | `POST /api/ai-chat/threads/{thread_id}/messages` shall create a chat message. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-091` | `GET /api/ai-chat/tools` shall list AI chat tools. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-092` | `POST /api/ai-chat/context/resolve` shall resolve page context. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-093` | `GET /api/ai-chat/threads/{thread_id}/signal-proposals` shall list signal proposals linked to a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-094` | `POST /api/ai-chat/threads/{thread_id}/signal-proposals/{proposal_id}/watchlist` shall save a signal proposal to the watchlist. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-095` | `POST /api/ai-chat/threads/{thread_id}/signal-proposals/{proposal_id}/review-queue` shall queue a signal proposal for review. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-096` | `GET /api/ai-chat/threads/{thread_id}/action-drafts` shall list action drafts linked to a thread. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-097` | `POST /api/ai-chat/threads/{thread_id}/action-drafts/{draft_id}/request-approval` shall request approval for an action draft. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-098` | `POST /api/ai-chat/threads/{thread_id}/action-drafts/{draft_id}/paper-execute` shall execute an action draft only in the approved paper path. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-099` | `POST /api/ai-chat/threads/{thread_id}/responses/stream` shall stream an AI chat response. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-100` | `POST /api/ai-chat/threads/{thread_id}/responses/regenerate` shall regenerate an AI chat response. | Modify | Preserve the AI-chat capability through the canonical principal, typed conversation APIs, bounded context, audit for destructive/governed actions, and documented streaming. | V1 provides substantial behavior but uses a development identity and mixed governance. |
| `UIAPI-FR-101` | `GET /api/strategies/templates/{template_name}` shall return a strategy template. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-102` | `POST /api/strategies/` shall create a strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-103` | `GET /api/strategies/` shall list strategies. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-104` | `GET /api/strategies/{strategy_id}` shall return one strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-105` | `PUT /api/strategies/{strategy_id}` shall update a strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-106` | `DELETE /api/strategies/{strategy_id}` shall delete a strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-107` | `GET /api/strategies/{strategy_id}/versions` shall list strategy versions. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-108` | `GET /api/strategies/{strategy_id}/versions/{version_id}/code` shall return version code. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-109` | `POST /api/strategies/{strategy_id}/versions/{version_id}/rollback` shall roll a strategy back to a version. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-110` | `POST /api/strategies/{strategy_id}/export` shall export a strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-111` | `POST /api/strategies/{strategy_id}/import` shall import a strategy. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-112` | `POST /api/sqx/import` shall import SQX strategies. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-113` | `POST /api/sqx/calculate-scores` shall validate and authorize the request, delegate SQX score calculation to the approved strategy or analytics service, and return the service result. | Add | Add authorized SQX score calculation only through the owning strategy/analytics domain. | This final behavior is not confirmed in the V1 capability catalogue. |
| `UIAPI-FR-114` | `GET /api/sqx/strategies` shall list imported SQX strategies. | Modify | Preserve strategy/SQX behavior as a thin authenticated boundary with upload limits, ownership, versioning, and compensating failure rules. | V1 is valuable but mixes DB, filesystem, governance, and route logic. |
| `UIAPI-FR-115` | `POST /api/backtest/run/{strategy_id}` shall validate and authorize the request, delegate backtest execution to the approved simulation service, and return the service result. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-116` | `GET /api/backtest/strategy/{strategy_id}` shall list backtests for a strategy. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-117` | `GET /api/backtest/{backtest_id}` shall return a backtest. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-118` | `GET /api/backtest/{backtest_id}/overview` shall return a backtest overview. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-119` | `GET /api/backtest/` shall list all backtests. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-120` | `PUT /api/backtest/{backtest_id}` shall update backtest metadata. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-121` | `DELETE /api/backtest/{backtest_id}` shall delete a backtest. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-122` | `POST /api/backtest/portfolio/run/{strategy_id}` shall validate and authorize the request, delegate portfolio backtest execution to the approved simulation or analytics service, and return the service result. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-123` | `WEBSOCKET /api/backtest/ws/{backtest_id}/logs` shall stream backtest logs. | Modify | Preserve the backtest route behavior while delegating execution/persistence/analytics to simulation and exposing authenticated typed results or a documented stream. | V1 route-local orchestration is oversized and reverses dependencies. |
| `UIAPI-FR-124` | `POST /api/simulator/start` shall start a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-125` | `GET /api/simulator/sessions` shall list simulation sessions. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-126` | `GET /api/simulator/paused` shall list paused simulation sessions. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-127` | `GET /api/simulator/{session_id}` shall return one simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-128` | `PUT /api/simulator/{session_id}` shall update a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-129` | `GET /api/simulator/{session_id}/bar/{bar_index}` shall return one bar from a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-130` | `POST /api/simulator/{session_id}/advance` shall advance a simulation by bars. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-131` | `GET /api/simulator/{session_id}/positions` shall return session positions. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-132` | `POST /api/simulator/{session_id}/trade` shall execute a simulated trade. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-133` | `POST /api/simulator/{session_id}/trade/preview` shall preview a simulated trade. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-134` | `POST /api/simulator/{session_id}/order/pending` shall place a simulated pending order. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-135` | `POST /api/simulator/{session_id}/what-if` shall evaluate a simulation what-if action. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-136` | `PATCH /api/simulator/{session_id}/positions/{position_id}` shall modify a simulated position. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-137` | `DELETE /api/simulator/{session_id}/positions/{position_id}` shall close a simulated position. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-138` | `POST /api/simulator/{session_id}/positions/{position_id}/partial` shall partially close a simulated position. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-139` | `PATCH /api/simulator/{session_id}/orders/{order_id}` shall modify a simulated order. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-140` | `DELETE /api/simulator/{session_id}/orders/{order_id}` shall delete a simulated order. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-141` | `POST /api/simulator/{session_id}/resume` shall resume a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-142` | `POST /api/simulator/{session_id}/seek` shall seek a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-143` | `GET /api/simulator/{session_id}/trades` shall list simulation trades. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-144` | `POST /api/simulator/{session_id}/seek-trade` shall seek to a trade. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-145` | `DELETE /api/simulator/{session_id}` shall delete a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-146` | `POST /api/simulator/{session_id}/stop-and-save` shall stop and save a simulation session. | Modify | Preserve the simulator operation as a thin authenticated call to a simulation runtime that owns state, leases, risk, and mutation behavior. | V1 workflow is valuable but the API package owns too much runtime/domain logic. |
| `UIAPI-FR-147` | `POST /api/risk/position-sizing` shall validate and authorize the request, delegate risk-based position sizing to the approved risk-domain service, and return the service result through the documented API response schema without implementing risk calculation logic in the UI/API layer. | Modify | Preserve the risk endpoint and delegate all calculations/state construction to the risk domain through typed contracts. | V1 route files contain domain adapters and computation orchestration. |
| `UIAPI-FR-148` | `POST /api/risk/regime-detection` shall validate and authorize the request, delegate regime detection to the approved risk-domain service, and return the service result through the documented API response schema. | Modify | Preserve the risk endpoint and delegate all calculations/state construction to the risk domain through typed contracts. | V1 route files contain domain adapters and computation orchestration. |
| `UIAPI-FR-149` | `POST /api/risk/allocation` shall validate and authorize the request, delegate risk allocation to the approved risk-domain service, and return the service result through the documented API response schema. | Modify | Preserve the risk endpoint and delegate all calculations/state construction to the risk domain through typed contracts. | V1 route files contain domain adapters and computation orchestration. |
| `UIAPI-FR-150` | `POST /api/risk/governance` shall validate and authorize the request, delegate risk governance evaluation to the approved risk-domain service, and return the service result through the documented API response schema. | Modify | Preserve the risk endpoint and delegate all calculations/state construction to the risk domain through typed contracts. | V1 route files contain domain adapters and computation orchestration. |
| `UIAPI-FR-151` | `POST /api/live/sessions` shall create a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-152` | `GET /api/live/sessions` shall list live sessions. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-153` | `GET /api/live/sessions/{session_id}` shall return one live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-154` | `PUT /api/live/sessions/{session_id}` shall update a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-155` | `DELETE /api/live/sessions/{session_id}` shall delete a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-156` | `POST /api/live/sessions/{session_id}/start` shall start a live session only through live-session controls. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-157` | `POST /api/live/sessions/{session_id}/stop` shall stop a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-158` | `POST /api/live/sessions/{session_id}/pause` shall pause a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-159` | `POST /api/live/sessions/{session_id}/resume` shall resume a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-160` | `GET /api/live/sessions/{session_id}/status` shall return live session status. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-161` | `GET /api/live/sessions/{session_id}/statistics` shall return live session statistics. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-162` | `GET /api/live/sessions/{session_id}/market-data` shall return live session market data. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-163` | `GET /api/live/sessions/{session_id}/signals` shall return live session signals. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-164` | `GET /api/live/sessions/{session_id}/positions` shall return live session positions. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-165` | `GET /api/live/sessions/{session_id}/logs` shall return live session logs. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-166` | `POST /api/live/sessions/{session_id}/strategies` shall add a strategy to a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-167` | `DELETE /api/live/sessions/{session_id}/strategies/{strategy_config_id}` shall remove a strategy from a live session. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-168` | `GET /api/live/sessions/{session_id}/strategies` shall list live session strategies. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-169` | `PUT /api/live/sessions/{session_id}/positions/{position_id}` shall request live position modification through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-170` | `POST /api/live/sessions/{session_id}/orders` shall request manual live order creation through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-171` | `GET /api/live/sessions/{session_id}/orders` shall return live session orders. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-172` | `DELETE /api/live/sessions/{session_id}/orders/{ticket}` shall request live order cancellation through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-173` | `POST /api/live/sessions/{session_id}/orders/pending` shall request pending live order creation through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-174` | `DELETE /api/live/sessions/{session_id}/positions/{position_id}` shall request live position closure through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-175` | `POST /api/live/sessions/{session_id}/positions/close-all` shall request closing all live positions through the live route. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-176` | `WEBSOCKET /api/live/sessions/{session_id}/ws` shall stream live session events. | Modify | Preserve the live operation behind explicit live enablement, authenticated ownership, risk/approval/reconciliation/idempotency/audit gates, and live-domain delegation. | V1 surface is valuable but runtime and broker safety are unverified and route-local. |
| `UIAPI-FR-177` | `POST /api/optimization/runs` shall validate and authorize the request, delegate bounded run creation to the approved optimization service, and return the run contract without implementing optimization algorithms in the UI/API layer. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-178` | `GET /api/optimization/runs/{optimization_id}` shall return optimization run detail. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-179` | `GET /api/optimization/runs/{optimization_id}/results` shall return optimization results. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-180` | `DELETE /api/optimization/runs/{optimization_id}` shall cancel an optimization run. | Modify | Cancellation must signal the active job and persist a reconciled terminal state, not only update a database flag. | V1 cancellation is incomplete. |
| `UIAPI-FR-181` | `POST /api/optimization/walk-forward` shall validate and authorize the request, delegate walk-forward analysis to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-182` | `POST /api/optimization/unsupervised-analysis` shall validate and authorize the request, delegate unsupervised analysis to the approved optimization or research service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-183` | `GET /api/optimization/runs/{optimization_id}/unsupervised-report` shall return an unsupervised report. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-184` | `POST /api/optimization/monte-carlo` shall validate and authorize the request, delegate Monte Carlo simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-185` | `GET /api/optimization/monte-carlo/{simulation_id}` shall return a Monte Carlo result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-186` | `POST /api/optimization/monte-carlo/parametric` shall validate and authorize the request, delegate parametric Monte Carlo to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-187` | `POST /api/optimization/monte-carlo/position-sizing` shall validate and authorize the request, delegate position-sizing simulation to the approved optimization or risk service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-188` | `POST /api/optimization/monte-carlo/consecutive-losing` shall validate and authorize the request, delegate consecutive-losing simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-189` | `POST /api/optimization/monte-carlo/profit-target` shall validate and authorize the request, delegate profit-target simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-190` | `POST /api/optimization/monte-carlo/random-win-rate` shall validate and authorize the request, delegate random-win-rate simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-191` | `POST /api/optimization/monte-carlo/robustness` shall validate and authorize the request, delegate robustness simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-192` | `POST /api/optimization/monte-carlo/multi-entry` shall validate and authorize the request, delegate multi-entry simulation to the approved optimization service, and return the service result. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-193` | `WEBSOCKET /api/optimization/ws/{optimization_id}` shall stream optimization progress. | Modify | Preserve the optimization/scenario behavior through authenticated bounded jobs, domain delegation, typed results, and documented progress streams. | V1 provides useful behavior but route handlers own too much orchestration and identity defaults. |
| `UIAPI-FR-194` | `GET /api/dashboard/broker` shall return broker status. | Modify | Keep broker status as a read-only facade with freshness and provider-state metadata. | V1 shares a mutable client. |
| `UIAPI-FR-195` | `GET /api/dashboard/equity-curve` shall return dashboard equity curve data. | Modify | Keep equity-curve data with typed pagination/bounds and analytics ownership. | Valuable dashboard workflow. |
| `UIAPI-FR-196` | `GET /api/dashboard/summary` shall return dashboard summary data. | Modify | Keep dashboard summary with a documented snapshot timestamp and stale state. | Valuable read workflow. |
| `UIAPI-FR-197` | `GET /api/dashboard/system/status` shall return system status. | Merge | Merge system status with the canonical operational health/status capability. | Avoid overlapping meanings. |
| `UIAPI-FR-198` | `GET /api/dashboard/system/resources` shall return resource usage. | Modify | Keep protected resource metrics with bounded details and no sensitive host data. | Useful operator/dashboard behavior. |
| `UIAPI-FR-199` | `GET /api/dashboard/market-hours` shall return market-hours data. | Modify | Keep market-hours data with timezone/DST/holiday correctness. | V1 behavior is useful but needs edge-case contracts. |
| `UIAPI-FR-200` | `GET /api/dashboard/currency-strength` shall remain optional/deferred until its schema, source service, stale-data behavior, and frontend contract are finalized. | Defer | Exclude currency strength from the initial rebuild until source, schema, freshness, and UI workflow are approved. | V2 itself marks it optional and V1 runtime value is unverified. |
| `UIAPI-FR-201` | `GET /api/dashboard/forex-calendar` shall return forex-calendar data. | Modify | Keep forex calendar with provider-unavailable, stale, and empty-result behavior. | External provider status is unverified. |
| `UIAPI-FR-202` | `GET /api/docs/files` shall return documentation file tree data. | Modify | Keep documentation tree listing as an authenticated developer/operator capability. | V1 exposes local filesystem data without evidenced auth. |
| `UIAPI-FR-203` | `GET /api/docs/content` shall return documentation file content. | Modify | Keep documentation read with root/path/content controls. | Useful internal workflow. |
| `UIAPI-FR-204` | `POST /api/docs/save` shall save documentation content. | Modify | Keep documentation save only for authorized developer/operator roles with audit, idempotency, size and path safety. | V1 write surface is unsafe if public. |
| `UIAPI-FR-205` | `DELETE /api/docs/delete` shall delete documentation content. | Modify | Keep documentation delete only for authorized developer/operator roles with audit and path safety. | V1 deletion lacks evidenced auth. |
| `UIAPI-FR-206` | `GET /api/data/symbols` shall return available market-data symbols. | Modify | Keep market symbol discovery with canonical auth and no default-user fallback. | V1 fallback can expose another user’s broker context. |
| `UIAPI-FR-207` | `POST /api/data/dataset/prepare` shall validate and authorize the request, delegate generic dataset preparation to the approved data or research service, and return the service result. | Modify | Keep dataset preparation as a delegated data/research operation with bounded response size and ownership. | V1 route performs domain preparation inline. |
| `UIAPI-FR-208` | `POST /api/edge-lab/run` shall validate and authorize the request, delegate Edge Lab analysis to approved Edge Lab or research services, and return the service result without implementing research algorithms in the UI/API layer. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-209` | `GET /api/edge-lab/runs` shall list Edge Lab runs. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-210` | `GET /api/edge-lab/runs/count` shall count Edge Lab runs. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-211` | `GET /api/edge-lab/runs/summary` shall return Edge Lab run summary. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-212` | `POST /api/edge-lab/dataset/prepare` shall validate and authorize the request, delegate Edge Lab-specific dataset preparation to the approved Edge Lab or data service, and return the service result. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-213` | `POST /api/edge-lab/seasonality` shall validate and authorize the request, delegate seasonality analysis to the approved research service, and return the service result. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-214` | `GET /api/edge-lab/runs/{run_id}` shall return an Edge Lab run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-215` | `GET /api/edge-lab/runs/{run_id}/stats` shall return Edge Lab run statistics. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-216` | `GET /api/edge-lab/runs/{run_id}/trades` shall return Edge Lab run trades. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-217` | `DELETE /api/edge-lab/runs/{run_id}` shall delete an Edge Lab run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-218` | `POST /api/edge-lab/core-metrics/run` shall validate and authorize the request, delegate core metric calculation to the approved research or analytics service, and return the service result. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-219` | `GET /api/edge-lab/core-metrics/runs` shall list core metric runs. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-220` | `GET /api/edge-lab/core-metrics/runs/{run_id}` shall return a core metric run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-221` | `DELETE /api/edge-lab/core-metrics/runs/{run_id}` shall delete a core metric run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-222` | `POST /api/edge-lab/market-structure/run` shall validate and authorize the request, delegate market-structure analysis to the approved research service, and return the service result. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-223` | `POST /api/edge-lab/unsupervised-structure/run` shall validate and authorize the request, delegate unsupervised-structure analysis to the approved research service, and return the service result. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-224` | `GET /api/edge-lab/market-structure/runs` shall list market-structure runs. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-225` | `GET /api/edge-lab/market-structure/runs/{run_id}` shall return a market-structure run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-226` | `DELETE /api/edge-lab/market-structure/runs/{run_id}` shall delete a market-structure run. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-227` | `GET /api/edge-lab/market-structure/validation` shall return market-structure validation. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-228` | `GET /api/edge-lab/market-structure/evaluations` shall list market-structure evaluations. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-229` | `POST /api/edge-lab/market-structure/evaluations/refresh` shall refresh market-structure evaluations. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-230` | `GET /api/edge-lab/market-structure/calibration` shall return market-structure calibration. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-231` | `GET /api/edge-lab/market-structure/profile-calibration` shall return profile calibration. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-232` | `GET /api/edge-lab/market-structure/metric-calibration` shall return metric calibration. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-233` | `POST /api/edge-lab/market-structure/stability` shall validate and authorize the request, delegate stability analysis to the approved research service, and return the service result. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-234` | `POST /api/edge-lab/market-structure/robustness` shall validate and authorize the request, delegate robustness analysis to the approved research service, and return the service result. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-235` | `POST /api/edge-lab/automation/run` shall validate and authorize the request, delegate Edge Lab automation to the approved orchestration service, and return the service result. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-236` | `POST /api/edge-lab/automation/batch` shall validate and authorize the request, delegate Edge Lab automation batch work to the approved orchestration service, and return the service result. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-237` | `POST /api/edge-lab/automation/refresh` shall refresh Edge Lab automation schedule. | Defer | Postpone advanced validation/calibration/stability/robustness and automation endpoints until usage, ownership, and an end-to-end workflow are confirmed. | The initial rebuild should retain the core research path and avoid reproducing the oversized V1 route surface. |
| `UIAPI-FR-238` | `POST /api/edge-lab/scorecard/snapshots` shall save a scorecard snapshot. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-239` | `GET /api/edge-lab/scorecard/snapshots` shall list scorecard snapshots. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-240` | `GET /api/edge-lab/scorecard/snapshots/{snapshot_id}` shall return a scorecard snapshot. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-241` | `GET /api/edge-lab/scorecard/snapshots/compare` shall compare scorecard snapshots. | Modify | Preserve the core Edge Lab run/result/profile/snapshot behavior as thin authenticated calls to research/data services with typed contracts. | V1 demonstrates useful research capability but route logic is oversized and runtime is unverified. |
| `UIAPI-FR-242` | `POST /api/edge-lab/scorecard/snapshots/{snapshot_id}/export-parquet` shall export a scorecard snapshot to Parquet. | Defer | Postpone specialized Parquet/report export endpoints; retain snapshot data and add export only when a consuming workflow is confirmed. | Artifact export formats are not essential to the initial boundary. |
| `UIAPI-FR-243` | `GET /api/edge-lab/scorecard/snapshots/{snapshot_id}/report` shall return a scorecard snapshot report. | Defer | Postpone specialized Parquet/report export endpoints; retain snapshot data and add export only when a consuming workflow is confirmed. | Artifact export formats are not essential to the initial boundary. |
| `UIAPI-FR-244` | `POST /api/edge-lab/scorecard/snapshots/{snapshot_id}/export-report` shall export a scorecard snapshot report. | Defer | Postpone specialized Parquet/report export endpoints; retain snapshot data and add export only when a consuming workflow is confirmed. | Artifact export formats are not essential to the initial boundary. |
| `UIAPI-FR-245` | `POST /api/edge-lab/scorecard/snapshots/compare/export-markdown` shall export scorecard snapshot comparison Markdown. | Defer | Postpone specialized Parquet/report export endpoints; retain snapshot data and add export only when a consuming workflow is confirmed. | Artifact export formats are not essential to the initial boundary. |
| `UIAPI-FR-246` | The frontend shall provide authentication routes `/login` and `/register`. | Add | Provide login and registration pages tied to the canonical auth contract. | Required for the confirmed user-auth workflow. |
| `UIAPI-FR-247` | The frontend shall provide dashboard-level routes for `/`, `/agents`, `/ai-ceo`, `/audit`, `/backtests`, `/board-room`, `/chart/[[...slug]]`, `/costs`, `/execution`, `/live`, `/optimization`, `/portfolio`, `/research`, `/risk-center`, `/settings`, `/strategies`, `/strategies/[id]`, `/strategy-lab`, `/tools`, and `/tools/currency-strength`. | Modify | Initial frontend scope includes dashboard, AI chat, strategies, backtests, simulation, risk, live, optimization and settings; defer agents, board-room, costs, audit and optional tools until their workflows are approved. | The proposed route list is broader than V1 evidence. |
| `UIAPI-FR-248` | The frontend shall provide documentation routes under `/documentation`, `/documentation/manage`, `/documentation/fundamentals/*`, `/documentation/development/*`, and `/documentation/robustness/*`. | Modify | Provide a documentation viewer and restricted editor; generate content navigation rather than hard-coding many hierarchy routes. | Keeps the workflow with less route complexity. |
| `UIAPI-FR-249` | The frontend shall provide Edge Lab routes under `/edge-lab`, including automation, core metric, discovery, edge profile, market structure, Monte Carlo lab, scorecard, seasonality, SQX import, and unsupervised structure. | Modify | Provide core Edge Lab pages aligned to approved backend capabilities; defer automation and specialized labs with their APIs. | Matches the reduced research scope. |
| `UIAPI-FR-250` | The frontend shall provide simulation routes under `/simulation`, including batch auto, manual, replay, visual auto, replay backtest detail, and replay trade detail. | Modify | Provide manual/replay simulator workflows first; defer batch-auto variants until a confirmed workflow exists. | Reduces initial UI surface. |
| `UIAPI-FR-251` | The frontend shall provide performance routes under `/performance`, including overview, metaparams, chart analysis, strategy analysis, trade analysis, trades calendar, and periodical analysis pages. | Defer | Defer the broad performance-page suite to the analytics/UI roadmap. | No V1 API audit evidence demonstrates these pages are required for the initial rebuild. |
| `UIAPI-FR-252` | The frontend shall provide live, simulation, risk, strategy, Edge Lab, dashboard, documentation, AI chat, and performance components that render backend data without owning backend business rules. | Modify | Build only components needed by approved workflows and keep domain rules server-side. | The behavior is valid; the full component catalogue is premature. |
| `UIAPI-FR-253` | `request` shall call the configured API URL, attach JSON content type, attach the local auth bearer token when present, parse JSON error details, support 204 responses, and return parsed JSON data. | Add | Create one typed request primitive with configured base URL, auth attachment, safe JSON/error parsing, and 204 support. | No V1 frontend-client evidence was available. |
| `UIAPI-FR-254` | `agenticApiRequest` shall create request and trace ids, attach headers, validate governed writes before sending, execute the fetch, parse payloads, validate contracts when a schema is supplied, track telemetry, and return an envelope with data, request id, trace id, stale flag, and stale warning. | Merge | Fold request IDs, tracing, validation, telemetry and stale metadata into the same typed request primitive with governed options. | A second parallel request stack would duplicate behavior. |
| `UIAPI-FR-255` | `agenticApiData` shall return only the data portion of `agenticApiRequest`. | Merge | Expose a small data-unwrapping helper only if needed; do not create a second transport abstraction. | Avoids API-client duplication. |
| `UIAPI-FR-256` | `governedWriteContext` shall construct governed write options with workflow id, approval id, required permission, audit event type, and optional board or critical-incident approval ids. | Modify | Represent governed-write context as typed request options; include only approved workflow/permission/approval fields. | Board/critical-incident fields are cross-domain decisions. |
| `UIAPI-FR-257` | `AgenticApiError` shall carry message, request id, trace id, and status for failed API calls. | Add | Use one typed API error carrying status, code, request id, trace id, retryability and bounded details. | Required for reliable UI error handling. |
| `UIAPI-FR-258` | Governed frontend writes shall be blocked before request when required request id, workflow id, approval id, server permission check, CSRF token, audit intent, or required approval context is missing. | Modify | Block missing client context as UX protection, but never treat cached permission checks as authoritative. | Backend enforcement remains decisive. |
| `UIAPI-FR-259` | Read-only GET requests may retry once when enabled and not governed. | Add | Allow at most one opt-in retry for idempotent reads on classified transient failures. | Useful resilience with bounded risk. |
| `UIAPI-FR-260` | Stale API responses shall emit telemetry and include a stale warning. | Add | Expose stale metadata/warnings and block governed decisions until refresh. | Required safety behavior. |
| `UIAPI-FR-261` | Frontend API clients shall expose typed access for AI chat, backtest, data, docs, Edge Lab, live, optimization, risk, simulator, strategies, trades, audit, board, cost, evidence, execution, portfolio, research, settings, and workflow domains. | Modify | Provide typed clients only for approved initial route groups; defer audit/board/cost/evidence clients. | The proposed client catalogue exceeds confirmed scope. |
| `UIAPI-FR-262` | `listAiChatThreads` shall list AI chat threads through the frontend AI chat client. | Add | Add typed AI-chat list behavior through the shared request primitive. | Supports an approved workflow. |
| `UIAPI-FR-263` | `streamAiChatResponse` shall stream AI chat responses through the frontend AI chat client. | Add | Add typed AI-chat streaming behavior using the approved stream contract. | Supports an approved workflow. |
| `UIAPI-FR-264` | `backtestApi` shall expose frontend backtest operations. | Add | Add a focused backtest client mapped to approved contracts. | Supports an approved workflow. |
| `UIAPI-FR-265` | `marketDataApi` shall expose frontend market-data operations. | Add | Add a focused market-data client mapped to approved contracts. | Supports an approved workflow. |
| `UIAPI-FR-266` | `edgeLabApi` shall expose frontend Edge Lab operations. | Add | Add a focused Edge Lab client for non-deferred routes. | Supports an approved workflow. |
| `UIAPI-FR-267` | `LiveTradingAPI` shall expose frontend live-trading operations. | Add | Add a focused live client with governed mutation options. | Supports an approved workflow. |
| `UIAPI-FR-268` | `optimizationApi` shall expose frontend optimization operations. | Add | Add a focused optimization client for approved routes. | Supports an approved workflow. |
| `UIAPI-FR-269` | `riskApi` shall expose frontend risk operations. | Add | Add a focused risk client. | Supports an approved workflow. |
| `UIAPI-FR-270` | `simulatorApi` shall expose frontend simulator operations. | Add | Add a focused simulator client. | Supports an approved workflow. |
| `UIAPI-FR-271` | `strategyApi` shall expose frontend strategy operations. | Add | Add a focused strategy client. | Supports an approved workflow. |
| `UIAPI-FR-272` | `tradesApi` shall expose frontend trade-data operations. | Defer | Do not add a standalone trades client until a distinct trade-data route contract is approved; use backtest/live/simulator clients meanwhile. | V1 trade-import route is disconnected and no standalone final trade API is confirmed. |
| `UIAPI-FR-273` | Frontend contract validators shall validate agentic and generic API contracts before data is trusted by UI workflows. | Add | Validate response contracts before governed or complex UI workflows consume data. | Prevents API/UI drift. |
| `UIAPI-FR-274` | Page context providers and hooks shall register current page context and actions for AI chat and route-aware workflows. | Add | Provide bounded, redacted page context registration for approved AI-chat workflows. | V1 chat context exists server-side; frontend behavior is missing from audit evidence. |
| `UIAPI-FR-275` | AI chat UI shall include launcher, panel, header, input, message list, action-plan preview, CEO status badge, route labels, page-intelligence blocks, and semantic snapshot support. | Modify | Build the core chat launcher/panel/messages/action preview first; defer decorative status and semantic-snapshot features until required. | The proposed component set is broader than the core workflow. |
| `UIAPI-FR-276` | Protected dashboard layouts shall prevent unauthenticated use of protected workflows. | Add | Protect authenticated frontend layouts and recover cleanly from expired sessions. | Required for all protected workflows. |
| `UIAPI-FR-277` | Auth components shall support login and registration flows. | Add | Provide login and registration components. | Supports approved auth routes. |
| `UIAPI-FR-278` | Layout components shall provide app shell, sidebar, navbar, offline banner, theme provider, error boundary, and shared UI primitives. | Modify | Provide app shell, navigation, error boundary and shared primitives; add offline/theme features only where they support a confirmed workflow. | Avoids component-first scope expansion. |
| `UIAPI-FR-279` | Dashboard components shall render system status, broker status, market hours, resource usage, recent activity, quick actions, active strategies, equity curve, daily PnL, win rate, and currency-strength views. | Modify | Render approved dashboard snapshots; omit currency strength until its capability is resumed. | Aligns UI with deferred API behavior. |
| `UIAPI-FR-280` | Strategy components shall support strategy listing, strategy cards, strategy creation, metadata editing, code editing, version history, diff viewing, and config preview. | Add | Provide strategy list/create/edit/version UI against the approved strategy contracts. | Supports a confirmed V1 workflow. |
| `UIAPI-FR-281` | Backtest and simulation components shall support configuration, execution view, results, charts, trade lists, sessions, positions, orders, risk panels, speed/skip controls, and trading dialogs. | Add | Provide focused backtest/simulator configuration, progress, results, state and governed controls. | Supports confirmed V1 workflows. |
| `UIAPI-FR-282` | Live components shall support live status, sessions, strategy runner, session strategy manager, positions, orders, manual order controls, risk monitoring, candle charts, and logs. | Add | Provide live monitoring and governed controls only when backend safety gates are available. | Supports confirmed V1 workflow without moving live logic client-side. |
| `UIAPI-FR-283` | Edge Lab components shall support prerequisite state, navigation, dataset summary, collection state, controls, scorecard evidence, indicator charting, core metric unsupervised views, and EDS evidence. | Modify | Provide core dataset/run/profile/scorecard research views; defer automation and advanced calibration/export views. | Matches reduced Edge Lab scope. |
| `UIAPI-FR-284` | Performance components shall support trade detail, trade chart, statistics, calendars, comparative charts, metric grids, distributions, scatter charts, series charts, and page-level actions. | Defer | Defer the broad performance visualization suite. | No initial API-domain evidence requires it. |
| `UIAPI-FR-285` | Documentation components shall support navigation, table of contents, Markdown rendering, document wrapping, and document editing. | Add | Provide documentation navigation, Markdown rendering and restricted editing. | Supports the preserved documentation workflow. |

#### Implementation-heavy V2 requirements

**Accepted behaviour:** route handlers must call approved domain boundaries, propagate identity/request context, apply timeouts where external work can block, and translate typed failures.

**Rejected or simplified implementation:** a network-style service client, service discovery mechanism, or orchestrator object is not mandatory for every in-process call. The final modular monolith may call explicit public domain functions/classes directly. A focused orchestrator is added only when a confirmed multi-domain workflow cannot remain a simple serial delegation. The separate operator FastAPI application and its special dependency accessor are not part of the final architecture.

### 6.3 Non-Functional Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-NFR-001` | Protected API endpoints shall require authenticated user or service-account context where applicable. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-002` | Mutating endpoints shall require role/action checks and governed write context where financial or operational side effects are possible. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-003` | Governed and financial endpoints shall require backend safety gates and audit; frontend checks are preflight only and shall not be treated as final authorization. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-004` | Live trading mutations shall remain disabled unless explicit live flags, risk approval, broker readiness, reconciliation, idempotency, audit, and kill-switch requirements are satisfied by backend services. | Keep | Keep live mutations fail-closed behind all backend safety gates. | Safety-critical and consistent with the platform boundary. |
| `UIAPI-NFR-005` | API responses shall use standard envelopes unless streaming has a documented approved event format. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-006` | API and UI shall prevent contract drift through typed DTOs, validators, and contract tests. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-007` | API errors and logs shall redact secrets and avoid exposing credentials or private broker data. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-008` | Frontend code shall not embed backend business logic for trading, risk, broker execution, research algorithms, or persistence rules. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-009` | Optional backend route import failures shall degrade route availability without blocking unrelated API startup. | Modify | Only explicitly optional routes may degrade; required-route failures must fail startup/readiness. | V1 broad fail-open behavior is unsafe. |
| `UIAPI-NFR-010` | WebSocket and streaming routes shall detect client disconnects, stop per-client delivery work, release per-client resources, preserve authoritative session state, emit no further events to the disconnected client, and record sanitized disconnect metadata. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-011` | API startup shall not require unavailable optional providers for unrelated routes. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-012` | Frontend API clients shall attach request and trace identifiers for observability. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-013` | UI workflows shall display stale or unavailable data clearly and shall not use stale data for governed decisions without refresh. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-014` | Primary UI workflow controls shall remain visible or reachable without horizontal scrolling at documented supported viewport widths, shall not overlap critical content, shall provide accessible labels, and shall satisfy the declared accessibility target. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-015` | Authentication tokens shall be treated as secrets and shall not be logged or exposed in telemetry. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-016` | Frontend build, lint, and agentic-firm contract tests shall remain runnable through package scripts. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-017` | API logs, traces, and telemetry shall include request id, trace or correlation id, route group, route intent, actor id where available, session id where available, status code, duration, and sanitized error code. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-018` | API logs, traces, telemetry, and frontend telemetry shall not include auth tokens, broker credentials, API provider credentials, passwords, raw secrets, authorization headers, CSRF tokens, or private broker account data. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-019` | Proposed Decision: Non-streaming authenticated read endpoints shall target p95 latency under 200 ms in lab/local contract tests and under 500 ms in production-like tests, excluding explicitly documented long-running analysis endpoints. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-020` | Proposed Decision: All API endpoints shall complete or return a structured error within 30 seconds unless the route contract documents a longer-running job, streaming flow, or accepted async run model. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-021` | Proposed Decision: Default request body size limit shall be 1 MB for standard JSON endpoints, 10 MB for approved import endpoints, and route-specific for explicitly approved artifact uploads. Oversized payloads return HTTP 413 with `PAYLOAD_TOO_LARGE`. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-022` | Proposed Decision: Default response size limit shall be 2 MB for standard JSON endpoints unless the route contract defines pagination, streaming, artifact download, or truncation behavior. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-023` | Mutating endpoints shall define retry eligibility, idempotency policy, audit-log requirement, and expected 4xx/5xx failure behavior. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-024` | API routes shall define timeout behavior and retry eligibility. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-025` | Proposed Decision: WebSocket/SSE routes shall use a 15-second client-to-server ping interval where supported, a 30-second server expectation window, and terminal cleanup after missed heartbeat policy is triggered. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-026` | Proposed Decision: Default maximum streaming connections shall be 5 per authenticated actor/session per stream class and 50 process-wide per stream class until production capacity tests approve higher limits. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-027` | Import and documentation endpoints shall define allowed content types, cleanup behavior, and path-safety behavior. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-028` | API and UI compatibility shall be tested through OpenAPI or equivalent route snapshots and TypeScript DTO/validator drift checks before production handoff. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-029` | Frontend primary workflows shall meet a declared accessibility target, preferably WCAG 2.1 AA for core workflows, before production handoff. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-030` | Build, lint, typecheck, contract validation, and security test gates shall be runnable in CI once implementation begins. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-031` | Proposed Decision: Initial rate-limit classes shall include `health` 120/minute, `standard-read` 300/minute, `standard-write` 60/minute, `auth` 10/minute, `ai-chat` 50/minute, `operator` 30/minute, `live-mutation` 5/minute, `import` 10/minute, and `analysis` 20/minute per actor/session or stricter route-specific scope. | Open Decision | Approve measured route-class targets and limits before production handoff. | The need is valid, but exact numbers require workload, deployment and security evidence. |
| `UIAPI-NFR-032` | Proposed Decision: Rate-limit responses shall return HTTP 429 with `RATE_LIMITED`, retry metadata where safe, request id, and trace or correlation id. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |
| `UIAPI-NFR-033` | Proposed Decision: Backend non-JSON upstream responses shall be translated to HTTP 502 with `UPSTREAM_NON_JSON_RESPONSE`, bounded sanitized details, request id, and trace or correlation id. | Add | Adopt as a release-quality non-functional contract, adjusted to approved routes and deployment. | V1 audit found little or no consistent evidence of this gate. |

### 6.4 Edge-Case Requirements

| V2 requirement ID | Proposed edge case | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-EDGE-001` | Unauthenticated request to a protected endpoint. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-002` | Expired, missing, malformed, or invalid auth token. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-003` | User account is deactivated by an admin after a token is issued; the token must be invalidated or rejected on next verification. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-004` | User logs in again and older session token becomes invalid. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-005` | Inactive user, unverified user, invalid password, or missing user. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-006` | Unsupported operator role or missing operator bearer token. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-007` | Permission profile changes between UI preflight and backend mutation. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-008` | Governed write attempted without request id, workflow id, approval id, required permission, CSRF token, or audit event type. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-009` | Live-order or live-activation request missing board approval. | Open Decision | Retain the failure case only after board/critical-incident approval contracts are confirmed at system level. | The approval actors and shared contracts are not resolved in the two inputs. |
| `UIAPI-EDGE-010` | Kill-switch reset request missing critical incident approval. | Open Decision | Retain the failure case only after board/critical-incident approval contracts are confirmed at system level. | The approval actors and shared contracts are not resolved in the two inputs. |
| `UIAPI-EDGE-011` | Optional backend route fails to import at startup. | Modify | Test failure of explicitly optional imports and failure of required imports separately. | Required routes must not silently disappear. |
| `UIAPI-EDGE-012` | Database initialization, migration, scheduler startup, Redis health, or schema registry health fails. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-013` | Client disconnects from WebSocket, AI chat stream, operator event stream, optimization progress stream, or backtest log stream. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-014` | Malformed JSON payload, malformed validation error payload, empty response body, text response body, or 204 response. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-015` | Backend service returns a non-JSON response and the gateway must translate it to HTTP 502 with `UPSTREAM_NON_JSON_RESPONSE`. | Modify | Translate non-JSON responses only for real HTTP upstreams; in-process domain failures use typed errors. | Avoids designing all internal calls as remote services. |
| `UIAPI-EDGE-016` | Backend returns 500 on retryable read-only GET request. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-017` | Slow response exceeds stale threshold. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-018` | API error detail is an array or object rather than a string. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-019` | Route path maps to unknown intent metadata. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-020` | UI page route exists without matching API client behavior. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-021` | API endpoint changes without updating frontend DTOs or validators. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-022` | Documentation save/delete attempts path traversal or invalid file paths. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-023` | Dashboard currency-strength endpoint remains deferred or unavailable. | Keep | Keep the UI/API stable when currency strength is deferred or unavailable. | Matches the reconciliation decision. |
| `UIAPI-EDGE-024` | Frontend runs without `NEXT_PUBLIC_API_URL` and must use the local default. | Modify | Allow a localhost default only in development; production requires explicit configuration. | Safer environment behavior. |
| `UIAPI-EDGE-025` | Browser has no auth token in local storage. | Open Decision | Handle missing/corrupted client auth state after the final token-storage mechanism is chosen. | LocalStorage is not approved as the final security model. |
| `UIAPI-EDGE-026` | Browser localStorage is unavailable, disabled, corrupted, or cleared during an active session. | Open Decision | Handle missing/corrupted client auth state after the final token-storage mechanism is chosen. | LocalStorage is not approved as the final security model. |
| `UIAPI-EDGE-027` | Provider-backed AI chat or research workflow is unavailable. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-028` | Live session mutation requested while backend safety gates are closed. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-029` | Simulation session, live session, strategy, backtest, optimization run, Edge Lab run, or scorecard snapshot id is missing or stale. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-030` | Payload exceeds the documented maximum request size. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-031` | Response exceeds the documented maximum response size or frontend context budget. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-032` | Import file has unsupported type, corrupt content, duplicate records, or partial parse failure. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-033` | Duplicate governed mutation arrives with the same idempotency key. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-034` | Duplicate governed mutation arrives without an idempotency key. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-035` | CSRF token is missing, expired, malformed, replayed, or belongs to another session. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-036` | Stream reconnect occurs after missed events. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-037` | Stream client is slow and triggers backpressure behavior. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-038` | Stream heartbeat is missed or terminal error is emitted. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-039` | Market-hours or time-sensitive endpoint crosses timezone, DST, weekend, holiday, or broker-session boundary. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-040` | API contract version expected by frontend does not match backend route schema. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-041` | Rate limit is exceeded by user, session, IP, or route group. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-042` | Backend dependency partially fails after a mutation has begun. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-043` | CORS origin is denied for browser-origin requests. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-044` | Operator event stream is requested by unauthenticated or underprivileged callers. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-045` | Public health-only stream, if configured, attempts to include approval, actor, broker, incident, policy, or live-execution data. | Reject | No public health-only stream is included in the initial rebuild. | The related V2 proposal is rejected. |
| `UIAPI-EDGE-046` | Idempotency key storage backend, such as Redis, is temporarily unavailable; governed and financial mutations fail closed by default with HTTP 503. | Modify | Test unavailability of the approved idempotency store without assuming Redis. | Storage technology remains open. |
| `UIAPI-EDGE-047` | Idempotency replay attempts to return a stored response whose schema version no longer matches the current gateway contract. | Add | Include this edge case in the approved capability tests. | It protects a confirmed boundary, workflow, or safety condition. |
| `UIAPI-EDGE-048` | Domain service client is unavailable, not registered, or returns an unsupported typed error. | Modify | Test unavailable or unsupported approved domain entry points; network client registration applies only to remote dependencies. | Keeps the boundary minimal. |
| `UIAPI-EDGE-049` | Complex governed workflow requires more than serial delegation and no approved orchestrator abstraction exists. | Modify | Reject unsupported complex workflow requests unless a demonstrated orchestrator exists. | Do not prebuild an orchestration layer. |

### 6.5 Test Requirements

| V2 requirement ID | Proposed test | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-TEST-001` | Contract definition tests shall fail Builder handoff when any public HTTP route lacks method, path, auth, roles/permissions, request schema, response schema, status codes, error codes, side effects, idempotency behavior, rate-limit class, observability fields, stability, or owning service. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-002` | Contract definition tests shall fail Builder handoff when any stream lacks auth, event schema, heartbeat, reconnect, backpressure, disconnect cleanup, terminal-error behavior, sequence behavior, and maximum connection policy. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-003` | Contract definition tests shall fail Builder handoff when any requirement lacks an ID, test mapping, or documented manual-verification reason. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-004` | Contract definition tests shall fail Builder handoff when any governed mutation lacks idempotency, audit, CSRF, duplicate-submit, stale-data, authorization, and replay behavior. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-005` | Contract definition tests shall validate that route contracts and TypeScript client schemas use the same approved API version. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-006` | API startup tests for canonical `api.main:app`, optional route import degradation, middleware installation, CORS settings, and health endpoint. | Modify | Test the single canonical app, required-vs-optional route behavior, middleware, CORS, liveness and readiness. | Reflects merged composition. |
| `UIAPI-TEST-007` | Operator API tests for dependency injection, metadata route, component health routes, operator auth middleware, role enforcement, approvals, and event stream access. | Modify | Test protected operator routes within the canonical app rather than a separate operator deployment. | Separate operator app is rejected. |
| `UIAPI-TEST-008` | Auth tests for registration, login, logout, token generation, single-session behavior, token verification, token expiration, invalid credentials, inactive users, unverified users, and missing Authorization headers. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-009` | Security middleware tests proving headers and query parameters are redacted before logging. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-010` | Intent-classifier tests for route-to-intent metadata and session header handling. | Modify | Test only the retained route-intent/request-context metadata and remove tests for unused mutable classifier APIs. | Keeps scope proportional. |
| `UIAPI-TEST-011` | Contract tests for every API route group: auth, settings, AI chat, strategies, SQX, backtest, simulator, risk, live, optimization, dashboard, docs, Edge Lab, data, operator approvals, and streams. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-012` | Permission and governance tests proving protected endpoints reject unauthenticated access and governed writes require backend authorization. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-013` | Live safety tests proving UI/API cannot bypass risk, approval, idempotency, reconciliation, audit, kill-switch, or explicit live-enable controls. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-014` | WebSocket and streaming tests for connect, event delivery, disconnect, cancellation, and cleanup. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-015` | Frontend request-helper tests for auth header attachment, error parsing, 204 responses, JSON parsing, retry behavior, stale warning behavior, and telemetry. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-016` | Frontend governed-write tests proving missing approval, permission, CSRF, workflow, request, board, or critical-incident context blocks requests before fetch. | Modify | Test approved governed context fields; board/critical-incident specifics remain conditional on system decisions. | Shared approval contracts are open. |
| `UIAPI-TEST-017` | Frontend API client contract tests for typed request/response behavior across AI chat, backtest, data, docs, Edge Lab, live, optimization, risk, simulator, strategies, trades, and agentic clients. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-018` | Frontend route smoke tests for auth routes, dashboard routes, documentation routes, Edge Lab routes, simulation routes, live routes, optimization routes, performance routes, strategy routes, and AI CEO routes. | Modify | Cover only approved initial frontend routes/workflows; add deferred suites when capabilities resume. | Avoids locking in deferred UI scope. |
| `UIAPI-TEST-019` | Protected-route tests proving unauthenticated users cannot access dashboard workflows. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-020` | UI integration tests for dashboard, strategy editor, backtest, simulation, live, Edge Lab, performance, docs, settings, and AI chat workflows. | Modify | Cover only approved initial frontend routes/workflows; add deferred suites when capabilities resume. | Avoids locking in deferred UI scope. |
| `UIAPI-TEST-021` | Accessibility and responsive-layout tests for primary UI workflows. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-022` | Build/lint gates using `npm --prefix ui run lint`, `npm --prefix ui run build`, and `npm --prefix ui run test:agentic-firm` when dependencies are installed. | Modify | Use the final approved frontend workspace path and scripts; keep lint/build/contract gates mandatory. | The current V2 path may change during package migration. |
| `UIAPI-TEST-023` | Backend validation gates using relevant Python tests and API contract tests when the test suite is available. | Add | Add API unit, contract and integration gates with the API package included in coverage/type checking. | V1 audit found no direct API tests or configured API coverage. |
| `UIAPI-TEST-024` | Route contract metadata tests proving every public HTTP and streaming capability declares classification, stability, auth, schemas, status codes, error envelope, side effects, idempotency behavior, audit requirement where applicable, and owning service. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-025` | Standard error-envelope tests for 400, 401, 403, 404, 409, 422, 429, 500, and 503 responses. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-026` | OpenAPI or maintained contract snapshot tests for every HTTP route group. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-027` | TypeScript DTO and validator drift tests against backend response schemas or approved contract snapshots. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-028` | Pagination, filtering, sorting, default-limit, maximum-limit, and empty-result tests for every list endpoint with finalized list semantics. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-029` | Streaming contract tests for auth, heartbeat, reconnect, disconnect cleanup, missed-event behavior, slow-client backpressure, cancellation, terminal error, and malformed event payloads. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-030` | Operator event stream tests proving unauthenticated and underprivileged callers are rejected unless an explicitly configured redacted public health-only stream is in use. | Modify | Test that the operator stream is always authenticated/authorized; remove the public-stream exception. | Public health stream is rejected. |
| `UIAPI-TEST-031` | CSRF failure tests for browser-origin mutating requests. | Open Decision | Add CSRF tests after the browser token/cookie transport is approved. | CSRF applicability depends on authentication transport. |
| `UIAPI-TEST-032` | Token, credential, CSRF, and broker-data redaction tests for backend logs, frontend telemetry, error envelopes, and usage examples. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-033` | Path traversal, symlink escape, invalid path, unsupported content, and maximum-size tests for documentation save/delete and import endpoints. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-034` | Rate-limit behavior tests for auth, AI chat, operator approvals, live mutations, imports, and expensive analysis endpoints. | Open Decision | Add rate-limit tests after route-class limits and scope keys are approved. | Exact policy is unresolved. |
| `UIAPI-TEST-035` | Duplicate governed mutation tests for same idempotency key, different material under same idempotency key, and missing idempotency key. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-036` | Partial dependency failure tests proving mutations either roll back, return explicit compensating failure behavior, or record a documented pending-reconciliation state. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-037` | Performance and reliability tests for p95 latency targets, maximum concurrent stream connections, optional provider startup degradation, and scheduler startup/shutdown observability when those targets are approved. | Open Decision | Add performance/load assertions after measurable targets and deployment topology are approved. | Exact thresholds lack evidence. |
| `UIAPI-TEST-038` | E2E tests for login, protected-route access, logout, expired-token redirect, invalid-token recovery, governed-write rejection, mocked governed-write success, stale data warnings, and blocked governed decisions from stale data. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-039` | Documentation/example tests proving TypeScript examples compile, HTTP examples match the standard envelope, and streaming examples follow the approved event contract. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |
| `UIAPI-TEST-040` | Requirement-to-test traceability matrix proving every functional and non-functional requirement has at least one mapped test or a documented manual-verification reason. | Add | Include this test in the final traceability matrix for approved capabilities. | V1 lacks direct API/frontend contract evidence. |

### 6.6 Usage-Example Dispositions

| V2 example ID | Proposed example | Decision | Final direction |
|---|---|---|---|
| `UIAPI-EX-001` | Run the backend with `uvicorn api.main:app --reload`. | Modify | Use the approved canonical import path after the package-path decision. |
| `UIAPI-EX-002` | Run the frontend with `npm --prefix ui run dev`. | Modify | Use the final approved frontend workspace path and package scripts. |
| `UIAPI-EX-003` | Call the generic typed frontend `request` helper for settings. | Merge | Demonstrate the single typed request primitive rather than a separate generic/agentic transport stack. |
| `UIAPI-EX-004` | Send request/correlation headers and receive a standard validation envelope. | Modify | Retain request/correlation IDs and standard envelopes using the final API version/error catalogue. |
| `UIAPI-EX-005` | Build and send governed-write context with idempotency and CSRF headers. | Modify | Retain governed request context; include only approved shared approval fields and the final auth/CSRF transport. |
| `UIAPI-EX-006` | Block an unsafe governed write before fetch and show a UI error. | Keep | Retain a client-preflight failure example while stating that backend enforcement remains authoritative. |
| `UIAPI-EX-007` | Return the stored original response for a duplicate successful idempotency key. | Modify | Retain idempotent replay semantics after key format/store/schema-version behavior is approved. |
| `UIAPI-EX-008` | Stream AI-chat deltas through the documented event envelope. | Modify | Retain streaming example using the final event envelope, auth and reconnect contract. |

### 6.7 Acceptance Requirements

| V2 requirement ID | Proposed acceptance condition | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `UIAPI-ACC-001` | Every public route group has a concrete route contract table with method, path, auth, schema refs, status codes, error codes, idempotency behavior, pagination behavior where applicable, rate-limit class, observability fields, side effects, stability, and owning service. | Add | Make this a mandatory README/Builder-handoff acceptance gate. | It closes documented V2 handoff gaps. |
| `UIAPI-ACC-002` | Every streaming surface has a concrete event contract with auth, event envelope, heartbeat, reconnect, backpressure, disconnect cleanup, terminal-error behavior, and maximum connection policy. | Add | Make this a mandatory README/Builder-handoff acceptance gate. | It closes documented V2 handoff gaps. |
| `UIAPI-ACC-003` | Every governed mutation has a concrete idempotency, audit, authorization, CSRF, duplicate-submit, and stale-data policy. | Add | Make this a mandatory README/Builder-handoff acceptance gate. | It closes documented V2 handoff gaps. |
| `UIAPI-ACC-004` | Every functional and non-functional requirement has a requirement ID and mapped test type. | Add | Make this a mandatory README/Builder-handoff acceptance gate. | It closes documented V2 handoff gaps. |
| `UIAPI-ACC-005` | Every pending policy in the Pre-handoff Blockers table is resolved or explicitly deferred by owner decision. | Open Decision | Resolve or explicitly defer every blocker with named ownership before Builder handoff. | Several blockers are cross-domain/system decisions. |

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
|---|---|---|---|---|---|---|
| WF-UI-001 | Gateway startup and readiness | Internal | V1-WF-API-001 Partial/Working | Canonical app lifecycle with optional degradation | Modify | Process configuration → compose required and approved optional routes → initialize required dependencies → expose truthful liveness/readiness → shut down owned gateway resources. |
| WF-UI-002 | Authenticated request boundary | Internal | Distributed across V1 routes | Gateway request sequence diagram | Add | HTTP request → request/trace context → authentication/authorization → boundary validation → one approved domain call → standard response/error envelope. |
| WF-UI-003 | User authentication and settings | Cross-domain | V1-WF-API-002, 003 structurally complete | Auth/settings routes and protected UI | Modify | Credentials/session input → identity/session domain validation → canonical principal → settings query/update → typed response; no fallback identity. |
| WF-UI-004 | Market data and dataset preparation | Cross-domain | V1-WF-API-004 Partial/Unverified | Data routes and typed client | Modify | Authenticated source/range request → data/research domain → prepared dataset or provider error → bounded typed response. |
| WF-UI-005 | Strategy catalogue and SQX lifecycle | Cross-domain | V1-WF-API-005 substantially complete | Strategy/SQX route inventory | Modify | Authenticated strategy command/query → strategy domain owns DB/artifact/governance work → boundary DTO/download; partial failures reconciled. |
| WF-UI-006 | Backtest run and result review | Cross-domain | V1-WF-API-006 Partial/Unverified | Thin backtest delegation and stream | Replace | Validated run request → simulation job → persisted result/analytics → query/stream response; gateway no longer executes simulation logic. |
| WF-UI-007 | Interactive simulation lifecycle | Cross-domain | V1-WF-API-007 structurally complete | Simulator route inventory | Modify | Owned session command → simulation runtime → state/risk snapshot → typed response; runtime/lease ownership outside gateway. |
| WF-UI-008 | Governed simulated mutation and what-if | Cross-domain | V1-WF-API-008 structurally complete | Governed-write contracts | Modify | Owned running session + request context → risk/governance evaluation → simulation mutation or non-mutating what-if → updated state and audit metadata. |
| WF-UI-009 | Optimization and scenario jobs | Cross-domain | V1-WF-API-009 Partial/Unverified | Optimization route inventory | Modify | Authenticated bounded request → optimization job → progress stream/polling → persisted result; cancel signals active work and reconciles state. |
| WF-UI-010 | Risk decision support | Cross-domain | V1-WF-API-010 Unverified | Risk delegation routes | Modify | Validated authorized risk request → risk-domain evaluation → typed size/regime/allocation/governance output; no gateway calculations. |
| WF-UI-011 | Core Edge Lab research | Cross-domain | V1-WF-API-011 Partial | Core and advanced research route proposal | Modify | Dataset input → approved research analysis → run/profile/scorecard persistence → retrieval; automation/calibration/export extras deferred. |
| WF-UI-012 | AI chat and governed draft lifecycle | Cross-domain | V1-WF-API-012 Partial/Unverified | Chat/context/proposal/action/stream routes | Modify | Canonical user + bounded page context → conversation domain → thread/message/stream → proposal/draft → governed approval or paper path. |
| WF-UI-013 | Live session and governed broker action | Cross-domain | V1-WF-API-013 Unverified | Live route inventory and safety NFRs | Replace | Authenticated live command → live domain verifies flags, broker readiness, risk, approval, reconciliation, idempotency and kill switch → action/status/event; gateway never calls broker directly. |
| WF-UI-014 | Operator approval and event review | Cross-domain | V1-WF-API-014 Partial | Protected operator routes/stream | Modify | Validated operator principal → approval create/vote or protected event subscription → governance/event domain → audited response/event; no public sample stream. |
| WF-UI-015 | Documentation management | Internal/Cross-domain | V1-WF-API-015 statically working | Docs viewer/editor | Modify | Authorized developer/operator → safe normalized docs path → list/read or audited idempotent write/delete → typed response. |
| WF-UI-016 | Frontend governed request | Cross-domain | Missing from V1 audit evidence | V2 gateway request flow and governed preflight | Add | User action → typed client builds request/trace/governed context → client preflight warning/block → backend authoritative checks → typed result/stale warning. |
| WF-UI-017 | Frontend stream consumption | Cross-domain | V1 backend streams only | V2 chat/backtest/live/optimization/operator streams | Add | Authenticated client connects → validates ordered event envelope → handles heartbeat/reconnect/backpressure/terminal error → cleans up and refreshes authoritative state after gaps. |

### `WF-UI-001` — Gateway startup and readiness

**Scope:** `Internal`

**V1 behaviour:**

```text
V1-WF-API-001 Partial/Working
```

**V2 proposal:**

```text
Canonical app lifecycle with optional degradation
```

**Final decision:**

```text
Modify: Process configuration → compose required and approved optional routes → initialize required dependencies → expose truthful liveness/readiness → shut down owned gateway resources.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-002` — Authenticated request boundary

**Scope:** `Internal`

**V1 behaviour:**

```text
Distributed across V1 routes
```

**V2 proposal:**

```text
Gateway request sequence diagram
```

**Final decision:**

```text
Add: HTTP request → request/trace context → authentication/authorization → boundary validation → one approved domain call → standard response/error envelope.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-003` — User authentication and settings

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-002, 003 structurally complete
```

**V2 proposal:**

```text
Auth/settings routes and protected UI
```

**Final decision:**

```text
Modify: Credentials/session input → identity/session domain validation → canonical principal → settings query/update → typed response; no fallback identity.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-004` — Market data and dataset preparation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-004 Partial/Unverified
```

**V2 proposal:**

```text
Data routes and typed client
```

**Final decision:**

```text
Modify: Authenticated source/range request → data/research domain → prepared dataset or provider error → bounded typed response.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-005` — Strategy catalogue and SQX lifecycle

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-005 substantially complete
```

**V2 proposal:**

```text
Strategy/SQX route inventory
```

**Final decision:**

```text
Modify: Authenticated strategy command/query → strategy domain owns DB/artifact/governance work → boundary DTO/download; partial failures reconciled.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-006` — Backtest run and result review

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-006 Partial/Unverified
```

**V2 proposal:**

```text
Thin backtest delegation and stream
```

**Final decision:**

```text
Replace: Validated run request → simulation job → persisted result/analytics → query/stream response; gateway no longer executes simulation logic.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-007` — Interactive simulation lifecycle

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-007 structurally complete
```

**V2 proposal:**

```text
Simulator route inventory
```

**Final decision:**

```text
Modify: Owned session command → simulation runtime → state/risk snapshot → typed response; runtime/lease ownership outside gateway.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-008` — Governed simulated mutation and what-if

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-008 structurally complete
```

**V2 proposal:**

```text
Governed-write contracts
```

**Final decision:**

```text
Modify: Owned running session + request context → risk/governance evaluation → simulation mutation or non-mutating what-if → updated state and audit metadata.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-009` — Optimization and scenario jobs

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-009 Partial/Unverified
```

**V2 proposal:**

```text
Optimization route inventory
```

**Final decision:**

```text
Modify: Authenticated bounded request → optimization job → progress stream/polling → persisted result; cancel signals active work and reconciles state.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-010` — Risk decision support

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-010 Unverified
```

**V2 proposal:**

```text
Risk delegation routes
```

**Final decision:**

```text
Modify: Validated authorized risk request → risk-domain evaluation → typed size/regime/allocation/governance output; no gateway calculations.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-011` — Core Edge Lab research

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-011 Partial
```

**V2 proposal:**

```text
Core and advanced research route proposal
```

**Final decision:**

```text
Modify: Dataset input → approved research analysis → run/profile/scorecard persistence → retrieval; automation/calibration/export extras deferred.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-012` — AI chat and governed draft lifecycle

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-012 Partial/Unverified
```

**V2 proposal:**

```text
Chat/context/proposal/action/stream routes
```

**Final decision:**

```text
Modify: Canonical user + bounded page context → conversation domain → thread/message/stream → proposal/draft → governed approval or paper path.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-013` — Live session and governed broker action

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-013 Unverified
```

**V2 proposal:**

```text
Live route inventory and safety NFRs
```

**Final decision:**

```text
Replace: Authenticated live command → live domain verifies flags, broker readiness, risk, approval, reconciliation, idempotency and kill switch → action/status/event; gateway never calls broker directly.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-014` — Operator approval and event review

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-014 Partial
```

**V2 proposal:**

```text
Protected operator routes/stream
```

**Final decision:**

```text
Modify: Validated operator principal → approval create/vote or protected event subscription → governance/event domain → audited response/event; no public sample stream.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-015` — Documentation management

**Scope:** `Internal/Cross-domain`

**V1 behaviour:**

```text
V1-WF-API-015 statically working
```

**V2 proposal:**

```text
Docs viewer/editor
```

**Final decision:**

```text
Modify: Authorized developer/operator → safe normalized docs path → list/read or audited idempotent write/delete → typed response.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-016` — Frontend governed request

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Missing from V1 audit evidence
```

**V2 proposal:**

```text
V2 gateway request flow and governed preflight
```

**Final decision:**

```text
Add: User action → typed client builds request/trace/governed context → client preflight warning/block → backend authoritative checks → typed result/stale warning.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

### `WF-UI-017` — Frontend stream consumption

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1 backend streams only
```

**V2 proposal:**

```text
V2 chat/backtest/live/optimization/operator streams
```

**Final decision:**

```text
Add: Authenticated client connects → validates ordered event envelope → handles heartbeat/reconnect/backpressure/terminal error → cleans up and refreshes authoritative state after gaps.
```

**Reason:** The final workflow preserves the valuable outcome while assigning domain algorithms, persistence, broker/runtime state, and safety enforcement to their owning domains. The UI/API boundary owns only client interaction, validation, authorization, delegation, DTO/error translation, and stream delivery.

## 8. Recommended Minimal Capability Structure

```text
api/
├── composition/     # Canonical app, lifecycle and registration
├── contracts/       # Boundary DTOs, envelopes and route metadata
├── identity/        # Principal, sessions and authorization
├── middleware/      # Redaction and request context
├── health/          # Liveness and readiness
├── routes/          # Thin feature-focused HTTP boundaries
└── streams/         # Shared event contract and connection lifecycle

ui/
├── app/              # Approved pages and protected layouts
├── clients/          # Typed request primitive and focused clients
├── context/          # Auth, page context and governed options
└── components/       # Components for approved workflows only

tests/
└── contracts/        # API/UI/stream/traceability contract gates
```

| Module | Capability | Source | Main decision |
|---|---|---|---|
| `api/composition` | Canonical app, lifecycle, CORS and route registration | Both | Modify/Merge |
| `api/contracts` | Shared request/response/error/stream metadata contracts | V2 | Add |
| `api/identity` | Canonical principal, sessions and authorization helpers | Both | Modify/Merge |
| `api/middleware` | Redaction, request context, auth and route intent | Both | Modify |
| `api/health` | Liveness, readiness and configured dependency status | Both | Merge |
| `api/routes` | Thin focused route files grouped by approved capability | Both | Split/Modify |
| `api/streams` | Shared stream envelope and focused connection lifecycle | Both | Merge/Modify |
| `ui/app` | Approved pages and protected layouts | V2 | Add/Modify |
| `ui/clients` | One request primitive plus focused typed clients | V2 | Add/Merge |
| `ui/context` | Bounded page context, auth/session and governed request options | V2 | Add |
| `ui/components` | Reusable components only for approved workflows | V2 | Add/Modify |
| `tests/contracts` | Route/stream/OpenAPI/DTO/traceability tests | V2 | Add |

The `routes/` module is a boundary grouping, not a service layer. Each route file represents one focused HTTP use case or closely related resource family. It may call an approved public domain function/class, but it must not own domain algorithms, repositories, broker clients, runtime engines, or long-lived business state.

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
|---:|---|---|---|---|
| 1 | `app/api/main.py`, `app/api/app.py` | Refactor/Merge | CAP-UI-001, CAP-UI-006 | Startup, liveness/readiness, route registration, deployment entry-point tests |
| 2 | `auth_utils.py`, `auth.py`, AI-chat user dependency | Refactor/Replace | CAP-UI-003, CAP-UI-004 | Session, revocation, role/permission, operator and chat ownership tests |
| 3 | `middleware/security.py`, `router.py` | Refactor | CAP-UI-005 | Redaction, request context, unknown-route and no-secret telemetry tests |
| 4 | `routes/strategies.py`, `routes/backtest.py`, `routes/risk.py`, `routes/live.py`, `routes/edge.py`, `routes/optimization.py` | Refactor/Split | CAP-UI-010–016 | Thin-route contract tests and domain-boundary mocks |
| 5 | `routes/simulator.py`, `session/*` | Refactor/Split | CAP-UI-012 | Ownership/lease/resume/save/mutation/what-if tests after runtime moves |
| 6 | `websocket.py`, `events.py` | Replace/Merge | CAP-UI-020 | Auth, event schema, heartbeat, reconnect, cleanup and deployment tests |
| 7 | `routes/docs.py` | Refactor | CAP-UI-019 | Auth, traversal, symlink, size, content and audit tests |
| 8 | `routes/data.py`, dashboard routes | Refactor | CAP-UI-009, CAP-UI-018 | No-fallback-user, freshness, provider failure and timezone tests |
| 9 | `routes/import_trades.py`, missing operator-strategy import, compatibility chat wrapper, disabled Edge scheduler job | Remove | None | External deployment/import search and migration notice |
| 10 | Frontend typed clients and approved pages | New | CAP-UI-021–023 | TypeScript contract, protected-route, E2E and accessibility tests |
| 11 | API/frontend quality gates | New | CAP-UI-024 | Coverage, typing, OpenAPI snapshot, DTO drift and traceability matrix |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
|---|---|---|
| Separate canonical and operator FastAPI applications | Duplicates composition, auth, health and deployment behavior | One canonical app; operator routes remain protected route groups. Temporary compatibility entry point only during migration. |
| Mandatory service-client/service-discovery abstraction for every route | Unnecessary in an in-process modular monolith | Call approved typed public domain APIs directly; add a remote client only when a dependency is actually remote. |
| Mandatory orchestrator for any multi-service request | Creates a layer before a workflow proves it is needed | Keep routes serial; add one focused orchestrator only for a confirmed complex cross-domain workflow. |
| Universal cursor pagination | Overkill for small bounded lists | Cursor pagination for unbounded/high-volume lists; simple bounded lists may use no cursor or a documented simpler scheme. |
| Exhaustive fixed error-code catalogue | Includes speculative codes and increases contract burden | Small common catalogue plus route-specific codes with tests. |
| Store complete idempotency response headers/body for every mutation | Can duplicate audit storage and retain secrets unnecessarily | Store request hash, actor/scope, state and only replay-safe response material. |
| Three separate WebSocket managers plus separate SSE implementation | Duplicates lifecycle logic and remains process-local | One stream envelope and small focused connection state implementations behind a common lifecycle contract. |
| Full Edge Lab calibration, automation and export surface in initial rebuild | V1 is oversized and scheduled workflow is disconnected | Core research runs/results/profiles/snapshots first; defer advanced calibration, automation and exports. |
| Full frontend route/component catalogue | Much broader than workflows evidenced by the V1 API audit | Build only core approved workflow pages; defer agents, board, costs, broad performance and optional tools. |
| Parallel `request`, `agenticApiRequest`, and `agenticApiData` transport stacks | Duplicates base URL, auth, parsing, tracing and validation | One typed request primitive with optional governed/stale/validation features and a tiny unwrap helper. |
| LocalStorage bearer token as fixed architecture | Creates XSS exposure and is not justified by the two inputs | Open system security decision: prefer secure HttpOnly cookie/session transport where feasible; adapt client after approval. |
| Public health-only operator stream | No confirmed user workflow and risks accidental data exposure | Reject for initial rebuild; use normal health endpoint and protected operator event stream. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
|---|---|---|---|---|
| Open — escalate | Final package/import path: `api/` or `app/api/` during migration | V1 actual path is `app/api`; V2 names `api.main:app`. | Move directly to `api/`; retain `app/api` compatibility; keep `app/api` canonical | CAP-UI-001, all imports |
| Open — escalate | Browser authentication transport and token storage | V2 fixes `hq_auth_token` localStorage; V1 uses bearer DB sessions; no security/deployment evidence. | HttpOnly secure cookie; in-memory bearer plus refresh; localStorage only as temporary dev compatibility | CAP-UI-003, CAP-UI-021–023 |
| Open — escalate | Canonical actor/role/permission model | V1 has DB user sessions, caller-controlled operator headers and development chat user. | Unified claims/permissions; role-only model; trusted reverse-proxy assertions | CAP-UI-003, CAP-UI-004, CAP-UI-007, CAP-UI-017 |
| Open — escalate | API versioning and deprecation policy | V2 proposes `v0-draft` and 409 mismatch; V1 has no evidenced version policy. | Path versioning; media/header versioning; unversioned internal API until v1 freeze | CAP-UI-002, CAP-UI-021 |
| Open — escalate | Idempotency key format, scope, store and retention | V2 blocker UIAPI-BLK-004; V1 has no consistent gateway idempotency evidence. | SQLite table; Redis; owning-domain stores; hybrid | CAP-UI-004 |
| Open — escalate | Initial latency, body/response limits, stream quotas, heartbeat and rate limits | V2 values are proposals; no traffic/load evidence. | Adopt proposed conservative defaults; benchmark first; route-class-specific values | CAP-UI-002, CAP-UI-020, CAP-UI-024 |
| Open — escalate | Multi-worker deployment and shared stream/runtime state | V1 managers/live maps are process-local; deployment topology unavailable. | Single worker initially; sticky sessions; shared event/backplane; move all runtime state to domains | CAP-UI-012, CAP-UI-014, CAP-UI-020 |
| Open — escalate | Cross-domain delegation and orchestration boundary | V2 requires service clients/orchestrators; V1 routes call internals directly. | Typed in-process public APIs; explicit application orchestrators; remote service clients only where deployed separately | CAP-UI-002, CAP-UI-010–017 |
| Open | Whether operator metadata endpoint is needed | V2 proposes it; V1 deployment/use is unconfirmed. | Defer; protected minimal metadata; omit entirely | CAP-UI-007 |
| Open | Whether advanced Edge Lab calibration/automation/export routes are needed initially | V1 route exists but operational use/traffic unavailable; scheduler is disconnected. | Defer all; retain selected used routes; rebuild full surface | CAP-UI-016 |
| Open | Whether docs write/delete are allowed outside local development | V1 exposes filesystem mutation; deployment reachability unavailable. | Local-only; operator-only; read-only production | CAP-UI-019 |
| Open | Whether currency strength has an approved source and consuming workflow | V1 capability exists; V2 marks it deferred. | Defer; retain read-only experimental; remove | CAP-UI-018 |

Cross-domain/system decisions marked **escalate** must be copied into the top-level system document and resolved there with an ADR. This reconciliation does not modify that document. Deferrals that affect the system shape—advanced Edge automation, broad frontend route families, currency strength, and public health streaming—must be reflected in the top-level Deferred Capabilities section during pipeline step 05.

## 12. Inputs for the Final Domain README

### Approved capabilities

* One canonical FastAPI gateway with truthful lifecycle, liveness and readiness.
* Typed HTTP/stream/client contracts with standard response and error envelopes.
* Canonical user/operator/chat identity, session validation and permission enforcement.
* Governed-write boundary with backend approval, idempotency, audit and safety context.
* Secret-safe request context, trace metadata and bounded page context.
* Thin route boundaries for settings, data, strategies/SQX, backtest, simulator, risk, live, optimization, core Edge Lab, AI chat, dashboards, documentation and operator approvals.
* Protected authoritative event streams for chat, backtest, simulator/live monitoring, optimization and operator events where approved.
* One typed frontend request primitive and focused clients for approved route groups.
* Protected frontend shell and pages/components for approved workflows.
* Route/stream/OpenAPI/DTO/security/accessibility/traceability test gates.

### Approved workflows

* `WF-UI-001` — Gateway startup and readiness
* `WF-UI-002` — Authenticated request boundary
* `WF-UI-003` — User authentication and settings
* `WF-UI-004` — Market data and dataset preparation
* `WF-UI-005` — Strategy catalogue and SQX lifecycle
* `WF-UI-006` — Backtest run and result review
* `WF-UI-007` — Interactive simulation lifecycle
* `WF-UI-008` — Governed simulated mutation and what-if
* `WF-UI-009` — Optimization and scenario jobs
* `WF-UI-010` — Risk decision support
* `WF-UI-011` — Core Edge Lab research
* `WF-UI-012` — AI chat and governed draft lifecycle
* `WF-UI-013` — Live session and governed broker action
* `WF-UI-014` — Operator approval and event review
* `WF-UI-015` — Documentation management
* `WF-UI-016` — Frontend governed request
* `WF-UI-017` — Frontend stream consumption

### V1 behaviours to preserve

* Database-backed registration/login/logout and single-session replacement.
* Authenticated settings read/update.
* Strategy catalogue/version/import/export outcomes.
* Backtest run/results/analytics and log delivery.
* Simulator ownership, lease conflict, resume/save, frame/replay, governed mutation and what-if outcomes.
* Optimization, walk-forward, scenario results and progress reporting.
* Risk decision-support outputs.
* Core Edge Lab analyses and profile/scorecard snapshot outcomes.
* AI-chat thread/message/context/proposal/draft outcomes.
* Live session/read/mutation/monitoring contracts, subject to backend safety verification.
* Operator approval creation/voting.
* Dashboard reads and safe documentation management.

### V1 behaviours to modify

* Merge the general and operator app composition roots.
* Replace fail-open required startup behavior and constant health.
* Unify user, operator and AI-chat identity; remove fallback user `1`.
* Move domain algorithms, runtime state, broker calls and persistence coordination out of route files.
* Replace process-local stream/live state where deployment requires shared ownership.
* Protect and contract all writes, streams and documentation mutation.
* Add typed envelopes, idempotency, audit, request tracing, freshness and rate/size/timeout policies.
* Include API/UI in coverage, typing, contract and security gates.

### V1 behaviours to remove

* Hard-coded public operator SSE sample events after confirming no demo client dependency.
* Unregistered trade-import route after checking deployment-specific mounts.
* Missing operator-strategy optional import target unless an approved contract appears.
* Unused AI-chat compatibility wrapper and mutable classifier methods after external-reference confirmation.
* Disabled log-only Edge refresh scheduler job.

### V2 behaviours to add

* Capability classification/stability and route/stream/client contract metadata.
* Standard response, error and stream envelopes.
* Backend idempotency and duplicate-submit behavior for governed/financial mutations.
* Truthful readiness and optional-capability degradation reporting.
* Protected authoritative operator events.
* Typed frontend request/client layer, protected layout, stale handling and governed preflight.
* Contract snapshots, DTO drift checks, stream lifecycle tests, security tests, accessibility and requirement traceability.

### V2 proposals to reject or defer

* Reject a permanent second operator FastAPI application and special dependency accessor.
* Reject a public health-only operator stream.
* Reject mandatory network-style service clients/service discovery for every in-process route.
* Reject mandatory orchestrator objects without a demonstrated complex workflow.
* Reject duplicate slash/no-slash settings handlers as separate capabilities.
* Defer currency strength, advanced Edge calibration/automation/exports, broad performance pages, agents/board/cost/audit pages, standalone trade client, and dedicated operator metadata.
* Defer exact versioning, idempotency storage, token transport, limits, stream quotas and rate values pending system decisions.

### Required open decisions before README completion

* Canonical package path and migration compatibility.
* Browser token/session transport and CSRF model.
* Unified role/permission and operator identity authority.
* API versioning/deprecation policy.
* Idempotency key/store/retention/replay policy.
* Initial measurable latency, size, timeout, heartbeat, stream quota and rate-limit baselines.
* Multi-worker/shared stream and runtime topology.
* Approved in-process domain boundary and criteria for application orchestrators.
* Production exposure of documentation writes, advanced Edge scope and currency strength.

## 13. Final Reconciliation Checklist

- [x] every V1 capability received a disposition.
- [x] every V2 checklist requirement received a disposition.
- [x] every V2 edge case received a disposition.
- [x] every V2 test requirement received a disposition.
- [x] every V2 usage example received a disposition.
- [x] every V1 workflow was reconciled.
- [x] the explicit V2 gateway request/stream workflows were reconciled.
- [x] confirmed working V1 behaviour was not discarded without reason.
- [x] unused V1 behaviour was not preserved without reason.
- [x] V2 implementation complexity was not accepted automatically.
- [x] the direction follows the four-level minimal structure.
- [x] cross-domain boundary questions are flagged for pipeline step 05.
- [x] unresolved conflicts are listed under Open Decisions.
- [x] no code was changed.
- [x] neither source document was modified.
- [x] the output is sufficient to write the final domain README.

## Evidence Unavailable

* Executable V1 API/frontend tests, imports, migrations, provider calls, WebSocket/SSE sessions, and startup results.
* Production ASGI entry point, reverse-proxy identity guarantees, worker count, routing/stickiness, and shared-state topology.
* Runtime endpoint traffic, frontend telemetry, and evidence of which optional/deferred routes or pages are actively used.
* Live MT5, Dukascopy, forex-calendar, SQX and AI-provider behavior.
* Approved system-wide contracts for identity/permissions, token transport, CSRF, API versioning, idempotency storage, rate limits, stream quotas, and performance targets.
* Cross-domain confirmation that proposed gateway calls match the final public APIs of data, strategy, simulation, risk, live, optimization, research, conversation, execution, governance and persistence domains.
