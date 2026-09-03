/**
 * FEAT-UI-08 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const TRADE_LOG_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-08",
  widgetType: "tradeLog",
  widgetVersion: 1,
  title: "Trade Log",
  description:
    "Historical transaction logs, execution fills review, trade notes, " +
    "and CSV export.",
  requiredCapabilities: [],
  optionalCapabilities: ["interfaces.operate-trading@1"],
  placement: { defaultPanel: "bottom" },
  defaultDimensions: { width: 800, height: 300 },
  minimumDimensions: { width: 400, height: 180 },
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
      "Removing the widget hides the trade log grid; completed trade execution " +
      "records and database logs are not removed.",
  },
};
