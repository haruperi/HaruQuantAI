import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { ManageLayoutsClientProvider } from "../../../features/manage_layouts";
import type { IUiPresentationClient } from "../../../clients/ui_client";
import { WorkspaceTemplatesWidget } from "../Component";
import { workspaceTemplatesManifest } from "../manifest";
import { workspaceTemplatesWidgetDefinition } from "../index";

function createFakeClient(
  manageLayouts: IUiPresentationClient["manageLayouts"]
): IUiPresentationClient & { isDevOnly: boolean } {
  const unused = async () => {
    throw new Error("unused");
  };
  return {
    isDevOnly: true,
    manageLayouts,
    startWork: unused,
    editInputs: unused,
    authorStrategies: unused,
    runResearch: unused,
    editProjects: unused,
    manageData: unused,
    operateDatabanks: unused,
    exploreResults: unused,
    composePortfolios: unused,
    editCode: unused,
    monitorWork: unused,
    administerSystem: unused,
    operateTrading: unused,
    ensureAccess: unused,
    extendViews: unused,
  };
}

const WIDGET_PROPS = {
  instance: {
    instance_id: "inst-templates-test",
    widget_type: "workspace_templates",
    workspace_id: "workstation-main",
    configuration_version: 1,
    state_version: 1,
    schema_version: 1,
  },
  configuration: {},
  state: {},
  onStateChange: () => undefined,
  onConfigChange: () => undefined,
} as const;

function renderWidget(client: IUiPresentationClient) {
  return render(
    <ManageLayoutsClientProvider client={client}>
      <WorkspaceTemplatesWidget {...WIDGET_PROPS} />
    </ManageLayoutsClientProvider>
  );
}

describe("FEAT-UI-MANAGE_LAYOUTS workspace_templates widget (FR-UI-COMPOSE_PANELS, FR-UI-DISTINGUISH_STATE)", () => {
  afterEach(() => {
    cleanup();
  });

  it("is owned by FEAT-UI-MANAGE_LAYOUTS with a registry-valid definition", () => {
    expect(workspaceTemplatesManifest.owning_feature).toBe("FEAT-UI-MANAGE_LAYOUTS");
    expect(workspaceTemplatesWidgetDefinition.descriptor.widget_type).toBe("workspace_templates");
    expect(typeof workspaceTemplatesWidgetDefinition.component).toBe("function");
  });

  it("lists versioned templates from the COMPOSE operation and labels mock data non-authoritative", async () => {
    const client = createFakeClient(async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-templates-test",
      result_version: 1,
      template: {
        template_id: "template-chart-ladder-v1",
        name: "Chart + Ladder (Mock)",
        description: "Mock template.",
        layout: {
          layout_id: "layout-tpl-mock",
          workspace_id: "template-chart-ladder",
          actor_id: "system",
          layout_version: 1,
          capability_snapshot_id: "snap-mock",
          widget_instances: [],
          placements: [],
          active_panel_id: null,
          content_hash: "hash",
          schema_version: 1,
        },
        schema_version: 1,
      },
      schema_version: 1,
    }));
    renderWidget(client);

    expect(await screen.findByTestId("workspace-template-template-haruquant-v1", {}, { timeout: 2000 })).toBeDefined();
    expect(screen.getByTestId("workspace-template-template-chart-ladder-v1")).toBeDefined();
    expect(screen.getByTestId("workspace-templates-mock-label").textContent).toContain("MOCK DATA");
  });

  it("renders applied template state structurally and with visible badge (FR-UI-DISTINGUISH_STATE)", async () => {
    const client = createFakeClient(async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-templates-apply",
      result_version: 1,
      schema_version: 1,
    }));
    renderWidget(client);

    const list = await screen.findByRole("list", { name: "Workspace templates" });
    expect(list).toBeInTheDocument();

    const tplBtn = screen.getByRole("button", { name: /HaruQuant/i });
    expect(tplBtn).toBeInTheDocument();
    expect(tplBtn.tagName).toBe("BUTTON");
    expect(tplBtn.closest("li")).not.toBeNull();
    expect(list.contains(tplBtn)).toBe(true);

    expect(tplBtn).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByTestId("template-applied-badge-template-haruquant-v1")).toBeNull();

    // Click to apply template
    fireEvent.click(tplBtn);

    expect(tplBtn).toHaveAttribute("aria-pressed", "true");
    const badge = screen.getByTestId("template-applied-badge-template-haruquant-v1");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("[Applied]");
  });

  it("renders a non-blocking unavailable state when the templates provider fails", async () => {
    const client = createFakeClient(async () => {
      throw new Error("offline");
    });
    renderWidget(client);

    const status = await screen.findByTestId("workspace-templates-unavailable", {}, { timeout: 2000 });
    expect(status.textContent).toContain("Layout controls remain available.");
  });
});
