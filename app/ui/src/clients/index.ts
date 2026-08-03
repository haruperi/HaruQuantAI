/**
 * Typed frontend client catalog.
 *
 * Aggregates the 9 focused domain clients into one `apiClients` object so
 * callers import a single entry point:
 *
 *   import { apiClients, unwrapData, ApiClientError } from "@/clients";
 *   const { data } = await apiClients.health.liveness();
 *
 * The catalog exposes typed clients only for the 21 registered backend-v1
 * operations. No parallel generic helper exists; every call delegates through
 * the single `request` transport. The drift test asserts this catalog matches
 * the backend route inventory exactly.
 */

// Type-only re-exports.
export type {
  ApiError,
  ApiErrorCode,
  ApiMetadata,
  ApiResponse,
  ApiErrorResponse,
  ApiStatus,
  ApiSuccessResponse,
  RouteSideEffect,
  StreamEvent,
  StreamEventType,
} from "./contracts";
export type { HttpMethod, RouteContract } from "./routes";

export type { QueryValue, RequestOptions } from "./request";

export type { Credentials, Identity, Session } from "./auth";
export type {
  HealthDependencyCheck,
  Liveness,
  Readiness,
} from "./health";
export type { SettingsUpdate, UserSettings } from "./settings";
export type { StreamQuery, SymbolPage, SymbolRow, SymbolsQuery } from "./data";
export { openStream } from "./stream";
export type { StreamTransportOptions } from "./stream";
export type { StrategyCatalogue, StrategyVersion } from "./strategies";
export type { ResearchReport, ResearchRunInput } from "./research";
export type { DashboardSnapshot } from "./dashboards";
export type {
  ApprovalRecord,
  ApprovalRequest,
  AuditEvent,
  AuditEventsPage,
  OperationalEvent,
} from "./operator";

// Value re-exports (used both as stand-alone exports and inside apiClients).
export { isApiSuccessResponse } from "./contracts";
export {
  ROUTE_CONTRACTS,
  ROUTE_CONTRACT_COUNT,
  ROUTE_CONTRACTS_BY_ID,
} from "./routes";
export {
  ApiClientError,
  request,
  resolveBaseUrl,
  unwrapData,
} from "./request";

import { auth } from "./auth";
import { health } from "./health";
import { settings } from "./settings";
import { data } from "./data";
import { strategies } from "./strategies";
import { research } from "./research";
import { dashboards } from "./dashboards";
import { operator } from "./operator";
import { metrics } from "./metrics";

export { auth, health, settings, data, strategies, research, dashboards, operator, metrics };

/**
 * The single typed client catalog.
 *
 * Each property is one focused domain client whose operations map 1:1 to the
 * registered backend route groups. The catalog never invents an operation the
 * backend does not expose.
 */
export const apiClients = {
  auth,
  health,
  settings,
  data,
  strategies,
  research,
  dashboards,
  operator,
  metrics,
} as const;

/** Aggregate type of the catalog, for callers that want to depend on the shape. */
export type ApiClients = typeof apiClients;
