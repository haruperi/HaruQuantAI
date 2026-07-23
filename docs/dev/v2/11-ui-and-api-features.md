# UI and API Domain — Capability Feature Extraction (from `11-ui-and-api.md`)

Source: `docs/dev/phase-implementation-plan/11-ui-and-api.md`. Backend module paths are under `api.*` (FastAPI gateway); frontend modules are under `ui/src/*` (TypeScript/React). Test and documentation modules are omitted.

---

## FEAT-API-01: Application Factory and Lifecycle (api.app / api.main / api.lifespan)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_app(settings: ApiSettings, dependencies: ApiDependencies) -> FastAPI` | Construct the ASGI application, register middleware/routes, and include optional routers safely. | Missing |
| `get_app() -> FastAPI` | Expose the constructed application to Uvicorn. | Missing |
| `lifespan(app: FastAPI) -> AsyncIterator[None]` | Database/scheduler lifecycle management (with `initialize_runtime` and `shutdown_runtime`). | Missing |
| `configure_cors(app: FastAPI, origins: Sequence[str], allow_credentials: bool) -> None` | CORS middleware installation. | Missing |
| `assert_pre_handoff_policy_state(blockers: Sequence[PolicyBlocker]) -> PolicyReadiness` | Package-gate policy readiness check. | Missing |

## FEAT-API-02: Route Contracts, DTOs, Versioning, and Pagination (api.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_route_contract(method: HttpMethod, path: str, request_schema: type[BaseModel], response_schema: type[BaseModel], owner: ServiceOwner, policy: RoutePolicy) -> RouteContract` | Typed route-contract construction (with catalog validation, capability classification, and client capability mapping). | Missing |
| `to_api_envelope(result: ServiceResult[T], context: RequestContext) -> ApiEnvelope[T]` | Standard API envelope construction (with request-payload validation and validation-error envelopes). | Missing |
| `build_stream_event(event_type: str, data: JsonValue, context: RequestContext, sequence: int, terminal_error: ApiError \| None = None) -> StreamEventEnvelope` | Sequenced stream-event envelopes (with stream-policy validation and public-stream classification). | Missing |
| `validate_expected_api_version(expected: str \| None, supported: ApiVersionPolicy) -> VersionCompatibility` | API version compatibility with deprecation notices. | Missing |
| `validate_page_request(limit: int \| None, cursor: str \| None, policy: PaginationPolicy) -> PageRequest` | Cursor pagination (with page-response construction and response-size enforcement). | Missing |
| `translate_service_error(error: Exception, context: RequestContext) -> HttpErrorResponse` | Deterministic service/authn/authz error translation with a registered error-code registry. | Missing |

## FEAT-API-03: Service Client Delegation (api.clients / api.dependencies)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `resolve_service_client(owner: ServiceOwner, context: RequestContext) -> ServiceClient` | Owner-based backend service client resolution. | Missing |
| `delegate_serially(request: RequestDto, client: ServiceClient, context: RequestContext) -> ServiceResult[JsonValue]` | Single-service delegation (with `run_orchestrated_workflow` for approved multi-service plans). | Missing |
| `get_operator_api_dependencies(request: HttpRequest) -> OperatorApiDependencies` | Request-scoped operator dependency resolution. | Missing |

## FEAT-API-04: API Settings, Rate Limits, and Timeouts (api.config)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `load_api_settings(source: SettingsSource) -> ApiSettings` | Configuration loading with validation. | Missing |
| `rate_limit_for(route: RouteContract, actor: ActorContext \| None, settings: ApiSettings) -> RateLimitPolicy` | Per-route/actor rate-limit resolution (with `timeout_for` counterpart). | Missing |

## FEAT-API-05: Governed Writes and Idempotency (api.governance / api.idempotency)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_governed_write_context(context: GovernedWriteContext, route: RouteContract) -> GovernedWriteValidation` | Fail-closed governed-write validation. | Missing |
| `require_idempotency_key(request: HttpRequest, policy: IdempotencyPolicy) -> str` | Mandatory idempotency keys with material construction and completed-response replay. | Missing |
| `enforce_live_mutation_gate(result: LiveGateResult) -> None` | Authoritative backend live-mutation gate enforcement. | Missing |
| `get_or_reserve(material: IdempotencyMaterial) -> IdempotencyReservation` | Idempotency persistence (with `complete_reservation` and `lookup_completed`). | Missing |

## FEAT-API-06: Middleware, Authentication, and Redaction (api.middleware / api.security)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `SecretRedactionMiddleware.dispatch(request: HttpRequest, call_next: RequestHandler) -> HttpResponse` | HTTP-boundary secret redaction (with request-metadata and error-detail redaction). | Missing |
| `IntentClassifier.classify(path: str, session_id: str \| None) -> RoutingMetadata` | Request intent classification middleware. | Missing |
| `OperatorAuthMiddleware.dispatch(request: HttpRequest, call_next: RequestHandler) -> HttpResponse` | Operator authorization boundary (with public-route policy check). | Missing |
| `authenticate_user(credentials: LoginRequest, auth_store: AuthStore) -> AuthenticatedUser` | Credential authentication (with token generation/verification/invalidation and session replacement). | Missing |
| `get_operator_principal(request: HttpRequest, token_service: TokenService) -> OperatorPrincipal` | Operator principal resolution with role requirements. | Missing |

## FEAT-API-07: Streaming Connection Management (api.streaming)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `open_stream(stream: StreamDescriptor, principal: ActorContext, manager: StreamManager) -> StreamSession` | Authenticated stream registration. | Missing |
| `publish_stream_event(session: StreamSession, event: StreamEventEnvelope) -> DeliveryResult` | Event delivery (with disconnect cleanup and telemetry). | Missing |
| `enforce_stream_backpressure(session: StreamSession, policy: StreamPolicy) -> BackpressureDecision` | Bounded queue/connection backpressure. | Missing |

## FEAT-API-08: Operator Governance Routes (api.routes.operator / operator_stream / health)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_live_execution_approval(request: LiveExecutionApprovalRequest, context: OperatorRequestContext) -> ApiEnvelope[ApprovalDto]` | Approval creation family: live execution, policy change, override, kill-switch recovery, and vote recording. | Missing |
| `trigger_emergency_kill_switch(request: EmergencyKillSwitchRequest, context: OperatorRequestContext) -> ApiEnvelope[ActionReceiptDto]` | Governed emergency kill-switch trigger. | Missing |
| `submit_manual_trade_intent(request: ManualTradeIntentRequest, context: OperatorRequestContext) -> ApiEnvelope[ActionReceiptDto]` | Manual trade intent, position close, and mass-cancel operator actions. | Missing |
| `get_operator_health(context: OperatorRequestContext, client: OperatorHealthClient) -> ApiEnvelope[AggregateHealthDto]` | Aggregate and per-component operator health (with public `get_health` liveness). | Missing |
| `stream_operator_events(request: WebSocketRequest, principal: OperatorPrincipal) -> None` | Operator WebSocket event stream. | Missing |

## FEAT-API-09: Conversational Chat Routes (api.routes.chat)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_message(thread_id: str, request: ChatMessageRequest, context: RequestContext) -> ApiEnvelope[ChatMessageDto]` | Chat messaging (with `regenerate_response` and `list_chat_tools`). | Missing |
| `list_threads(context: RequestContext) -> ApiEnvelope[CursorPage[ChatThreadDto]]` | Thread management family: archive, rename, delete, purge, context update, export. | Missing |
| `get_retention(thread_id: str, context: RequestContext) -> ApiEnvelope[RetentionDto]` | Retention read/update and lifecycle runs. | Missing |
| `list_signal_proposals(thread_id: str, context: RequestContext) -> ApiEnvelope[list[SignalProposalDto]]` | Signal proposals with watchlist and review-queue actions. | Missing |
| `list_action_drafts(thread_id: str, context: RequestContext) -> ApiEnvelope[list[ActionDraftDto]]` | Action drafts with approval requests and approved paper-only execution. | Missing |
| `resolve_page_context(request: ResolveContextRequest, context: RequestContext) -> ApiEnvelope[PageContextDto]` | Page-context resolution for context-aware chat. | Missing |

## FEAT-API-10: Research and Analysis Routes (api.routes — backtests / optimization / edge_lab / sqx)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_portfolio_backtest(strategy_id: str, request: PortfolioBacktestRequest, context: RequestContext) -> ApiEnvelope[BacktestRunDto]` | Backtest execution with overview, list, update, delete, and per-strategy listings. | Missing |
| `create_optimization_run(request: OptimizationRunRequest, context: RequestContext) -> ApiEnvelope[OptimizationRunDto]` | Optimization runs with results retrieval, cancellation, unsupervised analysis, and Monte Carlo sizing. | Missing |
| `run_edge_lab(request: EdgeLabRunRequest, context: RequestContext) -> ApiEnvelope[EdgeLabRunDto]` | Edge Lab family: dataset preparation, unsupervised structure, core metrics, automation batches, market-structure runs/calibration/evaluations, scorecard snapshots/comparisons/exports. | Missing |
| `calculate_sqx_scores(request: SqxScoreRequest, context: RequestContext) -> ApiEnvelope[SqxScoreResponse]` | StrategyQuant X scoring, import, and listing. | Missing |

## FEAT-API-11: Dashboard, Docs, Data, Auth, and Settings Routes (api.routes — dashboard / docs / data / auth / settings)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_dashboard_summary(context: RequestContext) -> ApiEnvelope[DashboardSummaryDto]` | Dashboard family: equity curve, currency strength, system status/resources, market hours, forex calendar. | Missing |
| `list_document_files(context: RequestContext) -> ApiEnvelope[DocumentTreeDto]` | Documentation reads/saves/deletes with safe path validation. | Missing |
| `list_symbols(query: SymbolListQuery, context: RequestContext) -> ApiEnvelope[CursorPage[SymbolDto]]` | Market-data symbol listing. | Missing |
| `register_user(request: RegistrationRequest, context: RequestContext) -> ApiEnvelope[UserDto]` | Registration, login, logout. | Missing |
| `get_settings(context: AuthenticatedRequestContext) -> ApiEnvelope[UserSettingsDto]` | User settings read/update. | Missing |

## FEAT-API-12: Strategy Management Routes (api.routes.strategies)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_strategy(request: StrategyCreateRequest, context: RequestContext) -> ApiEnvelope[StrategyDto]` | Strategy CRUD with templates, listing, and detail reads. | Missing |
| `list_strategy_versions(strategy_id: str, context: RequestContext) -> ApiEnvelope[list[StrategyVersionDto]]` | Versioning: code retrieval, rollback, export, import. | Missing |
| `add_live_session_strategy(session_id: str, request: LiveSessionStrategyRequest, context: RequestContext) -> ApiEnvelope[LiveSessionStrategyDto]` | Live-session strategy attachment/removal/listing. | Missing |

## FEAT-API-13: Interactive Simulator Routes (api.routes.simulator)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `start_simulation(request: SimulationStartRequest, context: RequestContext) -> ApiEnvelope[SimulationSessionDto]` | Session lifecycle: start, pause list, update, advance, resume, seek, stop-and-save, delete. | Missing |
| `run_simulation_what_if(session_id: str, request: WhatIfRequest, context: RequestContext) -> ApiEnvelope[WhatIfResultDto]` | What-if scenario evaluation with bar-level reads. | Missing |
| `preview_simulated_trade(session_id: str, request: SimulatedTradePreviewRequest, context: RequestContext) -> ApiEnvelope[TradePreviewDto]` | Simulated trading: pending orders, position modify/close/partial-close, order modify/delete, trades and positions listings. | Missing |

## FEAT-API-14: Live Trading Session Routes (api.routes.live)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_live_session(request: LiveSessionCreateRequest, context: RequestContext) -> ApiEnvelope[LiveSessionDto]` | Live session CRUD, start/resume, and statistics. | Missing |
| `get_live_session_market_data(session_id: str, context: RequestContext) -> ApiEnvelope[LiveMarketDataDto]` | Session market-data reads. | Missing |
| `create_live_pending_order(session_id: str, request: LivePendingOrderRequest, context: RequestContext) -> ApiEnvelope[OrderDto]` | Governed live order/position mutations: pending orders, cancel, modify, close, close-all. | Missing |
| `stream_live_session_events(session_id: str, request: WebSocketRequest, principal: ActorContext) -> None` | Live session WebSocket event stream. | Missing |

## FEAT-API-15: Frontend API Client and Governance Libraries (ui/src/lib)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validateApiEnvelope<T>(payload: unknown, schema: RuntimeSchema<T>) -> AgenticResponse<T>` | Runtime envelope/contract validation against the route catalog (with contract-drift detection and canonical DTO adaptation). | Missing |
| `agenticApiRequest<T>(request: AgenticApiRequest<T>) -> Promise<AgenticResponse<T>>` | Typed network client with retry policy, staleness evaluation, and structured errors (with domain clients: backtest, market data, edge lab, optimization, simulator, strategy, trades, risk, live trading). | Missing |
| `governedWriteContext(input: GovernedWriteInput) -> GovernedWriteOptions` | Frontend governed-write preflight (fail-closed) with blocked-write telemetry. | Missing |
| `emitApiTelemetry(event: ApiTelemetryEvent) -> void` | Sanitized frontend telemetry with stale-data warnings. | Missing |
| `sanitizePageContext(input: RawPageContext, policy: PageContextPolicy) -> PageContextPayload` | Page-context sanitization and registration for context-aware chat. | Missing |
| `routeManifest() -> readonly FrontendRouteContract[]` | Frontend route manifest and resolution. | Missing |

## FEAT-API-16: Frontend Workspaces and Components (ui/src/components)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `AppShell(props: AppShellProps) -> ReactElement` | Application shell with protected layouts and offline banner. | Missing |
| `StrategyList` / `StrategyEditor` / `VersionDiffViewer` | Strategy workspace components. | Missing |
| `EdgeLabWorkspace` / `ScorecardEvidencePanel` / `IndicatorChart` | Edge Lab research workspace. | Missing |
| `PerformanceWorkspace` / `TradeDetailPanel` / `PerformanceChart` | Performance analysis workspace. | Missing |
| `EmergencyKillSwitchControl` / `ManualTradeIntentPanel` / `LiveReadinessSummary` | Operator control components with confirmation and network triggers. | Missing |
| `AiChatPanel` / `streamAiChatResponse` / `listAiChatThreads` | Streaming AI chat components and clients. | Missing |
| `DashboardOverview` / `EquityCurvePanel` | Dashboard components. | Missing |
| `SimulatorWorkspace` / `SimulationTradeDialog` | Interactive simulator workspace. | Missing |
| `LiveWorkspace` / `LiveOrderControl` | Live trading workspace with preflight order control. | Missing |
| `LoginForm` / `RegistrationForm` | Authentication forms (with `DocumentationNavigation`, `MarkdownDocument`, `DocumentEditor` docs components and `assertPresentationOnly` boundary check). | Missing |

---

**Note:** the API gateway owns no business logic — every route delegates to owning services through typed clients, all writes are governed (idempotency keys, approval evidence, authoritative backend live gates), and all outputs pass envelope, versioning, pagination, and redaction contracts. The frontend enforces the same contracts at runtime and treats its preflight checks as advisory; the backend gate is authoritative.
