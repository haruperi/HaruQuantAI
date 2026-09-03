/**
 * FEAT-UI-05 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const PRICE_LADDER_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-05",
  widgetType: "priceLadder",
  widgetVersion: 1,
  title: "Price Ladder (DOM)",
  description:
    "Interactive depth-of-market ladder, price-level orders, cancels, " +
    "working order tags, and position tracking.",
  requiredCapabilities: ["interfaces.operate-trading@1"],
  optionalCapabilities: ["data.stream-depth-events@1"],
  placement: { defaultPanel: "right" },
  defaultDimensions: { width: 340, height: 600 },
  minimumDimensions: { width: 260, height: 400 },
  commands: [
    {
      id: "trading.submit-order",
      title: "Submit Ladder Order",
      destructive: true,
    },
    {
      id: "trading.cancel-order",
      title: "Cancel Ladder Order",
      destructive: true,
    },
  ],
  subscriptions: [
    {
      kind: "sse",
      route: "/api/v1/data/depth-stream",
      contract: "StreamEvent",
      contractVersion: "v1",
      capability: "data.stream-depth-events@1",
    },
  ],
  effects: {
    network: true,
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
      "Removing the widget hides the price ladder DOM; active exchange and " +
      "broker limit orders remain resting at server.",
  },
};
