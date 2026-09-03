/**
 * FEAT-UI-06 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const TRADING_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-06",
  widgetType: "trading",
  widgetVersion: 1,
  title: "Trading",
  description:
    "Governed order entry, ticket preflight, execution session routing, " +
    "and interactive price ladder execution.",
  requiredCapabilities: ["interfaces.operate-trading@1"],
  optionalCapabilities: ["data.stream-market-events@1"],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 720, height: 600 },
  minimumDimensions: { width: 360, height: 320 },
  commands: [
    {
      id: "trading.submit-order",
      title: "Submit Order",
      destructive: true,
    },
    {
      id: "trading.cancel-order",
      title: "Cancel Order",
      destructive: true,
    },
  ],
  subscriptions: [
    {
      kind: "sse",
      route: "/api/v1/trading/events",
      contract: "StreamEvent",
      contractVersion: "v1",
      capability: "interfaces.operate-trading@1",
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
      "Removing the widget hides the trading panel and order ticket; active " +
      "server-side orders and broker positions remain unaffected.",
  },
};
