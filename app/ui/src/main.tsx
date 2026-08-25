import React from "react";
import ReactDOM from "react-dom/client";
import { UiCompositionBridge } from "./runtime/composition_bridge";
import { UiRuntimeProvider } from "./runtime/context";
import { WidgetRegistry } from "./runtime/widget_registry";
import { WorkspaceHost } from "./workspaces/WorkspaceHost";
import { SelectionProvider } from "./context/selection";
import { TemporalProvider } from "./context/temporal";
import { FocusManagerProvider } from "./context/focus";
import { createFeature } from "./features/compose_shell";
import { systemStatusWidgetDefinition } from "./widgets/system_status";
import { widgetCatalogueWidgetDefinition } from "./widgets/widget_catalogue";

function bootstrapApp() {
  const bridge = new UiCompositionBridge();
  const composeShell = createFeature();
  bridge.registerFeature(composeShell);

  // Initialize global typed widget registry
  const widgetRegistry = new WidgetRegistry();
  widgetRegistry.registerWidget(systemStatusWidgetDefinition);
  widgetRegistry.registerWidget(widgetCatalogueWidgetDefinition);

  // Contribute default spatiotemporal workstation workspaces
  bridge.registerFeature({
    manifest: {
      featureId: "FEAT-UI-START_WORK",
      name: "Start Work",
      description: "Home workstation canvas",
      contributedWorkspaces: [
        {
          workspace_id: "workstation-main",
          route_path: "/home",
          display_name: "Workstation",
          icon_name: "??",
          is_authorized: true,
          renderWorkspace: () => (
            <WorkspaceHost
              workspaceId="workstation-main"
              registry={widgetRegistry}
            />
          ),
        },
        {
          workspace_id: "workstation-research",
          route_path: "/research",
          display_name: "Research",
          icon_name: "??",
          is_authorized: true,
          renderWorkspace: () => (
            <WorkspaceHost
              workspaceId="workstation-research"
              registry={widgetRegistry}
            />
          ),
        },
        {
          workspace_id: "workstation-data",
          route_path: "/data",
          display_name: "Data",
          icon_name: "??",
          is_authorized: true,
          renderWorkspace: () => (
            <WorkspaceHost
              workspaceId="workstation-data"
              registry={widgetRegistry}
            />
          ),
        },
      ],
    },
  });

  const initialPath =
    typeof window !== "undefined" && window.location.pathname && window.location.pathname !== "/"
      ? window.location.pathname
      : "/home";

  bridge.restoreRoute(initialPath, "/home");

  const rootElement = document.getElementById("root");
  if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <UiRuntimeProvider bridge={bridge}>
          <FocusManagerProvider>
            <SelectionProvider>
              <TemporalProvider workspaceId="global-workspace">
                {composeShell.render()}
              </TemporalProvider>
            </SelectionProvider>
          </FocusManagerProvider>
        </UiRuntimeProvider>
      </React.StrictMode>
    );
  }
}

bootstrapApp();
