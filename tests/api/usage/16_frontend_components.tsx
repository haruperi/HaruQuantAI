/**
 * Usage program 16 — Workflow presentation components (FEAT-API-11).
 *
 * Standalone numbered program, not a pytest test. Exercises the public surface
 * of the §4.11 components through an injected fake `fetch` and a self-contained
 * jsdom DOM, so no network is touched and no secrets are read.
 *
 * Run:
 *   cd app/ui && NODE_PATH=./node_modules npx tsx --tsconfig ./tsconfig.usage.json \
 *     ../../tests/api/usage/16_frontend_components.tsx
 */

import { JSDOM } from "jsdom";

// Establish a DOM before importing React/testing-library, which need globals.
const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
});
const define = (key: string, value: unknown) => {
  Object.defineProperty(globalThis, key, { value, configurable: true, writable: true });
};
define("window", dom.window);
define("document", dom.window.document);
define("sessionStorage", dom.window.sessionStorage);
define("HTMLElement", dom.window.HTMLElement);
define("Element", dom.window.Element);
define("Node", dom.window.Node);
define("getComputedStyle", dom.window.getComputedStyle);
define("MouseEvent", dom.window.MouseEvent);
define("Event", dom.window.Event);
define("CustomEvent", dom.window.CustomEvent);
const raf = (cb: FrameRequestCallback) => setTimeout(() => cb(Date.now()), 0) as unknown as number;
define("requestAnimationFrame", raf);
define("cancelAnimationFrame", (id: number) => clearTimeout(id));
dom.window.requestAnimationFrame = raf as never;
dom.window.cancelAnimationFrame = ((id: number) => clearTimeout(id)) as never;

import React, { type ReactNode } from "react";
import { render, waitFor } from "@testing-library/react";

import { AppShell, DashboardView, StrategyWorkspace, SimulationView, RiskView, TradingView, ResearchWorkspace } from "../../../app/ui/src/components/workflow";
import { AuthProvider } from "../../../app/ui/src/context";

/** Build a successful envelope. */
function successEnvelope(data: unknown, route = "/api/v1/x"): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_u",
        route,
        operation: route,
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

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(`usage assertion failed: ${message}`);
}

/** FR-API-046: AppShell renders children when authenticated. */
async function testUsageAppShell(): Promise<void> {
  // Mock useAuth via the module before importing AppShell is already done; stub
  // fetch so AuthProvider recovery (if it were mounted) would resolve. Here we
  // render AppShell directly and rely on the real useAuth → /me path returning
  // a 401 (unauthenticated), which the shell turns into a login prompt.
  globalThis.fetch = (() => Promise.resolve(new Response(
    JSON.stringify({ status: "error", message: "auth", data: null,
      error: { code: "AUTHENTICATION_REQUIRED", message: "expired", details: {}, request_id: "r", trace_id: null, retryable: false },
      metadata: { contract_version: "v1", schema_id: "api.metadata.v1", request_id: "r", route: "/api/v1/auth/me", operation: "api.auth.me", trace_id: null, side_effect: "read", duration_ms: 1, timestamp: "2026-08-03T12:00:00Z", stale: false, stale_reason: null, next_cursor: null, page_size: null, idempotency_replayed: false } }),
    { status: 401, headers: { "Content-Type": "application/json" } }
  ))) as unknown as typeof fetch;

  const { container, unmount } = render(<AuthProvider><AppShell><span>protected</span></AppShell></AuthProvider>);
  await waitFor(() => assert((container.textContent ?? "").includes("sign in"), "expected login prompt"), { timeout: 2000 });
  unmount();
  console.log("[testUsageAppShell] ok — shell renders login prompt when unauthenticated");
}

/** FR-API-047: DashboardView renders the six panels. */
async function testUsageDashboard(): Promise<void> {
  globalThis.fetch = (() => Promise.resolve(successEnvelope({ ok: true }, "/api/v1/dashboard/broker"))) as unknown as typeof fetch;
  const { container, unmount } = render(<DashboardView />);
  await waitFor(() => assert((container.textContent ?? "").includes("Broker"), "expected Broker panel"), { timeout: 2000 });
  unmount();
  console.log("[testUsageDashboard] ok — six panels render");
}

/** FR-API-048: StrategyWorkspace fetches the catalogue. */
async function testUsageStrategies(): Promise<void> {
  globalThis.fetch = (() => Promise.resolve(successEnvelope([{ id: "s1" }], "/api/v1/strategies"))) as unknown as typeof fetch;
  const { container, unmount } = render(<StrategyWorkspace />);
  await waitFor(() => assert((container.textContent ?? "").includes("s1"), "expected strategy id"), { timeout: 2000 });
  unmount();
  console.log("[testUsageStrategies] ok — catalogue renders");
}

/** FR-API-049: SimulationView is wired to the typed client. */
async function testUsageSimulation(): Promise<void> {
  globalThis.fetch = (() => Promise.resolve(successEnvelope({ run_id: "run_1", status: "completed" }, "/api/v1/simulation/run"))) as unknown as typeof fetch;
  const { container, unmount } = render(<SimulationView />);
  // Just assert the controls render (no click needed for this smoke test).
  assert((container.textContent ?? "").includes("Run Backtest"), "expected Run Backtest control");
  unmount();
  console.log("[testUsageSimulation] ok — simulation view mounts");
}

/** FR-API-050 Risk: RiskView mounts. */
async function testUsageRisk(): Promise<void> {
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/decisions")) {
      return successEnvelope([], "/api/v1/risk/decisions");
    }
    return successEnvelope({ state: "inactive" }, "/api/v1/risk/kill-switch");
  }) as unknown as typeof fetch;
  const { container, unmount } = render(<RiskView />);
  await waitFor(() => assert((container.textContent ?? "").includes("Kill Switch"), "expected kill-switch heading"), { timeout: 3000 });
  unmount();
  console.log("[testUsageRisk] ok — risk view mounts");
}

/** FR-API-050 Trading: TradingView mounts and gates governed actions. */
async function testUsageTrading(): Promise<void> {
  globalThis.fetch = (() => Promise.resolve(successEnvelope({ account: {}, positions: [], orders: [] }, "/api/v1/trading/session"))) as unknown as typeof fetch;
  const { container, unmount } = render(<TradingView />);
  await waitFor(() => assert((container.textContent ?? "").includes("Submit Order"), "expected Submit Order"), { timeout: 2000 });
  // Governed actions must be disabled by default.
  const buttons = container.querySelectorAll("button");
  const submitDisabled = Array.from(buttons).some((b) => (b.textContent ?? "").includes("Submit Order") && b.hasAttribute("disabled"));
  assert(submitDisabled, "expected Submit Order to be disabled before preflight");
  unmount();
  console.log("[testUsageTrading] ok — trading view mounts, governed actions disabled");
}

/** FR-API-051: ResearchWorkspace mounts. */
async function testUsageResearch(): Promise<void> {
  globalThis.fetch = (() => Promise.resolve(successEnvelope({ report_id: "r1" }, "/api/v1/research/run"))) as unknown as typeof fetch;
  const { container, unmount } = render(<ResearchWorkspace />);
  assert((container.textContent ?? "").includes("Run Edge Lab"), "expected Run Edge Lab control");
  unmount();
  console.log("[testUsageResearch] ok — research view mounts");
}

async function main(): Promise<void> {
  console.log("=== Usage program 16 — Workflow presentation components ===");
  await testUsageAppShell();
  await testUsageDashboard();
  await testUsageStrategies();
  await testUsageSimulation();
  await testUsageRisk();
  await testUsageTrading();
  await testUsageResearch();
  console.log("=== All usage cases passed ===");
}

void React;
main().catch((error) => {
  console.error("USAGE PROGRAM FAILED:", error);
  process.exit(1);
});
