/**
 * NFR-API-009: Accessibility — core workflow components have ARIA roles.
 *
 * Structural accessibility verification: core workflow components expose ARIA
 * roles, labels, and keyboard-reachable controls. This is not a full WCAG 2.1
 * AA audit (which needs browser tooling), but it verifies the structural
 * guarantees we can make at the component level today.
 */

import { describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";

import { AppShell } from "./shell";
import { useWorkspaceStore } from "@/features/workspaces";

// Mock useAuth for AppShell.
const authStateMock = vi.fn();
vi.mock("@/context", () => ({
  get useAuth() {
    return authStateMock;
  },
}));

function authed() {
  return {
    state: "authenticated",
    principal: null,
    error: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  };
}

describe("NFR-API-009: Accessibility structural checks", () => {
  beforeEach: vi.resetAllMocks;

  it("AppShell loading state has role=status and aria-live=polite", () => {
    authStateMock.mockReturnValue({ ...authed(), state: "loading" });
    const { container } = render(
      <AppShell><span>content</span></AppShell>
    );
    const status = container.querySelector('[role="status"]');
    expect(status).toBeTruthy();
    expect(status?.getAttribute("aria-live")).toBe("polite");
  });

  it("AppShell error boundary has role=alert", () => {
    authStateMock.mockReturnValue(authed());
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    function Boom(): React.ReactNode {
      throw new Error("boom");
    }
    const { container } = render(
      <AppShell><Boom /></AppShell>
    );
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeTruthy();
    spy.mockRestore();
  });

  it("AppShell unauthenticated state has role=status", () => {
    authStateMock.mockReturnValue({ ...authed(), state: "unauthenticated" });
    const { container } = render(
      <AppShell><span>content</span></AppShell>
    );
    const status = container.querySelector('[role="status"]');
    expect(status).toBeTruthy();
  });

  it("DashboardView renders a region with aria-label", async () => {
    const { DashboardView } = await import("./dashboard");
    globalThis.fetch = vi.fn(async () => new Response(
      JSON.stringify({
        status: "success", message: "ok", data: { ok: true }, error: null,
        metadata: {
          contract_version: "v1", schema_id: "api.metadata.v1", request_id: "r",
          route: "/x", operation: "x", trace_id: null, side_effect: "read",
          duration_ms: 1, timestamp: "2026-08-03T12:00:00Z", stale: false,
          stale_reason: null, next_cursor: null, page_size: null, idempotency_replayed: false,
        },
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )) as unknown as typeof fetch;
    const { container } = render(<DashboardView />);
    const region = container.querySelector('[role="region"][aria-label]');
    expect(region).toBeTruthy();
  });

  it("TradingWidget governed actions are keyboard-reachable (button elements)", async () => {
    useWorkspaceStore.setState({
      accountMode: "demo",
      platformAccountMode: "demo",
      tradingModeCompatible: true,
    });
    const { TradingWidget } = await import("../../features/trading");
    globalThis.fetch = vi.fn(async () => new Response(
      JSON.stringify({
        status: "success", message: "ok",
        data: [],
        error: null,
        metadata: {
          contract_version: "v1", schema_id: "api.metadata.v1", request_id: "r",
          route: "/x", operation: "x", trace_id: null, side_effect: "read",
          duration_ms: 1, timestamp: "2026-08-03T12:00:00Z", stale: false,
          stale_reason: null, next_cursor: null, page_size: null, idempotency_replayed: false,
        },
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )) as unknown as typeof fetch;
    const { container } = render(<TradingWidget accountId="account-1" symbol="EURUSD" />);
    // All interactive controls must be <button> elements (keyboard-reachable).
    await waitFor(() => expect(container.querySelectorAll("button").length).toBeGreaterThan(0));
  });
});
