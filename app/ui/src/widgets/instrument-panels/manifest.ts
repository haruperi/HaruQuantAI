/**
 * FEAT-UI-19 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: the instrument panels render local labelled values and
 * consume no backend capability.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const INSTRUMENT_PANELS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-19",
  widgetType: "optionsGrid",
  widgetVersion: 1,
  title: "Instrument Panels",
  description:
    "Labelled instrument value panels; owns presentation only and " +
    "consumes no backend capability.",
  requiredCapabilities: [],
  optionalCapabilities: [],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 480, height: 320 },
  minimumDimensions: { width: 320, height: 200 },
  commands: [],
  subscriptions: [],
  effects: {
    network: false,
    browserStorage: false,
    systemSettings: false,
  },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "region",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the widget removes its contribution from the catalogue " +
      "and saved workspaces; nothing else is affected.",
  },
};
