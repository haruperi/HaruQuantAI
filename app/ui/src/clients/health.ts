/**
 * Health client for the 2 health operations (public liveness, protected readiness).
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { healthRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Liveness response data. */
export const livenessSchema = z.object({
  status: z.enum(["healthy", "degraded", "unhealthy"]),
  checked_at: z.string().min(1),
});
export type Liveness = z.infer<typeof livenessSchema>;

/** One dependency check inside a readiness response. */
export const healthDependencyCheckSchema = z.object({
  component: z.string().min(1),
  required: z.boolean(),
  healthy: z.boolean(),
  checked_at: z.string().min(1),
  reason: z.string().nullable().nullish(),
});
export type HealthDependencyCheck = z.infer<typeof healthDependencyCheckSchema>;

/** Readiness response data. */
export const readinessSchema = z.object({
  status: z.enum(["ready", "degraded"]),
  checked_at: z.string().min(1),
  clock_drift_seconds: z.union([z.number(), z.string()]),
  dependencies: z.array(healthDependencyCheckSchema),
});
export type Readiness = z.infer<typeof readinessSchema>;

/** Public liveness probe (no auth). */
export function liveness(
  options?: RequestOptions
): Promise<ApiResponse<Liveness>> {
  return request<Liveness>(healthRoutes.liveness, {
    schema: livenessSchema,
    ...options,
  });
}

/** Protected readiness probe (requires `ops:read`). */
export function readiness(
  options?: RequestOptions
): Promise<ApiResponse<Readiness>> {
  return request<Readiness>(healthRoutes.readiness, {
    schema: readinessSchema,
    ...options,
  });
}

/** Aggregated health client. */
export const health = { liveness, readiness };
