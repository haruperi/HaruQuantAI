/**
 * Frozen typed route contracts for the 138 registered backend-v1 operations.
 *
 * Source of truth: `app/services/api/contracts/catalog.py` (`_KNOWN_ROUTE_CONTRACTS`).
 * The drift test in `clients.contract.test.ts` asserts that this module
 * mirrors the backend inventory exactly. Do not add or remove a route here
 * without a matching backend change.
 */

import type { RouteSideEffect } from "./contracts";

/** HTTP method union. */
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

/**
 * One typed frontend route contract.
 *
 * - `returnsText` marks routes that bypass the JSON envelope and return a raw
 *   text body (only `/api/v1/metrics` today, Prometheus exposition format).
 * - `authRequired` marks routes that require an authenticated session even
 *   when no specific permission string is attached (e.g. `/api/v1/auth/me`).
 * - `stream` marks SSE routes whose response contract is `StreamEvent.v1`
 *   (only `/api/v1/data/stream` today).
 */
export interface RouteContract<
  TMethod extends HttpMethod = HttpMethod,
  TPath extends string = string,
> {
  readonly id: string;
  readonly method: TMethod;
  readonly path: TPath;
  readonly permission: string | null;
  readonly authRequired: boolean;
  readonly sideEffect: RouteSideEffect;
  /** True for governed writes (require idempotency + governance + CSRF). */
  readonly governed: boolean;
  /** True for routes that require an idempotency-key header. */
  readonly idempotencyRequired: boolean;
  /** True for cursor-paginated list routes. */
  readonly paginated: boolean;
  /** True for SSE stream routes (response_contract = StreamEvent.v1). */
  readonly stream: boolean;
  /** True when the route returns raw text instead of the JSON envelope. */
  readonly returnsText: boolean;
}

/** Build one route contract with defaults aligned to the backend `_contract` helper. */
function route<TMethod extends HttpMethod, TPath extends string>(config: {
  id: string;
  method: TMethod;
  path: TPath;
  permission?: string;
  authRequired?: boolean;
  sideEffect?: RouteSideEffect;
  governed?: boolean;
  idempotencyRequired?: boolean;
  paginated?: boolean;
  stream?: boolean;
  returnsText?: boolean;
}): RouteContract<TMethod, TPath> {
  return {
    id: config.id,
    method: config.method,
    path: config.path,
    permission: config.permission ?? null,
    authRequired: config.authRequired ?? config.permission !== undefined,
    sideEffect: config.sideEffect ?? "read",
    governed: config.governed ?? false,
    idempotencyRequired: config.idempotencyRequired ?? false,
    paginated: config.paginated ?? false,
    stream: config.stream ?? false,
    returnsText: config.returnsText ?? false,
  };
}

// --- Authentication (4) --------------------------------------------------

export const authRoutes = {
  register: route({
    id: "api.auth.register",
    method: "POST",
    path: "/api/v1/auth/register",
    sideEffect: "write",
  }),
  login: route({
    id: "api.auth.login",
    method: "POST",
    path: "/api/v1/auth/login",
    sideEffect: "write",
  }),
  logout: route({
    id: "api.auth.logout",
    method: "POST",
    path: "/api/v1/auth/logout",
    sideEffect: "write",
  }),
  me: route({
    id: "api.auth.me",
    method: "GET",
    path: "/api/v1/auth/me",
    // Requires an authenticated session but carries no permission string.
    authRequired: true,
  }),
} as const;

// --- Health (2) ----------------------------------------------------------

export const healthRoutes = {
  liveness: route({
    id: "api.health.liveness",
    method: "GET",
    path: "/api/v1/health/liveness",
    sideEffect: "none",
  }),
  readiness: route({
    id: "api.health.readiness",
    method: "GET",
    path: "/api/v1/health/readiness",
    permission: "ops:read",
    sideEffect: "none",
  }),
} as const;

// --- Settings (5) --------------------------------------------------------

export const settingsRoutes = {
  read: route({
    id: "api.settings.read",
    method: "GET",
    path: "/api/v1/settings",
    permission: "settings:read",
  }),
  update: route({
    id: "api.settings.update",
    method: "PUT",
    path: "/api/v1/settings",
    permission: "settings:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  manifest: route({
    id: "api.settings.manifest",
    method: "GET",
    path: "/api/v1/settings/manifest",
    permission: "settings:admin",
  }),
  credentials: route({
    id: "api.settings.credentials.read",
    method: "GET",
    path: "/api/v1/settings/credentials",
    permission: "settings:admin",
  }),
  updateCredential: route({
    id: "api.settings.credentials.update",
    method: "PUT",
    path: "/api/v1/settings/credentials/{slot}",
    permission: "settings:admin",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
} as const;

// --- Watchlists (4) --------------------------------------------------------

export const watchlistsRoutes = {
  list: route({
    id: "api.watchlists.list",
    method: "GET",
    path: "/api/v1/watchlists",
    permission: "watchlists:read",
  }),
  create: route({
    id: "api.watchlists.create",
    method: "POST",
    path: "/api/v1/watchlists",
    permission: "watchlists:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  update: route({
    id: "api.watchlists.update",
    method: "PATCH",
    path: "/api/v1/watchlists/{watchlist_id}",
    permission: "watchlists:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  delete: route({
    id: "api.watchlists.delete",
    method: "DELETE",
    path: "/api/v1/watchlists/{watchlist_id}",
    permission: "watchlists:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
} as const;

// --- Data / symbol discovery + market stream (2) -------------------------

export const dataRoutes = {
  capabilities: route({
    id: "api.data.capabilities",
    method: "GET",
    path: "/api/v1/data/capabilities",
    permission: "data:read",
  }),
  symbols: route({
    id: "api.data.symbols",
    method: "GET",
    path: "/api/v1/data/symbols",
    permission: "data:read",
    paginated: true,
  }),
  series: route({
    id: "api.data.series",
    method: "GET",
    path: "/api/v1/data/series",
    permission: "data:read",
  }),
  instruments: route({
    id: "api.data.instruments",
    method: "GET",
    path: "/api/v1/data/instruments",
    permission: "data:read",
  }),
  brokers: route({
    id: "api.data.brokers",
    method: "GET",
    path: "/api/v1/data/brokers",
    permission: "data:read",
  }),
  instrument: route({
    id: "api.data.instrument",
    method: "GET",
    path: "/api/v1/data/instruments/{instrument}",
    permission: "data:read",
  }),
  updateSeries: route({
    id: "api.data.series_update",
    method: "PATCH",
    path: "/api/v1/data/series/{series_id}",
    permission: "data:write",
    sideEffect: "write",
    governed: true,
    idempotencyRequired: true,
  }),
  syncReference: route({
    id: "api.data.reference_sync",
    method: "POST",
    path: "/api/v1/data/reference/sync",
    permission: "data:write",
    sideEffect: "write",
    governed: true,
    idempotencyRequired: true,
  }),
  updateInstrument: route({
    id: "api.data.instrument_update",
    method: "PATCH",
    path: "/api/v1/data/instruments/{instrument}",
    permission: "data:write",
    sideEffect: "write",
    governed: true,
    idempotencyRequired: true,
  }),
  datasets: route({
    id: "api.data.datasets",
    method: "GET",
    path: "/api/v1/data/datasets",
    permission: "data:read",
  }),
  markets: route({
    id: "api.data.markets",
    method: "GET",
    path: "/api/v1/data/markets",
    permission: "data:read",
    paginated: true,
  }),
  quotes: route({
    id: "api.data.quotes",
    method: "GET",
    path: "/api/v1/data/quotes",
    permission: "data:read",
  }),
  bars: route({
    id: "api.data.bars",
    method: "GET",
    path: "/api/v1/data/bars",
    permission: "data:read",
  }),
  stream: route({
    id: "api.data.stream",
    method: "GET",
    path: "/api/v1/data/stream",
    permission: "data:read",
    sideEffect: "stream",
    stream: true,
  }),
  snapshotStream: route({
    id: "api.data.snapshot_stream",
    method: "GET",
    path: "/api/v1/data/snapshot-stream",
    permission: "data:read",
    sideEffect: "stream",
    stream: true,
  }),
  depthStream: route({
    id: "api.data.depth_stream",
    method: "GET",
    path: "/api/v1/data/depth-stream",
    permission: "data:read",
    sideEffect: "stream",
    stream: true,
  }),
  prepareDataset: route({
    id: "api.data.prepare_dataset",
    method: "POST",
    path: "/api/v1/data/datasets/prepare",
    permission: "data:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  importDialects: route({
    id: "api.data.import_dialects",
    method: "GET",
    path: "/api/v1/data/imports/dialects",
    permission: "data:read",
  }),
  importDataset: route({
    id: "api.data.import_dataset",
    method: "POST",
    path: "/api/v1/data/imports",
    permission: "data:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Strategies (4) ------------------------------------------------------

export const strategiesRoutes = {
  catalogue: route({
    id: "api.strategies.catalogue",
    method: "GET",
    path: "/api/v1/strategies",
    permission: "strategy:read",
  }),
  versions: route({
    id: "api.strategies.versions",
    method: "GET",
    path: "/api/v1/strategies/{strategy_id}/versions",
    permission: "strategy:read",
  }),
  register: route({
    id: "api.strategies.register",
    method: "POST",
    path: "/api/v1/strategies",
    permission: "strategy:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  updateParameters: route({
    id: "api.strategies.update_parameters",
    method: "PATCH",
    path: "/api/v1/strategies/{strategy_id}/parameters",
    permission: "strategy:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Research (20) -------------------------------------------------------

export const researchRoutes = {
  run: route({
    id: "api.research.run",
    method: "POST",
    path: "/api/v1/research/run",
    permission: "research:run",
    sideEffect: "read",
  }),
  presets: route({
    id: "api.research.presets",
    method: "GET",
    path: "/api/v1/research/presets",
    permission: "research:read",
  }),
  dashboard: route({
    id: "api.research.dashboard",
    method: "GET",
    path: "/api/v1/research/dashboard",
    permission: "research:read",
  }),
  createExperiment: route({
    id: "api.research.create_experiment",
    method: "POST",
    path: "/api/v1/research/experiments",
    permission: "research:run",
    sideEffect: "write",
  }),
  experiments: route({
    id: "api.research.experiments",
    method: "GET",
    path: "/api/v1/research/experiments",
    permission: "research:read",
  }),
  experiment: route({
    id: "api.research.experiment",
    method: "GET",
    path: "/api/v1/research/experiments/{experiment_id}",
    permission: "research:read",
  }),
  createRun: route({
    id: "api.research.create_run",
    method: "POST",
    path: "/api/v1/research/experiments/{experiment_id}/runs",
    permission: "research:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  runs: route({
    id: "api.research.runs",
    method: "GET",
    path: "/api/v1/research/runs",
    permission: "research:read",
  }),
  compareRuns: route({
    id: "api.research.compare_runs",
    method: "POST",
    path: "/api/v1/research/runs/compare",
    permission: "research:read",
    sideEffect: "write",
  }),
  runDetail: route({
    id: "api.research.run_detail",
    method: "GET",
    path: "/api/v1/research/runs/{run_id}",
    permission: "research:read",
  }),
  runReport: route({
    id: "api.research.run_report",
    method: "GET",
    path: "/api/v1/research/runs/{run_id}/report",
    permission: "research:read",
  }),
  runStage: route({
    id: "api.research.run_stage",
    method: "GET",
    path: "/api/v1/research/runs/{run_id}/stages/{stage}",
    permission: "research:read",
  }),
  runArtifacts: route({
    id: "api.research.run_artifacts",
    method: "GET",
    path: "/api/v1/research/runs/{run_id}/artifacts",
    permission: "research:read",
  }),
  cancelRun: route({
    id: "api.research.cancel_run",
    method: "POST",
    path: "/api/v1/research/runs/{run_id}/cancel",
    permission: "research:run",
    sideEffect: "write",
  }),
  runEvents: route({
    id: "api.research.run_events",
    method: "GET",
    path: "/api/v1/research/runs/{run_id}/events",
    permission: "research:read",
    sideEffect: "stream",
    stream: true,
  }),
  createAutomation: route({
    id: "api.research.create_automation",
    method: "POST",
    path: "/api/v1/research/automation",
    permission: "research:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  automationBatch: route({
    id: "api.research.automation_batch",
    method: "GET",
    path: "/api/v1/research/automation/{batch_id}",
    permission: "research:read",
  }),
  expectancy: route({
    id: "api.research.expectancy",
    method: "GET",
    path: "/api/v1/research/expectancy",
    permission: "research:read",
  }),
  createExpectancy: route({
    id: "api.research.create_expectancy",
    method: "POST",
    path: "/api/v1/research/expectancy",
    permission: "research:govern",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  transitionExpectancy: route({
    id: "api.research.transition_expectancy",
    method: "POST",
    path: "/api/v1/research/expectancy/{profile_id}/transition",
    permission: "research:govern",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  drift: route({
    id: "api.research.drift",
    method: "GET",
    path: "/api/v1/research/drift",
    permission: "research:read",
  }),
  createStressScenario: route({
    id: "api.research.create_stress_scenario",
    method: "POST",
    path: "/api/v1/research/stress-scenarios",
    permission: "research:govern",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Dashboards (6) ------------------------------------------------------

export const dashboardRoutes = {
  broker: route({
    id: "api.dashboard.broker",
    method: "GET",
    path: "/api/v1/dashboard/broker",
    permission: "dashboard:read",
  }),
  equityCurve: route({
    id: "api.dashboard.equity_curve",
    method: "GET",
    path: "/api/v1/dashboard/equity-curve",
    permission: "dashboard:read",
  }),
  summary: route({
    id: "api.dashboard.summary",
    method: "GET",
    path: "/api/v1/dashboard/summary",
    permission: "dashboard:read",
  }),
  systemResources: route({
    id: "api.dashboard.system_resources",
    method: "GET",
    path: "/api/v1/dashboard/system/resources",
    permission: "dashboard:read",
  }),
  marketHours: route({
    id: "api.dashboard.market_hours",
    method: "GET",
    path: "/api/v1/dashboard/market-hours",
    permission: "dashboard:read",
  }),
  forexCalendar: route({
    id: "api.dashboard.forex_calendar",
    method: "GET",
    path: "/api/v1/dashboard/forex-calendar",
    permission: "dashboard:read",
  }),
} as const;

// --- Operator (3) --------------------------------------------------------

export const operatorRoutes = {
  auditEvents: route({
    id: "api.operator.audit_events",
    method: "GET",
    path: "/api/v1/operator/audit-events",
    permission: "ops:audit:read",
  }),
  events: route({
    id: "api.operator.events",
    method: "GET",
    path: "/api/v1/operator/events",
    permission: "ops:events:read",
  }),
  approvals: route({
    id: "api.operator.approvals",
    method: "POST",
    path: "/api/v1/operator/approvals",
    permission: "ops:approve",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Metrics (1) ---------------------------------------------------------

export const metricsRoutes = {
  scrape: route({
    id: "api.metrics",
    method: "GET",
    path: "/api/v1/metrics",
    permission: "ops:metrics:read",
    sideEffect: "none",
    returnsText: true,
  }),
} as const;

// --- Simulation (3) ------------------------------------------------------

export const simulationRoutes = {
  run: route({
    id: "api.simulation.run",
    method: "POST",
    path: "/api/v1/simulation/run",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  portfolioRun: route({
    id: "api.simulation.portfolio_run",
    method: "POST",
    path: "/api/v1/simulation/portfolio-run",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  result: route({
    id: "api.simulation.result",
    method: "GET",
    path: "/api/v1/simulation/results/{run_id}",
    permission: "simulation:read",
  }),
} as const;

// --- Simulator canonical backtest runs (6) -------------------------------

export const simulatorRoutes = {
  strategies: route({
    id: "api.simulator.strategies",
    method: "GET",
    path: "/api/v1/simulator/strategies",
    permission: "simulation:read",
  }),
  startRun: route({
    id: "api.simulator.start_run",
    method: "POST",
    path: "/api/v1/simulator/runs",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  runs: route({
    id: "api.simulator.runs",
    method: "GET",
    path: "/api/v1/simulator/runs",
    permission: "simulation:read",
  }),
  run: route({
    id: "api.simulator.run",
    method: "GET",
    path: "/api/v1/simulator/runs/{run_id}",
    permission: "simulation:read",
  }),
  cancelRun: route({
    id: "api.simulator.cancel_run",
    method: "DELETE",
    path: "/api/v1/simulator/runs/{run_id}",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  runStream: route({
    id: "api.simulator.run_stream",
    method: "GET",
    path: "/api/v1/simulator/runs/{run_id}/stream",
    permission: "simulation:read",
    sideEffect: "stream",
    stream: true,
  }),
} as const;

// --- Simulation Workbench (18) -------------------------------------------

export const simulationWorkbenchRoutes = {
  createLiveSession: route({
    id: "api.simulator.workbench.live_session_create",
    method: "POST",
    path: "/api/v1/simulator/live-sessions",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  liveSessions: route({
    id: "api.simulator.workbench.live_sessions",
    method: "GET",
    path: "/api/v1/simulator/live-sessions",
    permission: "simulation:read",
  }),
  liveSession: route({
    id: "api.simulator.workbench.live_session",
    method: "GET",
    path: "/api/v1/simulator/live-sessions/{session_id}",
    permission: "simulation:read",
  }),
  liveSessionViewport: route({
    id: "api.simulator.workbench.live_session_viewport",
    method: "GET",
    path: "/api/v1/simulator/live-sessions/{session_id}/viewport",
    permission: "simulation:read",
  }),
  stepLiveSession: route({
    id: "api.simulator.workbench.live_session_step",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/step",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  seekLiveSession: route({
    id: "api.simulator.workbench.live_session_seek",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/seek",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  submitCommand: route({
    id: "api.simulator.workbench.live_session_command",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/commands",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  branchLiveSession: route({
    id: "api.simulator.workbench.live_session_branch",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/branch",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  restoreLiveSession: route({
    id: "api.simulator.workbench.live_session_restore",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/restore",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  rearmLiveSession: route({
    id: "api.simulator.workbench.live_session_rearm",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/rearm",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  finalizeLiveSession: route({
    id: "api.simulator.workbench.live_session_finalize",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/finalize",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  reproduceLiveSession: route({
    id: "api.simulator.workbench.live_session_reproduce",
    method: "POST",
    path: "/api/v1/simulator/live-sessions/{session_id}/reproduce",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  closeLiveSession: route({
    id: "api.simulator.workbench.live_session_close",
    method: "DELETE",
    path: "/api/v1/simulator/live-sessions/{session_id}",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  createBatch: route({
    id: "api.simulator.workbench.batch_create",
    method: "POST",
    path: "/api/v1/simulator/batches",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  batch: route({
    id: "api.simulator.workbench.batch",
    method: "GET",
    path: "/api/v1/simulator/batches/{batch_id}",
    permission: "simulation:read",
  }),
  batchStream: route({
    id: "api.simulator.workbench.batch_stream",
    method: "GET",
    path: "/api/v1/simulator/batches/{batch_id}/stream",
    permission: "simulation:read",
    sideEffect: "stream",
    stream: true,
  }),
  cancelBatch: route({
    id: "api.simulator.workbench.batch_cancel",
    method: "POST",
    path: "/api/v1/simulator/batches/{batch_id}/cancel",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  retryFailedBatch: route({
    id: "api.simulator.workbench.batch_retry_failed",
    method: "POST",
    path: "/api/v1/simulator/batches/{batch_id}/retry-failed",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
} as const;

// --- Analytics Workbench (13) --------------------------------------------

export const analyticsWorkbenchRoutes = {
  runs: route({
    id: "api.analytics.workbench.runs",
    method: "GET",
    path: "/api/v1/analytics/runs",
    permission: "simulation:read",
  }),
  run: route({
    id: "api.analytics.workbench.run",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}",
    permission: "simulation:read",
  }),
  simulationResult: route({
    id: "api.analytics.workbench.simulation_result",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/simulation-result",
    permission: "simulation:read",
  }),
  report: route({
    id: "api.analytics.workbench.report",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/report",
    permission: "simulation:read",
  }),
  workbenchPayload: route({
    id: "api.analytics.workbench.payload",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/workbench",
    permission: "simulation:read",
  }),
  trades: route({
    id: "api.analytics.workbench.trades",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/trades",
    permission: "simulation:read",
  }),
  trade: route({
    id: "api.analytics.workbench.trade",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/trades/{ticket}",
    permission: "simulation:read",
  }),
  periods: route({
    id: "api.analytics.workbench.periods",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/periods",
    permission: "simulation:read",
  }),
  artifacts: route({
    id: "api.analytics.workbench.artifacts",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/artifacts",
    permission: "simulation:read",
  }),
  replayAnchors: route({
    id: "api.analytics.workbench.replay_anchors",
    method: "GET",
    path: "/api/v1/analytics/runs/{run_id}/replay-anchors",
    permission: "simulation:read",
  }),
  compare: route({
    id: "api.analytics.workbench.compare",
    method: "POST",
    path: "/api/v1/analytics/compare",
    permission: "simulation:read",
  }),
  annotate: route({
    id: "api.analytics.workbench.annotate",
    method: "POST",
    path: "/api/v1/analytics/runs/{run_id}/annotations",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  archive: route({
    id: "api.analytics.workbench.archive",
    method: "POST",
    path: "/api/v1/analytics/runs/{run_id}/archive",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
} as const;

// --- Risk (3) ------------------------------------------------------------

export const riskRoutes = {
  killSwitch: route({
    id: "api.risk.kill_switch",
    method: "GET",
    path: "/api/v1/risk/kill-switch",
    permission: "risk:read",
  }),
  decisions: route({
    id: "api.risk.decisions",
    method: "GET",
    path: "/api/v1/risk/decisions",
    permission: "risk:read",
  }),
  applyKillSwitch: route({
    id: "api.risk.apply_kill_switch",
    method: "POST",
    path: "/api/v1/risk/kill-switch",
    permission: "risk:kill_switch",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Trading session (8) -------------------------------------------------

export const tradingRoutes = {
  executionSessions: route({
    id: "api.trading.execution_sessions",
    method: "GET",
    path: "/api/v1/trading/execution-sessions",
    permission: "trading:read",
  }),
  createExecutionSession: route({
    id: "api.trading.create_execution_session",
    method: "POST",
    path: "/api/v1/trading/execution-sessions",
    permission: "trading:write",
    sideEffect: "write",
  }),
  updateExecutionSession: route({
    id: "api.trading.update_execution_session",
    method: "PATCH",
    path: "/api/v1/trading/execution-sessions/{session_id}",
    permission: "trading:write",
    sideEffect: "write",
  }),
  defaultExecutionSession: route({
    id: "api.trading.default_execution_session",
    method: "POST",
    path: "/api/v1/trading/execution-sessions/{session_id}/default",
    permission: "trading:write",
    sideEffect: "write",
  }),
  startExecutionSession: route({
    id: "api.trading.start_execution_session",
    method: "POST",
    path: "/api/v1/trading/execution-sessions/{session_id}/start",
    permission: "trading:write",
    sideEffect: "write",
  }),
  stopExecutionSession: route({
    id: "api.trading.stop_execution_session",
    method: "POST",
    path: "/api/v1/trading/execution-sessions/{session_id}/stop",
    permission: "trading:write",
    sideEffect: "write",
  }),
  archiveExecutionSession: route({
    id: "api.trading.archive_execution_session",
    method: "DELETE",
    path: "/api/v1/trading/execution-sessions/{session_id}",
    permission: "trading:write",
    sideEffect: "write",
  }),
  executionSessionEvents: route({
    id: "api.trading.execution_session_events",
    method: "GET",
    path: "/api/v1/trading/execution-sessions/{session_id}/events",
    permission: "trading:read",
  }),
  completeExecutionSessionConfiguration: route({
    id: "api.trading.complete_execution_session_configuration",
    method: "POST",
    path: "/api/v1/trading/execution-sessions/{session_id}/complete-configuration",
    permission: "trading:write",
    sideEffect: "write",
  }),
  executionSessionActivity: route({
    id: "api.trading.execution_session_activity",
    method: "GET",
    path: "/api/v1/trading/execution-sessions/{session_id}/activity",
    permission: "trading:read",
    sideEffect: "stream",
    stream: true,
  }),
  accountProfile: route({
    id: "api.trading.account_profile",
    method: "GET",
    path: "/api/v1/trading/account-profile",
    permission: "trading:read",
  }),
  instrumentConstraints: route({
    id: "api.trading.instrument_constraints",
    method: "GET",
    path: "/api/v1/trading/instruments/{symbol}/constraints",
    permission: "trading:read",
  }),
  session: route({
    id: "api.trading.session",
    method: "GET",
    path: "/api/v1/trading/session",
    permission: "trading:read",
  }),
  preflightOrder: route({
    id: "api.trading.preflight_order",
    method: "POST",
    path: "/api/v1/trading/orders/preflight",
    permission: "trading:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  submitOrder: route({
    id: "api.trading.submit_order",
    method: "POST",
    path: "/api/v1/trading/orders",
    permission: "trading:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  cancelOrder: route({
    id: "api.trading.cancel_order",
    method: "DELETE",
    path: "/api/v1/trading/orders/{order_id}",
    permission: "trading:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  closePosition: route({
    id: "api.trading.close_position",
    method: "POST",
    path: "/api/v1/trading/positions/{position_id}/close",
    permission: "trading:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  cancelOrderPreflight: route({
    id: "api.trading.cancel_order_preflight",
    method: "POST",
    path: "/api/v1/trading/orders/{order_id}/preflight",
    permission: "trading:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  cancelAllPreflight: route({
    id: "api.trading.cancel_all_preflight",
    method: "POST",
    path: "/api/v1/trading/orders/cancel-all/preflight",
    permission: "trading:write",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  cancelAllOrders: route({
    id: "api.trading.cancel_all_orders",
    method: "POST",
    path: "/api/v1/trading/orders/cancel-all",
    permission: "trading:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Live what-if sessions (5) -------------------------------------------

export const liveSimulationRoutes = {
  createSession: route({
    id: "api.simulation.live_session_create",
    method: "POST",
    path: "/api/v1/simulation/live-sessions",
    permission: "simulation:run",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  readSession: route({
    id: "api.simulation.live_session_read",
    method: "GET",
    path: "/api/v1/simulation/live-sessions/{session_id}",
    permission: "simulation:read",
  }),
  step: route({
    id: "api.simulation.live_session_step",
    method: "POST",
    path: "/api/v1/simulation/live-sessions/{session_id}/step",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  restore: route({
    id: "api.simulation.live_session_restore",
    method: "POST",
    path: "/api/v1/simulation/live-sessions/{session_id}/restore",
    permission: "simulation:run",
    sideEffect: "write",
    idempotencyRequired: true,
  }),
  rearm: route({
    id: "api.simulation.live_session_rearm",
    method: "POST",
    path: "/api/v1/simulation/live-sessions/{session_id}/rearm",
    permission: "simulation:run",
    sideEffect: "write",
  }),
  branch: route({
    id: "api.simulation.live_session_branch",
    method: "POST",
    path: "/api/v1/simulation/live-sessions/{session_id}/branch",
    permission: "simulation:run",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  closeSession: route({
    id: "api.simulation.live_session_close",
    method: "DELETE",
    path: "/api/v1/simulation/live-sessions/{session_id}",
    permission: "simulation:run",
    sideEffect: "write",
  }),
} as const;

// --- Simulation journal playback sessions (2) ----------------------------

export const simulationSessionRoutes = {
  createSession: route({
    id: "api.simulation.session_create",
    method: "POST",
    path: "/api/v1/simulation/sessions",
    permission: "simulation:read",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  frames: route({
    id: "api.simulation.session_frames",
    method: "GET",
    path: "/api/v1/simulation/sessions/{session_id}/frames",
    permission: "simulation:read",
    sideEffect: "stream",
    stream: true,
  }),
} as const;

// --- Portfolio (10) ------------------------------------------------------

export const portfolioRoutes = {
  registerDefinition: route({
    id: "api.portfolio.definition_register",
    method: "POST",
    path: "/api/v1/portfolio/{portfolio_id}/definitions",
    permission: "portfolio:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  definition: route({
    id: "api.portfolio.definition",
    method: "GET",
    path: "/api/v1/portfolio/{portfolio_id}/definitions/{portfolio_version}",
    permission: "portfolio:read",
  }),
  construct: route({
    id: "api.portfolio.construct",
    method: "POST",
    path: "/api/v1/portfolio/construct",
    permission: "portfolio:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  status: route({
    id: "api.portfolio.status",
    method: "GET",
    path: "/api/v1/portfolio/{portfolio_id}/status",
    permission: "portfolio:read",
  }),
  history: route({
    id: "api.portfolio.history",
    method: "GET",
    path: "/api/v1/portfolio/{portfolio_id}/history",
    permission: "portfolio:read",
  }),
  activate: route({
    id: "api.portfolio.activate",
    method: "POST",
    path: "/api/v1/portfolio/{portfolio_id}/activate",
    permission: "portfolio:activate",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  rollback: route({
    id: "api.portfolio.rollback",
    method: "POST",
    path: "/api/v1/portfolio/{portfolio_id}/rollback",
    permission: "portfolio:activate",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  drift: route({
    id: "api.portfolio.drift",
    method: "POST",
    path: "/api/v1/portfolio/{portfolio_id}/drift",
    permission: "portfolio:read",
  }),
  rebalance: route({
    id: "api.portfolio.rebalance",
    method: "POST",
    path: "/api/v1/portfolio/rebalance",
    permission: "portfolio:rebalance",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  recomputeMeasurement: route({
    id: "api.portfolio.recompute_measurement",
    method: "POST",
    path: "/api/v1/portfolio/measurement/recompute",
    permission: "portfolio:write",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

// --- Optimization (11) ---------------------------------------------------

/** The four true Optimization run routes share permission and idempotency.
 * The analysis routes are reads and are declared individually. */
function optimizationRun<TPath extends string>(
  id: string,
  path: TPath,
): RouteContract<"POST", TPath> {
  return route({
    id,
    method: "POST",
    path,
    permission: "optimization:run",
    sideEffect: "write",
    idempotencyRequired: true,
  });
}

export const optimizationRoutes = {
  parameterSweep: optimizationRun(
    "api.optimization.parameter_sweep",
    "/api/v1/optimization/parameter-sweep",
  ),
  walkForward: optimizationRun(
    "api.optimization.walk_forward",
    "/api/v1/optimization/walk-forward",
  ),
  walkForwardMatrix: optimizationRun(
    "api.optimization.walk_forward_matrix",
    "/api/v1/optimization/walk-forward-matrix",
  ),
  robustness: optimizationRun(
    "api.optimization.robustness",
    "/api/v1/optimization/robustness",
  ),
  compare: route({
    id: "api.optimization.compare",
    method: "POST",
    path: "/api/v1/optimization/compare",
    permission: "optimization:read",
  }),
  stability: route({
    id: "api.optimization.stability",
    method: "POST",
    path: "/api/v1/optimization/stability",
    permission: "optimization:read",
  }),
  overfit: route({
    id: "api.optimization.overfit",
    method: "POST",
    path: "/api/v1/optimization/overfit",
    permission: "optimization:read",
  }),
  rank: route({
    id: "api.optimization.rank",
    method: "POST",
    path: "/api/v1/optimization/rank",
    permission: "optimization:read",
  }),
  robustnessScore: route({
    id: "api.optimization.robustness_score",
    method: "POST",
    path: "/api/v1/optimization/robustness-score",
    permission: "optimization:read",
  }),
  handoff: route({
    id: "api.optimization.handoff",
    method: "POST",
    path: "/api/v1/optimization/handoff",
    permission: "optimization:read",
  }),
  result: route({
    id: "api.optimization.result",
    method: "GET",
    path: "/api/v1/optimization/results/{search_id}",
    permission: "optimization:read",
  }),
} as const;

// --- Agentic operator tier (7) -------------------------------------------

export const agenticRoutes = {
  submitRun: route({
    id: "api.agentic.submit_run",
    method: "POST",
    path: "/api/v1/agentic/runs",
    permission: "agentic:submit",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
  getRun: route({
    id: "api.agentic.inspect_run",
    method: "GET",
    path: "/api/v1/agentic/runs/{run_id}",
    permission: "agentic:read_run",
  }),
  cancelRun: route({
    id: "api.agentic.cancel_run",
    method: "DELETE",
    path: "/api/v1/agentic/runs/{run_id}",
    permission: "agentic:cancel_run",
    sideEffect: "governed_write",
    governed: true,
  }),
  runAudit: route({
    id: "api.agentic.audit_run",
    method: "GET",
    path: "/api/v1/agentic/runs/{run_id}/audit",
    permission: "agentic:read_audit",
  }),
  approveHandoff: route({
    id: "api.agentic.approve_handoff",
    method: "POST",
    path: "/api/v1/agentic/handoffs/approve",
    permission: "agentic:approve_promotion",
    sideEffect: "governed_write",
    governed: true,
  }),
  quarantine: route({
    id: "api.agentic.quarantine_agent",
    method: "POST",
    path: "/api/v1/agentic/incidents/quarantine",
    permission: "agentic:operate",
    sideEffect: "governed_write",
    governed: true,
  }),
  disable: route({
    id: "api.agentic.disable",
    method: "POST",
    path: "/api/v1/agentic/disable",
    permission: "agentic:operate",
    sideEffect: "governed_write",
    governed: true,
  }),
} as const;

// --- Indicators (4) ------------------------------------------------------

export const indicatorsRoutes = {
  catalogue: route({
    id: "api.indicators.list",
    method: "GET",
    path: "/api/v1/indicators",
    permission: "indicators:read",
  }),
  capabilities: route({
    id: "api.indicators.capabilities",
    method: "GET",
    path: "/api/v1/indicators/capabilities",
    permission: "indicators:read",
  }),
  spec: route({
    id: "api.indicators.get_spec",
    method: "GET",
    path: "/api/v1/indicators/{indicator_id}",
    permission: "indicators:read",
  }),
  series: route({
    id: "api.indicators.series",
    method: "GET",
    path: "/api/v1/indicators/{indicator_id}/series",
    permission: "indicators:read",
  }),
} as const;

/**
 * Frozen registry of all 74 route contracts.
 *
 * The count is exported for the drift test so a structural mismatch fails CI.
 */
export const workstationRoutes = {
  read: route({
    id: "api.workstation.read",
    method: "GET",
    path: "/api/v1/workstation",
    permission: "workstation:read",
  }),
  command: route({
    id: "api.workstation.command",
    method: "POST",
    path: "/api/v1/workstation/commands",
    permission: "workstation:command",
    sideEffect: "governed_write",
    governed: true,
    idempotencyRequired: true,
  }),
} as const;

export const ROUTE_CONTRACTS = [
  authRoutes.register,
  authRoutes.login,
  authRoutes.logout,
  authRoutes.me,
  healthRoutes.liveness,
  healthRoutes.readiness,
  settingsRoutes.read,
  settingsRoutes.update,
  settingsRoutes.manifest,
  settingsRoutes.credentials,
  settingsRoutes.updateCredential,
  watchlistsRoutes.list,
  watchlistsRoutes.create,
  watchlistsRoutes.update,
  watchlistsRoutes.delete,
  dataRoutes.symbols,
  dataRoutes.datasets,
  dataRoutes.markets,
  dataRoutes.quotes,
  dataRoutes.bars,
  dataRoutes.capabilities,
  dataRoutes.stream,
  dataRoutes.snapshotStream,
  dataRoutes.depthStream,
  indicatorsRoutes.catalogue,
  indicatorsRoutes.capabilities,
  indicatorsRoutes.spec,
  indicatorsRoutes.series,
  strategiesRoutes.catalogue,
  strategiesRoutes.versions,
  researchRoutes.run,
  researchRoutes.presets,
  researchRoutes.dashboard,
  researchRoutes.createExperiment,
  researchRoutes.experiments,
  researchRoutes.experiment,
  researchRoutes.createRun,
  researchRoutes.runs,
  researchRoutes.compareRuns,
  researchRoutes.runDetail,
  researchRoutes.runReport,
  researchRoutes.runStage,
  researchRoutes.runArtifacts,
  researchRoutes.cancelRun,
  researchRoutes.runEvents,
  researchRoutes.createAutomation,
  researchRoutes.automationBatch,
  researchRoutes.expectancy,
  researchRoutes.createExpectancy,
  researchRoutes.transitionExpectancy,
  researchRoutes.drift,
  researchRoutes.createStressScenario,
  dashboardRoutes.broker,
  dashboardRoutes.equityCurve,
  dashboardRoutes.summary,
  dashboardRoutes.systemResources,
  dashboardRoutes.marketHours,
  dashboardRoutes.forexCalendar,
  operatorRoutes.auditEvents,
  operatorRoutes.events,
  operatorRoutes.approvals,
  metricsRoutes.scrape,
  simulationRoutes.run,
  simulationRoutes.portfolioRun,
  simulationRoutes.result,
  simulatorRoutes.strategies,
  simulatorRoutes.startRun,
  simulatorRoutes.runs,
  simulatorRoutes.run,
  simulatorRoutes.cancelRun,
  simulatorRoutes.runStream,
  simulationWorkbenchRoutes.createLiveSession,
  simulationWorkbenchRoutes.liveSessions,
  simulationWorkbenchRoutes.liveSession,
  simulationWorkbenchRoutes.liveSessionViewport,
  simulationWorkbenchRoutes.stepLiveSession,
  simulationWorkbenchRoutes.seekLiveSession,
  simulationWorkbenchRoutes.submitCommand,
  simulationWorkbenchRoutes.branchLiveSession,
  simulationWorkbenchRoutes.restoreLiveSession,
  simulationWorkbenchRoutes.rearmLiveSession,
  simulationWorkbenchRoutes.finalizeLiveSession,
  simulationWorkbenchRoutes.reproduceLiveSession,
  simulationWorkbenchRoutes.closeLiveSession,
  simulationWorkbenchRoutes.createBatch,
  simulationWorkbenchRoutes.batch,
  simulationWorkbenchRoutes.batchStream,
  simulationWorkbenchRoutes.cancelBatch,
  simulationWorkbenchRoutes.retryFailedBatch,
  analyticsWorkbenchRoutes.runs,
  analyticsWorkbenchRoutes.run,
  analyticsWorkbenchRoutes.simulationResult,
  analyticsWorkbenchRoutes.report,
  analyticsWorkbenchRoutes.workbenchPayload,
  analyticsWorkbenchRoutes.trades,
  analyticsWorkbenchRoutes.trade,
  analyticsWorkbenchRoutes.periods,
  analyticsWorkbenchRoutes.artifacts,
  analyticsWorkbenchRoutes.replayAnchors,
  analyticsWorkbenchRoutes.compare,
  analyticsWorkbenchRoutes.annotate,
  analyticsWorkbenchRoutes.archive,
  riskRoutes.killSwitch,
  riskRoutes.decisions,
  tradingRoutes.accountProfile,
  tradingRoutes.instrumentConstraints,
  tradingRoutes.executionSessions,
  tradingRoutes.createExecutionSession,
  tradingRoutes.updateExecutionSession,
  tradingRoutes.defaultExecutionSession,
  tradingRoutes.startExecutionSession,
  tradingRoutes.stopExecutionSession,
  tradingRoutes.archiveExecutionSession,
  tradingRoutes.executionSessionEvents,
  tradingRoutes.completeExecutionSessionConfiguration,
  tradingRoutes.executionSessionActivity,
  tradingRoutes.session,
  tradingRoutes.preflightOrder,
  tradingRoutes.submitOrder,
  tradingRoutes.cancelOrder,
  tradingRoutes.closePosition,
  tradingRoutes.cancelOrderPreflight,
  tradingRoutes.cancelAllPreflight,
  tradingRoutes.cancelAllOrders,
  dataRoutes.prepareDataset,
  dataRoutes.importDialects,
  dataRoutes.importDataset,
  strategiesRoutes.register,
  strategiesRoutes.updateParameters,
  riskRoutes.applyKillSwitch,
  liveSimulationRoutes.createSession,
  liveSimulationRoutes.readSession,
  liveSimulationRoutes.step,
  liveSimulationRoutes.restore,
  liveSimulationRoutes.rearm,
  liveSimulationRoutes.branch,
  liveSimulationRoutes.closeSession,
  simulationSessionRoutes.createSession,
  simulationSessionRoutes.frames,
  portfolioRoutes.construct,
  portfolioRoutes.registerDefinition,
  portfolioRoutes.definition,
  portfolioRoutes.status,
  portfolioRoutes.history,
  portfolioRoutes.activate,
  portfolioRoutes.rollback,
  portfolioRoutes.drift,
  portfolioRoutes.rebalance,
  portfolioRoutes.recomputeMeasurement,
  optimizationRoutes.parameterSweep,
  optimizationRoutes.walkForward,
  optimizationRoutes.walkForwardMatrix,
  optimizationRoutes.robustness,
  optimizationRoutes.compare,
  optimizationRoutes.stability,
  optimizationRoutes.overfit,
  optimizationRoutes.rank,
  optimizationRoutes.robustnessScore,
  optimizationRoutes.handoff,
  optimizationRoutes.result,
  agenticRoutes.submitRun,
  agenticRoutes.getRun,
  agenticRoutes.cancelRun,
  agenticRoutes.runAudit,
  agenticRoutes.approveHandoff,
  agenticRoutes.quarantine,
  agenticRoutes.disable,
  workstationRoutes.read,
  workstationRoutes.command,
] as const;

/** Exact approved backend-v1 operation count. Drift here must fail CI. */
export const ROUTE_CONTRACT_COUNT = 169;

/** Map of route id -> contract, for fast lookup and drift verification. */
export const ROUTE_CONTRACTS_BY_ID: Readonly<Record<string, RouteContract>> =
  Object.fromEntries(ROUTE_CONTRACTS.map((r) => [r.id, r]));
