/**
 * Simulator client for canonical backtest runs (6 operations).
 *
 * A canonical run exceeds the API's endpoint deadline, so the surface is a job:
 * `startRun` returns an accepted identity immediately, and progress is observed
 * by polling `run` or consuming `runStream`. The client never derives a metric;
 * every reported figure is Analytics-owned and arrives already calculated.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { simulatorRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** One declared strategy configuration parameter. */
export const strategyParameterSchema = z.object({
  name: z.string(),
  label: z.string(),
  kind: z.enum(["integer", "decimal"]),
  default: z.string(),
  minimum: z.string().nullable(),
  maximum: z.string().nullable(),
});
export type StrategyParameter = z.infer<typeof strategyParameterSchema>;

/**
 * One registered backtest strategy.
 *
 * A strategy the recipe cannot run today stays listed with `runnable: false`
 * and carries `unavailableReason`, so the picker shows the real catalogue
 * rather than silently hiding a strategy.
 */
export const backtestStrategySchema = z.object({
  strategy_id: z.string(),
  strategy_version: z.string(),
  evaluator_name: z.string(),
  label: z.string(),
  runnable: z.boolean(),
  unavailable_reason: z.string().nullable(),
  required_indicators: z.array(z.string()),
  supports_exits: z.boolean(),
  parameters: z.array(strategyParameterSchema),
});
export type BacktestStrategy = z.infer<typeof backtestStrategySchema>;

const strategyCatalogueSchema = z.object({
  strategies: z.array(backtestStrategySchema),
});
export type BacktestStrategyCatalogue = z.infer<typeof strategyCatalogueSchema>;

/** One ordered progress record emitted by a running backtest. */
export const runProgressEventSchema = z.object({
  sequence: z.number(),
  at: z.string(),
  stage: z.string(),
  detail: z.string(),
});
export type RunProgressEvent = z.infer<typeof runProgressEventSchema>;

/** Terminal run status. */
export const RUN_STATUSES = [
  "queued",
  "running",
  "succeeded",
  "failed",
  "cancelled",
] as const;
export type RunStatus = (typeof RUN_STATUSES)[number];

/**
 * Completed run evidence.
 *
 * `metrics` is an Analytics-owned key/value map holding only metrics whose
 * status was `calculated`; a metric absent from the map was not calculated and
 * must be presented as unavailable rather than as zero.
 */
export const runReportSchema = z.object({
  run_id: z.string(),
  engine_version: z.string(),
  config_hash: z.string(),
  strategy_id: z.string(),
  strategy_version: z.string(),
  strategy_label: z.string(),
  parameters: z.record(z.string(), z.string()),
  symbol: z.string(),
  timeframe: z.string(),
  start: z.string(),
  end: z.string(),
  initial_balance: z.string(),
  account_currency: z.string(),
  bar_count: z.number(),
  warmup_bars: z.number(),
  closed_trade_count: z.number(),
  metrics: z.record(z.string(), z.string()),
  quality: z.record(z.string(), z.unknown()),
  quality_flags: z.array(z.string()),
  caveats: z.array(z.string()),
});
export type RunReport = z.infer<typeof runReportSchema>;

/** Bounded projection of one backtest run. */
export const backtestRunSchema = z.object({
  job_id: z.string(),
  status: z.enum(RUN_STATUSES),
  stage: z.string().nullable(),
  submitted_at: z.string(),
  started_at: z.string().nullable(),
  finished_at: z.string().nullable(),
  symbol: z.string(),
  timeframe: z.string(),
  strategy_id: z.string(),
  events: z.array(runProgressEventSchema),
  result: runReportSchema.nullable(),
  error: z.string().nullable(),
});
export type BacktestRun = z.infer<typeof backtestRunSchema>;

const runListSchema = z.object({ runs: z.array(backtestRunSchema) });

/** Operator-chosen configuration for one canonical backtest run. */
export interface BacktestRunInput {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  strategy_id: string;
  parameters?: Record<string, string>;
  initial_balance?: string;
  account_currency?: string;
  volume?: string;
  commission_per_lot_per_side?: string;
  spread_points?: string;
  slippage_points?: string;
  seed?: number;
  bar_limit?: number;
}

/** List every registered backtest strategy (requires `simulation:read`). */
export function strategies(
  options?: RequestOptions
): Promise<ApiResponse<BacktestStrategyCatalogue>> {
  return request<BacktestStrategyCatalogue>(simulatorRoutes.strategies, {
    schema: strategyCatalogueSchema,
    ...options,
  });
}

/** Start one canonical backtest run (requires `simulation:run`; idempotent). */
export function startRun(
  input: BacktestRunInput,
  options?: RequestOptions
): Promise<ApiResponse<BacktestRun>> {
  return request<BacktestRun>(simulatorRoutes.startRun, {
    schema: backtestRunSchema,
    body: input,
    ...options,
  });
}

/** List the caller's retained runs, newest first (requires `simulation:read`). */
export function runs(
  options?: RequestOptions
): Promise<ApiResponse<{ runs: BacktestRun[] }>> {
  return request<{ runs: BacktestRun[] }>(simulatorRoutes.runs, {
    schema: runListSchema,
    ...options,
  });
}

/** Read one owned run including its terminal report (requires `simulation:read`). */
export function run(
  runId: string,
  options?: RequestOptions
): Promise<ApiResponse<BacktestRun>> {
  return request<BacktestRun>(simulatorRoutes.run, {
    schema: backtestRunSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Request cancellation of one owned run (requires `simulation:run`). */
export function cancelRun(
  runId: string,
  options?: RequestOptions
): Promise<ApiResponse<BacktestRun>> {
  return request<BacktestRun>(simulatorRoutes.cancelRun, {
    schema: backtestRunSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Aggregated simulator client. */
export const simulator = { strategies, startRun, runs, run, cancelRun };
