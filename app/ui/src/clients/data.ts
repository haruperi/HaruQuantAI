/**
 * Data client for symbol discovery, the market stream, governed dataset
 * preparation, and external import (6 operations).
 *
 * The Data domain owns the exact row shape; the gateway returns it opaquely.
 * The client validates a minimal structural contract (opaque rows) and leaves
 * field-level interpretation to consumers.
 */

import { z } from "zod";

import type { ApiResponse, StreamEvent } from "./contracts";
import { dataRoutes } from "./routes";
import { request, type RequestOptions, type QueryValue } from "./request";
import { openStream, type StreamTransportOptions } from "./stream";

/** One symbol row. Data-owned; field set may grow, so rows are open records. */
export const symbolRowSchema = z.record(z.string(), z.unknown());
export type SymbolRow = z.infer<typeof symbolRowSchema>;

/**
 * Symbol discovery page.
 *
 * Data returns provider-native symbol *names* here, not rows — this route is
 * the cheap read (no quote or OHLC evidence), which is what makes walking the
 * whole broker universe affordable. `next_cursor` is opaque and provider-owned;
 * pass it back verbatim to get the following page.
 */
export const symbolPageSchema = z.object({
  source_id: z.string().min(1),
  items: z.array(z.string()),
  limit: z.number().int().min(1),
  next_cursor: z.string().nullable().nullish(),
  revision: z.string().min(1),
  request_id: z.string().min(1),
});
export type SymbolPage = z.infer<typeof symbolPageSchema>;

/** One bounded Data feature summary. */
export const dataCapabilitySchema = z.object({
  feature_id: z.string(),
  name: z.string(),
  summary: z.string(),
  availability: z.literal("available"),
});
export type DataCapability = z.infer<typeof dataCapabilitySchema>;

/** Complete Data feature catalogue returned by the authenticated gateway. */
export const dataCapabilitiesSchema = z.object({
  capabilities: z.array(dataCapabilitySchema).length(14),
});
export type DataCapabilities = z.infer<typeof dataCapabilitiesSchema>;

/** List the complete Data capability surface (requires `data:read`). */
export function capabilities(
  options?: RequestOptions
): Promise<ApiResponse<DataCapabilities>> {
  return request<DataCapabilities>(dataRoutes.capabilities, {
    schema: dataCapabilitiesSchema,
    ...options,
  });
}

/** Query parameters for symbol discovery. */
export interface SymbolsQuery {
  source_id?: string;
  query?: string;
  cursor?: string;
  /** Page size 1..200; defaults to the backend `API_DEFAULT_PAGE_SIZE`. */
  limit?: number;
}

/** Discover symbols (requires `data:read`). */
export function symbols(
  params: SymbolsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<SymbolPage>> {
  const query: Record<string, QueryValue> = {};
  if (params.source_id !== undefined) query.source_id = params.source_id;
  if (params.query !== undefined) query.query = params.query;
  if (params.cursor !== undefined) query.cursor = params.cursor;
  if (params.limit !== undefined) query.limit = params.limit;
  return request<SymbolPage>(dataRoutes.symbols, {
    schema: symbolPageSchema,
    query,
    ...options,
  });
}

/** One categorized tradable-symbol row from the market directory. */
export const marketRowSchema = z.object({
  symbol: z.string().min(1),
  name: z.string().min(1),
  asset_class: z.string().min(1),
  source_id: z.string().min(1),
  digits: z.number().int().nullable(),
  last: z.number().nullable(),
  bid: z.number().nullable(),
  ask: z.number().nullable(),
  spread: z.number().nullable(),
  volume: z.number().nullable(),
  open: z.number().nullable(),
  high: z.number().nullable(),
  low: z.number().nullable(),
  close: z.number().nullable(),
  change: z.number().nullable(),
  change_percent: z.number().nullable(),
  /**
   * API-composed technical overlays (Data's D1 bars plus Indicators'
   * formulas). Present only when the request opted in via
   * `includeTechnicals`; absent (not merely null) otherwise.
   */
  volatility: z.number().nullable().optional(),
  adr: z.number().nullable().optional(),
  range_percent_of_adr: z.number().nullable().optional(),
  change_pips: z.number().nullable().optional(),
});
export type MarketRow = z.infer<typeof marketRowSchema>;

/** Categorized market-directory page (Data-owned row shape). */
export const marketDirectorySchema = z.object({
  source_id: z.string().min(1),
  rows: z.array(marketRowSchema),
  limit: z.number().int().min(1),
  next_cursor: z.string().nullable().nullish(),
  revision: z.string().min(1),
  generated_at: z.string().min(1),
  request_id: z.string().min(1),
});
export type MarketDirectory = z.infer<typeof marketDirectorySchema>;

/** Query parameters for the categorized market directory. */
export interface MarketsQuery {
  /** Defaults to the configured runtime broker when omitted. */
  source_id?: string;
  query?: string;
  cursor?: string;
  /** Page size 1..200; defaults to the backend `API_DEFAULT_PAGE_SIZE`. */
  limit?: number;
  /** Compose each row with the API-owned Volatility/ADR/Range overlay. */
  includeTechnicals?: boolean;
}

/** Read the categorized market directory (requires `data:read`). */
export function markets(
  params: MarketsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<MarketDirectory>> {
  const query: Record<string, QueryValue> = {};
  if (params.source_id !== undefined) query.source_id = params.source_id;
  if (params.query !== undefined) query.query = params.query;
  if (params.cursor !== undefined) query.cursor = params.cursor;
  if (params.limit !== undefined) query.limit = params.limit;
  if (params.includeTechnicals) query.include_technicals = "true";
  return request<MarketDirectory>(dataRoutes.markets, {
    schema: marketDirectorySchema,
    query,
    ...options,
  });
}

/** Optional parameters for {@link quotes}. */
export interface QuotesParams {
  /** Defaults to the configured runtime broker when omitted. */
  sourceId?: string;
  /**
   * Compose each row with the API-owned Volatility/ADR/Range overlay.
   * Opt-in: it costs a historical fetch and two indicator calculations per
   * symbol, well above a plain quote.
   */
  includeTechnicals?: boolean;
}

/**
 * Read categorized quotes for an explicit symbol list (requires `data:read`).
 *
 * Unlike `markets`, this never walks the full broker catalog — it enriches
 * exactly the named symbols (e.g. one watchlist's contents), so cost scales
 * with the list size, not the broker's universe.
 */
export function quotes(
  symbols: string[],
  params: QuotesParams = {},
  options?: RequestOptions
): Promise<ApiResponse<MarketDirectory>> {
  const query: Record<string, QueryValue> = { symbols: symbols.join(",") };
  if (params.sourceId !== undefined) query.source_id = params.sourceId;
  if (params.includeTechnicals) query.include_technicals = "true";
  return request<MarketDirectory>(dataRoutes.quotes, {
    schema: marketDirectorySchema,
    query,
    ...options,
  });
}

/**
 * Canonical timeframe keys Data can serve.
 *
 * Restated from the backend's accepted query domain so the UI never offers a
 * timeframe the broker has no bars for.
 */
export const BAR_TIMEFRAMES = [
  "M1",
  "M5",
  "M15",
  "M30",
  "H1",
  "H4",
  "D1",
  "W1",
  "MN1",
] as const;
export type BarTimeframe = (typeof BAR_TIMEFRAMES)[number];

/** One broker-owned OHLCV bar. `time` is an ISO-8601 UTC bar-open instant. */
export const barSchema = z.object({
  time: z.string().nullable(),
  open: z.number().nullable(),
  high: z.number().nullable(),
  low: z.number().nullable(),
  close: z.number().nullable(),
  volume: z.number().nullable(),
});
export type Bar = z.infer<typeof barSchema>;

/** Ordered bar history for one symbol and timeframe (Data-owned values). */
export const barSeriesSchema = z.object({
  source_id: z.string().min(1),
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  bars: z.array(barSchema),
  count: z.number().int().min(0),
  start: z.string().nullable(),
  end: z.string().nullable(),
  cache_status: z.string(),
  request_id: z.string().min(1),
});
export type BarSeries = z.infer<typeof barSeriesSchema>;

/** Query parameters for {@link bars}. */
export interface BarsQuery {
  symbol: string;
  /** Canonical timeframe key; defaults to `H1` at the backend. */
  timeframe?: BarTimeframe;
  /** Most-recent bar count, 1..1,000,000; defaults to 500 at the backend. */
  limit?: number;
  /** Defaults to the configured runtime broker when omitted. */
  sourceId?: string;
  /** Optional ISO-8601 inclusive window start. */
  start?: string;
  /** Optional ISO-8601 inclusive window end. */
  end?: string;
}

/**
 * Read broker bar history for one symbol (requires `data:read`).
 *
 * The series is whatever the runtime broker holds — an unavailable provider
 * returns an error envelope rather than a generated fallback, so a chart never
 * renders invented history as real.
 */
export function bars(
  params: BarsQuery,
  options?: RequestOptions
): Promise<ApiResponse<BarSeries>> {
  const query: Record<string, QueryValue> = { symbol: params.symbol };
  if (params.timeframe !== undefined) query.timeframe = params.timeframe;
  if (params.limit !== undefined) query.limit = params.limit;
  if (params.sourceId !== undefined) query.source_id = params.sourceId;
  if (params.start !== undefined) query.start = params.start;
  if (params.end !== undefined) query.end = params.end;
  return request<BarSeries>(dataRoutes.bars, {
    schema: barSeriesSchema,
    query,
    ...options,
  });
}

/** Query parameters for the SSE market stream. */
export interface StreamQuery {
  symbol: string;
  mode: "ticks";
  timeframe: string;
  source_id?: "mt5";
}

/** One latest-value quote received from the MT5 bridge EA. */
export interface SnapshotQuote {
  symbol: string;
  time: string;
  bid: string;
  ask: string;
  last: string | null;
  spread: string;
  digits: number;
}

/** Validated shape carried inside a snapshot stream event payload. */
export interface SnapshotPayload {
  quotes: SnapshotQuote[];
  stale: boolean;
  gap: number;
  kind: "snapshot";
}

/**
 * Open the authenticated SSE market stream and yield validated events.
 *
 * Delegates to the low-level SSE transport. Higher-level gap/reconnect
 * handling is provided by `context/streams.ts::consumeStream`.
 */
export function stream(
  params: StreamQuery,
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  const query: Record<string, QueryValue> = {
    symbol: params.symbol,
    mode: params.mode,
    timeframe: params.timeframe,
  };
  if (params.source_id !== undefined) query.source_id = params.source_id;
  return openStream(dataRoutes.stream, { query, ...options });
}

/** Open one authenticated multi-symbol MT5 snapshot stream. */
export function snapshotStream(
  symbols: string[],
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  if (symbols.length === 0 || symbols.length > 200) {
    throw new Error("snapshot stream requires 1..200 symbols");
  }
  return openStream(dataRoutes.snapshotStream, {
    query: { symbols: symbols.join(",") },
    ...options,
  });
}

/** Open one authenticated multi-symbol MT5 Depth-of-Market stream. */
export function depthStream(
  symbols: string[],
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  if (symbols.length === 0 || symbols.length > 200) {
    throw new Error("depth stream requires 1..200 symbols");
  }
  return openStream(dataRoutes.depthStream, {
    query: { symbols: symbols.join(",") },
    ...options,
  });
}

/** Aggregated data client. */
/**
 * Fetch and persist one market dataset through Data (requires `data:write`).
 *
 * Data performs both steps and authors the returned storage manifest; the
 * gateway holds no dataset and chooses no storage location.
 */
export function prepareDataset(
  body: { market_request: Record<string, unknown>; save_request: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.prepareDataset, {
    schema: z.record(z.string(), z.unknown()),
    body,
    ...options,
  });
}

const datasetSummarySchema = z.object({
  dataset_id: z.string().min(1),
  label: z.string().min(1),
  dataset_kind: z.string().min(1),
  symbol: z.string().nullable(),
  timeframe: z.string().nullable(),
  revision: z.string().min(1),
  content_hash: z.string().length(64),
  row_count: z.number().int().nonnegative(),
  active: z.literal(true),
});

export type DatasetSummary = z.infer<typeof datasetSummarySchema>;

/** List integrity-verified datasets eligible for SIM session binding. */
export function datasets(options?: RequestOptions): Promise<ApiResponse<DatasetSummary[]>> {
  return request<DatasetSummary[]>(dataRoutes.datasets, {
    schema: z.array(datasetSummarySchema),
    ...options,
  });
}

/** Read the import dialects Data supports (requires `data:read`). */
export function importDialects(
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.importDialects, {
    schema: z.record(z.string(), z.unknown()),
    ...options,
  });
}

/**
 * Import one external dataset through Data (requires `data:write`).
 *
 * Data parses, validates, and persists the source and authors the returned
 * manifest; the payload is forwarded unchanged.
 */
export function importDataset(
  body: { payload: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.importDataset, {
    schema: z.record(z.string(), z.unknown()),
    body,
    ...options,
  });
}

export const data = {
  capabilities,
  symbols,
  markets,
  quotes,
  bars,
  stream,
  snapshotStream,
  depthStream,
  prepareDataset,
  datasets,
  importDialects,
  importDataset,
};
