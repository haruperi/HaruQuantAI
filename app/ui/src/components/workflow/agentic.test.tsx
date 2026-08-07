/** Unit tests for the governed Agentic operator workflow. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AgenticView } from "./agentic";

function successEnvelope(data: unknown): Response {
  return new Response(JSON.stringify({
    status: "success",
    message: "ok",
    data,
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req_agentic",
      route: "/api/v1/agentic/runs",
      operation: "api.agentic.submit_run",
      trace_id: null,
      side_effect: "write",
      duration_ms: 1,
      timestamp: "2026-08-07T00:00:00Z",
      stale: false,
      stale_reason: null,
      next_cursor: null,
      page_size: null,
      idempotency_replayed: false,
    },
  }), { status: 200, headers: { "Content-Type": "application/json" } });
}

const realFetch = globalThis.fetch;

describe("AgenticView", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () => successEnvelope({ run_id: "run-one", state: "submitted" })) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("reserves rather than executes an Agentic run", async () => {
    render(<AgenticView />);
    fireEvent.click(screen.getByText("Reserve Agentic run"));
    await waitFor(() => expect(screen.getByLabelText("Agentic result")).toBeTruthy());
    expect(screen.getByText(/cannot approve risk/)).toBeTruthy();
    expect(screen.getByText(/run-one/)).toBeTruthy();
    expect(String(vi.mocked(globalThis.fetch).mock.calls[0][0])).toContain("/api/v1/agentic/runs");
  });

  it("requires confirmation before firm disablement", () => {
    const confirmation = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<AgenticView />);
    fireEvent.click(screen.getByText("Disable Agentic"));
    expect(confirmation).toHaveBeenCalledOnce();
    expect(vi.mocked(globalThis.fetch)).not.toHaveBeenCalled();
  });
});
