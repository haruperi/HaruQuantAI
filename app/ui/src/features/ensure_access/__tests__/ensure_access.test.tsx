import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";
import { UiCompositionBridge } from "../../../runtime/composition_bridge";
import { UiRuntimeProvider } from "../../../runtime/context";
import { Shell } from "../../compose_shell/Shell";
import { SPEC } from "../manifest";
import { parseEnsureAccessConfig } from "../config";
import { createFeature, EnsureAccessProvider } from "../feature";

describe("FEAT-UI-ENSURE_ACCESS (FR-UI-MANAGE_FOCUS, FR-UI-DISTINGUISH_STATE)", () => {
  let bridge: UiCompositionBridge;

  beforeEach(() => {
    cleanup();
    bridge = new UiCompositionBridge({ syncBrowserUrl: false });
  });

  afterEach(() => {
    bridge.destroy();
    cleanup();
  });

  it("manifest correctly declares identity, provided ui.ensure-access@1 and required ui.compose-shell@1", () => {
    expect(SPEC.featureId).toBe("FEAT-UI-ENSURE_ACCESS");
    expect(SPEC.name).toBe("Ensure Access");
    expect(SPEC.providesCapabilities).toContain("ui.ensure-access@1");
    expect(SPEC.requiredCapabilities).toContain("ui.compose-shell@1");
  });

  it("strict configuration parser enforces schema version and rejects unknown keys", () => {
    const defaultCfg = parseEnsureAccessConfig();
    expect(defaultCfg.schemaVersion).toBe(1);

    const emptyCfg = parseEnsureAccessConfig({});
    expect(emptyCfg.schemaVersion).toBe(1);

    expect(() => {
      parseEnsureAccessConfig({ unknown_key: true });
    }).toThrow(/Unknown configuration keys for EnsureAccess/);
  });

  it("removable feature registration updates bridge capability states cleanly", () => {
    const ensureAccess = createFeature();
    const unregister = bridge.registerFeature(ensureAccess);

    expect(bridge.getCapabilityPresentationState("ui.ensure-access@1")).toBe("ready");

    unregister();

    expect(bridge.getCapabilityPresentationState("ui.ensure-access@1")).toBe("unavailable");
  });

  it("transfers focus to active workspace outlet and empty outlet upon route/workspace transitions", () => {
    const ensureAccess = createFeature();
    bridge.registerFeature(ensureAccess);

    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-TEST-WORKSPACES",
        name: "Test Workspaces",
        description: "Test Workspaces",
        contributedWorkspaces: [
          {
            workspace_id: "ws-alpha",
            route_path: "/workspaces/alpha",
            display_name: "Alpha Workspace",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="ws-alpha-content">Alpha Content</div>,
          },
          {
            workspace_id: "ws-beta",
            route_path: "/workspaces/beta",
            display_name: "Beta Workspace",
            is_authorized: true,
            renderWorkspace: () => <div data-testid="ws-beta-content">Beta Content</div>,
          },
        ],
      },
    });

    // Start on ws-alpha
    bridge.restoreRoute("/workspaces/alpha", "/workspaces/alpha");

    render(
      <UiRuntimeProvider bridge={bridge}>
        <EnsureAccessProvider>
          <Shell />
        </EnsureAccessProvider>
      </UiRuntimeProvider>
    );

    // Initial route focuses alpha outlet
    const alphaOutlet = document.getElementById("workspace-panel-ws-alpha");
    expect(alphaOutlet).not.toBeNull();
    expect(document.activeElement).toBe(alphaOutlet);

    // Switch to ws-beta
    act(() => {
      bridge.switchWorkspace("ws-beta");
    });

    const betaOutlet = document.getElementById("workspace-panel-ws-beta");
    expect(betaOutlet).not.toBeNull();
    expect(document.activeElement).toBe(betaOutlet);

    // Restore an invalid route -> fallback to empty outlet
    act(() => {
      bridge.restoreRoute("/invalid-nonexistent-route", "/fallback");
    });

    const emptyOutlet = document.getElementById("workspace-panel-empty");
    expect(emptyOutlet).not.toBeNull();
    expect(document.activeElement).toBe(emptyOutlet);
  });
});
