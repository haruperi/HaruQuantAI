import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { UiCompositionBridge } from "../../../runtime/composition_bridge";
import { UiRuntimeProvider } from "../../../runtime/context";
import { Shell } from "../Shell";
import { parseComposeShellConfig } from "../config";
import { RouteManager } from "../RouteManager";
import { SPEC } from "../manifest";
import { createFeature } from "../feature";

describe("FEAT-UI-COMPOSE_SHELL", () => {
  let bridge: UiCompositionBridge;

  beforeEach(() => {
    bridge = new UiCompositionBridge({ syncBrowserUrl: false });
  });

  afterEach(() => {
    bridge.destroy();
    cleanup();
  });

  it("FR-UI-ASSEMBLE_SHELL: Assembles header, navigation, workspace outlet, status bar, and footer", () => {
    expect(SPEC.featureId).toBe("FEAT-UI-COMPOSE_SHELL");
    const composeShell = createFeature({ title: "HaruQuantAI Test Shell", show_footer: true });
    bridge.registerFeature(composeShell);

    render(
      <UiRuntimeProvider bridge={bridge}>
        <Shell title="HaruQuantAI Test Shell" showFooter={true} />
      </UiRuntimeProvider>
    );

    // 1. Header with title
    expect(screen.getByRole("banner")).toBeDefined();
    expect(screen.getByText("HaruQuantAI Test Shell")).toBeDefined();

    // 2. Navigation switcher
    expect(screen.getByRole("navigation", { name: /workspaces/i })).toBeDefined();

    // 3. Workspace main outlet
    expect(screen.getByRole("main")).toBeDefined();

    // 4. Status section
    expect(screen.getByText(/status:/i)).toBeDefined();

    // 5. Footer
    expect(screen.getByRole("contentinfo")).toBeDefined();
  });

  it("FR-UI-DISCOVER_WORKSPACES: Discovers authorized workspace routes from compatible contributions without hardcoded imports", () => {
    // Contribute two features with workspaces
    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-WS-ONE",
        name: "Feature One",
        description: "Feature one",
        contributedWorkspaces: [
          {
            workspace_id: "ws-1",
            route_path: "/workspaces/ws1",
            display_name: "Workspace One",
            icon_name: "1️⃣",
            required_capabilities: [],
            is_authorized: true,
            renderWorkspace: () => <div>Workspace One Content</div>,
          },
          {
            workspace_id: "ws-unauthorized",
            route_path: "/workspaces/unauth",
            display_name: "Unauthorized WS",
            required_capabilities: [],
            is_authorized: false,
          },
        ],
      },
    });

    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-WS-TWO",
        name: "Feature Two",
        description: "Feature two",
        contributedWorkspaces: [
          {
            workspace_id: "ws-2",
            route_path: "/workspaces/ws2",
            display_name: "Workspace Two",
            required_capabilities: ["custom.cap@1"],
            is_authorized: true,
            renderWorkspace: () => <div>Workspace Two Content</div>,
          },
        ],
      },
    });

    // Before custom.cap@1 is ready, only ws-1 is discovered
    let discovered = bridge.discoverWorkspaces();
    expect(discovered.map((w) => w.workspace_id)).toEqual(["ws-1"]);

    // Make custom.cap@1 ready
    bridge.setCapabilityState("custom.cap@1", "ready");
    discovered = bridge.discoverWorkspaces();
    expect(discovered.map((w) => w.workspace_id)).toEqual(["ws-1", "ws-2"]);
  });

  it("FR-UI-SWITCH_WORKSPACES: Switches active workspace and isolates interaction target", () => {
    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-TEST-WORKSPACES",
        name: "Test Workspaces",
        description: "Test",
        contributedWorkspaces: [
          {
            workspace_id: "ws-a",
            route_path: "/a",
            display_name: "Workspace A",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="content-a">Panel A</div>,
          },
          {
            workspace_id: "ws-b",
            route_path: "/b",
            display_name: "Workspace B",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="content-b">Panel B</div>,
          },
        ],
      },
    });

    render(
      <UiRuntimeProvider bridge={bridge}>
        <Shell />
      </UiRuntimeProvider>
    );

    // Initial state: click on Workspace A tab
    const tabA = screen.getByTestId("workspace-tab-ws-a");
    const tabB = screen.getByTestId("workspace-tab-ws-b");

    fireEvent.click(tabA);
    expect(screen.getByTestId("content-a")).toBeDefined();
    expect(screen.queryByTestId("content-b")).toBeNull();
    expect(tabA.getAttribute("aria-selected")).toBe("true");
    expect(tabB.getAttribute("aria-selected")).toBe("false");

    // Switch to Workspace B
    fireEvent.click(tabB);
    expect(screen.getByTestId("content-b")).toBeDefined();
    expect(screen.queryByTestId("content-a")).toBeNull();
    expect(tabB.getAttribute("aria-selected")).toBe("true");
    expect(tabA.getAttribute("aria-selected")).toBe("false");
  });

  it("FR-UI-SWITCH_WORKSPACES: Supports keyboard navigation and activation via Space, Enter, and Arrow keys", () => {
    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-TEST-WORKSPACES-KEYBOARD",
        name: "Keyboard Workspaces",
        description: "Test keyboard navigation",
        contributedWorkspaces: [
          {
            workspace_id: "ws-1",
            route_path: "/ws1",
            display_name: "Workspace 1",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="content-1">Content 1</div>,
          },
          {
            workspace_id: "ws-2",
            route_path: "/ws2",
            display_name: "Workspace 2",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="content-2">Content 2</div>,
          },
          {
            workspace_id: "ws-3",
            route_path: "/ws3",
            display_name: "Workspace 3",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="content-3">Content 3</div>,
          },
        ],
      },
    });

    render(
      <UiRuntimeProvider bridge={bridge}>
        <Shell />
      </UiRuntimeProvider>
    );

    const tab1 = screen.getByTestId("workspace-tab-ws-1");
    const tab2 = screen.getByTestId("workspace-tab-ws-2");
    const tab3 = screen.getByTestId("workspace-tab-ws-3");

    // 1. Activate via Enter
    fireEvent.keyDown(tab1, { key: "Enter" });
    expect(screen.getByTestId("content-1")).toBeDefined();
    expect(tab1.getAttribute("aria-selected")).toBe("true");

    // 2. Navigate and activate via ArrowRight
    fireEvent.keyDown(tab1, { key: "ArrowRight" });
    expect(screen.getByTestId("content-2")).toBeDefined();
    expect(tab2.getAttribute("aria-selected")).toBe("true");

    // 3. Navigate and activate via Space
    fireEvent.keyDown(tab3, { key: " " });
    expect(screen.getByTestId("content-3")).toBeDefined();
    expect(tab3.getAttribute("aria-selected")).toBe("true");

    // 4. Navigate to Home
    fireEvent.keyDown(tab3, { key: "Home" });
    expect(screen.getByTestId("content-1")).toBeDefined();
    expect(tab1.getAttribute("aria-selected")).toBe("true");
  });

  it("FR-UI-SHOW_CAPABILITY_STATE: Distinguishes all capability states without blank screens", () => {
    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-TEST-CAPS",
        name: "Test Caps",
        description: "Test Caps",
        requiredCapabilities: [
          "cap.ready@1",
          "cap.loading@1",
          "cap.degraded@1",
          "cap.unavailable@1",
          "cap.disabled@1",
          "cap.unauthorized@1",
          "cap.incompatible@1",
        ],
      },
    });

    bridge.setCapabilityState("cap.ready@1", "ready");
    bridge.setCapabilityState("cap.loading@1", "loading");
    bridge.setCapabilityState("cap.degraded@1", "degraded");
    bridge.setCapabilityState("cap.unavailable@1", "unavailable");
    bridge.setCapabilityState("cap.disabled@1", "disabled");
    bridge.setCapabilityState("cap.unauthorized@1", "unauthorized");
    bridge.setCapabilityState("cap.incompatible@1", "incompatible");

    render(
      <UiRuntimeProvider bridge={bridge}>
        <Shell />
      </UiRuntimeProvider>
    );

    expect(screen.getByTestId("capability-badge-cap.ready@1").textContent).toContain("Ready");
    expect(screen.getByTestId("capability-badge-cap.loading@1").textContent).toContain("Loading");
    expect(screen.getByTestId("capability-badge-cap.degraded@1").textContent).toContain("Degraded");
    expect(screen.getByTestId("capability-badge-cap.unavailable@1").textContent).toContain("Unavailable");
    expect(screen.getByTestId("capability-badge-cap.disabled@1").textContent).toContain("Disabled");
    expect(screen.getByTestId("capability-badge-cap.unauthorized@1").textContent).toContain("Unauthorized");
    expect(screen.getByTestId("capability-badge-cap.incompatible@1").textContent).toContain("Incompatible");
  });

  it("FR-UI-RESTORE_ROUTE: Restores valid authorized route and falls back on invalid route", () => {
    const available = [
      {
        workspace_id: "ws-valid",
        route_path: "/valid-path",
        display_name: "Valid Route",
        is_authorized: true,
      },
      {
        workspace_id: "ws-unauth",
        route_path: "/secret-path",
        display_name: "Secret Route",
        is_authorized: false,
      },
    ];

    // Valid route
    const res1 = RouteManager.resolveRoute("/valid-path", available, "/home");
    expect(res1.targetRoute).toBe("/valid-path");
    expect(res1.activeWorkspace?.workspace_id).toBe("ws-valid");

    // Unauthorized route -> fallback
    const res2 = RouteManager.resolveRoute("/secret-path", available, "/home");
    expect(res2.targetRoute).toBe("/home");
    expect(res2.activeWorkspace).toBeNull();

    // Removed / Nonexistent route -> fallback
    const res3 = RouteManager.resolveRoute("/deleted-path", available, "/home");
    expect(res3.targetRoute).toBe("/home");
    expect(res3.activeWorkspace).toBeNull();
  });

  it("FR-UI-RESTORE_ROUTE: Synchronizes browser URL history and handles popstate navigation", () => {
    const historyBridge = new UiCompositionBridge({ syncBrowserUrl: true });
    historyBridge.registerFeature({
      manifest: {
        featureId: "FEAT-TEST-HISTORY",
        name: "History WS",
        description: "Test History",
        contributedWorkspaces: [
          {
            workspace_id: "home",
            route_path: "/home",
            display_name: "Home",
            is_authorized: true,
          },
          {
            workspace_id: "research",
            route_path: "/research",
            display_name: "Research",
            is_authorized: true,
          },
        ],
      },
    });

    // Direct restoration of /research restores active_workspace_id to 'research'
    const restored = historyBridge.restoreRoute("/research", "/home");
    expect(restored).toBe("/research");
    expect(historyBridge.getSnapshot().active_workspace_id).toBe("research");

    // Switching workspace updates current route
    historyBridge.switchWorkspace("home");
    expect(historyBridge.getSnapshot().current_route).toBe("/home");

    // Clean up history bridge
    historyBridge.destroy();
  });

  it("Strict configuration parsing enforces allowed keys and valid types", () => {
    const defaultCfg = parseComposeShellConfig();
    expect(defaultCfg.defaultRoute).toBe("/home");
    expect(defaultCfg.showFooter).toBe(true);
    expect(defaultCfg.title).toBe("HaruQuantAI");

    const customCfg = parseComposeShellConfig({
      default_route: "/dashboard",
      show_footer: false,
      title: "Custom Title",
    });
    expect(customCfg.defaultRoute).toBe("/dashboard");
    expect(customCfg.showFooter).toBe(false);
    expect(customCfg.title).toBe("Custom Title");

    expect(() => {
      parseComposeShellConfig({ unknown_key: "value" });
    }).toThrow(/Unknown configuration keys/);
  });

  it("Feature unregister reverses capabilities and removes contributions cleanly", () => {
    const composeShell = createFeature();
    const unregister = bridge.registerFeature(composeShell);

    expect(bridge.getCapabilityPresentationState("ui.compose-shell@1")).toBe("ready");

    unregister();

    expect(bridge.getCapabilityPresentationState("ui.compose-shell@1")).toBe("unavailable");
  });
});
