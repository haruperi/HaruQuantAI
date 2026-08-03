/**
 * Data client for symbol discovery (1 cursor-paginated operation).
 *
 * The Data domain owns the exact row shape; the gateway returns it opaquely.
 * The client validates a minimal structural contract (opaque rows) and leaves
 * field-level interpretation to consumers.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { dataRoutes } from "./routes";
import { request, type RequestOptions, type QueryValue } from "./request";

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

/** Aggregated data client. */
export const data = { symbols };
