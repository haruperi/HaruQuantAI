/** Unit tests for ResearchWorkspace (FR-API-051). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { ResearchWorkspace } from "./research";

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
        route: "/api/v1/research/run",
        operation: "api.research.run",
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

describe("ResearchWorkspace — FR-API-051", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      successEnvelope({ report_id: "r1", hypothesis: "momentum" })
    ) as unknown as typeof fetch;
  });
  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("runs research and renders the advisory report", async () => {
    const { container } = render(<ResearchWorkspace />);
    fireEvent.click(screen.getByText("Run Edge Lab"));
    await waitFor(() => {
      expect(container.textContent).toContain("report_id");
      expect(container.textContent).toContain("r1");
    });
  });

  it("unregistered_research_types_are_absent: no profile/scorecard/snapshot sub-views", async () => {
    const { container } = render(<ResearchWorkspace />);
    fireEvent.click(screen.getByText("Run Edge Lab"));
    await waitFor(() => expect(container.textContent).toContain("r1"));
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/\bprofile\b|\bscorecard\b|\bsnapshot\b/i);
  });
});
