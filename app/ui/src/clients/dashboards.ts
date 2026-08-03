/**
 * Dashboards client for the 6 read-only snapshot operations.
 *
 * Each snapshot is owner-authored and timestamped; the gateway returns it
 * opaquely. The client validates a minimal structural contract that carries
 * the freshness `timestamp` and the opaque owner payload. Until the dashboard
 * source is injected in composition, the backend returns HTTP 503
 * `DASHBOARD_DEPENDENCY_UNAVAILABLE`; that surfaces as a normal error envelope.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { dashboardRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** One dashboard snapshot. Owner-authored; payload fields are open. */
export const dashboardSnapshotSchema = z.object({
  timestamp: z.string().min(1).nullish(),
  data: z.unknown().nullish(),
});
export type DashboardSnapshot = z.infer<typeof dashboardSnapshotSchema>;

/** Broker connectivity snapshot (requires `dashboard:read`). */
export function broker(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.broker, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** Equity-curve snapshot (requires `dashboard:read`). */
export function equityCurve(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.equityCurve, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** Summary snapshot (requires `dashboard:read`). */
export function summary(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.summary, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** System-resources snapshot (requires `dashboard:read`). */
export function systemResources(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.systemResources, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** Market-hours snapshot (requires `dashboard:read`). */
export function marketHours(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.marketHours, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** Forex-calendar snapshot (requires `dashboard:read`). */
export function forexCalendar(
  options?: RequestOptions
): Promise<ApiResponse<DashboardSnapshot>> {
  return request<DashboardSnapshot>(dashboardRoutes.forexCalendar, {
    schema: dashboardSnapshotSchema,
    ...options,
  });
}

/** Aggregated dashboards client. */
export const dashboards = {
  broker,
  equityCurve,
  summary,
  systemResources,
  marketHours,
  forexCalendar,
};
