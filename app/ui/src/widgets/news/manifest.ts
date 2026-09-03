/**
 * FEAT-UI-29 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: the news widget embeds the external Investing.com news
 * feed in an isolated iframe and consumes no backend capability.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const NEWS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-29",
  widgetType: "news",
  widgetVersion: 1,
  title: "News",
  description:
    "Isolated external news feed embed; owns presentation only and " +
    "consumes no backend capability.",
  requiredCapabilities: [],
  optionalCapabilities: [],
  placement: { defaultPanel: "bottom" },
  defaultDimensions: { width: 560, height: 400 },
  minimumDimensions: { width: 320, height: 240 },
  commands: [],
  subscriptions: [],
  effects: {
    network: true,
    browserStorage: false,
    systemSettings: false,
  },
  accessibility: {
    ariaLive: "off",
    landmarkRole: "region",
    keyboardNavigable: false,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the widget removes its contribution from the catalogue " +
      "and saved workspaces; the external feed is unaffected.",
  },
};
