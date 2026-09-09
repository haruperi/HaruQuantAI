/** FEAT-UI-DEBUG_CONSOLE typed widget manifest. */

import type { WidgetManifest } from "../../types/widget-manifest";

export const DEBUG_CONSOLE_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-DEBUG_CONSOLE",
  widgetType: "debugConsole",
  widgetVersion: 1,
  title: "Debug Console",
  description: "Permission-gated bounded redacted structured diagnostics.",
  requiredCapabilities: ["interfaces.operate-settings@1"],
  optionalCapabilities: [],
  placement: { defaultPanel: "bottom" },
  defaultDimensions: { width: 760, height: 320 },
  minimumDimensions: { width: 420, height: 220 },
  commands: [],
  subscriptions: [],
  effects: { network: true, browserStorage: false, systemSettings: false },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "region",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the console disposes presentation observers and buffers only; retained diagnostic/audit evidence remains with its owner.",
  },
};
