/**
 * Portfolio client covering the complete governed allocation lifecycle
 * (8 operations).
 *
 * Portfolio owns every payload shape returned here — construction results,
 * active allocations, drift observations, rebalance plans, and measurements are
 * all opaque owner records. The client neither reshapes nor interprets them,
 * and it never decides an approval: activation and rollback carry
 * caller-supplied Risk governance evidence straight through to the backend,
 * which forwards it to Risk for validation.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { portfolioRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Opaque Portfolio-owned record. */
export const portfolioRecordSchema = z.record(z.string(), z.unknown());
export type PortfolioRecord = z.infer<typeof portfolioRecordSchema>;

/** Immutable Portfolio definition registration body. */
export interface PortfolioDefinitionBody {
  contract_version: "v1";
  schema_id: "portfolio.definition.v1";
  portfolio_id: string;
  portfolio_version: string;
  scope: Record<string, string>;
  definition: Record<string, unknown>;
  canonical_hash: string;
}

/** Register one immutable definition version. */
export function registerDefinition(
  portfolioId: string,
  body: PortfolioDefinitionBody,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.registerDefinition, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    body,
    ...options,
  });
}

/** Read one exact immutable definition version. */
export function definition(
  portfolioId: string,
  portfolioVersion: string,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.definition, {
    schema: portfolioRecordSchema,
    pathParams: {
      portfolio_id: portfolioId,
      portfolio_version: portfolioVersion,
    },
    ...options,
  });
}

/** Governed activation or rollback command body. */
export interface PortfolioLifecycleBody {
  construction: Record<string, unknown>;
  simulation: Record<string, unknown>;
  approval_refs?: readonly string[];
  approval_attestation?: Record<string, unknown> | null;
  approval_validation?: Record<string, unknown> | null;
  expires_at: string;
  expected_predecessor?: string | null;
  expected_revision: number;
  /** Present only on rollback: the immutable prior version being rolled back. */
  rollback_of_version?: string;
}

/** Construct one Portfolio candidate (requires `portfolio:write`). */
export function construct(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.construct, {
    schema: portfolioRecordSchema,
    body,
    ...options,
  });
}

/** Read the active allocation for one exact scope (requires `portfolio:read`). */
export function status(
  portfolioId: string,
  scopeKey: string,
  scopeValue: string,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.status, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    query: { scope_key: scopeKey, scope_value: scopeValue },
    ...options,
  });
}

/** Read immutable allocation history (requires `portfolio:read`). */
export function history(
  portfolioId: string,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.history, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    ...options,
  });
}

/** Activate one reviewed allocation version (requires `portfolio:activate`). */
export function activate(
  portfolioId: string,
  body: PortfolioLifecycleBody,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.activate, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    body,
    ...options,
  });
}

/** Create a governed forward rollback version (requires `portfolio:activate`). */
export function rollback(
  portfolioId: string,
  body: PortfolioLifecycleBody,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.rollback, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    body,
    ...options,
  });
}

/** Assess allocation drift for one scope (requires `portfolio:read`). */
export function drift(
  portfolioId: string,
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.drift, {
    schema: portfolioRecordSchema,
    pathParams: { portfolio_id: portfolioId },
    body,
    ...options,
  });
}

/**
 * Submit one governed rebalance (requires `portfolio:rebalance`).
 *
 * The declared runtime profile and execution route must match the deployment's
 * composed settings, and a live route additionally requires
 * `allow_live_mutations`. The backend enforces both before Portfolio is
 * reached, so this client cannot widen what the deployment permits.
 */
export function rebalance(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.rebalance, {
    schema: portfolioRecordSchema,
    body,
    ...options,
  });
}

/** Recompute measurement from Trading evidence (requires `portfolio:write`). */
export function recomputeMeasurement(
  body: { plan_id: string; trading_request_id: string },
  options?: RequestOptions
): Promise<ApiResponse<PortfolioRecord>> {
  return request<PortfolioRecord>(portfolioRoutes.recomputeMeasurement, {
    schema: portfolioRecordSchema,
    body,
    ...options,
  });
}

/** Aggregated Portfolio client. */
export const portfolio = {
  registerDefinition,
  definition,
  construct,
  status,
  history,
  activate,
  rollback,
  drift,
  rebalance,
  recomputeMeasurement,
};
