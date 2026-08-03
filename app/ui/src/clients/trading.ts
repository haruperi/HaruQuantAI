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

/** Input for submitting a governed order (opaque; Trading-owned request). */
export interface SubmitOrderInput {
  [key: string]: unknown;
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
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.cancelOrder, {
    schema: executionReceiptSchema,
    pathParams: { order_id: orderId },
    ...options,
  });
}

/** Close a governed position (requires `trading:write`; governed + idempotent). */
export function closePosition(
  positionId: string,
  options?: RequestOptions
): Promise<ApiResponse<ExecutionReceipt>> {
  return request<ExecutionReceipt>(tradingRoutes.closePosition, {
    schema: executionReceiptSchema,
    pathParams: { position_id: positionId },
    ...options,
  });
}

/** Aggregated trading client. */
export const trading = { session, submitOrder, cancelOrder, closePosition };
