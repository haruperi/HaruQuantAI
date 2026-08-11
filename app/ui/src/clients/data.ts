/**
 * Data client for symbol discovery, the market stream, governed dataset
 * preparation, and external import (5 operations).
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

/** Symbol discovery page. */
export const symbolPageSchema = z.object({
  symbols: z.array(symbolRowSchema),
  next_cursor: z.string().nullable().nullish(),
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
  return request<MarketDirectory>(dataRoutes.markets, {
    schema: marketDirectorySchema,
    query,
    ...options,
  });
}

/** Query parameters for the SSE market stream. */
export interface StreamQuery {
  symbol: string;
  mode: "bars" | "ticks";
  timeframe: string;
  source_id?: "mt5";
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
  stream,
  prepareDataset,
  importDialects,
  importDataset,
};
