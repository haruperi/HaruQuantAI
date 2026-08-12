/** Unit tests for DashboardView (FR-UI-011). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { DashboardView } from "./dashboard";

/** Build a successful envelope response with optional stale metadata. */
function successEnvelope(data: unknown, opts: { stale?: boolean; staleReason?: string } = {}): Response {
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
        route: "/api/v1/dashboard/x",
        operation: "api.dashboard.x",
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-03T12:00:00Z",
        stale: opts.stale ?? false,
        stale_reason: opts.staleReason ?? null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
}

const realFetch = globalThis.fetch;

describe("DashboardView — FR-UI-011", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () => successEnvelope({ ok: true }, { stale: true, staleReason: "cache cold" })) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("staleSnapshotWarns: renders a stale warning when metadata.stale is true", async () => {
    render(<DashboardView />);
    await waitFor(() => {
      expect(screen.getAllByText(/stale/i).length).toBeGreaterThan(0);
    });
  });

  it("renders all six panels", async () => {
    render(<DashboardView />);
    await waitFor(() => {
      expect(screen.getByText("Broker")).toBeTruthy();
      expect(screen.getByText("Equity Curve")).toBeTruthy();
      expect(screen.getByText("Summary")).toBeTruthy();
      expect(screen.getByText("System Resources")).toBeTruthy();
      expect(screen.getByText("Market Hours")).toBeTruthy();
      expect(screen.getByText("Forex Calendar")).toBeTruthy();
    });
  });
});
