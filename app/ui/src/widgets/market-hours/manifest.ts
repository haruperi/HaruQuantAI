/**
 * FEAT-UI-30 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: the FX market hours widget embeds Dukascopy's applet in an
 * isolated iframe and consumes no backend capability.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const MARKET_HOURS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-30",
  widgetType: "market-hours",
  widgetVersion: 1,
  title: "Market Hours",
  description:
    "Isolated FX market-hours applet embed; owns presentation only and " +
    "consumes no backend capability.",
  requiredCapabilities: [],
  optionalCapabilities: [],
  placement: { defaultPanel: "bottom" },
  defaultDimensions: { width: 520, height: 420 },
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
      "and saved workspaces; the external applet is unaffected.",
  },
};
