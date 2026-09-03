/**
 * FEAT-UI-09 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const POSITIONS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-09",
  widgetType: "positions",
  widgetVersion: 1,
  title: "Positions & Orders",
  description:
    "Open positions monitoring, order lifecycle management, working orders filter, " +
    "and flatten-all execution.",
  requiredCapabilities: ["interfaces.operate-trading@1"],
  optionalCapabilities: [],
  placement: { defaultPanel: "bottom" },
  defaultDimensions: { width: 800, height: 260 },
  minimumDimensions: { width: 400, height: 180 },
  commands: [
    {
      id: "trading.close-position",
      title: "Close Position",
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
      "Removing the widget hides position and order grids; active server-side " +
      "orders and portfolio positions are not modified.",
  },
};
