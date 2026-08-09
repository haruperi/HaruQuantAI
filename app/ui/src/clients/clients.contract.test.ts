/**
 * Drift test: the frontend client catalog mirrors the backend route inventory.
 *
 * Asserts that `ROUTE_CONTRACTS` in `routes.ts` contains exactly the 81
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
  { id: "api.settings.manifest", method: "GET", path: "/api/v1/settings/manifest", permission: "settings:admin" },
  { id: "api.settings.credentials.read", method: "GET", path: "/api/v1/settings/credentials", permission: "settings:admin" },
  { id: "api.settings.credentials.update", method: "PUT", path: "/api/v1/settings/credentials/{slot}", permission: "settings:admin" },
  { id: "api.data.symbols", method: "GET", path: "/api/v1/data/symbols", permission: "data:read" },
  { id: "api.data.stream", method: "GET", path: "/api/v1/data/stream", permission: "data:read" },
  { id: "api.indicators.list", method: "GET", path: "/api/v1/indicators", permission: "indicators:read" },
  { id: "api.indicators.capabilities", method: "GET", path: "/api/v1/indicators/capabilities", permission: "indicators:read" },
  { id: "api.indicators.get_spec", method: "GET", path: "/api/v1/indicators/{indicator_id}", permission: "indicators:read" },
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
  { id: "api.simulation.run", method: "POST", path: "/api/v1/simulation/run", permission: "simulation:run" },
  { id: "api.simulation.portfolio_run", method: "POST", path: "/api/v1/simulation/portfolio-run", permission: "simulation:run" },
  { id: "api.simulation.result", method: "GET", path: "/api/v1/simulation/results/{run_id}", permission: "simulation:read" },
  { id: "api.risk.kill_switch", method: "GET", path: "/api/v1/risk/kill-switch", permission: "risk:read" },
  { id: "api.risk.decisions", method: "GET", path: "/api/v1/risk/decisions", permission: "risk:read" },
  { id: "api.trading.session", method: "GET", path: "/api/v1/trading/session", permission: "trading:read" },
  { id: "api.trading.submit_order", method: "POST", path: "/api/v1/trading/orders", permission: "trading:write" },
  { id: "api.trading.cancel_order", method: "DELETE", path: "/api/v1/trading/orders/{order_id}", permission: "trading:write" },
  { id: "api.trading.close_position", method: "POST", path: "/api/v1/trading/positions/{position_id}/close", permission: "trading:write" },
  { id: "api.data.prepare_dataset", method: "POST", path: "/api/v1/data/datasets/prepare", permission: "data:write" },
  { id: "api.data.import_dialects", method: "GET", path: "/api/v1/data/imports/dialects", permission: "data:read" },
  { id: "api.data.import_dataset", method: "POST", path: "/api/v1/data/imports", permission: "data:write" },
  { id: "api.strategies.register", method: "POST", path: "/api/v1/strategies", permission: "strategy:write" },
  { id: "api.strategies.update_parameters", method: "PATCH", path: "/api/v1/strategies/{strategy_id}/parameters", permission: "strategy:write" },
  { id: "api.risk.apply_kill_switch", method: "POST", path: "/api/v1/risk/kill-switch", permission: "risk:kill_switch" },
  { id: "api.simulation.session_create", method: "POST", path: "/api/v1/simulation/sessions", permission: "simulation:read" },
  { id: "api.simulation.live_session_create", method: "POST", path: "/api/v1/simulation/live-sessions", permission: "simulation:run" },
  { id: "api.simulation.live_session_read", method: "GET", path: "/api/v1/simulation/live-sessions/{session_id}", permission: "simulation:read" },
  { id: "api.simulation.live_session_step", method: "POST", path: "/api/v1/simulation/live-sessions/{session_id}/step", permission: "simulation:run" },
  { id: "api.simulation.live_session_branch", method: "POST", path: "/api/v1/simulation/live-sessions/{session_id}/branch", permission: "simulation:run" },
  { id: "api.simulation.live_session_close", method: "DELETE", path: "/api/v1/simulation/live-sessions/{session_id}", permission: "simulation:run" },
  { id: "api.simulation.session_frames", method: "GET", path: "/api/v1/simulation/sessions/{session_id}/frames", permission: "simulation:read" },
  { id: "api.portfolio.definition_register", method: "POST", path: "/api/v1/portfolio/{portfolio_id}/definitions", permission: "portfolio:write" },
  { id: "api.portfolio.definition", method: "GET", path: "/api/v1/portfolio/{portfolio_id}/definitions/{portfolio_version}", permission: "portfolio:read" },
  { id: "api.portfolio.construct", method: "POST", path: "/api/v1/portfolio/construct", permission: "portfolio:write" },
  { id: "api.portfolio.status", method: "GET", path: "/api/v1/portfolio/{portfolio_id}/status", permission: "portfolio:read" },
  { id: "api.portfolio.history", method: "GET", path: "/api/v1/portfolio/{portfolio_id}/history", permission: "portfolio:read" },
  { id: "api.portfolio.activate", method: "POST", path: "/api/v1/portfolio/{portfolio_id}/activate", permission: "portfolio:activate" },
  { id: "api.portfolio.rollback", method: "POST", path: "/api/v1/portfolio/{portfolio_id}/rollback", permission: "portfolio:activate" },
  { id: "api.portfolio.drift", method: "POST", path: "/api/v1/portfolio/{portfolio_id}/drift", permission: "portfolio:read" },
  { id: "api.portfolio.rebalance", method: "POST", path: "/api/v1/portfolio/rebalance", permission: "portfolio:rebalance" },
  { id: "api.portfolio.recompute_measurement", method: "POST", path: "/api/v1/portfolio/measurement/recompute", permission: "portfolio:write" },
  { id: "api.optimization.parameter_sweep", method: "POST", path: "/api/v1/optimization/parameter-sweep", permission: "optimization:run" },
  { id: "api.optimization.walk_forward", method: "POST", path: "/api/v1/optimization/walk-forward", permission: "optimization:run" },
  { id: "api.optimization.walk_forward_matrix", method: "POST", path: "/api/v1/optimization/walk-forward-matrix", permission: "optimization:run" },
  { id: "api.optimization.robustness", method: "POST", path: "/api/v1/optimization/robustness", permission: "optimization:run" },
  { id: "api.optimization.compare", method: "POST", path: "/api/v1/optimization/compare", permission: "optimization:read" },
  { id: "api.optimization.stability", method: "POST", path: "/api/v1/optimization/stability", permission: "optimization:read" },
  { id: "api.optimization.overfit", method: "POST", path: "/api/v1/optimization/overfit", permission: "optimization:read" },
  { id: "api.optimization.rank", method: "POST", path: "/api/v1/optimization/rank", permission: "optimization:read" },
  { id: "api.optimization.robustness_score", method: "POST", path: "/api/v1/optimization/robustness-score", permission: "optimization:read" },
  { id: "api.optimization.handoff", method: "POST", path: "/api/v1/optimization/handoff", permission: "optimization:read" },
  { id: "api.optimization.result", method: "GET", path: "/api/v1/optimization/results/{search_id}", permission: "optimization:read" },
  { id: "api.agentic.submit_run", method: "POST", path: "/api/v1/agentic/runs", permission: "agentic:submit" },
  { id: "api.agentic.inspect_run", method: "GET", path: "/api/v1/agentic/runs/{run_id}", permission: "agentic:read_run" },
  { id: "api.agentic.cancel_run", method: "DELETE", path: "/api/v1/agentic/runs/{run_id}", permission: "agentic:cancel_run" },
  { id: "api.agentic.audit_run", method: "GET", path: "/api/v1/agentic/runs/{run_id}/audit", permission: "agentic:read_audit" },
  { id: "api.agentic.approve_handoff", method: "POST", path: "/api/v1/agentic/handoffs/approve", permission: "agentic:approve_promotion" },
  { id: "api.agentic.quarantine_agent", method: "POST", path: "/api/v1/agentic/incidents/quarantine", permission: "agentic:operate" },
  { id: "api.agentic.disable", method: "POST", path: "/api/v1/agentic/disable", permission: "agentic:operate" },
  { id: "api.workstation.read", method: "GET", path: "/api/v1/workstation", permission: "workstation:read" },
  { id: "api.workstation.command", method: "POST", path: "/api/v1/workstation/commands", permission: "workstation:command" },
];

describe("clients match the backend route catalog", () => {
  it("has exactly the approved 81 operations", () => {
    expect(ROUTE_CONTRACT_COUNT).toBe(81);
    expect(ROUTE_CONTRACTS).toHaveLength(81);
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

  it("marks the three trading mutation routes as governed + idempotent", () => {
    for (const id of [
      "api.trading.submit_order",
      "api.trading.cancel_order",
      "api.trading.close_position",
    ]) {
      const contract = ROUTE_CONTRACTS_BY_ID[id];
      expect(contract?.governed, `${id} should be governed`).toBe(true);
      expect(contract?.idempotencyRequired, `${id} should require idempotency`).toBe(true);
      expect(contract?.sideEffect, `${id} should be governed_write`).toBe("governed_write");
    }
  });

  it("marks the simulation run routes as idempotency-required writes", () => {
    for (const id of ["api.simulation.run", "api.simulation.portfolio_run"]) {
      const contract = ROUTE_CONTRACTS_BY_ID[id];
      expect(contract?.idempotencyRequired, `${id} should require idempotency`).toBe(true);
      expect(contract?.sideEffect, `${id} should be write`).toBe("write");
    }
  });

  it("marks live session open and branch as governed + idempotent", () => {
    for (const id of [
      "api.simulation.live_session_create",
      "api.simulation.live_session_branch",
    ]) {
      const contract = ROUTE_CONTRACTS_BY_ID[id];
      expect(contract?.governed, `${id} should be governed`).toBe(true);
      expect(contract?.idempotencyRequired, `${id} should require idempotency`).toBe(true);
      expect(contract?.sideEffect, `${id} should be governed_write`).toBe("governed_write");
    }
  });

  it("leaves the live step deliberately un-keyed", () => {
    // Advancing is cumulative, not repeatable: a retried step is a further
    // step, so an idempotency key would promise a replay the engine cannot
    // give. The caller reconciles against the returned cursor instead.
    const step = ROUTE_CONTRACTS_BY_ID["api.simulation.live_session_step"];
    expect(step?.sideEffect).toBe("write");
    expect(step?.governed).toBe(false);
    expect(step?.idempotencyRequired).toBe(false);
  });
});
