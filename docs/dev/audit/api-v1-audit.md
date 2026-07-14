# API — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `api`
* **Repository:** `haruperi/HaruQuant`
* **Audited branch:** `main`
* **Audited commit:** `a39d26498e14772c571d75fa9a5f0e477a1dd912` — `refactor: remove unused and deprecated helper modules`
* **Requested package path:** `app/services/api`
* **Actual package path:** `app/api`
* **Boundary correction:** `app/services/api` does not exist at the audited commit. Repository architecture, imports, README entry-point guidance, and the current code place the API layer under `app/api`. The audit therefore treats `app/api` as the actual Version 1 domain and records the supplied path as a boundary mismatch.
* **Tests path searched:** `tests/**`, especially searches for `app.api`, `api.main`, `api.app`, `TestClient`, `ASGITransport`, route symbols, and WebSocket manager symbols.
* **Direct API tests found:** None confirmed.
* **Files inspected:** All 48 Python files discovered under the current `app/api` package boundary, plus `README.md`, `docs/ARCHITECTURE.md`, `pyproject.toml`, database/repository callers, service-layer imports, and package registration call sites.
* **Related packages searched:**
  * `app/services/analytics`
  * `app/services/brokers`
  * `app/services/conversation`
  * `app/services/execution`
  * `app/services/optimization`
  * `app/services/research`
  * `app/services/risk`
  * `app/services/simulation`
  * `app/services/strategy`
  * `app/services/trading`
  * `app/services/utils`
  * `agentic`
  * `data/database`
  * `data/strategies`
  * `app/web`
  * `tests`
* **Registration mechanisms checked:** FastAPI router inclusion, module-level `app` objects, middleware registration, lifespan startup/shutdown hooks, optional dynamic imports, BackgroundTasks, APScheduler jobs, WebSocket managers, dependency injection, module-level singletons, database-backed session leases, and compatibility re-exports.
* **Audit limitations:**
  * A local checkout could not be obtained because outbound Git access was unavailable in the execution environment. Code was inspected through the connected GitHub repository interface.
  * Tests, imports, startup, database migrations, MT5 calls, WebSockets, and FastAPI routes were not executed.
  * Uncommitted, ignored, generated, deployment-only, or machine-local files are not visible.
  * Deployment commands and process-manager configuration were not available, so direct production use of `app.api.app:app` could not be confirmed.
  * Large route/runtime files contain many public class methods. The public-behaviour tables enumerate externally relevant methods individually and group low-level supporting methods where they are only consumed inside the same workflow.
  * No evidence was available for frontend request telemetry, deployed endpoint traffic, or actual environment-variable values.

## 2. Executive Summary

The Version 1 API domain is a **large, active FastAPI integration layer** located at `app/api`, not the requested `app/services/api` path. It exposes user authentication, settings, strategy catalogue management, data preparation, backtesting, interactive simulation, risk analysis, optimization, Edge Lab research, AI chat, live trading, dashboards, documentation-file operations, WebSockets, and a separate operator-control-plane API.

The strongest confirmed workflows are:

1. general API startup and optional router composition through `app/api/main.py`;
2. database-backed registration/login/logout and settings management;
3. backtest and simulator-session orchestration into simulation, trading, analytics, risk, strategy, broker, and persistence services;
4. optimization and Monte Carlo execution through background tasks and WebSocket progress;
5. AI-chat thread/message lifecycle through the conversation service and AI-chat repository;
6. operator approval creation/voting through governance persistence;
7. dashboard and market-data reads.

The domain is not a thin transport layer. Several files contain substantial orchestration, provider adaptation, serialization, state management, persistence, business validation, and workflow logic. The largest examples are `routes/backtest.py`, `routes/live.py`, `routes/risk.py`, `routes/edge.py`, `routes/optimization.py`, `session/session_runtime.py`, and `session/route_support.py`.

The most important structural problems are:

* the documented/requested path does not match the actual package boundary;
* there are two independent FastAPI composition roots (`main.py` and `app.py`);
* `main.py` catches broad import/startup failures, silently disables routes, and still exposes a constant “healthy” response;
* `main.py` attempts to import missing `app.api.routes.operator_strategies`;
* user authentication and operator authentication are separate and materially inconsistent;
* operator authentication validates only header presence and caller-supplied role/actor headers, not a token authority;
* the operator event stream is public and emits hard-coded demonstration events;
* `routes/import_trades.py` is not registered by either composition root;
* the root `ai_chat.py` compatibility wrapper is bypassed by current route registration;
* API code is excluded from the configured coverage source and explicit mypy package list;
* route files frequently instantiate global database/broker/session objects at import time;
* multiple endpoints catch authentication failures and fall back to user ID `1`;
* several files expose write operations without a consistently evidenced authorization boundary;
* route-local helper/service classes duplicate responsibilities owned by lower service layers.

Evidence confidence is **high** for package structure, static call paths, route registration, direct imports, and the structural findings above. Confidence is **medium** for actual production usage because deployment configuration, runtime traffic, and test execution were unavailable.

```text
Module folders: 4 | Files: 48 | Public symbols: 339 | Symbols with confirmed callers: 286 (84.4%) | Workflows found: 15
```

Counting note: public-symbol metrics include public module constants, Pydantic/dataclass models, classes, externally callable class methods, route handlers, public helpers, singleton managers, routers, and application objects. Private underscore helpers are excluded except where a public file directly imports them as compatibility behavior.

## 3. Actual Package Structure

```text
app/
└── api/
    ├── __init__.py
    │   └── __all__ = []
    ├── ai_chat.py
    │   └── router (compatibility re-export)
    ├── app.py
    │   ├── get_operator_api_dependencies()
    │   ├── create_app()
    │   └── app
    ├── approvals.py
    │   ├── LiveExecutionApprovalCreateBody
    │   ├── ApprovalVoteBody
    │   ├── OverrideApprovalCreateBody
    │   ├── KillSwitchRecoveryApprovalBody
    │   ├── create_live_execution_approval()
    │   ├── create_policy_change_approval()
    │   ├── create_override_approval()
    │   ├── create_kill_switch_recovery_approval()
    │   └── vote_live_execution_approval()
    ├── auth.py
    │   ├── ALLOWED_OPERATOR_ROLES
    │   ├── PUBLIC_PATH_PREFIXES
    │   ├── OperatorPrincipal
    │   ├── OperatorAuthMiddleware
    │   ├── get_operator_principal()
    │   └── require_operator_role()
    ├── auth_utils.py
    │   ├── generate_token()
    │   ├── verify_token()
    │   ├── invalidate_token()
    │   ├── authenticate_user()
    │   └── get_user_id_from_token()
    ├── dependencies.py
    │   ├── OperatorApiDependencies
    │   ├── resolve_sqlite_database_path()
    │   └── build_operator_api_dependencies()
    ├── events.py
    │   └── stream_operator_events()
    ├── health.py
    │   ├── check_app_health()
    │   ├── check_database_health()
    │   ├── check_redis_health()
    │   └── check_schema_registry_health()
    ├── main.py
    │   ├── lifespan()
    │   ├── IntentClassificationMiddleware
    │   ├── app
    │   └── health_check()
    ├── models.py
    │   ├── RegisterRequest
    │   ├── LoginRequest
    │   ├── UserResponse
    │   ├── AuthResponse
    │   ├── ErrorResponse
    │   ├── UserSettingsResponse
    │   ├── UpdateUserSettingsRequest
    │   ├── BrokerStatusResponse
    │   ├── DashboardEquityPoint
    │   ├── DashboardEquityCurveResponse
    │   ├── DashboardDailyPnlPoint
    │   ├── DashboardActiveStrategyItem
    │   ├── DashboardSummaryResponse
    │   ├── MarketStatus
    │   ├── MarketHoursResponse
    │   ├── SystemStatusResponse
    │   └── ResourceUsageResponse
    ├── router.py
    │   ├── Intent
    │   ├── RoutingMetadata
    │   ├── IntentClassifier
    │   └── intent_classifier
    ├── scheduler.py
    │   ├── start_scheduler()
    │   └── shutdown_scheduler()
    ├── websocket.py
    │   ├── BacktestLogManager
    │   ├── backtest_log_manager
    │   ├── LiveTradingManager
    │   ├── live_trading_manager
    │   ├── OptimizationProgressManager
    │   └── optimization_progress_manager
    ├── middleware/
    │   ├── __init__.py
    │   └── security.py
    │       └── SecretRedactionMiddleware
    ├── routes/
    │   ├── __init__.py
    │   ├── ai_chat.py
    │   │   ├── request models
    │   │   ├── conversation dependencies
    │   │   └── thread/message/context/signal/action routes
    │   ├── auth.py
    │   │   ├── register()
    │   │   ├── login()
    │   │   └── logout()
    │   ├── backtest.py
    │   │   ├── DEFAULT_SIM_CONFIG
    │   │   ├── PortfolioRunResult
    │   │   ├── portfolio_run()
    │   │   ├── request/response models
    │   │   └── backtest CRUD/run/results/WebSocket routes
    │   ├── data.py
    │   │   ├── DatasetPrepareRequest
    │   │   ├── MT5DataSource
    │   │   ├── DukascopyDataSource
    │   │   ├── dataset serialization helpers
    │   │   └── get_symbols()/prepare_dataset_endpoint()
    │   ├── docs.py
    │   │   ├── DOCS_ROOT
    │   │   ├── FileNode
    │   │   ├── SaveFileRequest
    │   │   └── list/read/save/delete documentation routes
    │   ├── edge.py
    │   │   ├── Edge Lab request/response models
    │   │   └── dataset, EDS, seasonality, structure, calibration,
    │   │       snapshot, automation, and result routes
    │   ├── import_trades.py
    │   │   └── trade-import request parsing and persistence routes
    │   ├── live.py
    │   │   ├── MT5Utils
    │   │   ├── live-session request/response models
    │   │   └── session, trade, position, order, signal, log,
    │   │       statistics, candle, and WebSocket routes
    │   ├── optimization.py
    │   │   └── optimization, walk-forward, unsupervised, Monte Carlo,
    │   │       simulation, result, cancellation, and WebSocket routes
    │   ├── risk.py
    │   │   ├── risk request/response models
    │   │   └── position-sizing, regime, allocation, and governance routes
    │   ├── settings.py
    │   │   ├── get_user_id_from_token()
    │   │   ├── get_settings()
    │   │   ├── get_settings_no_slash()
    │   │   └── update_settings()
    │   ├── simulator.py
    │   │   ├── active_sessions
    │   │   ├── session_coordinator
    │   │   ├── cleanup_stale_simulation_leases()
    │   │   └── simulator lifecycle/state/trade/order/position routes
    │   ├── sqx.py
    │   │   └── StrategyQuant X import/parse/list/read routes
    │   ├── strategies.py
    │   │   ├── StrategyCatalogCreateRequest
    │   │   ├── StrategyCatalogUpdateRequest
    │   │   ├── StrategyCatalogService
    │   │   └── strategy/version/import/export routes
    │   └── dashboard/
    │       ├── __init__.py
    │       ├── broker.py
    │       │   └── broker connection/status/account/equity routes
    │       ├── currency_strength.py
    │       │   └── currency-strength calculation routes
    │       ├── forex_calendar.py
    │       │   └── economic-calendar routes
    │       ├── market_hours.py
    │       │   └── market-session status routes
    │       └── system.py
    │           └── system/database/resource status routes
    └── session/
        ├── __init__.py
        ├── models.py
        │   ├── SimulationStartRequest
        │   ├── SimulationUpdateRequest
        │   ├── ManualTradeRequest
        │   ├── PendingOrderRequest
        │   ├── PositionModifyRequest
        │   ├── OrderModifyRequest
        │   ├── SeekRequest
        │   ├── AdvanceRequest
        │   ├── WhatIfActionRequest
        │   ├── WhatIfRequest
        │   └── SeekTradeRequest
        ├── route_guards.py
        │   ├── get_owned_session_record()
        │   └── get_running_session()
        ├── route_support.py
        │   ├── normalize_position()
        │   ├── normalize_order()
        │   ├── position_info_to_dict()
        │   ├── order_info_to_dict()
        │   ├── collect_positions_orders()
        │   ├── refresh_session_risk_state()
        │   ├── monitor_refresh_collect()
        │   └── build_session_state_response()
        ├── serializers.py
        │   └── private serialization helpers consumed across session files
        ├── session_backend.py
        │   ├── SessionMetadata
        │   ├── SessionRuntimeStore
        │   └── SQLiteSessionRuntimeStore
        ├── session_coordinator.py
        │   └── SessionCoordinator
        ├── session_manager.py
        │   └── SimulatorSessionManager
        ├── session_runtime.py
        │   └── SimulatorSession
        ├── session_service.py
        │   ├── load_strategy_class()
        │   ├── resolve_strategy_version_id()
        │   ├── resume_or_restore_session()
        │   ├── delete_session_runtime()
        │   └── stop_and_save_session_runtime()
        └── trade_service.py
            ├── execute_trade()
            ├── preview_trade()
            ├── place_pending_order()
            ├── evaluate_what_if()
            ├── modify_position()
            ├── close_position()
            ├── partial_close_position()
            ├── modify_order()
            └── delete_order()
```

### Referenced but absent module

```text
app/api/routes/operator_strategies.py    [NOT PRESENT]
```

`app/api/main.py` attempts to import this module through its broad optional-import mechanism. The missing module is logged and its router is omitted.

## 4. Module and File Inventory

Files are ordered approximately from composition and contracts through supporting runtime code and route adapters.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `app.api` | `__init__.py` | Marks canonical API package; exports nothing | `__all__=[]` | Standard library only | Used as package marker | Supporting |
| `app.api` | `models.py` | Shared user/settings/dashboard response contracts | 17 Pydantic models | Pydantic | Used by auth/settings/dashboard routes | Supporting |
| `app.api` | `router.py` | Path-prefix intent classification and metadata | `Intent`, `RoutingMetadata`, `IntentClassifier`, singleton | enum, typing; utils logger | Used by `main.py` middleware | Useful |
| `app.api.middleware` | `__init__.py` | Package marker | None | None | Used as package marker | Supporting |
| `app.api.middleware` | `security.py` | Redacts headers/query values before request logging | `SecretRedactionMiddleware` | FastAPI/Starlette; utils redaction/logger | Used by `main.py` | Useful |
| `app.api` | `auth_utils.py` | Database-backed user sessions and credential authentication | five auth helpers | datetime; FastAPI; DB manager; password verifier | Used by auth/settings/data/simulator/risk/live routes | Essential |
| `app.api` | `auth.py` | Operator-header principal extraction and role gate | constants, `OperatorPrincipal`, middleware, guard functions | FastAPI/Starlette | Used by operator app/approval routes | Essential to operator workflow; security quality questionable |
| `app.api` | `dependencies.py` | Creates operator settings/schema/policy/repository container | dependency dataclass and builders | pathlib; database migrations/repo; agentic registry; risk policy; settings | Used by operator `app.py` | Essential |
| `app.api` | `health.py` | Operator component probes | four health functions | sqlite/pathlib; operator dependencies | Used by operator `app.py` | Useful |
| `app.api` | `approvals.py` | Operator approval and vote HTTP surface | four bodies, five route handlers | FastAPI/Pydantic; execution approval services; operator auth | Used by operator app | Essential |
| `app.api` | `events.py` | Operator SSE endpoint | `stream_operator_events` | json; FastAPI/Starlette | Used by operator app | Questionable: static demonstration feed |
| `app.api` | `app.py` | Separate operator-control-plane FastAPI composition root | `create_app`, dependency accessor, `app` | FastAPI/CORS; operator modules | Possibly used by direct deployment; no repository caller confirmed | Useful but duplicated composition |
| `app.api` | `scheduler.py` | Starts cleanup and disabled Edge Lab refresh jobs | `start_scheduler`, `shutdown_scheduler` | APScheduler; DB manager; logger | Used by general app lifespan | Supporting |
| `app.api` | `websocket.py` | In-memory WebSocket connection, subscription, and buffering managers | three manager classes and singletons | asyncio, deque; FastAPI WebSocket | Used by backtest/live/optimization routes | Essential |
| `app.api` | `ai_chat.py` | Compatibility re-export for AI-chat router | `router` | `app.api.routes.ai_chat` | No current caller found; `main.py` imports route module directly | No demonstrated value |
| `app.api` | `main.py` | General API composition, middleware, lifespan, and route registration | `app`, lifespan, middleware, health route | importlib; FastAPI/CORS; all optional routes; DB/scheduler at lifespan | Canonical runtime entry point | Essential |
| `app.api.routes` | `__init__.py` | Route-package marker | None | None | Used as package marker | Supporting |
| `app.api.routes` | `auth.py` | Register/login/logout endpoints | three route handlers, router | DB manager; auth helpers/models; logger | Registered under `/api/auth` | Essential |
| `app.api.routes` | `settings.py` | Authenticated read/update of user settings | local token helper; three handlers | DB manager; auth verify; models | Registered under `/api/settings` | Useful |
| `app.api.routes` | `data.py` | Broker-backed symbol lookup and reusable research dataset preparation | request model, data-source wrappers, serialization/range helpers, two handlers | hashlib/json/datetime; numpy/pandas; DB; broker/research/utils | Registered under `/api/data` | Essential for research/data workflows |
| `app.api.routes` | `strategies.py` | Strategy catalogue, versioned artifacts, governance projection, import/export | two request dataclasses, `StrategyCatalogService`, route handlers | json/tempfile/pathlib; DB/governance; strategy storage; FastAPI | Registered under `/api/strategies` | Essential |
| `app.api.routes` | `backtest.py` | Backtest orchestration, persistence, result adaptation, analytics, logs/WebSocket | config, result adapter, models, `portfolio_run`, handlers | asyncio/pandas; DB; strategy storage; simulation; analytics; permissions; WebSockets | Registered under `/api/backtest` | Essential |
| `app.api.routes` | `simulator.py` | Interactive session lifecycle and transport delegation | lease cleanup, coordinator globals, 20 route handlers | DB; FastAPI DI; session package; execution trading | Registered under `/api/simulator` | Essential |
| `app.api.routes` | `risk.py` | Standalone sizing, regime, allocation, and governance analysis | request/response models and route handlers | numpy/pandas; risk engines/models; simulation/broker; auth | Registered under `/api/risk` | Useful/Essential depending workflow |
| `app.api.routes` | `optimization.py` | Parameter optimization, walk-forward, unsupervised analysis, Monte Carlo, progress WebSocket | route handlers | DB; background tasks; optimization/research/brokers; WebSocket manager | Registered under `/api/optimization` | Essential |
| `app.api.routes` | `edge.py` | Broad Edge Lab dataset/research/calibration/snapshot/automation API | many Pydantic models and handlers | numpy/pandas; DB; broker; research; auth | Registered under `/api/edge-lab` | Essential for research workflows |
| `app.api.routes` | `ai_chat.py` | Conversation threads, messages, context, tools, signal/action drafts, retention | payload models, dependencies, route handlers | DB migrations/repository; conversation services/schemas; optional agentic tools | Registered under `/api/ai-chat` | Essential |
| `app.api.routes` | `live.py` | Live session control, MT5 market/trade operations, monitoring and WebSockets | `MT5Utils`, request models, route handlers, active-session map | pandas; DB; MT5; execution live; permissions; WebSockets | Registered under `/api/live` | Essential but heavily coupled |
| `app.api.routes` | `sqx.py` | StrategyQuant X import and inspection | import/parse/list/read handlers | FastAPI; DB/storage/parser utilities | Registered under `/api/sqx` | Useful |
| `app.api.routes` | `docs.py` | Lists, reads, writes, and deletes Markdown files under `docs/` | `DOCS_ROOT`, models, path helpers, four handlers | os/pathlib; FastAPI/Pydantic | Registered under `/api/docs` | Useful; high-impact write surface |
| `app.api.routes` | `import_trades.py` | Imports trade files/records into persistence | route handlers/models | FastAPI; DB/import parsing | No router inclusion found | Unused |
| `app.api.routes.dashboard` | `__init__.py` | Dashboard package marker | None | None | Used as package marker | Supporting |
| `app.api.routes.dashboard` | `broker.py` | Shared MT5 client and broker/account/equity status API | client and handlers | DB; MT5 broker; models/auth | Registered under `/api/dashboard` | Essential for live/dashboard reads |
| `app.api.routes.dashboard` | `currency_strength.py` | Currency-strength calculation and payloads | handlers/helpers | market data/broker; pandas/numeric logic | Registered under `/api/dashboard` | Useful |
| `app.api.routes.dashboard` | `forex_calendar.py` | Economic-calendar read surface | handlers/helpers | external/data calendar provider and FastAPI | Registered under `/api/dashboard` | Useful; operational status unverified |
| `app.api.routes.dashboard` | `market_hours.py` | Current market-session status | handlers/helpers | datetime/timezone; models | Registered under `/api/dashboard` | Useful |
| `app.api.routes.dashboard` | `system.py` | Backend/database/resource status | handlers/helpers | DB/system resource libraries; models | Registered under `/api/dashboard` | Useful |
| `app.api.session` | `__init__.py` | Simulator session package marker | None | None | Imported as package | Supporting |
| `app.api.session` | `models.py` | Simulator-session request contracts | 11 Pydantic models | Pydantic | Used by simulator routes | Essential |
| `app.api.session` | `session_manager.py` | Locked in-process runtime map | `SimulatorSessionManager` | threading/typing | Used by simulator route composition | Supporting |
| `app.api.session` | `session_backend.py` | Persistent metadata and SQLite lease abstraction | metadata dataclass, protocol, SQLite store | sqlite3/datetime | Used by coordinator | Essential |
| `app.api.session` | `session_coordinator.py` | Coordinates persistent ownership leases and in-memory runtimes | `SessionCoordinator` | os/datetime; FastAPI exceptions; backend/manager | Used by simulator routes/services | Essential |
| `app.api.session` | `route_guards.py` | Ownership and running-runtime guards | two functions | coordinator/runtime | Used by simulator DI | Essential |
| `app.api.session` | `serializers.py` | Risk/governance/recommendation/what-if serialization | private helpers only | math/dataclasses; risk models/engine | Used internally by runtime/trade service | Supporting |
| `app.api.session` | `route_support.py` | Position/order normalization, replay state, risk refresh, session response assembly | eight public helpers | datetime; MT5 constants; runtime | Used by simulator routes/services | Essential |
| `app.api.session` | `session_runtime.py` | Large stateful simulation runtime integrating engine, risk, strategy, replay, persistence | `SimulatorSession` | pandas; DB; MT5; execution; risk; simulation; serializers | Used by simulator routes/services | Essential |
| `app.api.session` | `session_service.py` | Strategy loading and session resume/delete/save lifecycle | five functions | DB/storage; permissions; coordinator/runtime/support | Used by simulator routes | Essential |
| `app.api.session` | `trade_service.py` | Governance-aware simulator trade/order mutations and what-if evaluation | nine functions | FastAPI; risk simulation; route support; runtime | Used indirectly through `app.services.execution.trading` and simulator routes | Essential |

## 5. Public Behaviour Inventory

### `app/api/__init__.py`

**File responsibility:** Package marker. It intentionally exposes no public registry.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `__all__` | Constant | Empty package export list | — | None | None | Python import system | None found | Used | Supporting |

### `app/api/main.py`

**File responsibility:** General application composition root.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `lifespan(app)` | Async context manager | Initialize DB/migrations, clear leases, start/stop scheduler | FastAPI app → lifecycle iterator | Persistence write; local state mutation | Startup errors are caught/logged | `FastAPI(lifespan=...)` | None found | Used | Essential |
| `IntentClassificationMiddleware.dispatch()` | Method | Attach path-derived routing metadata to request state | Request/call-next → response | Local state mutation | Downstream exceptions | FastAPI middleware chain | None found | Used | Supporting |
| `app` | FastAPI application | General REST/WebSocket application | ASGI calls → responses | Multiple | Import/dependency failures are partly suppressed | README/runtime entry point | None found | Used | Essential |
| `health_check()` | Route handler | Return constant API heartbeat | None → dict | None | None | `GET /api/health` | None found | Used | Useful, but not a dependency-health check |

**Confirmed concern:** optional route imports catch any `Exception`; missing or broken routes are omitted rather than failing application construction. `app.api.routes.operator_strategies` is currently missing.

### `app/api/app.py`

**File responsibility:** Separate operator API composition root.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `get_operator_api_dependencies()` | Dependency | Read operator dependency container from app state | Request → container | Read-only | Attribute error if unwired | Operator routes | None found | Used inside app | Supporting |
| `create_app()` | Function | Construct operator FastAPI app and routes | optional dependencies → FastAPI | DB migrations/path creation through default dependency build | Dependency errors | module-level `app` | None found | Used internally; direct deployment unverified | Useful |
| `app` | FastAPI application | Operator control-plane ASGI app | ASGI calls → responses | Persistence through routes | Dependency/startup errors | No repository deployment caller found | None found | Possibly used | Useful |

### `app/api/auth.py`

**File responsibility:** Minimal operator principal and role checks.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `ALLOWED_OPERATOR_ROLES` | Constant | Allowed role-header values | — | None | None | `_extract_principal` | None | Used | Supporting |
| `PUBLIC_PATH_PREFIXES` | Constant | Bypass paths for operator middleware | — | None | None | `_is_public_path` | None | Used | Supporting |
| `OperatorPrincipal` | Dataclass | Store bearer string, actor ID, role | values → immutable object | None | Validation is not enforced by dataclass | middleware/guards | None | Used | Supporting |
| `OperatorAuthMiddleware.dispatch()` | Method | Attach operator principal to protected routes | Request → response | Local state mutation | Converts auth exceptions to JSON | operator app | None | Used | Essential |
| `get_operator_principal()` | Function | Read principal from request state | Request → principal | Read-only | HTTP 401 | approval guards | None | Used | Essential |
| `require_operator_role()` | Function | Require role membership | Request/roles → principal | Read-only | HTTP 401/403 | approval handlers | None | Used | Essential |

**Security evidence:** bearer content is only required to be non-empty; role and actor identity come directly from `X-HQ-Role` and `X-HQ-Actor-Id` headers. No repository/token-authority validation is performed here.

### `app/api/auth_utils.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `generate_token()` | Function | Replace existing sessions and create 24-hour session | user ID/DB → token | Persistence write | DB exceptions | login route | None found | Used | Essential |
| `verify_token()` | Function | Resolve session, parse expiry, delete expired session | token/DB → user ID or `None` | Read-only; conditional persistence write | DB errors may propagate | settings/data/simulator/risk/live | None found | Used | Essential |
| `invalidate_token()` | Function | Delete session token | token/DB → `None` | Persistence write | DB errors | logout | None found | Used | Essential |
| `authenticate_user()` | Function | Verify credentials/account state and update login time | credentials/DB → status dict | Read-only; persistence write on success | DB/hash errors | login | None found | Used | Essential |
| `get_user_id_from_token()` | FastAPI dependency | Parse authorization header and validate DB session | header → user ID | DB read; possible expired-session deletion | HTTP 401 | multiple routes | None found | Used | Essential |

### `app/api/dependencies.py`, `health.py`, `approvals.py`, `events.py`

| File / symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------- | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `OperatorApiDependencies` | Dataclass | Operator dependency container | settings/registry/policy/repo | None | None | operator app/routes | None | Used | Supporting |
| `resolve_sqlite_database_path()` | Function | Enforce/parse SQLite URL | URL → `Path` | None | `ValueError` | dependency builder | None | Used | Supporting |
| `build_operator_api_dependencies()` | Function | Build settings, migrations, schema registry, policy resolver, repo | optional settings → container | Local directory mutation; persistence migrations | settings/DB errors | `create_app` | None | Used | Essential |
| `check_app_health()` | Function | Basic operator heartbeat | dependencies → dict | None | Attribute errors | operator health route | None | Used | Useful |
| `check_database_health()` | Function | SQLite `SELECT 1` probe | dependencies → dict | Local directory creation; DB read | sqlite errors | operator health route | None | Used | Useful |
| `check_redis_health()` | Function | Report disabled/unknown Redis state | dependencies → dict | None | None | operator health route | None | Used | Questionable: no Redis probe |
| `check_schema_registry_health()` | Function | Count seeded contracts | dependencies → dict | Read-only | Depends on private `_records` | operator health route | None | Used | Useful |
| Four approval body models | Pydantic models | Validate live/policy/override/recovery approval requests | JSON → model | None | Pydantic errors | approval handlers | None | Used | Supporting |
| Five approval route handlers | HTTP handlers | Create approvals and votes | body/request/path → dict | Persistence write | HTTP and service errors | operator router | None | Used | Essential |
| `stream_operator_events()` | HTTP/SSE handler | Stream three predefined messages | None → `StreamingResponse` | Network response | None | operator router | None | Used | Questionable |

### `app/api/router.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `Intent` | Enum | Standard path intent categories | — | None | None | classifier/middleware | None | Used | Useful |
| `RoutingMetadata` / `to_dict()` | Class/method | Hold normalized request routing metadata | intent/priority/session/user → dict | None | None | classifier/middleware | None | Used | Supporting |
| `IntentClassifier.classify()` | Method | Prefix-match request path | path → intent | Warning log for unknown path | None | middleware | None | Used | Useful |
| `classify_and_metadata()` | Method | Create routing metadata | path/options → object | Warning log on unknown | None | middleware | None | Used | Useful |
| `add_route()` | Method | Mutate runtime route map | prefix/intent → `None` | Local state mutation | None | No external caller found | None | Unused | Questionable |
| `allowed_intents()` | Method | Return mapped intent set | None → list | None | None | No external caller found | None | Unused | Questionable |
| `route_map` | Property | Return copy of prefix map | None → dict | None | None | No external caller found | None | Unused | Questionable |
| `intent_classifier` | Singleton | Shared classifier | — | Mutable local state | None | `main.py` | None | Used | Supporting |

### `app/api/scheduler.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `start_scheduler()` | Function | Register cleanup/refresh cron jobs and start scheduler | None → `None` | Local state mutation; future persistence writes | APScheduler/DB errors | general app lifespan | None | Used | Supporting |
| `shutdown_scheduler()` | Function | Stop scheduler | None → `None` | Local state mutation | scheduler errors | general app lifespan | None | Used | Supporting |

The registered `refresh_edge_lab_universe` job is explicitly disabled and only logs a message.

### `app/api/websocket.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `BacktestLogManager` | Class | Connect/disconnect, buffer, broadcast, inspect and clear backtest logs | IDs/WebSockets/messages | Local state mutation; network send | Send errors are swallowed and connections removed | backtest routes/services | None | Used | Essential |
| `backtest_log_manager` | Singleton | Shared backtest manager | — | Mutable process state | — | backtest route | None | Used | Essential |
| `LiveTradingManager` | Class | Channel subscriptions and live signal/position/status/log events | session/WebSocket/channel/payload | Local state mutation; network send | Send errors handled as disconnects | live routes/runtime callers | None | Used | Essential |
| `live_trading_manager` | Singleton | Shared live manager | — | Mutable process state | — | live route | None | Used | Essential |
| `OptimizationProgressManager` | Class | Cache latest progress and broadcast it | optimization/WebSocket/progress | Local state mutation; network send | Send errors handled | optimization routes/tasks | None | Used | Essential |
| `optimization_progress_manager` | Singleton | Shared optimization manager | — | Mutable process state | — | optimization route/tasks | None | Used | Essential |

All managers are process-local. No cross-process broker/backplane is present in this file.

### `app/api/middleware/security.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `SecretRedactionMiddleware.dispatch()` | Method | Redact request headers/query before debug logging | request/call-next → response | Log publication | Downstream errors | general app middleware | None | Used | Useful |

Request bodies and response bodies are not handled by this middleware.

### `app/api/models.py`

All models are side-effect-free Pydantic transport contracts.

| Symbols | Responsibility | Callers | Usage status | Value status |
| ------- | -------------- | ------- | ------------ | ------------ |
| `RegisterRequest`, `LoginRequest`, `UserResponse`, `AuthResponse`, `ErrorResponse` | Authentication request/response contracts | auth routes | Used except no confirmed caller for `ErrorResponse` | Supporting; `ErrorResponse` Questionable |
| `UserSettingsResponse`, `UpdateUserSettingsRequest` | Settings transport | settings routes | Used | Supporting |
| `BrokerStatusResponse` | Broker dashboard status | dashboard broker | Used | Supporting |
| Equity/daily-PnL/strategy/summary dashboard models | Dashboard payloads | dashboard routes | Used | Supporting |
| `MarketStatus`, `MarketHoursResponse` | Market-session payload | market-hours route | Used | Supporting |
| `SystemStatusResponse`, `ResourceUsageResponse` | System/resource payload | system route | Used | Supporting |

The settings response uses literal `{}` defaults for several mapping/list fields rather than factories. Pydantic may copy these, but the declaration is inconsistent with safer default-factory usage elsewhere.

### `app/api/routes/auth.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `register()` | Route | Create inactive/unverified user | `RegisterRequest` → `UserResponse` | Persistence write; logging | HTTP 400/500 | `/api/auth/register` | None | Used | Essential |
| `login()` | Route | Authenticate verified active user and create session | `LoginRequest` → `AuthResponse` | DB read/write; logging | HTTP 401/403/500 | `/api/auth/login` | None | Used | Essential |
| `logout()` | Route | Delete bearer session if well formed | header → message | Conditional persistence write | DB errors | `/api/auth/logout` | None | Used | Essential |

### `app/api/routes/settings.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `get_user_id_from_token()` | Function | Local duplicate of authorization parsing | header → user ID | DB read/conditional delete | HTTP 401 | settings handlers | None | Used | Supporting but duplicated |
| `get_settings()` / `get_settings_no_slash()` | Routes | Same read operation on slash/no-slash paths | bearer → model | DB read; logging | HTTP 401/404/500 | `/api/settings` | None | Used | Useful; duplicated route surface |
| `update_settings()` | Route | Persist non-null settings fields | request/bearer → model | Persistence write | HTTP 400/401/500 | `/api/settings/` | None | Used | Useful |

### `app/api/routes/data.py`

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | ------ | ------- | ------------ | ------------ |
| `DatasetPrepareRequest` | Dataset preparation contract | JSON → model | None | Validation | endpoint | Used | Supporting |
| `MT5DataSource.fetch_data()` | Credential-backed MT5 bars adapter | symbol/timeframe/range → DataFrame/None | External broker/API call | provider errors mostly become `None` | research preparation | Used | Essential |
| `DukascopyDataSource.fetch_data()` | Dukascopy bars adapter | symbol/timeframe/range → DataFrame/None | External API/file call | provider errors | research preparation | Used | Useful |
| JSON/report/dataset serialization helpers | Convert research objects to API-safe payloads | objects → dict/scalars | None | conversion/HTTP errors | data and Edge Lab flows | Used | Supporting |
| range/source/fingerprint/deserialization helpers | Validate source/range and reconstruct prepared datasets | payloads → normalized objects | None | HTTP 400/502, parse errors | data/Edge Lab/backtest flows | Used | Supporting |
| `get_symbols()` | Route | List MT5 symbols | bearer → list | DB read; broker call | HTTP 400/500/502 | `/api/data/symbols` | Used | Useful |
| `prepare_dataset_endpoint()` | Route | Load, clean, enrich, serialize dataset | request/bearer → dict | DB read; broker call | validation/provider errors | `/api/data/dataset/prepare` | Used | Essential |

Authentication failures in both routes are caught broadly and replaced with `user_id = 1`.

### `app/api/routes/strategies.py`

| Symbol group | Responsibility | Side effects | Callers | Usage status | Value status |
| ------------ | -------------- | ------------ | ------- | ------------ | ------------ |
| `StrategyCatalogCreateRequest`, `StrategyCatalogUpdateRequest` | Route-local service contracts | None | service/route wrappers | Used | Supporting |
| `StrategyCatalogService.create_strategy()` | Create DB row, version file, metadata and governance record | Persistence write; local file write | strategy create route | Used | Essential |
| `list_strategies()`, `get_strategy()` | Catalogue reads with governance projection | Read-only | list/detail routes | Used | Essential |
| `update_strategy()` | Update catalogue and optionally create version/governance state | Persistence/local file writes | update route | Used | Essential |
| `create_strategy_version()`, `rollback_version()` | Version creation and active-version rollback | Persistence/local file writes | version routes/update/import | Used | Essential |
| `delete_strategy()` | Delete DB and stored artifacts | Persistence/local file deletion | delete route | Used | Essential |
| `list_versions()`, `get_version_code()` | Version history and code/metadata read | Read-only/local file read | version routes | Used | Useful |
| `export_strategy()`, `import_strategy()` | Zip export/import | Local file read/write | upload/download routes | Used | Useful |
| Route handlers | Expose CRUD/version/import/export operations | Same as service calls | registered router | Used | Essential |

The route file contains a substantial route-local domain service, persistence coordination, filesystem versioning, governance synchronization, and transport code in one file.

### `app/api/routes/backtest.py`

| Symbol group | Responsibility | Side effects | Callers | Usage status | Value status |
| ------------ | -------------- | ------------ | ------- | ------------ | ------------ |
| `DEFAULT_SIM_CONFIG` | Default nested simulation configuration | None | `portfolio_run` and request mapping | Used | Supporting |
| `PortfolioRunResult` and public methods/properties | Adapt simulation result to trades/equity/analytics/dataframes | Read-only; lazy analytics call | backtest/optimization consumers | Used | Useful |
| `portfolio_run()` | Construct simulation engine, optionally connect credentials, run | Broker connection; simulation mutation | route and optimization service imports | Used | Essential |
| Backtest/portfolio request/response models | Validate transport and serialize records | None | route handlers | Used | Supporting |
| run/start/background helpers | Load strategy/data, enforce strategy permission, create/update run, execute simulation, persist result | Persistence write; broker/API call; local state mutation; WebSocket publication | HTTP run routes/background tasks | Used | Essential |
| list/detail/delete/result/overview routes | Query and mutate persisted backtests | DB read/write | `/api/backtest` | Used | Essential |
| backtest log WebSocket | Stream buffered progress/log messages | Network send; local connection state | WebSocket clients | Used | Useful |

The file exceeds 1,300 lines and mixes transport models, simulation configuration, strategy loading, execution, persistence, analytics adaptation, authorization fallback, CRUD, and WebSocket handling.

### `app/api/session/*` and `routes/simulator.py`

#### Public request models

`SimulationStartRequest`, `SimulationUpdateRequest`, `ManualTradeRequest`, `PendingOrderRequest`, `PositionModifyRequest`, `OrderModifyRequest`, `SeekRequest`, `AdvanceRequest`, `WhatIfActionRequest`, `WhatIfRequest`, and `SeekTradeRequest` validate simulator transport payloads. They are used by the registered simulator router and have no direct side effects.

#### Session storage and ownership

| Symbol | Responsibility | Side effects | Raises | Callers | Usage status | Value status |
| ------ | -------------- | ------------ | ------ | ------- | ------------ | ------------ |
| `SimulatorSessionManager.get/put/remove()` | Locked process-local runtime map | Local state mutation | None | coordinator | Used | Supporting |
| `SessionMetadata.from_record/as_record()` | Normalize persistent record | None | conversion errors | SQLite store/guards | Used | Supporting |
| `SessionRuntimeStore` | Protocol for metadata/lease operations | Contract only | — | coordinator typing | Used | Supporting |
| `SQLiteSessionRuntimeStore` public methods | Read/update metadata and atomically acquire/renew/release/clear leases | Persistence read/write | sqlite errors | coordinator/startup | Used | Essential |
| `SessionCoordinator` public methods | Enforce ownership, attach/get/require/release runtime, renew/check leases, update metadata | Persistence and local state mutation | HTTP 400/404/409 | simulator route/service | Used | Essential |
| `get_owned_session_record()`, `get_running_session()` | DI-friendly ownership/runtime guards | Read-only plus lease renewal | HTTP errors | simulator route dependencies | Used | Essential |

#### Session response and mutation services

| Symbol group | Responsibility | Side effects | Callers | Usage status | Value status |
| ------------ | -------------- | ------------ | ------- | ------------ | ------------ |
| route-support normalization helpers | Normalize MT5-like position/order/replay records | None | simulator state responses | Used | Supporting |
| `collect_positions_orders()` | Read and normalize current runtime records | Read-only | advance/positions/trade responses | Used | Essential |
| `refresh_session_risk_state()` | Rebuild risk state and derived outputs | Local runtime mutation | simulator routes/trade service | Used | Essential |
| `monitor_refresh_collect()` | Monitor account/positions, refresh risk, collect payloads | Local runtime mutation | response assembly | Used | Supporting |
| `build_session_state_response()` | Build positions/orders/risk/governance/recommendation payload | Read-only after refresh | simulator/trade service | Used | Essential |
| `load_strategy_class()`, `resolve_strategy_version_id()` | Permission-check and load persisted strategy class/version | DB/local file read | start/resume | Used | Essential |
| `resume_or_restore_session()` | Resume in-memory runtime or rebuild it from DB | Persistence/local state mutation; broker/data load | resume route | Used | Essential |
| `delete_session_runtime()` | Stop/release and delete session | Persistence/local state mutation | delete route | Used | Essential |
| `stop_and_save_session_runtime()` | Finalize runtime as backtest and persist risk snapshot | Persistence write; local state mutation | stop-and-save route | Used | Essential |
| nine trade-service functions | Governance-aware execute/preview/pending/what-if/position/order mutations | Simulation/broker mutation; local state mutation | execution facade/simulator routes | Used | Essential |

#### `SimulatorSession`

`SimulatorSession` is the central stateful runtime. Its externally used methods include data loading, account-default application, strategy attachment, replay setup, bar/tick processing, frame advancement, seeking, pause/resume/stop, trade and pending-order operations, position/order mutation, risk-state refresh, risk snapshot/score/recommendation/governance access, what-if review, runtime persistence, and final backtest creation. Side effects include local state mutation, database reads/writes, simulated broker mutation, strategy execution, and risk persistence.

#### Simulator routes

Confirmed handlers: `start_simulation`, `list_sessions`, `list_paused_sessions`, `get_session`, `update_session`, `get_bar`, `advance_bars`, `get_positions`, `execute_trade`, `preview_trade`, `place_pending_order`, `evaluate_what_if`, `modify_position`, `close_position`, `partial_close_position`, `modify_order`, `delete_order`, `resume_session`, `seek_session`, `get_session_trades`, `seek_trade`, `delete_session`, and `stop_and_save_session`.

All are registered under `/api/simulator`; protected routes resolve a DB-backed user session and enforce session ownership. `cleanup_stale_simulation_leases()` is called at general API startup when the route module imports successfully.

### `app/api/routes/optimization.py`

| Public handlers | Responsibility | Side effects | Usage status | Value status |
| --------------- | -------------- | ------------ | ------------ | ------------ |
| `start_optimization()` | Create optimization run and queue background task | Persistence write; background execution | Used | Essential |
| `get_optimization_run()`, `get_optimization_results()` | Read persisted run/results | DB read | Used | Essential |
| `cancel_optimization()` | Mark run cancelled | Persistence write | Used | Essential |
| `start_walk_forward()` | Create/queue walk-forward run | Persistence write; background execution | Used | Essential |
| `run_unsupervised_analysis()`, `get_unsupervised_report()` | Execute/read unsupervised research | Broker/data read; computation; DB read | Used | Useful |
| `start_monte_carlo()`, `get_monte_carlo()` | Queue and read stored Monte Carlo simulation | Persistence/background execution | Used | Essential |
| `run_parametric_monte_carlo()` | Immediate parametric simulation | Computation | Used | Useful |
| `run_position_sizing()`, `run_consecutive_losing()`, `run_profit_target()`, `run_random_win_rate()`, `run_robustness()`, `run_multi_entry()` | Immediate scenario simulations | Computation; robustness may read backtest data | Used | Useful |
| `optimization_progress_websocket()` | Connect to progress manager | Network/local state | Used | Useful |

`user_id` defaults to `1` in several handlers with an explicit TODO to obtain it from authentication.

### `app/api/routes/risk.py`

| Public symbols | Responsibility | Side effects | Usage status | Value status |
| -------------- | -------------- | ------------ | ------------ | ------------ |
| Position-sizing models and `calculate_position_size()` | Route to `PositionSizer` | Computation/logging | Used | Useful |
| Regime models and `detect_regime()` | Build state from MT5/manual returns and run crisis/full regime engines | Broker read; computation | Used | Useful |
| Allocation models and allocation handler | Compute target lots/deltas under budgets/correlation/regime | Broker read; computation | Used | Useful |
| Governance models and governance handler | Compare current/candidate portfolio risk and governance | Broker read; computation | Used | Essential to decision support |

The file embeds adapter/state-building/CSV parsing logic in addition to transport. Some risk endpoints authenticate only for MT5 mode; manual-data modes are callable without the same token path.

### `app/api/routes/optimization.py`, `edge.py`, and research surface

`edge.py` exposes request models and endpoints for dataset preparation, EDS trend/mean-reversion/null/session runs, seasonality, core metrics, market structure, unsupervised structure, stability, robustness, calibration, scorecard generation, profile snapshot persistence, single/batch automation, scheduling records, result retrieval, and evaluation refresh. It calls broker data providers, the research package, persistence, hashing/cache logic, and optional authentication.

This file is a broad orchestration layer rather than a narrow route adapter. Several helper paths can fall back to `user_id=1` after authentication errors, and the APScheduler refresh job does not invoke the automation; it only logs that migration is incomplete.

### `app/api/routes/ai_chat.py`

| Public symbols | Responsibility | Side effects | Usage status | Value status |
| -------------- | -------------- | ------------ | ------------ | ------------ |
| Payload models | Thread create/rename/retention, lifecycle, message, approval, paper execution, context resolution | None | Used | Supporting |
| `default_database_path()` | Resolve chat DB from environment/default | None | Used | Supporting |
| `get_user_id()` | Return environment/default development user | None | Used | Questionable for multi-user production |
| `get_conversation_service()` | Apply migrations and create repository/service per dependency call | Persistence migration | Used | Essential |
| `get_ceo_chat_gateway()` | Create CEO gateway | Object construction | Used | Essential |
| Thread list/create/get/rename/context/delete/archive/restore/purge routes | Manage conversation lifecycle | Persistence read/write | Used | Essential |
| Retention detail/update/lifecycle routes | Manage/run retention policy | Persistence read/write | Used | Useful |
| export/message routes | Export thread and add messages | Read/write | Used | Essential |
| `list_tools()` | Publish available read-only agent tool definitions | Read-only | Used | Useful |
| `resolve_context()` | Build route/page/DOM context | Computation | Used | Useful |
| signal/action draft, approval and paper-execution routes | Manage non-executed proposals/drafts and governed action lifecycle | Persistence; possible paper execution through gateway | Used | Essential |
| streaming chat route(s) | Stream CEO-chat response | Network streaming; service calls | Used | Essential |

The dependency returns `HARUQUANT_DEV_USER_ID` or `local-operator` rather than deriving a user from the main authentication system.

### `app/api/routes/live.py`

`live.py` provides live-session CRUD/control, strategy assignment, candles, signals, positions, orders, logs, statistics, risk-rule data, manual trade and position/order operations, and a live WebSocket channel. Public `MT5Utils.add_pips_to_price()` supports SL/TP calculations. The module stores active `LiveTradingSession` objects in a global process-local dictionary and mutates a shared MT5 client with per-user credentials.

Side effects include DB writes, live broker reads, broker mutations, background/runtime state changes, and WebSocket publication. Strategy permission is checked for live activation. The file mixes transport models, MT5 mapping, global connection management, session orchestration, persistence, and execution. Operational status is **unverified** because no live broker/test execution was available.

### `app/api/routes/docs.py`

| Symbol | Responsibility | Side effects | Usage status | Value status |
| ------ | -------------- | ------------ | ------------ | ------------ |
| `DOCS_ROOT` | Resolved repository docs root | None | Used | Supporting |
| `FileNode`, `SaveFileRequest` | Documentation transport | None | Used | Supporting |
| `get_directory_structure()` | Recursively list Markdown tree | Local file read | Used | Useful |
| `validate_path()` | Reject traversal and constrain resolved path | None | Used | Essential |
| `get_files()`, `get_content()` | List/read docs | Local file read; may create docs directory | Used | Useful |
| `save_file()`, `delete_file()` | Write/delete Markdown | Local file write/delete | Used | Useful but high impact |

No route-level authentication dependency is present in this file.

### `app/api/routes/dashboard/*`

| File | Public behaviour | Side effects | Usage status | Value status |
| ---- | ---------------- | ------------ | ------------ | ------------ |
| `broker.py` | Configure shared MT5 client from user credentials; return connection/account/equity/status data | DB read; broker external calls; shared client mutation | Used | Essential |
| `currency_strength.py` | Fetch market prices and calculate relative currency strength | Broker/data read; computation | Used | Useful |
| `forex_calendar.py` | Return economic-calendar/event data | External/data read | Used; operational status unverified | Useful |
| `market_hours.py` | Calculate market open/closed windows and local times | Read-only computation | Used | Useful |
| `system.py` | Return backend/database/resource status | DB/system reads | Used | Useful |

### `app/api/routes/sqx.py`

The module exposes StrategyQuant X import/parse/list/detail behavior and persists imported strategy/backtest artifacts. It is registered under `/api/sqx`, so its router is confirmed used. Side effects include file upload reads, parsing, and persistence writes. It is classified **Useful**; exact external SQX compatibility was not runtime-verified.

### `app/api/routes/import_trades.py`

The module contains trade-import API behavior, but neither `main.py` nor `app.py` includes its router. No other router inclusion or direct runtime caller was found. It is classified **Unused** with high static confidence and **No demonstrated value** in the current composition.

## 6. Actual Workflows

### `V1-WF-API-001` — General API Startup and Route Composition

* **Scope:** Internal
* **Trigger:** ASGI server imports `app.api.main:app` / `api.main:app`.
* **Input boundary:** Process environment and installed/importable modules.
* **Functions and methods used:** module optional imports → `FastAPI(...)` → middleware registration → router inclusion → `lifespan()`.
* **Files involved:** `main.py`, `middleware/security.py`, `router.py`, `scheduler.py`, every registered route module, `routes/simulator.py`.
* **External dependencies:** FastAPI, CORS middleware, database migrations, APScheduler.
* **Output boundary:** Running REST/WebSocket API.
* **Failure behaviour:** Most route-import exceptions are logged and omitted. Lifespan startup exceptions are caught/logged; application construction can continue. `/api/health` remains a constant healthy response.
* **Operational status:** **Partial/Working** — composition is real, but fail-open behavior can produce a degraded app without an explicit unhealthy state.
* **Evidence:** `app/api/main.py:optional imports, router inclusion, lifespan, health_check`; missing `app/api/routes/operator_strategies.py`.

```text
ASGI import
→ optional route imports
→ middleware + router registration
→ lifespan DB/migrations/lease cleanup/scheduler
→ API serves available routes
```

### `V1-WF-API-002` — User Registration, Login, Session Validation, Logout

* **Scope:** Cross-domain
* **Trigger:** `/api/auth/register`, `/login`, `/logout`.
* **Input boundary:** Registration/login JSON or bearer header.
* **Functions and methods used:** `register()` → DB user creation; `login()` → `authenticate_user()` → `generate_token()`; protected route → `get_user_id_from_token()` → `verify_token()`; logout → `invalidate_token()`.
* **Files involved:** `routes/auth.py`, `auth_utils.py`, `models.py`, database manager, utils password verifier.
* **External dependencies:** SQLite/database layer.
* **Output boundary:** User/session records and auth responses.
* **Failure behaviour:** HTTP 400/401/403/500; malformed logout is treated as already logged out.
* **Operational status:** **Unverified but structurally complete**.
* **Evidence:** direct calls in route and helper files.

### `V1-WF-API-003` — User Settings Read/Update

* **Scope:** Cross-domain
* **Trigger:** `/api/settings` GET/PUT.
* **Input boundary:** Bearer session and settings payload.
* **Sequence:** local token parsing → DB session validation → DB settings read/update → Pydantic response.
* **Files involved:** `routes/settings.py`, `auth_utils.py`, `models.py`, DB manager.
* **Output boundary:** User settings.
* **Failure behaviour:** HTTP 400/401/404/500.
* **Operational status:** **Unverified but structurally complete**.
* **Evidence:** route registration and direct calls.

### `V1-WF-API-004` — Market Data and Prepared Research Dataset

* **Scope:** Cross-domain
* **Trigger:** `/api/data/symbols` or `/api/data/dataset/prepare`.
* **Input boundary:** symbol/timeframe/source/range and optional bearer.
* **Sequence:** resolve user/credentials → choose MT5 or Dukascopy wrapper → load OHLCV → canonical preparation → clean/enrich/report → serialize/fingerprint → response.
* **Files involved:** `routes/data.py`; brokers; research dataset preparation; utils validator; DB.
* **External dependencies:** MT5/Dukascopy, pandas/numpy.
* **Output boundary:** symbol metadata or reusable prepared dataset payload.
* **Failure behaviour:** validation/provider HTTP errors; auth failure can fall back to user `1`.
* **Operational status:** **Partial/Unverified**.
* **Evidence:** `MT5DataSource`, `DukascopyDataSource`, `prepare_dataset_endpoint`.

### `V1-WF-API-005` — Strategy Catalogue and Version Lifecycle

* **Scope:** Cross-domain
* **Trigger:** strategy CRUD/version/import/export endpoints.
* **Input boundary:** strategy source, metadata, uploaded archive, IDs.
* **Sequence:** route → `StrategyCatalogService` → DB row/version → filesystem artifact → governance projection → response/download.
* **Files involved:** `routes/strategies.py`, `data/strategies/storage`, DB manager, governance repository.
* **Output boundary:** strategy catalogue records and versioned artifacts.
* **Failure behaviour:** HTTP validation/not-found/server errors; partial DB/filesystem operations are possible because no transaction spanning both is evidenced.
* **Operational status:** **Unverified but substantially complete**.
* **Evidence:** service methods and registered route.

### `V1-WF-API-006` — Backtest Execution and Result Retrieval

* **Scope:** Cross-domain
* **Trigger:** backtest run endpoint/background task.
* **Input boundary:** strategy, symbols, data range, engine/execution/account settings.
* **Sequence:** authenticate/resolve strategy → permission gate → map config → create DB run → simulation `Engine.run()` → adapt result → analytics overview → persist snapshots/results → broadcast logs/progress → query result endpoints.
* **Files involved:** `routes/backtest.py`, `websocket.py`, simulation, analytics, trading permissions, DB, strategy storage.
* **External dependencies:** broker data/MT5 where configured.
* **Output boundary:** persisted backtest, trades, equity, analytics, WebSocket logs.
* **Failure behaviour:** run status/logging updates; broad HTTP 500 paths; exact rollback behavior varies by branch.
* **Operational status:** **Partial/Unverified**.
* **Evidence:** `portfolio_run`, route/background helpers, router registration.

### `V1-WF-API-007` — Interactive Simulator Session Lifecycle

* **Scope:** Cross-domain
* **Trigger:** `/api/simulator/start`, resume, advance, seek, mutate, stop/save, or delete.
* **Input boundary:** authenticated user and simulator request models.
* **Sequence:** create DB session → construct `SimulatorSession` → load bars/account/risk/strategy/replay → acquire SQLite lease → attach runtime → process frames/trades → persist metadata/risk → finalize as backtest or delete.
* **Files involved:** `routes/simulator.py`, all `session/*`, execution trading, simulation, risk, strategy storage, DB.
* **External dependencies:** MT5/broker data when configured.
* **Output boundary:** session state, positions/orders, risk/governance/recommendations, saved backtest.
* **Failure behaviour:** 404 ownership failure, 400 not running, 409 another worker owns lease, 500 workflow errors; stop/save attempts to reattach runtime on save failure.
* **Operational status:** **Structurally complete; runtime unverified**.
* **Evidence:** direct registered call path through coordinator/runtime/services.

### `V1-WF-API-008` — Governance-Aware Simulator Trade/Order Mutation

* **Scope:** Cross-domain
* **Trigger:** simulator trade, pending order, position/order modify/delete, partial close, what-if endpoints.
* **Input boundary:** owned running session and mutation payload.
* **Sequence:** route → execution facade → `session/trade_service` → risk/governance evaluation → runtime mutation or non-mutating what-if → state/risk response.
* **Files involved:** `routes/simulator.py`, `app/services/execution/trading.py`, `session/trade_service.py`, `route_support.py`, `session_runtime.py`, risk simulation.
* **Output boundary:** mutation result plus updated state/governance/risk.
* **Failure behaviour:** governance rejection or HTTP 400/500; manual override only under explicit session/payload conditions.
* **Operational status:** **Structurally complete; runtime unverified**.
* **Evidence:** public trade-service functions and route delegates.

### `V1-WF-API-009` — Optimization, Walk-Forward and Monte Carlo

* **Scope:** Cross-domain
* **Trigger:** optimization/Monte Carlo endpoints.
* **Input boundary:** optimization or simulation request model.
* **Sequence:** create DB record → enqueue background service task or run immediate simulation → update progress manager → persist/query results → WebSocket clients receive progress.
* **Files involved:** `routes/optimization.py`, `websocket.py`, optimization services/models, research service, DB.
* **Output boundary:** run IDs, ranked results, reports, scenario simulations, progress events.
* **Failure behaviour:** HTTP 500 wrapping broad exceptions; cancellation updates status but does not prove active worker interruption.
* **Operational status:** **Partial/Unverified**.
* **Evidence:** registered routes and BackgroundTasks calls.

### `V1-WF-API-010` — Risk Analysis and Governance Decision Support

* **Scope:** Cross-domain
* **Trigger:** risk position-sizing/regime/allocation/governance endpoints.
* **Input boundary:** account, market, position, returns, regime and risk-limit payloads.
* **Sequence:** parse/build portfolio state → call risk engines → adapt reports to transport models.
* **Files involved:** `routes/risk.py`, risk calculations/core/domain/limits/optimization/regimes, simulation/broker adapters.
* **Output boundary:** sizes, regime states, allocations, current/candidate governance reports.
* **Failure behaviour:** validation 400; provider/computation 500.
* **Operational status:** **Unverified**.
* **Evidence:** direct route calls to risk engines.

### `V1-WF-API-011` — Edge Lab Research and Profile Persistence

* **Scope:** Cross-domain
* **Trigger:** Edge Lab dataset, analysis, snapshot, automation, result endpoints.
* **Input boundary:** source/range/symbols, prepared dataset, research settings.
* **Sequence:** data load/prepare → selected research functions → classify/validate/calibrate → scorecard/profile/snapshot persistence → result retrieval/evaluation.
* **Files involved:** `routes/edge.py`, brokers, research package, DB, validators.
* **Output boundary:** research results, profiles, scorecards, snapshots, automation records.
* **Failure behaviour:** broad 400/500 paths; scheduled refresh is not actually wired by `scheduler.py`.
* **Operational status:** **Partial**.
* **Evidence:** registered route and disabled scheduler message.

### `V1-WF-API-012` — AI Chat Thread, Context and Governed Draft Lifecycle

* **Scope:** Cross-domain
* **Trigger:** AI-chat thread/message/context/tool/signal/action routes.
* **Input boundary:** development user dependency, thread/message/context payload.
* **Sequence:** apply migrations → create repository/service/gateway → CRUD/retention/context/message → optional read-only tool catalogue → signal/action draft → approval/paper execution path → response/stream.
* **Files involved:** `routes/ai_chat.py`, conversation services/schemas, AI-chat repository, agentic read-only capabilities.
* **Output boundary:** chat records, exports, streamed responses, proposal/draft state.
* **Failure behaviour:** 400/404 and service errors; optional agentic tools fall back to empty list.
* **Operational status:** **Partial/Unverified**.
* **Evidence:** registered route and direct service calls.

### `V1-WF-API-013` — Live Trading Session and Real-Time Monitoring

* **Scope:** Cross-domain
* **Trigger:** live session/control/trade/monitor/WebSocket endpoints.
* **Input boundary:** authenticated user, MT5 credentials, strategy and trade/session payloads.
* **Sequence:** configure shared MT5 client → create/start in-memory `LiveTradingSession` → permission-check strategy → broker read/mutation → DB logs/state → WebSocket events.
* **Files involved:** `routes/live.py`, dashboard broker client, `websocket.py`, brokers/MT5, execution live, permissions, DB.
* **Output boundary:** session state, broker positions/orders/signals/logs/stats and real-time events.
* **Failure behaviour:** missing credentials/market data/session errors; process restart loses active-session map; exact broker-state reconciliation unverified.
* **Operational status:** **Unverified**.
* **Evidence:** registered route, global active-session dictionary, MT5/execution imports.

### `V1-WF-API-014` — Operator Health, Approval and Event Control Plane

* **Scope:** Cross-domain
* **Trigger:** `app.api.app:app` operator endpoints.
* **Input boundary:** operator headers, approval payloads, health/event requests.
* **Sequence:** construct dependencies/migrate DB → middleware builds principal → role guard → approval services/repository; health probes inspect dependencies; SSE emits events.
* **Files involved:** `app.py`, `auth.py`, `dependencies.py`, `approvals.py`, `health.py`, `events.py`.
* **Output boundary:** approval/vote records, health payloads, SSE messages.
* **Failure behaviour:** 401/403/400/service errors; event route is public; token value is not validated.
* **Operational status:** **Partial**.
* **Evidence:** direct app router inclusion and middleware.

### `V1-WF-API-015` — Documentation File Management

* **Scope:** Internal/cross-domain
* **Trigger:** `/api/docs/files|content|save|delete`.
* **Input boundary:** relative Markdown path/content.
* **Sequence:** validate path under resolved docs root → list/read/write/delete local files.
* **Files involved:** `routes/docs.py`.
* **External dependencies:** local filesystem.
* **Output boundary:** docs tree/content/status.
* **Failure behaviour:** HTTP 400/403/404/500.
* **Operational status:** **Working by static inspection; execution unverified**.
* **Evidence:** registered router and direct filesystem calls.

## 7. Usage and Caller Map

| Public symbol / surface | Called from | Call type | Runtime or test | Evidence |
| ----------------------- | ----------- | --------- | --------------- | -------- |
| `app.api.main:app` | README/runtime entry guidance | ASGI entry point | Runtime | `README.md`; module-level app |
| route-module `router` objects | `main.py::_include_optional_router` | Dynamic optional import + router inclusion | Runtime | `main.py` |
| `app.api.app:app` | Module-level `create_app()` | Direct construction; deployment caller unknown | Runtime possible | `app.py` |
| `SecretRedactionMiddleware` | `main.py` | Middleware registration | Runtime | `main.py` |
| `intent_classifier` | `IntentClassificationMiddleware` | Direct singleton call | Runtime | `main.py`, `router.py` |
| `start_scheduler`, `shutdown_scheduler` | `main.py::lifespan` | Direct call | Runtime | `main.py` |
| `cleanup_stale_simulation_leases` | `main.py::lifespan` | Optional route-module call | Runtime | `main.py`, `routes/simulator.py` |
| user auth helpers | auth/settings/data/simulator/risk/live routes | Direct call/FastAPI dependency | Runtime | imports and call sites |
| operator auth guards | approvals/operator app | Middleware/direct guard | Runtime | `auth.py`, `approvals.py`, `app.py` |
| operator health functions | local operator health routes | Direct call | Runtime | `app.py` |
| approval handlers/services | operator router | FastAPI decorator/direct service call | Runtime | `approvals.py`, `app.py` |
| `BacktestLogManager` singleton | backtest route/background code | Direct async call | Runtime | `routes/backtest.py` |
| `LiveTradingManager` singleton | live routes/runtime | Direct async call | Runtime | `routes/live.py` |
| `OptimizationProgressManager` singleton | optimization route/tasks | Direct async call | Runtime | `routes/optimization.py` |
| `portfolio_run` | backtest routes and optimization execution | Direct import/call | Runtime | `routes/backtest.py`; `app/services/optimization/execution.py` search |
| `StrategyCatalogService` | strategy route handlers | Direct construction/call | Runtime | `routes/strategies.py` |
| `SimulatorSessionManager`, `SessionCoordinator`, SQLite store | simulator module globals | Direct construction/call | Runtime | `routes/simulator.py` |
| session guards | simulator dependencies | FastAPI dependency | Runtime | `routes/simulator.py` |
| session lifecycle helpers | simulator handlers | Direct call | Runtime | `routes/simulator.py` |
| trade-service functions | execution trading facade/simulator handlers | Direct import/call | Runtime | `app/services/execution/trading.py`, simulator route |
| `SimulatorSession` | simulator start/resume | Direct construction | Runtime | simulator route/session service |
| shared transport models | route decorators/parameters | FastAPI/Pydantic reflection | Runtime | route imports/decorators |
| root compatibility `app.api.ai_chat.router` | No current caller found | — | — | main imports `app.api.routes.ai_chat` directly |
| `routes/import_trades.router` | No inclusion found | — | — | absent from both app composition roots |
| missing `routes.operator_strategies` | `main.py` | Optional string import | Runtime attempt | exact fetch returned absent |
| direct API tests | None found | — | Test | searches for `TestClient`, `ASGITransport`, app/route imports |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in API | Evidence |
| --------------------------- | -------------------------------- | ----------------- | -------- |
| `data.database` | users, sessions, settings, backtests, simulations, optimization, chat, governance, migrations | almost all route groups and operator dependencies | direct imports/calls |
| `data.strategies` | load/save/version/import/export strategy artifacts | strategies, backtest, simulator session service | direct imports |
| `app.services.utils` | logging, password verification, validation, redaction, settings | root, middleware and routes | direct imports |
| `app.services.brokers` | MT5 clients/data/symbols and Dukascopy | data, live, dashboard, optimization, risk, Edge Lab | direct imports |
| `app.services.simulation` | `Engine`, result and configuration helpers | backtest, simulator runtime, risk | direct imports |
| `app.services.execution` | live runtime, simulator trading facade, approval services | live, simulator, approvals | direct imports |
| `app.services.trading` | strategy permission gate and trade facade | backtest, live, simulator runtime/service | direct imports |
| `app.services.risk` | portfolio state/risk/governance/recommendation/what-if/limits/regimes/allocation | risk routes and simulator session runtime | direct imports |
| `app.services.analytics` | overview/report generation | backtest/dashboard | direct imports |
| `app.services.optimization` | tasks/models/Monte Carlo simulations | optimization routes | direct imports |
| `app.services.research` | dataset preparation, Edge Lab, unsupervised analysis | data, edge, optimization | direct imports |
| `app.services.conversation` | chat service/gateway/context/schema | AI-chat routes | direct imports |
| `agentic` | schema registry and optional read-only tool definitions | operator dependencies; AI chat | direct/optional imports |
| FastAPI/Starlette/Pydantic | HTTP, WebSocket, middleware and models | entire package | direct imports |
| APScheduler | scheduled cleanup/refresh | scheduler | direct imports |
| pandas/numpy | route-local data processing | data, backtest, live, risk, edge | direct imports |
| local filesystem | docs, strategy artifacts, exports/imports | docs and strategy routes | direct path/file calls |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| ASGI server / deployment | `app.api.main:app` or `api.main:app` | Start general API | README/module entry point |
| possible operator deployment | `app.api.app:app` | Start operator API | module-level app; deployment config unavailable |
| `app.services.optimization.execution` | `app.api.routes.backtest.portfolio_run` | Reuse route-local backtest execution adapter | repository import search |
| `app.services.execution.trading` | session trade-service/serializers/runtime helpers | Reuse simulator mutation logic | repository import search |
| frontend/UI clients | REST/WebSocket paths | User, research, trading and dashboard workflows | route registrations; traffic unavailable |
| scheduler/lifespan | simulator route cleanup function | Clear stale leases | `main.py` |

The outbound surface is very broad: the API domain directly touches most core domains, persistence, filesystems, broker providers, and agentic infrastructure.

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| `app/api/main.py` | `app/api/app.py` | Two FastAPI composition roots, CORS, health and auth concerns | both define module-level `app` | Deployment ambiguity and divergent behavior |
| `auth_utils.get_user_id_from_token` | `routes/settings.get_user_id_from_token` | Bearer parsing and DB session validation | near-equivalent logic | Inconsistent fixes/error behavior |
| DB-session user auth | operator header auth | Two incompatible identity models | `auth_utils.py` vs `auth.py` | Identity/authorization inconsistency |
| `/api/health` | operator app/database/Redis/schema health routes | Health reporting | `main.py`, `app.py`, `health.py` | General health can report healthy while dependencies/routes failed |
| `app/api/ai_chat.py` | `app/api/routes/ai_chat.py` | Router exposure | compatibility re-export vs direct registration | Stale wrapper |
| `routes/backtest.py::portfolio_run` | simulation service | Route layer owns reusable execution adapter imported by optimization | optimization import search | Reverse dependency into API layer |
| `routes/strategies.py::StrategyCatalogService` | strategy/data storage/services | Catalogue/version/governance orchestration | route-local service calls DB/filesystem/governance | Domain logic concentrated in transport layer |
| `routes/live.py` MT5 helpers | broker/trading/execution services | Connection, price, mapping and mutation support | direct MT5 use in route | Provider coupling and duplicated broker logic |
| `routes/data.py` serializers/source wrappers | research/data/broker services | Data-source and canonical dataset adaptation | route-local classes/helpers | Reuse/consistency risk |
| `routes/risk.py::_RiskApiClientAdapter` | broker/risk adapter concepts | Broker methods normalized for risk engines | route-local adapter | Duplicate adapter surface |
| settings slash/no-slash GET handlers | each other | Same operation on two paths | `_get_settings` wrappers | Redundant public surface |
| WebSocket process-local managers | session/live/optimization runtimes | Each independently manages connection maps | `websocket.py` | Repeated lifecycle/concurrency behavior |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| `app/services/api` | Requested package does not exist | exact file/path/import/dynamic-import searches | High | no package; architecture points to `app/api` |
| `app/api/ai_chat.py` | Compatibility wrapper bypassed by current registration | imports/callers/router registration | High | `main.py` imports `app.api.routes.ai_chat` |
| `routes/import_trades.py` | Router is not included by either app | router includes, imports, route-module searches | High | absent from composition roots |
| `routes/operator_strategies.py` | Referenced by optional import but file absent | exact fetch and search | High | missing target |
| `IntentClassifier.add_route()` | No runtime caller found | direct symbol/call search | High | only definition |
| `IntentClassifier.allowed_intents()` | No runtime caller found | direct symbol/call search | High | only definition |
| `IntentClassifier.route_map` | No runtime caller found | direct symbol/call search | High | only definition |
| `models.ErrorResponse` | No route response-model caller found | import/symbol search | Medium | model definition only in available evidence |
| `scheduler._refresh_edge_lab_universe` job | Job is scheduled but explicitly disabled | scheduler and Edge Lab call searches | High | logs disabled migration message |
| operator SSE event stream | Emits hard-coded demonstration messages | direct file inspection | High | static list in `_sse_messages` |
| Redis health probe | Returns “unknown; not wired yet” when selected | direct file inspection | High | `check_redis_health` |
| `app.api.app:app` | No repository deployment/caller reference found | entry-point/import searches | Medium | only module-level construction; external deployment may use it |
| unauthenticated/fallback user `1` paths | Auth exceptions are suppressed in data/Edge Lab and user defaults appear in optimization | direct route inspection | High | route code |
| direct API tests | None found | TestClient/ASGITransport/app.api/route symbol searches | Medium | repository search coverage; local ignored tests unavailable |

No item is labelled dead code unless it has high-confidence usage evidence. `app.api.app:app` remains “possibly used” because deployment can reference it without a repository import.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Operator strategy routes | Module referenced but absent | Router silently omitted | `main.py` optional import; missing file |
| Import-trades API | Existing router not registered | No endpoint through known apps | composition-root inspection |
| Edge Lab scheduled refresh | Job does not call Edge Lab automation | Scheduled workflow only logs disabled state | `scheduler.py` |
| Redis health | No actual Redis probe | Cannot establish backend health | `health.py` |
| Operator event stream | No event bus/subscription connection | UI receives static sample events | `events.py` |
| General API health | No dependency/router degradation check | Reports healthy despite swallowed startup/import failures | `main.py` |
| API test/coverage gate | `app/api` omitted from configured coverage/mypy package lists | Large transport/orchestration surface lacks evidenced quality gate | `pyproject.toml` |
| Operator identity | No token authority validation | Any non-empty bearer plus allowed role header passes middleware | `auth.py` |
| AI-chat identity | Development environment/default user rather than main session principal | Chat ownership can be disconnected from registered users | `routes/ai_chat.py` |
| Multi-worker WebSocket/session state | In-memory managers/maps lack shared backplane | Connections and live runtimes are worker-local | `websocket.py`, `routes/live.py` |
| Optimization cancellation | DB status update not shown to cancel active worker/task | Work may continue after “cancelled” record | `routes/optimization.py` |
| Strategy DB/filesystem/governance writes | No cross-resource transaction | Partial state possible on mid-workflow failure | `routes/strategies.py` |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-API-001` | Requested package path is wrong/nonexistent | `app/services/api` vs `app/api` | Audit/dependency tooling can miss the real domain | package/architecture inspection |
| `V1-ISSUE-API-002` | Two independent FastAPI apps | `main.py`, `app.py` | Split routes, auth, health and deployment behavior | two module-level `app` objects |
| `V1-ISSUE-API-003` | Broad optional imports suppress all exceptions | `main.py::_optional_import` | Broken route code can disappear at startup | catches `Exception` |
| `V1-ISSUE-API-004` | Startup failures are caught and application continues | `main.py::lifespan` | Migrations/scheduler/cleanup can fail without preventing traffic | broad startup exception handling |
| `V1-ISSUE-API-005` | General health endpoint is constant | `main.py::health_check` | False healthy state during degraded startup | fixed dict response |
| `V1-ISSUE-API-006` | Missing route module is still imported | `app.api.routes.operator_strategies` | Intended operator strategy API absent | exact missing file |
| `V1-ISSUE-API-007` | Existing import-trades router is disconnected | `routes/import_trades.py` | Capability unreachable through known apps | no router inclusion |
| `V1-ISSUE-API-008` | Operator auth does not validate token content | `auth.py::_extract_principal` | Caller-controlled identity/role trust boundary | header-only construction |
| `V1-ISSUE-API-009` | Operator event stream is public and static | `auth.py`, `events.py` | No real event observability; potential information exposure pattern | public-path bypass + hard-coded events |
| `V1-ISSUE-API-010` | User, operator and AI-chat identities are disconnected | `auth_utils.py`, `auth.py`, `routes/ai_chat.py` | Inconsistent ownership and authorization | DB token vs headers vs env/default user |
| `V1-ISSUE-API-011` | Authentication errors fall back to user `1` | data/Edge Lab routes | Unauthenticated caller may access default user resources | broad `except` fallback |
| `V1-ISSUE-API-012` | Optimization handlers use default user `1` | `routes/optimization.py` | Jobs are not tied to authenticated user | explicit TODO/default |
| `V1-ISSUE-API-013` | Documentation write/delete routes show no auth dependency | `routes/docs.py` | Remote local-file mutation surface | registered handlers |
| `V1-ISSUE-API-014` | Route files contain substantial domain/business orchestration | backtest/live/risk/edge/strategies/session runtime | High coupling, difficult isolated verification | file responsibilities/call paths |
| `V1-ISSUE-API-015` | Optimization service imports API route helper | `app/services/optimization/execution.py` → `routes/backtest.portfolio_run` | Lower service depends upward on transport layer | repository import search |
| `V1-ISSUE-API-016` | Shared mutable singletons initialized at import time | DB managers, MT5 client, WebSocket managers, active sessions | Process-local state and test isolation issues | module globals |
| `V1-ISSUE-API-017` | WebSocket managers are process-local only | `websocket.py` | Multi-worker clients see inconsistent buffers/progress | in-memory maps/deques |
| `V1-ISSUE-API-018` | Live sessions are process-local | `routes/live.py::active_sessions` | Restart/worker routing loses active runtime | global dictionary |
| `V1-ISSUE-API-019` | Simulator runtime file is an oversized integration hub | `session/session_runtime.py` | Many dependencies/responsibilities and large change blast radius | >2,000 lines and broad imports |
| `V1-ISSUE-API-020` | Backtest route is oversized and reusable as service | `routes/backtest.py` | Transport and execution/persistence/analytics mixed | >1,300 lines; imported by service |
| `V1-ISSUE-API-021` | Edge, live, risk and optimization routes are oversized | corresponding route files | Difficult testing and unclear ownership | broad imports/responsibilities |
| `V1-ISSUE-API-022` | Settings auth helper duplicated | `auth_utils.py`, `routes/settings.py` | Divergent behavior risk | duplicate implementation |
| `V1-ISSUE-API-023` | Redis health is a placeholder | `health.py` | Cannot verify configured backend | explicit “not wired yet” |
| `V1-ISSUE-API-024` | Schema health accesses a private registry field | `health.py` | Tight implementation coupling | `dependencies.schema_registry._records` |
| `V1-ISSUE-API-025` | Scheduler registers a disabled job | `scheduler.py` | Operational noise and misleading scheduling | log-only refresh function |
| `V1-ISSUE-API-026` | API package is absent from configured coverage source | `pyproject.toml` | API regressions are not evidenced by project coverage gate | coverage source excludes `app/api` |
| `V1-ISSUE-API-027` | API package is absent from explicit mypy package list | `pyproject.toml` | Large public surface lacks evidenced static type gate | mypy packages exclude API |
| `V1-ISSUE-API-028` | Direct API tests were not found | `tests` | Operational behavior and security boundaries lack repository evidence | test searches |
| `V1-ISSUE-API-029` | Compatibility wrapper adds no current value | `app/api/ai_chat.py` | Extra import surface/stale migration artifact | direct route import bypasses wrapper |
| `V1-ISSUE-API-030` | General route availability depends on import side effects | `main.py` and route module globals | DB/broker/module errors affect which API exists | optional import composition |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-API-001` | General FastAPI composition | `main.py::app` | `001` | Used | Essential | Fail-open optional composition |
| `V1-CAP-API-002` | Operator API composition | `app.py::app` | `014` | Possibly used | Useful | Separate deployment entry point |
| `V1-CAP-API-003` | User registration/login/logout | `routes/auth.py`, `auth_utils.py`, models | `002` | Used | Essential | DB session tokens |
| `V1-CAP-API-004` | Operator role gate | `auth.py` | `014` | Used | Essential | Token authority not validated |
| `V1-CAP-API-005` | User settings | `routes/settings.py` | `003` | Used | Useful | Duplicate auth helper |
| `V1-CAP-API-006` | Request secret redaction | middleware/security | `001` | Used | Useful | Headers/query only |
| `V1-CAP-API-007` | Intent classification | `router.py`, main middleware | `001` | Used | Useful | Metadata only; no dispatcher enforcement |
| `V1-CAP-API-008` | Market symbol discovery | `routes/data.py` | `004` | Used | Useful | MT5 credentials/provider |
| `V1-CAP-API-009` | Prepared research datasets | `routes/data.py` | `004`, `011` | Used | Essential | Clean/enrich/serialize |
| `V1-CAP-API-010` | Strategy catalogue CRUD | `routes/strategies.py` | `005` | Used | Essential | DB/filesystem/governance coordination |
| `V1-CAP-API-011` | Strategy version/import/export | `routes/strategies.py` | `005` | Used | Essential | Local artifacts |
| `V1-CAP-API-012` | Backtest execution | `routes/backtest.py` | `006` | Used | Essential | Route-local execution adapter |
| `V1-CAP-API-013` | Backtest CRUD/results/analytics | `routes/backtest.py` | `006` | Used | Essential | Persistence and analytics |
| `V1-CAP-API-014` | Backtest log streaming | `websocket.py`, backtest route | `006` | Used | Useful | Process-local buffer |
| `V1-CAP-API-015` | Interactive simulator sessions | simulator route/session package | `007` | Used | Essential | DB lease + in-memory runtime |
| `V1-CAP-API-016` | Simulator frame/replay control | `SimulatorSession`, simulator routes | `007` | Used | Essential | Advance/seek/replay |
| `V1-CAP-API-017` | Simulator trade/order mutation | trade service/execution facade/routes | `008` | Used | Essential | Governance-aware |
| `V1-CAP-API-018` | Simulator what-if analysis | trade service/runtime/risk | `008` | Used | Useful | Non-mutating scenario path |
| `V1-CAP-API-019` | Simulator risk/governance/recommendations | session runtime/support/serializers | `007`, `008` | Used | Essential | Large coupling surface |
| `V1-CAP-API-020` | Optimization runs/results | optimization routes/services | `009` | Used | Essential | Background tasks |
| `V1-CAP-API-021` | Walk-forward analysis | optimization route/service | `009` | Used | Useful | Runtime unverified |
| `V1-CAP-API-022` | Monte Carlo/scenario simulation | optimization route/monte-carlo services | `009` | Used | Useful | Multiple immediate endpoints |
| `V1-CAP-API-023` | Optimization progress WebSocket | WebSocket manager/route | `009` | Used | Useful | Process-local |
| `V1-CAP-API-024` | Position sizing API | risk route | `010` | Used | Useful | Risk service call |
| `V1-CAP-API-025` | Regime detection API | risk route | `010` | Used | Useful | MT5/manual modes |
| `V1-CAP-API-026` | Allocation planning API | risk route | `010` | Used | Useful | Portfolio decision support |
| `V1-CAP-API-027` | Governance comparison API | risk route | `010` | Used | Essential | Current/candidate reports |
| `V1-CAP-API-028` | Edge Lab analyses | `routes/edge.py` | `011` | Used | Essential | Broad research surface |
| `V1-CAP-API-029` | Edge profile/snapshot persistence | Edge route/DB | `011` | Used | Useful | Operational verification unavailable |
| `V1-CAP-API-030` | Edge automation records | Edge route | `011` | Used | Useful | Scheduled execution disconnected |
| `V1-CAP-API-031` | AI-chat thread/message lifecycle | AI-chat route/conversation service | `012` | Used | Essential | Development user dependency |
| `V1-CAP-API-032` | AI-chat context and read-only tool catalogue | AI-chat route | `012` | Used | Useful | Optional tools fall back empty |
| `V1-CAP-API-033` | AI signal/action draft lifecycle | AI-chat route/gateway | `012` | Used | Essential | Governed proposal surface |
| `V1-CAP-API-034` | Live session management | `routes/live.py` | `013` | Used | Essential | Process-local active map |
| `V1-CAP-API-035` | Live broker reads/mutations | live/dashboard broker routes | `013` | Used | Essential | Runtime unverified/high risk |
| `V1-CAP-API-036` | Live WebSocket monitoring | live manager/route | `013` | Used | Useful | Process-local subscriptions |
| `V1-CAP-API-037` | Broker dashboard | dashboard broker | `013` | Used | Essential | Shared client mutation |
| `V1-CAP-API-038` | Currency strength | dashboard route | dashboard read | Used | Useful | Computation/provider read |
| `V1-CAP-API-039` | Forex calendar | dashboard route | dashboard read | Used | Useful | Provider status unverified |
| `V1-CAP-API-040` | Market hours | dashboard route | dashboard read | Used | Useful | Time calculation |
| `V1-CAP-API-041` | System/resource status | dashboard route | dashboard read | Used | Useful | Not equivalent to startup health |
| `V1-CAP-API-042` | Operator approvals and votes | approvals/operator app | `014` | Used | Essential | Persistence-backed |
| `V1-CAP-API-043` | Operator component health | health/operator app | `014` | Used | Useful | Redis incomplete |
| `V1-CAP-API-044` | Operator event SSE | events/operator app | `014` | Used | Questionable | Static sample events |
| `V1-CAP-API-045` | Documentation tree/read/write/delete | docs route | `015` | Used | Useful | No auth evidenced |
| `V1-CAP-API-046` | SQX import/inspection | sqx route | import workflow | Used | Useful | Runtime parser compatibility unverified |
| `V1-CAP-API-047` | Trade import route | import_trades route | None | Unused | No demonstrated value | Not registered |
| `V1-CAP-API-048` | Operator strategy API | Missing module | None | Unused/missing | No demonstrated value | Optional import target absent |
| `V1-CAP-API-049` | Background session cleanup | scheduler + simulator cleanup | `001`, `007` | Used | Supporting | APScheduler and startup cleanup |
| `V1-CAP-API-050` | Scheduled Edge refresh | scheduler placeholder | `011` intended | Used as log-only job | Questionable | No analysis invoked |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* General route composition and the actual endpoint catalogue.
* Database-backed user registration/session validation and ownership checks.
* Strategy catalogue/version artifact workflows.
* Backtest execution, result persistence, analytics and log streaming.
* Simulator session leasing, ownership, resume/save lifecycle, and governance-aware trade operations.
* Optimization/Monte Carlo execution and progress reporting.
* Risk decision-support endpoints.
* Edge Lab research orchestration and profile persistence.
* AI-chat thread/message/context/proposal workflows.
* Operator approval creation/voting.
* Broker/dashboard and live-monitoring interfaces, subject to runtime confirmation.

### Behaviour that exists but is disconnected or incomplete

* `routes/import_trades.py` exists but is not registered.
* `routes.operator_strategies` is expected but absent.
* scheduled Edge Lab refresh is a disabled logging placeholder.
* Redis health is not implemented.
* operator event streaming is not connected to a real event source.
* the compatibility `app/api/ai_chat.py` wrapper is not used by current composition.
* operator API deployment usage cannot be confirmed from repository callers.

### Likely dead weight

High-confidence candidates:

* the unused AI-chat compatibility wrapper;
* the unregistered import-trades router, unless directly mounted by external code not in the repository;
* unused mutable-intent-classifier methods;
* scheduled disabled Edge refresh behavior;
* unused response models where no imports were found.

The missing operator-strategies module is not dead code; it is an incomplete reference.

### Duplicated responsibilities

* general and operator application composition;
* multiple identity/authentication mechanisms;
* duplicate token parsing in settings;
* route-local strategy, backtest, broker, data and risk adapters/services;
* multiple independent WebSocket manager implementations;
* overlapping health endpoints with different meanings.

### Important uncertainties

* Which FastAPI app(s) are deployed.
* Whether live trading, MT5, Dukascopy, forex-calendar and SQX flows work with current external providers.
* Whether any external deployment mounts `import_trades.router` or imports `app.api.ai_chat.router`.
* Whether ignored/local tests cover the API.
* Actual traffic and use frequency per endpoint.
* Multi-worker process configuration and its effect on in-memory managers/session maps.

### Areas requiring manual confirmation

1. Confirm canonical deployment entry points: general app, operator app, or both.
2. Confirm whether operator headers are intentionally trusted only behind an authenticated reverse proxy.
3. Confirm whether fallback user ID `1` is intentional development behavior.
4. Confirm whether docs write/delete endpoints are externally reachable.
5. Confirm whether `routes/import_trades.py` should be reachable.
6. Confirm the intended source of `routes.operator_strategies`.
7. Run a clean startup and record which optional routes import successfully.
8. Run API integration tests against temporary SQLite, mocked broker providers, WebSockets, and both app roots.
9. Confirm production worker count and whether process-local runtime state is acceptable.
10. Confirm which API files are expected to be included in coverage and static typing gates.

## Evidence Not Accessible

* Local checkout and executable test/import/startup results.
* Uncommitted, ignored, generated, or deployment-only files.
* Production ASGI/process-manager configuration and environment variables.
* Runtime endpoint traffic and frontend telemetry.
* Live MT5/Dukascopy/calendar/SQX provider responses.
* Deployed reverse-proxy or identity-provider guarantees for operator headers.
* Multi-worker/distributed runtime behavior.
