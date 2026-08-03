/**
 * Frozen typed route contracts for the 23 registered backend-v1 operations.
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
  TPath extends string = string
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
    authRequired: config.authRequired ?? (config.permission !== undefined),
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

// --- Settings (2) --------------------------------------------------------

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
} as const;

// --- Data / symbol discovery + market stream (2) -------------------------

export const dataRoutes = {
  symbols: route({
    id: "api.data.symbols",
    method: "GET",
    path: "/api/v1/data/symbols",
    permission: "data:read",
    paginated: true,
  }),
  stream: route({
    id: "api.data.stream",
    method: "GET",
    path: "/api/v1/data/stream",
    permission: "data:read",
    sideEffect: "stream",
    stream: true,
  }),
} as const;

// --- Strategies (2) ------------------------------------------------------

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
} as const;

// --- Research (1) --------------------------------------------------------

export const researchRoutes = {
  run: route({
    id: "api.research.run",
    method: "POST",
    path: "/api/v1/research/run",
    permission: "research:run",
    sideEffect: "read",
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

/**
 * Frozen registry of all 23 route contracts.
 *
 * The count is exported for the drift test so a structural mismatch fails CI.
 */
export const ROUTE_CONTRACTS = [
  authRoutes.register,
  authRoutes.login,
  authRoutes.logout,
  authRoutes.me,
  healthRoutes.liveness,
  healthRoutes.readiness,
  settingsRoutes.read,
  settingsRoutes.update,
  dataRoutes.symbols,
  dataRoutes.stream,
  strategiesRoutes.catalogue,
  strategiesRoutes.versions,
  researchRoutes.run,
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
] as const;

/** Exact approved backend-v1 operation count. Drift here must fail CI. */
export const ROUTE_CONTRACT_COUNT = 23;

/** Map of route id -> contract, for fast lookup and drift verification. */
export const ROUTE_CONTRACTS_BY_ID: Readonly<Record<string, RouteContract>> =
  Object.fromEntries(ROUTE_CONTRACTS.map((r) => [r.id, r]));
