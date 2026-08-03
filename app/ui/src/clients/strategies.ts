/**
 * Strategies client for the 2 read-only strategy catalogue operations.
 *
 * Mutations, raw import/export, and SQX handling are excluded from backend v1;
 * this client exposes only the registered reads.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { strategiesRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Strategy version entry. Strategy-owned; fields are open records. */
export const strategyVersionSchema = z.record(z.string(), z.unknown());
export type StrategyVersion = z.infer<typeof strategyVersionSchema>;

/** Catalogue response (array of version entries). */
export const strategyCatalogueSchema = z.array(strategyVersionSchema);
export type StrategyCatalogue = z.infer<typeof strategyCatalogueSchema>;

/** Read the full strategy version catalogue (requires `strategy:read`). */
export function catalogue(
  options?: RequestOptions
): Promise<ApiResponse<StrategyCatalogue>> {
  return request<StrategyCatalogue>(strategiesRoutes.catalogue, {
    schema: strategyCatalogueSchema,
    ...options,
  });
}

/** Read the version catalogue for one strategy (requires `strategy:read`). */
export function versions(
  strategyId: string,
  options?: RequestOptions
): Promise<ApiResponse<StrategyCatalogue>> {
  return request<StrategyCatalogue>(strategiesRoutes.versions, {
    schema: strategyCatalogueSchema,
    pathParams: { strategy_id: strategyId },
    ...options,
  });
}

/** Aggregated strategies client. */
export const strategies = { catalogue, versions };
