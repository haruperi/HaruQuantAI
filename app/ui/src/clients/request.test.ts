/**
 * Unit tests for the transport primitive (`request`, `unwrapData`,
 * `ApiClientError`).
 *
 * Every test uses a fake `fetch` so no network is touched. The cases mirror
 * the FR-API-038/039/040 acceptance unit names from the API README.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import {
  ApiClientError,
  request,
  unwrapData,
} from "./request";
import { dataRoutes, healthRoutes, metricsRoutes, operatorRoutes, authRoutes } from "./routes";
import type { ApiResponse } from "./contracts";

/** Build a successful JSON envelope response. */
function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Build a 204 no-content response. */
function noContentResponse(): Response {
  return new Response(null, { status: 204 });
}

/** Build a text response (metrics). */
function textResponse(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/plain" },
  });
}

/** Minimal envelope used across success cases. */
function envelope<T>(data: T): ApiResponse<T> {
  return {
    status: "success",
    message: "ok",
    data,
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req_test_1",
      route: "/api/v1/health/liveness",
      operation: "api.health.liveness",
      trace_id: "trc_test_1",
      side_effect: "none",
      duration_ms: 12.5,
      timestamp: "2026-08-03T12:00:00Z",
      stale: false,
      stale_reason: null,
      next_cursor: null,
      page_size: null,
      idempotency_replayed: false,
    },
  };
}

describe("request — FR-API-038 typed transport", () => {
  let originalFetch: typeof globalThis.fetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("parses a successful JSON envelope and validates the payload", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(envelope({ status: "healthy", checked_at: "2026-08-03T12:00:00Z" })));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request<{ status: string; checked_at: string }>(
      healthRoutes.liveness,
      {
        schema: z.object({
          status: z.string(),
          checked_at: z.string(),
        }),
      }
    );

    expect(result.status).toBe("success");
    expect(result.data?.status).toBe("healthy");
    // Request id header is attached and forwarded.
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["X-Request-Id"]).toMatch(
      /^req-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
    // credentials: include is always set.
    expect(init.credentials).toBe("include");
  });

  it("parses 204 No Content as an empty success", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(noContentResponse());
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request<null>(authRoutes.logout);

    expect(result.status).toBe("success");
    expect(result.data).toBeNull();
  });

  it("rejects an error envelope without throwing (returns the error branch)", async () => {
    const errorEnvelope: ApiResponse<never> = {
      status: "error",
      message: "denied",
      data: null,
      error: {
        code: "AUTHORIZATION_DENIED",
        message: "permission missing",
        details: {},
        request_id: "req_test_1",
        trace_id: "trc_test_1",
        retryable: false,
      },
      metadata: envelope(null).metadata,
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(errorEnvelope, 403));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request<unknown>(healthRoutes.readiness);

    expect(result.status).toBe("error");
    if (result.status === "error") {
      expect(result.error.code).toBe("AUTHORIZATION_DENIED");
      expect(result.error.retryable).toBe(false);
    }
  });

  it("throws ApiClientError when the response is non-JSON", async () => {
    // Return a fresh Response per call so the retry path (502 is transient)
    // works correctly; after the single retry the body is still non-JSON.
    const fetchMock = vi.fn<typeof fetch>().mockImplementation(async () =>
      new Response("<html>not json</html>", {
        status: 400,
        headers: { "Content-Type": "text/html" },
      })
    );
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    await expect(request(healthRoutes.liveness)).rejects.toBeInstanceOf(ApiClientError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws ApiClientError when the envelope fails contract validation", async () => {
    // Envelope missing required `metadata.request_id`.
    const badEnvelope = {
      status: "success",
      message: "ok",
      data: {},
      error: null,
      metadata: { route: "/x", operation: "op" },
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(badEnvelope));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    await expect(request(healthRoutes.liveness)).rejects.toBeInstanceOf(ApiClientError);
  });

  it("attaches the CSRF header for non-GET cookie-authenticated calls", async () => {
    // Simulate the JS-readable CSRF cookie set on login.
    const originalDocument = globalThis.document;
    Object.defineProperty(globalThis, "document", {
      value: { cookie: "hq_csrf=test-csrf-token" },
      configurable: true,
    });

    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(envelope({}), 201)
    );
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    try {
      await request(operatorRoutes.approvals, {
        body: {
          subject_id: "u1",
          scope: "trade:approve",
          evidence: {},
          ttl_seconds: 60,
        },
      });
    } finally {
      Object.defineProperty(globalThis, "document", {
        value: originalDocument,
        configurable: true,
      });
    }

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["X-CSRF-Token"]).toBe("test-csrf-token");
    expect(headers["Idempotency-Key"]).toBeDefined();
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("returns raw text for the metrics route (returnsText bypass)", async () => {
    const prometheusText = "# HELP hq_requests_total\n# TYPE hq_requests_total counter\n";
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(textResponse(prometheusText));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request<string>(metricsRoutes.scrape);

    expect(result.status).toBe("success");
    expect(result.data).toBe(prometheusText);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Accept).toBe("text/plain");
  });

  it("retries once on a transient GET 503 then succeeds", async () => {
    const ok = jsonResponse(envelope({ symbols: [], next_cursor: null }));
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(ok);
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request(dataRoutes.symbols);

    expect(result.status).toBe("success");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("propagates stale metadata through the envelope", async () => {
    const staleEnvelope = {
      ...envelope({ status: "healthy", checked_at: "2026-08-03T12:00:00Z" }),
      metadata: { ...envelope(null).metadata, stale: true, stale_reason: "cache cold" },
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(staleEnvelope));
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch;

    const result = await request<{ status: string }>(healthRoutes.liveness);

    expect(result.status).toBe("success");
    if (result.status === "success") {
      expect(result.metadata.stale).toBe(true);
      expect(result.metadata.stale_reason).toBe("cache cold");
    }
  });
});

describe("unwrapData — FR-API-039", () => {
  it("returns data for a successful response", () => {
    const response = envelope({ count: 3 });
    expect(unwrapData(response)).toEqual({ count: 3 });
  });

  it("throws ApiClientError for an error response", () => {
    const response: ApiResponse<never> = {
      status: "error",
      message: "denied",
      data: null,
      error: {
        code: "STALE_DATA",
        message: "evidence too old",
        details: { age_seconds: 600 },
        request_id: "req_x",
        trace_id: null,
        retryable: true,
      },
      metadata: envelope(null).metadata,
    };
    try {
      unwrapData(response);
      throw new Error("should have thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      if (error instanceof ApiClientError) {
        expect(error.code).toBe("STALE_DATA");
        expect(error.retryable).toBe(true);
        expect(error.requestId).toBe("req_x");
      }
    }
  });
});

describe("ApiClientError — FR-API-040", () => {
  it("carries status, code, ids, retryability, and bounded details", () => {
    const error = new ApiClientError({
      message: "rate limited",
      status: 429,
      code: "RATE_LIMITED",
      requestId: "req_1",
      traceId: "trc_1",
      retryable: true,
      details: { retry_after_seconds: 30 },
    });
    expect(error.status).toBe(429);
    expect(error.code).toBe("RATE_LIMITED");
    expect(error.requestId).toBe("req_1");
    expect(error.traceId).toBe("trc_1");
    expect(error.retryable).toBe(true);
    expect(error.details).toEqual({ retry_after_seconds: 30 });
    // details is frozen.
    expect(Object.isFrozen(error.details)).toBe(true);
    expect(error.name).toBe("ApiClientError");
    expect(error.message).toBe("rate limited");
  });

  it("preserves the cause chain", () => {
    const cause = new TypeError("network down");
    const error = new ApiClientError({
      message: "upstream unavailable",
      status: 0,
      code: "UPSTREAM_UNAVAILABLE",
      cause,
    });
    expect(error.cause).toBe(cause);
  });
});
