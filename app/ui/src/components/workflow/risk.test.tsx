/** Unit tests for RiskView (FR-API-050 Risk). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { RiskView } from "./risk";

let callCount = 0;
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
        route: "/api/v1/risk/kill-switch",
        operation: "api.risk.kill_switch",
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

describe("RiskView — FR-API-050 Risk", () => {
  beforeEach(() => {
    callCount = 0;
    globalThis.fetch = vi.fn(async () => {
      callCount += 1;
      // First call: kill-switch; second: decisions.
      return successEnvelope(
        callCount === 1
          ? { state: "inactive", scope_level: "global", reason: "ok", version: 3, updated_at: "2026-08-03T12:00:00Z" }
          : [{ decision_id: "d1", state: "APPROVE" }]
      );
    }) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("rendersKillSwitchAndDecisions: shows state + a bounded decisions list", async () => {
    render(<RiskView />);
    await waitFor(() => {
      expect(screen.getByText("inactive")).toBeTruthy();
      expect(screen.getByText("d1 — APPROVE")).toBeTruthy();
    });
  });

  it("is read-only: no mutation controls", async () => {
    const { container } = render(<RiskView />);
    await waitFor(() => expect(screen.getByText("inactive")).toBeTruthy());
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/activate|deactivate|clear kill.switch|issue decision/i);
  });
});
