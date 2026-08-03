/**
 * Simulation client for backtest execution and result review (3 operations).
 *
 * The Simulator domain owns the exact `SimulationResult.v1` and
 * `PortfolioSimulationResult.v1` shapes; the gateway returns them opaquely.
 * The client validates the structural envelope and renders bounded fields.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { simulationRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Simulation result payload (opaque; Simulator-owned `SimulationResult.v1`). */
export const simulationResultSchema = z.record(z.string(), z.unknown());
export type SimulationResult = z.infer<typeof simulationResultSchema>;

/** Portfolio simulation result payload (opaque; Simulator-owned). */
export const portfolioSimulationResultSchema = z.record(z.string(), z.unknown());
export type PortfolioSimulationResult = z.infer<typeof portfolioSimulationResultSchema>;

/** Input for a synchronous backtest run (opaque; Simulator-owned request). */
export interface SimulationRunInput {
  [key: string]: unknown;
}

/** Run a synchronous backtest (requires `simulation:run`; idempotent). */
export function run(
  input: SimulationRunInput,
  options?: RequestOptions
): Promise<ApiResponse<SimulationResult>> {
  return request<SimulationResult>(simulationRoutes.run, {
    schema: simulationResultSchema,
    body: input,
    ...options,
  });
}

/** Run a synchronous portfolio backtest (requires `simulation:run`; idempotent). */
export function portfolioRun(
  input: SimulationRunInput,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioSimulationResult>> {
  return request<PortfolioSimulationResult>(simulationRoutes.portfolioRun, {
    schema: portfolioSimulationResultSchema,
    body: input,
    ...options,
  });
}

/** Read a stored simulation result by run id (requires `simulation:read`). */
export function result(
  runId: string,
  options?: RequestOptions
): Promise<ApiResponse<SimulationResult>> {
  return request<SimulationResult>(simulationRoutes.result, {
    schema: simulationResultSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Aggregated simulation client. */
export const simulation = { run, portfolioRun, result };
