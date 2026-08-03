/**
 * Research client for the single Edge Lab run operation.
 *
 * The request body is the backend `ResearchRunRequest` (hypothesis + dataset +
 * config). The dataset/config objects are coerced by the backend into
 * Data-owned `MarketDataset` and Research-owned `EdgeLabConfig` values; the
 * client sends them as opaque JSON objects.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { researchRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Advisory research report. Research-owned; returned opaquely. */
export const researchReportSchema = z.record(z.string(), z.unknown());
export type ResearchReport = z.infer<typeof researchReportSchema>;

/** Request body for an Edge Lab run (backend `ResearchRunRequest`). */
export interface ResearchRunInput {
  hypothesis: string;
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
}

/** Run a core Edge Lab research profile (requires `research:run`). */
export function run(
  input: ResearchRunInput,
  options?: RequestOptions
): Promise<ApiResponse<ResearchReport>> {
  return request<ResearchReport>(researchRoutes.run, {
    schema: researchReportSchema,
    body: input,
    ...options,
  });
}

/** Aggregated research client. */
export const research = { run };
