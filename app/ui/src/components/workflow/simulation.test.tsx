/** Unit tests for SimulationView (FR-UI-013). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { SimulationView } from "./simulation";

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
        route: "/api/v1/simulation/run",
        operation: "api.simulation.run",
        trace_id: null,
        side_effect: "write",
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

describe("SimulationView — FR-UI-013", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope({
        run_id: "run_1",
        status: "completed",
        request_hash: "abc",
        config_hash: "def",
        engine_version: "1.0",
        initial_balance: 100000,
      })
    ) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("rendersResult: clicking Run fetches and renders the result fields", async () => {
    render(<SimulationView />);
    fireEvent.click(screen.getByText("Run Backtest"));
    await waitFor(() => {
      expect(screen.getByText("run_1")).toBeTruthy();
      expect(screen.getByText("completed")).toBeTruthy();
    });
    const calls = (globalThis.fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls;
    expect(String(calls[0]?.[0] ?? "")).toContain("/api/v1/simulation/run");
  });

  it("does not invent metrics beyond the payload", async () => {
    const { container } = render(<SimulationView />);
    fireEvent.click(screen.getByText("Run Backtest"));
    await waitFor(() => expect(screen.getByText("run_1")).toBeTruthy());
    // No Sharpe/Drawdown invented unless present in the opaque payload.
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/sharpe|drawdown|sortino/i);
  });
});
