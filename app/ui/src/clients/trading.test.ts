/** Contract tests for the governed Trading HTTP client. */

import { afterEach, describe, expect, it, vi } from "vitest";

import { cancelOrder, closePosition, submitOrder, type TradingMutationInput } from "./trading";

const realFetch = globalThis.fetch;

function input(action: string): TradingMutationInput {
  return {
    request_id: "req-1",
    workflow_id: "wf-1",
    correlation_id: "cor-1",
    route: "demo",
    action,
    account_id: "account-1",
    strategy_id: "strategy-1",
    strategy_version: "v1",
    intent_id: "intent-1",
    symbol: "EURUSD",
    side: "BUY",
    order_type: "MARKET",
    quantity_unit: "units",
    quantity: "1",
    risk_decision_id: "risk-1",
    action_policy_verdict_id: "verdict-1",
    approval_token_ref: "approval-1",
    idempotency_key: "idem-1",
    canonical_material_version: "v1",
    system_time: "2026-08-06T08:00:00Z",
    valid_until: "2026-08-06T08:05:00Z",
  };
}

function response(): Response {
  return new Response(JSON.stringify({
    status: "success",
    message: "ok",
    data: { receipt_id: "receipt-1" },
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req-1",
      route: "/api/v1/trading",
      operation: "api.trading.write",
      trace_id: null,
      side_effect: "write",
      duration_ms: 1,
      timestamp: "2026-08-06T08:00:00Z",
      stale: false,
      stale_reason: null,
      next_cursor: null,
      page_size: null,
      idempotency_replayed: false,
    },
  }), { status: 200, headers: { "Content-Type": "application/json" } });
}

describe("Trading governed client", () => {
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("routes submit, cancel, and close bodies through their exact endpoints", async () => {
    globalThis.fetch = vi.fn(async () => response()) as unknown as typeof fetch;
    const options = { idempotencyKey: "idem-1" };

    await submitOrder(input("submit_order"), options);
    await cancelOrder("order-1", input("cancel_order"), options);
    await closePosition("position-1", input("close_position"), options);

    const calls = vi.mocked(globalThis.fetch).mock.calls;
    expect(calls).toHaveLength(3);
    expect(String(calls[0][0])).toContain("/api/v1/trading/orders");
    expect(String(calls[1][0])).toContain("order-1");
    expect(String(calls[2][0])).toContain("position-1");
    expect(calls.map(([, requestOptions]) => requestOptions?.method)).toEqual([
      "POST",
      "DELETE",
      "POST",
    ]);
    for (const [, requestOptions] of calls) {
      expect(requestOptions?.body).toContain('"risk_decision_id":"risk-1"');
    }
  });
});
