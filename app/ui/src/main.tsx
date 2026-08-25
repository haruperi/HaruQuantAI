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
import { systemStatusWidgetDefinition } from "./widgets/system_status";
import { widgetCatalogueWidgetDefinition } from "./widgets/widget_catalogue";
import { homeWidgetDefinition } from "./widgets/home";
import { productNewsWidgetDefinition } from "./widgets/product_news";
import { MockUiPresentationProvider } from "./mocks/mock_provider";

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

  // FEAT-UI-START_WORK owns the /home landing workspace and product news.
  // Dev runtime uses the gated mock capability provider; production injects
  // the generated HTTP client instead.
  const startWork = createStartWorkFeature({
    presentationClient: new MockUiPresentationProvider(),
    widgetRegistry,
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
