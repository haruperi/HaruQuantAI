/**
 * Typed frontend client catalog.
 *
 * Aggregates the focused domain clients into one `apiClients` object so
 * callers import a single entry point:
 *
 *   import { apiClients, unwrapData, ApiClientError } from "@/clients";
 *   const { data } = await apiClients.health.liveness();
 *
 * The catalog exposes typed clients only for the registered backend-v1
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
  DatasetSummary,
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
export type {
  BarPreview,
  DatasetIdentity,
  EffectiveConfiguration,
  Overview,
  Provenance,
  Readiness as ResearchReadiness,
  ResearchArtifact,
  ResearchArtifactList,
  ResearchAutomationBatch,
  ResearchAutomationInput,
  ResearchComparison,
  ResearchComparisonEntry,
  ResearchDashboard,
  ResearchDatasetSelection,
  ResearchDrift,
  ResearchExpectancy,
  ResearchExpectancyTransition,
  ResearchExpectancyTransitionInput,
  ResearchExperimentCreateInput,
  ResearchExperimentDetail,
  ResearchExperimentSummary,
  ResearchPreset,
  ResearchPresetCatalogue,
  ResearchReport,
  ResearchRunCreateInput,
  ResearchRunDetail,
  ResearchRunInput,
  ResearchRunReport,
  ResearchRunStatus,
  ResearchRunSummary,
  ResearchStageView,
  ResearchWarning,
  Scorecard,
  StageState,
  StageView,
} from "./research";
export { RESEARCH_RUN_STATUSES, STAGE_STATES, STAGE_VIEWS } from "./research";
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
  BacktestRun,
  BacktestRunInput,
  BacktestStrategy,
  BacktestStrategyCatalogue,
  RunProgressEvent,
  RunReport,
  RunStatus,
  StrategyParameter,
} from "./simulator";
export { RUN_STATUSES } from "./simulator";
export type {
  KillSwitchQuery,
  KillSwitchState,
  RiskDecision,
  RiskDecisionsQuery,
} from "./risk";
export type {
  CancelAllPreflightInput,
  CancelOrderPreflightInput,
  ExecutionReceipt,
  ExecutionSession,
  ExecutionSessionCreateInput,
  ExecutionSessionEvent,
  OrderPreflightInput,
  Position,
  RiskPreflightResponse,
  SubmitOrderInput,
  TradingMutationInput,
  TradingAccountProfile,
  TradingInstrumentConstraints,
  TradingProjection,
  WorkingOrder,
} from "./trading";
export { listPositions, listWorkingOrders } from "./trading";
export type { PortfolioDefinitionBody, PortfolioRecord } from "./portfolio";

export type {
  CapabilityMatrix,
  IndicatorCapability,
  IndicatorCatalogue,
  IndicatorSeries,
  IndicatorSeriesQuery,
  IndicatorSpec,
} from "./indicators";

export type {
  ArchiveState,
  BatchCreateInput,
  BatchItem,
  BatchProjection,
  BatchRunSpec,
  CatalogueStatus,
  CommandReceipt,
  CommandType,
  EvidenceClass,
  LiveSessionBranchInput,
  LiveSessionCommandInput,
  LiveSessionCreateInput,
  LiveSessionProjection,
  MarketViewport,
  OriginKind,
  RunCatalogueEntry,
  SessionAccount,
  SessionBranch,
  SessionDataset,
  SessionOrder,
  SessionPosition,
  SessionRecovery,
  StateFreshness,
  ViewportRow,
} from "./simulationWorkbench";
export {
  ARCHIVE_STATES,
  CATALOGUE_STATUSES,
  COMMAND_TYPES,
  EVIDENCE_CLASSES,
  ORIGIN_KINDS,
  STATE_FRESHNESS_VALUES,
  batchProjectionSchema,
  commandReceiptSchema,
  liveSessionProjectionSchema,
  marketViewportSchema,
  runCatalogueEntrySchema,
} from "./simulationWorkbench";

export type {
  JournalFrame,
  SimulationSession,
} from "./simulationSessions";
export {
  journalFrameSchema,
  simulationSessionSchema,
} from "./simulationSessions";

export type {
  AnalyticsAnnotationInput,
  AnalyticsArchiveInput,
  AnalyticsCompareInput,
  AnalyticsPeriodsQuery,
  AnalyticsTradesQuery,
  AnalyticsWorkbenchPayload,
  AnalyticsWorkbenchSection,
  ArtifactInventory,
  ClosedTradeRecord,
  ComparisonEvidence,
  ComparisonMetric,
  PeriodDimension,
  PeriodTablePayload,
  ReplayAnchorsPayload,
  RunCataloguePage,
  TradePage,
  TradeSide,
  TradeSort,
} from "./analyticsWorkbench";
export {
  COMPARISON_METRICS,
  PERIOD_DIMENSIONS,
  TRADE_SIDES,
  TRADE_SORTS,
  analyticsWorkbenchPayloadSchema,
  analyticsWorkbenchSectionSchema,
  artifactInventorySchema,
  closedTradeRecordSchema,
  comparisonEvidenceSchema,
  periodTablePayloadSchema,
  replayAnchorsPayloadSchema,
  tradePageSchema,
} from "./analyticsWorkbench";

// Value re-exports (used both as stand-alone exports and inside apiClients).
export { isApiSuccessResponse } from "./contracts";
export {
  ROUTE_CONTRACTS,
  ROUTE_CONTRACT_COUNT,
  ROUTE_CONTRACTS_BY_ID,
  analyticsWorkbenchRoutes,
  simulationWorkbenchRoutes,
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
import { simulator } from "./simulator";
import { simulationWorkbench } from "./simulationWorkbench";
import { analyticsWorkbench } from "./analyticsWorkbench";
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
  simulator,
  simulationWorkbench,
  analyticsWorkbench,
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
  simulator,
  simulationWorkbench,
  analyticsWorkbench,
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
