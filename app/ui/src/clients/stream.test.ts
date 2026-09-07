/** Unit tests for the typed SSE transport. */

import { afterEach, describe, expect, it, vi } from "vitest";

import { dataRoutes } from "./routes";
import { openStream } from "./stream";

describe("openStream request identity", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("generates a canonical prefixed UUID4 request ID", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("", { status: 200 }));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    for await (const _event of openStream(dataRoutes.stream)) {
      // The empty response intentionally yields no events.
    }

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["X-Request-Id"]).toMatch(
      /^req-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
  });

  it("validates the wire error object and preserves a safe message", async () => {
    const wire = {
      sequence: 7,
      request_id: "req-stream",
      route: "/api/v1/data/snapshot-stream",
      event_type: "error",
      timestamp: "2026-09-08T00:00:00Z",
      payload: null,
      error: { message: "backpressure", private: { omitted: true } },
      cursor: "cursor-7",
      schema_version: 1,
    };
    const body = `id: 7\nevent: error\ndata: ${JSON.stringify(wire)}\n\n`;
    globalThis.fetch = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response(body, { status: 200 }));

    const events = [];
    for await (const event of openStream(dataRoutes.stream)) events.push(event);

    expect(events).toHaveLength(1);
    expect(events[0]?.error).toBe("backpressure");
    expect(events[0]?.sequence).toBe(7);
  });
});
