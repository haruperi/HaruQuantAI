/**
 * Strategies client for catalogue reads and governed mutations (4 operations).
 *
 * Raw import/export and SQX handling remain excluded from backend v1; this
 * client exposes only the registered reads and the two governed mutations.
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
/**
 * Register one new Strategy version (requires `strategy:write`).
 *
 * Strategy owns the registration schema and its validation policy; the payload
 * is forwarded unchanged and Strategy returns immutable mutation truth.
 */
export function register(
  body: { payload: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(strategiesRoutes.register, {
    schema: z.record(z.string(), z.unknown()),
    body,
    ...options,
  });
}

/** Update approved parameters for one registered Strategy version. */
export function updateParameters(
  strategyId: string,
  body: { payload: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(strategiesRoutes.updateParameters, {
    schema: z.record(z.string(), z.unknown()),
    pathParams: { strategy_id: strategyId },
    body,
    ...options,
  });
}

export const strategies = { catalogue, versions, register, updateParameters };
