/** Unit tests for the advisory Optimization workflow. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OptimizationView } from "./optimization";

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
        route: "/api/v1/optimization/parameter-sweep",
        operation: "api.optimization.parameter_sweep",
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-07T00:00:00Z",
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

describe("OptimizationView", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope({ search_id: "search-one", decision: "validation_needed" })
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("runs a bounded request and renders advisory evidence", async () => {
    render(<OptimizationView />);
    fireEvent.click(screen.getByText("Run bounded optimization"));
    await waitFor(() => expect(screen.getByText("Advisory result")).toBeTruthy());
    expect(screen.getByText(/Optimization cannot place trades/)).toBeTruthy();
    expect(screen.getByText(/search-one/)).toBeTruthy();
    expect(String(vi.mocked(globalThis.fetch).mock.calls[0][0])).toContain(
      "/api/v1/optimization/parameter-sweep"
    );
  });

  it("fails closed before the API when request JSON is invalid", async () => {
    render(<OptimizationView />);
    fireEvent.change(screen.getByLabelText("Bounded parameter sweep request"), {
      target: { value: "{" },
    });
    fireEvent.click(screen.getByText("Run bounded optimization"));
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toBe("Request must be valid JSON");
    expect(vi.mocked(globalThis.fetch)).not.toHaveBeenCalled();
  });
});
