/**
 * Watchlists client for the 4 registered watchlist operations
 * (list, create, update, delete).
 *
 * Every account has exactly one default watchlist, seeded on first read with
 * a curated symbol set; the backend owns seeding, ownership checks, and the
 * "exactly one default per account" invariant. Mutations require an
 * idempotency key; the transport generates one automatically when omitted.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { watchlistsRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** One symbol entry within a watchlist. */
export const watchlistItemSchema = z.object({
  source_id: z.string().min(1),
  symbol: z.string().min(1),
  sort_order: z.number().int(),
  asset_class: z.string().min(1),
});
export type WatchlistItem = z.infer<typeof watchlistItemSchema>;

/** One account-owned named, ordered collection of watched symbols. */
export const watchlistSchema = z.object({
  watchlist_id: z.string().min(1),
  account_id: z.string().min(1),
  name: z.string().min(1),
  is_default: z.boolean(),
  sort_order: z.number().int(),
  items: z.array(watchlistItemSchema),
  created_at: z.string().min(1),
  updated_at: z.string().min(1),
});
export type Watchlist = z.infer<typeof watchlistSchema>;

const watchlistListSchema = z.array(watchlistSchema);

/** List every watchlist owned by the caller (requires `watchlists:read`). */
export function list(
  options?: RequestOptions
): Promise<ApiResponse<Watchlist[]>> {
  return request<Watchlist[]>(watchlistsRoutes.list, {
    schema: watchlistListSchema,
    ...options,
  });
}

/** Create one new empty, non-default watchlist (requires `watchlists:write`). */
export function create(
  name: string,
  options?: RequestOptions
): Promise<ApiResponse<Watchlist>> {
  return request<Watchlist>(watchlistsRoutes.create, {
    schema: watchlistSchema,
    body: { name },
    ...options,
  });
}

/** Partial update: rename, replace items, and/or promote to default. */
export interface WatchlistUpdate {
  name?: string;
  symbols?: string[];
  is_default?: boolean;
}

/**
 * Update one watchlist (requires `watchlists:write`).
 *
 * Every present field applies independently in one request: renaming,
 * replacing the complete ordered item list, and promoting to the account's
 * default may all be combined.
 */
export function update(
  watchlistId: string,
  body: WatchlistUpdate,
  options?: RequestOptions
): Promise<ApiResponse<Watchlist>> {
  return request<Watchlist>(watchlistsRoutes.update, {
    schema: watchlistSchema,
    pathParams: { watchlist_id: watchlistId },
    body,
    ...options,
  });
}

const watchlistDeleteResultSchema = z.object({
  watchlist_id: z.string().min(1),
  deleted: z.literal(true),
});

/**
 * Delete one non-default watchlist (requires `watchlists:write`).
 *
 * Rejects deleting the account's current default; promote another watchlist
 * to default first.
 */
export function remove(
  watchlistId: string,
  options?: RequestOptions
): Promise<ApiResponse<z.infer<typeof watchlistDeleteResultSchema>>> {
  return request(watchlistsRoutes.delete, {
    schema: watchlistDeleteResultSchema,
    pathParams: { watchlist_id: watchlistId },
    ...options,
  });
}

/** Aggregated watchlists client. */
export const watchlists = {
  list,
  create,
  update,
  remove,
};
