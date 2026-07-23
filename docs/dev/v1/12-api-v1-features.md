## FEAT-API-01: FastAPI application skeleton for the operator API (app.services.api.app)

| Function | Purpose |
|----------|---------|
| `get_operator_api_dependencies(request: Request) -> OperatorApiDependencies` | Expose the operator API dependency container to route handlers. |
| `create_app(dependencies: OperatorApiDependencies \| None = None) -> FastAPI` | Build the migration-era operator API application. |


## FEAT-API-02: Approval API routes for the operator control plane (app.services.api.approvals)

| Function | Purpose |
|----------|---------|
| `LiveExecutionApprovalCreateBody` (model) | Live Execution Approval Create Body data model. |
| `ApprovalVoteBody` (model) | Approval Vote Body data model. |
| `OverrideApprovalCreateBody` (model) | Override Approval Create Body data model. |
| `KillSwitchRecoveryApprovalBody` (model) | Kill Switch Recovery Approval Body data model. |
| `create_live_execution_approval(body: LiveExecutionApprovalCreateBody, request: Request) -> dict[str, object]` | Create live execution approval. |
| `create_policy_change_approval(body: LiveExecutionApprovalCreateBody, request: Request) -> dict[str, object]` | Create policy change approval. |
| `create_override_approval(body: OverrideApprovalCreateBody, request: Request) -> dict[str, object]` | Create override approval. |
| `create_kill_switch_recovery_approval(body: KillSwitchRecoveryApprovalBody, request: Request) -> dict[str, object]` | Create kill switch recovery approval. |
| `vote_live_execution_approval(approval_id: str, body: ApprovalVoteBody, request: Request) -> dict[str, object]` | Vote live execution approval operation. |


## FEAT-API-03: Authentication and authorization helpers for the operator API (app.services.api.auth)

| Function | Purpose |
|----------|---------|
| `OperatorPrincipal` (model) | Minimal operator identity extracted from request headers. |
| `OperatorAuthMiddleware.dispatch(request: Request, call_next)` | Attach a minimal operator principal to protected operator API requests. |
| `get_operator_principal(request: Request) -> OperatorPrincipal` | Return the authenticated operator principal for a request. |
| `require_operator_role(request: Request, *allowed_roles: str) -> OperatorPrincipal` | Enforce that the current operator has one of the allowed roles. |


## FEAT-API-04: Authentication utility functions (app.services.api.auth_utils)

| Function | Purpose |
|----------|---------|
| `generate_token(user_id: int, db_manager: DatabaseManager) -> str` | Generate a secure random token for user authentication and store in DB. |
| `verify_token(token: str, db_manager: DatabaseManager) -> int \| None` | Verify a token and return the associated user ID. |
| `invalidate_token(token: str, db_manager: DatabaseManager) -> None` | Invalidate a token (logout). |
| `authenticate_user(username: str, password: str, db_manager: DatabaseManager) -> dict` | Authenticate a user with username and password. |
| `get_user_id_from_token(authorization: str \| None = Header(None)) -> int` | Validate token and return user ID. |


## FEAT-API-05: Dependency wiring for the migration-era operator API (app.services.api.dependencies)

| Function | Purpose |
|----------|---------|
| `OperatorApiDependencies` (model) | Shared service container for the operator API skeleton. |
| `resolve_sqlite_database_path(database_url: str) -> Path` | Resolve the SQLite database path from a runtime database URL. |
| `build_operator_api_dependencies(*, settings: RuntimeSettings \| None = None) -> OperatorApiDependencies` | Construct the minimum dependency set needed by the operator API. |


## FEAT-API-06: SSE event stream for the operator dashboard (app.services.api.events)

| Function | Purpose |
|----------|---------|
| `stream_operator_events() -> StreamingResponse` | Stream operator events. |


## FEAT-API-07: Health checks for the operator API skeleton (app.services.api.health)

| Function | Purpose |
|----------|---------|
| `check_app_health(dependencies: OperatorApiDependencies) -> dict[str, object]` | Return a minimal application heartbeat. |
| `check_database_health(dependencies: OperatorApiDependencies) -> dict[str, object]` | Run the smallest possible database connectivity check. |
| `check_redis_health(dependencies: OperatorApiDependencies) -> dict[str, object]` | Report the current event-backend status. |
| `check_schema_registry_health(dependencies: OperatorApiDependencies) -> dict[str, object]` | Validate that the schema registry has active seeded contracts. |


## FEAT-API-08: FastAPI application main entry point (app.services.api.main)

| Function | Purpose |
|----------|---------|
| `lifespan(app: FastAPI)` | Manage application lifespan events. |
| `IntentClassificationMiddleware.dispatch(request: Request, call_next)` | Classify request intent and attach routing metadata. |
| `health_check()` | Return health check status. |


## FEAT-API-09: API middleware for secret-safe request logging (app.services.api.middleware.security)

| Function | Purpose |
|----------|---------|
| `SecretRedactionMiddleware.dispatch(request: Request, call_next)` | Sanitize request metadata before it is written to logs. |


## FEAT-API-10: Pydantic models for API requests and responses (app.services.api.models)

| Function | Purpose |
|----------|---------|
| `RegisterRequest` (model) | User registration request. |
| `LoginRequest` (model) | User login request. |
| `UserResponse` (model) | User data response. |
| `AuthResponse` (model) | Authentication response with token and user data. |
| `ErrorResponse` (model) | Error response. |
| `UserSettingsResponse` (model) | User settings response. |
| `UpdateUserSettingsRequest` (model) | Update user settings request. |
| `BrokerStatusResponse` (model) | Broker status response. |
| `DashboardEquityPoint` (model) | Single dashboard equity point. |
| `DashboardEquityCurveResponse` (model) | Dashboard equity curve response. |
| `DashboardDailyPnlPoint` (model) | Single daily PnL point for the dashboard. |
| `DashboardActiveStrategyItem` (model) | Active strategy row for the dashboard. |
| `DashboardSummaryResponse` (model) | Dashboard summary response. |
| `MarketStatus` (model) | Market status details. |
| `MarketHoursResponse` (model) | Response model for market hours. |
| `SystemStatusResponse` (model) | System status response. |
| `ResourceUsageResponse` (model) | Resource usage response. |


## FEAT-API-11: Intent classifier and routing dispatcher for the API layer (app.services.api.router)

| Function | Purpose |
|----------|---------|
| `Intent` (model) | Request intent categories (Playbook §3.2). |
| `RoutingMetadata.__init__(intent: Intent = Intent.UNKNOWN, priority: int = 0, session_id: str \| None = None, user_id: int \| None = None) -> None` | Standard routing metadata attached to every request. |
| `RoutingMetadata.to_dict() -> dict[str, Any]` | Standard routing metadata attached to every request. |
| `IntentClassifier.__init__() -> None` | Rule-based intent classifier with fallback to UNKNOWN. |
| `IntentClassifier.classify(path: str) -> Intent` | Classify request path into an Intent. |
| `IntentClassifier.classify_and_metadata(path: str, *, priority: int = 0, session_id: str \| None = None, user_id: int \| None = None) -> RoutingMetadata` | Classify path and return full routing metadata. |
| `IntentClassifier.add_route(prefix: str, intent: Intent) -> None` | Add or override a route mapping. |
| `IntentClassifier.allowed_intents() -> list[Intent]` | Return all known intents from route map. |
| `IntentClassifier.route_map -> dict[str, Intent]` | Return a copy of the current route-prefix mapping. |


## FEAT-API-12: CEO chat endpoints for the canonical HaruQuant API package (app.services.api.routes.ai_chat)

| Function | Purpose |
|----------|---------|
| `ThreadCreatePayload` (model) | Thread Create Payload data model. |
| `ThreadRenamePayload` (model) | Thread Rename Payload data model. |
| `ThreadRetentionPayload` (model) | Thread Retention Payload data model. |
| `LifecycleRunPayload` (model) | Lifecycle Run Payload data model. |
| `MessageCreatePayload` (model) | Message Create Payload data model. |
| `ApprovalPayload` (model) | Approval Payload data model. |
| `PaperExecutePayload` (model) | Paper Execute Payload data model. |
| `ContextResolvePayload` (model) | Context Resolve Payload data model. |
| `default_database_path() -> Path` | Default database path operation. |
| `get_user_id() -> str` | Return user id. |
| `get_conversation_service() -> ConversationService` | Return conversation service. |
| `get_ceo_chat_gateway() -> CEOChatGateway` | Return ceo chat gateway. |
| `list_threads(q: Annotated[str \| None, Query()] = None, include_archived: Annotated[bool, Query()] = False, user_id: str = Depends(get_user_id), conversations: ConversationService = Depends(get_conversation_service)) -> list[ChatThread]` | List threads. |
| `create_thread(payload: ThreadCreatePayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Create thread. |
| `get_thread(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Return thread. |
| `rename_thread(thread_id: str, payload: ThreadRenamePayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Rename thread operation. |
| `update_thread_context(thread_id: str, payload: ThreadCreatePayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Update thread context. |
| `delete_thread(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, bool]` | Delete thread. |
| `archive_thread(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Archive thread operation. |
| `restore_thread(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Restore thread operation. |
| `purge_thread(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, bool]` | Purge thread operation. |
| `get_thread_retention(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatRetentionPolicyDetail` | Return thread retention. |
| `update_thread_retention(thread_id: str, payload: ThreadRetentionPayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatThreadDetail` | Update thread retention. |
| `run_retention_lifecycle(payload: LifecycleRunPayload, conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, Any]` | Run retention lifecycle. |
| `export_thread(thread_id: str, format: str = 'markdown', user_id: str = Depends(get_user_id), conversations: ConversationService = Depends(get_conversation_service)) -> Response` | Export thread. |
| `create_message(thread_id: str, payload: MessageCreatePayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> ChatMessage` | Create message. |
| `list_tools() -> list[dict[str, Any]]` | List tools. |
| `resolve_context(payload: ContextResolvePayload) -> dict[str, Any]` | Resolve context. |
| `list_signal_proposals(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> list[dict[str, Any]]` | List signal proposals. |
| `save_signal_proposal_to_watchlist(thread_id: str, proposal_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, Any]` | Save signal proposal to watchlist. |
| `queue_signal_proposal_for_review(thread_id: str, proposal_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, Any]` | Queue signal proposal for review operation. |
| `list_action_drafts(thread_id: str, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> list[dict[str, Any]]` | List action drafts. |
| `request_action_draft_approval(thread_id: str, draft_id: str, payload: ApprovalPayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, Any]` | Request action draft approval operation. |
| `execute_paper_action_draft(thread_id: str, draft_id: str, payload: PaperExecutePayload, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)]) -> dict[str, Any]` | Execute paper action draft operation. |
| `stream_response(thread_id: str, payload: ChatTurnRequest, user_id: Annotated[str, Depends(get_user_id)], gateway: Annotated[CEOChatGateway, Depends(get_ceo_chat_gateway)]) -> StreamingResponse` | Stream response. |
| `regenerate_response(thread_id: str, payload: ChatTurnRequest, user_id: Annotated[str, Depends(get_user_id)], conversations: Annotated[ConversationService, Depends(get_conversation_service)], gateway: Annotated[CEOChatGateway, Depends(get_ceo_chat_gateway)]) -> StreamingResponse` | Regenerate response operation. |


## FEAT-API-13: Authentication routes (app.services.api.routes.auth)

| Function | Purpose |
|----------|---------|
| `register(request: RegisterRequest)` | Register a new user. |
| `login(request: LoginRequest)` | Authenticate a user and return an access token. |
| `logout(authorization: Annotated[str \| None, Header()] = None)` | Logout the current user. |


## FEAT-API-14: Backtest API routes and helpers (app.services.api.routes.backtest)

| Function | Purpose |
|----------|---------|
| `PortfolioRunResult.__init__(run_result: Any, initial_balance: float \| None = None) -> None` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.trades -> list[Any]` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.equity_curve -> list[Any]` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.final_value -> float` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.total_return() -> float` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.metadata() -> dict[str, Any]` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.analytics() -> dict[str, Any]` | Small result adapter returned by route-local portfolio backtests. |
| `PortfolioRunResult.result() -> dict[str, pd.DataFrame]` | Small result adapter returned by route-local portfolio backtests. |
| `portfolio_run(config: dict[str, Any] \| Any \| None = None, user_id: int \| None = None) -> PortfolioRunResult` | Run a simulation and return the route-local portfolio result adapter. |
| `BacktestRequest` (model) | Request payload for running a backtest. |
| `BacktestResponse` (model) | Response model for backtest runs. |
| `BacktestOverviewResponse` (model) | Backend-computed overview payload for a backtest. |
| `BacktestUpdateRequest` (model) | Request payload for updating backtest metadata. |
| `PortfolioBacktestRequest` (model) | Request payload for running a multi-symbol portfolio backtest. |
| `PortfolioBacktestResponse` (model) | Response model for portfolio backtest runs. |
| `run_backtest(strategy_id: int, request: BacktestRequest, background_tasks: BackgroundTasks, authorization: Annotated[str \| None, Header()] = None) -> BacktestResponse` | Run a backtest for a strategy. |
| `list_strategy_backtests(strategy_id: int) -> list[BacktestResponse]` | List all backtests for a strategy. |
| `get_backtest(backtest_id: int) -> BacktestResponse` | Get a specific backtest. |
| `get_backtest_overview(backtest_id: int) -> BacktestOverviewResponse` | Get the backend-computed performance overview for a backtest. |
| `backtest_logs_websocket(websocket: WebSocket, backtest_id: int) -> None` | Websocket endpoint for streaming backtest logs in real time. |
| `list_all_backtests(authorization: str = AUTH_HEADER, limit: int = 100) -> list[BacktestResponse]` | List all backtests across all strategies. |
| `update_backtest(backtest_id: int, request: BacktestUpdateRequest) -> BacktestResponse` | Update backtest metadata (alias, description). |
| `delete_backtest_endpoint(backtest_id: int) -> None` | Delete a backtest and all associated data. |
| `run_portfolio_backtest(strategy_id: int, request: PortfolioBacktestRequest, background_tasks: BackgroundTasks, authorization: Annotated[str \| None, Header()] = None) -> PortfolioBacktestResponse` | Run a portfolio backtest with multiple symbols. |


## FEAT-API-15: Broker routes (app.services.api.routes.dashboard.broker)

| Function | Purpose |
|----------|---------|
| `get_last_credentials() -> dict[str, Any]` | Get last known MT5 credentials for auto-reconnect. |
| `get_broker_status(authorization: Annotated[str \| None, Header()] = None)` | Get current broker connection status and account info. |
| `get_equity_curve(authorization: Annotated[str \| None, Header()] = None)` | Build dashboard equity curve from MT5 historical deals. |
| `get_dashboard_summary(authorization: Annotated[str \| None, Header()] = None)` | Return dashboard summary metrics backed by live MT5 and session data. |


## FEAT-API-16: Currency Strength API Routes (app.services.api.routes.dashboard.currency_strength)

| Function | Purpose |
|----------|---------|
| `CurrencyStrengthResponse` (model) | Response model for individual currency strength. |
| `CurrencyPairSignalResponse` (model) | Response model for currency pair trading signal. |
| `CurrencyStrengthDataResponse` (model) | Complete currency strength analysis response. |
| `get_currency_strength(authorization: Annotated[str \| None, Header()] = None, pairs_count: int = 15, tf1: str = 'M1', tf2: str = 'M5', tf3: str = 'H1') -> CurrencyStrengthDataResponse` | Get real-time multi-timeframe currency strength analysis from MT5 data. |


## FEAT-API-17: Forex calendar dashboard route (app.services.api.routes.dashboard.forex_calendar)

| Function | Purpose |
|----------|---------|
| `get_forex_calendar(range_key: Annotated[Literal['today', 'tomorrow', 'this_week', 'next_week', 'next_month', 'yesterday', 'up_next', 'last_week', 'last_month'], Query()] = 'this_week')` | Return the normalized Forex Factory weekly calendar feed. |


## FEAT-API-18: Market Hours API endpoint (app.services.api.routes.dashboard.market_hours)

| Function | Purpose |
|----------|---------|
| `is_market_open(current_time_local: datetime, open_time: time, close_time: time, lunch_start: time \| None = None, lunch_end: time \| None = None) -> bool` | Check if a market is open based on local time. |
| `format_timedelta(td: timedelta) -> str` | Format a timedelta as a short human-readable string. |
| `get_market_message(current_time_local: datetime, open_time: time, close_time: time, lunch_start: time \| None = None, lunch_end: time \| None = None, is_open: bool = False) -> str` | Get a status message like "Opening in X" or "Closing in X". |
| `get_market_hours()` | Get status of major financial markets. |


## FEAT-API-19: System status and resources routes (app.services.api.routes.dashboard.system)

| Function | Purpose |
|----------|---------|
| `get_system_status()` | Get backend and database status. |
| `get_resource_usage()` | Get system resource usage (CPU, Memory). |


## FEAT-API-20: Data API routes for market instruments and dataset preparation (app.services.api.routes.data)

| Function | Purpose |
|----------|---------|
| `DatasetPrepareRequest` (model) | Request model for preparing a reusable dataset. |
| `MT5DataSource.__init__(user_id: int, start_date: datetime \| None, end_date: datetime \| None, count: int \| None) -> None` | MT5 data source wrapper. |
| `MT5DataSource.fetch_data(symbol: str, timeframe: str, start_pos: int, end_pos: int) -> pd.DataFrame \| None` | MT5 data source wrapper. |
| `DukascopyDataSource.__init__(start_date: str \| None, end_date: str \| None, count: int \| None) -> None` | Dukascopy data source wrapper. |
| `DukascopyDataSource.fetch_data(symbol: str, timeframe: str, start_pos: int, end_pos: int) -> pd.DataFrame \| None` | Dukascopy data source wrapper. |
| `json_safe_value(value: Any) -> Any` | Safely convert common data types to JSON-serializable values. |
| `report_to_dict(report: DataQualityReportModel) -> dict[str, Any]` | Serialize a DataQualityReportModel to a dictionary. |
| `serialize_prepared_dataset(prepared: PreparedDataset) -> dict[str, Any]` | Serialize a PreparedDataset to a dictionary. |
| `extract_mt5_bars_frame(result: dict[str, Any]) -> pd.DataFrame \| None` | Extract MT5 bars from a broker response envelope. |
| `extract_mt5_symbols(result: dict[str, Any]) -> list[dict[str, Any]]` | Extract symbol metadata from a broker response envelope. |
| `resolve_symbol_price_metadata(source: DataSource, symbol: str) -> dict[str, Any]` | Resolve broker price display metadata for a symbol when available. |
| `parse_date(value: str \| None) -> datetime \| None` | Parse an ISO date string. |
| `hash_jsonable(payload: dict[str, Any]) -> str` | Stable hash of a JSON-serializable dictionary. |
| `dataset_fingerprint(prepared: PreparedDataset) -> str` | Generate a content-based fingerprint for a prepared dataset. |
| `deserialize_prepared_dataset(payload: dict[str, Any]) -> PreparedDataset` | Reconstruct a PreparedDataset from its serialized dictionary form. |
| `resolve_prepared_dataset_from_payload(payload: dict[str, Any] \| None) -> PreparedDataset \| None` | Helper to safely resolve a dataset from a request payload. |
| `validate_range_params(range_by: str, start_date_str: str \| None, end_date_str: str \| None, number_of_bars: int \| None) -> tuple[str, datetime \| None, datetime \| None, int \| None]` | Validate and parse common range parameters. |
| `create_data_source(data_source: str, user_id: int, start_date: datetime \| None, end_date: datetime \| None, number_of_bars: int \| None, string_dates: tuple[str \| None, str \| None] = (None, None)) -> DataSource` | Create a data source object based on source type. |
| `default_session_hours() -> dict[str, list[int]]` | Return default trading session hour buckets. |
| `get_symbols(authorization: Annotated[str \| None, Header()] = None)` | Get all available symbols from MT5 terminal. |
| `prepare_dataset_endpoint(request: DatasetPrepareRequest, authorization: Annotated[str \| None, Header()] = None)` | Prepare and serialize a reusable dataset. |


## FEAT-API-21: Documentation file management routes (app.services.api.routes.docs)

| Function | Purpose |
|----------|---------|
| `FileNode` (model) | Tree node representing a documentation file or directory. |
| `SaveFileRequest` (model) | Request payload for saving a documentation file. |
| `get_directory_structure(root_dir: Path, relative_path: str = '') -> list[FileNode]` | Return a tree structure for markdown files under a root directory. |
| `validate_path(request_path: str) -> Path` | Validate and resolve a path within the docs root. |
| `get_files()` | Get the tree structure of the documentation directory. |
| `get_content(path: str = CONTENT_PATH_QUERY)` | Read the content of a markdown file. |
| `save_file(request: SaveFileRequest)` | Save content to a markdown file. |
| `delete_file(path: str = CONTENT_PATH_QUERY)` | Delete a markdown file. |


## FEAT-API-22: Edge Lab API routes (app.services.api.routes.edge)

| Function | Purpose |
|----------|---------|
| `EdgeLabRunRequest` (model) | Request model for running Edge Lab analysis. |
| `EdgeLabSummary` (model) | Summary of Edge Lab run results. |
| `EdgeLabRunResponse` (model) | Response model for Edge Lab run, containing results and summary. |
| `EdgeLabSeasonalityRequest` (model) | Request model for seasonality analysis. |
| `EdgeCoreMetricRequest` (model) | Request model for Core Metric MVP profile generation. |
| `EdgeLabDatasetRequest` (model) | Request model for preparing a reusable Edge Lab dataset. |
| `EdgeMarketStructureRequest` (model) | Request model for Market Structure profile generation. |
| `EdgeProfileSnapshotRequest` (model) | Request model for persisting one versioned Edge Lab profile snapshot. |
| `EdgeUnsupervisedStructureRequest` (model) | Request model for unsupervised PCA/K-Means structure analysis. |
| `EdgeLabAutomationRequest` (model) | Request model for automated single-symbol Edge Lab execution. |
| `EdgeLabAutomationBatchRequest` (model) | Request model for automated batch Edge Lab execution. |
| `EdgeLabAutomationScheduleRequest` (model) | Request model for scheduled Edge Lab refresh workflow. |
| `MT5DataSource.__init__(user_id: int, start_date: datetime \| None, end_date: datetime \| None, count: int \| None) -> None` | Initialize MT5DataSource. |
| `MT5DataSource.fetch_data(symbol: str, timeframe: str, start_pos: int, end_pos: int) -> pd.DataFrame \| None` | Fetch data from MT5. |
| `DukascopyDataSource.__init__(start_date: str \| None, end_date: str \| None, count: int \| None) -> None` | Initialize DukascopyDataSource. |
| `DukascopyDataSource.fetch_data(symbol: str, timeframe: str, start_pos: int, end_pos: int) -> pd.DataFrame \| None` | Fetch data from Dukascopy. |
| `run_scheduled_edge_lab_refresh() -> dict[str, Any]` | Run one scheduled Edge Lab batch refresh from environment configuration. |
| `run_edge_lab(request: EdgeLabRunRequest, authorization: str = AUTH_HEADER)` | Run Edge Lab analysis. |
| `list_edge_runs(symbol: str \| None = None, timeframe: str \| None = None, eds_type: str \| None = None, verdict: str \| None = None, edge_confirmed_only: bool = False, limit: int = 100, offset: int = 0)` | List edge analysis runs. |
| `count_edge_runs(symbol: str \| None = None, timeframe: str \| None = None, eds_type: str \| None = None, verdict: str \| None = None, edge_confirmed_only: bool = False)` | Count edge analysis runs. |
| `get_edge_run_summary(symbol: str \| None = None, timeframe: str \| None = None, verdict: str \| None = None, edge_confirmed_only: bool = False, sort_by: str = 'latest_created_at', sort_dir: str = 'desc', limit: int = 25, offset: int = 0)` | Get summary of edge analysis runs. |
| `prepare_edge_lab_dataset(request: EdgeLabDatasetRequest, authorization: str = AUTH_HEADER)` | Prepare and serialize a reusable Edge Lab dataset. |
| `run_seasonality_lab(request: EdgeLabSeasonalityRequest, authorization: str = AUTH_HEADER)` | Run seasonality analysis. |
| `get_edge_run(run_id: int)` | Get specific Edge Lab run. |
| `get_edge_run_stats(run_id: int)` | Get stats for a specific Edge Lab run. |
| `get_edge_run_trades(run_id: int)` | Get trades for a specific Edge Lab run. |
| `delete_edge_run(run_id: int) -> None` | Delete an Edge Lab run. |
| `run_core_metrics(request: EdgeCoreMetricRequest, authorization: str = AUTH_HEADER)` | Run the Core Metric MVP profile for one symbol. |
| `list_core_metric_runs(symbol: str \| None = None, timeframe: str \| None = None, limit: int = 50, offset: int = 0)` | List stored Core Metric profile runs. |
| `get_core_metric_run(run_id: int)` | Get one stored Core Metric profile. |
| `delete_core_metric_run(run_id: int) -> None` | Delete a stored Core Metric profile. |
| `run_market_structure(request: EdgeMarketStructureRequest, authorization: str = AUTH_HEADER)` | Run the Market Structure profile for one symbol. |
| `run_unsupervised_structure(request: EdgeUnsupervisedStructureRequest, authorization: str = AUTH_HEADER)` | Run PCA/K-Means unsupervised structure analysis for one symbol. |
| `list_market_structure_runs(symbol: str \| None = None, timeframe: str \| None = None, limit: int = 50, offset: int = 0)` | List stored Market Structure runs. |
| `get_market_structure_run(run_id: int)` | Get one stored Market Structure profile. |
| `delete_market_structure_run(run_id: int) -> None` | Delete a stored Market Structure profile. |
| `get_market_structure_validation(limit: int = 20, horizon_bars: int = 48, refresh: bool = True, authorization: str = AUTH_HEADER)` | Validate saved Market Structure runs against simple forward realized behavior. |
| `list_market_structure_evaluations(symbol: str \| None = None, timeframe: str \| None = None, limit: int = 100, offset: int = 0)` | List persisted Market Structure forward-evaluation rows. |
| `refresh_market_structure_evaluations(limit: int = 100, horizon_bars: int = 48, authorization: str = AUTH_HEADER)` | Refresh persisted Market Structure forward-evaluation rows. |
| `get_market_structure_calibration(limit: int = 50, horizon_bars: int = 48, authorization: str = AUTH_HEADER)` | Evaluate a small grid of top-level verdict thresholds against forward validation rows. |
| `get_market_structure_profile_calibration(limit: int = 100, horizon_bars: int = 48, authorization: str = AUTH_HEADER)` | Group calibration results by symbol/timeframe profile class. |
| `get_market_structure_metric_calibration(limit: int = 50, horizon_bars: int = 48, authorization: str = AUTH_HEADER)` | Evaluate a small grid of lower-level score normalization bands. |
| `get_market_structure_stability(request: EdgeMarketStructureRequest, authorization: str = AUTH_HEADER)` | Evaluate block-by-block Market Structure stability on the current dataset. |
| `get_market_structure_robustness(request: EdgeMarketStructureRequest, authorization: str = AUTH_HEADER)` | Evaluate verdict robustness across nearby parameter variants. |
| `run_edge_lab_automation(request: EdgeLabAutomationRequest, authorization: str = AUTH_HEADER)` | Run the progressive Edge Lab chain for one symbol with cache/dependency metadata. |
| `run_edge_lab_automation_batch(request: EdgeLabAutomationBatchRequest, authorization: str = AUTH_HEADER)` | Run the progressive Edge Lab chain across a batch of symbols. |
| `refresh_edge_lab_automation_schedule(request: EdgeLabAutomationScheduleRequest, authorization: str = AUTH_HEADER)` | Run one scheduled-style refresh workflow for a symbol batch. |
| `save_scorecard_snapshot(request: EdgeProfileSnapshotRequest, authorization: str = AUTH_HEADER)` | Persist one versioned Edge Lab profile snapshot from the progressive tab chain. |
| `list_scorecard_snapshots(symbol: str \| None = None, timeframe: str \| None = None, limit: int = 50, offset: int = 0)` | List stored Edge Lab profile snapshots. |
| `get_scorecard_snapshot(snapshot_id: int)` | Get one stored Edge Lab profile snapshot. |
| `compare_scorecard_snapshots(left_snapshot_id: int, right_snapshot_id: int)` | Compare two stored Edge Lab profile snapshots. |
| `export_scorecard_snapshot_parquet(snapshot_id: int)` | Export one profile snapshot's wide metrics to a Parquet artifact. |
| `get_scorecard_snapshot_report(snapshot_id: int)` | Build a machine-readable complete pair report from one stored snapshot. |
| `export_scorecard_snapshot_report(snapshot_id: int)` | Export Markdown and JSON reports for one stored snapshot. |
| `export_scorecard_snapshot_comparison_markdown(left_snapshot_id: int, right_snapshot_id: int)` | Export a Markdown comparison report for two stored snapshots. |


## FEAT-API-23: Routes for importing external backtest trades (app.services.api.routes.import_trades)

| Function | Purpose |
|----------|---------|
| `import_sqx_trades(file: Annotated[UploadFile, File(...)], strategy_name: Annotated[str, Form(...)], symbol: Annotated[str, Form(...)], timeframe: Annotated[str, Form(...)], user_id: Annotated[int, Depends(get_user_id_from_token)], alias: Annotated[str \| None, Form()] = None, description: Annotated[str \| None, Form()] = None, initial_balance: Annotated[float, Form()] = 10000.0)` | Import trades from a Strategy Quant X CSV export. |


## FEAT-API-24: Live Trading API Routes (app.services.api.routes.live)

| Function | Purpose |
|----------|---------|
| `MT5Utils.add_pips_to_price(price: float, pips: float, symbol_info, direction: int = 1) -> float` | Add pips to price. |
| `SessionCreateRequest` (model) | Request model for creating a new live trading session. |
| `SessionUpdateRequest` (model) | Request model for updating a session. |
| `SessionResponse` (model) | Response model for session data. |
| `SessionStatusResponse` (model) | Lightweight response for session status. |
| `SessionStatisticsResponse` (model) | Comprehensive session statistics. |
| `StrategyAddRequest` (model) | Request model for adding a strategy to a session. |
| `StrategyUpdateRequest` (model) | Request model for updating strategy configuration. |
| `PositionModifyRequest` (model) | Request model for modifying a position. |
| `ManualOrderRequest` (model) | Request model for placing a manual order. |
| `PendingOrderRequest` (model) | Request model for placing a pending order. |
| `SignalResponse` (model) | Response model for signal data. |
| `PositionResponse` (model) | Response model for position data. |
| `create_session(request: SessionCreateRequest, authorization: str = AUTH_HEADER)` | Create a new live trading session. |
| `list_sessions(authorization: str = AUTH_HEADER, status_filter: str \| None = SESSION_STATUS_FILTER_QUERY)` | List all live trading sessions for the authenticated user. |
| `get_session(session_id: int, authorization: str = AUTH_HEADER)` | Get details of a specific live trading session. |
| `update_session(session_id: int, request: SessionUpdateRequest, authorization: str = AUTH_HEADER)` | Update a live trading session configuration. |
| `delete_session(session_id: int, authorization: str = AUTH_HEADER) -> None` | Delete a live trading session. |
| `start_session(session_id: int, authorization: str = AUTH_HEADER)` | Start a live trading session. |
| `stop_session(session_id: int, authorization: str = AUTH_HEADER)` | Stop a live trading session. |
| `pause_session(session_id: int, authorization: str = AUTH_HEADER)` | Pause a live trading session. |
| `resume_session(session_id: int, authorization: str = AUTH_HEADER)` | Resume a paused live trading session. |
| `get_session_status(session_id: int, authorization: str = AUTH_HEADER)` | Get lightweight real-time status of a session. |
| `get_session_statistics(session_id: int, authorization: str = AUTH_HEADER)` | Get comprehensive session statistics. |
| `get_market_data(session_id: int, symbol: str = CANDLES_SYMBOL_QUERY, timeframe: str = CANDLES_TIMEFRAME_QUERY, count: int = CANDLES_COUNT_QUERY, authorization: str = AUTH_HEADER)` | Get historical candlestick data from MT5 for charting. |
| `get_session_signals(session_id: int, authorization: str = AUTH_HEADER, limit: int = SIGNALS_LIMIT_QUERY, status_filter: str \| None = SIGNALS_STATUS_QUERY)` | Get detected signals for a session. |
| `get_session_positions(session_id: int, authorization: str = AUTH_HEADER, status_filter: str \| None = POSITIONS_STATUS_QUERY)` | Get positions for a session. |
| `get_session_logs(session_id: int, authorization: str = AUTH_HEADER, limit: int = LOGS_LIMIT_QUERY, level: str \| None = LOGS_LEVEL_QUERY, category: str \| None = LOGS_CATEGORY_QUERY)` | Get session logs. |
| `add_strategy_to_session(session_id: int, request: StrategyAddRequest, authorization: str = AUTH_HEADER)` | Add a strategy to a live trading session. |
| `remove_strategy_from_session(session_id: int, strategy_config_id: int, authorization: str = AUTH_HEADER)` | Remove a strategy from a live trading session. |
| `get_session_strategies(session_id: int, authorization: str = AUTH_HEADER)` | Get all strategies configured for a session. |
| `modify_position(session_id: int, position_id: int, request: PositionModifyRequest, authorization: str = AUTH_HEADER)` | Modify an open position's stop loss or take profit. |
| `create_manual_order(session_id: int, request: ManualOrderRequest, authorization: str = AUTH_HEADER)` | Execute a manual order with optional pips-based SL/TP. |
| `get_session_orders(session_id: int, authorization: str = AUTH_HEADER)` | Get pending orders for a session. |
| `cancel_order(session_id: int, ticket: int, authorization: str = AUTH_HEADER)` | Cancel a pending order by ticket. |
| `create_pending_order(session_id: int, request: PendingOrderRequest, authorization: str = AUTH_HEADER)` | Place a pending order with optional pips-based SL/TP. |
| `close_position(session_id: int, position_id: int, authorization: str = AUTH_HEADER)` | Manually close an open position. |
| `close_all_positions(session_id: int, authorization: str = AUTH_HEADER)` | Close all open positions for a session. |
| `websocket_endpoint(websocket: WebSocket, session_id: int) -> None` | Websocket endpoint for real-time live trading updates. |


## FEAT-API-25: Optimization API routes (app.services.api.routes.optimization)

| Function | Purpose |
|----------|---------|
| `start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks, user_id: int = 1)` | Start a new optimization run. |
| `get_optimization_run(optimization_id: int)` | Get details of an optimization run. |
| `get_optimization_results(optimization_id: int, limit: int = 100, order_by: str = 'score')` | Get ranked results for an optimization run. |
| `cancel_optimization(optimization_id: int) -> None` | Cancel a running optimization. |
| `start_walk_forward(request: WalkForwardRequest, background_tasks: BackgroundTasks, user_id: int = 1)` | Start walk-forward analysis. |
| `run_unsupervised_analysis(request: UnsupervisedAnalysisRequest, user_id: int = 1)` | Run standalone unsupervised analysis over market data. |
| `get_unsupervised_report(optimization_id: int)` | Fetch the persisted unsupervised report for one optimization run. |
| `start_monte_carlo(request: MonteCarloRequest, background_tasks: BackgroundTasks)` | Start Monte Carlo simulation. |
| `get_monte_carlo(simulation_id: int)` | Get Monte Carlo simulation results. |
| `run_parametric_monte_carlo(request: ParametricMonteCarloRequest)` | Run Parametric Monte Carlo simulation. |
| `run_position_sizing(request: PositionSizingRequest)` | Run Position Sizing simulation (Linear vs Compounding). |
| `run_consecutive_losing(request: ConsecutiveLosingRequest)` | Run Consecutive Losing simulation for multiple systems. |
| `run_profit_target(request: ProfitTargetRequest)` | Run Profit Target simulation. |
| `run_random_win_rate(request: RandomWinRateRequest)` | Run Random Win Rate simulation. |
| `run_robustness(request: RobustnessRequest)` | Run Robustness simulation. |
| `run_multi_entry(request: MultiEntryRequest)` | Run Multi-Entry simulation. |
| `optimization_progress_websocket(websocket: WebSocket, optimization_id: int) -> None` | Websocket endpoint for real-time optimization progress updates. |


## FEAT-API-26: Risk API routes (app.services.api.routes.risk)

| Function | Purpose |
|----------|---------|
| `PositionSizingRequest` (model) | Position Sizing Request data model. |
| `PositionSizingResponse` (model) | Position Sizing Response data model. |
| `RegimeDetectionRequest` (model) | Regime Detection Request data model. |
| `RegimeStatePayload` (model) | Regime State Payload data model. |
| `RegimeSignalPayload` (model) | Regime Signal Payload data model. |
| `RegimeDetectionResponse` (model) | Regime Detection Response data model. |
| `RiskAllocationRequest` (model) | Risk Allocation Request data model. |
| `RiskAllocationResponse` (model) | Risk Allocation Response data model. |
| `GovernanceEventPayload` (model) | Governance Event Payload data model. |
| `GovernanceReportPayload` (model) | Governance Report Payload data model. |
| `GovernanceRequest` (model) | Governance Request data model. |
| `GovernanceResponse` (model) | Governance Response data model. |
| `calculate_position_size(request: PositionSizingRequest) -> PositionSizingResponse` | Calculate position size using the Python risk PositionSizer. |
| `detect_regime(request: RegimeDetectionRequest, authorization: str = AUTH_HEADER) -> RegimeDetectionResponse` | Run crisis-only or full regime detection from pasted returns input. |
| `calculate_risk_allocation(request: RiskAllocationRequest, authorization: str = AUTH_HEADER) -> RiskAllocationResponse` | Compute target lots and deltas using the live AllocationPlanner. |
| `evaluate_risk_governance(request: GovernanceRequest, authorization: str = AUTH_HEADER) -> GovernanceResponse` | Evaluate current compliance and one candidate add-position check. |


## FEAT-API-27: Settings routes (app.services.api.routes.settings)

| Function | Purpose |
|----------|---------|
| `get_user_id_from_token(authorization: str) -> int` | Extract and verify user ID from authorization token. |
| `get_settings(authorization: str = AUTH_HEADER)` | Get settings (slash route). |
| `get_settings_no_slash(authorization: str = AUTH_HEADER)` | Get settings (no-slash route). |
| `update_settings(request: UpdateUserSettingsRequest, authorization: str = AUTH_HEADER)` | Update user settings. |


## FEAT-API-28: Trading simulator API routes (app.services.api.routes.simulator)

| Function | Purpose |
|----------|---------|
| `cleanup_stale_simulation_leases() -> int` | Clear expired simulator runtime leases during application startup. |
| `start_simulation(payload: SimulationStartRequest, user_id: Annotated[int, Depends(_get_authenticated_user_id)])` | Start a new simulation session. |
| `list_sessions(user_id: Annotated[int, Depends(_get_authenticated_user_id)])` | List sessions for the authenticated user. |
| `list_paused_sessions(user_id: Annotated[int, Depends(_get_authenticated_user_id)])` | List paused sessions for resume. |
| `get_session(session_id: int, session: Annotated[dict[str, Any], Depends(_get_owned_session)])` | Get a simulation session. |
| `update_session(session_id: int, payload: SimulationUpdateRequest, session: Annotated[dict[str, Any], Depends(_get_owned_session)])` | Update speed or pause state. |
| `get_bar(session_id: int, bar_index: int, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Get a specific bar by index. |
| `advance_bars(session_id: int, payload: AdvanceRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Advance the simulation by N bars and return them. |
| `get_positions(session_id: int, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Get current positions and orders for a session. |
| `execute_trade(session_id: int, payload: ManualTradeRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Execute a manual trade within a session. |
| `preview_trade(session_id: int, payload: ManualTradeRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Preview a manual trade without executing it. |
| `place_pending_order(session_id: int, payload: PendingOrderRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Place a pending order within a session. |
| `evaluate_what_if(session_id: int, payload: WhatIfRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Evaluate a hypothetical portfolio change without mutating the live simulator. |
| `modify_position(session_id: int, position_id: int, payload: PositionModifyRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Modify a position's SL/TP. |
| `close_position(session_id: int, position_id: int, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Close a position. |
| `partial_close_position(session_id: int, position_id: int, request: Request, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Partially close a position by the given volume. |
| `modify_order(session_id: int, order_id: int, payload: OrderModifyRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Modify a pending order's price/SL/TP and optionally reduce its volume. |
| `delete_order(session_id: int, order_id: int, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Delete a pending order. |
| `resume_session(session_id: int, user_id: Annotated[int, Depends(_get_authenticated_user_id)], session_data: Annotated[dict[str, Any], Depends(_get_owned_session)])` | Resume a paused session. |
| `seek_session(session_id: int, payload: SeekRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Seek to a bar index. |
| `get_session_trades(session_id: int, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Get the list of trades (for replay mode). |
| `seek_trade(session_id: int, payload: SeekTradeRequest, active: Annotated[SimulatorSession, Depends(_get_running_session)])` | Seek to a specific trade in replay mode. |
| `delete_session(session_id: int, _session: Annotated[dict[str, Any], Depends(_get_owned_session)])` | Delete a session. |
| `stop_and_save_session(session_id: int, user_id: Annotated[int, Depends(_get_authenticated_user_id)], _session: Annotated[dict[str, Any], Depends(_get_owned_session)])` | Stop a simulation session and persist it as a completed backtest run. |


## FEAT-API-29: SQX import routes (app.services.api.routes.sqx)

| Function | Purpose |
|----------|---------|
| `import_sqx_strategies(stage: Annotated[str, Form(...)], file: Annotated[UploadFile, File(...)], mapping: Annotated[str \| None, Form()] = None, import_name: Annotated[str \| None, Form()] = None, purge_missing: Annotated[bool, Form()] = False)` | Import SQX strategies from CSV. |
| `calculate_scores(symbol: Annotated[str \| None, Form()] = None)` | Run scorecard calculation for strategies. |
| `list_strategies(symbol: Annotated[str \| None, Query()] = None, stage: Annotated[str \| None, Query()] = None, limit: Annotated[int, Query(ge=1, le=2000)] = 200, offset: Annotated[int, Query(ge=0)] = 0, sort_by: Annotated[str \| None, Query()] = None, sort_dir: Annotated[str, Query()] = 'desc')` | List SQX strategies with optional filters. |


## FEAT-API-30: Strategy routes for managing trading strategies (app.services.api.routes.strategies)

| Function | Purpose |
|----------|---------|
| `StrategyCatalogCreateRequest` (model) | Strategy Catalog Create Request data model. |
| `StrategyCatalogUpdateRequest` (model) | Strategy Catalog Update Request data model. |
| `StrategyCatalogService.__init__(db_manager: DatabaseManager, governance_repository: GovernanceRepository \| None = None) -> None` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.create_strategy(request: StrategyCatalogCreateRequest, *, user_id: int) -> dict[str, Any]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.list_strategies(*, user_id: int, status: str \| None = None, category: str \| None = None, include_shared: bool = False) -> list[dict[str, Any]]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.get_strategy(strategy_id: int, *, user_id: int \| None = None) -> dict[str, Any]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.update_strategy(strategy_id: int, request: StrategyCatalogUpdateRequest, *, user_id: int) -> dict[str, Any]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.create_strategy_version(*, strategy_id: int, code: str, parameters: dict[str, Any] \| None, user_id: int, strategy_name: str, metadata: dict[str, Any], changelog: str \| None, major_bump: bool = False) -> str` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.delete_strategy(strategy_id: int, *, user_id: int) -> None` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.list_versions(strategy_id: int) -> list[dict[str, Any]]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.get_version_code(*, strategy_id: int, version_id: int, user_id: int) -> dict[str, Any]` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.rollback_version(*, strategy_id: int, version_id: int, user_id: int) -> None` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.export_strategy(*, strategy_id: int, user_id: int) -> str` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCatalogService.import_strategy(*, strategy_id: int, import_path: str, original_filename: str, user_id: int) -> str` | Route-local service for strategy DB rows and versioned source artifacts. |
| `StrategyCreateRequest` (model) | Request payload for creating a strategy. |
| `StrategyUpdateRequest` (model) | Request payload for updating a strategy. |
| `StrategyResponse` (model) | Response model for strategy metadata. |
| `VersionResponse` (model) | Response model for strategy versions. |
| `PerformanceSummaryRequest` (model) | Request payload for summarizing performance. |
| `get_strategy_template(template_name: str) -> dict[str, str]` | Get a strategy template by name. |
| `create_strategy(request: StrategyCreateRequest, user_id: int = 1) -> StrategyResponse` | Create a new strategy. |
| `list_strategies(user_id: int = 1, strategy_status: str \| None = None, category: str \| None = None, include_shared: bool = False) -> list[StrategyResponse]` | List all strategies for a user. |
| `get_strategy(strategy_id: int) -> StrategyResponse` | Get a specific strategy. |
| `update_strategy(strategy_id: int, request: StrategyUpdateRequest, user_id: int = 1) -> StrategyResponse` | Update a strategy. |
| `delete_strategy(strategy_id: int, user_id: int = 1) -> None` | Delete a strategy and all its versions. |
| `list_versions(strategy_id: int) -> list[VersionResponse]` | List all versions of a strategy. |
| `get_version_code(strategy_id: int, version_id: int, user_id: int = 1) -> dict[str, Any]` | Get the code for a specific version. |
| `rollback_version(strategy_id: int, version_id: int, user_id: int = 1) -> dict[str, str]` | Rollback to a specific version (make it the active version). |
| `export_strategy(strategy_id: int, user_id: int = 1) -> FileResponse` | Export strategy as a zip file. |
| `import_strategy(strategy_id: int, file: UploadFile = IMPORT_FILE, user_id: int = 1) -> dict[str, str]` | Import strategy from a zip file. |


## FEAT-API-31: Background scheduler jobs (app.services.api.scheduler)

| Function | Purpose |
|----------|---------|
| `start_scheduler() -> None` | Start the background scheduler if not already running. |
| `shutdown_scheduler() -> None` | Shutdown the background scheduler. |


## FEAT-API-32: Helpers for retrieving Forex Factory calendar export data (app.services.api.services.forex_calendar)

| Function | Purpose |
|----------|---------|
| `fetch_forex_factory_calendar(range_key: RangeKey = 'this_week') -> dict[str, Any]` | Fetch and normalize Forex Factory's weekly calendar export. |


## FEAT-API-33: Pydantic models for simulator API routes (app.services.api.session.models)

| Function | Purpose |
|----------|---------|
| `SimulationStartRequest` (model) | Request to start a simulation session. |
| `SimulationUpdateRequest` (model) | Request to update a simulation session. |
| `ManualTradeRequest` (model) | Request to execute a manual trade. |
| `PendingOrderRequest` (model) | Request to place a pending order. |
| `PositionModifyRequest` (model) | Request to modify a position. |
| `OrderModifyRequest` (model) | Request to modify a pending order. |
| `SeekRequest` (model) | Request to seek to a bar index. |
| `AdvanceRequest` (model) | Request to advance by N synchronized simulator frames. |
| `WhatIfActionRequest` (model) | One hypothetical non-mutating portfolio action. |
| `WhatIfRequest` (model) | Request to evaluate a what-if scenario against the current simulator state. |
| `SeekTradeRequest` (model) | Request to seek to a specific trade index in replay mode. |


## FEAT-API-34: Shared auth/session guards for simulator routes (app.services.api.session.route_guards)

| Function | Purpose |
|----------|---------|
| `get_owned_session_record(*, coordinator: SessionCoordinator[SimulatorSession], session_id: int, user_id: int) -> dict[str, Any]` | Public function for route_guards.get_owned_session_record. |
| `get_running_session(*, coordinator: SessionCoordinator[SimulatorSession], session_id: int) -> SimulatorSession` | Public function for route_guards.get_running_session. |


## FEAT-API-35: Shared helpers for simulator route payloads (app.services.api.session.route_support)

| Function | Purpose |
|----------|---------|
| `normalize_position(position: dict) -> dict` | Public function for route_support.normalize_position. |
| `normalize_order(order: dict) -> dict` | Public function for route_support.normalize_order. |
| `position_info_to_dict(position: Any) -> dict` | Public function for route_support.position_info_to_dict. |
| `order_info_to_dict(order: Any) -> dict` | Public function for route_support.order_info_to_dict. |
| `collect_positions_orders(active: SimulatorSession) -> tuple[list[dict], list[dict]]` | Public function for route_support.collect_positions_orders. |
| `refresh_session_risk_state(active: SimulatorSession) -> None` | Public function for route_support.refresh_session_risk_state. |
| `monitor_refresh_collect(active: SimulatorSession) -> tuple[list[dict], list[dict]]` | Public function for route_support.monitor_refresh_collect. |
| `build_session_state_response(active: SimulatorSession) -> dict[str, Any]` | Public function for route_support.build_session_state_response. |


## FEAT-API-36: Session metadata and lease backend abstractions (app.services.api.session.session_backend)

| Function | Purpose |
|----------|---------|
| `SessionMetadata.from_record(record: dict[str, Any]) -> SessionMetadata` | Public function for session_backend.from_record. |
| `SessionMetadata.as_record() -> dict[str, Any]` | Public function for session_backend.as_record. |
| `SessionRuntimeStore.get_metadata(session_id: int) -> SessionMetadata \| None` | Return metadata for a simulator session. |
| `SessionRuntimeStore.create_metadata(metadata: SessionMetadata) -> None` | Create metadata for a simulator session. |
| `SessionRuntimeStore.update_metadata(session_id: int, patch: dict[str, Any]) -> None` | Patch metadata for a simulator session. |
| `SessionRuntimeStore.acquire_lease(session_id: int, worker_id: str, ttl_seconds: int) -> bool` | Acquire a runtime lease for a simulator session. |
| `SessionRuntimeStore.renew_lease(session_id: int, worker_id: str, ttl_seconds: int) -> bool` | Renew an existing runtime lease for a simulator session. |
| `SessionRuntimeStore.release_lease(session_id: int, worker_id: str) -> None` | Release a runtime lease for a simulator session. |
| `SessionRuntimeStore.clear_expired_leases() -> int` | Clear expired runtime leases and return the affected row count. |
| `SQLiteSessionRuntimeStore.__init__(db_manager: Any) -> None` | Internal function for session_backend.__init__. |
| `SQLiteSessionRuntimeStore.get_metadata(session_id: int) -> SessionMetadata \| None` | Public function for session_backend.get_metadata. |
| `SQLiteSessionRuntimeStore.create_metadata(metadata: SessionMetadata) -> None` | Public function for session_backend.create_metadata. |
| `SQLiteSessionRuntimeStore.update_metadata(session_id: int, patch: dict[str, Any]) -> None` | Public function for session_backend.update_metadata. |
| `SQLiteSessionRuntimeStore.acquire_lease(session_id: int, worker_id: str, ttl_seconds: int) -> bool` | Public function for session_backend.acquire_lease. |
| `SQLiteSessionRuntimeStore.renew_lease(session_id: int, worker_id: str, ttl_seconds: int) -> bool` | Public function for session_backend.renew_lease. |
| `SQLiteSessionRuntimeStore.release_lease(session_id: int, worker_id: str) -> None` | Public function for session_backend.release_lease. |
| `SQLiteSessionRuntimeStore.clear_expired_leases() -> int` | Public function for session_backend.clear_expired_leases. |


## FEAT-API-37: Coordinator for simulator session metadata, lease ownership, and runtimes (app.services.api.session.session_coordinator)

| Function | Purpose |
|----------|---------|
| `SessionCoordinator.__init__(*, store: SessionRuntimeStore, runtimes: SimulatorSessionManager[SessionT], worker_id: str \| None = None, lease_ttl_seconds: int = 30) -> None` | Internal function for session_coordinator.__init__. |
| `SessionCoordinator.get_metadata(session_id: int) -> SessionMetadata \| None` | Public function for session_coordinator.get_metadata. |
| `SessionCoordinator.get_owned_metadata(session_id: int, user_id: int) -> SessionMetadata` | Public function for session_coordinator.get_owned_metadata. |
| `SessionCoordinator.attach_runtime(session_id: int, runtime: SessionT) -> None` | Public function for session_coordinator.attach_runtime. |
| `SessionCoordinator.get_runtime(session_id: int, *, renew: bool = True) -> SessionT \| None` | Public function for session_coordinator.get_runtime. |
| `SessionCoordinator.require_runtime(session_id: int) -> SessionT` | Public function for session_coordinator.require_runtime. |
| `SessionCoordinator.release_runtime(session_id: int) -> SessionT \| None` | Public function for session_coordinator.release_runtime. |
| `SessionCoordinator.renew_lease(session_id: int) -> bool` | Public function for session_coordinator.renew_lease. |
| `SessionCoordinator.update_metadata(session_id: int, patch: dict[str, object]) -> None` | Public function for session_coordinator.update_metadata. |
| `SessionCoordinator.is_owned_by_me(session_id: int) -> bool` | Public function for session_coordinator.is_owned_by_me. |
| `SessionCoordinator.is_lease_expired(session_id: int) -> bool` | Public function for session_coordinator.is_lease_expired. |
| `SessionCoordinator.get_runtime_owner(session_id: int) -> str \| None` | Public function for session_coordinator.get_runtime_owner. |
| `SessionCoordinator.clear_expired_leases() -> int` | Public function for session_coordinator.clear_expired_leases. |


## FEAT-API-38: Thread-safe in-memory simulator session store (app.services.api.session.session_manager)

| Function | Purpose |
|----------|---------|
| `SimulatorSessionManager.__init__() -> None` | Internal function for session_manager.__init__. |
| `SimulatorSessionManager.get(session_id: int) -> SessionT \| None` | Public function for session_manager.get. |
| `SimulatorSessionManager.put(session_id: int, session: SessionT) -> None` | Public function for session_manager.put. |
| `SimulatorSessionManager.remove(session_id: int) -> SessionT \| None` | Public function for session_manager.remove. |


## FEAT-API-39: Simulator session runtime and helpers (app.services.api.session.session_runtime)

| Function | Purpose |
|----------|---------|
| `SimulatorSession.__init__(session_id: int, config: dict[str, Any], db: DatabaseManager) -> None` | Internal function for session_runtime.__init__. |
| `SimulatorSession.apply_mt5_account_defaults() -> None` | Public function for session_runtime.apply_mt5_account_defaults. |
| `SimulatorSession.set_strategy(strategy_instance) -> None` | Public function for session_runtime.set_strategy. |
| `SimulatorSession.set_strategy_map(strategies_by_symbol: dict[str, Any]) -> None` | Public function for session_runtime.set_strategy_map. |
| `SimulatorSession.set_replay_trades(trades) -> None` | Public function for session_runtime.set_replay_trades. |
| `SimulatorSession.load_historical_bars() -> None` | Public function for session_runtime.load_historical_bars. |
| `SimulatorSession.get_bar(index: int)` | Public function for session_runtime.get_bar. |
| `SimulatorSession.process_bar_at_index(index: int)` | Public function for session_runtime.process_bar_at_index. |
| `SimulatorSession.advance_frames(count: int) -> list[dict[str, Any]]` | Public function for session_runtime.advance_frames. |
| `SimulatorSession.get_indicators_at_index(index: int)` | Public function for session_runtime.get_indicators_at_index. |
| `SimulatorSession.execute_trade(request: dict[str, Any])` | Public function for session_runtime.execute_trade. |
| `SimulatorSession.place_pending_order(request: dict[str, Any])` | Public function for session_runtime.place_pending_order. |
| `SimulatorSession.get_market_snapshots()` | Public function for session_runtime.get_market_snapshots. |
| `SimulatorSession.risk_limits_enforced() -> bool` | Public function for session_runtime.risk_limits_enforced. |
| `SimulatorSession.evaluate_pre_trade_governance(*, symbol: str, signed_volume: float)` | Public function for session_runtime.evaluate_pre_trade_governance. |
| `SimulatorSession.project_state_for_signed_volume(*, symbol: str, signed_volume: float) -> PortfolioState` | Public function for session_runtime.project_state_for_signed_volume. |
| `SimulatorSession.build_manual_trade_review(*, symbol: str, signed_volume: float) -> dict` | Public function for session_runtime.build_manual_trade_review. |
| `SimulatorSession.evaluate_current_governance()` | Public function for session_runtime.evaluate_current_governance. |
| `SimulatorSession.build_risk_state() -> PortfolioState` | Public function for session_runtime.build_risk_state. |
| `SimulatorSession.refresh_risk_state() -> PortfolioState \| None` | Public function for session_runtime.refresh_risk_state. |
| `SimulatorSession.get_risk_summary() -> dict[str, Any]` | Public function for session_runtime.get_risk_summary. |
| `SimulatorSession.get_governance_report() -> dict[str, Any] \| None` | Public function for session_runtime.get_governance_report. |
| `SimulatorSession.get_risk_score_summary() -> dict[str, Any]` | Public function for session_runtime.get_risk_score_summary. |
| `SimulatorSession.get_recommendation_summary() -> dict[str, Any]` | Public function for session_runtime.get_recommendation_summary. |
| `SimulatorSession.ensure_risk_run() -> int` | Public function for session_runtime.ensure_risk_run. |
| `SimulatorSession.persist_current_risk_bundle(*, backtest_id: int \| None = None) -> int \| None` | Public function for session_runtime.persist_current_risk_bundle. |
| `SimulatorSession.persist_what_if_comparison(comparison: Any) -> dict[str, int \| None]` | Public function for session_runtime.persist_what_if_comparison. |
| `SimulatorSession.build_current_replay_frame() -> ReplayFrame` | Public function for session_runtime.build_current_replay_frame. |
| `SimulatorSession.evaluate_what_if(*, actions: list[HypotheticalOrderAction], leverage_override: int \| None = None)` | Public function for session_runtime.evaluate_what_if. |
| `SimulatorSession.pause() -> None` | Public function for session_runtime.pause. |
| `SimulatorSession.resume() -> None` | Public function for session_runtime.resume. |
| `SimulatorSession.finalize_for_saved_backtest(user_id: int) -> int` | Public function for session_runtime.finalize_for_saved_backtest. |
| `SimulatorSession.save_state() -> None` | Public function for session_runtime.save_state. |
| `SimulatorSession.visible_total_steps() -> int` | Public function for session_runtime.visible_total_steps. |
| `SimulatorSession.visible_current_step() -> int` | Public function for session_runtime.visible_current_step. |
| `SimulatorSession.resolve_base_bar_index(target_time: str \| None, fallback_index: int \| None) -> int` | Public function for session_runtime.resolve_base_bar_index. |
| `SimulatorSession.seek_to_trade(trade_index: int) -> None` | Public function for session_runtime.seek_to_trade. |
| `SimulatorSession.seek_to_bar(index: int) -> None` | Public function for session_runtime.seek_to_bar. |
| `SimulatorSession.stop() -> None` | Public function for session_runtime.stop. |


## FEAT-API-40: Session lifecycle helpers for simulator routes (app.services.api.session.session_service)

| Function | Purpose |
|----------|---------|
| `load_strategy_class(db_manager: DatabaseManager, user_id: int, strategy_id: int, version_id: int)` | Public function for session_service.load_strategy_class. |
| `resolve_strategy_version_id(db_manager: DatabaseManager, strategy_id: int) -> int` | Public function for session_service.resolve_strategy_version_id. |
| `resume_or_restore_session(*, db_manager: DatabaseManager, coordinator: SessionCoordinator[SimulatorSession], session_id: int, session_data: dict[str, Any], user_id: int) -> dict[str, Any]` | Public function for session_service.resume_or_restore_session. |
| `delete_session_runtime(*, db_manager: DatabaseManager, coordinator: SessionCoordinator[SimulatorSession], session_id: int) -> dict[str, Any]` | Public function for session_service.delete_session_runtime. |
| `stop_and_save_session_runtime(*, db_manager: DatabaseManager, coordinator: SessionCoordinator[SimulatorSession], session_id: int, user_id: int) -> dict[str, Any]` | Public function for session_service.stop_and_save_session_runtime. |


## FEAT-API-41: Trade and order mutation helpers for simulator routes (app.services.api.session.trade_service)

| Function | Purpose |
|----------|---------|
| `execute_trade(active: SimulatorSession, request_payload: dict[str, Any]) -> dict[str, Any]` | Public function for trade_service.execute_trade. |
| `preview_trade(active: SimulatorSession, request_payload: dict[str, Any]) -> dict[str, Any]` | Public function for trade_service.preview_trade. |
| `place_pending_order(active: SimulatorSession, request_payload: dict[str, Any]) -> dict[str, Any]` | Public function for trade_service.place_pending_order. |
| `evaluate_what_if(active: SimulatorSession, actions_payload: list[Any], leverage_override: int \| None, *, refresh_session_risk_state: Callable[[SimulatorSession], None]) -> dict[str, Any]` | Public function for trade_service.evaluate_what_if. |
| `modify_position(active: SimulatorSession, *, session_id: int, position_id: int, sl: float \| None, tp: float \| None) -> dict[str, Any]` | Public function for trade_service.modify_position. |
| `close_position(active: SimulatorSession, *, session_id: int, position_id: int) -> dict[str, Any]` | Public function for trade_service.close_position. |
| `partial_close_position(active: SimulatorSession, *, session_id: int, position_id: int, volume: float) -> dict[str, Any]` | Public function for trade_service.partial_close_position. |
| `modify_order(active: SimulatorSession, *, session_id: int, order_id: int, request_payload: dict[str, Any]) -> dict[str, Any]` | Public function for trade_service.modify_order. |
| `delete_order(active: SimulatorSession, *, session_id: int, order_id: int) -> dict[str, Any]` | Public function for trade_service.delete_order. |


## FEAT-API-42: WebSocket Manager for Real-time Updates (app.services.api.websocket)

| Function | Purpose |
|----------|---------|
| `BacktestLogManager.__init__() -> None` | Initialize the log manager with empty connections. |
| `BacktestLogManager.connect(backtest_id: int, websocket: WebSocket) -> None` | Add a WebSocket connection for a backtest and send buffered logs. |
| `BacktestLogManager.disconnect(backtest_id: int, websocket: WebSocket) -> None` | Remove a WebSocket connection for a backtest. |
| `BacktestLogManager.broadcast(backtest_id: int, message: dict) -> None` | Broadcast a message to all connected clients and buffer it for future connections. |
| `BacktestLogManager.has_connections(backtest_id: int) -> bool` | Check if there are any active connections for a backtest. |
| `BacktestLogManager.clear_buffer(backtest_id: int) -> None` | Clear the log buffer for a completed backtest. |
| `LiveTradingManager.__init__() -> None` | Initialize the live trading manager with empty connections. |
| `LiveTradingManager.connect(session_id: int, websocket: WebSocket) -> None` | Add a WebSocket connection for a live trading session. |
| `LiveTradingManager.disconnect(session_id: int, websocket: WebSocket) -> None` | Remove a WebSocket connection for a trading session. |
| `LiveTradingManager.subscribe(session_id: int, websocket: WebSocket, channels: list[str]) -> None` | Subscribe a WebSocket to specific channels. |
| `LiveTradingManager.broadcast(session_id: int, channel: str, message: dict, include_type: bool = True) -> None` | Broadcast a message to all subscribed clients on a specific channel. |
| `LiveTradingManager.has_connections(session_id: int, channel: str \| None = None) -> bool` | Check if there are any active connections for a session. |
| `LiveTradingManager.send_signal_detected(session_id: int, signal: dict) -> None` | Send signal_detected event to subscribed clients. |
| `LiveTradingManager.send_signal_approved(session_id: int, signal: dict) -> None` | Send signal_approved event to subscribed clients. |
| `LiveTradingManager.send_signal_rejected(session_id: int, signal: dict, reason: str) -> None` | Send signal_rejected event to subscribed clients. |
| `LiveTradingManager.send_position_opened(session_id: int, position: dict) -> None` | Send position_opened event to subscribed clients. |
| `LiveTradingManager.send_position_updated(session_id: int, position: dict) -> None` | Send position_updated event to subscribed clients. |
| `LiveTradingManager.send_position_closed(session_id: int, position: dict, reason: str) -> None` | Send position_closed event to subscribed clients. |
| `LiveTradingManager.send_status_update(session_id: int, status: dict) -> None` | Send status_update event to subscribed clients. |
| `LiveTradingManager.send_log_message(session_id: int, level: str, category: str, message: str, details: dict[str, Any] \| None = None) -> None` | Send log_message event to subscribed clients. |
| `OptimizationProgressManager.__init__() -> None` | Initialize the optimization progress manager with empty connections. |
| `OptimizationProgressManager.connect(optimization_id: int, websocket: WebSocket) -> None` | Add a WebSocket connection for an optimization run and send latest progress. |
| `OptimizationProgressManager.disconnect(optimization_id: int, websocket: WebSocket) -> None` | Remove a WebSocket connection for an optimization run. |
| `OptimizationProgressManager.broadcast_progress(optimization_id: int, progress: dict) -> None` | Broadcast progress update to all connected clients. |
| `OptimizationProgressManager.has_connections(optimization_id: int) -> bool` | Check if there are any active connections for an optimization run. |
| `OptimizationProgressManager.clear_progress(optimization_id: int) -> None` | Clear the progress data for a completed optimization. |

