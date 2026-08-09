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
});
