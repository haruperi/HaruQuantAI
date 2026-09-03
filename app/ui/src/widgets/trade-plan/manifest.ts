/**
 * FEAT-UI-10 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const TRADE_PLAN_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-10",
  widgetType: "tradePlan",
  widgetVersion: 1,
  title: "Trade Plan",
  description:
    "Interactive trade planning, risk-reward calculation, TP/SL levels setup, " +
    "and ticket dispatch.",
  requiredCapabilities: [],
  optionalCapabilities: ["trading.manage-trade-plans@1"],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 500, height: 600 },
  minimumDimensions: { width: 340, height: 400 },
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
      "Removing the trade plan widget resets uncommitted draft plan parameters; " +
      "submitted orders remain active in trading subsystem.",
  },
};
