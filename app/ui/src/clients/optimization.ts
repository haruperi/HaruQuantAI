/**
 * Optimization client for the ten run/analysis operations plus one durable
 * result read (11 operations).
 *
 * Optimization owns every result shape; the gateway returns them opaquely and
 * this client performs no scoring, ranking, or interpretation of its own. Every
 * run route requires an idempotency key, which the shared transport supplies
 * automatically when the caller omits one.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { optimizationRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Opaque Optimization-owned result record. */
export const optimizationRecordSchema = z.record(z.string(), z.unknown());
export type OptimizationRecord = z.infer<typeof optimizationRecordSchema>;

/** Build one POST helper bound to a registered Optimization run route. */
function runOperation(
  contract: (typeof optimizationRoutes)[keyof typeof optimizationRoutes]
) {
  return (
    body: Record<string, unknown>,
    options?: RequestOptions
  ): Promise<ApiResponse<OptimizationRecord>> =>
    request<OptimizationRecord>(contract, {
      schema: optimizationRecordSchema,
      body,
      ...options,
    });
}

/** Run one parameter sweep (requires `optimization:run`). */
export const parameterSweep = runOperation(optimizationRoutes.parameterSweep);
/** Run one walk-forward optimization. */
export const walkForward = runOperation(optimizationRoutes.walkForward);
/** Run one walk-forward matrix. */
export const walkForwardMatrix = runOperation(
  optimizationRoutes.walkForwardMatrix
);
/** Run one robustness analysis. */
export const robustness = runOperation(optimizationRoutes.robustness);
/** Compare completed optimization runs. */
export const compare = runOperation(optimizationRoutes.compare);
/** Calculate parameter stability. */
export const stability = runOperation(optimizationRoutes.stability);
/** Detect overfit parameters. */
export const overfit = runOperation(optimizationRoutes.overfit);
/** Rank candidate parameter sets. */
export const rank = runOperation(optimizationRoutes.rank);
/** Calculate one robustness score. */
export const robustnessScore = runOperation(optimizationRoutes.robustnessScore);
/** Build one evidence handoff package. */
export const handoff = runOperation(optimizationRoutes.handoff);

/** Read one durable optimization result (requires `optimization:read`). */
export function result(
  searchId: string,
  reproducibilityHash: string,
  options?: RequestOptions
): Promise<ApiResponse<OptimizationRecord>> {
  return request<OptimizationRecord>(optimizationRoutes.result, {
    schema: optimizationRecordSchema,
    pathParams: { search_id: searchId },
    query: { reproducibility_hash: reproducibilityHash },
    ...options,
  });
}

/** Aggregated Optimization client. */
export const optimization = {
  parameterSweep,
  walkForward,
  walkForwardMatrix,
  robustness,
  compare,
  stability,
  overfit,
  rank,
  robustnessScore,
  handoff,
  result,
};
