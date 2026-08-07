/** Unit tests for TradingView (FR-API-050 Trading). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { TradingView } from "./trading";

function successEnvelope(data: unknown): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_t",
        route: "/api/v1/trading/session",
        operation: "api.trading.session",
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-03T12:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
}

const realFetch = globalThis.fetch;

describe("TradingView — FR-API-050 Trading", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope({
        account: { balance: 100000, equity: 100000 },
        positions: [{ symbol: "EURUSD", qty: 1 }],
        orders: [],
      })
    ) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("sessionReads: fetches and renders account/positions/orders", async () => {
    render(<TradingView />);
    await waitFor(() => {
      expect(screen.getByText("Account")).toBeTruthy();
      expect(screen.getByText("Positions")).toBeTruthy();
      expect(screen.getByText("Orders")).toBeTruthy();
    });
  });

  it("governedActionsBlocked: Submit/Cancel/Close are disabled before arming preflight", async () => {
    render(<TradingView />);
    await waitFor(() => expect(screen.getByText("Submit Order")).toBeTruthy());
    const submit = screen.getByText("Submit Order").closest("button");
    const cancel = screen.getByText("Cancel Order").closest("button");
    const close = screen.getByText("Close Position").closest("button");
    expect(submit?.hasAttribute("disabled")).toBe(true);
    expect(cancel?.hasAttribute("disabled")).toBe(true);
    expect(close?.hasAttribute("disabled")).toBe(true);
  });

  it("governedActionsReachable: explicit authority enables all three API actions", async () => {
    render(<TradingView />);
    await waitFor(() => expect(screen.getByText("Submit Order")).toBeTruthy());

    const values: Record<string, string> = {
      "Account ID": "account-1",
      "Strategy ID": "strategy-1",
      "Strategy version": "v1",
      "Intent ID": "intent-1",
      Symbol: "EURUSD",
      Quantity: "1",
      "Risk decision ID": "risk-1",
      "Action-policy verdict ID": "verdict-1",
      "Approval token reference": "approval-1",
      "Broker order ID": "broker-order-1",
      "Broker position ID": "broker-position-1",
    };
    for (const [label, value] of Object.entries(values)) {
      fireEvent.change(screen.getByLabelText(label), { target: { value } });
    }

    for (const action of ["Submit Order", "Cancel Order", "Close Position"]) {
      fireEvent.click(screen.getByText("Arm preflight"));
      const button = screen.getByText(action).closest("button");
      expect(button?.hasAttribute("disabled")).toBe(false);
      fireEvent.click(screen.getByText(action));
      await waitFor(() => expect(screen.getByRole("status")).toBeTruthy());
    }

    const calls = vi.mocked(globalThis.fetch).mock.calls;
    expect(calls).toHaveLength(4);
    expect(String(calls[1][0])).toContain("/api/v1/trading/orders");
    expect(String(calls[2][0])).toContain("broker-order-1");
    expect(String(calls[3][0])).toContain("broker-position-1");
    expect(calls.slice(1).map(([, options]) => options?.method)).toEqual([
      "POST",
      "DELETE",
      "POST",
    ]);
    for (const [, options] of calls.slice(1)) {
      expect(options?.headers).toMatchObject({ "Idempotency-Key": expect.any(String) });
    }
  });
});
