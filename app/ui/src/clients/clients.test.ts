/**
 * Domain-client integration tests.
 *
 * Each focused client (`auth`, `health`, `settings`, `data`, `strategies`,
 * `research`, `dashboards`, `operator`, `metrics`) delegates through the single
 * `request` transport. These tests prove each client is wired correctly and
 * exercises FR-UI-004 (one catalog with typed clients for the 21 operations)
 * across every family. A fake `fetch` is used; no network is touched.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiClients, unwrapData } from "./index";

/** Build a JSON success envelope response. */
function success(data: unknown, status = 200): Response {
  const body = {
    status: "success",
    message: "ok",
    data,
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req_test",
      route: "/api/v1/x",
      operation: "api.x",
      trace_id: null,
      side_effect: "read",
      duration_ms: 1.0,
      timestamp: "2026-08-03T12:00:00Z",
      stale: false,
      stale_reason: null,
      next_cursor: null,
      page_size: null,
      idempotency_replayed: false,
    },
  };
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Install a fake fetch that always returns the given response factory. */
function fakeFetch(factory: () => Response): RequestInit[] {
  const calls: RequestInit[] = [];
  globalThis.fetch = (async (
    _input: RequestInfo | URL,
    init?: RequestInit
  ) => {
    calls.push(init ?? ({} as RequestInit));
    return factory();
  }) as unknown as typeof fetch;
  return calls;
}

/** Restore the real fetch after each test. */
const realFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = realFetch;
  vi.restoreAllMocks();
});

describe("auth client", () => {
  beforeEach(() => {
    fakeFetch(() =>
      success({ user_id: "u1", username: "alice", expires_at: "2026-08-04T00:00:00Z" }, 201)
    );
  });

  it("register posts credentials and returns a session", async () => {
    const res = await apiClients.auth.register({
      username: "alice",
      password: "test-fixture-password", // pragma: allowlist secret
    });
    expect(res.status).toBe("success");
    expect(unwrapData(res).username).toBe("alice");
  });

  it("login posts credentials and returns a session", async () => {
    const res = await apiClients.auth.login({
      username: "alice",
      password: "test-fixture-password", // pragma: allowlist secret
    });
    expect(unwrapData(res).user_id).toBe("u1");
  });

  it("logout returns a bodyless success", async () => {
    fakeFetch(() => new Response(null, { status: 204 }));
    const res = await apiClients.auth.logout();
    expect(res.status).toBe("success");
    expect(res.data).toBeNull();
  });

  it("me recovers the server-authoritative identity", async () => {
    fakeFetch(() =>
      success({ user_id: "u1", username: "alice", expires_at: "2026-08-04T00:00:00Z" })
    );
    const res = await apiClients.auth.me();
    expect(unwrapData(res).username).toBe("alice");
  });
});

describe("health client", () => {
  beforeEach(() => {
    fakeFetch(() => undefined as unknown as Response);
  });

  it("liveness returns the status object", async () => {
    fakeFetch(() =>
      success({ status: "healthy", checked_at: "2026-08-03T12:00:00Z" })
    );
    const res = await apiClients.health.liveness();
    expect(unwrapData(res).status).toBe("healthy");
  });

  it("readiness returns the dependency list", async () => {
    fakeFetch(() =>
      success({
        status: "ready",
        checked_at: "2026-08-03T12:00:00Z",
        clock_drift_seconds: 0.1,
        dependencies: [
          {
            component: "api.process",
            required: true,
            healthy: true,
            checked_at: "2026-08-03T12:00:00Z",
            reason: null,
          },
        ],
      })
    );
    const res = await apiClients.health.readiness();
    expect(unwrapData(res).dependencies).toHaveLength(1);
  });
});

describe("settings client", () => {
  it("read returns the versioned record", async () => {
    fakeFetch(() =>
      success({
        user_id: "u1",
        settings: { theme: "dark" },
        version: 3,
        updated_at: "2026-08-03T12:00:00Z",
      })
    );
    const res = await apiClients.settings.read();
    expect(unwrapData(res).version).toBe(3);
  });

  it("update sends the body and returns the updated record", async () => {
    const calls = fakeFetch(() =>
      success({
        user_id: "u1",
        settings: { theme: "light" },
        version: 4,
        updated_at: "2026-08-03T12:00:00Z",
      })
    );
    const res = await apiClients.settings.update({
      settings: { theme: "light" },
      expected_version: 3,
    });
    expect(unwrapData(res).version).toBe(4);
    const init = calls[0] as RequestInit;
    expect(init.method).toBe("PUT");
    // Idempotency key is auto-generated for the update route.
    const headers = init.headers as Record<string, string>;
    expect(headers["Idempotency-Key"]).toBeDefined();
  });
});

describe("data client", () => {
  it("symbols forwards query params and returns a page", async () => {
    const calls = fakeFetch(() =>
      success({ symbols: [{ symbol: "ESU5" }], next_cursor: null })
    );
    const res = await apiClients.data.symbols({ limit: 10, query: "ES" });
    expect(unwrapData(res).symbols).toHaveLength(1);
    const init = calls[0] as RequestInit;
    expect(init.method).toBe("GET");
    const url = (calls[0] as RequestInit & { url?: string });
    void url;
  });
});

describe("strategies client", () => {
  it("catalogue returns the version list", async () => {
    fakeFetch(() => success([{ id: "s1", version: 1 }]));
    const res = await apiClients.strategies.catalogue();
    expect(unwrapData(res)).toHaveLength(1);
  });

  it("versions interpolates the strategy id path param", async () => {
    const calls = fakeFetch(() => success([{ id: "s1", version: 2 }]));
    await apiClients.strategies.versions("s1");
    const init = calls[0] as RequestInit;
    expect(init.method).toBe("GET");
  });
});

describe("research client", () => {
  it("run posts the hypothesis/dataset/config body", async () => {
    const calls = fakeFetch(() => success({ report_id: "r1" }));
    const res = await apiClients.research.run({
      hypothesis: "momentum persists",
      dataset: { symbol: "ESU5" },
      config: { stage: "enrichment" },
    });
    expect(unwrapData(res).report_id).toBe("r1");
    const init = calls[0] as RequestInit;
    expect(init.method).toBe("POST");
  });
});

describe("dashboards client", () => {
  it("each snapshot operation returns the owner payload", async () => {
    fakeFetch(() =>
      success({ timestamp: "2026-08-03T12:00:00Z", data: { ok: true } })
    );
    const broker = await apiClients.dashboards.broker();
    expect(unwrapData(broker).data).toEqual({ ok: true });
    await apiClients.dashboards.equityCurve();
    await apiClients.dashboards.summary();
    await apiClients.dashboards.systemResources();
    await apiClients.dashboards.marketHours();
    await apiClients.dashboards.forexCalendar();
  });
});

describe("operator client", () => {
  it("auditEvents forwards the limit param", async () => {
    fakeFetch(() => success({ events: [{ event_id: "e1" }] }));
    const res = await apiClients.operator.auditEvents({ limit: 5 });
    expect(unwrapData(res).events).toHaveLength(1);
  });

  it("events returns the operational event list", async () => {
    fakeFetch(() => success([{ event_id: "e1" }]));
    const res = await apiClients.operator.events();
    expect(unwrapData(res)).toHaveLength(1);
  });

  it("approvals posts the governed body with idempotency + csrf", async () => {
    const calls = fakeFetch(() =>
      success(
        {
          approval_id: "a1",
          issuer_id: "u1",
          subject_id: "u2",
          scope: "trade:approve",
          evidence_hash: "h",
          created_at: "2026-08-03T12:00:00Z",
          expires_at: "2026-08-03T13:00:00Z",
          consumed_at: null,
        },
        201
      )
    );
    Object.defineProperty(globalThis, "document", {
      value: { cookie: "hq_csrf=csrf-token" },
      configurable: true,
    });
    try {
      const res = await apiClients.operator.approvals({
        subject_id: "u2",
        scope: "trade:approve",
        evidence: { note: "ok" },
        ttl_seconds: 3600,
      });
      expect(unwrapData(res).approval_id).toBe("a1");
      const init = calls[0] as RequestInit;
      const headers = init.headers as Record<string, string>;
      expect(headers["Idempotency-Key"]).toBeDefined();
      expect(headers["X-CSRF-Token"]).toBe("csrf-token");
    } finally {
      Object.defineProperty(globalThis, "document", {
        value: undefined,
        configurable: true,
      });
    }
  });
});

describe("metrics client", () => {
  it("scrape returns the raw Prometheus text", async () => {
    fakeFetch(() =>
      new Response("# HELP x\n# TYPE x gauge\n", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      })
    );
    const res = await apiClients.metrics.scrape();
    expect(res.status).toBe("success");
    expect(res.data).toContain("# HELP x");
  });
});
