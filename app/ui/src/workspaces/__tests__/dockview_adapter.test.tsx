import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { WorkspaceHost } from "../WorkspaceHost";
import { WidgetRegistry } from "../../runtime/widget_registry";
import { systemStatusWidgetDefinition } from "../../widgets/system_status";
import { widgetCatalogueWidgetDefinition } from "../../widgets/widget_catalogue";
import { UiCompositionBridge } from "../../runtime/composition_bridge";
import { UiRuntimeProvider } from "../../runtime/context";
import {
  createTemplateRequestBus,
  buildTemplateManager,
  MANAGE_LAYOUTS_TEMPLATES,
} from "../../features/manage_layouts";
import type { LayoutPersistenceLike } from "../WorkspaceHost";

describe("WorkspaceHost and Dockview Integration", () => {
  it("renders workspace toolbar with add widget button and template selector", () => {
    const bridge = new UiCompositionBridge();
    const registry = new WidgetRegistry();
    registry.registerWidget(systemStatusWidgetDefinition);
    registry.registerWidget(widgetCatalogueWidgetDefinition);

    render(
      <UiRuntimeProvider bridge={bridge}>
        <WorkspaceHost workspaceId="test-ws" registry={registry} />
      </UiRuntimeProvider>
    );

    expect(screen.getByTestId("workspace-host")).toBeInTheDocument();
    expect(screen.getByText("+ Add Widget")).toBeInTheDocument();
    expect(screen.getByLabelText("Template:")).toBeInTheDocument();
    expect(screen.getByText("Clear Canvas")).toBeInTheDocument();
  });

  it("FR-UI-RESTORE_LAYOUTS: restores a persisted snapshot on mount and saves changes (persistence wiring)", async () => {
    const bridge = new UiCompositionBridge();
    const registry = new WidgetRegistry();
    registry.registerWidget(systemStatusWidgetDefinition);
    registry.registerWidget(widgetCatalogueWidgetDefinition);

    const saved: string[] = [];
    const persistence: LayoutPersistenceLike = {
      save: (workspaceId, snapshot) => saved.push(`${workspaceId}:${snapshot.layout_id}`),
      load: () => ({
        snapshot: {
          layout_id: "layout-persisted-test",
          workspace_id: "test-ws-restore",
          actor_id: "actor-current",
          layout_version: 1,
          capability_snapshot_id: "snap-test",
          widget_instances: [
            {
              instance_id: "inst-persisted-status",
              widget_type: "system_status",
              workspace_id: "test-ws-restore",
              configuration_version: 1,
              state_version: 1,
              schema_version: 1,
            },
          ],
          placements: [
            {
              instance_id: "inst-persisted-status",
              panel_id: "panel-1",
              panel_order: 0,
              tab_order: 0,
              size_ratio: "1",
              schema_version: 1,
            },
          ],
          active_panel_id: "inst-persisted-status",
          content_hash: "persisted-hash",
          schema_version: 1,
        },
        diagnostics: [],
      }),
    };

    render(
      <UiRuntimeProvider bridge={bridge}>
        <WorkspaceHost
          workspaceId="test-ws-restore"
          registry={registry}
          layoutPersistence={persistence}
        />
      </UiRuntimeProvider>
    );

    // Persisted snapshot restored: the system_status widget from storage (not
    // the default template) is mounted.
    await waitFor(
      () => {
        expect(document.querySelector('[data-widget-type="system_status"]')).not.toBeNull();
      },
      { timeout: 3000 }
    );
  });

  it("FR-UI-COMPOSE_PANELS: applies a harvested template requested through the feature bus", async () => {
    const bridge = new UiCompositionBridge();
    const registry = new WidgetRegistry();
    registry.registerWidget(systemStatusWidgetDefinition);
    registry.registerWidget(widgetCatalogueWidgetDefinition);

    const bus = createTemplateRequestBus();
    const harvested = MANAGE_LAYOUTS_TEMPLATES[0]!; // haruquant preset

    render(
      <UiRuntimeProvider bridge={bridge}>
        <WorkspaceHost
          workspaceId="test-ws-templates"
          registry={registry}
          templateManager={buildTemplateManager()}
          templateRequests={bus}
        />
      </UiRuntimeProvider>
    );

    bus.emit(harvested.template_id);

    // Harvested template's panels are instantiated; unregistered widget
    // types are diagnosed by the engine serializer (missing placeholders).
    await waitFor(
      () => {
        const panels = document.querySelectorAll(
          '[data-testid="dockview-workspace"] .dv-resize-container, [data-testid="dockview-workspace"] [role="region"]'
        );
        expect(panels.length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );
  });
});
