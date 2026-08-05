/** Unit tests for WhatIfView (CAP-UI-013, FR-API-027 live tier). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { WhatIfView } from "./whatIf";

function successEnvelope(data: unknown, route: string): Response {
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
        route,
        operation: "api.simulation.live_session_create",
        trace_id: null,
        side_effect: "write",
        duration_ms: 1,
        timestamp: "2026-08-05T12:00:00Z",
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

/** Record every request the view makes, in order. */
function stubFetch(
  responder: (url: string, init: RequestInit) => unknown
): Array<{ url: string; method: string }> {
  const calls: Array<{ url: string; method: string }> = [];
  globalThis.fetch = vi.fn(async (input: unknown, init: RequestInit = {}) => {
    const url = String(input);
    calls.push({ url, method: String(init.method ?? "GET") });
    return successEnvelope(responder(url, init), url);
  }) as unknown as typeof fetch;
  return calls;
}

describe("WhatIfView — CAP-UI-013", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
  });

  it("opens a session and shows the server cursor, not a local guess", async () => {
    stubFetch(() => ({ session_id: "sess_1", cursor: 0 }));
    render(<WhatIfView />);
    fireEvent.click(screen.getByRole("button", { name: "Open session" }));
    await waitFor(() =>
      expect(screen.getByText(/Active sess_1 — cursor 0/)).toBeTruthy()
    );
  });

  it("adopts the cursor the step returns rather than adding the step size", async () => {
    // The engine decides how far it actually advanced — a step near the end of
    // the dataset moves less than requested. Trusting a local sum would show a
    // position the session is not at.
    let cursor = 0;
    stubFetch((url) => {
      if (url.includes("/step")) {
        cursor = 7;
      }
      return { session_id: "sess_1", cursor };
    });
    render(<WhatIfView stepSize={100} />);
    fireEvent.click(screen.getByRole("button", { name: "Open session" }));
    await waitFor(() => screen.getByText(/Active sess_1/));
    fireEvent.click(screen.getByRole("button", { name: "Step 100" }));
    await waitFor(() =>
      expect(screen.getByText(/Active sess_1 — cursor 7/)).toBeTruthy()
    );
  });

  it("keeps the parent alongside the branch and records the lineage", async () => {
    stubFetch((url) =>
      url.includes("/branch")
        ? {
            session_id: "sess_2",
            cursor: 12,
            parent_session_id: "sess_1",
            divergence_index: 12,
          }
        : { session_id: "sess_1", cursor: 12 }
    );
    render(<WhatIfView />);
    fireEvent.click(screen.getByRole("button", { name: "Open session" }));
    await waitFor(() => screen.getByText(/Active sess_1/));
    fireEvent.click(screen.getByRole("button", { name: "Branch here" }));
    await waitFor(() => screen.getByText(/Active sess_2/));

    const lineage = screen.getByRole("list", { name: "Session lineage" });
    expect(lineage.textContent).toContain("sess_1");
    expect(lineage.textContent).toContain("baseline");
    expect(lineage.textContent).toContain("branched from sess_1 at 12");
  });

  it("refuses malformed overrides before calling the backend", async () => {
    const calls = stubFetch(() => ({ session_id: "sess_1", cursor: 0 }));
    render(<WhatIfView />);
    fireEvent.click(screen.getByRole("button", { name: "Open session" }));
    await waitFor(() => screen.getByText(/Active sess_1/));
    fireEvent.change(screen.getByLabelText("Branch overrides (JSON)"), {
      target: { value: "{not json" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Branch here" }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(calls.some((call) => call.url.includes("/branch"))).toBe(false);
  });

  it("drops a closed session from the lineage", async () => {
    stubFetch(() => ({ session_id: "sess_1", cursor: 3 }));
    render(<WhatIfView />);
    fireEvent.click(screen.getByRole("button", { name: "Open session" }));
    await waitFor(() => screen.getByText(/Active sess_1/));
    fireEvent.click(screen.getByRole("button", { name: "Close session" }));
    await waitFor(() =>
      expect(screen.getByText("No active session.")).toBeTruthy()
    );
    const lineage = screen.getByRole("list", { name: "Session lineage" });
    expect(lineage.textContent).not.toContain("sess_1");
  });

  it("disables session operations until a session exists", () => {
    render(<WhatIfView />);
    expect(
      screen.getByRole("button", { name: /^Step / }).hasAttribute("disabled")
    ).toBe(true);
    expect(
      screen.getByRole("button", { name: "Branch here" }).hasAttribute("disabled")
    ).toBe(true);
  });
});
