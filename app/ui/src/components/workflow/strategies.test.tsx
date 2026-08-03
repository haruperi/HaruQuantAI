/** Unit tests for StrategyWorkspace (FR-API-048). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { StrategyWorkspace } from "./strategies";

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
        route: "/api/v1/strategies",
        operation: "api.strategies.catalogue",
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

describe("StrategyWorkspace — FR-API-048", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope([{ id: "strat-1", name: "Momentum" }])
    ) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("usesTypedClient: fetches the catalogue and renders entries", async () => {
    render(<StrategyWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("strat-1")).toBeTruthy();
    });
    const calls = (globalThis.fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls;
    // First call must target the strategies route.
    expect(String(calls[0]?.[0] ?? "")).toContain("/api/v1/strategies");
  });

  it("does not render mutation/import/export/SQX controls", async () => {
    const { container } = render(<StrategyWorkspace />);
    await waitFor(() => expect(screen.getByText("strat-1")).toBeTruthy());
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/import|export|SQX|delete|register|update/i);
  });
});
