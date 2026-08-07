/**
 * Trading session client for read-only session + governed mutations (4 operations).
 *
 * The Trading domain owns the exact `TradingProjection.v1` and
 * `ExecutionReceipt.v1` shapes; the gateway returns them opaquely. The three
 * mutation routes are governed writes: the transport auto-attaches the
 * idempotency key and CSRF header, and backend gates (kill-switch, risk review,
 * approval, evidence freshness) remain the sole authority.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { tradingRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Trading session projection (opaque; Trading-owned `TradingProjection.v1`). */
export const tradingProjectionSchema = z.record(z.string(), z.unknown());
export type TradingProjection = z.infer<typeof tradingProjectionSchema>;

/** Execution receipt (opaque; Trading-owned `ExecutionReceipt.v1`). */
export const executionReceiptSchema = z.record(z.string(), z.unknown());
export type ExecutionReceipt = z.infer<typeof executionReceiptSchema>;

/** Exact API projection of `trading.trading_request.v1`. */
export interface TradingMutationInput {
  contract_version?: "v1";
  schema_id?: "trading.trading_request.v1";
  request_id: string;
  workflow_id: string;
  correlation_id: string;
  causation_id?: string | null;
  route: "paper" | "live";
  action: string;
  provider_id?: string | null;
  account_id: string;
  portfolio_id?: string | null;
  strategy_id: string;
  strategy_version: string;
  intent_id: string;
  symbol?: string | null;
  side?: "BUY" | "SELL" | null;
  order_type: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
  quantity_unit: string;
  quantity?: string | number | null;
  price?: string | number | null;
  stop_price?: string | number | null;
  stop_loss?: string | number | null;
  take_profit?: string | number | null;
  time_in_force?: "GTC" | "IOC" | "FOK" | "GTD" | "DAY" | null;
  expiration?: string | null;
  target_broker_order_id?: string | null;
  target_broker_position_id?: string | null;
  order_id?: string | null;
  position_id?: string | null;
  expected_version?: number | null;
  risk_decision_id: string;
  action_policy_verdict_id: string;
  approval_token_ref: string;
  eligibility_decision_id?: string | null;
  allocation_decision_id?: string | null;
  scope_level?: "global" | "portfolio" | "strategy" | "symbol" | null;
  control_reason?: string | null;
  idempotency_key: string;
  canonical_material_version: string;
  system_time: string;
  broker_time?: string | null;
  valid_until: string;
}

export type SubmitOrderInput = TradingMutationInput;

/** Read the aggregate trading session (requires `trading:read`). */
export function session(
  options?: RequestOptions
): Promise<ApiResponse<TradingProjection>> {
  return request<TradingProjection>(tradingRoutes.session, {
    schema: tradingProjectionSchema,
    ...options,
  });
}

/** Submit a governed order (requires `trading:write`; governed + idempotent). */
export function submitOrder(
  input: SubmitOrderInput,
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.submitOrder, {
    schema: executionReceiptSchema,
    body: input,
    ...options,
  });
}

/** Cancel a governed order (requires `trading:write`; governed + idempotent). */
export function cancelOrder(
  orderId: string,
  input: TradingMutationInput,
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.cancelOrder, {
    schema: executionReceiptSchema,
    pathParams: { order_id: orderId },
    body: input,
    ...options,
  });
}

/** Close a governed position (requires `trading:write`; governed + idempotent). */
export function closePosition(
  positionId: string,
  input: TradingMutationInput,
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.closePosition, {
    schema: executionReceiptSchema,
    pathParams: { position_id: positionId },
    body: input,
    ...options,
  });
}

/** Aggregated trading client. */
export const trading = { session, submitOrder, cancelOrder, closePosition };
