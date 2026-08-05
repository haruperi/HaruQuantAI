/**
 * Risk client for risk state reads and the governed kill-switch command (3 operations).
 *
 * The Risk domain owns the exact `KillSwitchState.v1` and
 * `RiskDecisionPackage.v1` shapes; the gateway returns them opaquely.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { riskRoutes } from "./routes";
import { request, type RequestOptions, type QueryValue } from "./request";

/** Kill-switch state payload (opaque; Risk-owned `KillSwitchState.v1`). */
export const killSwitchStateSchema = z.record(z.string(), z.unknown());
export type KillSwitchState = z.infer<typeof killSwitchStateSchema>;

/** Risk decision package payload (opaque; Risk-owned `RiskDecisionPackage.v1`). */
export const riskDecisionSchema = z.record(z.string(), z.unknown());
export type RiskDecision = z.infer<typeof riskDecisionSchema>;

/** Query parameters for the kill-switch read. */
export interface KillSwitchQuery {
  scope_level?: string;
  scope?: string;
}

/** Query parameters for the decisions read. */
export interface RiskDecisionsQuery {
  limit?: number;
}

/** Read the current kill-switch state (requires `risk:read`). */
export function killSwitch(
  params: KillSwitchQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<KillSwitchState>> {
  const query: Record<string, QueryValue> = {};
  if (params.scope_level !== undefined) query.scope_level = params.scope_level;
  if (params.scope !== undefined) query.scope = params.scope;
  return request<KillSwitchState>(riskRoutes.killSwitch, {
    schema: killSwitchStateSchema,
    query,
    ...options,
  });
}

/** Read recent risk decisions (requires `risk:read`). */
export function decisions(
  params: RiskDecisionsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<RiskDecision[]>> {
  const query: Record<string, QueryValue> = {};
  if (params.limit !== undefined) query.limit = params.limit;
  return request<RiskDecision[]>(riskRoutes.decisions, {
    schema: z.array(riskDecisionSchema),
    query,
    ...options,
  });
}

/**
 * Request one governed kill-switch transition (requires `risk:kill_switch`).
 *
 * Risk validates the attestation and owns the resulting state; a command
 * without attestation is refused by the backend before any owner call.
 */
export function applyKillSwitch(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<KillSwitchState>> {
  return request<KillSwitchState>(riskRoutes.applyKillSwitch, {
    schema: killSwitchStateSchema,
    body,
    ...options,
  });
}

/** Aggregated risk client. */
export const risk = { killSwitch, decisions, applyKillSwitch };
