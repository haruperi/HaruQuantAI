/**
 * Simulation Workbench client (18 operations).
 *
 * Exposes live what-if engines, step/seek navigation, manual execution commands,
 * immutable branch creation, recovery-aware state reconstruction, advisory finalization,
 * canonical reproduction requests, and bounded batch execution.
 *
 * Every engine mutation is Simulator-owned. The client only formats inputs and
 * validates server projections; it never calculates balances, margins, or PnLs.
 */

import { z } from "zod";

import type { ApiResponse, StreamEvent } from "./contracts";
import { simulationWorkbenchRoutes } from "./routes";
import { request, type RequestOptions } from "./request";
import { openStream, type StreamTransportOptions } from "./stream";

// --- Enums & Literals ------------------------------------------------------

export const ORIGIN_KINDS = [
  "canonical_job",
  "batch",
  "practice",
  "reproduction",
  "portfolio",
] as const;
export type OriginKind = (typeof ORIGIN_KINDS)[number];

export const CATALOGUE_STATUSES = [
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
] as const;
export type CatalogueStatus = (typeof CATALOGUE_STATUSES)[number];

export const EVIDENCE_CLASSES = [
  "canonical",
  "practice",
  "advisory",
  "playback",
  "fast_research",
] as const;
export type EvidenceClass = (typeof EVIDENCE_CLASSES)[number];

export const ARCHIVE_STATES = ["active", "archived"] as const;
export type ArchiveState = (typeof ARCHIVE_STATES)[number];

export const COMMAND_TYPES = [
  "submit_order",
  "modify_pending_order",
  "cancel_pending_order",
  "close_position",
  "reduce_position",
  "close_all_practice_exposure",
] as const;
export type CommandType = (typeof COMMAND_TYPES)[number];

export const STATE_FRESHNESS_VALUES = [
  "fresh",
  "stale_cursor",
  "recovered",
  "recovery_blocked",
  "out_of_sync",
] as const;
export type StateFreshness = (typeof STATE_FRESHNESS_VALUES)[number];

// --- Schemas ---------------------------------------------------------------

/** Bounded run catalogue summary record. */
export const runCatalogueEntrySchema = z.object({
  contract_version: z.literal("v1").default("v1"),
  schema_id: z
    .literal("api.run_catalogue_entry.v1")
    .default("api.run_catalogue_entry.v1"),
  run_id: z.string(),
  principal_id: z.string(),
  origin_kind: z.enum(ORIGIN_KINDS),
  origin_id: z.string(),
  job_id: z.string().nullable().optional(),
  batch_id: z.string().nullable().optional(),
  session_id: z.string().nullable().optional(),
  strategy_id: z.string(),
  strategy_version: z.string().optional(),
  strategy_label: z.string().optional(),
  symbols: z.array(z.string()),
  timeframe: z.string(),
  measurement_start: z.string(),
  measurement_end: z.string(),
  status: z.enum(CATALOGUE_STATUSES),
  result_ref: z.string().nullable().optional(),
  report_id: z.string().nullable().optional(),
  report_ref: z.string().nullable().optional(),
  artifact_manifest_ref: z.string().nullable().optional(),
  quality_status: z.string().nullable().optional(),
  evidence_class: z.enum(EVIDENCE_CLASSES),
  created_at: z.string(),
  completed_at: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
  alias: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  tags: z.array(z.string()).default([]),
  run_reason: z.string().nullable().optional(),
  archive_state: z.enum(ARCHIVE_STATES).default("active"),
});
export type RunCatalogueEntry = z.infer<typeof runCatalogueEntrySchema>;

/** Dataset metadata attached to a live session. */
export const sessionDatasetSchema = z.object({
  dataset_id: z.string(),
  revision: z.string().optional(),
  content_hash: z.string().optional(),
});
export type SessionDataset = z.infer<typeof sessionDatasetSchema>;

/** Branch metadata attached to a live session. */
export const sessionBranchSchema = z.object({
  parent_session_id: z.string().nullable().optional(),
  divergence_cursor: z.number().nullable().optional(),
  overrides: z.record(z.string(), z.unknown()).default({}),
});
export type SessionBranch = z.infer<typeof sessionBranchSchema>;

/** Account snapshot attached to a live session. */
export const sessionAccountSchema = z.object({
  currency: z.string(),
  balance: z.string().or(z.number()),
  equity: z.string().or(z.number()),
  margin: z.string().or(z.number()).optional(),
  free_margin: z.string().or(z.number()).optional(),
  margin_level: z.string().or(z.number()).nullable().optional(),
});
export type SessionAccount = z.infer<typeof sessionAccountSchema>;

/** Position snapshot inside a live session. */
export const sessionPositionSchema = z.object({
  position_id: z.string(),
  symbol: z.string(),
  side: z.enum(["buy", "sell"]).or(z.string()),
  volume: z.string().or(z.number()),
  open_price: z.string().or(z.number()),
  stop_loss: z.string().or(z.number()).nullable().optional(),
  take_profit: z.string().or(z.number()).nullable().optional(),
  unrealized_pnl: z.string().or(z.number()).optional(),
  margin_allocated: z.string().or(z.number()).optional(),
});
export type SessionPosition = z.infer<typeof sessionPositionSchema>;

/** Pending or working order inside a live session. */
export const sessionOrderSchema = z.object({
  order_id: z.string(),
  symbol: z.string(),
  side: z.enum(["buy", "sell"]).or(z.string()),
  order_type: z.string(),
  volume: z.string().or(z.number()),
  price: z.string().or(z.number()).nullable().optional(),
  stop_loss: z.string().or(z.number()).nullable().optional(),
  take_profit: z.string().or(z.number()).nullable().optional(),
  status: z.string(),
});
export type SessionOrder = z.infer<typeof sessionOrderSchema>;

/** Command receipt returned from a manual order/action submission. */
export const commandReceiptSchema = z.object({
  receipt_id: z.string(),
  command_type: z.enum(COMMAND_TYPES).or(z.string()),
  status: z.enum(["executed", "rejected", "queued", "recovery_blocked"]),
  reason: z.string().nullable().optional(),
  order_id: z.string().nullable().optional(),
  position_id: z.string().nullable().optional(),
  executed_at: z.string().nullable().optional(),
});
export type CommandReceipt = z.infer<typeof commandReceiptSchema>;

/** Recovery health & checksum block. */
export const sessionRecoverySchema = z.object({
  status: z.enum(["healthy", "recovery_blocked", "corrupted", "recovering"]),
  persisted_state_hash: z.string().nullable().optional(),
  integrity_status: z.string().optional(),
  recovery_generation: z.number().default(0),
  recovery_run_id: z.string().nullable().optional(),
  last_checkpoint_at: z.string().nullable().optional(),
});
export type SessionRecovery = z.infer<typeof sessionRecoverySchema>;

/** Full Live Session projection returned by the engine. */
export const liveSessionProjectionSchema = z.object({
  contract_version: z.literal("v1").default("v1"),
  schema_id: z
    .literal("api.live_session_projection.v1")
    .default("api.live_session_projection.v1"),
  session_id: z.string(),
  run_id: z.string().nullable().optional(),
  mode: z.enum(["practice", "challenge", "historical_what_if", "live_practice"]),
  evidence_class: z.enum(EVIDENCE_CLASSES),
  cursor: z.number(),
  timestamp: z.string(),
  tick_count: z.number(),
  completed: z.boolean(),
  dataset: sessionDatasetSchema.optional(),
  branch: sessionBranchSchema.optional(),
  account: sessionAccountSchema.nullable().optional(),
  positions: z.array(sessionPositionSchema).default([]),
  orders: z.array(sessionOrderSchema).default([]),
  receipt: commandReceiptSchema.nullable().optional(),
  pending_intent_count: z.number().default(0),
  recovery: sessionRecoverySchema.optional(),
  exposure_blocked: z.boolean().default(false),
  state_hash: z.string().optional(),
  state_freshness: z.enum(STATE_FRESHNESS_VALUES).default("fresh"),
  permitted_actions: z.array(z.string()).default([]),
});
export type LiveSessionProjection = z.infer<typeof liveSessionProjectionSchema>;

const liveSessionListSchema = z.object({
  sessions: z.array(liveSessionProjectionSchema),
});

/** Single candle/row inside a market viewport. */
export const viewportRowSchema = z.object({
  timestamp: z.string(),
  open: z.string().or(z.number()),
  high: z.string().or(z.number()),
  low: z.string().or(z.number()),
  close: z.string().or(z.number()),
  volume: z.string().or(z.number()),
  forming: z.boolean().default(false),
  markers: z.array(z.record(z.string(), z.unknown())).default([]),
});
export type ViewportRow = z.infer<typeof viewportRowSchema>;

/** Backwards-only market viewport projection. */
export const marketViewportSchema = z.object({
  session_id: z.string(),
  cursor: z.number(),
  timestamp: z.string(),
  before: z.number(),
  after: z.literal(0).default(0),
  rows: z.array(viewportRowSchema),
});
export type MarketViewport = z.infer<typeof marketViewportSchema>;

/** Single item row within a batch. */
export const batchItemSchema = z.object({
  item_id: z.string(),
  batch_id: z.string(),
  job_id: z.string().nullable().optional(),
  symbol: z.string(),
  timeframe: z.string(),
  strategy_id: z.string(),
  parameters: z.record(z.string(), z.unknown()).default({}),
  status: z.enum(CATALOGUE_STATUSES),
  run_id: z.string().nullable().optional(),
  error: z.string().nullable().optional(),
});
export type BatchItem = z.infer<typeof batchItemSchema>;

/** Batch execution projection. */
export const batchProjectionSchema = z.object({
  batch_id: z.string(),
  principal_id: z.string(),
  name: z.string().nullable().optional(),
  status: z.enum(CATALOGUE_STATUSES),
  concurrency: z.number().default(1),
  total_items: z.number(),
  completed_items: z.number().default(0),
  failed_items: z.number().default(0),
  cancelled_items: z.number().default(0),
  created_at: z.string(),
  completed_at: z.string().nullable().optional(),
  items: z.array(batchItemSchema).default([]),
});
export type BatchProjection = z.infer<typeof batchProjectionSchema>;

// --- Request Input Types ---------------------------------------------------

export interface LiveSessionCreateInput {
  run_id?: string;
  dataset_id?: string;
  strategy_id?: string;
  symbol?: string;
  timeframe?: string;
  start?: string;
  end?: string;
  parameters?: Record<string, unknown>;
  mode?: "practice" | "challenge" | "historical_what_if" | "live_practice";
  durable?: boolean;
  initial_balance?: string | number;
  currency?: string;
}

export interface StepInput {
  ticks?: number;
}

export interface SeekInput {
  target_cursor?: number;
  target_timestamp?: string;
}

export interface LiveSessionCommandInput {
  command: CommandType;
  symbol?: string;
  side?: "buy" | "sell";
  order_type?: "market" | "limit" | "stop";
  volume?: string | number;
  price?: string | number;
  stop_loss?: string | number;
  take_profit?: string | number;
  order_id?: string;
  position_id?: string;
}

export interface LiveSessionBranchInput {
  overrides?: Record<string, unknown>;
  name?: string;
}

export interface BatchRunSpec {
  symbol: string;
  timeframe: string;
  strategy_id: string;
  parameters?: Record<string, unknown>;
  start?: string;
  end?: string;
}

export interface BatchCreateInput {
  items: BatchRunSpec[];
  concurrency?: number;
  name?: string;
}

export interface ViewportQuery {
  before?: number;
}

// --- Client Implementation -------------------------------------------------

export const simulationWorkbench = {
  /** Open one live what-if simulation session. */
  async createLiveSession(
    input: LiveSessionCreateInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.createLiveSession, {
      ...options,
      body: input,
      schema: liveSessionProjectionSchema,
    });
  },

  /** List owned active and recent live sessions. */
  async listLiveSessions(
    options?: RequestOptions,
  ): Promise<ApiResponse<{ sessions: LiveSessionProjection[] }>> {
    return request(simulationWorkbenchRoutes.liveSessions, {
      ...options,
      schema: liveSessionListSchema,
    });
  },

  /** Read one owned live session. */
  async getLiveSession(
    sessionId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.liveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      schema: liveSessionProjectionSchema,
    });
  },

  /** Return one backwards-only market viewport at or before the cursor. */
  async getViewport(
    sessionId: string,
    query?: ViewportQuery,
    options?: RequestOptions,
  ): Promise<ApiResponse<MarketViewport>> {
    return request(simulationWorkbenchRoutes.liveSessionViewport, {
      ...options,
      pathParams: { session_id: sessionId },
      query: {
        before: query?.before ?? 300,
        after: 0,
      },
      schema: marketViewportSchema,
    });
  },

  /** Advance one owned session by a bounded tick count. */
  async stepLiveSession(
    sessionId: string,
    input: StepInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.stepLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      body: input,
      schema: liveSessionProjectionSchema,
    });
  },

  /** Move one owned session forward to an absolute cursor. */
  async seekLiveSession(
    sessionId: string,
    input: SeekInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.seekLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      body: input,
      schema: liveSessionProjectionSchema,
    });
  },

  /** Submit one manual command and return receipt plus refreshed state. */
  async submitCommand(
    sessionId: string,
    input: LiveSessionCommandInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<CommandReceipt>> {
    return request(simulationWorkbenchRoutes.submitCommand, {
      ...options,
      pathParams: { session_id: sessionId },
      body: input,
      schema: commandReceiptSchema,
    });
  },

  /** Fork one owned session into an advisory what-if branch. */
  async branchLiveSession(
    sessionId: string,
    input: LiveSessionBranchInput = {},
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.branchLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      body: input,
      schema: liveSessionProjectionSchema,
    });
  },

  /** Reconstruct one durable session and leave it recovery-blocked. */
  async restoreLiveSession(
    sessionId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.restoreLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      schema: liveSessionProjectionSchema,
    });
  },

  /** Explicitly rearm one verified reconstructed session. */
  async rearmLiveSession(
    sessionId: string,
    approved: boolean,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.rearmLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      query: { approved },
      schema: liveSessionProjectionSchema,
    });
  },

  /** Seal one session's advisory journal; finalization stays advisory. */
  async finalizeLiveSession(
    sessionId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.finalizeLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      schema: liveSessionProjectionSchema,
    });
  },

  /** Reproduce one finalized session as a separate canonical job. */
  async reproduceLiveSession(
    sessionId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return request(simulationWorkbenchRoutes.reproduceLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      schema: z.record(z.string(), z.unknown()),
    });
  },

  /** Close one owned live session and release its engine. */
  async closeLiveSession(
    sessionId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<LiveSessionProjection>> {
    return request(simulationWorkbenchRoutes.closeLiveSession, {
      ...options,
      pathParams: { session_id: sessionId },
      schema: liveSessionProjectionSchema,
    });
  },

  /** Execute a bounded batch of canonical runs. */
  async createBatch(
    input: BatchCreateInput,
    options?: RequestOptions,
  ): Promise<ApiResponse<BatchProjection>> {
    return request(simulationWorkbenchRoutes.createBatch, {
      ...options,
      body: input,
      schema: batchProjectionSchema,
    });
  },

  /** Read one owned batch with its ordered item rows. */
  async getBatch(
    batchId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<BatchProjection>> {
    return request(simulationWorkbenchRoutes.batch, {
      ...options,
      pathParams: { batch_id: batchId },
      schema: batchProjectionSchema,
    });
  },

  /** Stream ordered batch progress frames. */
  streamBatch(
    batchId: string,
    options: StreamTransportOptions = {},
  ): AsyncIterable<StreamEvent> {
    return openStream(simulationWorkbenchRoutes.batchStream, {
      ...options,
      pathParams: { batch_id: batchId },
    });
  },

  /** Cancel every non-terminal item of one owned batch. */
  async cancelBatch(
    batchId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<BatchProjection>> {
    return request(simulationWorkbenchRoutes.cancelBatch, {
      ...options,
      pathParams: { batch_id: batchId },
      schema: batchProjectionSchema,
    });
  },

  /** Retry only the failed items of one owned batch. */
  async retryFailedBatch(
    batchId: string,
    options?: RequestOptions,
  ): Promise<ApiResponse<BatchProjection>> {
    return request(simulationWorkbenchRoutes.retryFailedBatch, {
      ...options,
      pathParams: { batch_id: batchId },
      schema: batchProjectionSchema,
    });
  },
};
