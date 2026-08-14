/**
 * Typed frontend client catalog.
 *
 * Aggregates the 18 focused domain clients into one `apiClients` object so
 * callers import a single entry point:
 *
 *   import { apiClients, unwrapData, ApiClientError } from "@/clients";
 *   const { data } = await apiClients.health.liveness();
 *
 * The catalog exposes typed clients only for the 91 registered backend-v1
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
export type {
  CredentialStatus,
  SettingsUpdate,
  SystemSettingDefinition,
  SystemSettings,
  UserSettings,
} from "./settings";
export type { Watchlist, WatchlistItem, WatchlistUpdate } from "./watchlists";
export type {
  Bar,
  BarSeries,
  BarTimeframe,
  BarsQuery,
  DataCapabilities,
  DataCapability,
  MarketDirectory as MarketDirectoryPage,
  MarketRow,
  MarketsQuery,
  QuotesParams,
  StreamQuery,
  SnapshotPayload,
  SnapshotQuote,
  SymbolPage,
  SymbolRow,
  SymbolsQuery,
} from "./data";
export { BAR_TIMEFRAMES } from "./data";
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
export type { LiveSession } from "./liveSimulation";
export type {
  PortfolioSimulationResult,
  SimulationResult,
  SimulationRunInput,
} from "./simulation";
export type {
  KillSwitchQuery,
  KillSwitchState,
  RiskDecision,
  RiskDecisionsQuery,
} from "./risk";
export type {
  ExecutionReceipt,
  SubmitOrderInput,
  TradingMutationInput,
  TradingProjection,
} from "./trading";
export type { PortfolioDefinitionBody, PortfolioRecord } from "./portfolio";

export type {
  CapabilityMatrix,
  IndicatorCapability,
  IndicatorCatalogue,
  IndicatorSeries,
  IndicatorSeriesQuery,
  IndicatorSpec,
} from "./indicators";

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
import { watchlists } from "./watchlists";
import { data } from "./data";
import { indicators } from "./indicators";
import { strategies } from "./strategies";
import { research } from "./research";
import { dashboards } from "./dashboards";
import { operator } from "./operator";
import { metrics } from "./metrics";
import { simulation } from "./simulation";
import { risk } from "./risk";
import { trading } from "./trading";
import { portfolio } from "./portfolio";
import { optimization } from "./optimization";
export type { OptimizationRecord } from "./optimization";
import { agentic } from "./agentic";
import { simulationSessions } from "./simulationSessions";
import { liveSimulation } from "./liveSimulation";
import { workstation } from "./workstation";

export {
  auth,
  health,
  settings,
  watchlists,
  data,
  indicators,
  strategies,
  research,
  dashboards,
  operator,
  metrics,
  simulation,
  simulationSessions,
  liveSimulation,
  risk,
  trading,
  portfolio,
  optimization,
  agentic,
  workstation,
};

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
  watchlists,
  data,
  indicators,
  strategies,
  research,
  dashboards,
  operator,
  metrics,
  simulation,
  simulationSessions,
  liveSimulation,
  risk,
  trading,
  portfolio,
  optimization,
  agentic,
  workstation,
} as const;

/** Aggregate type of the catalog, for callers that want to depend on the shape. */
export type ApiClients = typeof apiClients;
