/** Unit tests for the governed Portfolio workflow. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PortfolioView } from "./portfolio";

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
        route: "/api/v1/portfolio/portfolio-alpha/definitions",
        operation: "api.portfolio.definition_register",
        trace_id: null,
        side_effect: "governed_write",
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

describe("PortfolioView", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope({ portfolio_id: "portfolio-alpha", portfolio_version: "v1" })
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("does not mutate on mount and explicitly registers a definition", async () => {
    render(<PortfolioView />);
    expect(vi.mocked(globalThis.fetch)).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Canonical SHA-256"), {
      target: { value: "a".repeat(64) },
    });
    fireEvent.click(screen.getByText("Register definition"));
    await waitFor(() => expect(screen.getByLabelText("Portfolio definition result")).toBeTruthy());
    expect(screen.getByText(/Risk approval and Trading execution remain/)).toBeTruthy();
    expect(String(vi.mocked(globalThis.fetch).mock.calls[0][0])).toContain(
      "/api/v1/portfolio/portfolio-alpha/definitions"
    );
  });

  it("fails closed before the API when definition JSON is invalid", async () => {
    render(<PortfolioView />);
    fireEvent.change(screen.getByLabelText("Immutable definition"), {
      target: { value: "{" },
    });
    fireEvent.click(screen.getByText("Register definition"));
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toBe("Definition must be valid JSON");
    expect(vi.mocked(globalThis.fetch)).not.toHaveBeenCalled();
  });
});
