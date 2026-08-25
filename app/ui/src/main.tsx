import React from "react";
import ReactDOM from "react-dom/client";
import { UiCompositionBridge } from "./runtime/composition_bridge";
import { UiRuntimeProvider } from "./runtime/context";
import { WidgetRegistry } from "./runtime/widget_registry";
import { SelectionProvider } from "./context/selection";
import { TemporalProvider } from "./context/temporal";
import { FocusManagerProvider } from "./context/focus";
import { createFeature as createComposeShellFeature } from "./features/compose_shell";
import { createFeature as createStartWorkFeature } from "./features/start_work";
import {
  createFeature as createManageLayoutsFeature,
  ViewScaleProvider,
  ScaleControls,
} from "./features/manage_layouts";
import { createFeature as createEditInputsFeature } from "./features/edit_inputs";
import { createFeature as createMonitorWorkFeature } from "./features/monitor_work";
import { systemStatusWidgetDefinition } from "./widgets/system_status";
import { widgetCatalogueWidgetDefinition } from "./widgets/widget_catalogue";
import { homeWidgetDefinition } from "./widgets/home";
import { productNewsWidgetDefinition } from "./widgets/product_news";
import { workspaceTemplatesWidgetDefinition } from "./widgets/workspace_templates";
import { jobProgressWidgetDefinition } from "./widgets/job_progress";
import { activityLogWidgetDefinition } from "./widgets/activity_log";
import { MockUiPresentationProvider } from "./mocks/mock_provider";
import { MOCK_ACTIVITY_SNAPSHOT } from "./mocks/fixtures";

function bootstrapApp() {
  const bridge = new UiCompositionBridge();
  const composeShell = createComposeShellFeature();
  bridge.registerFeature(composeShell);

  // Initialize global typed widget registry
  const widgetRegistry = new WidgetRegistry();
  widgetRegistry.registerWidget(systemStatusWidgetDefinition);
  widgetRegistry.registerWidget(widgetCatalogueWidgetDefinition);
  widgetRegistry.registerWidget(homeWidgetDefinition);
  widgetRegistry.registerWidget(productNewsWidgetDefinition);
  widgetRegistry.registerWidget(workspaceTemplatesWidgetDefinition);
  widgetRegistry.registerWidget(jobProgressWidgetDefinition);
  widgetRegistry.registerWidget(activityLogWidgetDefinition);

  // FEAT-UI-MANAGE_LAYOUTS owns templates, persistence, and view scale.
  const manageLayouts = createManageLayoutsFeature({
    presentationClient: new MockUiPresentationProvider(),
  });
  bridge.registerFeature(manageLayouts);

  // FEAT-UI-EDIT_INPUTS owns local draft preservation (Partial slice).
  bridge.registerFeature(createEditInputsFeature());

  // FEAT-UI-MONITOR_WORK owns job progress tracking and activity log.
  const monitorWork = createMonitorWorkFeature({
    presentationClient: new MockUiPresentationProvider(),
    activitySnapshot: MOCK_ACTIVITY_SNAPSHOT,
  });
  bridge.registerFeature(monitorWork);

  // FEAT-UI-START_WORK owns the /home landing workspace and product news.
  // Dev runtime uses the gated mock capability provider; production injects
  // the generated HTTP client instead.
  const startWork = createStartWorkFeature({
    presentationClient: new MockUiPresentationProvider(),
    widgetRegistry,
    layoutController: manageLayouts.layoutController,
  });
  bridge.registerFeature(startWork);

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
          <ViewScaleProvider>
            <FocusManagerProvider>
              <SelectionProvider>
                <TemporalProvider workspaceId="global-workspace">
                  {manageLayouts.renderClientProvider(
                    monitorWork.renderClientProvider(
                      composeShell.render(<ScaleControls />)
                    )
                  )}
                </TemporalProvider>
              </SelectionProvider>
            </FocusManagerProvider>
          </ViewScaleProvider>
        </UiRuntimeProvider>
      </React.StrictMode>
    );
  }
}

bootstrapApp();
