/**
 * Analytics Workbench client (13 operations).
 *
 * Exposes run library, canonical Simulation result references, attached Analytics
 * reports, owner-delegated workbench projections, trade drill-downs, periods,
 * artifacts, replay anchors, comparisons, and metadata-only annotations/archiving.
 *
 * Every calculation is Analytics-owned. The client validates shape and never
 * computes ratios, metrics, drawdowns, or scorecards.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { analyticsWorkbenchRoutes } from "./routes";
import { request, type RequestOptions } from "./request";
import { runCatalogueEntrySchema, type RunCatalogueEntry } from "./simulationWorkbench";

// --- Enums & Literals ------------------------------------------------------

export const PERIOD_DIMENSIONS = [
  "year",
  "quarter",
  "month",
  "week",
  "day",
  "day_of_week",
  "hour",
] as const;
export type PeriodDimension = (typeof PERIOD_DIMENSIONS)[number];

export const COMPARISON_METRICS = [
  "summary",
  "returns",
  "risk",
  "ratios",
  "costs",
] as const;
export type ComparisonMetric = (typeof COMPARISON_METRICS)[number];

export const TRADE_SIDES = ["all", "buy", "sell"] as const;
export type TradeSide = (typeof TRADE_SIDES)[number];

export const TRADE_SORTS = ["exit_time_asc", "exit_time_desc"] as const;
export type TradeSort = (typeof TRADE_SORTS)[number];

// --- Schemas ---------------------------------------------------------------

/** One structured section in the Analytics workbench projection. */
export const analyticsWorkbenchSectionSchema = z.object({
  key: z.string(),
  status: z.enum(["completed", "unavailable"]),
  unit: z.string().nullable().optional(),
  source_context: z.string().default("all"),
  sample_count: z.number().default(0),
  reason: z.string().nullable().optional(),
  truncated: z.boolean().default(false),
  total_count: z.number().default(0),
  items: z.array(z.record(z.string(), z.unknown())).default([]),
});
export type AnalyticsWorkbenchSection = z.infer<
  typeof analyticsWorkbenchSectionSchema
>;

/** Full run-specific workbench payload projected by Analytics. */
export const analyticsWorkbenchPayloadSchema = z.object({
  contract_version: z.literal("v1").default("v1"),
  schema_id: z
    .literal("analytics.workbench_payload.v1")
    .default("analytics.workbench_payload.v1"),
  payload_id: z.string(),
  report_id: z.string(),
  generated_at: z.string(),
  summary: analyticsWorkbenchSectionSchema,
  equity_curve: analyticsWorkbenchSectionSchema,
  drawdown_curve: analyticsWorkbenchSectionSchema,
  returns_series: analyticsWorkbenchSectionSchema,
  vami: analyticsWorkbenchSectionSchema,
  monthly_returns: analyticsWorkbenchSectionSchema,
  period_tables: analyticsWorkbenchSectionSchema,
  trade_calendar: analyticsWorkbenchSectionSchema,
  streaks: analyticsWorkbenchSectionSchema,
  distribution: analyticsWorkbenchSectionSchema,
  histogram: analyticsWorkbenchSectionSchema,
  outliers: analyticsWorkbenchSectionSchema,
  excursions: analyticsWorkbenchSectionSchema,
  duration: analyticsWorkbenchSectionSchema,
  grouped_performance: analyticsWorkbenchSectionSchema,
  benchmark: analyticsWorkbenchSectionSchema,
  costs: analyticsWorkbenchSectionSchema,
  warnings: z.array(z.record(z.string(), z.unknown())).default([]),
  quality_flags: z.array(z.record(z.string(), z.unknown())).default([]),
  lineage: z.record(z.string(), z.unknown()).default({}),
  truncation: z.array(z.record(z.string(), z.unknown())).default([]),
  non_binding: z.literal(true).default(true),
});
export type AnalyticsWorkbenchPayload = z.infer<
  typeof analyticsWorkbenchPayloadSchema
>;

/** One closed trade record from the canonical Simulation ledger. */
export const closedTradeRecordSchema = z.object({
  ticket: z.string().or(z.number()).transform(String),
  symbol: z.string().optional(),
  side: z.enum(["buy", "sell"]).or(z.string()),
  volume: z.string().or(z.number()),
  entry_time: z.string(),
  entry_price: z.string().or(z.number()),
  exit_time: z.string(),
  exit_price: z.string().or(z.number()),
  pnl: z.string().or(z.number()).optional(),
  pnl_percent: z.string().or(z.number()).optional(),
  return_pct: z.string().or(z.number()).optional(),
  commission: z.string().or(z.number()).optional(),
  swap: z.string().or(z.number()).optional(),
  reason: z.string().nullable().optional(),
  mae: z.string().or(z.number()).nullable().optional(),
  mfe: z.string().or(z.number()).nullable().optional(),
  bars_held: z.number().nullable().optional(),
  duration_seconds: z.number().nullable().optional(),
});
export type ClosedTradeRecord = z.infer<typeof closedTradeRecordSchema>;

/** Paginated trade page response. */
export const tradePageSchema = z.object({
  run_id: z.string(),
  page: z.number(),
  page_size: z.number(),
  total_trades: z.number(),
  total_pages: z.number(),
  trades: z.array(closedTradeRecordSchema),
});
export type TradePage = z.infer<typeof tradePageSchema>;

/** List runs response. */
export const runCataloguePageSchema = z.object({
  runs: z.array(runCatalogueEntrySchema),
});
export type RunCataloguePage = z.infer<typeof runCataloguePageSchema>;

/** Periods response. */
export const periodTablePayloadSchema = z.object({
  run_id: z.string(),
  dimension: z.string(),
  context: z.string(),
  section: analyticsWorkbenchSectionSchema.nullable().optional(),
});
export type PeriodTablePayload = z.infer<typeof periodTablePayloadSchema>;

/** Artifact item. */
export const artifactItemSchema = z.object({
  kind: z.string(),
  ref: z.string(),
});
export type ArtifactItem = z.infer<typeof artifactItemSchema>;

/** Artifacts inventory response. */
export const artifactInventorySchema = z.object({
  run_id: z.string(),
  artifacts: z.array(artifactItemSchema),
});
export type ArtifactInventory = z.infer<typeof artifactInventorySchema>;

/** Replay anchor item. */
export const replayAnchorItemSchema = z.object({
  ticket: z.string(),
  exit_time: z.string().nullable().optional(),
});
export type ReplayAnchorItem = z.infer<typeof replayAnchorItemSchema>;

/** Replay anchors response. */
export const replayAnchorsPayloadSchema = z.object({
  run_id: z.string(),
  anchors: z.array(replayAnchorItemSchema),
});
export type ReplayAnchorsPayload = z.infer<typeof replayAnchorsPayloadSchema>;

/** Comparison evidence response. */
export const comparisonEvidenceSchema = z.object({
  contract_version: z.string().default("v1"),
  schema_id: z.string().default("analytics.comparison_evidence.v1"),
  comparison_id: z.string().optional(),
  metric: z.string(),
  runs: z.array(z.record(z.string(), z.unknown())),
});
export type ComparisonEvidence = z.infer<typeof comparisonEvidenceSchema>;

// --- Request Input Types ---------------------------------------------------

export interface AnalyticsTradesQuery {
  page?: number;
  page_size?: number;
  sort?: TradeSort;
  side?: TradeSide;
  symbol?: string;
}

export interface AnalyticsPeriodsQuery {
  dimension?: PeriodDimension;
  context?: "all" | "long" | "short";
}

export interface AnalyticsCompareInput {
  run_ids: string[];
  metric?: ComparisonMetric;
}

export interface AnalyticsAnnotationInput {
  name?: string | null;
  alias?: string | null;
  description?: string | null;
  tags?: string[];
  run_reason?: string | null;
}

export interface AnalyticsArchiveInput {
  archive_state: "active" | "archived";
}

// --- Client Implementation -------------------------------------------------

export const analyticsWorkbench = {
  /** List the caller's catalogue runs, newest first. */
  async listRuns(
    query?: { page?: number; page_size?: number },
    options?: RequestOptions,
  ): Promise<ApiResponse<RunCataloguePage>> {
    return request(analyticsWorkbenchRoutes.runs, {
      ...options,
      query: {
        page: query?.page ?? 1,
        page_size: query?.page_size ?? 50,
      },
      schema: runCataloguePageSchema,
    });
  },

  /** Read one owned catalogue run. */
  async getRun(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<RunCatalogueEntry>> {
    return request(analyticsWorkbenchRoutes.run, {
      ...options,
      pathParams: { run_id: runId },
      schema: runCatalogueEntrySchema,
    });
  },

  /** Read the canonical Simulation result reference for one run. */
  async getSimulationResult(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return request(analyticsWorkbenchRoutes.simulationResult, {
      ...options,
      pathParams: { run_id: runId },
      schema: z.record(z.string(), z.unknown()),
    });
  },

  /** Read the attached immutable Analytics report artifact. */
  async getReport(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return request(analyticsWorkbenchRoutes.report, {
      ...options,
      pathParams: { run_id: runId },
      schema: z.record(z.string(), z.unknown()),
    });
  },

  /** Read the Analytics-delegated workbench projection for one run. */
  async getWorkbenchPayload(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<AnalyticsWorkbenchPayload>> {
    return request(analyticsWorkbenchRoutes.workbenchPayload, {
      ...options,
      pathParams: { run_id: runId },
      schema: analyticsWorkbenchPayloadSchema,
    });
  },

  /** Paginate the canonical Simulation trade ledger. */
  async getTrades(
    runId: string,
    query?: AnalyticsTradesQuery,
    options?: RequestOptions,
  ): Promise<ApiResponse<TradePage>> {
    return request(analyticsWorkbenchRoutes.trades, {
      ...options,
      pathParams: { run_id: runId },
      query: {
        page: query?.page ?? 1,
        page_size: query?.page_size ?? 50,
        sort: query?.sort ?? "exit_time_desc",
        side: query?.side ?? "all",
        ...(query?.symbol ? { symbol: query.symbol } : {}),
      },
      schema: tradePageSchema,
    });
  },

  /** Read one trade from the canonical Simulation result. */
  async getTrade(
    runId: string,
    ticket: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<ClosedTradeRecord>> {
    return request(analyticsWorkbenchRoutes.trade, {
      ...options,
      pathParams: { run_id: runId, ticket },
      schema: closedTradeRecordSchema,
    });
  },

  /** Read the workbench period-table section with exact query dimensions. */
  async getPeriods(
    runId: string,
    query?: AnalyticsPeriodsQuery,
    options?: RequestOptions,
  ): Promise<ApiResponse<PeriodTablePayload>> {
    return request(analyticsWorkbenchRoutes.periods, {
      ...options,
      pathParams: { run_id: runId },
      query: {
        dimension: query?.dimension ?? "month",
        context: query?.context ?? "all",
      },
      schema: periodTablePayloadSchema,
    });
  },

  /** List the immutable artifact references recorded for one run. */
  async getArtifacts(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<ArtifactInventory>> {
    return request(analyticsWorkbenchRoutes.artifacts, {
      ...options,
      pathParams: { run_id: runId },
      schema: artifactInventorySchema,
    });
  },

  /** List replay anchors for one run's immutable journal. */
  async getReplayAnchors(
    runId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<ReplayAnchorsPayload>> {
    return request(analyticsWorkbenchRoutes.replayAnchors, {
      ...options,
      pathParams: { run_id: runId },
      schema: replayAnchorsPayloadSchema,
    });
  },

  /** Delegate one multi-run comparison to Analytics. */
  async compareRuns(
    input: AnalyticsCompareInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<ComparisonEvidence>> {
    return request(analyticsWorkbenchRoutes.compare, {
      ...options,
      body: input,
      schema: comparisonEvidenceSchema,
    });
  },

  /** Apply metadata-only annotations to one owned run. */
  async annotateRun(
    runId: string,
    input: AnalyticsAnnotationInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<RunCatalogueEntry>> {
    return request(analyticsWorkbenchRoutes.annotate, {
      ...options,
      pathParams: { run_id: runId },
      body: input,
      schema: runCatalogueEntrySchema,
    });
  },

  /** Change one run's archive state; evidence is never deleted. */
  async archiveRun(
    runId: string,
    input: AnalyticsArchiveInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<RunCatalogueEntry>> {
    return request(analyticsWorkbenchRoutes.archive, {
      ...options,
      pathParams: { run_id: runId },
      body: input,
      schema: runCatalogueEntrySchema,
    });
  },
};
