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

/** Minimal provider-authored identity shown in the application Header. */
export const tradingAccountProfileSchema = z.object({
  contract_version: z.literal("v1"),
  schema_id: z.literal("api.trading.account_profile.v1"),
  account_name: z.string().min(1),
  trade_mode: z.enum(["SIMULATION", "DEMO", "REAL", "CONTEST"]),
  environment_label: z.string().min(1),
  source: z.enum(["simulator", "mt5"]),
  retrieved_at: z.string(),
});
export type TradingAccountProfile = z.infer<typeof tradingAccountProfileSchema>;

/** Read the active Simulator or MT5 account identity. */
export function accountProfile(
  options?: RequestOptions
): Promise<ApiResponse<TradingAccountProfile>> {
  return request<TradingAccountProfile>(tradingRoutes.accountProfile, {
    schema: tradingAccountProfileSchema,
    ...options,
  });
}

/** Trading session projection (opaque; Trading-owned `TradingProjection.v1`). */
export const tradingProjectionSchema = z.record(z.string(), z.unknown());
export type TradingProjection = z.infer<typeof tradingProjectionSchema>;

/**
 * One real working order, exactly as Trading's own state projection reports
 * it — the submitted intent plus whatever the broker has acknowledged so far.
 * `broker_order_id` is present only once a receipt has arrived; an order
 * without it cannot yet be targeted by `DELETE /orders/{order_id}`.
 */
export const workingOrderSchema = z.object({
  request_id: z.string(),
  intent: z.object({
    client_order_id: z.string(),
    symbol: z.string(),
    side: z.enum(["BUY", "SELL"]),
    order_type: z.enum(["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]),
    approved_volume: z.union([z.string(), z.number()]),
    price: z.union([z.string(), z.number()]).nullable().optional(),
  }),
  broker_order_id: z.string().optional(),
});
export type WorkingOrder = z.infer<typeof workingOrderSchema>;

/** Extract every real working order Trading's session projection reports. */
export function listWorkingOrders(projection: TradingProjection): WorkingOrder[] {
  const raw = projection.orders;
  if (typeof raw !== "object" || raw === null) return [];
  const orders: WorkingOrder[] = [];
  for (const value of Object.values(raw as Record<string, unknown>)) {
    const parsed = workingOrderSchema.safeParse(value);
    if (parsed.success) orders.push(parsed.data);
  }
  return orders;
}

/**
 * One real open position, exactly as Trading's own state projection reports
 * it. `broker_position_id` is what `POST /positions/{position_id}/close`
 * targets; a position without a positive quantity is already flat and is
 * never closable.
 */
export const positionSchema = z.object({
  position_id: z.string(),
  account_id: z.string(),
  symbol: z.string(),
  broker_position_id: z.string(),
  side: z.enum(["LONG", "SHORT", "UNKNOWN"]),
  state: z.string(),
  quantity: z.union([z.string(), z.number()]),
  average_entry_price: z.union([z.string(), z.number()]).nullable().optional(),
});
export type Position = z.infer<typeof positionSchema>;

/**
 * Extract every real position Trading's session projection reports.
 *
 * Positions the projection reports as flat or with a non-positive quantity are
 * omitted: they are closed history, not open exposure, and must never be
 * counted or offered for closing.
 */
export function listPositions(projection: TradingProjection): Position[] {
  const raw = projection.positions;
  if (typeof raw !== "object" || raw === null) return [];
  const positions: Position[] = [];
  for (const value of Object.values(raw as Record<string, unknown>)) {
    const parsed = positionSchema.safeParse(value);
    if (!parsed.success) continue;
    if (parsed.data.state === "FLAT") continue;
    if (Number(parsed.data.quantity) <= 0) continue;
    positions.push(parsed.data);
  }
  return positions;
}

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
  route: "sim" | "demo" | "live";
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

/** Real Risk decision/verdict pair the API gateway itself produces and owns. */
export const riskPreflightResponseSchema = z.object({
  state: z.string(),
  risk_decision_id: z.string(),
  action_policy_verdict_id: z.string().nullable(),
  approval_token_ref: z.string().nullable(),
  reasons: z.array(z.string()),
  expires_at: z.string(),
});
export type RiskPreflightResponse = z.infer<typeof riskPreflightResponseSchema>;

/** Exact API projection of `trading.order_preflight_request.v1`. */
export interface OrderPreflightInput {
  request_id: string;
  workflow_id: string;
  correlation_id: string;
  route: "sim" | "demo" | "live";
  account_id: string;
  portfolio_id?: string | null;
  symbol: string;
  side: "BUY" | "SELL";
  order_type: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
  quantity: string | number;
  current_price: string | number;
  stop_distance?: string | number | null;
  idempotency_key: string;
}

/** Exact API projection of `trading.cancel_all_preflight_request.v1`. */
export interface CancelAllPreflightInput {
  request_id: string;
  workflow_id: string;
  correlation_id: string;
  route: "sim" | "demo" | "live";
  account_id: string;
  portfolio_id?: string | null;
  representative_symbol: string;
  idempotency_key: string;
}

/** Exact API projection of `trading.cancel_order_preflight_request.v1`. */
export interface CancelOrderPreflightInput {
  request_id: string;
  workflow_id: string;
  correlation_id: string;
  route: "sim" | "demo" | "live";
  account_id: string;
  portfolio_id?: string | null;
  representative_symbol: string;
  target_broker_order_id: string;
  idempotency_key: string;
}

/** Review one candidate order through Risk's real gate (requires `trading:write`). */
export function preflightOrder(
  input: OrderPreflightInput,
  options?: RequestOptions
): Promise<ApiResponse<RiskPreflightResponse>> {
  return request<RiskPreflightResponse>(tradingRoutes.preflightOrder, {
    schema: riskPreflightResponseSchema,
    body: input,
    ...options,
  });
}

/** Authorize one order's cancellation through Risk's real gate (requires `trading:write`). */
export function preflightCancelOrder(
  orderId: string,
  input: CancelOrderPreflightInput,
  options?: RequestOptions
): Promise<ApiResponse<RiskPreflightResponse>> {
  return request<RiskPreflightResponse>(tradingRoutes.cancelOrderPreflight, {
    schema: riskPreflightResponseSchema,
    pathParams: { order_id: orderId },
    body: input,
    ...options,
  });
}

/** Authorize a bulk cancel-all through Risk's real gate (requires `trading:write`). */
export function preflightCancelAllOrders(
  input: CancelAllPreflightInput,
  options?: RequestOptions
): Promise<ApiResponse<RiskPreflightResponse>> {
  return request<RiskPreflightResponse>(tradingRoutes.cancelAllPreflight, {
    schema: riskPreflightResponseSchema,
    body: input,
    ...options,
  });
}

/** Cancel every eligible governed order (requires `trading:write`; governed + idempotent). */
export function cancelAllOrders(
  input: TradingMutationInput,
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.cancelAllOrders, {
    schema: executionReceiptSchema,
    body: input,
    ...options,
  });
}

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
export const trading = {
  accountProfile,
  session,
  preflightOrder,
  submitOrder,
  preflightCancelOrder,
  cancelOrder,
  closePosition,
  preflightCancelAllOrders,
  cancelAllOrders,
};
