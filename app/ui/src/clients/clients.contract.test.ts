/**
 * Drift test: the frontend client catalog mirrors the backend route inventory.
 *
 * Asserts that `ROUTE_CONTRACTS` in `routes.ts` contains exactly the 21
 * approved backend-v1 operations with the expected method/path/permission,
 * matching `app/services/api/contracts/catalog.py` (`_KNOWN_ROUTE_CONTRACTS`).
 * A backend route add/remove/rename must be reflected here or this test fails.
 */

import { describe, expect, it } from "vitest";

import {
  ROUTE_CONTRACTS,
  ROUTE_CONTRACTS_BY_ID,
  ROUTE_CONTRACT_COUNT,
} from "./routes";

/** Expected backend-v1 inventory, mirroring `_KNOWN_ROUTE_CONTRACTS`. */
const EXPECTED: ReadonlyArray<{
  id: string;
  method: string;
  path: string;
  permission: string | null;
}> = [
  { id: "api.auth.register", method: "POST", path: "/api/v1/auth/register", permission: null },
  { id: "api.auth.login", method: "POST", path: "/api/v1/auth/login", permission: null },
  { id: "api.auth.logout", method: "POST", path: "/api/v1/auth/logout", permission: null },
  { id: "api.auth.me", method: "GET", path: "/api/v1/auth/me", permission: null },
  { id: "api.health.liveness", method: "GET", path: "/api/v1/health/liveness", permission: null },
  { id: "api.health.readiness", method: "GET", path: "/api/v1/health/readiness", permission: "ops:read" },
  { id: "api.metrics", method: "GET", path: "/api/v1/metrics", permission: "ops:metrics:read" },
  { id: "api.settings.read", method: "GET", path: "/api/v1/settings", permission: "settings:read" },
  { id: "api.settings.update", method: "PUT", path: "/api/v1/settings", permission: "settings:write" },
  { id: "api.data.symbols", method: "GET", path: "/api/v1/data/symbols", permission: "data:read" },
  { id: "api.data.stream", method: "GET", path: "/api/v1/data/stream", permission: "data:read" },
  { id: "api.strategies.catalogue", method: "GET", path: "/api/v1/strategies", permission: "strategy:read" },
  {
    id: "api.strategies.versions",
    method: "GET",
    path: "/api/v1/strategies/{strategy_id}/versions",
    permission: "strategy:read",
  },
  { id: "api.research.run", method: "POST", path: "/api/v1/research/run", permission: "research:run" },
  { id: "api.dashboard.broker", method: "GET", path: "/api/v1/dashboard/broker", permission: "dashboard:read" },
  {
    id: "api.dashboard.equity_curve",
    method: "GET",
    path: "/api/v1/dashboard/equity-curve",
    permission: "dashboard:read",
  },
  { id: "api.dashboard.summary", method: "GET", path: "/api/v1/dashboard/summary", permission: "dashboard:read" },
  {
    id: "api.dashboard.system_resources",
    method: "GET",
    path: "/api/v1/dashboard/system/resources",
    permission: "dashboard:read",
  },
  {
    id: "api.dashboard.market_hours",
    method: "GET",
    path: "/api/v1/dashboard/market-hours",
    permission: "dashboard:read",
  },
  {
    id: "api.dashboard.forex_calendar",
    method: "GET",
    path: "/api/v1/dashboard/forex-calendar",
    permission: "dashboard:read",
  },
  {
    id: "api.operator.audit_events",
    method: "GET",
    path: "/api/v1/operator/audit-events",
    permission: "ops:audit:read",
  },
  { id: "api.operator.events", method: "GET", path: "/api/v1/operator/events", permission: "ops:events:read" },
  {
    id: "api.operator.approvals",
    method: "POST",
    path: "/api/v1/operator/approvals",
    permission: "ops:approve",
  },
];

describe("clients match the backend route catalog", () => {
  it("has exactly the approved 23 operations", () => {
    expect(ROUTE_CONTRACT_COUNT).toBe(23);
    expect(ROUTE_CONTRACTS).toHaveLength(23);
  });

  it("matches every expected id, method, path, and permission", () => {
    for (const expected of EXPECTED) {
      const contract = ROUTE_CONTRACTS_BY_ID[expected.id];
      expect(contract, `route ${expected.id} must exist`).toBeDefined();
      if (!contract) continue;
      expect(contract.method).toBe(expected.method);
      expect(contract.path).toBe(expected.path);
      expect(contract.permission).toBe(expected.permission);
    }
  });

  it("does not declare an unknown route id", () => {
    const knownIds = new Set(EXPECTED.map((e) => e.id));
    for (const contract of ROUTE_CONTRACTS) {
      expect(knownIds.has(contract.id), `unexpected route id ${contract.id}`).toBe(true);
    }
  });

  it("marks the governed approval route correctly", () => {
    const approvals = ROUTE_CONTRACTS_BY_ID["api.operator.approvals"];
    expect(approvals?.governed).toBe(true);
    expect(approvals?.idempotencyRequired).toBe(true);
  });

  it("marks the settings update as idempotency-required", () => {
    const update = ROUTE_CONTRACTS_BY_ID["api.settings.update"];
    expect(update?.idempotencyRequired).toBe(true);
  });

  it("marks the metrics route as text-returning", () => {
    const metrics = ROUTE_CONTRACTS_BY_ID["api.metrics"];
    expect(metrics?.returnsText).toBe(true);
  });

  it("marks the symbols route as paginated", () => {
    const symbols = ROUTE_CONTRACTS_BY_ID["api.data.symbols"];
    expect(symbols?.paginated).toBe(true);
  });

  it("marks auth.me as auth-required with no permission string", () => {
    const me = ROUTE_CONTRACTS_BY_ID["api.auth.me"];
    expect(me?.authRequired).toBe(true);
    expect(me?.permission).toBeNull();
  });

  it("marks data.stream as an SSE stream route", () => {
    const stream = ROUTE_CONTRACTS_BY_ID["api.data.stream"];
    expect(stream?.stream).toBe(true);
    expect(stream?.sideEffect).toBe("stream");
    expect(stream?.permission).toBe("data:read");
  });
});
