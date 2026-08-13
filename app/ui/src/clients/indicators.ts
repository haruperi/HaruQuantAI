/**
 * Indicators client for catalogue and capability matrix reads (3 operations).
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { indicatorsRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Indicator specification schema. */
export const indicatorSpecSchema = z.object({
  indicator_id: z.string(),
  name: z.string(),
  indicator_version: z.string(),
  formula_version: z.string(),
  tier: z.string(),
  required_columns: z.array(z.string()),
  parameter_schema: z.record(z.string(), z.unknown()),
  output_templates: z.array(z.string()),
  warmup_policy: z.string(),
  vectorized: z.boolean(),
  multi_symbol: z.boolean(),
  multi_timeframe: z.boolean(),
  import_path: z.string(),
  stability: z.string(),
  workflow_eligibility: z.array(z.string()),
});
export type IndicatorSpec = z.infer<typeof indicatorSpecSchema>;

/** Indicator catalogue schema (array of specs). */
export const indicatorCatalogueSchema = z.array(indicatorSpecSchema);
export type IndicatorCatalogue = z.infer<typeof indicatorCatalogueSchema>;

/** Indicator capability record schema. */
export const indicatorCapabilitySchema = z.object({
  indicator_id: z.string(),
  indicator_version: z.string(),
  formula_version: z.string(),
  tier: z.string(),
  batch: z.boolean(),
  vectorized: z.boolean(),
  multi_symbol: z.boolean(),
  multi_timeframe: z.boolean(),
  unsupported_optional_modes: z.array(z.string()),
  dependencies: z.array(z.string()),
  unsupported_codes: z.array(z.string()),
  official_workflow_eligibility: z.array(z.string()),
});
export type IndicatorCapability = z.infer<typeof indicatorCapabilitySchema>;

/** Capability matrix schema (array of capability records). */
export const capabilityMatrixSchema = z.array(indicatorCapabilitySchema);
export type CapabilityMatrix = z.infer<typeof capabilityMatrixSchema>;

/** One timestamp-aligned indicator value; null is authoritative warm-up. */
export const indicatorPointSchema = z.object({
  time: z.string(),
  value: z.number().nullable(),
  unavailable_reason: z.string().nullable(),
});

/** Indicators-owned chart series with the exact calculation parameters. */
export const indicatorSeriesSchema = z.object({
  indicator_id: z.enum(["ema", "rsi"]),
  name: z.string(),
  symbol: z.string(),
  timeframe: z.string(),
  source_id: z.string(),
  parameters: z.object({
    period: z.number().int().min(2),
    source: z.enum(["open", "high", "low", "close"]),
  }),
  points: z.array(indicatorPointSchema),
  count: z.number().int().nonnegative(),
  valid_count: z.number().int().nonnegative(),
  availability: z.enum(["available", "insufficient_history"]),
  unavailable_reason: z.string().nullable(),
  indicator_version: z.string(),
  formula_version: z.string(),
  request_id: z.string(),
});
export type IndicatorSeries = z.infer<typeof indicatorSeriesSchema>;

export interface IndicatorSeriesQuery {
  indicatorId: "ema" | "rsi";
  symbol: string;
  timeframe: string;
  period: number;
  source?: "open" | "high" | "low" | "close";
  limit: number;
  start?: string;
  end?: string;
}

/** Read the full indicator catalogue (requires `indicators:read`). */
export function catalogue(
  options?: RequestOptions
): Promise<ApiResponse<IndicatorCatalogue>> {
  return request<IndicatorCatalogue>(indicatorsRoutes.catalogue, {
    schema: indicatorCatalogueSchema,
    ...options,
  });
}

/** Read the indicator capability matrix (requires `indicators:read`). */
export function capabilities(
  options?: RequestOptions
): Promise<ApiResponse<CapabilityMatrix>> {
  return request<CapabilityMatrix>(indicatorsRoutes.capabilities, {
    schema: capabilityMatrixSchema,
    ...options,
  });
}

/** Read the spec for one indicator (requires `indicators:read`). */
export function getSpec(
  indicatorId: string,
  options?: RequestOptions
): Promise<ApiResponse<IndicatorSpec>> {
  return request<IndicatorSpec>(indicatorsRoutes.spec, {
    schema: indicatorSpecSchema,
    pathParams: { indicator_id: indicatorId },
    ...options,
  });
}

/** Calculate one chart series through the workstation Indicators boundary. */
export function series(
  query: IndicatorSeriesQuery,
  options?: RequestOptions
): Promise<ApiResponse<IndicatorSeries>> {
  return request<IndicatorSeries>(indicatorsRoutes.series, {
    schema: indicatorSeriesSchema,
    pathParams: { indicator_id: query.indicatorId },
    query: {
      symbol: query.symbol,
      timeframe: query.timeframe,
      period: query.period,
      source: query.source ?? "close",
      limit: query.limit,
      start: query.start,
      end: query.end,
    },
    ...options,
  });
}

export const indicators = { catalogue, capabilities, getSpec, series };
