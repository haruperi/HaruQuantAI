/** FEAT-UI-SYSTEM_SETTINGS typed widget manifest. */

import type { WidgetManifest } from "../../types/widget-manifest";

export const SYSTEM_SETTINGS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-SYSTEM_SETTINGS",
  widgetType: "systemSettings",
  widgetVersion: 1,
  title: "System Settings",
  description:
    "Versioned system configuration with effective-policy, conflict, and write-only credential handling.",
  requiredCapabilities: ["interfaces.operate-settings@1"],
  optionalCapabilities: [],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 720, height: 540 },
  minimumDimensions: { width: 400, height: 320 },
  commands: [],
  subscriptions: [],
  effects: { network: true, browserStorage: false, systemSettings: true },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "dialog",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the widget hides configuration UI only; Workspace-owned settings and audit state remain unchanged.",
  },
};
