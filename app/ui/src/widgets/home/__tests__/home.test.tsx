import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { UiCompositionBridge } from "../../../runtime/composition_bridge";
import { UiRuntimeProvider } from "../../../runtime/context";
import { StartWorkClientProvider } from "../../../features/start_work";
import type { IUiPresentationClient } from "../../../clients/ui_client";
import { HomeWidget } from "../Component";
import { homeManifest } from "../manifest";
import { homeWidgetDefinition } from "../index";

function createFakeClient(overrides: Partial<IUiPresentationClient> = {}): IUiPresentationClient & { isDevOnly: boolean } {
  const base: IUiPresentationClient & { isDevOnly: boolean } = {
    isDevOnly: true,
    startWork: async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-home-test",
      result_version: 1,
      schema_version: 1,
    }),
    manageLayouts: async () => { throw new Error("unused"); },
    editInputs: async () => { throw new Error("unused"); },
    authorStrategies: async () => { throw new Error("unused"); },
    runResearch: async () => { throw new Error("unused"); },
    editProjects: async () => { throw new Error("unused"); },
    manageData: async () => { throw new Error("unused"); },
    operateDatabanks: async () => { throw new Error("unused"); },
    exploreResults: async () => { throw new Error("unused"); },
    composePortfolios: async () => { throw new Error("unused"); },
    editCode: async () => { throw new Error("unused"); },
    monitorWork: async () => { throw new Error("unused"); },
    administerSystem: async () => { throw new Error("unused"); },
    operateTrading: async () => { throw new Error("unused"); },
    ensureAccess: async () => { throw new Error("unused"); },
    extendViews: async () => { throw new Error("unused"); },
    ...overrides,
  };
  return base;
}

describe("FEAT-UI-START_WORK home widget (FR-UI-PRESENT_HOME)", () => {
  let bridge: UiCompositionBridge;

  beforeEach(() => {
    bridge = new UiCompositionBridge({ syncBrowserUrl: false });
    bridge.registerFeature({
      manifest: {
        featureId: "FEAT-WS-TEST",
        name: "Test Workspaces",
        description: "Test",
        contributedWorkspaces: [
          {
            workspace_id: "ws-available",
            route_path: "/available",
            display_name: "Available Workspace",
            is_authorized: true,
          },
          {
            workspace_id: "ws-capability-gated",
            route_path: "/gated",
            display_name: "Gated Workspace",
            required_capabilities: ["missing.cap@1"],
            is_authorized: true,
          },
        ],
      },
    });
  });

  afterEach(() => {
    bridge.destroy();
    cleanup();
  });

  it("is owned by FEAT-UI-START_WORK with a registry-valid definition", () => {
    expect(homeManifest.owning_feature).toBe("FEAT-UI-START_WORK");
    expect(homeWidgetDefinition.descriptor.widget_type).toBe("home");
    expect(typeof homeWidgetDefinition.component).toBe("function");
  });

  it("renders product/workspace identity, versions, and capability-aware entry points; hides capability-absent actions; labels mock data non-authoritative", async () => {
    const client = createFakeClient();
    render(
      <UiRuntimeProvider bridge={bridge}>
        <StartWorkClientProvider client={client}>
          <HomeWidget
            instance={{
              instance_id: "inst-home-test",
              widget_type: "home",
              workspace_id: "workstation-main",
              configuration_version: 1,
              state_version: 1,
              schema_version: 1,
            }}
            configuration={{}}
            state={{}}
            onStateChange={() => undefined}
            onConfigChange={() => undefined}
          />
        </StartWorkClientProvider>
      </UiRuntimeProvider>
    );

    // Identity and version presentation
    expect(screen.getByTestId("home-identity").textContent).toContain("HaruQuantAI");
    expect(screen.getByTestId("home-version").textContent).toContain("HaruQuantAI Workstation 0.1.0");

    // Capability-aware entry points: available workspace offered, gated one hidden
    expect(screen.getByTestId("home-entry-ws-available")).toBeDefined();
    expect(screen.queryByTestId("home-entry-ws-capability-gated")).toBeNull();

    // SHOW_HOME succeeded
    await screen.findByText(/Home ready/, {}, { timeout: 2000 });

    // Mock-derived content is visibly labeled non-authoritative
    expect(screen.getByTestId("home-mock-label").textContent).toContain("MOCK DATA");
  });

  it("keeps identity and entry points usable when the home provider fails", async () => {
    const client = createFakeClient({
      startWork: async () => {
        throw new Error("provider offline");
      },
    });
    render(
      <UiRuntimeProvider bridge={bridge}>
        <StartWorkClientProvider client={client}>
          <HomeWidget
            instance={{
              instance_id: "inst-home-test-2",
              widget_type: "home",
              workspace_id: "workstation-main",
              configuration_version: 1,
              state_version: 1,
              schema_version: 1,
            }}
            configuration={{}}
            state={{}}
            onStateChange={() => undefined}
            onConfigChange={() => undefined}
          />
        </StartWorkClientProvider>
      </UiRuntimeProvider>
    );

    expect(await screen.findByText(/Home provider unavailable/, {}, { timeout: 2000 })).toBeDefined();
    expect(screen.getByTestId("home-entry-ws-available")).toBeDefined();
    expect(screen.getByTestId("home-version")).toBeDefined();
  });
});
