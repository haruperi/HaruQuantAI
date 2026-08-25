import React from "react";
import ReactDOM from "react-dom/client";
import { UiCompositionBridge } from "./runtime/composition_bridge";
import { UiRuntimeProvider } from "./runtime/context";
import { createFeature } from "./features/compose_shell";

function bootstrapApp() {
  const bridge = new UiCompositionBridge();
  const composeShell = createFeature();
  bridge.registerFeature(composeShell);

  // Contribute default home workspace
  bridge.registerFeature({
    manifest: {
      featureId: "FEAT-UI-START_WORK",
      name: "Start Work",
      description: "Home workspace",
      contributedWorkspaces: [
        {
          workspace_id: "home",
          route_path: "/home",
          display_name: "Home",
          icon_name: "🏠",
          is_authorized: true,
          renderWorkspace: () => (
            <div className="home-workspace-view">
              <h2>Welcome to HaruQuantAI</h2>
              <p>Capability-aware quantitative trading research platform.</p>
            </div>
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
          {composeShell.render()}
        </UiRuntimeProvider>
      </React.StrictMode>
    );
  }
}

bootstrapApp();
