/** FEAT-UI-RUN_MONITOR typed widget manifest. */

import type { WidgetManifest } from "../../types/widget-manifest";

export const RUN_MONITOR_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-RUN_MONITOR",
  widgetType: "runMonitor",
  widgetVersion: 1,
  title: "Jobs",
  description: "Bounded authoritative job/run monitoring and supported controls.",
  requiredCapabilities: ["interfaces.operate-jobs@1"],
  optionalCapabilities: [],
  placement: { defaultPanel: "right" },
  defaultDimensions: { width: 480, height: 420 },
  minimumDimensions: { width: 340, height: 240 },
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
      "Removing the widget disposes observations and buffers only; accepted jobs and workers remain owned by Orchestration.",
  },
};
