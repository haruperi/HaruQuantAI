/**
 * Metrics client for the protected Prometheus exposition endpoint.
 *
 * This route is the one documented deviation from the JSON-envelope rule: it
 * returns Prometheus text-format exposition rather than an `ApiResponse`. The
 * transport detects this via `contract.returnsText` and wraps the raw text in
 * a synthetic success envelope so callers see a uniform type.
 */

import type { ApiResponse } from "./contracts";
import { metricsRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Scrape the Prometheus exposition surface (requires `ops:metrics:read`). */
export function scrape(options?: RequestOptions): Promise<ApiResponse<string>> {
  return request<string>(metricsRoutes.scrape, options);
}

/** Aggregated metrics client. */
export const metrics = { scrape };
