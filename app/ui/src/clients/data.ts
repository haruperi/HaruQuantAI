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

export const data = { symbols, stream, prepareDataset, importDialects, importDataset };
