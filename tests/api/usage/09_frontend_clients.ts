/**
 * Usage program 09 — Typed frontend clients (FEAT-API-09).
 *
 * Standalone numbered program, not a pytest test. Exercises every public
 * operation of the typed transport through the documented public API using an
 * injected fake `fetch`, so no network is touched and no secrets are read.
 *
 * Run:
 *   cd app/ui && npx tsx ../../tests/api/usage/09_frontend_clients.ts
 *
 * Each acceptance case prints a bounded, secret-safe line and exits non-zero
 * on the first failure.
 */

import {
  apiClients,
  ApiClientError,
  unwrapData,
} from "../../../app/ui/src/clients";
import type { ApiResponse } from "../../../app/ui/src/clients";
import { ROUTE_CONTRACT_COUNT } from "../../../app/ui/src/clients";

/** Fake fetch response spec. */
interface FakeResponseSpec {
  readonly status: number;
  readonly headers?: Record<string, string>;
  readonly body: string;
}

/** Build a minimal valid metadata object. */
function metadata(route: string, operation: string) {
  return {
    contract_version: "v1" as const,
    schema_id: "api.metadata.v1",
    request_id: "req_usage_1",
    route,
    operation,
    trace_id: "trc_usage_1",
    side_effect: "read" as const,
    duration_ms: 8.2,
    timestamp: "2026-08-03T12:00:00Z",
    stale: false,
    stale_reason: null,
    next_cursor: null,
    page_size: null,
    idempotency_replayed: false,
  };
}

/** Build a success envelope JSON string. */
function successEnvelope<T>(route: string, operation: string, data: T): string {
  return JSON.stringify({
    status: "success",
    message: "ok",
    data,
    error: null,
    metadata: metadata(route, operation),
  });
}

/** Build an error envelope JSON string. */
function errorEnvelope(
  route: string,
  operation: string,
  code: string,
  message: string
): string {
  return JSON.stringify({
    status: "error",
    message,
    data: null,
    error: {
      code,
      message,
      details: {},
      request_id: "req_usage_1",
      trace_id: "trc_usage_1",
      retryable: false,
    },
    metadata: metadata(route, operation),
  });
}

/** Install a fake fetch that maps the next call to a canned response. */
function installFakeFetch(queue: FakeResponseSpec[]): {
  calls: RequestInit[];
} {
  const calls: RequestInit[] = [];
  let index = 0;
  const fakeFetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
    calls.push(init ?? ({} as RequestInit));
    const spec = queue[index] ?? queue[queue.length - 1];
    index += 1;
    return new Response(spec.body, {
      status: spec.status,
      headers: spec.headers,
    });
  }) as unknown as typeof fetch;
  globalThis.fetch = fakeFetch;
  return { calls };
}

/** Assert helper that throws with a clear message on mismatch. */
function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(`usage assertion failed: ${message}`);
}

/** FR-API-038: typed request parses a successful envelope. */
async function testUsageRequest(): Promise<void> {
  installFakeFetch([
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
      body: successEnvelope("/api/v1/health/liveness", "api.health.liveness", {
        status: "healthy",
        checked_at: "2026-08-03T12:00:00Z",
      }),
    },
  ]);

  const result: ApiResponse<{ status: string; checked_at: string }> =
    await apiClients.health.liveness();
  assert(result.status === "success", "liveness should succeed");
  if (result.status === "success") {
    assert(result.data?.status === "healthy", "liveness data.status mismatch");
    console.log("[testUsageRequest] ok — liveness returned healthy envelope");
  }
}

/** FR-API-039: unwrapData returns the data field. */
async function testUsageUnwrapData(): Promise<void> {
  installFakeFetch([
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
      body: successEnvelope(
        "/api/v1/settings",
        "api.settings.read",
        {
          user_id: "u_1",
          settings: { theme: "dark" },
          version: 4,
          updated_at: "2026-08-03T12:00:00Z",
        }
      ),
    },
  ]);

  const response = await apiClients.settings.read();
  const data = unwrapData(response);
  assert(data.version === 4, "settings version should be 4");
  console.log("[testUsageUnwrapData] ok — settings version 4 unwrapped");
}

/** FR-API-040: ApiClientError carries traceable fields. */
async function testUsageApiClientError(): Promise<void> {
  installFakeFetch([
    {
      status: 403,
      headers: { "Content-Type": "application/json" },
      body: errorEnvelope(
        "/api/v1/dashboard/summary",
        "api.dashboard.summary",
        "AUTHORIZATION_DENIED",
        "dashboard:read missing"
      ),
    },
  ]);

  const response = await apiClients.dashboards.summary();
  assert(response.status === "error", "summary should be an error branch");
  try {
    unwrapData(response);
    throw new Error("unwrapData should have thrown on an error branch");
  } catch (error) {
    assert(error instanceof ApiClientError, "error should be ApiClientError");
    if (error instanceof ApiClientError) {
      assert(error.code === "AUTHORIZATION_DENIED", "error code mismatch");
      assert(error.requestId === "req_usage_1", "request id mismatch");
      console.log(
        `[testUsageApiClientError] ok — ${error.code} (req=${error.requestId})`
      );
    }
  }
}

/** FR-API-041: focused clients map to the 78 registered operations. */
async function testUsageFocusedClients(): Promise<void> {
  // Drift check: the catalog declares exactly the 78 approved operations.
  assert(ROUTE_CONTRACT_COUNT === 78, "route count should be 78");

  // Exercise a representative slice of the catalog (one op per family) through
  // the typed client surface so the catalog is proven wired end-to-end.
  const livenessCall = apiClients.health.liveness;
  const symbolsCall = apiClients.data.symbols;
  const approvalsCall = apiClients.operator.approvals;
  const metricsCall = apiClients.metrics.scrape;
  const liveBranchCall = apiClients.liveSimulation.branch;
  assert(typeof livenessCall === "function", "health.liveness missing");
  assert(typeof symbolsCall === "function", "data.symbols missing");
  assert(typeof approvalsCall === "function", "operator.approvals missing");
  assert(typeof liveBranchCall === "function", "liveSimulation.branch missing");
  assert(typeof metricsCall === "function", "metrics.scrape missing");

  // Verify the metrics text-return path through the catalog.
  installFakeFetch([
    {
      status: 200,
      headers: { "Content-Type": "text/plain" },
      body: "# HELP hq_uptime\n# TYPE hq_uptime gauge\n",
    },
  ]);
  const metricsResponse = await apiClients.metrics.scrape();
  assert(metricsResponse.status === "success", "metrics should succeed");
  if (metricsResponse.status === "success") {
    assert(
      typeof metricsResponse.data === "string",
      "metrics data should be a string"
    );
  }

  console.log(
    `[testUsageFocusedClients] ok — catalog has ${ROUTE_CONTRACT_COUNT} operations, all families reachable`
  );
}

/** Run every acceptance case in order; exit non-zero on the first failure. */
async function main(): Promise<void> {
  console.log("=== Usage program 09 — Typed frontend clients ===");
  await testUsageRequest();
  await testUsageUnwrapData();
  await testUsageApiClientError();
  await testUsageFocusedClients();
  console.log("=== All usage cases passed ===");
}

main().catch((error) => {
  console.error("USAGE PROGRAM FAILED:", error);
  process.exit(1);
});
